"""
Content Generation Workflow - Generates content with AI, validates output via Slack
Uses OpenAI Agents SDK for content creation, SEO optimization, and quality review
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
class ContentRequest:
    """Content generation request."""

    topic: str
    content_type: str  # 'blog', 'documentation', 'marketing', 'technical'
    target_audience: str
    tone: str  # 'professional', 'casual', 'technical', 'friendly'
    length: str  # 'short', 'medium', 'long'
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
class ContentResult:
    """Generated content result."""

    topic: str
    content_type: str
    generated_content: str
    seo_keywords: list[str]
    readability_score: float
    word_count: int
    validated: bool
    validation_feedback: str


# Structured output models for LLM responses


class ContentOutput(BaseModel):
    """Structured output for generated content."""

    title: str = Field(description="Compelling title for the content")
    introduction: str = Field(description="Engaging introduction paragraph")
    main_body: str = Field(description="Main content body with all sections")
    conclusion: str = Field(description="Concluding paragraph with call-to-action")
    meta_description: str = Field(
        max_length=160, description="SEO meta description (max 160 chars)"
    )
    tags: list[str] = Field(description="Relevant tags or categories for the content")
    estimated_reading_time: int = Field(description="Estimated reading time in minutes")


# Activities


@activity.defn
async def generate_outline(topic: str, content_type: str, audience: str) -> str:
    """Generate content outline using AI."""
    activity.logger.info(f"Generating outline for: {topic}")

    # Simulate outline generation
    await asyncio.sleep(2)

    outline = f"""Content Outline: {topic}

1. Introduction
   - Hook the reader
   - Set context

2. Main Points
   - Point A: Key concept 1
   - Point B: Key concept 2
   - Point C: Key concept 3

3. Examples and Use Cases
   - Real-world example 1
   - Real-world example 2

4. Best Practices
   - Tip 1
   - Tip 2

5. Conclusion
   - Summary
   - Call to action
"""

    return outline


@activity.defn
async def perform_seo_research(topic: str) -> dict[str, list[str]]:
    """Perform SEO keyword research."""
    activity.logger.info(f"Researching SEO keywords for: {topic}")

    # Simulate SEO research
    await asyncio.sleep(2)

    return {
        "primary_keywords": [topic.lower(), f"{topic} guide", f"{topic} tutorial"],
        "secondary_keywords": [
            f"best {topic}",
            f"{topic} examples",
            f"{topic} tips",
        ],
        "long_tail_keywords": [
            f"how to {topic}",
            f"what is {topic}",
            f"{topic} best practices",
        ],
    }


@activity.defn
async def check_readability(content: str) -> dict[str, float]:
    """Check content readability."""
    activity.logger.info("Checking readability")

    # Simulate readability check
    await asyncio.sleep(1)

    return {
        "flesch_reading_ease": 65.5,
        "flesch_kincaid_grade": 8.2,
        "word_count": len(content.split()),
    }


@activity.defn(name="post_content_validation_to_slack")
async def post_validation_request_to_slack(
    content: str, metadata: dict, workflow_id: str, channel: str = "human-in-loop"
) -> str:
    """Post content to Slack for validation before sending to user."""
    activity.logger.info("Posting validation request to Slack")

    try:
        import os

        from slack_sdk.web.async_client import AsyncWebClient

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")

        client = AsyncWebClient(token=slack_token)

        # Truncate content for Slack
        preview = content[:1000] + "..." if len(content) > 1000 else content

        response = await client.chat_postMessage(
            channel=channel,
            text="*Content Validation*",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*📝 Content Generation Complete - Validation Needed*",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"**Topic:** {metadata.get('topic', 'N/A')}\n**Type:** {metadata.get('type', 'N/A')}\n**Word Count:** {metadata.get('word_count', 0)}",
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"**Content Preview:**\n```{preview}```",
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


@activity.defn(name="update_content_slack_thread")
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
class ContentGenerationWorkflow:
    """
    Content generation workflow that:
    1. Generates content outline
    2. Creates content using AI
    3. Performs SEO optimization
    4. Validates result via Slack before sending to user
    """

    def __init__(self) -> None:
        self._validation: SlackValidation | None = None
        self._thread_ts: str | None = None

    @workflow.run
    async def run(self, request: ContentRequest) -> ContentResult:
        """Execute content generation workflow."""
        workflow.logger.info(f"Starting content generation: {request.topic}")

        with trace("Content generation workflow"):
            # Step 1: Research and planning
            outline, seo_data = await self._research_and_plan(request)

            # Step 2: Generate content
            content = await self._generate_content(request, outline, seo_data)

            # Step 3: Quality check
            quality_metrics = await workflow.execute_activity(
                check_readability,
                content,
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Step 4: Validate via Slack before sending to user
            validated = await self._validate_via_slack(
                content, request, quality_metrics
            )

            # Step 5: Generate result
            result = ContentResult(
                topic=request.topic,
                content_type=request.content_type,
                generated_content=content,
                seo_keywords=seo_data.get("primary_keywords", []),
                readability_score=quality_metrics.get("flesch_reading_ease", 0.0),
                word_count=quality_metrics.get("word_count", 0),
                validated=validated,
                validation_feedback=(
                    self._validation.feedback if self._validation else "timeout"
                ),
            )

        return result

    async def _research_and_plan(
        self, request: ContentRequest
    ) -> tuple[str, dict[str, list[str]]]:
        """Research topic and create plan."""
        workflow.logger.info("Researching and planning content")

        # Run in parallel
        outline_task = workflow.execute_activity(
            generate_outline,
            args=[request.topic, request.content_type, request.target_audience],
            start_to_close_timeout=timedelta(seconds=30),
        )

        seo_task = workflow.execute_activity(
            perform_seo_research,
            request.topic,
            start_to_close_timeout=timedelta(seconds=30),
        )

        outline, seo_data = await asyncio.gather(outline_task, seo_task)

        return outline, seo_data

    async def _generate_content(
        self, request: ContentRequest, outline: str, seo_data: dict[str, list[str]]
    ) -> str:
        """Generate content using AI with structured outputs."""
        workflow.logger.info("Generating content with AI")

        # Create content writer agent with tools and structured output
        readability_tool = temporal_agents.workflow.activity_as_tool(
            check_readability, start_to_close_timeout=timedelta(seconds=30)
        )

        agent = Agent(
            name="Content Writer",
            model="gpt-5-mini",
            instructions=f"""You are a professional {request.content_type} writer.
            Write engaging, informative content for {request.target_audience} audience.
            Use a {request.tone} tone.
            Target length: {request.length}.

            Provide:
            - Compelling title
            - Engaging introduction
            - Well-structured main body content
            - Strong conclusion with call-to-action
            - SEO-optimized meta description (max 160 characters)
            - Relevant tags
            - Estimated reading time

            Incorporate SEO keywords naturally.
            Focus on clarity, accuracy, and readability.""",
            tools=[readability_tool],
            output_type=ContentOutput,  # Structured output
        )

        # Generate content
        content_input = f"""Topic: {request.topic}

Outline:
{outline}

Primary Keywords: {', '.join(seo_data.get('primary_keywords', []))}
Secondary Keywords: {', '.join(seo_data.get('secondary_keywords', []))}

Please write comprehensive, engaging content following the outline."""

        result = await Runner.run(agent, input=content_input, run_config=RunConfig())

        # Output is guaranteed to be ContentOutput
        assert isinstance(result.final_output, ContentOutput)
        content = result.final_output

        workflow.logger.info(
            f"Content generated: '{content.title}' "
            f"({content.estimated_reading_time} min read, {len(content.tags)} tags)"
        )

        # Format structured content into readable string
        formatted_content = f"""# {content.title}

{content.introduction}

{content.main_body}

{content.conclusion}

---
**Tags:** {', '.join(content.tags)}
**Reading Time:** {content.estimated_reading_time} minutes
**Meta Description:** {content.meta_description}
"""

        return formatted_content

    async def _validate_via_slack(
        self, content: str, request: ContentRequest, metrics: dict
    ) -> bool:
        """Validate content via Slack before sending to user."""
        workflow.logger.info("Requesting validation via Slack")

        workflow_id = workflow.info().workflow_id

        # Post to Slack for validation
        metadata = {
            "topic": request.topic,
            "type": request.content_type,
            "word_count": metrics.get("word_count", 0),
        }

        self._thread_ts = await workflow.execute_activity(
            post_validation_request_to_slack,
            args=[content, metadata, workflow_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Wait for validation (24 hour timeout)
        try:
            await workflow.wait_condition(
                lambda: self._validation is not None, timeout=timedelta(hours=24)
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
        workflow.logger.info(f"Received validation: approved={validation.approved}")
        self._validation = validation

    @workflow.query
    def get_status(self) -> dict:
        """Get workflow status."""
        return {
            "current_phase": (
                "generating" if self._thread_ts is None else "validating"
            ),
            "has_validation": self._validation is not None,
            "validated": self._validation.approved if self._validation else None,
            "thread_ts": self._thread_ts,
        }

    @workflow.query
    def get_thread_ts(self) -> str | None:
        """Get Slack thread timestamp."""
        return self._thread_ts
