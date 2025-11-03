"""
Example: Human in the Loop - Approval Pattern

Demonstrates workflows that require human approval or input before proceeding.

Note: This is a simplified simulation. In production, you would integrate with:
- External approval systems (email, Slack, web forms)
- Prefect UI manual task runs
- Message queues or webhooks
"""

import time
from prefect import flow, task, get_run_logger
from datetime import datetime


# ========== Simulated Approval System ==========

# In a real system, this would be an external database or service
APPROVAL_STORE = {}


def simulate_approval_request(request_id: str, details: dict) -> None:
    """Simulates sending an approval request to a human."""
    logger = get_run_logger()
    logger.info(f"Approval request sent: {request_id}")

    # In reality, this would send an email, Slack message, or create a web form
    print(f"\n{'='*60}")
    print(f"🔔 APPROVAL REQUIRED")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    print(f"Details: {details}")
    print(f"{'='*60}\n")


def wait_for_approval(request_id: str, timeout_seconds: int = 10) -> dict:
    """
    Waits for human approval.

    In a real system, this would:
    - Poll a database for approval status
    - Wait for a webhook callback
    - Check a message queue
    """
    logger = get_run_logger()
    logger.info(f"Waiting for approval on request {request_id}...")

    start_time = time.time()

    # Simulate waiting for approval (with timeout)
    while time.time() - start_time < timeout_seconds:
        # Check if approval was granted (simulated)
        if request_id in APPROVAL_STORE:
            approval = APPROVAL_STORE[request_id]
            logger.info(f"Approval received: {approval['status']}")
            return approval

        time.sleep(1)

    # Timeout - no approval received
    logger.warning(f"Approval timeout for request {request_id}")
    return {
        "status": "timeout",
        "approved": False,
        "reason": "No response within timeout period"
    }


def simulate_human_approval(request_id: str, approved: bool = True, comment: str = ""):
    """
    Simulates a human approving/rejecting a request.

    In a real system, this would be triggered by:
    - A web form submission
    - An email response
    - A Slack button click
    - An API call from external system
    """
    APPROVAL_STORE[request_id] = {
        "status": "approved" if approved else "rejected",
        "approved": approved,
        "comment": comment,
        "timestamp": datetime.now().isoformat(),
        "approver": "human_operator"
    }


# ========== Workflow Tasks ==========

@task
def prepare_deployment(app_name: str, version: str) -> dict:
    """Prepares a deployment package."""
    logger = get_run_logger()
    logger.info(f"Preparing deployment: {app_name} v{version}")

    return {
        "app_name": app_name,
        "version": version,
        "package_size": "125 MB",
        "changes": [
            "Updated authentication module",
            "Fixed critical bug in payment processing",
            "Added new user dashboard"
        ]
    }


@task
def deploy_to_production(deployment_info: dict) -> dict:
    """Deploys to production environment."""
    logger = get_run_logger()
    logger.info(f"Deploying {deployment_info['app_name']} to production...")

    time.sleep(2)  # Simulate deployment

    return {
        "status": "deployed",
        "app_name": deployment_info["app_name"],
        "version": deployment_info["version"],
        "deployed_at": datetime.now().isoformat()
    }


@task
def rollback_deployment(deployment_info: dict) -> dict:
    """Rolls back a deployment."""
    logger = get_run_logger()
    logger.warning(f"Rolling back {deployment_info['app_name']}...")

    return {
        "status": "rolled_back",
        "app_name": deployment_info["app_name"],
        "rolled_back_at": datetime.now().isoformat()
    }


@task
def process_large_batch(batch_id: int, record_count: int) -> dict:
    """Processes a large batch of records."""
    logger = get_run_logger()
    logger.info(f"Processing batch {batch_id} with {record_count} records")

    return {
        "batch_id": batch_id,
        "records_processed": record_count,
        "estimated_cost": record_count * 0.001  # $0.001 per record
    }


# ========== Approval Workflows ==========

@flow(name="Deployment Approval Flow", log_prints=True)
def deployment_approval_flow(app_name: str = "MyApp", version: str = "2.0.0"):
    """
    Deployment workflow that requires human approval before deploying to production.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print(f"DEPLOYMENT WORKFLOW: {app_name} v{version}")
    print(f"{'='*60}\n")

    # Step 1: Prepare deployment
    print("Step 1: Preparing deployment package...")
    deployment_info = prepare_deployment(app_name, version)
    print(f"✓ Package prepared: {deployment_info['package_size']}")
    print(f"  Changes:")
    for change in deployment_info["changes"]:
        print(f"    - {change}")

    # Step 2: Request approval
    print("\nStep 2: Requesting approval for production deployment...")
    request_id = f"deploy_{app_name}_{version}_{int(time.time())}"

    simulate_approval_request(request_id, {
        "action": "Deploy to Production",
        "application": app_name,
        "version": version,
        "changes": len(deployment_info["changes"]),
        "package_size": deployment_info["package_size"]
    })

    # Simulate human approval after 3 seconds
    print("⏳ Waiting for human approval...")
    time.sleep(3)
    simulate_human_approval(request_id, approved=True, comment="Approved by DevOps team")

    # Step 3: Wait for approval
    approval = wait_for_approval(request_id, timeout_seconds=10)

    # Step 4: Act based on approval
    if approval["approved"]:
        print(f"\n✓ Approval granted: {approval['comment']}")
        print("\nStep 3: Deploying to production...")
        result = deploy_to_production(deployment_info)
        print(f"✓ Deployment complete: {result['deployed_at']}")

        return {
            "status": "success",
            "deployment": result,
            "approval": approval
        }
    else:
        print(f"\n✗ Approval denied: {approval.get('comment', approval.get('reason', 'Unknown'))}")
        print("\nDeployment cancelled.")

        return {
            "status": "cancelled",
            "approval": approval
        }


@flow(name="Batch Processing Approval Flow", log_prints=True)
def batch_processing_approval_flow(batch_size: int = 10000):
    """
    Batch processing that requires approval if cost exceeds threshold.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print(f"BATCH PROCESSING WORKFLOW")
    print(f"{'='*60}\n")

    batch_id = int(time.time())
    estimated_cost = batch_size * 0.001

    print(f"Batch ID: {batch_id}")
    print(f"Records to process: {batch_size:,}")
    print(f"Estimated cost: ${estimated_cost:.2f}")

    # Check if approval is needed (cost threshold: $5.00)
    COST_THRESHOLD = 5.00

    if estimated_cost > COST_THRESHOLD:
        print(f"\n⚠️  Cost exceeds threshold (${COST_THRESHOLD:.2f})")
        print("Requesting approval...")

        request_id = f"batch_{batch_id}"

        simulate_approval_request(request_id, {
            "action": "Process Large Batch",
            "batch_id": batch_id,
            "record_count": batch_size,
            "estimated_cost": f"${estimated_cost:.2f}",
            "threshold": f"${COST_THRESHOLD:.2f}"
        })

        print("⏳ Waiting for approval...")
        time.sleep(2)
        simulate_human_approval(request_id, approved=True, comment="Budget approved")

        approval = wait_for_approval(request_id, timeout_seconds=10)

        if not approval["approved"]:
            print(f"\n✗ Batch processing cancelled: {approval.get('reason', 'Approval denied')}")
            return {"status": "cancelled", "approval": approval}

        print(f"\n✓ Approval granted: {approval['comment']}")

    # Process batch
    print("\nProcessing batch...")
    result = process_large_batch(batch_id, batch_size)
    print(f"✓ Batch processed: {result['records_processed']:,} records")
    print(f"  Actual cost: ${result['estimated_cost']:.2f}")

    return {
        "status": "success",
        "result": result,
        "approval_required": estimated_cost > COST_THRESHOLD
    }


@flow(name="Multi-Stage Approval Flow", log_prints=True)
def multi_stage_approval_flow():
    """
    Workflow with multiple approval gates.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print(f"MULTI-STAGE APPROVAL WORKFLOW")
    print(f"{'='*60}\n")

    stages = [
        {"name": "Development", "requires_approval": False},
        {"name": "Staging", "requires_approval": True},
        {"name": "Production", "requires_approval": True},
    ]

    deployment_info = prepare_deployment("CriticalApp", "3.0.0")

    for i, stage in enumerate(stages, 1):
        print(f"\nStage {i}: {stage['name']}")
        print("-" * 40)

        if stage["requires_approval"]:
            request_id = f"stage_{stage['name'].lower()}_{int(time.time())}"

            simulate_approval_request(request_id, {
                "action": f"Deploy to {stage['name']}",
                "stage": stage['name'],
                "application": deployment_info['app_name']
            })

            print(f"⏳ Waiting for approval for {stage['name']}...")
            time.sleep(2)
            simulate_human_approval(request_id, approved=True, comment=f"{stage['name']} deployment approved")

            approval = wait_for_approval(request_id)

            if not approval["approved"]:
                print(f"✗ Deployment stopped at {stage['name']} stage")
                return {"status": "failed", "stopped_at": stage['name']}

            print(f"✓ Approved for {stage['name']}")

        # Deploy to stage
        print(f"Deploying to {stage['name']}...")
        time.sleep(1)
        print(f"✓ Deployed to {stage['name']}")

    print(f"\n{'='*60}")
    print("✓ All stages completed successfully!")
    print(f"{'='*60}")

    return {"status": "success", "stages_completed": len(stages)}


# ========== Comprehensive Demo ==========

@flow(name="Human-in-Loop Comprehensive Demo", log_prints=True)
def comprehensive_human_in_loop_demo():
    """Runs all human-in-the-loop examples."""
    print("="*70)
    print("COMPREHENSIVE HUMAN-IN-THE-LOOP DEMONSTRATION")
    print("="*70)

    # Example 1: Deployment approval
    deployment_approval_flow("WebApp", "1.5.0")

    # Example 2: Cost-based approval
    batch_processing_approval_flow(batch_size=7000)

    # Example 3: Multi-stage approval
    multi_stage_approval_flow()

    print("\n" + "="*70)
    print("All human-in-the-loop examples completed")
    print("="*70)


if __name__ == "__main__":
    comprehensive_human_in_loop_demo()
