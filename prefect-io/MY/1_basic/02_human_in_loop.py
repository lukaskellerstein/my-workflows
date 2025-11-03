"""
Example 2: Human in the Loop

Demonstrates workflows that require human approval or input before proceeding.
This is a simplified example for learning the basic pattern.

Note: In production, you would integrate with external approval systems
(email, Slack, web forms, etc.). This example uses a simulated approval.
"""

import time
from datetime import datetime
from prefect import flow, task, get_run_logger


# ========== Simulated Approval System ==========

# In reality, this would be an external database or service
APPROVAL_STORE = {}


@task
def request_approval(request_id: str, details: dict) -> str:
    """
    Sends an approval request to a human.

    In production, this would:
    - Send an email with approval links
    - Post to Slack with approve/reject buttons
    - Create a web form for approval
    - Store request in database
    """
    logger = get_run_logger()
    logger.info(f"Approval request sent: {request_id}")

    print(f"\n{'='*60}")
    print(f"🔔 APPROVAL REQUIRED")
    print(f"{'='*60}")
    print(f"Request ID: {request_id}")
    for key, value in details.items():
        print(f"{key}: {value}")
    print(f"{'='*60}\n")

    return request_id


@task(retries=5, retry_delay_seconds=2)
def wait_for_approval(request_id: str) -> dict:
    """
    Waits for human approval.

    In production, this would:
    - Poll a database for approval status
    - Wait for webhook callback
    - Check message queue
    """
    logger = get_run_logger()

    # Check if approval was granted
    if request_id in APPROVAL_STORE:
        approval = APPROVAL_STORE[request_id]
        logger.info(f"Approval received: {approval['status']}")
        return approval

    # No approval yet - this will cause retry
    logger.info(f"Waiting for approval on {request_id}...")
    raise Exception(f"Approval pending for {request_id}")


@task
def process_with_approval(data: dict) -> dict:
    """Processes data after receiving approval."""
    logger = get_run_logger()
    logger.info(f"Processing approved data: {data}")

    # Simulate processing
    time.sleep(1)

    return {
        "status": "processed",
        "data": data,
        "processed_at": datetime.now().isoformat()
    }


# ========== Helper Function (not a task) ==========

def simulate_human_approval(request_id: str, approved: bool = True, comment: str = ""):
    """
    Simulates a human approving/rejecting a request.

    In reality, this would be triggered by:
    - Web form submission
    - Email link click
    - Slack button press
    - API call from external system
    """
    APPROVAL_STORE[request_id] = {
        "status": "approved" if approved else "rejected",
        "approved": approved,
        "comment": comment,
        "timestamp": datetime.now().isoformat(),
        "approver": "human_operator"
    }


# ========== Flows ==========

@flow(name="Simple Approval Flow", log_prints=True)
def simple_approval_flow(data: dict = None):
    """
    Basic workflow that requires human approval.

    Steps:
    1. Prepare data
    2. Request approval
    3. Wait for approval
    4. Process if approved
    """
    logger = get_run_logger()

    if data is None:
        data = {"action": "delete_database", "database": "production"}

    print(f"\n{'='*60}")
    print("SIMPLE APPROVAL WORKFLOW")
    print(f"{'='*60}\n")

    # Step 1: Request approval
    print("Step 1: Requesting approval...")
    request_id = f"approval_{int(time.time())}"
    request_approval(request_id, {
        "Action": data["action"],
        "Database": data["database"],
        "Requested at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Simulate human approval after 3 seconds
    print("⏳ Simulating human decision in 3 seconds...")
    time.sleep(3)
    simulate_human_approval(request_id, approved=True, comment="Approved by admin")

    # Step 2: Wait for approval (with retries)
    print("\nStep 2: Waiting for approval...")
    approval = wait_for_approval(request_id)

    # Step 3: Process based on approval
    if approval["approved"]:
        print(f"\n✓ Approval granted: {approval['comment']}")
        print("\nStep 3: Processing approved action...")
        result = process_with_approval(data)
        print(f"✓ Processing complete: {result['status']}")

        return {
            "status": "success",
            "approval": approval,
            "result": result
        }
    else:
        print(f"\n✗ Approval denied: {approval.get('comment', 'No reason provided')}")
        return {
            "status": "cancelled",
            "approval": approval
        }


@flow(name="Conditional Approval Flow", log_prints=True)
def conditional_approval_flow(amount: float):
    """
    Workflow that only requires approval if amount exceeds threshold.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("CONDITIONAL APPROVAL WORKFLOW")
    print(f"{'='*60}\n")

    APPROVAL_THRESHOLD = 1000.0

    print(f"Transaction amount: ${amount:.2f}")
    print(f"Approval threshold: ${APPROVAL_THRESHOLD:.2f}\n")

    if amount > APPROVAL_THRESHOLD:
        print(f"⚠️  Amount exceeds threshold - approval required\n")

        # Request approval
        request_id = f"transaction_{int(time.time())}"
        request_approval(request_id, {
            "Transaction Amount": f"${amount:.2f}",
            "Threshold": f"${APPROVAL_THRESHOLD:.2f}",
            "Reason": "Amount exceeds approval threshold"
        })

        # Simulate approval
        print("⏳ Waiting for approval...")
        time.sleep(2)
        simulate_human_approval(request_id, approved=True, comment="Large transaction approved")

        approval = wait_for_approval(request_id)

        if not approval["approved"]:
            print(f"\n✗ Transaction cancelled: {approval['comment']}")
            return {"status": "cancelled", "amount": amount}

        print(f"\n✓ Transaction approved: {approval['comment']}")

    else:
        print("✓ Amount within threshold - no approval needed\n")

    # Process transaction
    print("Processing transaction...")
    time.sleep(1)
    print(f"✓ Transaction processed: ${amount:.2f}")

    return {
        "status": "completed",
        "amount": amount,
        "approval_required": amount > APPROVAL_THRESHOLD
    }


@flow(name="Multi-Step Approval Flow", log_prints=True)
def multi_step_approval_flow():
    """
    Workflow with multiple approval gates.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("MULTI-STEP APPROVAL WORKFLOW")
    print(f"{'='*60}\n")

    steps = [
        {"name": "Development", "requires_approval": False},
        {"name": "Staging", "requires_approval": True},
        {"name": "Production", "requires_approval": True}
    ]

    for i, step in enumerate(steps, 1):
        print(f"\nStep {i}: {step['name']}")
        print("-" * 40)

        if step["requires_approval"]:
            request_id = f"{step['name'].lower()}_{int(time.time())}"

            # Request approval
            request_approval(request_id, {
                "Stage": step['name'],
                "Action": "Deploy application"
            })

            # Simulate approval
            print(f"⏳ Waiting for {step['name']} approval...")
            time.sleep(2)
            simulate_human_approval(
                request_id,
                approved=True,
                comment=f"{step['name']} deployment approved"
            )

            approval = wait_for_approval(request_id)

            if not approval["approved"]:
                print(f"✗ Deployment stopped at {step['name']}")
                return {"status": "failed", "stopped_at": step['name']}

            print(f"✓ {step['name']} approved")

        # Deploy
        print(f"Deploying to {step['name']}...")
        time.sleep(1)
        print(f"✓ Deployed to {step['name']}")

    print(f"\n{'='*60}")
    print("✓ All stages completed successfully!")
    print(f"{'='*60}")

    return {"status": "success", "stages_completed": len(steps)}


# ========== Comprehensive Demo ==========

@flow(name="Human-in-Loop Comprehensive Demo", log_prints=True)
def comprehensive_human_in_loop_demo():
    """Runs all human-in-the-loop examples."""
    print("="*70)
    print("COMPREHENSIVE HUMAN-IN-THE-LOOP DEMONSTRATION")
    print("="*70)

    # Example 1: Simple approval
    print("\n\nEXAMPLE 1: Simple Approval")
    print("="*70)
    simple_approval_flow({"action": "delete_records", "database": "test_db"})

    # Example 2: Conditional approval
    print("\n\nEXAMPLE 2: Conditional Approval (Below Threshold)")
    print("="*70)
    conditional_approval_flow(amount=500.0)

    print("\n\nEXAMPLE 3: Conditional Approval (Above Threshold)")
    print("="*70)
    conditional_approval_flow(amount=5000.0)

    # Example 3: Multi-step approval
    print("\n\nEXAMPLE 4: Multi-Step Approval")
    print("="*70)
    multi_step_approval_flow()

    print("\n" + "="*70)
    print("All human-in-the-loop examples completed")
    print("="*70)


if __name__ == "__main__":
    comprehensive_human_in_loop_demo()
