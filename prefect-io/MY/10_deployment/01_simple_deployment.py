"""
Simple Deployment Example

This example demonstrates how to deploy a flow to a running Prefect server.

Key Concepts:
- Using flow.serve() to create a deployment
- Flow runs on server, not in local script
- Can be triggered via UI or API
- Process blocks until stopped (Ctrl+C)

Prerequisites:
1. Start Prefect server with Docker Compose:
   cd 10_server && docker-compose up -d

2. Configure client to use Docker server:
   export PREFECT_API_URL="http://localhost:4200/api"

3. Run this script (it will block):
   uv run 10_server/01_simple_deployment.py

4. In another terminal, trigger the flow:
   - Open UI: http://localhost:4200
   - Navigate to Deployments
   - Find "simple-hello" and click "Run"

   OR use API (see 04_trigger_via_api.py)
"""

import os

# Configure Prefect to use Docker Compose server
# This must be set BEFORE importing prefect
os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"

from prefect import flow, task, get_run_logger
from datetime import datetime


@task(name="Greet User")
def greet(name: str) -> str:
    """Generate a greeting message."""
    logger = get_run_logger()
    message = f"Hello, {name}! 👋"
    logger.info(message)
    return message


@task(name="Get Current Time")
def get_timestamp() -> str:
    """Get current timestamp."""
    logger = get_run_logger()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Current time: {now}")
    return now


@flow(name="Simple Hello Flow", log_prints=True)
def hello_flow(name: str = "World") -> dict:
    """
    A simple flow that demonstrates server deployment.

    Args:
        name: Name to greet (default: "World")

    Returns:
        dict: Results containing greeting and timestamp
    """
    logger = get_run_logger()

    logger.info("🚀 Starting Simple Hello Flow")

    # Execute tasks
    greeting = greet(name)
    timestamp = get_timestamp()

    # Compile results
    result = {
        "greeting": greeting,
        "timestamp": timestamp,
        "flow_run": "completed successfully",
    }

    logger.info(f"✅ Flow completed: {result}")

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("Simple Deployment Example")
    print("=" * 60)
    print()
    print("This will deploy the flow to your Prefect server.")
    print()
    print("Prerequisites:")
    print("1. Prefect server running: docker-compose up -d")
    print("2. API URL configured: export PREFECT_API_URL='http://localhost:4200/api'")
    print()
    print("After deployment:")
    print("- Open UI: http://localhost:4200")
    print("- Navigate to: Deployments → simple-hello")
    print("- Click 'Run' to trigger the flow")
    print()
    print("This script will block. Press Ctrl+C to stop serving.")
    print("=" * 60)
    print()

    # Deploy the flow with serve()
    # This blocks until Ctrl+C
    hello_flow.serve(
        name="simple-hello",
        tags=["example", "simple", "server"],
        description="A simple hello world flow for learning deployments",
    )
