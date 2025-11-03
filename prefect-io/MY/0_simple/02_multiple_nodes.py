"""
Example 2: Multiple Nodes Workflow

Demonstrates a workflow with multiple tasks that pass data between each other.
"""

from prefect import flow, task, get_run_logger


@task
def extract_data(source: str) -> dict:
    """Simulates data extraction from a source."""
    logger = get_run_logger()
    logger.info(f"Extracting data from {source}")

    # Simulate data extraction
    data = {
        "source": source,
        "records": [1, 2, 3, 4, 5],
        "count": 5
    }
    return data


@task
def transform_data(raw_data: dict) -> dict:
    """Transforms the extracted data."""
    logger = get_run_logger()
    logger.info(f"Transforming {raw_data['count']} records")

    # Simulate data transformation
    transformed = {
        "source": raw_data["source"],
        "records": [r * 2 for r in raw_data["records"]],
        "sum": sum(raw_data["records"])
    }
    return transformed


@task
def load_data(data: dict, destination: str) -> str:
    """Simulates loading data to a destination."""
    logger = get_run_logger()
    logger.info(f"Loading data to {destination}")
    logger.info(f"Data summary: {data}")

    return f"Successfully loaded {len(data['records'])} records to {destination}"


@flow(name="Multiple Nodes Workflow", log_prints=True)
def multiple_nodes_flow(source: str = "database", destination: str = "warehouse"):
    """A flow demonstrating multiple tasks in sequence (ETL pattern)."""
    logger = get_run_logger()
    logger.info(f"Starting ETL workflow: {source} -> {destination}")

    # Extract
    raw_data = extract_data(source)

    # Transform
    transformed_data = transform_data(raw_data)

    # Load
    result = load_data(transformed_data, destination)

    print(f"Pipeline completed: {result}")
    return result


if __name__ == "__main__":
    # Run the ETL workflow
    multiple_nodes_flow()

    # Run with custom parameters
    multiple_nodes_flow(source="API", destination="data_lake")
