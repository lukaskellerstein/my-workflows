"""
Task vs Regular Function - Understanding the Difference

This example demonstrates the key differences between @task decorated functions
and regular Python functions when used in Prefect flows.
"""

import time
from prefect import flow, task, get_run_logger


# ========== Regular Python Function ==========

def regular_function(x: int) -> int:
    """A regular Python function - no Prefect features."""
    print(f"Regular function processing {x}")
    time.sleep(0.5)
    return x * 2


# ========== Task Function ==========

@task(retries=2, retry_delay_seconds=1)
def task_function(x: int) -> int:
    """A task function - gets Prefect superpowers."""
    logger = get_run_logger()
    logger.info(f"Task processing {x}")
    time.sleep(0.5)
    return x * 2


# ========== Comparison Examples ==========

@flow(name="Comparison Flow", log_prints=True)
def comparison_flow():
    """Demonstrates the differences between tasks and regular functions."""
    print("\n" + "="*70)
    print("TASK vs REGULAR FUNCTION COMPARISON")
    print("="*70 + "\n")

    # 1. Basic execution - both work the same
    print("1. Basic Execution:")
    regular_result = regular_function(5)
    task_result = task_function(5)
    print(f"   Regular: {regular_result}")
    print(f"   Task: {task_result}")
    print()

    # 2. Observability - tasks are tracked
    print("2. Observability:")
    print("   Regular function: No tracking in Prefect UI")
    print("   Task: Full tracking - start time, end time, inputs, outputs, logs")
    print()

    # 3. Parallel execution with map
    print("3. Parallel Execution:")
    items = [1, 2, 3, 4, 5]

    # Regular function - must use loop (sequential)
    start = time.time()
    regular_results = [regular_function(i) for i in items]
    regular_time = time.time() - start
    print(f"   Regular function (sequential): {regular_time:.2f}s")

    # Task - can use .map() for parallel execution
    start = time.time()
    task_results = task_function.map(items)
    task_time = time.time() - start
    print(f"   Task with .map() (parallel): {task_time:.2f}s")
    print(f"   Speedup: {regular_time/task_time:.2f}x faster!")
    print()

    return {
        "regular": regular_results,
        "task": task_results
    }


# ========== Key Differences Demonstrated ==========

# 1. RETRY BEHAVIOR
@task(retries=3, retry_delay_seconds=1)
def task_with_retry(should_fail: bool = False) -> str:
    """Task will automatically retry on failure."""
    logger = get_run_logger()

    if should_fail:
        logger.warning("Task failing - will retry automatically")
        raise Exception("Temporary failure")

    return "Success"


def regular_function_no_retry(should_fail: bool = False) -> str:
    """Regular function - you must implement retry logic yourself."""
    if should_fail:
        raise Exception("Failure - no automatic retry")

    return "Success"


@flow(name="Retry Behavior", log_prints=True)
def retry_comparison_flow():
    """Shows automatic retry behavior of tasks."""
    print("\n" + "="*70)
    print("RETRY BEHAVIOR")
    print("="*70 + "\n")

    # Task with retry
    print("1. Task with retry (will succeed after failures):")
    try:
        # This would fail first time, but retry automatically
        result = task_with_retry(should_fail=False)  # Using False to demo
        print(f"   ✓ Task result: {result}")
        print("   Note: If should_fail=True, task would retry 3 times automatically")
    except Exception as e:
        print(f"   ✗ Failed after retries: {e}")
    print()

    # Regular function - no retry
    print("2. Regular function (no automatic retry):")
    try:
        result = regular_function_no_retry(should_fail=True)
        print(f"   ✓ Regular result: {result}")
    except Exception as e:
        print(f"   ✗ Failed immediately: {e}")
        print("   You must implement retry logic yourself")
    print()


# ========== State and Futures ==========

@flow(name="State and Futures", log_prints=True)
def state_and_futures_flow():
    """Shows how tasks return futures with state information."""
    print("\n" + "="*70)
    print("STATE AND FUTURES")
    print("="*70 + "\n")

    # Regular function - just returns the value
    print("1. Regular function:")
    regular_result = regular_function(10)
    print(f"   Type: {type(regular_result)}")
    print(f"   Value: {regular_result}")
    print("   Note: Just returns the raw value, no metadata")
    print()

    # Task - can return future or value depending on how called
    print("2. Task function:")

    # Direct call - returns value (default behavior in flows)
    task_result = task_function(10)
    print(f"   Direct call type: {type(task_result)}")
    print(f"   Direct call value: {task_result}")

    # Submit - returns future
    task_future = task_function.submit(10)
    print(f"   Submit type: {type(task_future)}")
    print(f"   Future has state: {task_future.state}")
    print(f"   Future result: {task_future.result()}")
    print()


# ========== Caching ==========

@task(cache_key_fn=lambda *args, **kwargs: "static_key", cache_expiration=None)
def cached_task(x: int) -> int:
    """Task with caching - expensive computation only runs once."""
    logger = get_run_logger()
    logger.info(f"Running expensive computation for {x}")
    time.sleep(2)  # Simulate expensive operation
    return x ** 2


def regular_function_uncached(x: int) -> int:
    """Regular function - runs every time, no caching."""
    print(f"Running expensive computation for {x}")
    time.sleep(2)
    return x ** 2


@flow(name="Caching Behavior", log_prints=True)
def caching_comparison_flow():
    """Shows caching capability of tasks."""
    print("\n" + "="*70)
    print("CACHING BEHAVIOR")
    print("="*70 + "\n")

    print("1. Regular function (no caching):")
    start = time.time()
    result1 = regular_function_uncached(5)
    time1 = time.time() - start
    print(f"   First call: {time1:.2f}s")

    start = time.time()
    result2 = regular_function_uncached(5)
    time2 = time.time() - start
    print(f"   Second call: {time2:.2f}s (runs again)")
    print()

    print("2. Task with caching:")
    # Note: In this example, caching would need proper cache_key_fn setup
    # This is simplified for demonstration
    print("   First call: Runs computation")
    print("   Second call: Returns cached result (instant)")
    print("   Note: Tasks can cache results based on inputs")
    print()


# ========== Logging ==========

@flow(name="Logging Comparison", log_prints=True)
def logging_comparison_flow():
    """Shows logging differences."""
    print("\n" + "="*70)
    print("LOGGING")
    print("="*70 + "\n")

    print("1. Regular function:")
    regular_function(7)
    print("   Uses print() - appears in stdout only")
    print()

    print("2. Task function:")
    task_function(7)
    print("   Uses get_run_logger() - logged to Prefect backend")
    print("   Visible in Prefect UI with timestamps and task context")
    print()


# ========== Summary Table ==========

@flow(name="Feature Summary", log_prints=True)
def feature_summary():
    """Prints a comprehensive feature comparison table."""
    print("\n" + "="*70)
    print("FEATURE COMPARISON SUMMARY")
    print("="*70 + "\n")

    comparison = """
╔═══════════════════════════╦═══════════════════╦══════════════════════╗
║ Feature                   ║ Regular Function  ║ @task Function       ║
╠═══════════════════════════╬═══════════════════╬══════════════════════╣
║ Basic Execution           ║ ✓                 ║ ✓                    ║
║ Automatic Retries         ║ ✗                 ║ ✓                    ║
║ Parallel Execution (.map) ║ ✗                 ║ ✓                    ║
║ State Tracking            ║ ✗                 ║ ✓                    ║
║ UI Visibility             ║ ✗                 ║ ✓                    ║
║ Structured Logging        ║ ✗                 ║ ✓                    ║
║ Caching                   ║ ✗                 ║ ✓                    ║
║ Futures/Async Submit      ║ ✗                 ║ ✓                    ║
║ Execution Time Tracking   ║ ✗                 ║ ✓                    ║
║ Input/Output Tracking     ║ ✗                 ║ ✓                    ║
║ Conditional Retries       ║ ✗                 ║ ✓                    ║
║ Wait/Depend Logic         ║ ✗                 ║ ✓                    ║
║ Task Tags                 ║ ✗                 ║ ✓                    ║
║ Result Persistence        ║ ✗                 ║ ✓ (optional)         ║
╚═══════════════════════════╩═══════════════════╩══════════════════════╝

KEY DIFFERENCES EXPLAINED:

1. OBSERVABILITY
   - Regular: No tracking, no visibility
   - Task: Full tracking in Prefect UI with execution graph

2. RETRIES
   - Regular: Must implement manually
   - Task: @task(retries=3, retry_delay_seconds=2)

3. PARALLELISM
   - Regular: Must use threading/multiprocessing manually
   - Task: task.map(items) automatically runs in parallel

4. FUTURES
   - Regular: Blocks until completion
   - Task: Can submit() and get future, check state, wait async

5. CACHING
   - Regular: No built-in caching
   - Task: Cache based on inputs automatically

6. STATE MANAGEMENT
   - Regular: No state concept
   - Task: Has states (PENDING, RUNNING, COMPLETED, FAILED, etc.)

WHEN TO USE EACH:

Use Regular Functions:
  ✓ Simple utility functions (formatting, calculations)
  ✓ Helper functions that don't need tracking
  ✓ Functions called many times (low overhead)
  ✓ Pure functions with no side effects

Use Tasks:
  ✓ I/O operations (API calls, database queries)
  ✓ Long-running operations
  ✓ Operations that might fail (need retries)
  ✓ Operations you want to run in parallel
  ✓ Critical operations you want to monitor
  ✓ Operations that should be cached
"""
    print(comparison)


# ========== Practical Example ==========

def format_name(first: str, last: str) -> str:
    """Simple helper - regular function is fine."""
    return f"{last}, {first}"


@task(retries=3, retry_delay_seconds=2)
def fetch_user_from_api(user_id: int) -> dict:
    """API call - should be a task for retries and tracking."""
    logger = get_run_logger()
    logger.info(f"Fetching user {user_id}")
    # Simulate API call
    return {"id": user_id, "first": "John", "last": "Doe"}


@task
def save_to_database(user: dict) -> bool:
    """Database operation - should be a task for tracking."""
    logger = get_run_logger()
    logger.info(f"Saving user {user['id']}")
    # Simulate save
    return True


@flow(name="Practical Example", log_prints=True)
def practical_example_flow():
    """Shows when to use tasks vs regular functions in real workflow."""
    print("\n" + "="*70)
    print("PRACTICAL EXAMPLE: USER PROCESSING PIPELINE")
    print("="*70 + "\n")

    user_ids = [1, 2, 3, 4, 5]

    # Fetch users in parallel (TASK - I/O bound, needs retries)
    print("Step 1: Fetching users from API (parallel)...")
    users = fetch_user_from_api.map(user_ids)
    print(f"✓ Fetched {len(users)} users in parallel\n")

    # Format names (REGULAR FUNCTION - simple utility)
    print("Step 2: Formatting names...")
    for user in users:
        formatted = format_name(user["first"], user["last"])
        user["formatted_name"] = formatted
        print(f"   {formatted}")
    print()

    # Save to database (TASK - I/O bound, want tracking)
    print("Step 3: Saving to database (parallel)...")
    results = save_to_database.map(users)
    print(f"✓ Saved {sum(results)} users\n")

    print("✓ Pipeline complete!")
    print("\nNote: Tasks used for I/O, regular functions for simple utilities")


# ========== Main Demo ==========

@flow(name="Comprehensive Demo", log_prints=True)
def comprehensive_demo():
    """Runs all comparison examples."""
    comparison_flow()
    retry_comparison_flow()
    state_and_futures_flow()
    caching_comparison_flow()
    logging_comparison_flow()
    feature_summary()
    practical_example_flow()

    print("\n" + "="*70)
    print("ALL COMPARISONS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    comprehensive_demo()
