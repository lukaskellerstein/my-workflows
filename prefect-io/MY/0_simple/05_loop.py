"""
Example 4: Workflow with LOOP

Demonstrates loop patterns in workflows, including both sequential and parallel execution.
"""

from prefect import flow, task, get_run_logger


@task
def fetch_data(source_id: int) -> dict:
    """Fetches data from a source."""
    logger = get_run_logger()
    logger.info(f"Fetching data from source {source_id}")

    # Simulate fetching data
    return {
        "source_id": source_id,
        "data": [i * source_id for i in range(1, 6)],
        "timestamp": f"2024-01-{source_id:02d}"
    }


@task
def process_batch(batch: dict) -> dict:
    """Processes a single batch of data."""
    logger = get_run_logger()
    logger.info(f"Processing batch from source {batch['source_id']}")

    processed = {
        "source_id": batch["source_id"],
        "sum": sum(batch["data"]),
        "count": len(batch["data"]),
        "timestamp": batch["timestamp"]
    }

    return processed


@task
def aggregate_results(results: list[dict]) -> dict:
    """Aggregates all processed results."""
    logger = get_run_logger()
    logger.info(f"Aggregating {len(results)} results")

    total_sum = sum(r["sum"] for r in results)
    total_count = sum(r["count"] for r in results)

    return {
        "total_batches": len(results),
        "total_sum": total_sum,
        "total_count": total_count,
        "average": total_sum / total_count if total_count > 0 else 0
    }


@flow(name="Sequential Loop Workflow", log_prints=True)
def sequential_loop_flow(num_sources: int = 5):
    """A flow that processes multiple sources sequentially using a loop."""
    logger = get_run_logger()
    logger.info(f"Starting sequential processing of {num_sources} sources")

    results = []

    # Sequential loop - processes one at a time
    for source_id in range(1, num_sources + 1):
        print(f"Processing source {source_id}/{num_sources}")

        # Fetch and process data
        raw_data = fetch_data(source_id)
        processed = process_batch(raw_data)
        results.append(processed)

    # Aggregate all results
    final_result = aggregate_results(results)

    print(f"Sequential processing completed: {final_result}")
    return final_result


@flow(name="Parallel Loop Workflow", log_prints=True)
def parallel_loop_flow(num_sources: int = 5):
    """A flow that processes multiple sources in parallel using task mapping."""
    logger = get_run_logger()
    logger.info(f"Starting parallel processing of {num_sources} sources")

    # Generate source IDs
    source_ids = list(range(1, num_sources + 1))

    print(f"Fetching data from {num_sources} sources in parallel")

    # Parallel execution using map - all sources processed concurrently
    raw_data_list = fetch_data.map(source_ids)

    print("Processing batches in parallel")

    # Process all batches in parallel
    processed_results = process_batch.map(raw_data_list)

    # Aggregate results (waits for all parallel tasks to complete)
    final_result = aggregate_results(processed_results)

    print(f"Parallel processing completed: {final_result}")
    return final_result


@flow(name="Nested Loop Workflow", log_prints=True)
def nested_loop_flow(num_categories: int = 3, items_per_category: int = 4):
    """A flow demonstrating nested loops."""
    logger = get_run_logger()
    logger.info(f"Processing {num_categories} categories with {items_per_category} items each")

    all_results = []

    # Outer loop - categories
    for category_id in range(1, num_categories + 1):
        print(f"\nProcessing category {category_id}/{num_categories}")
        category_results = []

        # Inner loop - items within category
        for item_id in range(1, items_per_category + 1):
            source_id = category_id * 10 + item_id

            raw_data = fetch_data(source_id)
            processed = process_batch(raw_data)
            category_results.append(processed)

        # Aggregate category results
        category_summary = aggregate_results(category_results)
        category_summary["category_id"] = category_id
        all_results.append(category_summary)

        print(f"Category {category_id} summary: {category_summary}")

    print(f"\nProcessed {len(all_results)} categories")
    return all_results


if __name__ == "__main__":
    # Example 1: Sequential loop
    print("=== Test 1: Sequential Loop ===")
    sequential_loop_flow(num_sources=3)

    # Example 2: Parallel loop
    print("\n=== Test 2: Parallel Loop (Task Mapping) ===")
    parallel_loop_flow(num_sources=3)

    # Example 3: Nested loops
    print("\n=== Test 3: Nested Loops ===")
    nested_loop_flow(num_categories=2, items_per_category=3)
