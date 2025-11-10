"""
Example 3: Fan-In, Fan-Out Workflow
This demonstrates parallel execution pattern where:
- Fan-Out: Multiple tasks are started in parallel
- Fan-In: Results from parallel tasks are collected and aggregated

This pattern is useful for:
- Parallel data processing
- Distributed computations
- Concurrent API calls
- Batch operations
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
class DataChunk:
    chunk_id: int
    data: List[int]


@dataclass
class ProcessingResult:
    chunk_id: int
    sum: int
    average: float
    max_value: int
    min_value: int


# Activities for parallel processing


@activity.defn
def process_chunk(chunk: DataChunk) -> ProcessingResult:
    """
    Process a chunk of data. This activity will run in parallel.
    Simulates expensive computation that benefits from parallelization.
    """
    activity.logger.info(f"Processing chunk {chunk.chunk_id} with {len(chunk.data)} items")

    # Simulate some computation
    total = sum(chunk.data)
    avg = total / len(chunk.data) if chunk.data else 0
    max_val = max(chunk.data) if chunk.data else 0
    min_val = min(chunk.data) if chunk.data else 0

    result = ProcessingResult(
        chunk_id=chunk.chunk_id,
        sum=total,
        average=avg,
        max_value=max_val,
        min_value=min_val,
    )

    activity.logger.info(
        f"Chunk {chunk.chunk_id} processed: sum={total}, avg={avg:.2f}"
    )
    return result


@activity.defn
def aggregate_results(results: List[ProcessingResult]) -> str:
    """
    Aggregate results from all parallel tasks (Fan-In).
    """
    activity.logger.info(f"Aggregating {len(results)} results")

    total_sum = sum(r.sum for r in results)
    overall_avg = sum(r.average for r in results) / len(results) if results else 0
    global_max = max(r.max_value for r in results) if results else 0
    global_min = min(r.min_value for r in results) if results else 0

    summary = f"""
Aggregated Results:
  - Total chunks processed: {len(results)}
  - Total sum across all chunks: {total_sum}
  - Overall average: {overall_avg:.2f}
  - Global maximum: {global_max}
  - Global minimum: {global_min}
"""
    return summary.strip()


# Workflow with Fan-Out/Fan-In pattern


@workflow.defn
class FanOutFanInWorkflow:
    @workflow.run
    async def run(self, data: List[int], chunk_size: int = 10) -> str:
        workflow.logger.info(
            f"Starting Fan-Out/Fan-In workflow with {len(data)} items"
        )

        # Step 1: Split data into chunks (preparation for fan-out)
        chunks: List[DataChunk] = []
        for i in range(0, len(data), chunk_size):
            chunk_data = data[i : i + chunk_size]
            chunks.append(DataChunk(chunk_id=len(chunks), data=chunk_data))

        workflow.logger.info(f"Split data into {len(chunks)} chunks")

        # Step 2: FAN-OUT - Process all chunks in parallel
        workflow.logger.info("FAN-OUT: Starting parallel processing")

        # Use asyncio.gather to execute activities in parallel
        chunk_results = await asyncio.gather(*[
            workflow.execute_activity(
                process_chunk,
                chunk,
                start_to_close_timeout=timedelta(seconds=10),
            )
            for chunk in chunks
        ])

        workflow.logger.info(f"FAN-OUT completed: {len(chunk_results)} results received")

        # Step 3: FAN-IN - Aggregate all results
        workflow.logger.info("FAN-IN: Aggregating results")

        aggregated = await workflow.execute_activity(
            aggregate_results,
            chunk_results,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info("Workflow completed")
        return aggregated


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="0-simple-fan-out-fan-in-task-queue",
        workflows=[FanOutFanInWorkflow],
        activities=[process_chunk, aggregate_results],
        activity_executor=ThreadPoolExecutor(20),  # Allow many parallel activities
    ):
        # Generate sample data
        # Simulating a large dataset that benefits from parallel processing
        data = list(range(1, 101))  # Numbers 1 to 100

        print("=== Fan-Out / Fan-In Pattern Demo ===\n")
        print(f"Processing {len(data)} numbers in parallel chunks")
        print(f"Data: {data[:10]}...{data[-10:]}")
        print()

        # Execute the workflow
        result = await client.execute_workflow(
            FanOutFanInWorkflow.run,
            args=[data, 10],  # Pass multiple args as a list
            id="0-simple-fan-out-fan-in-workflow",
            task_queue="0-simple-fan-out-fan-in-task-queue",
        )

        print("Result:")
        print(result)

        print("\n" + "=" * 50)
        print("\n=== Pattern Explanation ===")
        print("""
This workflow demonstrates:

1. FAN-OUT Phase:
   - Data is split into chunks
   - Each chunk is processed by a separate activity
   - All activities run in PARALLEL (using asyncio.gather)
   - Significantly faster than sequential processing

2. FAN-IN Phase:
   - Results from all parallel activities are collected
   - A single aggregation activity combines all results
   - Produces final summary

Benefits:
✓ Faster processing through parallelization
✓ Efficient use of resources
✓ Scalable to large datasets
✓ Natural handling of independent tasks
        """)


if __name__ == "__main__":
    asyncio.run(main())
