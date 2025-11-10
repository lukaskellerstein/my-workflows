"""
Example 3: Workflow with IF Condition
This demonstrates conditional workflow execution based on runtime data.
Different activities are executed based on conditions.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


class ProcessingType(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    DETAILED = "detailed"


@dataclass
class ProcessingInput:
    value: int
    priority: str  # "high", "medium", "low"


# Fast processing activity
@activity.defn
def fast_process(value: int) -> str:
    activity.logger.info(f"Fast processing: {value}")
    result = value * 2
    return f"Fast result: {result}"


# Standard processing activity
@activity.defn
def standard_process(value: int) -> str:
    activity.logger.info(f"Standard processing: {value}")
    result = value * 3 + 5
    return f"Standard result: {result}"


# Detailed processing activity
@activity.defn
def detailed_process(value: int) -> str:
    activity.logger.info(f"Detailed processing: {value}")
    result = value * 5 + 10
    return f"Detailed result: {result}"


# Workflow with conditional logic
@workflow.defn
class ConditionalWorkflow:
    @workflow.run
    async def run(self, input_data: ProcessingInput) -> str:
        workflow.logger.info(
            f"Starting workflow with value={input_data.value}, priority={input_data.priority}"
        )

        # Determine processing type based on priority (IF condition)
        if input_data.priority == "high":
            # High priority: use fast processing
            result = await workflow.execute_activity(
                fast_process,
                input_data.value,
                start_to_close_timeout=timedelta(seconds=10),
            )
        elif input_data.priority == "medium":
            # Medium priority: use standard processing
            result = await workflow.execute_activity(
                standard_process,
                input_data.value,
                start_to_close_timeout=timedelta(seconds=10),
            )
        else:
            # Low priority or default: use detailed processing
            result = await workflow.execute_activity(
                detailed_process,
                input_data.value,
                start_to_close_timeout=timedelta(seconds=10),
            )

        workflow.logger.info(f"Workflow completed with: {result}")
        return result


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="0-simple-if-condition-task-queue",
        workflows=[ConditionalWorkflow],
        activities=[fast_process, standard_process, detailed_process],
        activity_executor=ThreadPoolExecutor(5),
    ):
        # Test with different priorities
        print("\n=== Testing HIGH priority ===")
        result1 = await client.execute_workflow(
            ConditionalWorkflow.run,
            ProcessingInput(value=10, priority="high"),
            id="0-simple-if-condition-workflow-high",
            task_queue="0-simple-if-condition-task-queue",
        )
        print(f"Result: {result1}")

        print("\n=== Testing MEDIUM priority ===")
        result2 = await client.execute_workflow(
            ConditionalWorkflow.run,
            ProcessingInput(value=10, priority="medium"),
            id="0-simple-if-condition-workflow-medium",
            task_queue="0-simple-if-condition-task-queue",
        )
        print(f"Result: {result2}")

        print("\n=== Testing LOW priority ===")
        result3 = await client.execute_workflow(
            ConditionalWorkflow.run,
            ProcessingInput(value=10, priority="low"),
            id="0-simple-if-condition-workflow-low",
            task_queue="0-simple-if-condition-task-queue",
        )
        print(f"Result: {result3}")


if __name__ == "__main__":
    asyncio.run(main())
