"""
Example 3: Runtime Workflow Builder
This demonstrates how to build complex workflow execution paths at runtime
based on configuration, enabling completely dynamic workflow construction.
"""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# Define activity types
class StepType(str, Enum):
    ACTIVITY = "activity"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    CHILD_WORKFLOW = "child_workflow"


# Define all available activities
@activity.defn(name="fetch_data")
async def fetch_data(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Fetching data with params: {params}")
    return {"data": f"fetched_{params.get('source')}", "count": 100}


@activity.defn(name="transform_data")
async def transform_data(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Transforming data: {params}")
    data = params.get("data", {})
    return {"data": f"transformed_{data}", "transformed": True}


@activity.defn(name="validate_data")
async def validate_data(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Validating data: {params}")
    return {"valid": True, "data": params.get("data")}


@activity.defn(name="save_to_database")
async def save_to_database(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Saving to database: {params}")
    return {"saved": True, "record_id": "rec_12345"}


@activity.defn(name="send_notification")
async def send_notification(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Sending notification: {params}")
    return {"notification_sent": True, "recipient": params.get("recipient")}


@activity.defn(name="generate_report")
async def generate_report(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Generating report: {params}")
    return {"report_id": "rpt_67890", "format": "pdf"}


@activity.defn(name="cleanup_resources")
async def cleanup_resources(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Cleaning up resources: {params}")
    return {"cleanup_complete": True}


@activity.defn(name="enrich_data")
async def enrich_data(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Enriching data: {params}")
    data = params.get("data", {})
    return {"data": data, "enriched": True, "metadata": {"timestamp": "2024-01-01"}}


@activity.defn(name="aggregate_results")
async def aggregate_results(params: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Aggregating results: {params}")
    results = params.get("results", [])
    return {"total": len(results), "summary": "aggregated"}


# Workflow step definition
@dataclass
class WorkflowStep:
    """Defines a single step in the dynamic workflow"""

    id: str
    type: str  # Store as string instead of enum for better serialization
    activity_name: Optional[str] = None  # For ACTIVITY type
    params: Optional[Dict[str, Any]] = None  # Parameters for the activity
    parallel_steps: Optional[List["WorkflowStep"]] = None  # For PARALLEL type
    condition_field: Optional[str] = None  # For CONDITIONAL type
    condition_value: Optional[Any] = None  # For CONDITIONAL type
    true_steps: Optional[List["WorkflowStep"]] = None  # For CONDITIONAL type
    false_steps: Optional[List["WorkflowStep"]] = None  # For CONDITIONAL type
    loop_count: Optional[int] = None  # For LOOP type
    loop_steps: Optional[List["WorkflowStep"]] = None  # For LOOP type
    child_workflow_name: Optional[str] = None  # For CHILD_WORKFLOW type


@dataclass
class WorkflowBlueprint:
    """Defines the complete workflow structure"""

    name: str
    description: str
    steps: List[WorkflowStep]
    initial_data: Dict[str, Any]


# Simple child workflow for testing
@workflow.defn
class DataProcessingChildWorkflow:
    @workflow.run
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info(f"Child workflow processing: {data}")
        return {"child_result": "processed", "data": data}


# Main dynamic workflow
@workflow.defn
class RuntimeBuiltWorkflow:
    @workflow.run
    async def run(self, blueprint: WorkflowBlueprint) -> Dict[str, Any]:
        workflow.logger.info(f"Starting runtime-built workflow: {blueprint.name}")
        workflow.logger.info(f"Description: {blueprint.description}")

        # Initialize workflow context with initial data
        context = {
            "initial_data": blueprint.initial_data,
            "execution_log": [],
            "results": {},
        }

        # Execute the workflow steps dynamically
        for step in blueprint.steps:
            step_result = await self._execute_step(step, context)
            context["results"][step.id] = step_result

        workflow.logger.info(f"Workflow completed: {blueprint.name}")

        return {
            "workflow": blueprint.name,
            "execution_log": context["execution_log"],
            "results": context["results"],
        }

    async def _execute_step(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Any:
        """Execute a single workflow step based on its type"""

        workflow.logger.info(f"Executing step: {step.id} (type: {step.type})")
        context["execution_log"].append(
            {"step_id": step.id, "type": step.type}
        )

        if step.type == StepType.ACTIVITY.value:
            return await self._execute_activity_step(step, context)
        elif step.type == StepType.PARALLEL.value:
            return await self._execute_parallel_step(step, context)
        elif step.type == StepType.CONDITIONAL.value:
            return await self._execute_conditional_step(step, context)
        elif step.type == StepType.LOOP.value:
            return await self._execute_loop_step(step, context)
        elif step.type == StepType.CHILD_WORKFLOW.value:
            return await self._execute_child_workflow_step(step, context)
        else:
            workflow.logger.warning(f"Unknown step type: {step.type}")
            return None

    async def _execute_activity_step(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Any:
        """Execute an activity"""

        workflow.logger.info(f"Executing activity: {step.activity_name}")

        # Merge step params with context data
        params = {**step.params} if step.params else {}
        params["context"] = context["results"]

        result = await workflow.execute_activity(
            step.activity_name,
            params,
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"Activity {step.activity_name} completed")
        return result

    async def _execute_parallel_step(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> List[Any]:
        """Execute multiple steps in parallel"""

        workflow.logger.info(f"Executing {len(step.parallel_steps)} steps in parallel")

        tasks = []
        for parallel_step in step.parallel_steps:
            tasks.append(self._execute_step(parallel_step, context))

        results = await asyncio.gather(*tasks)

        workflow.logger.info("Parallel execution completed")
        return list(results)

    async def _execute_conditional_step(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Any:
        """Execute conditional branch"""

        # Evaluate condition
        condition_value = context["results"].get(step.condition_field)
        condition_met = condition_value == step.condition_value

        workflow.logger.info(
            f"Condition: {step.condition_field} == {step.condition_value} -> {condition_met}"
        )

        if condition_met and step.true_steps:
            workflow.logger.info("Executing TRUE branch")
            results = []
            for true_step in step.true_steps:
                result = await self._execute_step(true_step, context)
                results.append(result)
            return {"branch": "true", "results": results}
        elif not condition_met and step.false_steps:
            workflow.logger.info("Executing FALSE branch")
            results = []
            for false_step in step.false_steps:
                result = await self._execute_step(false_step, context)
                results.append(result)
            return {"branch": "false", "results": results}
        else:
            return {"branch": "none", "results": []}

    async def _execute_loop_step(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> List[Any]:
        """Execute loop"""

        workflow.logger.info(f"Executing loop {step.loop_count} times")

        results = []
        for i in range(step.loop_count):
            workflow.logger.info(f"Loop iteration {i + 1}/{step.loop_count}")
            for loop_step in step.loop_steps:
                result = await self._execute_step(loop_step, context)
                results.append(result)

        workflow.logger.info("Loop completed")
        return results

    async def _execute_child_workflow_step(
        self, step: WorkflowStep, context: Dict[str, Any]
    ) -> Any:
        """Execute child workflow"""

        workflow.logger.info(f"Executing child workflow: {step.child_workflow_name}")

        params = {**step.params} if step.params else {}
        params["context"] = context["results"]

        result = await workflow.execute_child_workflow(
            step.child_workflow_name,
            params,
            id=f"child-{step.id}-{workflow.uuid4()}",
        )

        workflow.logger.info(f"Child workflow {step.child_workflow_name} completed")
        return result


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker
    async with Worker(
        client,
        task_queue="3-advanced-runtime-builder-task-queue",
        workflows=[RuntimeBuiltWorkflow, DataProcessingChildWorkflow],
        activities=[
            fetch_data,
            transform_data,
            validate_data,
            save_to_database,
            send_notification,
            generate_report,
            cleanup_resources,
            enrich_data,
            aggregate_results,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        # Example 1: Simple sequential workflow
        print("\n" + "=" * 60)
        print("Example 1: Sequential Data Processing Pipeline")
        print("=" * 60)

        blueprint1 = WorkflowBlueprint(
            name="Sequential Data Pipeline",
            description="Fetch, transform, validate, and save data",
            steps=[
                WorkflowStep(
                    id="step1",
                    type=StepType.ACTIVITY.value,
                    activity_name="fetch_data",
                    params={"source": "database"},
                ),
                WorkflowStep(
                    id="step2",
                    type=StepType.ACTIVITY.value,
                    activity_name="transform_data",
                    params={},
                ),
                WorkflowStep(
                    id="step3",
                    type=StepType.ACTIVITY.value,
                    activity_name="validate_data",
                    params={},
                ),
                WorkflowStep(
                    id="step4",
                    type=StepType.ACTIVITY.value,
                    activity_name="save_to_database",
                    params={},
                ),
            ],
            initial_data={"job_id": "job_001"},
        )

        result1 = await client.execute_workflow(
            RuntimeBuiltWorkflow.run,
            blueprint1,
            id=f"3-advanced-runtime-builder-example-1-{uuid.uuid4()}",
            task_queue="3-advanced-runtime-builder-task-queue",
        )

        print(f"\nResult 1:")
        print(f"  Workflow: {result1['workflow']}")
        print(f"  Steps executed: {len(result1['execution_log'])}")
        for log in result1["execution_log"]:
            print(f"    - {log['step_id']}: {log['type']}")

        # Example 2: Parallel execution
        print("\n" + "=" * 60)
        print("Example 2: Parallel Processing")
        print("=" * 60)

        blueprint2 = WorkflowBlueprint(
            name="Parallel Processing Pipeline",
            description="Fetch data, then process in parallel",
            steps=[
                WorkflowStep(
                    id="step1",
                    type=StepType.ACTIVITY.value,
                    activity_name="fetch_data",
                    params={"source": "api"},
                ),
                WorkflowStep(
                    id="step2",
                    type=StepType.PARALLEL.value,
                    parallel_steps=[
                        WorkflowStep(
                            id="step2a",
                            type=StepType.ACTIVITY.value,
                            activity_name="transform_data",
                            params={},
                        ),
                        WorkflowStep(
                            id="step2b",
                            type=StepType.ACTIVITY.value,
                            activity_name="enrich_data",
                            params={},
                        ),
                        WorkflowStep(
                            id="step2c",
                            type=StepType.ACTIVITY.value,
                            activity_name="generate_report",
                            params={},
                        ),
                    ],
                ),
                WorkflowStep(
                    id="step3",
                    type=StepType.ACTIVITY.value,
                    activity_name="send_notification",
                    params={"recipient": "admin@example.com"},
                ),
            ],
            initial_data={"job_id": "job_002"},
        )

        result2 = await client.execute_workflow(
            RuntimeBuiltWorkflow.run,
            blueprint2,
            id=f"3-advanced-runtime-builder-example-2-{uuid.uuid4()}",
            task_queue="3-advanced-runtime-builder-task-queue",
        )

        print(f"\nResult 2:")
        print(f"  Workflow: {result2['workflow']}")
        print(f"  Steps executed: {len(result2['execution_log'])}")
        for log in result2["execution_log"]:
            print(f"    - {log['step_id']}: {log['type']}")

        # Example 3: Complex workflow with loops and conditionals
        print("\n" + "=" * 60)
        print("Example 3: Complex Dynamic Workflow")
        print("=" * 60)

        blueprint3 = WorkflowBlueprint(
            name="Complex Dynamic Workflow",
            description="Demonstrates loops, conditionals, and child workflows",
            steps=[
                WorkflowStep(
                    id="step1",
                    type=StepType.ACTIVITY.value,
                    activity_name="fetch_data",
                    params={"source": "stream"},
                ),
                WorkflowStep(
                    id="step2",
                    type=StepType.LOOP.value,
                    loop_count=3,
                    loop_steps=[
                        WorkflowStep(
                            id="step2_loop",
                            type=StepType.ACTIVITY.value,
                            activity_name="transform_data",
                            params={},
                        ),
                    ],
                ),
                WorkflowStep(
                    id="step3",
                    type=StepType.CHILD_WORKFLOW.value,
                    child_workflow_name="DataProcessingChildWorkflow",
                    params={"data": "test"},
                ),
                WorkflowStep(
                    id="step4",
                    type=StepType.ACTIVITY.value,
                    activity_name="cleanup_resources",
                    params={},
                ),
            ],
            initial_data={"job_id": "job_003"},
        )

        result3 = await client.execute_workflow(
            RuntimeBuiltWorkflow.run,
            blueprint3,
            id=f"3-advanced-runtime-builder-example-3-{uuid.uuid4()}",
            task_queue="3-advanced-runtime-builder-task-queue",
        )

        print(f"\nResult 3:")
        print(f"  Workflow: {result3['workflow']}")
        print(f"  Steps executed: {len(result3['execution_log'])}")
        for log in result3["execution_log"]:
            print(f"    - {log['step_id']}: {log['type']}")


if __name__ == "__main__":
    asyncio.run(main())
