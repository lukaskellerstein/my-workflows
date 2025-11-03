"""
ETL Flow for Kubernetes Deployment

This is an example flow that demonstrates deploying to Kubernetes.
Based on the multiple_nodes workflow pattern.
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


@flow(name="k8s-etl-workflow", log_prints=True)
def k8s_etl_flow(source: str = "database", destination: str = "warehouse"):
    """
    ETL workflow deployed to Kubernetes.

    This flow demonstrates:
    - Running in a Kubernetes pod
    - Passing parameters
    - Logging to Prefect server
    """
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
    # This allows local testing before building the Docker image
    k8s_etl_flow()
