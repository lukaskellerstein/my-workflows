"""
Workflow and Activity Definitions - Slack Human in the Loop
Posts questions to Slack, waits for text responses, and executes different paths.
"""
import asyncio
import os
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow


@dataclass
class Question:
    """A question to post to Slack."""

    text: str
    context: str
    channel: str = "human-in-loop"


@dataclass
class SlackAnswer:
    """Answer received from Slack."""

    text: str
    user: str
    user_id: str
    timestamp: str
    thread_ts: str


# Activities


@activity.defn
async def post_question_to_slack(question: Question, workflow_id: str) -> str:
    """
    Post a question to Slack channel and return message timestamp.

    Args:
        question: The question to post
        workflow_id: Workflow ID for tracking

    Returns:
        Message timestamp (thread_ts) for receiving replies
    """
    activity.logger.info(f"Posting question to Slack: {question.text}")

    try:
        from slack_sdk.web.async_client import AsyncWebClient

        slack_token = os.getenv("SLACK_BOT_TOKEN")

        if not slack_token:
            activity.logger.error("SLACK_BOT_TOKEN not set - cannot post to Slack")
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")

        client = AsyncWebClient(token=slack_token)

        # Post message
        response = await client.chat_postMessage(
            channel=question.channel,
            text=f"*Question:* {question.text}",
            blocks=[
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*Question:*"}},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"_{question.text}_"},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Context:*\n{question.context}"},
                },
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"💬 Please reply in thread with your answer\n🆔 Workflow: `{workflow_id}`",
                        }
                    ],
                },
            ],
        )

        thread_ts = response["ts"]
        activity.logger.info(f"Posted to Slack successfully. Thread TS: {thread_ts}")
        return thread_ts

    except ImportError:
        activity.logger.error("slack_sdk not installed - run: uv add slack-sdk aiohttp")
        raise ImportError("slack_sdk is required. Install with: uv add slack-sdk aiohttp")
    except Exception as e:
        activity.logger.error(f"Failed to post to Slack: {e}")
        raise


@activity.defn
async def update_slack_thread(thread_ts: str, channel: str, message: str) -> None:
    """
    Post an update message in the Slack thread.

    Args:
        thread_ts: Thread timestamp to reply to
        channel: Channel where the thread is
        message: Message to post
    """
    activity.logger.info(f"Updating Slack thread: {thread_ts}")

    try:
        from slack_sdk.web.async_client import AsyncWebClient

        slack_token = os.getenv("SLACK_BOT_TOKEN")

        if not slack_token:
            activity.logger.error("SLACK_BOT_TOKEN not set - cannot update thread")
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")

        client = AsyncWebClient(token=slack_token)

        # Post reply in thread
        await client.chat_postMessage(
            channel=channel, thread_ts=thread_ts, text=message
        )

        activity.logger.info("Slack thread updated successfully")

    except ImportError:
        activity.logger.error("slack_sdk not installed - run: uv add slack-sdk aiohttp")
        raise ImportError("slack_sdk is required. Install with: uv add slack-sdk aiohttp")
    except Exception as e:
        activity.logger.error(f"Failed to update Slack thread: {e}")
        raise


@activity.defn
def execute_path_yes(context: str) -> str:
    """Execute Path 1 when answer is 'yes'."""
    activity.logger.info(f"Executing Path: YES for context: {context}")
    # Simulate path 1 work
    result = f"✅ Path YES executed successfully\nContext: {context}\nAction: Proceeding with approved workflow"
    activity.logger.info(result)
    return result


@activity.defn
def execute_path_no(context: str, answer: str) -> str:
    """Execute Path 2 when answer is anything other than 'yes'."""
    activity.logger.info(f"Executing Path: NO for context: {context}, answer: {answer}")
    # Simulate path 2 work
    result = f"❌ Path NO executed\nContext: {context}\nAnswer received: '{answer}'\nAction: Taking alternative workflow path"
    activity.logger.info(result)
    return result


# Main Workflow


@workflow.defn
class SlackQuestionWorkflow:
    """
    Workflow that posts a question to Slack and waits for a text answer.

    Based on the answer:
    - "yes" (case-insensitive) → Execute Path YES
    - Anything else → Execute Path NO
    """

    def __init__(self) -> None:
        self._answer: SlackAnswer | None = None
        self._thread_ts: str | None = None

    @workflow.run
    async def run(self, question: Question) -> str:
        """Execute workflow with Slack question."""
        workflow.logger.info(f"Starting Slack question workflow: {question.text}")

        workflow_id = workflow.info().workflow_id

        # Step 1: Post question to Slack
        self._thread_ts = await workflow.execute_activity(
            post_question_to_slack,
            args=[question, workflow_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info(f"Posted to Slack, thread_ts: {self._thread_ts}")

        # Step 2: Wait for answer (with timeout)
        workflow.logger.info("Waiting for Slack answer...")

        try:
            await workflow.wait_condition(
                lambda: self._answer is not None,
                timeout=timedelta(hours=2),  # 2-hour response window
            )
            workflow.logger.info(
                f"Received answer: '{self._answer.text}' from {self._answer.user}"
            )
        except asyncio.TimeoutError:
            workflow.logger.warning("Answer timeout - defaulting to NO path")
            self._answer = SlackAnswer(
                text="timeout",
                user="system",
                user_id="system",
                timestamp="timeout",
                thread_ts=self._thread_ts or "unknown",
            )

        # Step 3: Determine path based on answer
        answer_text = self._answer.text.strip().lower()
        is_yes = answer_text == "yes"

        # Step 4: Update Slack thread
        await workflow.execute_activity(
            update_slack_thread,
            args=[
                self._thread_ts,
                question.channel,
                f"✅ Answer received from <@{self._answer.user_id}>: *{self._answer.text}*\n"
                f"Executing path: *{'YES' if is_yes else 'NO'}*",
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 5: Execute appropriate path
        if is_yes:
            workflow.logger.info("Executing Path YES")
            result = await workflow.execute_activity(
                execute_path_yes,
                question.context,
                start_to_close_timeout=timedelta(seconds=30),
            )
        else:
            workflow.logger.info(f"Executing Path NO (answer was: {answer_text})")
            result = await workflow.execute_activity(
                execute_path_no,
                args=[question.context, self._answer.text],
                start_to_close_timeout=timedelta(seconds=30),
            )

        # Final update to Slack
        await workflow.execute_activity(
            update_slack_thread,
            args=[self._thread_ts, question.channel, f"🎉 Workflow completed!\n\n{result}"],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return f"Answer: '{self._answer.text}' by {self._answer.user}\n{result}"

    @workflow.signal
    async def receive_answer(self, answer: SlackAnswer) -> None:
        """Signal to receive answer from Slack."""
        workflow.logger.info(f"Received answer signal: '{answer.text}' from {answer.user}")
        self._answer = answer

    @workflow.query
    def get_status(self) -> dict:
        """Query to check current status."""
        return {
            "has_answer": self._answer is not None,
            "answer": self._answer.text if self._answer else None,
            "user": self._answer.user if self._answer else None,
            "thread_ts": self._thread_ts,
        }

    @workflow.query
    def get_thread_ts(self) -> str | None:
        """Query to get the Slack thread timestamp."""
        return self._thread_ts
