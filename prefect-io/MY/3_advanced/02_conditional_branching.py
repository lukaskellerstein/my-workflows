"""
Example 2: Dynamic Conditional Branching

Demonstrates how to create workflows with dynamic conditional paths.
The workflow structure changes based on runtime conditions and data.

Key Concepts:
- Runtime conditional execution
- Dynamic path selection
- Multi-way branching based on data
- Conditional task submission
- State-dependent workflow paths
"""

from prefect import flow, task, get_run_logger
from typing import List, Dict, Any, Optional
import time
from enum import Enum


# ========== Simple Conditional Branching ==========

class DataQuality(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"


@task
def assess_data_quality(data: Dict[str, Any]) -> DataQuality:
    """Assesses data quality and returns quality level."""
    logger = get_run_logger()
    logger.info(f"Assessing data quality for: {data.get('name', 'unknown')}")
    time.sleep(0.1)

    # Quality assessment logic
    completeness = data.get("completeness", 0)
    accuracy = data.get("accuracy", 0)

    if completeness < 0.5 or accuracy < 0.5:
        quality = DataQuality.INVALID
    elif completeness >= 0.9 and accuracy >= 0.9:
        quality = DataQuality.HIGH
    elif completeness >= 0.7 and accuracy >= 0.7:
        quality = DataQuality.MEDIUM
    else:
        quality = DataQuality.LOW

    logger.info(f"Quality assessed: {quality.value}")
    return quality


@task
def process_high_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processing for high-quality data (fast path)."""
    logger = get_run_logger()
    logger.info(f"Fast processing for high-quality data: {data.get('name')}")
    time.sleep(0.1)

    return {
        **data,
        "processed": True,
        "processing_type": "fast_track",
        "enhanced": True
    }


@task
def process_medium_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processing for medium-quality data (standard path)."""
    logger = get_run_logger()
    logger.info(f"Standard processing for medium-quality data: {data.get('name')}")
    time.sleep(0.2)

    return {
        **data,
        "processed": True,
        "processing_type": "standard",
        "enhanced": False
    }


@task
def process_low_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """Processing for low-quality data (remediation path)."""
    logger = get_run_logger()
    logger.info(f"Remediation processing for low-quality data: {data.get('name')}")
    time.sleep(0.3)

    # Attempt to improve data quality
    return {
        **data,
        "processed": True,
        "processing_type": "remediation",
        "remediation_applied": True,
        "completeness": min(data.get("completeness", 0) + 0.2, 1.0),
        "accuracy": min(data.get("accuracy", 0) + 0.2, 1.0)
    }


@task
def reject_invalid_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Rejects invalid data."""
    logger = get_run_logger()
    logger.warning(f"Rejecting invalid data: {data.get('name')}")

    return {
        **data,
        "processed": False,
        "rejected": True,
        "reason": "Data quality too low"
    }


@flow(name="Quality-Based Branching", log_prints=True)
def quality_based_branching_flow(datasets: List[Dict[str, Any]] = None):
    """
    Demonstrates conditional branching based on data quality.

    Different datasets take different paths through the workflow.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("QUALITY-BASED CONDITIONAL BRANCHING")
    print(f"{'='*70}\n")

    if datasets is None:
        datasets = [
            {"name": "dataset_A", "completeness": 0.95, "accuracy": 0.92},
            {"name": "dataset_B", "completeness": 0.75, "accuracy": 0.78},
            {"name": "dataset_C", "completeness": 0.62, "accuracy": 0.55},
            {"name": "dataset_D", "completeness": 0.45, "accuracy": 0.40},
            {"name": "dataset_E", "completeness": 0.88, "accuracy": 0.91},
        ]

    print(f"Processing {len(datasets)} datasets with dynamic branching\n")

    results = []

    for data in datasets:
        print(f"\nProcessing: {data['name']}")
        print(f"  Completeness: {data['completeness']:.0%}, Accuracy: {data['accuracy']:.0%}")

        # Assess quality - this determines the path
        quality = assess_data_quality(data)
        print(f"  Quality: {quality.value}")

        # Dynamic branching - different paths based on quality
        if quality == DataQuality.HIGH:
            print(f"  → Taking HIGH quality path (fast track)")
            result = process_high_quality(data)
        elif quality == DataQuality.MEDIUM:
            print(f"  → Taking MEDIUM quality path (standard)")
            result = process_medium_quality(data)
        elif quality == DataQuality.LOW:
            print(f"  → Taking LOW quality path (remediation)")
            result = process_low_quality(data)
        else:  # INVALID
            print(f"  → Taking INVALID path (rejection)")
            result = reject_invalid_data(data)

        results.append(result)

    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")

    processing_types = {}
    for result in results:
        proc_type = result.get("processing_type", "rejected")
        processing_types[proc_type] = processing_types.get(proc_type, 0) + 1

    for proc_type, count in processing_types.items():
        print(f"{proc_type}: {count} datasets")

    print(f"{'='*70}")

    return results


# ========== Multi-Stage Conditional Processing ==========

@task
def validate_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Validates a transaction."""
    logger = get_run_logger()
    logger.info(f"Validating transaction {transaction['id']}")
    time.sleep(0.1)

    amount = transaction.get("amount", 0)
    account_balance = transaction.get("account_balance", 0)

    return {
        **transaction,
        "validation": {
            "sufficient_funds": account_balance >= amount,
            "amount_valid": 0 < amount <= 10000,
            "account_valid": account_balance >= 0
        }
    }


@task
def process_normal_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Processes normal transaction."""
    logger = get_run_logger()
    logger.info(f"Processing normal transaction {transaction['id']}")
    time.sleep(0.1)

    return {
        **transaction,
        "status": "completed",
        "processing_path": "normal"
    }


@task
def request_manual_approval(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Requests manual approval for transaction."""
    logger = get_run_logger()
    logger.info(f"Requesting manual approval for transaction {transaction['id']}")
    time.sleep(0.2)

    # Simulate manual approval (in reality, this would be async)
    approved = transaction.get("amount", 0) < 5000  # Auto-approve if < 5000

    return {
        **transaction,
        "manual_review": True,
        "approved": approved
    }


@task
def process_approved_transaction(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Processes manually approved transaction."""
    logger = get_run_logger()
    logger.info(f"Processing approved transaction {transaction['id']}")
    time.sleep(0.1)

    return {
        **transaction,
        "status": "completed",
        "processing_path": "manual_approved"
    }


@task
def decline_transaction(transaction: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Declines a transaction."""
    logger = get_run_logger()
    logger.warning(f"Declining transaction {transaction['id']}: {reason}")

    return {
        **transaction,
        "status": "declined",
        "reason": reason,
        "processing_path": "declined"
    }


@flow(name="Multi-Stage Conditional Flow", log_prints=True)
def multi_stage_conditional_flow(transactions: List[Dict[str, Any]] = None):
    """
    Demonstrates multi-stage conditional processing with complex branching.

    Each transaction can take multiple different paths through the workflow
    based on validation results and approval status.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("MULTI-STAGE CONDITIONAL PROCESSING")
    print(f"{'='*70}\n")

    if transactions is None:
        transactions = [
            {"id": 1, "amount": 100, "account_balance": 1000},
            {"id": 2, "amount": 500, "account_balance": 300},   # Insufficient funds
            {"id": 3, "amount": 3000, "account_balance": 5000},  # Needs approval
            {"id": 4, "amount": 15000, "account_balance": 20000},  # Invalid amount
            {"id": 5, "amount": 200, "account_balance": 500},
        ]

    print(f"Processing {len(transactions)} transactions\n")

    results = []

    for txn in transactions:
        print(f"\nTransaction {txn['id']}: ${txn['amount']}")
        print(f"  Account balance: ${txn['account_balance']}")

        # Stage 1: Validation
        validated = validate_transaction(txn)
        validation = validated["validation"]

        # Stage 2: Conditional path based on validation
        if not validation["amount_valid"]:
            print(f"  → DECLINED: Invalid amount")
            result = decline_transaction(validated, "Invalid amount")

        elif not validation["account_valid"]:
            print(f"  → DECLINED: Invalid account")
            result = decline_transaction(validated, "Invalid account")

        elif not validation["sufficient_funds"]:
            print(f"  → DECLINED: Insufficient funds")
            result = decline_transaction(validated, "Insufficient funds")

        elif txn["amount"] > 2000:
            # Large transaction needs approval
            print(f"  → MANUAL REVIEW: Large amount")
            approval = request_manual_approval(validated)

            # Stage 3: Conditional path based on approval
            if approval["approved"]:
                print(f"    → APPROVED: Processing")
                result = process_approved_transaction(approval)
            else:
                print(f"    → DECLINED: Not approved")
                result = decline_transaction(approval, "Manual review declined")

        else:
            print(f"  → NORMAL: Processing")
            result = process_normal_transaction(validated)

        results.append(result)

    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")

    by_path = {}
    for result in results:
        path = result.get("processing_path", "unknown")
        by_path[path] = by_path.get(path, 0) + 1

    for path, count in by_path.items():
        print(f"{path}: {count} transactions")

    print(f"{'='*70}")

    return results


# ========== Dynamic Feature Flags ==========

@task
def check_feature_flags(user: Dict[str, Any]) -> Dict[str, bool]:
    """Checks which features are enabled for a user."""
    logger = get_run_logger()
    logger.info(f"Checking feature flags for user {user['id']}")
    time.sleep(0.05)

    # Simulate feature flag evaluation based on user attributes
    tier = user.get("tier", "free")
    region = user.get("region", "US")

    flags = {
        "analytics_v2": tier in ["premium", "enterprise"],
        "ai_assistant": tier == "enterprise",
        "beta_features": user.get("beta_tester", False),
        "regional_compliance": region in ["EU", "UK"],
        "advanced_reporting": tier in ["premium", "enterprise"]
    }

    return flags


@task
def run_analytics_v2(user: Dict[str, Any]) -> Dict[str, Any]:
    """Runs new analytics (feature flag gated)."""
    logger = get_run_logger()
    logger.info(f"Running Analytics v2 for user {user['id']}")
    time.sleep(0.2)

    return {"feature": "analytics_v2", "result": "completed"}


@task
def run_ai_assistant(user: Dict[str, Any]) -> Dict[str, Any]:
    """Runs AI assistant (feature flag gated)."""
    logger = get_run_logger()
    logger.info(f"Running AI Assistant for user {user['id']}")
    time.sleep(0.3)

    return {"feature": "ai_assistant", "result": "completed"}


@task
def apply_regional_compliance(user: Dict[str, Any]) -> Dict[str, Any]:
    """Applies regional compliance (feature flag gated)."""
    logger = get_run_logger()
    logger.info(f"Applying regional compliance for user {user['id']}")
    time.sleep(0.1)

    return {"feature": "regional_compliance", "result": "completed"}


@task
def run_advanced_reporting(user: Dict[str, Any]) -> Dict[str, Any]:
    """Runs advanced reporting (feature flag gated)."""
    logger = get_run_logger()
    logger.info(f"Running advanced reporting for user {user['id']}")
    time.sleep(0.15)

    return {"feature": "advanced_reporting", "result": "completed"}


@flow(name="Feature Flag Branching", log_prints=True)
def feature_flag_branching_flow(users: List[Dict[str, Any]] = None):
    """
    Demonstrates dynamic workflow paths based on feature flags.

    Each user gets a different set of features enabled, creating
    a unique workflow path.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("FEATURE FLAG-BASED BRANCHING")
    print(f"{'='*70}\n")

    if users is None:
        users = [
            {"id": 1, "tier": "free", "region": "US", "beta_tester": False},
            {"id": 2, "tier": "premium", "region": "EU", "beta_tester": True},
            {"id": 3, "tier": "enterprise", "region": "US", "beta_tester": False},
            {"id": 4, "tier": "premium", "region": "UK", "beta_tester": False},
        ]

    print(f"Processing {len(users)} users with dynamic feature flags\n")

    all_results = []

    for user in users:
        print(f"\nUser {user['id']}: {user['tier']} tier, {user['region']}")

        # Check feature flags
        flags = check_feature_flags(user)
        enabled_features = [k for k, v in flags.items() if v]
        print(f"  Enabled features: {', '.join(enabled_features) if enabled_features else 'none'}")

        user_results = []

        # Conditionally run features based on flags
        if flags["analytics_v2"]:
            print(f"    → Running Analytics v2")
            result = run_analytics_v2(user)
            user_results.append(result)

        if flags["ai_assistant"]:
            print(f"    → Running AI Assistant")
            result = run_ai_assistant(user)
            user_results.append(result)

        if flags["regional_compliance"]:
            print(f"    → Applying Regional Compliance")
            result = apply_regional_compliance(user)
            user_results.append(result)

        if flags["advanced_reporting"]:
            print(f"    → Running Advanced Reporting")
            result = run_advanced_reporting(user)
            user_results.append(result)

        all_results.append({
            "user_id": user["id"],
            "features_run": user_results,
            "feature_count": len(user_results)
        })

    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")

    for result in all_results:
        print(f"User {result['user_id']}: {result['feature_count']} features executed")

    print(f"{'='*70}")

    return all_results


# ========== Comprehensive Demo ==========

@flow(name="Conditional Branching Demo", log_prints=True)
def comprehensive_demo():
    """Runs all conditional branching examples."""
    print("="*70)
    print("COMPREHENSIVE CONDITIONAL BRANCHING DEMONSTRATION")
    print("="*70)

    # Example 1: Quality-based branching
    print("\n\nEXAMPLE 1: Quality-Based Branching")
    print("="*70)
    quality_based_branching_flow()

    # Example 2: Multi-stage conditional
    print("\n\nEXAMPLE 2: Multi-Stage Conditional Processing")
    print("="*70)
    multi_stage_conditional_flow()

    # Example 3: Feature flag branching
    print("\n\nEXAMPLE 3: Feature Flag-Based Branching")
    print("="*70)
    feature_flag_branching_flow()

    print("\n" + "="*70)
    print("All conditional branching examples completed")
    print("="*70)


if __name__ == "__main__":
    comprehensive_demo()
