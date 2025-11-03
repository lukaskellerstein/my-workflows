"""
Example 1: Single Node Workflow

Demonstrates the simplest Prefect workflow with a single task.
"""

from prefect import flow, task, get_run_logger


@task
def process_data(value: int) -> int:
    """A simple task that processes a single value."""
    logger = get_run_logger()
    result = value * 2
    logger.info(f"Processing {value} -> {result}")
    return result


@flow(name="Single Node Workflow", log_prints=True)
def single_node_flow(input_value: int = 10):
    """A flow with a single task execution."""
    logger = get_run_logger()
    logger.info(f"Starting single node workflow with input: {input_value}")

    result = process_data(input_value)

    print(f"Final result: {result}")
    return result


if __name__ == "__main__":
    # # Run the flow with default value
    # single_node_flow()

    # Run with custom value
    single_node_flow(input_value=42)
