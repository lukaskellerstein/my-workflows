"""
Example 2: Prefect UI Visualization

Demonstrates how Prefect visualizes workflows in the UI with real-time execution graphs.

The Prefect UI provides:
- Real-time workflow execution graphs
- Interactive task exploration
- State tracking and history
- Artifact visualization
- Log integration

To use:
    1. Start Prefect server: prefect server start
    2. Run this file: python 02_ui_visualization.py
    3. Open browser: http://localhost:4200
    4. Navigate to Flow Runs → View your run
"""

import time
from prefect import flow, task, get_run_logger


# ========== Example 1: Real-Time Visualization ==========

@task
def step_1() -> str:
    """First step - visible in UI immediately."""
    logger = get_run_logger()
    logger.info("Executing step 1...")
    time.sleep(2)  # Simulate work
    return "Step 1 complete"


@task
def step_2(input_data: str) -> str:
    """Second step - shows dependency on step 1."""
    logger = get_run_logger()
    logger.info(f"Executing step 2 with: {input_data}")
    time.sleep(2)
    return "Step 2 complete"


@task
def step_3(input_data: str) -> str:
    """Third step - final step in sequence."""
    logger = get_run_logger()
    logger.info(f"Executing step 3 with: {input_data}")
    time.sleep(2)
    return "Step 3 complete"


@flow(name="Sequential Visualization Example", log_prints=True)
def sequential_visualization_flow():
    """
    Sequential flow that's easy to follow in the UI.

    In the UI, you'll see:
    - Tasks appear as they start
    - States change color (pending → running → completed)
    - Execution timeline
    - Dependencies between tasks
    """
    print("Starting sequential workflow...")
    print("Watch in Prefect UI at: http://localhost:4200\n")

    result1 = step_1()
    print(f"✓ {result1}")

    result2 = step_2(result1)
    print(f"✓ {result2}")

    result3 = step_3(result2)
    print(f"✓ {result3}")

    return "All steps completed"


# ========== Example 2: Parallel Visualization ==========

@task
def parallel_task_a() -> dict:
    """Parallel task A - runs independently."""
    logger = get_run_logger()
    logger.info("Processing task A...")
    time.sleep(3)
    return {"task": "A", "value": 100}


@task
def parallel_task_b() -> dict:
    """Parallel task B - runs independently."""
    logger = get_run_logger()
    logger.info("Processing task B...")
    time.sleep(3)
    return {"task": "B", "value": 200}


@task
def parallel_task_c() -> dict:
    """Parallel task C - runs independently."""
    logger = get_run_logger()
    logger.info("Processing task C...")
    time.sleep(3)
    return {"task": "C", "value": 300}


@task
def aggregate_parallel_results(a: dict, b: dict, c: dict) -> dict:
    """Aggregates results from parallel tasks."""
    logger = get_run_logger()
    logger.info("Aggregating parallel results...")
    time.sleep(1)

    return {
        "total_value": a["value"] + b["value"] + c["value"],
        "tasks_completed": [a["task"], b["task"], c["task"]]
    }


@flow(name="Parallel Visualization Example", log_prints=True)
def parallel_visualization_flow():
    """
    Parallel flow showing fan-out/fan-in pattern in UI.

    In the UI, you'll see:
    - Three tasks start simultaneously
    - All run in parallel (overlapping time)
    - Aggregate task waits for all three
    - Clear visual of fan-out/fan-in pattern
    """
    print("Starting parallel workflow...")
    print("Watch in Prefect UI to see parallel execution!\n")

    # These tasks have no dependencies, so they run in parallel
    result_a = parallel_task_a()
    result_b = parallel_task_b()
    result_c = parallel_task_c()

    # This task waits for all three
    final_result = aggregate_parallel_results(result_a, result_b, result_c)

    print(f"\n✓ Parallel workflow completed: {final_result}")
    return final_result


# ========== Example 3: Complex Workflow with Multiple Patterns ==========

@task
def initialize() -> dict:
    """Initializes the workflow."""
    logger = get_run_logger()
    logger.info("Initializing workflow...")
    time.sleep(1)
    return {"status": "initialized", "data": [1, 2, 3, 4, 5]}


@task
def validate_data(data: dict) -> bool:
    """Validates the data."""
    logger = get_run_logger()
    logger.info("Validating data...")
    time.sleep(1)
    return len(data["data"]) > 0


@task
def process_batch_1(data: dict) -> dict:
    """Processes first batch."""
    logger = get_run_logger()
    logger.info("Processing batch 1...")
    time.sleep(2)
    return {"batch": 1, "processed": len(data["data"])}


@task
def process_batch_2(data: dict) -> dict:
    """Processes second batch."""
    logger = get_run_logger()
    logger.info("Processing batch 2...")
    time.sleep(2)
    return {"batch": 2, "processed": len(data["data"])}


@task
def finalize_results(batch1: dict, batch2: dict) -> dict:
    """Finalizes all results."""
    logger = get_run_logger()
    logger.info("Finalizing results...")
    time.sleep(1)
    return {
        "total_batches": 2,
        "total_processed": batch1["processed"] + batch2["processed"],
        "status": "completed"
    }


@flow(name="Complex Visualization Example", log_prints=True)
def complex_visualization_flow():
    """
    Complex workflow demonstrating multiple patterns.

    In the UI, you'll see:
    - Sequential initialization and validation
    - Conditional branching
    - Parallel batch processing
    - Final aggregation step
    - Complete workflow dependency graph
    """
    print("Starting complex workflow...")
    print("This demonstrates multiple patterns in one flow!\n")

    # Sequential initialization
    init_data = initialize()
    print("✓ Initialized")

    # Validation
    is_valid = validate_data(init_data)

    if is_valid:
        print("✓ Data validated")

        # Parallel processing of batches
        batch1_result = process_batch_1(init_data)
        batch2_result = process_batch_2(init_data)

        # Final aggregation
        final = finalize_results(batch1_result, batch2_result)

        print(f"✓ Complex workflow completed: {final}")
        return final
    else:
        print("✗ Data validation failed")
        return {"status": "failed", "reason": "validation"}


# ========== Main Demo ==========

def main():
    """
    Runs all visualization examples.

    Make sure Prefect server is running:
        prefect server start

    Then view at:
        http://localhost:4200
    """
    print("="*70)
    print("PREFECT UI VISUALIZATION DEMONSTRATION")
    print("="*70)
    print("""
These examples demonstrate how Prefect visualizes workflows in the UI.

SETUP:
1. Start Prefect server in another terminal:
   prefect server start

2. Open browser:
   http://localhost:4200

3. As each flow runs, navigate to:
   Flow Runs → Click on the run → Graph tab

WHAT TO OBSERVE IN THE UI:
- Real-time task execution
- Task states: Pending → Running → Completed
- Dependencies visualized as connecting lines
- Parallel execution (tasks running simultaneously)
- Task logs and details
- Execution timeline

Press Enter to start running flows...
""")
    input()

    print("\n" + "="*70)
    print("EXAMPLE 1: Sequential Flow")
    print("="*70)
    print("Running sequential workflow...")
    sequential_visualization_flow()

    print("\n\nCheck the UI to see the sequential execution graph!")
    print("Press Enter to continue to next example...")
    input()

    print("\n" + "="*70)
    print("EXAMPLE 2: Parallel Flow")
    print("="*70)
    print("Running parallel workflow...")
    parallel_visualization_flow()

    print("\n\nCheck the UI to see parallel tasks running!")
    print("Press Enter to continue to next example...")
    input()

    print("\n" + "="*70)
    print("EXAMPLE 3: Complex Flow")
    print("="*70)
    print("Running complex workflow...")
    complex_visualization_flow()

    print("\n\n" + "="*70)
    print("✓ All examples completed!")
    print("="*70)
    print("""
View all executions in the Prefect UI:
http://localhost:4200

Explore:
- Graph tab: See workflow visualization
- Logs tab: View task execution logs
- Details tab: Inspect task inputs/outputs
- Timeline: See execution duration
""")
    print("="*70)


if __name__ == "__main__":
    main()
