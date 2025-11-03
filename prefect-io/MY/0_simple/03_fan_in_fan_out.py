"""
Example 3: Fan-In / Fan-Out Workflow

Demonstrates the fan-in/fan-out pattern where work is split into parallel
branches (fan-out) and then results are combined (fan-in).

This is a fundamental pattern for parallel processing and data pipelines.
"""

from prefect import flow, task, get_run_logger
import time


# ========== Fan-Out Tasks ==========

@task
def split_data(data: list[int], num_partitions: int = 3) -> list[list[int]]:
    """
    Splits data into partitions for parallel processing (Fan-Out).
    """
    logger = get_run_logger()
    logger.info(f"Splitting {len(data)} items into {num_partitions} partitions")

    partition_size = len(data) // num_partitions
    partitions = []

    for i in range(num_partitions):
        start = i * partition_size
        end = start + partition_size if i < num_partitions - 1 else len(data)
        partition = data[start:end]
        partitions.append(partition)

    logger.info(f"Created {len(partitions)} partitions")
    return partitions


# ========== Parallel Processing Tasks ==========

@task
def process_partition(partition: list[int], partition_id: int) -> dict:
    """
    Processes a single partition of data (runs in parallel).
    """
    logger = get_run_logger()
    logger.info(f"Processing partition {partition_id} with {len(partition)} items")

    time.sleep(0.5)  # Simulate processing time

    result = {
        "partition_id": partition_id,
        "count": len(partition),
        "sum": sum(partition),
        "avg": sum(partition) / len(partition) if partition else 0,
        "min": min(partition) if partition else 0,
        "max": max(partition) if partition else 0
    }

    logger.info(f"Partition {partition_id} processed: sum={result['sum']}")
    return result


# ========== Fan-In Task ==========

@task
def aggregate_results(partition_results: list[dict]) -> dict:
    """
    Aggregates results from all partitions (Fan-In).
    """
    logger = get_run_logger()
    logger.info(f"Aggregating results from {len(partition_results)} partitions")

    total_count = sum(r["count"] for r in partition_results)
    total_sum = sum(r["sum"] for r in partition_results)
    global_avg = total_sum / total_count if total_count > 0 else 0

    # Find global min and max
    all_mins = [r["min"] for r in partition_results if r["min"] > 0]
    all_maxs = [r["max"] for r in partition_results if r["max"] > 0]

    aggregated = {
        "total_partitions": len(partition_results),
        "total_items": total_count,
        "global_sum": total_sum,
        "global_avg": global_avg,
        "global_min": min(all_mins) if all_mins else 0,
        "global_max": max(all_maxs) if all_maxs else 0
    }

    logger.info(f"Aggregation complete: {total_count} items processed")
    return aggregated


# ========== Fan-In / Fan-Out Flow ==========

@flow(name="Fan-In / Fan-Out Flow", log_prints=True)
def fan_in_fan_out_flow(data: list[int] = None, num_partitions: int = 3):
    """
    Demonstrates the fan-in/fan-out pattern.

    Flow:
    1. Split data into partitions (fan-out)
    2. Process partitions in parallel (parallel execution)
    3. Aggregate results (fan-in)
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("FAN-IN / FAN-OUT PATTERN")
    print(f"{'='*70}\n")

    # Default data if none provided
    if data is None:
        data = list(range(1, 31))  # [1, 2, 3, ..., 30]

    print(f"Input: {len(data)} items")
    print(f"Partitions: {num_partitions}\n")

    # Step 1: Fan-Out - Split data into partitions
    print("Step 1: Fan-Out (splitting data)...")
    partitions = split_data(data, num_partitions)
    print(f"✓ Split into {len(partitions)} partitions\n")

    # Step 2: Parallel Processing - Process each partition
    print("Step 2: Parallel Processing (processing partitions)...")

    # Use .map() to process all partitions in parallel
    partition_ids = list(range(len(partitions)))
    results = process_partition.map(partitions, partition_ids)

    print(f"✓ Processed {len(results)} partitions in parallel\n")

    # Step 3: Fan-In - Aggregate all results
    print("Step 3: Fan-In (aggregating results)...")
    final_result = aggregate_results(results)

    print(f"✓ Aggregation complete\n")
    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Total items processed: {final_result['total_items']}")
    print(f"Global sum: {final_result['global_sum']}")
    print(f"Global average: {final_result['global_avg']:.2f}")
    print(f"Global min: {final_result['global_min']}")
    print(f"Global max: {final_result['global_max']}")
    print(f"{'='*70}")

    return final_result


# ========== Advanced Example: Multi-Stage Fan-In/Fan-Out ==========

@task
def extract_from_source(source_id: int) -> dict:
    """Extracts data from a source."""
    logger = get_run_logger()
    logger.info(f"Extracting from source {source_id}")
    time.sleep(0.3)

    return {
        "source_id": source_id,
        "records": [i * source_id for i in range(1, 11)]
    }


@task
def transform_records(data: dict, transformation: str) -> dict:
    """Transforms records with a specific transformation."""
    logger = get_run_logger()
    logger.info(f"Applying {transformation} to source {data['source_id']}")
    time.sleep(0.2)

    if transformation == "multiply":
        transformed = [r * 2 for r in data["records"]]
    elif transformation == "square":
        transformed = [r ** 2 for r in data["records"]]
    else:
        transformed = data["records"]

    return {
        "source_id": data["source_id"],
        "transformation": transformation,
        "records": transformed,
        "count": len(transformed)
    }


@task
def load_to_destination(transformed_data: list[dict], destination: str) -> dict:
    """Loads all transformed data to destination."""
    logger = get_run_logger()
    logger.info(f"Loading {len(transformed_data)} datasets to {destination}")
    time.sleep(0.5)

    total_records = sum(d["count"] for d in transformed_data)

    return {
        "destination": destination,
        "datasets_loaded": len(transformed_data),
        "total_records": total_records,
        "status": "success"
    }


@flow(name="Multi-Stage Fan-In/Fan-Out", log_prints=True)
def multi_stage_fan_in_fan_out_flow(num_sources: int = 4):
    """
    Advanced example with multiple fan-out/fan-in stages.

    Flow:
    1. Fan-out: Extract from multiple sources in parallel
    2. Fan-out: Transform each with multiple transformations in parallel
    3. Fan-in: Load all results to destination
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("MULTI-STAGE FAN-IN / FAN-OUT")
    print(f"{'='*70}\n")

    print(f"Processing {num_sources} sources with multiple transformations\n")

    # Stage 1: Fan-Out - Extract from multiple sources in parallel
    print("Stage 1: Fan-Out (extracting from sources)...")
    source_ids = list(range(1, num_sources + 1))
    extracted_data = extract_from_source.map(source_ids)
    print(f"✓ Extracted from {len(extracted_data)} sources\n")

    # Stage 2: Fan-Out Again - Apply multiple transformations to each source
    print("Stage 2: Fan-Out (applying transformations)...")

    # For each extracted dataset, apply multiple transformations
    transformations = ["multiply", "square"]
    all_transformed = []

    for data in extracted_data:
        # Fan-out: Apply each transformation in parallel
        transformed = transform_records.map(
            [data] * len(transformations),
            transformations
        )
        all_transformed.extend(transformed)

    print(f"✓ Applied {len(transformations)} transformations to {len(extracted_data)} sources")
    print(f"  Total transformed datasets: {len(all_transformed)}\n")

    # Stage 3: Fan-In - Load all transformed data
    print("Stage 3: Fan-In (loading to destination)...")
    load_result = load_to_destination(all_transformed, "data_warehouse")

    print(f"✓ Loaded to {load_result['destination']}\n")
    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Sources processed: {num_sources}")
    print(f"Transformations per source: {len(transformations)}")
    print(f"Total datasets: {load_result['datasets_loaded']}")
    print(f"Total records: {load_result['total_records']}")
    print(f"Status: {load_result['status']}")
    print(f"{'='*70}")

    return load_result


# ========== Real-World Example: Distributed Data Processing ==========

@task
def fetch_user_batch(batch_id: int, batch_size: int) -> dict:
    """Fetches a batch of user data."""
    logger = get_run_logger()
    logger.info(f"Fetching batch {batch_id} ({batch_size} users)")
    time.sleep(0.3)

    users = [
        {"id": batch_id * batch_size + i, "status": "active"}
        for i in range(batch_size)
    ]

    return {"batch_id": batch_id, "users": users}


@task
def enrich_user_data(user_batch: dict) -> dict:
    """Enriches user data with additional information."""
    logger = get_run_logger()
    logger.info(f"Enriching batch {user_batch['batch_id']}")
    time.sleep(0.2)

    enriched_users = []
    for user in user_batch["users"]:
        enriched_users.append({
            **user,
            "tier": "premium" if user["id"] % 3 == 0 else "standard",
            "region": "US" if user["id"] % 2 == 0 else "EU"
        })

    return {
        "batch_id": user_batch["batch_id"],
        "users": enriched_users,
        "count": len(enriched_users)
    }


@task
def save_batch_results(enriched_batches: list[dict]) -> dict:
    """Saves all enriched batches to database."""
    logger = get_run_logger()
    logger.info(f"Saving {len(enriched_batches)} batches to database")
    time.sleep(0.5)

    total_users = sum(batch["count"] for batch in enriched_batches)
    premium_users = sum(
        sum(1 for user in batch["users"] if user["tier"] == "premium")
        for batch in enriched_batches
    )

    return {
        "batches_saved": len(enriched_batches),
        "total_users": total_users,
        "premium_users": premium_users,
        "standard_users": total_users - premium_users
    }


@flow(name="Distributed User Processing", log_prints=True)
def distributed_user_processing_flow(total_users: int = 100, batch_size: int = 20):
    """
    Real-world example: Process large number of users in batches.

    Pattern:
    1. Fan-out: Fetch users in parallel batches
    2. Parallel: Enrich each batch with additional data
    3. Fan-in: Save all enriched batches
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DISTRIBUTED USER PROCESSING")
    print(f"{'='*70}\n")

    num_batches = (total_users + batch_size - 1) // batch_size
    print(f"Processing {total_users} users in {num_batches} batches of {batch_size}\n")

    # Fan-Out: Fetch all batches in parallel
    print("Phase 1: Fan-Out (fetching user batches)...")
    batch_ids = list(range(num_batches))
    user_batches = fetch_user_batch.map(batch_ids, [batch_size] * num_batches)
    print(f"✓ Fetched {len(user_batches)} batches in parallel\n")

    # Parallel Processing: Enrich each batch
    print("Phase 2: Parallel Processing (enriching user data)...")
    enriched_batches = enrich_user_data.map(user_batches)
    print(f"✓ Enriched {len(enriched_batches)} batches\n")

    # Fan-In: Save all results
    print("Phase 3: Fan-In (saving to database)...")
    save_result = save_batch_results(enriched_batches)

    print(f"✓ Saved to database\n")
    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Total users processed: {save_result['total_users']}")
    print(f"Premium users: {save_result['premium_users']}")
    print(f"Standard users: {save_result['standard_users']}")
    print(f"Batches: {save_result['batches_saved']}")
    print(f"{'='*70}")

    return save_result


# ========== Comprehensive Demo ==========

@flow(name="Fan-In/Fan-Out Comprehensive Demo", log_prints=True)
def comprehensive_fan_in_fan_out_demo():
    """Runs all fan-in/fan-out examples."""
    print("="*70)
    print("COMPREHENSIVE FAN-IN / FAN-OUT DEMONSTRATION")
    print("="*70)

    # Example 1: Basic fan-in/fan-out
    print("\n\nEXAMPLE 1: Basic Fan-In / Fan-Out")
    print("="*70)
    fan_in_fan_out_flow(data=list(range(1, 31)), num_partitions=3)

    # Example 2: Multi-stage
    print("\n\nEXAMPLE 2: Multi-Stage Fan-In / Fan-Out")
    print("="*70)
    multi_stage_fan_in_fan_out_flow(num_sources=4)

    # Example 3: Real-world example
    print("\n\nEXAMPLE 3: Distributed User Processing")
    print("="*70)
    distributed_user_processing_flow(total_users=100, batch_size=20)

    print("\n" + "="*70)
    print("All fan-in/fan-out examples completed")
    print("="*70)


if __name__ == "__main__":
    comprehensive_fan_in_fan_out_demo()
