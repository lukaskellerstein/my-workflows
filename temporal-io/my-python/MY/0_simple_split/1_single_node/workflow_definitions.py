"""
Workflow and Activity Definitions
Shared definitions for the single node workflow example.
"""
from datetime import timedelta

from temporalio import activity, workflow


# Single activity that processes data
@activity.defn
def process_data(input_value: int) -> int:
    """Process input data by doubling it."""
    activity.logger.info(f"Processing data: {input_value}")
    result = input_value * 2
    activity.logger.info(f"Result: {result}")
    return result


# Workflow with a single activity node
@workflow.defn
class SingleNodeWorkflow:
    """Simple workflow that executes a single activity."""

    @workflow.run
    async def run(self, input_value: int) -> int:
        """Execute the workflow with the given input value."""
        workflow.logger.info(f"Starting workflow with input: {input_value}")

        # Execute single activity
        result = await workflow.execute_activity(
            process_data,
            input_value,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Workflow completed with result: {result}")
        return result
