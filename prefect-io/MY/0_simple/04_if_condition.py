"""
Example 3: Workflow with IF Condition

Demonstrates conditional logic in workflows based on task results.
"""

from prefect import flow, task, get_run_logger


@task
def check_data_quality(data: list[int]) -> dict:
    """Checks the quality of input data."""
    logger = get_run_logger()
    logger.info(f"Checking quality of {len(data)} records")

    quality_score = sum(data) / len(data) if data else 0
    has_nulls = any(x is None or x < 0 for x in data)

    quality_report = {
        "score": quality_score,
        "has_nulls": has_nulls,
        "count": len(data),
        "passed": quality_score > 0 and not has_nulls
    }

    logger.info(f"Quality report: {quality_report}")
    return quality_report


@task
def process_good_data(data: list[int]) -> dict:
    """Processes data that passed quality checks."""
    logger = get_run_logger()
    logger.info("Processing good quality data")

    return {
        "status": "success",
        "sum": sum(data),
        "avg": sum(data) / len(data),
        "max": max(data)
    }


@task
def handle_bad_data(data: list[int], quality_report: dict) -> dict:
    """Handles data that failed quality checks."""
    logger = get_run_logger()
    logger.warning("Handling bad quality data")

    # Clean the data
    cleaned = [x for x in data if x is not None and x >= 0]

    return {
        "status": "data_cleaned",
        "original_count": len(data),
        "cleaned_count": len(cleaned),
        "reason": quality_report
    }


@task
def send_notification(result: dict):
    """Sends a notification about the workflow result."""
    logger = get_run_logger()
    logger.info(f"Sending notification: {result['status']}")
    return f"Notification sent for {result['status']}"


@flow(name="Conditional Workflow", log_prints=True)
def conditional_flow(data: list[int] = None):
    """A flow that branches based on data quality checks."""
    logger = get_run_logger()

    # Default data if none provided
    if data is None:
        data = [10, 20, 30, 40, 50]

    logger.info(f"Starting conditional workflow with {len(data)} records")

    # Check data quality
    quality_report = check_data_quality(data)

    # Branch based on quality check
    if quality_report["passed"]:
        print("✓ Data quality check passed - processing data")
        result = process_good_data(data)
    else:
        print("✗ Data quality check failed - handling bad data")
        result = handle_bad_data(data, quality_report)

    # Send notification regardless of path
    notification = send_notification(result)

    print(f"Workflow completed: {result['status']}")
    print(f"Notification: {notification}")

    return result


if __name__ == "__main__":
    # Run with good data
    print("=== Test 1: Good Quality Data ===")
    conditional_flow([10, 20, 30, 40, 50])

    print("\n=== Test 2: Bad Quality Data ===")
    conditional_flow([10, -5, None, 40, -10])

    print("\n=== Test 3: Empty Data ===")
    conditional_flow([])
