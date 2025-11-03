"""
Example: Error Handling Patterns

Demonstrates various error handling strategies in Prefect workflows.
"""

from prefect import flow, task, get_run_logger
from prefect.states import Failed, Completed
from prefect.futures import wait


# ========== Task-Level Error Handling ==========

@task
def risky_operation(value: int) -> int:
    """A task that might raise an exception."""
    logger = get_run_logger()

    if value < 0:
        raise ValueError(f"Negative value not allowed: {value}")

    if value == 0:
        raise ZeroDivisionError("Cannot divide by zero")

    return 100 // value


# ========== Graceful Degradation ==========

@task
def fetch_user_data(user_id: int) -> dict:
    """Fetches user data, might fail for some users."""
    logger = get_run_logger()

    if user_id % 3 == 0:
        raise Exception(f"User {user_id} not found")

    return {"user_id": user_id, "name": f"User_{user_id}"}


@task
def process_user(user_data: dict) -> dict:
    """Processes user data."""
    logger = get_run_logger()

    return {
        "user_id": user_data["user_id"],
        "processed": True,
        "message": f"Processed {user_data['name']}"
    }


# ========== State-Based Error Handling ==========

@task
def operation_that_might_fail(should_fail: bool = False) -> str:
    """Task that conditionally fails."""
    if should_fail:
        raise Exception("Operation failed as requested")
    return "Success"


# ========== Flows ==========

@flow(name="Try-Except Flow", log_prints=True)
def try_except_flow():
    """Demonstrates basic try-except error handling in flows."""
    logger = get_run_logger()
    print("\n=== Try-Except Error Handling ===")

    test_values = [10, 5, 0, -1, 2]
    results = []

    for value in test_values:
        try:
            result = risky_operation(value)
            print(f"✓ {value}: {result}")
            results.append({"value": value, "result": result, "status": "success"})
        except ValueError as e:
            print(f"✗ {value}: ValueError - {e}")
            results.append({"value": value, "error": str(e), "status": "value_error"})
        except ZeroDivisionError as e:
            print(f"✗ {value}: ZeroDivisionError - {e}")
            results.append({"value": value, "error": str(e), "status": "zero_error"})
        except Exception as e:
            print(f"✗ {value}: Unexpected error - {e}")
            results.append({"value": value, "error": str(e), "status": "unknown_error"})

    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nResults: {success_count}/{len(results)} operations succeeded")

    return results


@flow(name="Graceful Degradation Flow", log_prints=True)
def graceful_degradation_flow():
    """Demonstrates graceful degradation - continue processing despite failures."""
    logger = get_run_logger()
    print("\n=== Graceful Degradation ===")

    user_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    successful_results = []
    failed_users = []

    print(f"Processing {len(user_ids)} users...")

    for user_id in user_ids:
        try:
            # Try to fetch user data
            user_data = fetch_user_data(user_id)
            # Process if successful
            result = process_user(user_data)
            successful_results.append(result)
            print(f"✓ User {user_id}: {result['message']}")
        except Exception as e:
            # Log failure but continue with other users
            failed_users.append({"user_id": user_id, "error": str(e)})
            print(f"✗ User {user_id}: Failed - {e}")

    # Summary
    print(f"\n{'='*50}")
    print(f"Processing complete:")
    print(f"  ✓ Successful: {len(successful_results)}")
    print(f"  ✗ Failed: {len(failed_users)}")
    print(f"{'='*50}")

    return {
        "successful": successful_results,
        "failed": failed_users,
        "success_rate": len(successful_results) / len(user_ids)
    }


@flow(name="State-Based Error Handling Flow", log_prints=True)
def state_based_error_handling_flow():
    """Demonstrates error handling using Prefect states."""
    logger = get_run_logger()
    print("\n=== State-Based Error Handling ===")

    # Submit multiple tasks
    tasks_to_run = [
        ("Task 1", False),
        ("Task 2", True),   # Will fail
        ("Task 3", False),
        ("Task 4", True),   # Will fail
        ("Task 5", False),
    ]

    futures = []
    for task_name, should_fail in tasks_to_run:
        future = operation_that_might_fail.submit(should_fail=should_fail)
        futures.append((task_name, future))

    # Wait for all tasks to complete (even failures)
    wait([f for _, f in futures])

    # Check states and handle accordingly
    results = []
    for task_name, future in futures:
        state = future.state

        if state.is_completed():
            result = future.result()
            print(f"✓ {task_name}: {result}")
            results.append({"task": task_name, "status": "completed", "result": result})
        elif state.is_failed():
            print(f"✗ {task_name}: Failed")
            results.append({"task": task_name, "status": "failed", "error": str(state.message)})
        else:
            print(f"? {task_name}: {state.type}")
            results.append({"task": task_name, "status": state.type.value})

    success_count = sum(1 for r in results if r["status"] == "completed")
    print(f"\nResults: {success_count}/{len(results)} tasks succeeded")

    return results


@flow(name="Custom Error Response Flow", log_prints=True)
def custom_error_response_flow():
    """Demonstrates returning custom error responses instead of raising exceptions."""
    logger = get_run_logger()
    print("\n=== Custom Error Response ===")

    test_values = [10, 5, 0, -1, 2]
    results = []

    for value in test_values:
        try:
            result = risky_operation(value)
            response = {
                "value": value,
                "result": result,
                "status": "success",
                "error": None
            }
            print(f"✓ {value}: {result}")
        except Exception as e:
            response = {
                "value": value,
                "result": None,
                "status": "error",
                "error": {"type": type(e).__name__, "message": str(e)}
            }
            print(f"✗ {value}: {type(e).__name__}")

        results.append(response)

    # Flow doesn't fail even if some tasks failed
    print(f"\nProcessed {len(results)} values (flow completed successfully)")

    return {
        "results": results,
        "success_count": sum(1 for r in results if r["status"] == "success"),
        "error_count": sum(1 for r in results if r["status"] == "error")
    }


@flow(name="Comprehensive Error Handling Flow", log_prints=True)
def comprehensive_error_handling_flow():
    """Runs all error handling pattern examples."""
    logger = get_run_logger()

    print("="*60)
    print("COMPREHENSIVE ERROR HANDLING DEMONSTRATION")
    print("="*60)

    # Run all examples
    try_except_flow()
    graceful_degradation_flow()
    state_based_error_handling_flow()
    custom_error_response_flow()

    print("\n" + "="*60)
    print("All error handling examples completed")
    print("="*60)


if __name__ == "__main__":
    # Run comprehensive demo
    comprehensive_error_handling_flow()
