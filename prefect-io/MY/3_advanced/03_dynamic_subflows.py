"""
Example 3: Dynamic Subflow Creation

Demonstrates how to create and invoke flows dynamically at runtime.
This is one of the most powerful features for building adaptive workflows.

Key Concepts:
- Creating subflows dynamically based on runtime data
- Calling different flows based on conditions
- Generating workflow definitions at runtime
- Composing complex workflows from reusable flow components
- Runtime flow selection
"""

from prefect import flow, task, get_run_logger
from typing import List, Dict, Any, Callable
import time


# ========== Basic Dynamic Subflow Invocation ==========

@flow(name="ETL - Extract")
def extract_flow(source: str) -> Dict[str, Any]:
    """Extraction flow for a specific source type."""
    logger = get_run_logger()
    logger.info(f"Extracting from {source}")
    time.sleep(0.2)

    return {
        "source": source,
        "records": list(range(1, 11)),
        "metadata": {"extracted_at": "2024-01-01", "count": 10}
    }


@flow(name="ETL - Transform CSV")
def transform_csv_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform flow specific to CSV data."""
    logger = get_run_logger()
    logger.info(f"Transforming CSV data from {data['source']}")
    time.sleep(0.2)

    return {
        **data,
        "transformed": True,
        "format": "csv",
        "transformation_applied": "csv_to_records"
    }


@flow(name="ETL - Transform JSON")
def transform_json_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform flow specific to JSON data."""
    logger = get_run_logger()
    logger.info(f"Transforming JSON data from {data['source']}")
    time.sleep(0.2)

    return {
        **data,
        "transformed": True,
        "format": "json",
        "transformation_applied": "json_normalization"
    }


@flow(name="ETL - Transform XML")
def transform_xml_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform flow specific to XML data."""
    logger = get_run_logger()
    logger.info(f"Transforming XML data from {data['source']}")
    time.sleep(0.2)

    return {
        **data,
        "transformed": True,
        "format": "xml",
        "transformation_applied": "xml_parsing"
    }


@flow(name="ETL - Load")
def load_flow(data: Dict[str, Any], destination: str) -> Dict[str, Any]:
    """Loading flow."""
    logger = get_run_logger()
    logger.info(f"Loading {data.get('format', 'unknown')} data to {destination}")
    time.sleep(0.2)

    return {
        **data,
        "loaded": True,
        "destination": destination,
        "status": "success"
    }


@flow(name="Dynamic ETL Pipeline", log_prints=True)
def dynamic_etl_flow(source: str, source_type: str, destination: str):
    """
    Demonstrates dynamic subflow selection based on data type.

    The transformation flow is selected at runtime based on the source type.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print(f"DYNAMIC ETL PIPELINE")
    print(f"{'='*70}\n")

    print(f"Source: {source} (Type: {source_type})")
    print(f"Destination: {destination}\n")

    # Step 1: Extract (always the same)
    print("Step 1: Extracting data...")
    extracted_data = extract_flow(source)
    print(f"✓ Extracted {extracted_data['metadata']['count']} records\n")

    # Step 2: Transform (dynamically selected based on type)
    print(f"Step 2: Transforming {source_type} data...")

    # Dynamic subflow selection - different flows for different types
    transform_flows = {
        "csv": transform_csv_flow,
        "json": transform_json_flow,
        "xml": transform_xml_flow
    }

    # Select and invoke the appropriate transform flow at runtime
    transform_flow_func = transform_flows.get(source_type)

    if transform_flow_func:
        print(f"  → Selected transform flow: {transform_flow_func.__name__}")
        transformed_data = transform_flow_func(extracted_data)
    else:
        print(f"  → No specific transform flow for {source_type}, using default")
        transformed_data = extracted_data

    print(f"✓ Transformation complete: {transformed_data.get('transformation_applied')}\n")

    # Step 3: Load (always the same)
    print("Step 3: Loading data...")
    final_result = load_flow(transformed_data, destination)
    print(f"✓ Loaded to {destination}\n")

    print(f"{'='*70}")
    print(f"ETL Pipeline Status: {final_result['status']}")
    print(f"{'='*70}")

    return final_result


# ========== Dynamic Subflow Generation ==========

def create_processing_flow(flow_name: str, processing_type: str) -> Callable:
    """
    Factory function that creates flow definitions dynamically at runtime.

    This demonstrates runtime flow generation - the flow itself is created
    based on input parameters.
    """

    @flow(name=flow_name)
    def dynamic_processing_flow(data: Dict[str, Any]) -> Dict[str, Any]:
        """Dynamically generated processing flow."""
        logger = get_run_logger()
        logger.info(f"Running {processing_type} processing in {flow_name}")
        time.sleep(0.2)

        # Different processing logic based on type
        if processing_type == "aggregate":
            result = sum(data.get("values", []))
            operation = "sum"
        elif processing_type == "filter":
            result = [v for v in data.get("values", []) if v > 5]
            operation = "filter > 5"
        elif processing_type == "transform":
            result = [v * 2 for v in data.get("values", [])]
            operation = "multiply by 2"
        else:
            result = data.get("values", [])
            operation = "passthrough"

        return {
            "flow_name": flow_name,
            "processing_type": processing_type,
            "operation": operation,
            "result": result,
            "input_count": len(data.get("values", []))
        }

    return dynamic_processing_flow


@flow(name="Dynamic Flow Generation", log_prints=True)
def dynamic_flow_generation_demo(processing_requests: List[Dict[str, Any]] = None):
    """
    Demonstrates generating and executing flows at runtime.

    Flows are created on-the-fly based on processing requirements.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DYNAMIC FLOW GENERATION")
    print(f"{'='*70}\n")

    if processing_requests is None:
        processing_requests = [
            {"type": "aggregate", "values": [1, 2, 3, 4, 5]},
            {"type": "filter", "values": [3, 6, 2, 8, 1, 9]},
            {"type": "transform", "values": [10, 20, 30]},
        ]

    print(f"Processing {len(processing_requests)} requests with dynamically generated flows\n")

    results = []

    for i, request in enumerate(processing_requests, 1):
        proc_type = request["type"]
        values = request["values"]

        print(f"\nRequest {i}: {proc_type}")
        print(f"  Input: {values}")

        # Dynamically create a flow for this processing type
        flow_name = f"Dynamic {proc_type.title()} Flow #{i}"
        processing_flow = create_processing_flow(flow_name, proc_type)

        print(f"  → Created flow: {flow_name}")

        # Execute the dynamically created flow
        result = processing_flow({"values": values})

        print(f"  → Operation: {result['operation']}")
        print(f"  → Result: {result['result']}")

        results.append(result)

    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")

    for result in results:
        print(f"{result['flow_name']}: {result['operation']}")

    print(f"{'='*70}")

    return results


# ========== Complex Dynamic Subflow Composition ==========

@flow(name="Validation Flow")
def validation_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates data."""
    logger = get_run_logger()
    logger.info("Running validation")
    time.sleep(0.1)

    return {
        **data,
        "validated": True,
        "validation_errors": []
    }


@flow(name="Enrichment Flow")
def enrichment_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Enriches data with additional information."""
    logger = get_run_logger()
    logger.info("Running enrichment")
    time.sleep(0.15)

    return {
        **data,
        "enriched": True,
        "additional_fields": ["field1", "field2"]
    }


@flow(name="Anonymization Flow")
def anonymization_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Anonymizes sensitive data."""
    logger = get_run_logger()
    logger.info("Running anonymization")
    time.sleep(0.1)

    return {
        **data,
        "anonymized": True,
        "pii_removed": True
    }


@flow(name="Aggregation Flow")
def aggregation_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregates data."""
    logger = get_run_logger()
    logger.info("Running aggregation")
    time.sleep(0.1)

    return {
        **data,
        "aggregated": True,
        "summary_created": True
    }


@flow(name="Encryption Flow")
def encryption_flow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypts data."""
    logger = get_run_logger()
    logger.info("Running encryption")
    time.sleep(0.12)

    return {
        **data,
        "encrypted": True,
        "encryption_algorithm": "AES-256"
    }


@flow(name="Dynamic Pipeline Composition", log_prints=True)
def dynamic_pipeline_composition_flow(pipeline_config: Dict[str, Any]):
    """
    Demonstrates composing complex pipelines from reusable flow components.

    The pipeline structure is defined by configuration at runtime.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DYNAMIC PIPELINE COMPOSITION")
    print(f"{'='*70}\n")

    # Available flow components
    available_flows = {
        "validation": validation_flow,
        "enrichment": enrichment_flow,
        "anonymization": anonymization_flow,
        "aggregation": aggregation_flow,
        "encryption": encryption_flow
    }

    # Get pipeline stages from config
    stages = pipeline_config.get("stages", [])
    input_data = pipeline_config.get("data", {})

    print(f"Pipeline configuration: {len(stages)} stages")
    print(f"Stages: {' → '.join(stages)}\n")

    # Start with input data
    current_data = input_data
    stage_results = []

    # Dynamically compose and execute pipeline
    for i, stage_name in enumerate(stages, 1):
        print(f"Stage {i}/{len(stages)}: {stage_name}")

        # Get the flow for this stage
        stage_flow = available_flows.get(stage_name)

        if stage_flow:
            print(f"  → Executing {stage_flow.__name__}")
            # Execute the subflow
            current_data = stage_flow(current_data)
            stage_results.append(stage_name)
            print(f"  ✓ Complete\n")
        else:
            print(f"  ✗ Unknown stage: {stage_name}\n")

    print(f"{'='*70}")
    print("PIPELINE RESULTS")
    print(f"{'='*70}")
    print(f"Stages executed: {' → '.join(stage_results)}")
    print(f"Final data keys: {', '.join(current_data.keys())}")
    print(f"{'='*70}")

    return current_data


# ========== Parallel Subflow Execution ==========

@flow(name="Process Region Flow")
def process_region_flow(region: str, data: List[int]) -> Dict[str, Any]:
    """Processes data for a specific region."""
    logger = get_run_logger()
    logger.info(f"Processing {len(data)} items for region: {region}")
    time.sleep(0.3)

    return {
        "region": region,
        "count": len(data),
        "sum": sum(data),
        "avg": sum(data) / len(data) if data else 0
    }


@flow(name="Parallel Subflows", log_prints=True)
def parallel_subflows_flow(regions_data: Dict[str, List[int]] = None):
    """
    Demonstrates executing multiple subflows in parallel.

    Each region gets its own subflow instance, all running concurrently.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("PARALLEL SUBFLOW EXECUTION")
    print(f"{'='*70}\n")

    if regions_data is None:
        regions_data = {
            "US-WEST": [10, 20, 30, 40],
            "US-EAST": [15, 25, 35],
            "EU": [5, 10, 15, 20, 25],
            "ASIA": [30, 40]
        }

    print(f"Processing {len(regions_data)} regions in parallel\n")

    # Create a subflow for each region
    region_flows = []
    for region, data in regions_data.items():
        print(f"Creating subflow for {region} ({len(data)} items)")
        region_flows.append((region, data))

    print(f"\nExecuting {len(region_flows)} subflows in parallel...\n")

    # Execute all subflows (Prefect will parallelize them)
    results = [
        process_region_flow(region, data)
        for region, data in region_flows
    ]

    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")

    for result in results:
        print(f"{result['region']}: {result['count']} items, avg={result['avg']:.2f}")

    print(f"{'='*70}")

    return results


# ========== Comprehensive Demo ==========

@flow(name="Dynamic Subflows Demo", log_prints=True)
def comprehensive_demo():
    """Runs all dynamic subflow examples."""
    print("="*70)
    print("COMPREHENSIVE DYNAMIC SUBFLOWS DEMONSTRATION")
    print("="*70)

    # Example 1: Dynamic ETL with runtime flow selection
    print("\n\nEXAMPLE 1: Dynamic ETL Pipeline")
    print("="*70)
    dynamic_etl_flow(
        source="s3://bucket/data.csv",
        source_type="csv",
        destination="warehouse.table"
    )

    # Example 2: Dynamic flow generation
    print("\n\nEXAMPLE 2: Dynamic Flow Generation")
    print("="*70)
    dynamic_flow_generation_demo()

    # Example 3: Dynamic pipeline composition
    print("\n\nEXAMPLE 3: Dynamic Pipeline Composition")
    print("="*70)
    pipeline_config = {
        "stages": ["validation", "enrichment", "anonymization", "encryption"],
        "data": {"user_id": 123, "name": "John Doe", "email": "john@example.com"}
    }
    dynamic_pipeline_composition_flow(pipeline_config)

    # Example 4: Parallel subflows
    print("\n\nEXAMPLE 4: Parallel Subflow Execution")
    print("="*70)
    parallel_subflows_flow()

    print("\n" + "="*70)
    print("All dynamic subflow examples completed")
    print("="*70)


if __name__ == "__main__":
    comprehensive_demo()
