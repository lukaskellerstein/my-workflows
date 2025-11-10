"""
Deep Research Workflow - Asks clarifying questions via UI, validates results via Slack
Uses OpenAI Agents SDK with tools and Slack for final validation
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from agents import Agent, RunConfig, Runner, trace
from pydantic import BaseModel, Field
from temporalio import activity, workflow
from temporalio.contrib import openai_agents as temporal_agents


@dataclass
class ResearchRequest:
    """Initial research request from user."""

    task: str
    user_id: str = "unknown"


@dataclass
class ClarifyingQuestion:
    """Clarifying question to narrow scope."""

    question: str
    context: str


@dataclass
class UIAnswer:
    """Answer received from UI."""

    text: str
    question_index: int
    timestamp: str


@dataclass
class SlackValidation:
    """Validation from Slack before sending to user."""

    approved: bool
    user: str
    user_id: str
    feedback: str
    timestamp: str
    thread_ts: str


@dataclass
class ResearchResult:
    """Final research result."""

    original_task: str
    clarifications: list[str]
    research_summary: str
    detailed_findings: str
    sources: list[str]
    confidence_score: float
    validated: bool


# Structured output models for LLM responses


class QuestionOutput(BaseModel):
    """A single clarifying question."""

    question: str = Field(description="The clarifying question to ask")
    context: str = Field(description="Why this question is important for the research")


class ClarifyingQuestionsOutput(BaseModel):
    """Structured output for clarifying questions generation."""

    questions: list[QuestionOutput] = Field(
        min_length=2, max_length=3, description="2-3 focused clarifying questions"
    )
    reasoning: str = Field(description="Why these specific questions were chosen")


class ResearchDataOutput(BaseModel):
    """Structured output for research data."""

    summary: str = Field(description="Comprehensive summary of research findings")
    key_findings: list[str] = Field(description="List of key findings")
    sources: list[str] = Field(description="List of sources consulted")
    confidence_level: str = Field(
        description="Confidence level in the research: high, medium, or low"
    )


class ResearchReportOutput(BaseModel):
    """Structured output for the final research report."""

    executive_summary: str = Field(
        description="Brief executive summary (2-3 sentences)"
    )
    main_findings: str = Field(description="Detailed main findings and analysis")
    recommendations: list[str] = Field(description="Actionable recommendations")
    conclusion: str = Field(description="Concluding remarks")
    confidence_assessment: str = Field(
        description="Assessment of confidence in the findings"
    )


# Activities


@activity.defn
async def perform_web_search(query: str) -> str:
    """Perform web search using AI."""
    activity.logger.info(f"Searching: {query}")

    # Simulate web search - in production, use real search API
    result = f"Search results for '{query}':\n\n"
    result += "- Finding 1: Relevant information about the topic\n"
    result += "- Finding 2: Statistical data and trends\n"
    result += "- Finding 3: Expert opinions and analysis\n"

    await asyncio.sleep(2)  # Simulate search time
    return result


@activity.defn
async def analyze_content(content: str, focus: str) -> str:
    """Analyze content with AI."""
    activity.logger.info(f"Analyzing content with focus: {focus}")

    # In production, use real LLM analysis
    result = f"Analysis of content (focus: {focus}):\n\n"
    result += "Key insights:\n"
    result += "- Main point 1\n"
    result += "- Main point 2\n"
    result += "- Main point 3\n"

    await asyncio.sleep(2)  # Simulate analysis time
    return result


@activity.defn(name="post_research_validation_to_slack")
async def post_validation_request_to_slack(
    research_result: str, workflow_id: str, channel: str = "human-in-loop"
) -> str:
    """Post research result to Slack for validation before sending to user."""
    activity.logger.info("Posting validation request to Slack")

    try:
        import os

        from slack_sdk.web.async_client import AsyncWebClient

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")

        client = AsyncWebClient(token=slack_token)

        # Truncate for Slack
        preview = (
            research_result[:1000] + "..."
            if len(research_result) > 1000
            else research_result
        )

        response = await client.chat_postMessage(
            channel=channel,
            text="*Research Result Validation*",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🔍 Deep Research Complete - Validation Needed*",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"**Research Result:**\n```{preview}```",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Should we send this to the user?*\nReply 'yes' to approve or 'no' with feedback",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"💬 Reply in thread\n🆔 Workflow: `{workflow_id}`",
                        }
                    ],
                },
            ],
        )

        return response["ts"]

    except Exception as e:
        activity.logger.error(f"Failed to post to Slack: {e}")
        raise


@activity.defn(name="update_research_slack_thread")
async def update_slack_thread(thread_ts: str, channel: str, message: str) -> None:
    """Update Slack thread."""
    activity.logger.info(f"Updating thread: {thread_ts}")

    try:
        import os

        from slack_sdk.web.async_client import AsyncWebClient

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")

        client = AsyncWebClient(token=slack_token)
        await client.chat_postMessage(
            channel=channel, thread_ts=thread_ts, text=message
        )

    except Exception as e:
        activity.logger.error(f"Failed to update thread: {e}")
        raise


# Main Workflow


@workflow.defn
class DeepResearchWorkflow:
    """
    Deep research workflow that:
    1. Asks clarifying questions via UI
    2. Performs 15-minute deep research
    3. Validates result via Slack before sending to user
    4. Provides comprehensive answer
    """

    def __init__(self) -> None:
        self._ui_answers: list[UIAnswer] = []
        self._clarifying_questions: list[ClarifyingQuestion] = []
        self._waiting_for_ui_answer = False
        self._current_question_index = -1
        self._slack_validation: SlackValidation | None = None
        self._slack_thread_ts: str | None = None

    @workflow.run
    async def run(self, request: ResearchRequest) -> ResearchResult:
        """Execute deep research workflow."""
        workflow.logger.info(f"Starting deep research: {request.task}")

        with trace("Deep research workflow"):
            # Step 1: Generate clarifying questions using AI
            self._clarifying_questions = await self._generate_clarifying_questions(
                request.task
            )

            # Step 2: Ask questions via UI (not Slack!)
            clarifications = await self._collect_ui_answers()

            # Step 3: Perform deep research (15 minutes)
            research_data = await self._perform_deep_research(
                request.task, clarifications
            )

            # Step 4: Generate comprehensive report
            report = await self._generate_report(
                request.task, clarifications, research_data
            )

            # Step 5: Validate via Slack before sending to user
            validated = await self._validate_via_slack(report)

            # Step 6: Finalize result
            result = ResearchResult(
                original_task=request.task,
                clarifications=clarifications,
                research_summary=report[:500],
                detailed_findings=report,
                sources=research_data.get("sources", []),
                confidence_score=0.85,
                validated=validated,
            )

        return result

    async def _generate_clarifying_questions(
        self, task: str
    ) -> list[ClarifyingQuestion]:
        """Generate clarifying questions using AI with structured outputs."""
        workflow.logger.info("Generating clarifying questions")

        agent = Agent(
            name="Question Generator",
            model="gpt-5-mini",
            instructions="""You are a research assistant that asks clarifying questions.
            Given a research task, generate 2-3 focused clarifying questions that will help
            narrow down the scope and improve research quality.

            Focus on questions that will:
            - Clarify the specific aspect or angle of interest
            - Understand the intended use case or audience
            - Determine the depth and breadth of research needed""",
            output_type=ClarifyingQuestionsOutput,  # Structured output
        )

        result = await Runner.run(
            agent, input=f"Research task: {task}", run_config=RunConfig()
        )

        # Output is guaranteed to be ClarifyingQuestionsOutput
        assert isinstance(result.final_output, ClarifyingQuestionsOutput)
        questions_output = result.final_output

        # Convert to ClarifyingQuestion dataclasses
        questions = [
            ClarifyingQuestion(
                question=q.question,
                context=q.context,
            )
            for q in questions_output.questions
        ]

        workflow.logger.info(
            f"Generated {len(questions)} questions: {questions_output.reasoning}"
        )

        return questions

    async def _collect_ui_answers(self) -> list[str]:
        """Collect answers to clarifying questions via UI."""
        workflow.logger.info(
            f"Collecting {len(self._clarifying_questions)} answers from UI"
        )

        clarifications = []

        for idx, question in enumerate(self._clarifying_questions):
            self._current_question_index = idx
            self._waiting_for_ui_answer = True

            workflow.logger.info(f"Waiting for UI answer to question {idx + 1}")

            # Wait for answer from UI (30 minute timeout)
            try:
                await workflow.wait_condition(
                    lambda: any(a.question_index == idx for a in self._ui_answers),
                    timeout=timedelta(minutes=30),
                )

                # Get the answer for this question
                answer = next(a for a in self._ui_answers if a.question_index == idx)
                clarifications.append(answer.text)

                workflow.logger.info(f"Received UI answer: {answer.text}")

            except asyncio.TimeoutError:
                workflow.logger.warning(f"Timeout on question {idx+1}, using default")
                clarifications.append("No specific preference")

            self._waiting_for_ui_answer = False

        self._current_question_index = -1
        return clarifications

    async def _perform_deep_research(
        self, task: str, clarifications: list[str]
    ) -> dict[str, any]:
        """Perform deep research using AI agents with tools and structured outputs."""
        workflow.logger.info("Starting deep research phase")

        # Create research agent with tools
        search_tool = temporal_agents.workflow.activity_as_tool(
            perform_web_search, start_to_close_timeout=timedelta(seconds=30)
        )
        analysis_tool = temporal_agents.workflow.activity_as_tool(
            analyze_content, start_to_close_timeout=timedelta(seconds=30)
        )

        agent = Agent(
            name="Research Agent",
            model="gpt-5-mini",
            instructions="""You are a thorough research assistant.
            Use web search to find information, then analyze the content.
            Focus on providing comprehensive, well-sourced information.

            Provide a detailed summary, key findings, list your sources, and assess confidence level.""",
            tools=[search_tool, analysis_tool],
            output_type=ResearchDataOutput,  # Structured output
        )

        # Perform research
        research_input = f"""Task: {task}

Clarifications:
{chr(10).join(f"- {c}" for c in clarifications)}

Please conduct thorough research on this topic."""

        result = await Runner.run(agent, input=research_input, run_config=RunConfig())

        # Output is guaranteed to be ResearchDataOutput
        assert isinstance(result.final_output, ResearchDataOutput)
        research_data = result.final_output

        workflow.logger.info(
            f"Research complete: {len(research_data.key_findings)} findings, "
            f"confidence: {research_data.confidence_level}"
        )

        return {
            "summary": research_data.summary,
            "key_findings": research_data.key_findings,
            "sources": research_data.sources,
            "confidence_level": research_data.confidence_level,
        }

    async def _generate_report(
        self, task: str, clarifications: list[str], research_data: dict[str, str]
    ) -> str:
        """Generate comprehensive research report with structured output."""
        workflow.logger.info("Generating final report")

        agent = Agent(
            name="Report Writer",
            model="gpt-5-mini",
            instructions="""You are a research report writer.
            Create a comprehensive, well-structured report with:
            - Executive summary (brief overview)
            - Main findings (detailed analysis)
            - Actionable recommendations
            - Conclusion
            - Confidence assessment

            Make it clear, actionable, and professional.""",
            output_type=ResearchReportOutput,  # Structured output
        )

        report_input = f"""Original Task: {task}

Clarifications:
{chr(10).join(f"- {c}" for c in clarifications)}

Research Summary:
{research_data['summary']}

Key Findings:
{chr(10).join(f"- {f}" for f in research_data.get('key_findings', []))}

Sources:
{chr(10).join(f"- {s}" for s in research_data.get('sources', []))}

Confidence Level: {research_data.get('confidence_level', 'medium')}

Please write a comprehensive research report."""

        result = await Runner.run(agent, input=report_input, run_config=RunConfig())

        # Output is guaranteed to be ResearchReportOutput
        assert isinstance(result.final_output, ResearchReportOutput)
        report = result.final_output

        # Format the structured report into a readable string
        formatted_report = f"""# Research Report: {task}

## Executive Summary
{report.executive_summary}

## Main Findings
{report.main_findings}

## Recommendations
{chr(10).join(f"- {r}" for r in report.recommendations)}

## Conclusion
{report.conclusion}

## Confidence Assessment
{report.confidence_assessment}
"""

        workflow.logger.info("Report generated with structured format")
        return formatted_report

    async def _validate_via_slack(self, report: str) -> bool:
        """Validate research result via Slack before sending to user."""
        workflow.logger.info("Requesting validation via Slack")

        workflow_id = workflow.info().workflow_id

        # Post to Slack for validation
        self._slack_thread_ts = await workflow.execute_activity(
            post_validation_request_to_slack,
            args=[report, workflow_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Wait for validation (2 hour timeout)
        try:
            await workflow.wait_condition(
                lambda: self._slack_validation is not None,
                timeout=timedelta(hours=2),
            )

            if self._slack_validation and self._slack_validation.approved:
                await workflow.execute_activity(
                    update_slack_thread,
                    args=[
                        self._slack_thread_ts,
                        "human-in-loop",
                        f"✅ Validated by {self._slack_validation.user}! Sending to user...",
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                return True
            else:
                await workflow.execute_activity(
                    update_slack_thread,
                    args=[
                        self._slack_thread_ts,
                        "human-in-loop",
                        f"❌ Not approved. Feedback: {self._slack_validation.feedback if self._slack_validation else 'timeout'}",
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                return False

        except asyncio.TimeoutError:
            workflow.logger.warning("Validation timeout - defaulting to approved")
            return True  # Auto-approve on timeout

    @workflow.signal
    async def answer_question(self, answer: UIAnswer) -> None:
        """Receive answer from UI for clarifying question."""
        workflow.logger.info(
            f"Received UI answer for question {answer.question_index}: {answer.text}"
        )
        self._ui_answers.append(answer)

    @workflow.signal
    async def receive_validation(self, validation: SlackValidation) -> None:
        """Receive validation from Slack."""
        workflow.logger.info(f"Received Slack validation: {validation.approved}")
        self._slack_validation = validation

    @workflow.query
    def get_status(self) -> dict:
        """Get current workflow status."""
        return {
            "current_phase": (
                "asking_questions"
                if self._waiting_for_ui_answer
                else "researching" if self._slack_thread_ts is None else "validating"
            ),
            "current_question_index": self._current_question_index,
            "total_questions": len(self._clarifying_questions),
            "answers_received": len(self._ui_answers),
            "waiting_for_ui": self._waiting_for_ui_answer,
            "slack_thread_ts": self._slack_thread_ts,
        }

    @workflow.query
    def get_clarifying_questions(self) -> list[dict]:
        """Get clarifying questions for UI."""
        return [
            {
                "index": idx,
                "question": q.question,
                "context": q.context,
                "answered": any(a.question_index == idx for a in self._ui_answers),
            }
            for idx, q in enumerate(self._clarifying_questions)
        ]

    @workflow.query
    def get_thread_ts(self) -> str | None:
        """Get Slack thread timestamp."""
        return self._slack_thread_ts
