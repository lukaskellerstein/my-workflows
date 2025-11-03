"""
Trigger Flows via API Example

This example demonstrates how to programmatically trigger deployed flows.

Key Concepts:
- REST API interaction with Prefect server
- Finding deployments by name
- Creating flow runs with parameters
- Monitoring flow run status
- Canceling flow runs

Prerequisites:
1. Start Prefect server: cd 10_deployment && docker-compose up -d
2. Deploy a flow (e.g., run 01_simple_deployment.py in another terminal)
3. Run this script: uv run 10_deployment/04_trigger_via_api.py

Note: PREFECT_API_URL is automatically set in the script
"""

import os

# Configure Prefect to use Docker Compose server
os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"

from prefect import get_client
from prefect.exceptions import ObjectNotFound
import asyncio
from datetime import datetime


async def list_deployments():
    """List all available deployments."""
    print("\n📋 Available Deployments:")
    print("-" * 60)

    async with get_client() as client:
        deployments = await client.read_deployments()

        if not deployments:
            print("No deployments found.")
            print("\nMake sure you have a deployment running:")
            print("  uv run 10_server/01_simple_deployment.py")
            return []

        for i, deployment in enumerate(deployments, 1):
            print(f"{i}. {deployment.name}")
            print(f"   Flow: {deployment.flow_name}")
            print(f"   Tags: {deployment.tags}")
            if deployment.schedule:
                print(f"   Schedule: {deployment.schedule}")
            print()

        return deployments


async def trigger_simple_flow():
    """Trigger the simple hello flow."""
    print("\n🚀 Triggering Simple Hello Flow")
    print("-" * 60)

    async with get_client() as client:
        try:
            # Find deployment by name
            deployment = await client.read_deployment_by_name(
                "Simple Hello Flow/simple-hello"
            )

            print(f"Found deployment: {deployment.name}")
            print(f"Flow ID: {deployment.flow_id}")

            # Create a flow run with parameters
            flow_run = await client.create_flow_run_from_deployment(
                deployment.id,
                parameters={"name": "API Trigger"},
                tags=["api-triggered", "example"]
            )

            print(f"✅ Flow run created!")
            print(f"   Run ID: {flow_run.id}")
            print(f"   State: {flow_run.state.type}")
            print(f"   View in UI: http://localhost:4200/flow-runs/flow-run/{flow_run.id}")

            return flow_run

        except ObjectNotFound:
            print("❌ Deployment 'simple-hello' not found!")
            print("\nMake sure the deployment is running:")
            print("  uv run 10_server/01_simple_deployment.py")
            return None


async def trigger_parameterized_flow():
    """Trigger the parameterized ETL flow with custom parameters."""
    print("\n🚀 Triggering Parameterized ETL Flow")
    print("-" * 60)

    async with get_client() as client:
        try:
            # Find deployment
            deployment = await client.read_deployment_by_name(
                "Parameterized ETL Flow/parameterized-etl"
            )

            print(f"Found deployment: {deployment.name}")

            # Custom parameters
            parameters = {
                "source": "database",
                "limit": 15,
                "operation": "lowercase",
                "min_value": 50,
                "report_format": "detailed"
            }

            print(f"Parameters: {parameters}")

            # Create flow run
            flow_run = await client.create_flow_run_from_deployment(
                deployment.id,
                parameters=parameters,
                tags=["api-triggered", "custom-params"]
            )

            print(f"✅ Flow run created!")
            print(f"   Run ID: {flow_run.id}")
            print(f"   State: {flow_run.state.type}")
            print(f"   View in UI: http://localhost:4200/flow-runs/flow-run/{flow_run.id}")

            return flow_run

        except ObjectNotFound:
            print("❌ Deployment 'parameterized-etl' not found!")
            print("\nMake sure the deployment is running:")
            print("  uv run 10_server/03_parameterized_deployment.py")
            return None


async def monitor_flow_run(flow_run_id: str, timeout: int = 30):
    """Monitor a flow run until completion or timeout."""
    print(f"\n👀 Monitoring Flow Run: {flow_run_id}")
    print("-" * 60)

    async with get_client() as client:
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < timeout:
            flow_run = await client.read_flow_run(flow_run_id)

            print(f"State: {flow_run.state.type} | {flow_run.state.name}")

            # Check if terminal state
            if flow_run.state.is_final():
                print(f"\n✅ Flow run completed: {flow_run.state.type}")
                if flow_run.state.is_completed():
                    print("Status: SUCCESS")
                elif flow_run.state.is_failed():
                    print("Status: FAILED")
                    print(f"Message: {flow_run.state.message}")
                elif flow_run.state.is_cancelled():
                    print("Status: CANCELLED")
                break

            await asyncio.sleep(2)
        else:
            print(f"\n⏱️  Timeout reached ({timeout}s)")


async def cancel_flow_run(flow_run_id: str):
    """Cancel a running flow."""
    print(f"\n🛑 Cancelling Flow Run: {flow_run_id}")
    print("-" * 60)

    async with get_client() as client:
        await client.set_flow_run_state(
            flow_run_id,
            state={"type": "CANCELLED", "message": "Cancelled via API"}
        )

        print("✅ Flow run cancelled")


async def get_flow_run_logs(flow_run_id: str):
    """Retrieve logs for a flow run."""
    print(f"\n📝 Logs for Flow Run: {flow_run_id}")
    print("-" * 60)

    async with get_client() as client:
        logs = await client.read_logs(flow_run_filter={"id": {"any_": [flow_run_id]}})

        if not logs:
            print("No logs found (flow may not have started yet)")
            return

        for log in logs:
            timestamp = log.timestamp.strftime("%H:%M:%S")
            print(f"[{timestamp}] {log.level}: {log.message}")


async def main():
    """Main demonstration function."""
    print("=" * 60)
    print("Trigger Flows via API Example")
    print("=" * 60)

    # List available deployments
    deployments = await list_deployments()

    if not deployments:
        print("\nNo deployments available. Please start a deployment first.")
        return

    # Example 1: Trigger simple flow
    flow_run = await trigger_simple_flow()

    if flow_run:
        # Wait a moment for flow to start
        await asyncio.sleep(3)

        # Get logs
        await get_flow_run_logs(str(flow_run.id))

        # Monitor until completion (with short timeout for demo)
        await monitor_flow_run(str(flow_run.id), timeout=30)

    # Example 2: Trigger parameterized flow
    print("\n" + "=" * 60)
    param_flow_run = await trigger_parameterized_flow()

    if param_flow_run:
        await asyncio.sleep(3)
        await get_flow_run_logs(str(param_flow_run.id))

    print("\n" + "=" * 60)
    print("✅ API Trigger Examples Complete")
    print("=" * 60)
    print("\nView all runs in UI: http://localhost:4200/flow-runs")


if __name__ == "__main__":
    asyncio.run(main())
