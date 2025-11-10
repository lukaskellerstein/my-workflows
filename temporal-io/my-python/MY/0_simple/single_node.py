"""
Example 1: Single Node Workflow
This demonstrates the simplest possible workflow with a single activity.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# Single activity that processes data
@activity.defn
def process_data(input_value: int) -> int:
    activity.logger.info(f"Processing data: {input_value}")
    result = input_value * 2
    activity.logger.info(f"Result: {result}")
    return result


# Workflow with a single activity node
@workflow.defn
class SingleNodeWorkflow:
    @workflow.run
    async def run(self, input_value: int) -> int:
        workflow.logger.info(f"Starting workflow with input: {input_value}")

        # Execute single activity
        result = await workflow.execute_activity(
            process_data,
            input_value,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Workflow completed with result: {result}")
        return result


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="0-simple-single-node-task-queue",
        workflows=[SingleNodeWorkflow],
        activities=[process_data],
        activity_executor=ThreadPoolExecutor(5),
    ):
        # Execute the workflow
        result = await client.execute_workflow(
            SingleNodeWorkflow.run,
            42,
            id="0-simple-single-node-workflow",
            task_queue="0-simple-single-node-task-queue",
        )
        print(f"Workflow result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
