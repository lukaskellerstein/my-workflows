"""Cleanup script to terminate ALL running workflows"""
import asyncio
from temporalio.client import Client

async def main():
    client = await Client.connect("localhost:7233")

    # List all workflows (no filter = all running workflows)
    print("Fetching all running workflows...")

    workflows_to_terminate = []

    async for workflow in client.list_workflows():
        workflows_to_terminate.append(workflow.id)
        print(f"Found: {workflow.id}")

    print(f"\nTotal workflows to terminate: {len(workflows_to_terminate)}")

    if not workflows_to_terminate:
        print("No workflows to terminate!")
        return

    # Terminate each one
    for workflow_id in workflows_to_terminate:
        try:
            handle = client.get_workflow_handle(workflow_id)
            await handle.terminate("Cleaning up all old workflows")
            print(f"✓ Terminated: {workflow_id}")
        except Exception as e:
            print(f"✗ Failed to terminate {workflow_id}: {e}")

    print("\nCleanup complete!")

if __name__ == "__main__":
    asyncio.run(main())
