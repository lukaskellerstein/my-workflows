"""
Code Analysis Workflow - Analyzes codebase with AI agents, validates output via Slack
Uses OpenAI Agents SDK with tools for code analysis, security checks
Slack is used ONLY for final validation before sending results to user
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
class CodeAnalysisRequest:
    """Code analysis request."""

    repository_path: str
    analysis_type: str  # 'security', 'performance', 'quality', 'refactoring'
    user_id: str = "unknown"


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
class CodeAnalysisResult:
    """Code analysis result."""

    repository: str
    analysis_type: str
    issues_found: int
    critical_issues: list[str]
    recommendations: list[str]
    refactoring_suggestions: list[str]
    validated: bool
    validation_feedback: str


# Structured output models for LLM responses


class CodeIssue(BaseModel):
    """A single code issue identified."""

    file: str = Field(description="File where the issue was found")
    severity: str = Field(description="Severity: critical, high, medium, or low")
    description: str = Field(description="Description of the issue")
    line_number: int | None = Field(
        default=None, description="Line number if applicable"
    )


class CodeAnalysisOutput(BaseModel):
    """Structured output for code analysis."""

    summary: str = Field(description="Overall summary of the analysis")
    critical_issues: list[CodeIssue] = Field(
        description="List of critical issues that need immediate attention"
    )
    other_issues: list[CodeIssue] = Field(description="List of non-critical issues")
    recommendations: list[str] = Field(
        description="Actionable recommendations for improvement"
    )
    refactoring_suggestions: list[str] = Field(
        description="Suggestions for code refactoring"
    )
    overall_quality_score: float = Field(
        ge=0.0, le=10.0, description="Overall code quality score (0-10)"
    )


# Activities


@activity.defn
async def scan_repository(repo_path: str) -> dict[str, list[str]]:
    """Scan repository and list files."""
    activity.logger.info(f"Scanning repository: {repo_path}")

    import os

    files = {"python": [], "javascript": [], "other": []}

    # Simulate file scanning
    await asyncio.sleep(1)

    files["python"] = ["main.py", "utils.py", "models.py"]
    files["javascript"] = ["app.js", "config.js"]

    activity.logger.info(f"Found {sum(len(v) for v in files.values())} files")
    return files


@activity.defn
async def analyze_code_file(file_path: str, analysis_type: str) -> str:
    """Analyze individual code file."""
    activity.logger.info(f"Analyzing {file_path} for {analysis_type}")

    # Simulate code analysis
    await asyncio.sleep(1)

    result = f"Analysis of {file_path} ({analysis_type}):\n"
    result += "- Issue 1: Potential security vulnerability\n"
    result += "- Issue 2: Performance bottleneck detected\n"
    result += "- Recommendation: Refactor for better maintainability\n"

    return result


@activity.defn
async def run_security_scan(code: str) -> dict[str, any]:
    """Run security analysis on code."""
    activity.logger.info("Running security scan")

    # Simulate security scan
    await asyncio.sleep(2)

    return {
        "vulnerabilities": ["SQL Injection risk", "XSS vulnerability"],
        "severity": "high",
        "recommendations": ["Use parameterized queries", "Sanitize user input"],
    }


@activity.defn(name="post_code_validation_to_slack")
async def post_validation_request_to_slack(
    analysis_summary: str, workflow_id: str, channel: str = "human-in-loop"
) -> str:
    """Post analysis result to Slack for validation before sending to user."""
    activity.logger.info("Posting validation request to Slack")

    try:
        import os

        from slack_sdk.web.async_client import AsyncWebClient

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")

        client = AsyncWebClient(token=slack_token)

        response = await client.chat_postMessage(
            channel=channel,
            text="*Code Analysis Validation*",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🔍 Code Analysis Complete - Validation Needed*",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{analysis_summary}"},
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


@activity.defn(name="update_code_slack_thread")
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
class CodeAnalysisWorkflow:
    """
    Code analysis workflow that:
    1. Scans repository
    2. Analyzes code with AI agents
    3. Runs security/quality checks
    4. Validates result via Slack before sending to user
    """

    def __init__(self) -> None:
        self._validation: SlackValidation | None = None
        self._thread_ts: str | None = None

    @workflow.run
    async def run(self, request: CodeAnalysisRequest) -> CodeAnalysisResult:
        """Execute code analysis workflow."""
        workflow.logger.info(
            f"Starting code analysis: {request.repository_path} ({request.analysis_type})"
        )

        with trace("Code analysis workflow"):
            # Step 1: Scan repository
            files = await workflow.execute_activity(
                scan_repository,
                request.repository_path,
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 2: Analyze code with AI
            analysis_results = await self._analyze_with_ai(files, request.analysis_type)

            # Step 3: Validate via Slack before sending to user
            validated = await self._validate_via_slack(analysis_results)

            # Step 4: Generate final result
            result = CodeAnalysisResult(
                repository=request.repository_path,
                analysis_type=request.analysis_type,
                issues_found=len(analysis_results.get("issues", [])),
                critical_issues=analysis_results.get("critical", []),
                recommendations=analysis_results.get("recommendations", []),
                refactoring_suggestions=[
                    "Extract common functionality",
                    "Improve error handling",
                ],
                validated=validated,
                validation_feedback=(
                    self._validation.feedback if self._validation else "timeout"
                ),
            )

        return result

    async def _analyze_with_ai(
        self, files: dict[str, list[str]], analysis_type: str
    ) -> dict[str, any]:
        """Analyze code using AI agents with tools and structured outputs."""
        workflow.logger.info(f"Analyzing code with AI ({analysis_type})")

        # Create tools from activities
        file_analysis_tool = temporal_agents.workflow.activity_as_tool(
            analyze_code_file, start_to_close_timeout=timedelta(seconds=30)
        )
        security_scan_tool = temporal_agents.workflow.activity_as_tool(
            run_security_scan, start_to_close_timeout=timedelta(seconds=30)
        )

        # Create analyzer agent with tools and structured output
        agent = Agent(
            name="Code Analyzer",
            model="gpt-5-mini",
            instructions=f"""You are a senior code reviewer and security expert.
            Analyze the codebase for {analysis_type} issues.

            For each issue found, specify:
            - The file where it was found
            - Severity level (critical, high, medium, low)
            - Clear description of the issue
            - Line number if applicable

            Provide:
            - Summary of overall findings
            - List of critical issues (need immediate attention)
            - List of other issues
            - Actionable recommendations
            - Refactoring suggestions
            - Overall quality score (0-10)

            Focus on being specific and actionable.""",
            tools=[file_analysis_tool, security_scan_tool],
            output_type=CodeAnalysisOutput,  # Structured output
        )

        # Run analysis
        analysis_input = f"""Analyze the following codebase:

Python files: {', '.join(files.get('python', []))}
JavaScript files: {', '.join(files.get('javascript', []))}

Analysis type: {analysis_type}

Provide a comprehensive analysis with specific issues and recommendations."""

        result = await Runner.run(agent, input=analysis_input, run_config=RunConfig())

        # Output is guaranteed to be CodeAnalysisOutput
        assert isinstance(result.final_output, CodeAnalysisOutput)
        analysis = result.final_output

        workflow.logger.info(
            f"Analysis complete: {len(analysis.critical_issues)} critical issues, "
            f"{len(analysis.other_issues)} other issues, "
            f"quality score: {analysis.overall_quality_score}/10"
        )

        # Format critical issues for easy access
        critical_issues_formatted = [
            f"{issue.file}: {issue.description} (Severity: {issue.severity})"
            for issue in analysis.critical_issues
        ]

        all_issues_formatted = [
            f"{issue.file}: {issue.description} (Severity: {issue.severity})"
            for issue in analysis.critical_issues + analysis.other_issues
        ]

        return {
            "summary": analysis.summary,
            "issues": all_issues_formatted,
            "critical": critical_issues_formatted,
            "recommendations": analysis.recommendations,
            "refactoring_suggestions": analysis.refactoring_suggestions,
            "quality_score": analysis.overall_quality_score,
        }

    async def _validate_via_slack(self, analysis_results: dict[str, any]) -> bool:
        """Validate analysis result via Slack before sending to user."""
        workflow.logger.info("Requesting validation via Slack")

        workflow_id = workflow.info().workflow_id

        # Format summary
        summary = f"""**Analysis Summary**

Critical Issues: {len(analysis_results.get('critical', []))}
Total Issues: {len(analysis_results.get('issues', []))}

**Top Recommendations:**
{chr(10).join(f"• {r}" for r in analysis_results.get('recommendations', [])[:3])}

**Full Analysis:**
{analysis_results.get('summary', 'N/A')[:500]}...
"""

        # Post to Slack
        self._thread_ts = await workflow.execute_activity(
            post_validation_request_to_slack,
            args=[summary, workflow_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Wait for validation (2 hour timeout)
        try:
            await workflow.wait_condition(
                lambda: self._validation is not None, timeout=timedelta(hours=2)
            )

            if self._validation and self._validation.approved:
                # Approved
                await workflow.execute_activity(
                    update_slack_thread,
                    args=[
                        self._thread_ts,
                        "human-in-loop",
                        f"✅ Validated by {self._validation.user}! Sending to user...",
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                return True
            else:
                # Not approved
                await workflow.execute_activity(
                    update_slack_thread,
                    args=[
                        self._thread_ts,
                        "human-in-loop",
                        f"❌ Not approved. Feedback: {self._validation.feedback if self._validation else 'timeout'}",
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                return False

        except asyncio.TimeoutError:
            workflow.logger.warning("Validation timeout - defaulting to approved")
            return True  # Auto-approve on timeout

    @workflow.signal
    async def receive_validation(self, validation: SlackValidation) -> None:
        """Receive validation from Slack."""
        workflow.logger.info(f"Received validation: {validation.approved}")
        self._validation = validation

    @workflow.query
    def get_status(self) -> dict:
        """Get workflow status."""
        return {
            "current_phase": ("scanning" if self._thread_ts is None else "validating"),
            "has_validation": self._validation is not None,
            "validated": self._validation.approved if self._validation else None,
            "thread_ts": self._thread_ts,
        }

    @workflow.query
    def get_thread_ts(self) -> str | None:
        """Get Slack thread timestamp."""
        return self._thread_ts
