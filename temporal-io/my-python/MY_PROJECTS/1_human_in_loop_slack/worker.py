"""
Worker Script - Slack Human in the Loop
Runs the Temporal worker that processes Slack question workflows.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from workflow_definitions import (
    SlackQuestionWorkflow,
    execute_path_no,
    execute_path_yes,
    post_question_to_slack,
    update_slack_thread,
)

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "slack-question-task-queue"
MAX_CONCURRENT_ACTIVITIES = 10


async def main():
    """Start and run the worker."""
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    print(f"Connected to Temporal at {TEMPORAL_HOST}")

    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SlackQuestionWorkflow],
        activities=[
            post_question_to_slack,
            update_slack_thread,
            execute_path_yes,
            execute_path_no,
        ],
        activity_executor=ThreadPoolExecutor(MAX_CONCURRENT_ACTIVITIES),
    )

    print(f"Worker started on task queue: {TASK_QUEUE}")
    print(f"Max concurrent activities: {MAX_CONCURRENT_ACTIVITIES}")
    print("\nRegistered workflows:")
    print("  - SlackQuestionWorkflow (posts questions, waits for text answers)")
    print("\nRegistered activities:")
    print("  - post_question_to_slack: Post question to Slack")
    print("  - update_slack_thread: Update thread with status")
    print("  - execute_path_yes: Execute YES path")
    print("  - execute_path_no: Execute NO path")
    print("\n" + "=" * 60)
    print("NOTE: Ensure SLACK_BOT_TOKEN is set for Slack integration")
    print("Channel: #human-in-loop")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the worker\n")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
