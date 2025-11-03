"""
Example: Child Workflow (Nested Flows)

Demonstrates how flows can call other flows, creating parent-child relationships.
This enables workflow composition and reusability.
"""

from prefect import flow, task, get_run_logger


# ========== Child Flow 1: Data Validation ==========

@task
def validate_records(records: list[dict]) -> dict:
    """Validates individual records."""
    logger = get_run_logger()
    logger.info(f"Validating {len(records)} records")

    valid_records = [r for r in records if r.get("value", 0) > 0]
    invalid_count = len(records) - len(valid_records)

    return {
        "valid_records": valid_records,
        "valid_count": len(valid_records),
        "invalid_count": invalid_count
    }


@flow(name="Validation Flow")
def validation_flow(records: list[dict]) -> dict:
    """Child flow that validates data."""
    logger = get_run_logger()
    logger.info("Starting validation flow")

    validation_result = validate_records(records)

    logger.info(
        f"Validation complete: {validation_result['valid_count']} valid, "
        f"{validation_result['invalid_count']} invalid"
    )

    return validation_result


# ========== Child Flow 2: Data Processing ==========

@task
def calculate_statistics(records: list[dict]) -> dict:
    """Calculates statistics on the records."""
    logger = get_run_logger()

    if not records:
        return {"count": 0, "sum": 0, "average": 0, "max": 0, "min": 0}

    values = [r["value"] for r in records]

    stats = {
        "count": len(values),
        "sum": sum(values),
        "average": sum(values) / len(values),
        "max": max(values),
        "min": min(values)
    }

    logger.info(f"Statistics calculated: {stats}")
    return stats


@flow(name="Processing Flow")
def processing_flow(records: list[dict]) -> dict:
    """Child flow that processes data."""
    logger = get_run_logger()
    logger.info(f"Starting processing flow with {len(records)} records")

    stats = calculate_statistics(records)

    return {
        "records_processed": len(records),
        "statistics": stats
    }


# ========== Child Flow 3: Data Storage ==========

@task
def save_to_database(data: dict, table_name: str) -> str:
    """Simulates saving data to a database."""
    logger = get_run_logger()
    logger.info(f"Saving data to table: {table_name}")

    # Simulate database operation
    record_count = data.get("records_processed", 0)

    return f"Successfully saved {record_count} records to {table_name}"


@flow(name="Storage Flow")
def storage_flow(data: dict, destination: str = "processed_data") -> dict:
    """Child flow that handles data storage."""
    logger = get_run_logger()
    logger.info("Starting storage flow")

    result = save_to_database(data, destination)

    return {
        "destination": destination,
        "message": result,
        "status": "success"
    }


# ========== Parent Flow ==========

@flow(name="Parent Orchestration Flow", log_prints=True)
def parent_flow(raw_records: list[dict] = None):
    """
    Parent flow that orchestrates multiple child flows.

    This demonstrates how flows can be composed together, with the parent
    flow managing the overall workflow and delegating specific tasks to
    child flows.
    """
    logger = get_run_logger()

    # Default sample data if none provided
    if raw_records is None:
        raw_records = [
            {"id": 1, "value": 100},
            {"id": 2, "value": -50},  # Invalid: negative value
            {"id": 3, "value": 200},
            {"id": 4, "value": 0},    # Invalid: zero value
            {"id": 5, "value": 150},
            {"id": 6, "value": 300},
        ]

    logger.info(f"Parent flow started with {len(raw_records)} raw records")
    print(f"\n{'='*60}")
    print(f"PARENT FLOW: Processing {len(raw_records)} records")
    print(f"{'='*60}\n")

    # Step 1: Call validation child flow
    print("Step 1: Validating records...")
    validation_result = validation_flow(raw_records)
    print(f"✓ Validation complete: {validation_result['valid_count']} valid records\n")

    # Step 2: Call processing child flow with validated records
    print("Step 2: Processing valid records...")
    processing_result = processing_flow(validation_result["valid_records"])
    print(f"✓ Processing complete: {processing_result['statistics']}\n")

    # Step 3: Call storage child flow
    print("Step 3: Storing processed data...")
    storage_result = storage_flow(processing_result, destination="analytics_db")
    print(f"✓ Storage complete: {storage_result['message']}\n")

    # Aggregate final results
    final_result = {
        "total_input_records": len(raw_records),
        "valid_records": validation_result["valid_count"],
        "invalid_records": validation_result["invalid_count"],
        "statistics": processing_result["statistics"],
        "storage": storage_result,
        "status": "completed"
    }

    print(f"{'='*60}")
    print(f"PARENT FLOW: Pipeline completed successfully!")
    print(f"{'='*60}")
    print(f"Summary: {final_result['total_input_records']} input records -> "
          f"{final_result['valid_records']} processed and stored")

    return final_result


# ========== Advanced Example: Parallel Child Flows ==========

@flow(name="Department Processing")
def process_department(department_name: str, records: list[dict]) -> dict:
    """Child flow that processes a single department's data."""
    logger = get_run_logger()
    logger.info(f"Processing department: {department_name}")

    # Validate
    validation = validation_flow(records)

    # Process
    processing = processing_flow(validation["valid_records"])

    return {
        "department": department_name,
        "validation": validation,
        "processing": processing
    }


@flow(name="Multi-Department Parent Flow", log_prints=True)
def multi_department_parent_flow():
    """
    Parent flow that processes multiple departments in parallel.

    Demonstrates running multiple child flows concurrently using map.
    """
    logger = get_run_logger()

    # Sample data for multiple departments
    departments = {
        "Sales": [
            {"id": 1, "value": 1000},
            {"id": 2, "value": 1500},
            {"id": 3, "value": -100},
        ],
        "Engineering": [
            {"id": 1, "value": 2000},
            {"id": 2, "value": 2500},
        ],
        "Marketing": [
            {"id": 1, "value": 800},
            {"id": 2, "value": 0},
            {"id": 3, "value": 1200},
        ]
    }

    print(f"\n{'='*60}")
    print(f"MULTI-DEPARTMENT FLOW: Processing {len(departments)} departments")
    print(f"{'='*60}\n")

    results = []

    # Process each department (child flows)
    for dept_name, records in departments.items():
        print(f"Processing {dept_name} department...")
        result = process_department(dept_name, records)
        results.append(result)
        print(f"✓ {dept_name} complete: "
              f"{result['processing']['records_processed']} records processed\n")

    # Aggregate results
    total_records = sum(r["processing"]["records_processed"] for r in results)

    print(f"{'='*60}")
    print(f"MULTI-DEPARTMENT FLOW: All departments processed!")
    print(f"{'='*60}")
    print(f"Total records processed across all departments: {total_records}")

    return {
        "departments_processed": len(departments),
        "department_results": results,
        "total_records": total_records
    }


if __name__ == "__main__":
    # Example 1: Basic parent-child workflow
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Parent-Child Workflow")
    print("="*70)
    parent_flow()

    # Example 2: Custom data
    print("\n\n" + "="*70)
    print("EXAMPLE 2: Parent-Child with Custom Data")
    print("="*70)
    custom_data = [
        {"id": 1, "value": 50},
        {"id": 2, "value": 75},
        {"id": 3, "value": 100},
    ]
    parent_flow(custom_data)

    # Example 3: Multiple parallel child flows
    print("\n\n" + "="*70)
    print("EXAMPLE 3: Multiple Child Flows (Multi-Department)")
    print("="*70)
    multi_department_parent_flow()
