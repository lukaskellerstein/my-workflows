"""
Parameterized Deployment Example

This example demonstrates how to create deployments that accept parameters.

Key Concepts:
- Flow parameters with type hints
- Default parameter values
- Passing parameters via UI
- Passing parameters via API
- Parameter validation

Prerequisites:
1. Start Prefect server: cd 10_deployment && docker-compose up -d
2. Run this script: uv run 10_deployment/03_parameterized_deployment.py

Note: PREFECT_API_URL is automatically set in the script

To trigger with parameters:
- UI: Click deployment → Custom Run → Enter parameters
- API: Use 04_trigger_via_api.py
"""

import os

# Configure Prefect to use Docker Compose server
os.environ["PREFECT_API_URL"] = "http://localhost:4200/api"

from prefect import flow, task, get_run_logger
from datetime import datetime
from typing import Literal


@task(name="Fetch Data")
def fetch_data(source: str, limit: int) -> list[dict]:
    """Simulate fetching data from a source."""
    logger = get_run_logger()

    logger.info(f"Fetching data from {source} (limit: {limit})")

    # Simulate data based on source
    data = [
        {
            "id": i,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "value": i * 10
        }
        for i in range(1, limit + 1)
    ]

    logger.info(f"Fetched {len(data)} records from {source}")
    return data


@task(name="Transform Data")
def transform_data(
    data: list[dict],
    operation: Literal["uppercase", "lowercase", "capitalize"]
) -> list[dict]:
    """Transform data based on operation."""
    logger = get_run_logger()

    logger.info(f"Applying transformation: {operation}")

    transformed = []
    for item in data:
        transformed_item = item.copy()
        source = item["source"]

        if operation == "uppercase":
            transformed_item["source"] = source.upper()
        elif operation == "lowercase":
            transformed_item["source"] = source.lower()
        elif operation == "capitalize":
            transformed_item["source"] = source.capitalize()

        transformed.append(transformed_item)

    logger.info(f"Transformed {len(transformed)} records")
    return transformed


@task(name="Filter Data")
def filter_data(data: list[dict], min_value: int) -> list[dict]:
    """Filter data by minimum value."""
    logger = get_run_logger()

    filtered = [item for item in data if item["value"] >= min_value]

    logger.info(f"Filtered from {len(data)} to {len(filtered)} records (min_value: {min_value})")
    return filtered


@task(name="Generate Report")
def generate_report(data: list[dict], report_format: str) -> dict:
    """Generate report in specified format."""
    logger = get_run_logger()

    total = sum(item["value"] for item in data)
    average = total / len(data) if data else 0

    report = {
        "format": report_format,
        "generated_at": datetime.now().isoformat(),
        "total_records": len(data),
        "sum": total,
        "average": round(average, 2),
        "records": data if report_format == "detailed" else []
    }

    logger.info(f"Generated {report_format} report with {len(data)} records")
    return report


@flow(name="Parameterized ETL Flow", log_prints=True)
def etl_flow(
    source: str = "api",
    limit: int = 10,
    operation: Literal["uppercase", "lowercase", "capitalize"] = "uppercase",
    min_value: int = 0,
    report_format: Literal["summary", "detailed"] = "summary"
) -> dict:
    """
    ETL flow that accepts multiple parameters for customization.

    Args:
        source: Data source name (e.g., "api", "database", "file")
        limit: Maximum number of records to fetch (default: 10)
        operation: Transformation operation to apply (default: "uppercase")
        min_value: Minimum value filter (default: 0)
        report_format: Report format - "summary" or "detailed" (default: "summary")

    Returns:
        dict: Generated report with results
    """
    logger = get_run_logger()

    logger.info("🚀 Starting Parameterized ETL Flow")
    logger.info(f"Parameters: source={source}, limit={limit}, operation={operation}, "
                f"min_value={min_value}, report_format={report_format}")

    # Extract
    data = fetch_data(source, limit)

    # Transform
    transformed = transform_data(data, operation)

    # Filter
    filtered = filter_data(transformed, min_value)

    # Load / Report
    report = generate_report(filtered, report_format)

    logger.info(f"✅ ETL Flow completed: {report['total_records']} records processed")

    return report


if __name__ == "__main__":
    print("=" * 60)
    print("Parameterized Deployment Example")
    print("=" * 60)
    print()
    print("This flow accepts the following parameters:")
    print()
    print("  source: str = 'api'")
    print("    - Data source name (e.g., 'api', 'database', 'file')")
    print()
    print("  limit: int = 10")
    print("    - Maximum number of records to fetch")
    print()
    print("  operation: 'uppercase' | 'lowercase' | 'capitalize' = 'uppercase'")
    print("    - Transformation operation to apply")
    print()
    print("  min_value: int = 0")
    print("    - Minimum value filter")
    print()
    print("  report_format: 'summary' | 'detailed' = 'summary'")
    print("    - Report format")
    print()
    print("How to trigger with parameters:")
    print()
    print("1. Via UI:")
    print("   - Open: http://localhost:4200")
    print("   - Go to: Deployments → parameterized-etl")
    print("   - Click: 'Run' → 'Custom'")
    print("   - Enter parameters in JSON format:")
    print('     {"source": "database", "limit": 20, "operation": "lowercase"}')
    print()
    print("2. Via API:")
    print("   - See: 04_trigger_via_api.py")
    print()
    print("This script will block. Press Ctrl+C to stop serving.")
    print("=" * 60)
    print()

    # Deploy the flow
    etl_flow.serve(
        name="parameterized-etl",
        tags=["parameterized", "etl", "example"],
        description="ETL flow demonstrating parameter handling"
    )
