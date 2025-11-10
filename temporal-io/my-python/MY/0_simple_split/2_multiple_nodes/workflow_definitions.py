"""
Workflow and Activity Definitions - Multiple Nodes
Demonstrates a workflow with multiple activities executed sequentially.
"""
from datetime import timedelta

from temporalio import activity, workflow


# Activity 1: Validate input
@activity.defn
def validate_input(value: int) -> bool:
    """Validate that the input value is positive."""
    activity.logger.info(f"Validating input: {value}")
    is_valid = value > 0
    activity.logger.info(f"Validation result: {is_valid}")
    return is_valid


# Activity 2: Transform data
@activity.defn
def transform_data(value: int) -> int:
    """Transform data using a mathematical operation."""
    activity.logger.info(f"Transforming data: {value}")
    result = value * 3 + 10
    activity.logger.info(f"Transformed result: {result}")
    return result


# Activity 3: Save result
@activity.defn
def save_result(value: int) -> str:
    """Save the result (simulation)."""
    activity.logger.info(f"Saving result: {value}")
    return f"Successfully saved value: {value}"


# Workflow with multiple activity nodes executed sequentially
@workflow.defn
class MultipleNodesWorkflow:
    """
    Workflow that executes multiple activities in sequence:
    1. Validate input
    2. Transform data
    3. Save result
    """

    @workflow.run
    async def run(self, input_value: int) -> str:
        """Execute the workflow with the given input value."""
        workflow.logger.info(f"Starting workflow with input: {input_value}")

        # Node 1: Validate input
        is_valid = await workflow.execute_activity(
            validate_input,
            input_value,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not is_valid:
            workflow.logger.warning("Input validation failed")
            return "Input validation failed"

        # Node 2: Transform data
        transformed = await workflow.execute_activity(
            transform_data,
            input_value,
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Node 3: Save result
        save_message = await workflow.execute_activity(
            save_result,
            transformed,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Workflow completed: {save_message}")
        return save_message
