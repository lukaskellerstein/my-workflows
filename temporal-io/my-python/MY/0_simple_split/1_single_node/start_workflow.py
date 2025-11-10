"""
Workflow Starter Script
Simple Python script to start a new workflow instance.
"""
import asyncio
import uuid

from temporalio.client import Client

from workflow_definitions import SingleNodeWorkflow

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "0-simple-single-node-task-queue"


async def start_workflow(input_value: int, workflow_id: str = None) -> int:
    """
    Start a new workflow instance.

    Args:
        input_value: The input value to process
        workflow_id: Optional workflow ID (auto-generated if not provided)

    Returns:
        The workflow result
    """
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)

    # Generate workflow ID if not provided
    if workflow_id is None:
        workflow_id = f"single-node-workflow-{uuid.uuid4()}"

    print(f"Starting workflow with ID: {workflow_id}")
    print(f"Input value: {input_value}")

    # Start and wait for workflow completion
    result = await client.execute_workflow(
        SingleNodeWorkflow.run,
        input_value,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"Workflow completed with result: {result}")
    return result


async def main():
    """Main entry point."""
    # Example: Start workflow with input value 42
    await start_workflow(input_value=42)


if __name__ == "__main__":
    asyncio.run(main())
