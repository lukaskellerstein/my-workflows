"""
Example 1: Basic Flow Visualization

Demonstrates how to visualize Prefect workflows using flow.visualize().

Requirements:
    - graphviz system library: apt-get install graphviz (Linux)
    - graphviz Python package: pip install graphviz
"""

from prefect import flow, task, get_run_logger


# ========== Simple Linear Flow ==========

@task
def extract_data() -> list[int]:
    """Extracts data from source."""
    return [1, 2, 3, 4, 5]


@task
def transform_data(data: list[int]) -> list[int]:
    """Transforms the data."""
    return [x * 2 for x in data]


@task
def load_data(data: list[int]) -> str:
    """Loads data to destination."""
    return f"Loaded {len(data)} items"


@flow(name="Simple Linear Flow")
def simple_linear_flow():
    """
    A simple linear flow: Extract → Transform → Load

    Visualization will show:
        extract_data → transform_data → load_data
    """
    raw_data = extract_data()
    transformed = transform_data(raw_data)
    result = load_data(transformed)
    return result


# ========== Branching Flow ==========

@task
def fetch_data() -> dict:
    """Fetches data."""
    return {"value": 100, "type": "premium"}


@task
def process_premium(data: dict) -> str:
    """Processes premium data."""
    return f"Premium processing: {data['value']}"


@task
def process_standard(data: dict) -> str:
    """Processes standard data."""
    return f"Standard processing: {data['value']}"


@task
def save_result(result: str) -> str:
    """Saves the result."""
    return f"Saved: {result}"


@flow(name="Branching Flow")
def branching_flow():
    """
    A flow with conditional branches.

    Visualization will show branching based on condition:
        fetch_data → [process_premium or process_standard] → save_result
    """
    data = fetch_data()

    if data["type"] == "premium":
        processed = process_premium(data)
    else:
        processed = process_standard(data)

    result = save_result(processed)
    return result


# ========== Parallel Flow ==========

@task
def task_a() -> str:
    """Independent task A."""
    return "Result A"


@task
def task_b() -> str:
    """Independent task B."""
    return "Result B"


@task
def task_c() -> str:
    """Independent task C."""
    return "Result C"


@task
def combine_results(a: str, b: str, c: str) -> str:
    """Combines results from parallel tasks."""
    return f"Combined: {a}, {b}, {c}"


@flow(name="Parallel Flow")
def parallel_flow():
    """
    A flow with parallel task execution.

    Visualization will show:
        ┌─> task_a ─┐
        ├─> task_b ─┤─> combine_results
        └─> task_c ─┘
    """
    # These tasks have no dependencies, so they can run in parallel
    result_a = task_a()
    result_b = task_b()
    result_c = task_c()

    # This task depends on all three
    combined = combine_results(result_a, result_b, result_c)
    return combined


# ========== Multi-Level Flow ==========

@task
def level_1_task() -> str:
    """First level task."""
    return "Level 1"


@task
def level_2_task_a(input_data: str) -> str:
    """Second level task A."""
    return f"{input_data} -> 2A"


@task
def level_2_task_b(input_data: str) -> str:
    """Second level task B."""
    return f"{input_data} -> 2B"


@task
def level_3_task(a: str, b: str) -> str:
    """Third level task."""
    return f"Final: {a} + {b}"


@flow(name="Multi-Level Flow")
def multi_level_flow():
    """
    A flow with multiple dependency levels.

    Visualization will show:
        level_1_task ─┬─> level_2_task_a ─┐
                      └─> level_2_task_b ─┤─> level_3_task
    """
    level_1 = level_1_task()

    level_2a = level_2_task_a(level_1)
    level_2b = level_2_task_b(level_1)

    level_3 = level_3_task(level_2a, level_2b)
    return level_3


# ========== Visualization Demo ==========

def demonstrate_visualization():
    """
    Demonstrates flow visualization.

    NOTE: This requires graphviz to be installed:
        - System: apt-get install graphviz (Linux) or brew install graphviz (Mac)
        - Python: pip install graphviz
    """
    print("="*70)
    print("PREFECT FLOW VISUALIZATION DEMONSTRATION")
    print("="*70)

    print("\n1. Simple Linear Flow")
    print("-" * 70)
    print("Generating visualization...")
    try:
        simple_linear_flow.visualize()
        print("✓ Visualization saved/displayed")
        print("Pattern: extract_data → transform_data → load_data\n")
    except Exception as e:
        print(f"✗ Visualization failed: {e}")
        print("Make sure graphviz is installed: apt-get install graphviz\n")

    print("\n2. Branching Flow")
    print("-" * 70)
    print("Generating visualization...")
    try:
        branching_flow.visualize()
        print("✓ Visualization saved/displayed")
        print("Pattern: Shows conditional branching\n")
    except Exception as e:
        print(f"✗ Visualization failed: {e}\n")

    print("\n3. Parallel Flow")
    print("-" * 70)
    print("Generating visualization...")
    try:
        parallel_flow.visualize()
        print("✓ Visualization saved/displayed")
        print("Pattern: Shows parallel task execution\n")
    except Exception as e:
        print(f"✗ Visualization failed: {e}\n")

    print("\n4. Multi-Level Flow")
    print("-" * 70)
    print("Generating visualization...")
    try:
        multi_level_flow.visualize()
        print("✓ Visualization saved/displayed")
        print("Pattern: Shows multi-level dependencies\n")
    except Exception as e:
        print(f"✗ Visualization failed: {e}\n")

    print("="*70)
    print("IMPORTANT NOTES")
    print("="*70)
    print("""
1. flow.visualize() requirements:
   - Graphviz system library must be installed
   - Python graphviz package must be installed

2. Visualization captures:
   - Task dependencies (data flow)
   - Execution order
   - Branching and parallel patterns

3. Limitations:
   - Does not support task.map() visualization
   - Does not support task.submit() patterns
   - Executes the flow to capture dependencies

4. Alternative: Prefect UI
   - Start Prefect server: prefect server start
   - Run flows: python <your_flow>.py
   - View at: http://localhost:4200
   - Provides real-time execution graphs
   - Shows task states and artifacts
   - Interactive exploration
""")

    print("\n="*70)
    print("To visualize in Prefect UI:")
    print("="*70)
    print("""
1. Start Prefect server:
   prefect server start

2. Run any flow example:
   python 01_basic_visualization.py

3. Open browser:
   http://localhost:4200

4. Navigate to:
   Flow Runs → Select your run → Graph tab
""")
    print("="*70)


if __name__ == "__main__":
    # Option 1: Generate static visualizations
    print("\nGenerating static visualizations with flow.visualize()...\n")
    demonstrate_visualization()

    # Option 2: Run flows for UI visualization
    print("\n\nRunning flows for Prefect UI visualization...\n")
    print("="*70)
    print("EXECUTING FLOWS")
    print("="*70)

    print("\n1. Running Simple Linear Flow...")
    result1 = simple_linear_flow()
    print(f"   Result: {result1}")

    print("\n2. Running Branching Flow...")
    result2 = branching_flow()
    print(f"   Result: {result2}")

    print("\n3. Running Parallel Flow...")
    result3 = parallel_flow()
    print(f"   Result: {result3}")

    print("\n4. Running Multi-Level Flow...")
    result4 = multi_level_flow()
    print(f"   Result: {result4}")

    print("\n" + "="*70)
    print("✓ All flows executed successfully!")
    print("View in Prefect UI at: http://localhost:4200")
    print("="*70)
