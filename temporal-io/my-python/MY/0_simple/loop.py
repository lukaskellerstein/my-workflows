"""
Example 4: Workflow with LOOP
This demonstrates a workflow that executes activities in a loop.
Useful for batch processing or iterating over collections.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class Item:
    id: int
    name: str
    value: float


# Activity to process a single item
@activity.defn
def process_item(item: Item) -> str:
    activity.logger.info(f"Processing item: {item.name}")
    # Simulate processing
    processed_value = item.value * 1.1  # Add 10%
    return f"Processed {item.name}: ${processed_value:.2f}"


# Activity to aggregate results
@activity.defn
def aggregate_results(results: List[str]) -> str:
    activity.logger.info(f"Aggregating {len(results)} results")
    total_count = len(results)
    return f"Successfully processed {total_count} items"


# Workflow with loop
@workflow.defn
class LoopWorkflow:
    @workflow.run
    async def run(self, items: List[Item]) -> str:
        workflow.logger.info(f"Starting workflow with {len(items)} items")

        # Loop through items and process each one
        results: List[str] = []
        for item in items:
            workflow.logger.info(f"Processing item {item.id}: {item.name}")

            result = await workflow.execute_activity(
                process_item,
                item,
                start_to_close_timeout=timedelta(seconds=10),
            )
            results.append(result)

        # Aggregate all results
        summary = await workflow.execute_activity(
            aggregate_results,
            results,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Workflow completed: {summary}")

        # Return summary with all results
        return f"{summary}\n" + "\n".join(results)


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="0-simple-loop-task-queue",
        workflows=[LoopWorkflow],
        activities=[process_item, aggregate_results],
        activity_executor=ThreadPoolExecutor(5),
    ):
        # Create sample items
        items = [
            Item(id=1, name="Widget A", value=100.0),
            Item(id=2, name="Widget B", value=150.0),
            Item(id=3, name="Widget C", value=200.0),
            Item(id=4, name="Widget D", value=175.0),
            Item(id=5, name="Widget E", value=125.0),
        ]

        # Execute the workflow
        result = await client.execute_workflow(
            LoopWorkflow.run,
            items,
            id="0-simple-loop-workflow",
            task_queue="0-simple-loop-task-queue",
        )
        print(f"\nWorkflow result:\n{result}")


if __name__ == "__main__":
    asyncio.run(main())
