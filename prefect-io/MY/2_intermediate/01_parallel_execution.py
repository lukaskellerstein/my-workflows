"""
Example: Parallel Execution

Demonstrates various concurrency patterns for parallel task execution in Prefect.
"""

import time
import asyncio
import httpx
from prefect import flow, task, get_run_logger
from prefect.task_runners import ThreadPoolTaskRunner


# ========== Sequential vs Parallel Tasks ==========

@task
def slow_operation(item_id: int, duration: float = 1.0) -> dict:
    """Simulates a slow operation (e.g., API call, database query)."""
    logger = get_run_logger()
    logger.info(f"Processing item {item_id}...")

    time.sleep(duration)

    return {
        "item_id": item_id,
        "processed_at": time.time(),
        "duration": duration
    }


@flow(name="Sequential Flow", log_prints=True)
def sequential_flow(num_items: int = 5):
    """Processes items sequentially (one at a time)."""
    logger = get_run_logger()
    print(f"\n=== Sequential Processing of {num_items} items ===")

    start_time = time.time()
    results = []

    # Sequential execution - each task waits for previous to complete
    for i in range(num_items):
        result = slow_operation(i, duration=0.5)
        results.append(result)

    elapsed = time.time() - start_time
    print(f"✓ Sequential processing completed in {elapsed:.2f} seconds")

    return {"results": results, "elapsed_time": elapsed}


@flow(name="Parallel Flow with Map", log_prints=True)
def parallel_flow_with_map(num_items: int = 5):
    """Processes items in parallel using task.map()."""
    logger = get_run_logger()
    print(f"\n=== Parallel Processing of {num_items} items (using map) ===")

    start_time = time.time()

    # Parallel execution using map - all tasks run concurrently
    item_ids = list(range(num_items))
    results = slow_operation.map(item_ids, duration=[0.5] * num_items)

    elapsed = time.time() - start_time
    print(f"✓ Parallel processing completed in {elapsed:.2f} seconds")
    print(f"Speedup: {(num_items * 0.5) / elapsed:.2f}x faster")

    return {"results": results, "elapsed_time": elapsed}


# ========== Thread Pool Task Runner ==========

@task
def cpu_intensive_task(n: int) -> dict:
    """Simulates CPU-intensive work."""
    logger = get_run_logger()
    logger.info(f"Computing Fibonacci({n})...")

    def fibonacci(num):
        if num <= 1:
            return num
        return fibonacci(num - 1) + fibonacci(num - 2)

    start = time.time()
    result = fibonacci(n)
    elapsed = time.time() - start

    return {"n": n, "result": result, "time": elapsed}


@flow(
    name="Thread Pool Flow",
    task_runner=ThreadPoolTaskRunner(max_workers=5),
    log_prints=True
)
def thread_pool_flow():
    """Uses ThreadPoolTaskRunner for concurrent execution."""
    logger = get_run_logger()
    print("\n=== Thread Pool Execution ===")

    numbers = [25, 26, 27, 28, 29]

    start_time = time.time()

    # Tasks automatically run in thread pool
    results = cpu_intensive_task.map(numbers)

    elapsed = time.time() - start_time
    print(f"✓ Thread pool processing completed in {elapsed:.2f} seconds")

    return {"results": results, "elapsed_time": elapsed}


# ========== Async/Await Pattern ==========

@task
async def async_http_request(url: str) -> dict:
    """Makes an async HTTP request."""
    logger = get_run_logger()
    logger.info(f"Fetching {url}")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            return {
                "url": url,
                "status": response.status_code,
                "length": len(response.text)
            }
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            return {
                "url": url,
                "status": "error",
                "error": str(e)
            }


@flow(name="Async Flow", log_prints=True)
async def async_flow():
    """Uses async/await for concurrent I/O operations."""
    logger = get_run_logger()
    print("\n=== Async/Await HTTP Requests ===")

    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1",
    ]

    start_time = time.time()

    # Submit all requests concurrently
    futures = [async_http_request.submit(url) for url in urls]

    # Wait for all to complete
    results = [await future for future in futures]

    elapsed = time.time() - start_time
    print(f"✓ Async requests completed in {elapsed:.2f} seconds")
    print(f"Made {len(urls)} requests (would take ~{len(urls)} seconds sequentially)")

    return {"results": results, "elapsed_time": elapsed}


# ========== Mixed Parallel and Sequential ==========

@task
def extract_batch(batch_id: int) -> dict:
    """Extracts a batch of data."""
    logger = get_run_logger()
    time.sleep(0.3)
    return {"batch_id": batch_id, "records": list(range(batch_id * 10, (batch_id + 1) * 10))}


@task
def transform_batch(batch: dict) -> dict:
    """Transforms a batch of data."""
    logger = get_run_logger()
    time.sleep(0.2)
    return {
        "batch_id": batch["batch_id"],
        "transformed_records": [r * 2 for r in batch["records"]]
    }


@task
def load_all_batches(batches: list[dict]) -> dict:
    """Loads all batches (must be sequential)."""
    logger = get_run_logger()
    logger.info(f"Loading {len(batches)} batches to database...")
    time.sleep(0.5)

    total_records = sum(len(b["transformed_records"]) for b in batches)
    return {"batches_loaded": len(batches), "total_records": total_records}


@flow(name="Mixed Parallel-Sequential Flow", log_prints=True)
def mixed_parallel_sequential_flow(num_batches: int = 5):
    """Demonstrates mixing parallel and sequential operations."""
    logger = get_run_logger()
    print(f"\n=== Mixed Parallel-Sequential Processing ===")

    start_time = time.time()

    # Phase 1: Extract in parallel
    print("Phase 1: Extracting batches in parallel...")
    batch_ids = list(range(num_batches))
    raw_batches = extract_batch.map(batch_ids)

    # Phase 2: Transform in parallel
    print("Phase 2: Transforming batches in parallel...")
    transformed_batches = transform_batch.map(raw_batches)

    # Phase 3: Load sequentially (database constraint)
    print("Phase 3: Loading batches sequentially...")
    load_result = load_all_batches(transformed_batches)

    elapsed = time.time() - start_time
    print(f"✓ Mixed processing completed in {elapsed:.2f} seconds")

    return {
        "load_result": load_result,
        "elapsed_time": elapsed
    }


# ========== Comprehensive Demo ==========

@flow(name="Comprehensive Concurrency Demo", log_prints=True)
def comprehensive_concurrency_demo():
    """Runs all concurrency pattern examples."""
    print("="*60)
    print("COMPREHENSIVE CONCURRENCY PATTERNS DEMONSTRATION")
    print("="*60)

    # Sequential vs Parallel comparison
    seq_result = sequential_flow(num_items=5)
    par_result = parallel_flow_with_map(num_items=5)

    speedup = seq_result["elapsed_time"] / par_result["elapsed_time"]
    print(f"\n💡 Speedup: {speedup:.2f}x faster with parallel execution\n")

    # Thread pool
    thread_pool_flow()

    # Mixed pattern
    mixed_parallel_sequential_flow(num_batches=5)

    # Note: Async example requires asyncio.run() - see below

    print("\n" + "="*60)
    print("Concurrency examples completed")
    print("="*60)


if __name__ == "__main__":
    # Run synchronous examples
    comprehensive_concurrency_demo()

    # Run async example separately
    print("\n" + "="*60)
    print("Running Async Example...")
    print("="*60)
    asyncio.run(async_flow())
