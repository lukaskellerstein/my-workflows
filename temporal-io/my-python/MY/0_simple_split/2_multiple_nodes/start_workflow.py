"""
Workflow Starter Script - Multiple Nodes
Simple Python script to start a new multiple-nodes workflow instance.
"""
import asyncio
import uuid

from temporalio.client import Client

from workflow_definitions import MultipleNodesWorkflow

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "0-simple-multiple-nodes-task-queue"


async def start_workflow(input_value: int, workflow_id: str = None) -> str:
    """
    Start a new multiple-nodes workflow instance.

    Args:
        input_value: The input value to process (must be positive)
        workflow_id: Optional workflow ID (auto-generated if not provided)

    Returns:
        The workflow result message
    """
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)

    # Generate workflow ID if not provided
    if workflow_id is None:
        workflow_id = f"multiple-nodes-workflow-{uuid.uuid4()}"

    print(f"Starting workflow with ID: {workflow_id}")
    print(f"Input value: {input_value}")

    # Start and wait for workflow completion
    result = await client.execute_workflow(
        MultipleNodesWorkflow.run,
        input_value,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"Workflow completed: {result}")
    return result


async def main():
    """Main entry point."""
    # Example 1: Valid input
    print("=== Example 1: Valid input ===")
    await start_workflow(input_value=15)

    print("\n=== Example 2: Invalid input (should fail validation) ===")
    await start_workflow(input_value=-5)


if __name__ == "__main__":
    asyncio.run(main())
