"""
Example: Retry Patterns

Demonstrates various retry strategies for handling transient failures in tasks.
"""

import random
from prefect import flow, task, get_run_logger
from prefect.states import Failed


# ========== Basic Retry ==========

@task(retries=3, retry_delay_seconds=1)
def unreliable_api_call(success_rate: float = 0.3) -> dict:
    """Simulates an unreliable API that might fail."""
    logger = get_run_logger()

    if random.random() > success_rate:
        logger.warning("API call failed - will retry")
        raise Exception("API temporarily unavailable")

    logger.info("API call succeeded")
    return {"status": "success", "data": [1, 2, 3, 4, 5]}


# ========== Exponential Backoff ==========

@task(retries=3, retry_delay_seconds=[1, 4, 10])
def api_with_backoff(endpoint: str) -> dict:
    """
    Task with exponential backoff retry strategy.

    Retry delays: 1s, 4s, 10s
    """
    logger = get_run_logger()

    # Simulate API that might be rate-limited
    if random.random() > 0.4:
        logger.warning(f"Rate limited on {endpoint}")
        raise Exception("429 Too Many Requests")

    logger.info(f"Successfully called {endpoint}")
    return {"endpoint": endpoint, "status": 200}


# ========== Conditional Retry ==========

def should_retry_on_value_error(task, task_run, state) -> bool:
    """Custom retry condition - only retry on ValueError."""
    logger = get_run_logger()

    try:
        state.result()
        return False
    except ValueError as e:
        logger.info(f"ValueError encountered: {e} - will retry")
        return True
    except Exception as e:
        logger.warning(f"Non-ValueError exception: {e} - will NOT retry")
        return False


@task(
    retries=2,
    retry_delay_seconds=2,
    retry_condition_fn=should_retry_on_value_error
)
def selective_retry_task(value: int) -> int:
    """Only retries on ValueError, not on other exceptions."""
    logger = get_run_logger()

    if value < 0:
        raise ValueError(f"Negative value not allowed: {value}")
    elif value == 0:
        raise TypeError("Zero is not a valid type indicator")

    return value * 2


# ========== Retry with Fallback ==========

@task(retries=2, retry_delay_seconds=1)
def primary_data_source() -> dict:
    """Primary data source that might fail."""
    logger = get_run_logger()

    if random.random() > 0.2:
        raise Exception("Primary source unavailable")

    return {"source": "primary", "data": [10, 20, 30]}


@task
def fallback_data_source() -> dict:
    """Fallback data source with cached/default data."""
    logger = get_run_logger()
    logger.info("Using fallback data source")

    return {"source": "fallback", "data": [1, 2, 3]}


# ========== Flows ==========

@flow(name="Basic Retry Flow", log_prints=True)
def basic_retry_flow():
    """Demonstrates basic retry behavior."""
    logger = get_run_logger()
    print("\n=== Basic Retry Example ===")

    try:
        result = unreliable_api_call(success_rate=0.5)
        print(f"✓ API call succeeded: {result}")
        return result
    except Exception as e:
        print(f"✗ API call failed after all retries: {e}")
        return None


@flow(name="Exponential Backoff Flow", log_prints=True)
def exponential_backoff_flow():
    """Demonstrates exponential backoff retry strategy."""
    logger = get_run_logger()
    print("\n=== Exponential Backoff Example ===")

    endpoints = ["/users", "/posts", "/comments"]
    results = []

    for endpoint in endpoints:
        try:
            result = api_with_backoff(endpoint)
            print(f"✓ {endpoint}: {result['status']}")
            results.append(result)
        except Exception as e:
            print(f"✗ {endpoint} failed: {e}")

    return results


@flow(name="Conditional Retry Flow", log_prints=True)
def conditional_retry_flow():
    """Demonstrates conditional retry based on exception type."""
    logger = get_run_logger()
    print("\n=== Conditional Retry Example ===")

    test_values = [-5, 0, 10]
    results = []

    for value in test_values:
        print(f"\nTesting value: {value}")
        try:
            result = selective_retry_task(value)
            print(f"✓ Success: {value} -> {result}")
            results.append(result)
        except ValueError as e:
            print(f"✗ ValueError (retried but still failed): {e}")
        except TypeError as e:
            print(f"✗ TypeError (not retried): {e}")

    return results


@flow(name="Retry with Fallback Flow", log_prints=True)
def retry_with_fallback_flow():
    """Demonstrates using a fallback when primary source fails."""
    logger = get_run_logger()
    print("\n=== Retry with Fallback Example ===")

    try:
        # Try primary source (will retry automatically)
        print("Attempting primary data source...")
        data = primary_data_source()
        print(f"✓ Primary source succeeded: {data}")
        return data
    except Exception as e:
        # Fall back to secondary source
        print(f"✗ Primary source failed: {e}")
        print("Falling back to secondary source...")
        data = fallback_data_source()
        print(f"✓ Fallback source succeeded: {data}")
        return data


@flow(name="Comprehensive Retry Flow", log_prints=True)
def comprehensive_retry_flow():
    """Runs all retry pattern examples."""
    logger = get_run_logger()

    print("="*60)
    print("COMPREHENSIVE RETRY PATTERNS DEMONSTRATION")
    print("="*60)

    # Run all examples
    basic_retry_flow()
    exponential_backoff_flow()
    conditional_retry_flow()
    retry_with_fallback_flow()

    print("\n" + "="*60)
    print("All retry pattern examples completed")
    print("="*60)


if __name__ == "__main__":
    # Run comprehensive demo
    comprehensive_retry_flow()
