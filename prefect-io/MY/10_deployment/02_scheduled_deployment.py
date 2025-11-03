"""
Scheduled Deployment Example

This example demonstrates how to deploy flows with schedules.

Key Concepts:
- Cron-based scheduling
- Interval-based scheduling
- Multiple schedules for same flow
- Schedule activation/deactivation

Prerequisites:
1. Start Prefect server: cd 10_deployment && docker-compose up -d
2. Run this script: uv run 10_deployment/02_scheduled_deployment.py

Note: PREFECT_API_URL is automatically set in the script

The flow will run automatically based on the schedule.
View scheduled runs in UI: http://localhost:4200
"""

import os

# Configure Prefect to use Docker Compose server
os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"

from prefect import flow, task, get_run_logger
from datetime import datetime, timedelta
import random


@task(name="Generate Data")
def generate_data() -> list[dict]:
    """Simulate data generation."""
    logger = get_run_logger()

    # Simulate some data points
    data = [
        {"id": i, "value": random.randint(1, 100), "timestamp": datetime.now().isoformat()}
        for i in range(5)
    ]

    logger.info(f"Generated {len(data)} data points")
    return data


@task(name="Process Data")
def process_data(data: list[dict]) -> dict:
    """Process the generated data."""
    logger = get_run_logger()

    total = sum(item["value"] for item in data)
    average = total / len(data) if data else 0

    result = {
        "total_records": len(data),
        "sum": total,
        "average": round(average, 2),
        "min": min((item["value"] for item in data), default=0),
        "max": max((item["value"] for item in data), default=0)
    }

    logger.info(f"Processed data: {result}")
    return result


@task(name="Save Results")
def save_results(results: dict) -> str:
    """Simulate saving results."""
    logger = get_run_logger()

    # In real scenario, save to database/file
    filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    logger.info(f"Results saved to {filename}")
    return filename


@flow(name="Scheduled Data Processing", log_prints=True)
def scheduled_flow() -> dict:
    """
    A flow that processes data on a schedule.

    This demonstrates typical ETL patterns:
    - Extract: Generate/fetch data
    - Transform: Process data
    - Load: Save results

    Returns:
        dict: Summary of processing run
    """
    logger = get_run_logger()

    logger.info("🔄 Starting scheduled data processing")

    # Extract
    data = generate_data()

    # Transform
    processed = process_data(data)

    # Load
    filename = save_results(processed)

    summary = {
        "status": "completed",
        "processed_at": datetime.now().isoformat(),
        "statistics": processed,
        "output_file": filename
    }

    logger.info(f"✅ Processing complete: {summary}")

    return summary


if __name__ == "__main__":
    print("=" * 60)
    print("Scheduled Deployment Example")
    print("=" * 60)
    print()
    print("This demonstrates various scheduling options:")
    print()
    print("Option 1: Cron Schedule")
    print("  - Run every 5 minutes: cron='*/5 * * * *'")
    print("  - Run every hour: cron='0 * * * *'")
    print("  - Run daily at 9 AM: cron='0 9 * * *'")
    print()
    print("Option 2: Interval Schedule")
    print("  - Run every 30 seconds: interval=30")
    print("  - Run every 10 minutes: interval=600")
    print()
    print("Choose deployment option:")
    print("=" * 60)
    print()

    # For demonstration, we'll show multiple options

    # OPTION 1: Cron schedule - Every 5 minutes
    # Uncomment to use:
    # scheduled_flow.serve(
    #     name="data-processing-cron",
    #     cron="*/5 * * * *",
    #     tags=["scheduled", "cron", "etl"],
    #     description="Runs every 5 minutes via cron schedule"
    # )

    # OPTION 2: Interval schedule - Every 30 seconds (for quick testing)
    print("Deploying with 30-second interval for quick testing...")
    print("The flow will run automatically every 30 seconds.")
    print()
    print("View runs in UI: http://localhost:4200/flow-runs")
    print()
    print("Press Ctrl+C to stop serving.")
    print()

    scheduled_flow.serve(
        name="data-processing-interval",
        interval=30,  # Run every 30 seconds
        tags=["scheduled", "interval", "etl", "demo"],
        description="Runs every 30 seconds for demonstration"
    )

    # OPTION 3: Multiple schedules for same flow
    # You can deploy the same flow with different schedules:
    #
    # from prefect.deployments import Deployment
    # from prefect.server.schemas.schedules import CronSchedule, IntervalSchedule
    #
    # Deployment(
    #     flow=scheduled_flow,
    #     name="data-processing-morning",
    #     schedule=CronSchedule(cron="0 9 * * *"),  # 9 AM daily
    # )
    #
    # Deployment(
    #     flow=scheduled_flow,
    #     name="data-processing-evening",
    #     schedule=CronSchedule(cron="0 18 * * *"),  # 6 PM daily
    # )
