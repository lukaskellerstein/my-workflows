"""
Example 4: Data-Driven Pipeline Construction

Demonstrates the most advanced dynamic workflow pattern: constructing the entire
workflow structure based on runtime data and metadata.

Key Concepts:
- Building workflow DAGs from data/configuration
- Runtime dependency resolution
- Dynamic task graph construction
- Schema-driven pipelines
- Metadata-driven workflow generation
- Adaptive pipeline structures
"""

from prefect import flow, task, get_run_logger
from typing import List, Dict, Any, Optional
import time
from dataclasses import dataclass


# ========== Schema-Driven Pipeline ==========

@dataclass
class SchemaField:
    """Represents a field in a data schema."""
    name: str
    type: str
    transformations: List[str]
    validations: List[str]


@task
def validate_field(field_name: str, validation_type: str, value: Any) -> bool:
    """Validates a field based on validation type."""
    logger = get_run_logger()
    logger.info(f"Validating {field_name} with {validation_type}")
    time.sleep(0.05)

    # Simulate different validation types
    validations = {
        "not_null": value is not None,
        "positive": isinstance(value, (int, float)) and value > 0,
        "string_length": isinstance(value, str) and len(value) > 0,
        "email_format": isinstance(value, str) and "@" in value,
        "range_0_100": isinstance(value, (int, float)) and 0 <= value <= 100
    }

    return validations.get(validation_type, True)


@task
def transform_field(field_name: str, transformation_type: str, value: Any) -> Any:
    """Transforms a field based on transformation type."""
    logger = get_run_logger()
    logger.info(f"Transforming {field_name} with {transformation_type}")
    time.sleep(0.05)

    # Simulate different transformation types
    transformations = {
        "uppercase": value.upper() if isinstance(value, str) else value,
        "lowercase": value.lower() if isinstance(value, str) else value,
        "trim": value.strip() if isinstance(value, str) else value,
        "double": value * 2 if isinstance(value, (int, float)) else value,
        "round": round(value) if isinstance(value, float) else value,
        "anonymize": "***" if value else value
    }

    return transformations.get(transformation_type, value)


@flow(name="Schema-Driven Pipeline", log_prints=True)
def schema_driven_pipeline_flow(schema: List[Dict[str, Any]], data: Dict[str, Any]):
    """
    Constructs a processing pipeline based on schema definition.

    The pipeline structure is entirely driven by the schema - different schemas
    create different workflows.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("SCHEMA-DRIVEN PIPELINE")
    print(f"{'='*70}\n")

    print(f"Schema has {len(schema)} fields")
    print(f"Input data: {data}\n")

    processed_data = {}

    # Dynamically construct pipeline based on schema
    for field_def in schema:
        field_name = field_def["name"]
        field_type = field_def["type"]
        validations = field_def.get("validations", [])
        transformations = field_def.get("transformations", [])

        print(f"\nProcessing field: {field_name} ({field_type})")

        # Get value from input data
        value = data.get(field_name)

        # Dynamically apply validations (number determined by schema)
        if validations:
            print(f"  Validations: {', '.join(validations)}")
            validation_results = []

            for validation in validations:
                is_valid = validate_field(field_name, validation, value)
                validation_results.append(is_valid)

            if not all(validation_results):
                print(f"  ✗ Validation failed")
                continue
            else:
                print(f"  ✓ All validations passed")

        # Dynamically apply transformations (number determined by schema)
        if transformations:
            print(f"  Transformations: {', '.join(transformations)}")
            transformed_value = value

            for transformation in transformations:
                transformed_value = transform_field(field_name, transformation, transformed_value)

            processed_data[field_name] = transformed_value
            print(f"  ✓ Transformed: {value} → {transformed_value}")
        else:
            processed_data[field_name] = value

    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Original: {data}")
    print(f"Processed: {processed_data}")
    print(f"{'='*70}")

    return processed_data


# ========== DAG Construction from Configuration ==========

@task
def read_source(source_id: str) -> Dict[str, Any]:
    """Reads data from a source."""
    logger = get_run_logger()
    logger.info(f"Reading from source: {source_id}")
    time.sleep(0.15)

    return {
        "source_id": source_id,
        "data": list(range(1, 6)),
        "metadata": {"timestamp": "2024-01-01"}
    }


@task
def apply_transformation(data: Dict[str, Any], transformation_id: str) -> Dict[str, Any]:
    """Applies a transformation to data."""
    logger = get_run_logger()
    logger.info(f"Applying transformation: {transformation_id}")
    time.sleep(0.1)

    return {
        **data,
        "transformations_applied": data.get("transformations_applied", []) + [transformation_id]
    }


@task
def join_datasets(datasets: List[Dict[str, Any]], join_type: str) -> Dict[str, Any]:
    """Joins multiple datasets."""
    logger = get_run_logger()
    logger.info(f"Joining {len(datasets)} datasets with {join_type}")
    time.sleep(0.15)

    return {
        "joined": True,
        "join_type": join_type,
        "source_count": len(datasets),
        "sources": [d.get("source_id") for d in datasets]
    }


@task
def write_destination(data: Dict[str, Any], destination_id: str) -> Dict[str, Any]:
    """Writes data to a destination."""
    logger = get_run_logger()
    logger.info(f"Writing to destination: {destination_id}")
    time.sleep(0.1)

    return {
        **data,
        "destination_id": destination_id,
        "status": "written"
    }


@flow(name="DAG from Configuration", log_prints=True)
def dag_from_config_flow(pipeline_config: Dict[str, Any]):
    """
    Constructs a complete DAG from configuration.

    The workflow structure, including dependencies, is defined in the config.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DAG CONSTRUCTION FROM CONFIGURATION")
    print(f"{'='*70}\n")

    # Parse configuration
    sources = pipeline_config.get("sources", [])
    transformations = pipeline_config.get("transformations", {})  # source_id -> [transform_ids]
    joins = pipeline_config.get("joins", [])
    destinations = pipeline_config.get("destinations", [])

    print(f"Configuration:")
    print(f"  Sources: {len(sources)}")
    print(f"  Transformations: {sum(len(t) for t in transformations.values())} total")
    print(f"  Joins: {len(joins)}")
    print(f"  Destinations: {len(destinations)}\n")

    # Step 1: Read from all sources
    print("Phase 1: Reading from sources...")
    source_data = {}
    for source_id in sources:
        print(f"  → Reading {source_id}")
        data = read_source(source_id)
        source_data[source_id] = data

    print(f"✓ Read from {len(sources)} sources\n")

    # Step 2: Apply transformations (dynamically based on config)
    print("Phase 2: Applying transformations...")
    transformed_data = {}

    for source_id, data in source_data.items():
        # Get transformations for this source from config
        source_transforms = transformations.get(source_id, [])

        if source_transforms:
            print(f"  {source_id}: {len(source_transforms)} transformations")
            current_data = data

            # Chain transformations dynamically
            for transform_id in source_transforms:
                current_data = apply_transformation(current_data, transform_id)

            transformed_data[source_id] = current_data
        else:
            print(f"  {source_id}: no transformations")
            transformed_data[source_id] = data

    print(f"✓ Applied transformations\n")

    # Step 3: Perform joins (if configured)
    print("Phase 3: Joining datasets...")
    joined_datasets = []

    for join_config in joins:
        join_sources = join_config.get("sources", [])
        join_type = join_config.get("type", "inner")

        print(f"  → Joining {join_sources} ({join_type})")

        # Get the datasets to join
        datasets_to_join = [
            transformed_data[source_id]
            for source_id in join_sources
            if source_id in transformed_data
        ]

        if datasets_to_join:
            joined = join_datasets(datasets_to_join, join_type)
            joined_datasets.append(joined)

    print(f"✓ Created {len(joined_datasets)} joined datasets\n")

    # Step 4: Write to destinations
    print("Phase 4: Writing to destinations...")
    results = []

    # Write both transformed and joined data
    all_outputs = list(transformed_data.values()) + joined_datasets

    for dest_id in destinations:
        for data in all_outputs:
            print(f"  → Writing to {dest_id}")
            result = write_destination(data, dest_id)
            results.append(result)

    print(f"✓ Written to {len(destinations)} destinations\n")

    print(f"{'='*70}")
    print("PIPELINE EXECUTION COMPLETE")
    print(f"{'='*70}")

    return results


# ========== Dependency-Driven Pipeline ==========

@dataclass
class PipelineStep:
    """Represents a step in a pipeline with dependencies."""
    id: str
    action: str
    params: Dict[str, Any]
    depends_on: List[str]


@task
def execute_step(step_id: str, action: str, params: Dict[str, Any], inputs: List[Any]) -> Dict[str, Any]:
    """Executes a pipeline step."""
    logger = get_run_logger()
    logger.info(f"Executing step {step_id}: {action}")
    time.sleep(0.1)

    return {
        "step_id": step_id,
        "action": action,
        "params": params,
        "input_count": len(inputs),
        "completed": True
    }


@flow(name="Dependency-Driven Pipeline", log_prints=True)
def dependency_driven_pipeline_flow(steps: List[Dict[str, Any]]):
    """
    Constructs a pipeline with explicit dependency resolution.

    Steps are executed in dependency order, determined at runtime.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("DEPENDENCY-DRIVEN PIPELINE")
    print(f"{'='*70}\n")

    print(f"Pipeline has {len(steps)} steps\n")

    # Build dependency graph
    step_results = {}
    completed_steps = set()

    def can_execute(step: Dict[str, Any]) -> bool:
        """Check if all dependencies are satisfied."""
        dependencies = step.get("depends_on", [])
        return all(dep in completed_steps for dep in dependencies)

    def get_inputs(step: Dict[str, Any]) -> List[Any]:
        """Get inputs from dependent steps."""
        dependencies = step.get("depends_on", [])
        return [step_results[dep] for dep in dependencies if dep in step_results]

    # Execute steps in dependency order
    remaining_steps = list(steps)
    iteration = 0
    max_iterations = len(steps) * 2  # Prevent infinite loops

    while remaining_steps and iteration < max_iterations:
        iteration += 1
        executed_this_round = []

        print(f"\nIteration {iteration}:")

        for step in remaining_steps:
            step_id = step["id"]

            if can_execute(step):
                # Get inputs from dependencies
                inputs = get_inputs(step)

                print(f"  → Executing {step_id} (depends on: {step.get('depends_on', [])})")

                # Execute the step
                result = execute_step(
                    step_id,
                    step.get("action", "unknown"),
                    step.get("params", {}),
                    inputs
                )

                step_results[step_id] = result
                completed_steps.add(step_id)
                executed_this_round.append(step)

        # Remove executed steps
        for step in executed_this_round:
            remaining_steps.remove(step)

        if not executed_this_round and remaining_steps:
            print(f"\n  ✗ Circular dependency detected!")
            print(f"  Remaining steps: {[s['id'] for s in remaining_steps]}")
            break

    print(f"\n{'='*70}")
    print("EXECUTION SUMMARY")
    print(f"{'='*70}")
    print(f"Steps executed: {len(completed_steps)}/{len(steps)}")
    print(f"Execution order: {' → '.join(completed_steps)}")
    print(f"{'='*70}")

    return list(step_results.values())


# ========== Adaptive Pipeline Based on Runtime Metrics ==========

@task
def process_batch_adaptive(batch: List[int], strategy: str) -> Dict[str, Any]:
    """Processes a batch using specified strategy."""
    logger = get_run_logger()
    logger.info(f"Processing batch with {strategy} strategy")
    time.sleep(0.1)

    return {
        "strategy": strategy,
        "count": len(batch),
        "sum": sum(batch),
        "processing_time": 0.1
    }


@task
def analyze_performance(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyzes performance metrics."""
    logger = get_run_logger()
    logger.info("Analyzing performance metrics")
    time.sleep(0.05)

    total_time = sum(r["processing_time"] for r in results)
    total_items = sum(r["count"] for r in results)

    return {
        "total_batches": len(results),
        "total_items": total_items,
        "total_time": total_time,
        "throughput": total_items / total_time if total_time > 0 else 0
    }


@flow(name="Adaptive Pipeline", log_prints=True)
def adaptive_pipeline_flow(batches: List[List[int]]):
    """
    Demonstrates an adaptive pipeline that changes its strategy based on runtime metrics.

    The processing strategy adapts based on performance measurements.
    """
    logger = get_run_logger()
    print(f"\n{'='*70}")
    print("ADAPTIVE PIPELINE")
    print(f"{'='*70}\n")

    print(f"Processing {len(batches)} batches with adaptive strategy\n")

    all_results = []
    current_strategy = "standard"

    for i, batch in enumerate(batches, 1):
        print(f"\nBatch {i}/{len(batches)} (size: {len(batch)})")
        print(f"  Current strategy: {current_strategy}")

        # Process with current strategy
        result = process_batch_adaptive(batch, current_strategy)
        all_results.append(result)

        # Every 2 batches, analyze performance and adapt
        if i % 2 == 0 and i < len(batches):
            print(f"\n  → Analyzing performance...")
            metrics = analyze_performance(all_results)

            # Adapt strategy based on metrics
            throughput = metrics["throughput"]
            print(f"    Throughput: {throughput:.2f} items/sec")

            if throughput < 50:
                new_strategy = "optimized"
                print(f"    → Switching to OPTIMIZED strategy")
            elif throughput > 100:
                new_strategy = "fast"
                print(f"    → Switching to FAST strategy")
            else:
                new_strategy = "standard"
                print(f"    → Keeping STANDARD strategy")

            current_strategy = new_strategy

    print(f"\n{'='*70}")
    print("ADAPTIVE PIPELINE COMPLETE")
    print(f"{'='*70}")

    final_metrics = analyze_performance(all_results)
    print(f"Total batches: {final_metrics['total_batches']}")
    print(f"Total items: {final_metrics['total_items']}")
    print(f"Average throughput: {final_metrics['throughput']:.2f} items/sec")

    strategies_used = {}
    for r in all_results:
        s = r["strategy"]
        strategies_used[s] = strategies_used.get(s, 0) + 1

    print(f"\nStrategies used:")
    for strategy, count in strategies_used.items():
        print(f"  {strategy}: {count} batches")

    print(f"{'='*70}")

    return all_results


# ========== Comprehensive Demo ==========

@flow(name="Data-Driven Pipelines Demo", log_prints=True)
def comprehensive_demo():
    """Runs all data-driven pipeline examples."""
    print("="*70)
    print("COMPREHENSIVE DATA-DRIVEN PIPELINES DEMONSTRATION")
    print("="*70)

    # Example 1: Schema-driven pipeline
    print("\n\nEXAMPLE 1: Schema-Driven Pipeline")
    print("="*70)

    schema = [
        {
            "name": "username",
            "type": "string",
            "validations": ["not_null", "string_length"],
            "transformations": ["trim", "lowercase"]
        },
        {
            "name": "email",
            "type": "string",
            "validations": ["not_null", "email_format"],
            "transformations": ["trim", "lowercase"]
        },
        {
            "name": "age",
            "type": "integer",
            "validations": ["not_null", "positive", "range_0_100"],
            "transformations": []
        },
        {
            "name": "score",
            "type": "float",
            "validations": ["not_null"],
            "transformations": ["double", "round"]
        }
    ]

    data = {
        "username": "  JohnDoe  ",
        "email": "  JOHN@EXAMPLE.COM  ",
        "age": 30,
        "score": 85.7
    }

    schema_driven_pipeline_flow(schema, data)

    # Example 2: DAG from configuration
    print("\n\nEXAMPLE 2: DAG Construction from Configuration")
    print("="*70)

    pipeline_config = {
        "sources": ["source_a", "source_b", "source_c"],
        "transformations": {
            "source_a": ["transform_1", "transform_2"],
            "source_b": ["transform_3"],
            "source_c": []
        },
        "joins": [
            {"sources": ["source_a", "source_b"], "type": "inner"}
        ],
        "destinations": ["warehouse", "analytics_db"]
    }

    dag_from_config_flow(pipeline_config)

    # Example 3: Dependency-driven pipeline
    print("\n\nEXAMPLE 3: Dependency-Driven Pipeline")
    print("="*70)

    steps = [
        {"id": "step_1", "action": "extract", "params": {}, "depends_on": []},
        {"id": "step_2", "action": "extract", "params": {}, "depends_on": []},
        {"id": "step_3", "action": "transform", "params": {}, "depends_on": ["step_1"]},
        {"id": "step_4", "action": "transform", "params": {}, "depends_on": ["step_2"]},
        {"id": "step_5", "action": "join", "params": {}, "depends_on": ["step_3", "step_4"]},
        {"id": "step_6", "action": "load", "params": {}, "depends_on": ["step_5"]},
    ]

    dependency_driven_pipeline_flow(steps)

    # Example 4: Adaptive pipeline
    print("\n\nEXAMPLE 4: Adaptive Pipeline")
    print("="*70)

    batches = [
        list(range(1, 21)),   # 20 items
        list(range(1, 31)),   # 30 items
        list(range(1, 26)),   # 25 items
        list(range(1, 41)),   # 40 items
        list(range(1, 16)),   # 15 items
    ]

    adaptive_pipeline_flow(batches)

    print("\n" + "="*70)
    print("All data-driven pipeline examples completed")
    print("="*70)


if __name__ == "__main__":
    comprehensive_demo()
