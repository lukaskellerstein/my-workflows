"""
Temporal Worker for Kubernetes Deployment
This worker runs in a Kubernetes pod and processes workflow tasks.
Based on MY/0_simple/multiple_nodes.py
"""
import asyncio
import logging
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Activity 1: Validate input
@activity.defn
def validate_input(value: int) -> bool:
    activity.logger.info(f"Validating input: {value}")
    is_valid = value > 0
    activity.logger.info(f"Validation result: {is_valid}")
    return is_valid


# Activity 2: Transform data
@activity.defn
def transform_data(value: int) -> int:
    activity.logger.info(f"Transforming data: {value}")
    result = value * 3 + 10
    activity.logger.info(f"Transformed result: {result}")
    return result


# Activity 3: Save result
@activity.defn
def save_result(value: int) -> str:
    activity.logger.info(f"Saving result: {value}")
    return f"Successfully saved value: {value}"


# Workflow with multiple activity nodes
@workflow.defn
class MultipleNodesWorkflow:
    @workflow.run
    async def run(self, input_value: int) -> str:
        workflow.logger.info(f"Starting workflow with input: {input_value}")

        # Node 1: Validate input
        is_valid = await workflow.execute_activity(
            validate_input,
            input_value,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not is_valid:
            return "Input validation failed"

        # Node 2: Transform data
        transformed = await workflow.execute_activity(
            transform_data,
            input_value,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Node 3: Save result
        save_message = await workflow.execute_activity(
            save_result,
            transformed,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Workflow completed: {save_message}")
        return save_message


async def main():
    """Main worker function that runs in the Kubernetes pod"""

    # Get configuration from environment variables
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    task_queue = os.getenv("TASK_QUEUE", "k8s-multiple-nodes-task-queue")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")

    logger.info(f"Starting Temporal worker...")
    logger.info(f"  Temporal Host: {temporal_host}")
    logger.info(f"  Task Queue: {task_queue}")
    logger.info(f"  Namespace: {namespace}")

    # Connect to Temporal
    try:
        client = await Client.connect(
            temporal_host,
            namespace=namespace,
        )
        logger.info("Successfully connected to Temporal server")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal: {e}")
        sys.exit(1)

    # Create worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[MultipleNodesWorkflow],
        activities=[validate_input, transform_data, save_result],
        activity_executor=ThreadPoolExecutor(max_workers=10),
    )

    logger.info("Worker created successfully")
    logger.info(f"Registered workflows: {[MultipleNodesWorkflow.__name__]}")
    logger.info(f"Registered activities: {[validate_input.__name__, transform_data.__name__, save_result.__name__]}")

    # Handle graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(signum, _frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run worker
    logger.info("Worker starting - ready to process workflows!")
    logger.info("Press Ctrl+C to stop the worker")

    try:
        async with worker:
            # Wait for shutdown signal
            await shutdown_event.wait()
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
