"""
Example 1: Dynamic Task Mapping

Demonstrates how to dynamically map tasks based on runtime data.
The number of parallel tasks is determined by the data itself, not hardcoded.

Key Concepts:
- Using .map() with runtime-determined data
- Dynamic parallelism based on input
- Nested mapping (map of maps)
- Dynamic unmapping/flattening
"""

from prefect import flow, task, get_run_logger
from typing import List, Dict, Any
import time


# ========== Basic Dynamic Mapping ==========

@task
def analyze_file(file_path: str) -> Dict[str, Any]:
    """Analyzes a file and returns metadata."""
    logger = get_run_logger()
    logger.info(f"Analyzing file: {file_path}")
    time.sleep(0.2)

    # Simulate file analysis
    return {
        "file": file_path,
        "size": len(file_path) * 100,
        "type": file_path.split(".")[-1] if "." in file_path else "unknown",
        "lines": len(file_path) * 10
    }


@task
def process_by_type(file_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Processes file based on its type."""
    logger = get_run_logger()
    file_type = file_metadata["type"]
    logger.info(f"Processing {file_metadata['file']} as {file_type}")
    time.sleep(0.1)

    processing_map = {
        "txt": "text_processor",
        "csv": "data_processor",
        "json": "json_parser",
        "unknown": "default_handler"
    }

    processor = processing_map.get(file_type, "default_handler")

    return {
        **file_metadata,
        "processor_used": processor,
        "processed": True
    }


@flow(name="Dynamic File Processing", log_prints=True)
def dynamic_file_processing_flow(directory_pattern: str = "*.txt"):
    """
    Dynamically processes files discovered at runtime.

    The workflow structure adapts to the number of files found.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DYNAMIC FILE PROCESSING")
    print(f"{'='*70}\n")

    # Simulate discovering files at runtime
    # In real scenario, this could be os.listdir() or API call
    discovered_files = [
        "data/file1.txt",
        "data/file2.csv",
        "data/file3.json",
        "data/file4.txt",
        "data/file5.csv",
        "data/report.txt",
        "data/metrics.json",
        "data/unknown_file"
    ]

    print(f"Discovered {len(discovered_files)} files matching '{directory_pattern}'")
    print(f"Files: {', '.join(discovered_files)}\n")

    # Dynamic mapping - number of tasks created at runtime
    print("Step 1: Analyzing files in parallel (dynamic mapping)...")
    analyzed_files = analyze_file.map(discovered_files)
    print(f"✓ Created {len(discovered_files)} analysis tasks dynamically\n")

    # Process each file based on its type (determined at runtime)
    print("Step 2: Processing files by type (dynamic)...")
    processed_files = process_by_type.map(analyzed_files)
    print(f"✓ Processed {len(discovered_files)} files\n")

    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    for result in processed_files:
        print(f"  {result['file']}: {result['type']} -> {result['processor_used']}")
    print(f"{'='*70}")

    return processed_files


# ========== Nested Dynamic Mapping ==========

@task
def fetch_api_endpoints(service: str) -> List[str]:
    """Discovers API endpoints for a service at runtime."""
    logger = get_run_logger()
    logger.info(f"Discovering endpoints for {service}")
    time.sleep(0.1)

    # Simulate API discovery - different services have different endpoints
    endpoints_map = {
        "users": ["/users", "/users/profile", "/users/settings"],
        "orders": ["/orders", "/orders/history"],
        "products": ["/products", "/products/categories", "/products/search", "/products/reviews"]
    }

    return endpoints_map.get(service, [])


@task
def call_endpoint(service: str, endpoint: str) -> Dict[str, Any]:
    """Calls an API endpoint."""
    logger = get_run_logger()
    logger.info(f"Calling {service}{endpoint}")
    time.sleep(0.15)

    return {
        "service": service,
        "endpoint": endpoint,
        "status": 200,
        "response_time": 0.15,
        "data_size": len(endpoint) * 50
    }


@task
def aggregate_service_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregates results for a service."""
    if not results:
        return {"service": "unknown", "total_calls": 0}

    logger = get_run_logger()
    service = results[0]["service"]
    logger.info(f"Aggregating {len(results)} results for {service}")

    return {
        "service": service,
        "total_calls": len(results),
        "total_response_time": sum(r["response_time"] for r in results),
        "avg_response_time": sum(r["response_time"] for r in results) / len(results),
        "total_data": sum(r["data_size"] for r in results)
    }


@flow(name="Nested Dynamic Mapping", log_prints=True)
def nested_dynamic_mapping_flow(services: List[str] = None):
    """
    Demonstrates nested dynamic mapping where the structure is unknown until runtime.

    Each service has a different number of endpoints discovered at runtime,
    and we dynamically map over all of them.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("NESTED DYNAMIC MAPPING")
    print(f"{'='*70}\n")

    if services is None:
        services = ["users", "orders", "products"]

    print(f"Processing {len(services)} services\n")

    all_results = []

    for service in services:
        print(f"Service: {service}")

        # Step 1: Discover endpoints dynamically
        endpoints = fetch_api_endpoints(service)
        print(f"  Discovered {len(endpoints)} endpoints: {endpoints}")

        # Step 2: Dynamically map over discovered endpoints
        # Number of tasks created depends on runtime discovery
        if endpoints:
            service_results = call_endpoint.map(
                [service] * len(endpoints),
                endpoints
            )
            print(f"  Created {len(endpoints)} parallel API call tasks\n")

            all_results.append({
                "service": service,
                "results": service_results
            })
        else:
            print(f"  No endpoints found\n")

    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")

    for service_data in all_results:
        service = service_data["service"]
        results = service_data["results"]
        print(f"\n{service.upper()}:")
        for result in results:
            print(f"  {result['endpoint']}: {result['status']} ({result['response_time']}s)")

    print(f"{'='*70}")

    return all_results


# ========== Dynamic Unmapping/Flattening ==========

@task
def extract_records(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts variable number of records from a source."""
    logger = get_run_logger()
    source_id = source["id"]
    record_count = source["record_count"]
    logger.info(f"Extracting {record_count} records from source {source_id}")
    time.sleep(0.1)

    # Each source returns different number of records
    return [
        {"source_id": source_id, "record_id": i, "value": i * 10}
        for i in range(1, record_count + 1)
    ]


@task
def validate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validates a single record."""
    logger = get_run_logger()
    logger.info(f"Validating record {record['record_id']} from source {record['source_id']}")
    time.sleep(0.05)

    return {
        **record,
        "validated": True,
        "validation_time": 0.05
    }


@flow(name="Dynamic Unmapping", log_prints=True)
def dynamic_unmapping_flow():
    """
    Demonstrates dynamic unmapping where tasks produce variable numbers of outputs.

    Each source produces a different number of records, and we need to
    process all records individually.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DYNAMIC UNMAPPING (FLATTENING)")
    print(f"{'='*70}\n")

    # Each source has different number of records
    sources = [
        {"id": 1, "record_count": 3},
        {"id": 2, "record_count": 5},
        {"id": 3, "record_count": 2},
        {"id": 4, "record_count": 4}
    ]

    print(f"Processing {len(sources)} sources with variable record counts\n")

    # Step 1: Extract records from each source (produces lists)
    print("Step 1: Extracting records from sources...")
    extracted_records_per_source = extract_records.map(sources)
    print(f"✓ Extracted records from {len(sources)} sources\n")

    # Step 2: Flatten/unmap - process all records individually
    print("Step 2: Flattening and validating all records...")
    all_records = []
    for records_list in extracted_records_per_source:
        # Dynamically map over each record in the list
        validated = validate_record.map(records_list)
        all_records.extend(validated)

    print(f"✓ Validated {len(all_records)} total records\n")

    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")

    # Group by source
    by_source = {}
    for record in all_records:
        source_id = record["source_id"]
        if source_id not in by_source:
            by_source[source_id] = []
        by_source[source_id].append(record)

    for source_id, records in sorted(by_source.items()):
        print(f"\nSource {source_id}: {len(records)} records")
        for record in records:
            print(f"  Record {record['record_id']}: value={record['value']}, validated={record['validated']}")

    print(f"\nTotal records processed: {len(all_records)}")
    print(f"{'='*70}")

    return all_records


# ========== Dynamic Batching ==========

@task
def create_dynamic_batches(items: List[Any], batch_size: int = None) -> List[List[Any]]:
    """
    Dynamically creates batches based on runtime data.

    If batch_size is None, determines optimal batch size at runtime.
    """
    logger = get_run_logger()

    # Determine batch size dynamically
    if batch_size is None:
        # Dynamic decision: larger datasets get larger batches
        if len(items) > 100:
            batch_size = 20
        elif len(items) > 50:
            batch_size = 10
        else:
            batch_size = 5

    logger.info(f"Creating batches of size {batch_size} for {len(items)} items")

    batches = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batches.append(batch)

    return batches


@task
def process_dynamic_batch(batch: List[int], batch_id: int) -> Dict[str, Any]:
    """Processes a dynamically created batch."""
    logger = get_run_logger()
    logger.info(f"Processing batch {batch_id} with {len(batch)} items")
    time.sleep(0.1)

    return {
        "batch_id": batch_id,
        "size": len(batch),
        "sum": sum(batch),
        "min": min(batch) if batch else 0,
        "max": max(batch) if batch else 0
    }


@flow(name="Dynamic Batching", log_prints=True)
def dynamic_batching_flow(num_items: int = 75):
    """
    Demonstrates dynamic batching where batch size is determined at runtime.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DYNAMIC BATCHING")
    print(f"{'='*70}\n")

    # Generate data
    items = list(range(1, num_items + 1))
    print(f"Processing {len(items)} items with dynamic batching\n")

    # Create batches dynamically (batch size determined at runtime)
    print("Step 1: Creating batches dynamically...")
    batches = create_dynamic_batches(items)
    print(f"✓ Created {len(batches)} batches (batch size determined at runtime)\n")

    # Process batches in parallel
    print("Step 2: Processing batches in parallel...")
    batch_ids = list(range(len(batches)))
    results = process_dynamic_batch.map(batches, batch_ids)
    print(f"✓ Processed {len(results)} batches\n")

    print(f"{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    for result in results:
        print(f"Batch {result['batch_id']}: {result['size']} items, sum={result['sum']}, range=[{result['min']}-{result['max']}]")
    print(f"{'='*70}")

    return results


# ========== Comprehensive Demo ==========

@flow(name="Dynamic Task Mapping Demo", log_prints=True)
def comprehensive_demo():
    """Runs all dynamic task mapping examples."""
    print("="*70)
    print("COMPREHENSIVE DYNAMIC TASK MAPPING DEMONSTRATION")
    print("="*70)

    # Example 1: Basic dynamic mapping
    print("\n\nEXAMPLE 1: Dynamic File Processing")
    print("="*70)
    dynamic_file_processing_flow()

    # Example 2: Nested dynamic mapping
    print("\n\nEXAMPLE 2: Nested Dynamic Mapping")
    print("="*70)
    nested_dynamic_mapping_flow()

    # Example 3: Dynamic unmapping
    print("\n\nEXAMPLE 3: Dynamic Unmapping/Flattening")
    print("="*70)
    dynamic_unmapping_flow()

    # Example 4: Dynamic batching
    print("\n\nEXAMPLE 4: Dynamic Batching")
    print("="*70)
    dynamic_batching_flow(num_items=75)

    print("\n" + "="*70)
    print("All dynamic task mapping examples completed")
    print("="*70)


if __name__ == "__main__":
    comprehensive_demo()
