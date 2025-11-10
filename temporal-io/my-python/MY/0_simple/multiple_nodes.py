"""
Example 2: Multiple Nodes Workflow
This demonstrates a workflow with multiple activities executed sequentially.
Each activity represents a node in the workflow.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


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
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="0-simple-multiple-nodes-task-queue",
        workflows=[MultipleNodesWorkflow],
        activities=[validate_input, transform_data, save_result],
        activity_executor=ThreadPoolExecutor(5),
    ):
        # Execute the workflow
        result = await client.execute_workflow(
            MultipleNodesWorkflow.run,
            15,
            id="0-simple-multiple-nodes-workflow",
            task_queue="0-simple-multiple-nodes-task-queue",
        )
        print(f"Workflow result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
