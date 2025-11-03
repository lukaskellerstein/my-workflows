"""
Work Pool Deployment Example

This example demonstrates deploying flows to work pools for scalable execution.

Key Concepts:
- Work pools separate deployment from execution
- Workers poll work pools for scheduled runs
- Scale workers independently of deployments
- Better isolation and resource management

Architecture:
1. Deploy flow to work pool (this script)
2. Start worker to execute runs (separate process)
3. Trigger flow via UI or API
4. Worker picks up and executes run

Prerequisites:
1. Start Prefect server: cd 10_deployment && docker-compose up -d
2. Create work pool: uv run prefect work-pool create "my-pool" --type process
3. Run this script: uv run 10_deployment/05_work_pool.py
4. Start worker: uv run prefect worker start --pool "my-pool"

Note: PREFECT_API_URL is automatically set in the script
Note: Unlike serve(), deploy() returns immediately (doesn't block).
"""

import os

# Configure Prefect to use Docker Compose server
os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"

from prefect import flow, task, get_run_logger
from datetime import datetime
import time


@task(name="Heavy Computation")
def heavy_computation(data: int) -> int:
    """Simulate heavy computation."""
    logger = get_run_logger()

    logger.info(f"Starting heavy computation for: {data}")

    # Simulate work
    time.sleep(2)
    result = data ** 2

    logger.info(f"Computation complete: {data}^2 = {result}")
    return result


@task(name="Process Batch")
def process_batch(batch_id: int, items: list[int]) -> dict:
    """Process a batch of items."""
    logger = get_run_logger()

    logger.info(f"Processing batch {batch_id} with {len(items)} items")

    # Process each item
    results = []
    for item in items:
        result = heavy_computation(item)
        results.append(result)

    batch_result = {
        "batch_id": batch_id,
        "items_processed": len(results),
        "sum": sum(results),
        "results": results
    }

    logger.info(f"Batch {batch_id} complete: {batch_result}")
    return batch_result


@flow(name="Work Pool Flow", log_prints=True)
def work_pool_flow(batch_id: int = 1, batch_size: int = 5) -> dict:
    """
    A flow designed for work pool execution.

    This demonstrates:
    - Deploying to work pool
    - Worker-based execution
    - Resource isolation

    Args:
        batch_id: Identifier for this batch (default: 1)
        batch_size: Number of items to process (default: 5)

    Returns:
        dict: Processing results
    """
    logger = get_run_logger()

    logger.info(f"🚀 Starting Work Pool Flow (batch {batch_id})")

    # Generate items to process
    items = list(range(1, batch_size + 1))

    # Process batch
    result = process_batch(batch_id, items)

    summary = {
        "status": "completed",
        "batch_id": batch_id,
        "processed_at": datetime.now().isoformat(),
        "statistics": result
    }

    logger.info(f"✅ Flow completed: {summary}")

    return summary


def create_work_pool():
    """Helper to create work pool."""
    import subprocess

    print("\n📦 Creating Work Pool")
    print("-" * 60)

    try:
        result = subprocess.run(
            ["uv", "run", "prefect", "work-pool", "create", "my-pool", "--type", "process"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 or "already exists" in result.stderr:
            print("✅ Work pool 'my-pool' ready")
            return True
        else:
            print(f"❌ Error creating work pool: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def deploy_to_work_pool():
    """Deploy the flow to the work pool."""
    print("\n🚀 Deploying to Work Pool")
    print("-" * 60)

    # Deploy to work pool
    # Note: deploy() returns immediately (doesn't block like serve())
    work_pool_flow.deploy(
        name="work-pool-deployment",
        work_pool_name="my-pool",
        tags=["work-pool", "scalable", "production"],
        description="Flow deployed to work pool for scalable execution",
        # Optional: Add schedule
        # cron="0 * * * *",  # Run every hour
    )

    print("✅ Deployment complete!")
    print(f"   Name: work-pool-deployment")
    print(f"   Work Pool: my-pool")


def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print()
    print("1. Start a worker (in another terminal):")
    print("   uv run prefect worker start --pool 'my-pool'")
    print()
    print("2. Trigger the flow:")
    print()
    print("   Option A - Via UI:")
    print("     - Open: http://localhost:4200")
    print("     - Go to: Deployments → work-pool-deployment")
    print("     - Click: 'Run'")
    print()
    print("   Option B - Via CLI:")
    print("     uv run prefect deployment run 'Work Pool Flow/work-pool-deployment'")
    print()
    print("   Option C - Via API:")
    print("     (See 04_trigger_via_api.py)")
    print()
    print("3. View execution:")
    print("   - Worker logs will show execution")
    print("   - UI shows flow run: http://localhost:4200/flow-runs")
    print()
    print("=" * 60)
    print()
    print("Benefits of Work Pools:")
    print("  ✓ Scale workers independently")
    print("  ✓ Better resource isolation")
    print("  ✓ Separate deployment from execution")
    print("  ✓ Production-ready architecture")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("Work Pool Deployment Example")
    print("=" * 60)
    print()
    print("This demonstrates:")
    print("  1. Creating a work pool")
    print("  2. Deploying flow to work pool")
    print("  3. Executing via separate worker")
    print()
    print("Unlike serve(), deploy() returns immediately.")
    print("A separate worker process executes the flows.")
    print()

    # Create work pool
    if not create_work_pool():
        print("\n❌ Failed to create work pool. Exiting.")
        exit(1)

    # Deploy to work pool
    deploy_to_work_pool()

    # Show next steps
    print_next_steps()

    print("Tip: To see workers:")
    print("  uv run prefect worker ls")
    print()
    print("Tip: To see work pool details:")
    print("  uv run prefect work-pool inspect 'my-pool'")
    print()
