"""
Workflow Starter Script
This script triggers workflows that will be processed by workers running in Kubernetes.
Run this from your local machine.
"""
import asyncio
import os
import sys
from datetime import timedelta

from temporalio import workflow
from temporalio.client import Client


# Workflow definition (must match the worker)
@workflow.defn
class MultipleNodesWorkflow:
    @workflow.run
    async def run(self, input_value: int) -> str:
        ...


async def start_workflow(
    temporal_host: str,
    task_queue: str,
    workflow_id: str,
    input_value: int,
    namespace: str = "default",
):
    """Start a workflow execution"""
    print(f"Connecting to Temporal at {temporal_host}...")

    try:
        client = await Client.connect(temporal_host, namespace=namespace)
        print(f"✓ Connected to Temporal server")
    except Exception as e:
        print(f"✗ Failed to connect to Temporal: {e}")
        sys.exit(1)

    print(f"\nStarting workflow:")
    print(f"  Workflow ID: {workflow_id}")
    print(f"  Task Queue: {task_queue}")
    print(f"  Input Value: {input_value}")
    print(f"  Namespace: {namespace}")

    try:
        handle = await client.start_workflow(
            MultipleNodesWorkflow.run,
            input_value,
            id=workflow_id,
            task_queue=task_queue,
        )

        print(f"\n✓ Workflow started successfully!")
        print(f"  Run ID: {handle.result_run_id}")
        print(f"  Workflow ID: {workflow_id}")
        print(f"\nWaiting for workflow to complete...")

        result = await handle.result()

        print(f"\n✓ Workflow completed!")
        print(f"  Result: {result}")

        return result

    except Exception as e:
        print(f"\n✗ Error starting/executing workflow: {e}")
        sys.exit(1)


async def get_workflow_status(
    temporal_host: str,
    workflow_id: str,
    namespace: str = "default",
):
    """Get the status of a running workflow"""
    print(f"Connecting to Temporal at {temporal_host}...")

    try:
        client = await Client.connect(temporal_host, namespace=namespace)
        print(f"✓ Connected to Temporal server")
    except Exception as e:
        print(f"✗ Failed to connect to Temporal: {e}")
        sys.exit(1)

    try:
        handle = client.get_workflow_handle(workflow_id)
        description = await handle.describe()

        print(f"\nWorkflow Status:")
        print(f"  Workflow ID: {workflow_id}")
        print(f"  Run ID: {description.run_id}")
        print(f"  Status: {description.status}")
        print(f"  Type: {description.workflow_type}")
        print(f"  Task Queue: {description.task_queue}")
        print(f"  Start Time: {description.start_time}")

        if description.close_time:
            print(f"  Close Time: {description.close_time}")

    except Exception as e:
        print(f"\n✗ Error getting workflow status: {e}")
        sys.exit(1)


async def main():
    """Main entry point"""

    temporal_host = os.getenv("TEMPORAL_HOST", "192.168.5.65:30733")
    task_queue = os.getenv("TASK_QUEUE", "k8s-multiple-nodes-task-queue")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")

    print("=" * 60)
    print("Temporal Workflow Starter")
    print("=" * 60)

    if len(sys.argv) < 2:
        print("\nUsage:")
        print(f"  {sys.argv[0]} start <input_value> [workflow_id]")
        print(f"  {sys.argv[0]} status <workflow_id>")
        print(f"\nExamples:")
        print(f"  {sys.argv[0]} start 42")
        print(f"  {sys.argv[0]} start 42 my-workflow-1")
        print(f"  {sys.argv[0]} status my-workflow-1")
        print(f"\nEnvironment Variables:")
        print(f"  TEMPORAL_HOST: {temporal_host}")
        print(f"  TASK_QUEUE: {task_queue}")
        print(f"  TEMPORAL_NAMESPACE: {namespace}")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        if len(sys.argv) < 3:
            print("Error: Missing input_value argument")
            sys.exit(1)

        try:
            input_value = int(sys.argv[2])
        except ValueError:
            print(f"Error: input_value must be an integer, got: {sys.argv[2]}")
            sys.exit(1)

        if len(sys.argv) >= 4:
            workflow_id = sys.argv[3]
        else:
            import time
            workflow_id = f"k8s-workflow-{int(time.time())}"

        await start_workflow(
            temporal_host=temporal_host,
            task_queue=task_queue,
            workflow_id=workflow_id,
            input_value=input_value,
            namespace=namespace,
        )

    elif command == "status":
        if len(sys.argv) < 3:
            print("Error: Missing workflow_id argument")
            sys.exit(1)

        workflow_id = sys.argv[2]

        await get_workflow_status(
            temporal_host=temporal_host,
            workflow_id=workflow_id,
            namespace=namespace,
        )

    else:
        print(f"Error: Unknown command: {command}")
        print("Valid commands: start, status")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
