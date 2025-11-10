"""
Example 1: Dynamic Activity Invocation
This demonstrates how to execute activities dynamically at runtime by name,
allowing workflows to determine which activities to run based on input data.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# Define different activities that can be invoked dynamically
@activity.defn(name="validate_email")
async def validate_email(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Validating email: {data.get('email')}")
    email = data.get("email", "")
    is_valid = "@" in email and "." in email
    return {"field": "email", "valid": is_valid, "value": email}


@activity.defn(name="validate_phone")
async def validate_phone(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Validating phone: {data.get('phone')}")
    phone = data.get("phone", "")
    is_valid = len(phone.replace("-", "").replace(" ", "")) >= 10
    return {"field": "phone", "valid": is_valid, "value": phone}


@activity.defn(name="validate_age")
async def validate_age(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Validating age: {data.get('age')}")
    age = data.get("age", 0)
    is_valid = age >= 18 and age <= 120
    return {"field": "age", "valid": is_valid, "value": age}


@activity.defn(name="validate_address")
async def validate_address(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Validating address: {data.get('address')}")
    address = data.get("address", "")
    is_valid = len(address) > 10
    return {"field": "address", "valid": is_valid, "value": address}


@activity.defn(name="transform_uppercase")
async def transform_uppercase(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Transforming to uppercase: {data}")
    return {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}


@activity.defn(name="transform_lowercase")
async def transform_lowercase(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Transforming to lowercase: {data}")
    return {k: v.lower() if isinstance(v, str) else v for k, v in data.items()}


@activity.defn(name="enrich_data")
async def enrich_data(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Enriching data: {data}")
    data["timestamp"] = "2024-01-01T00:00:00Z"
    data["enriched"] = True
    return data


@dataclass
class ValidationRule:
    """Defines a validation rule to be executed dynamically"""

    activity_name: str
    field: str


@dataclass
class WorkflowConfig:
    """Configuration that determines which activities to run"""

    validation_rules: List[str]  # Activity names to execute for validation
    transformations: List[str]  # Activity names to execute for transformation
    enrichment: bool  # Whether to enrich the data


# Dynamic workflow that executes activities based on configuration
@workflow.defn
class DynamicActivityWorkflow:
    @workflow.run
    async def run(self, data: Dict[str, Any], config: WorkflowConfig) -> Dict[str, Any]:
        workflow.logger.info(f"Starting dynamic workflow with config: {config}")
        workflow.logger.info(f"Input data: {data}")

        result = {"input": data, "validation_results": [], "transformations": []}

        # Phase 1: Dynamic validation
        workflow.logger.info("Phase 1: Running dynamic validations")
        for activity_name in config.validation_rules:
            workflow.logger.info(f"Dynamically executing activity: {activity_name}")

            # Execute activity by name (dynamic invocation)
            validation_result = await workflow.execute_activity(
                activity_name,  # Activity name as string
                data,
                start_to_close_timeout=timedelta(seconds=10),
            )

            result["validation_results"].append(validation_result)
            workflow.logger.info(f"Validation result: {validation_result}")

        # Phase 2: Dynamic transformations
        workflow.logger.info("Phase 2: Running dynamic transformations")
        transformed_data = data.copy()
        for activity_name in config.transformations:
            workflow.logger.info(f"Dynamically executing transformation: {activity_name}")

            # Execute transformation activity by name
            transformed_data = await workflow.execute_activity(
                activity_name,
                transformed_data,
                start_to_close_timeout=timedelta(seconds=10),
            )

            result["transformations"].append(activity_name)
            workflow.logger.info(f"Data after {activity_name}: {transformed_data}")

        result["transformed_data"] = transformed_data

        # Phase 3: Optional enrichment
        if config.enrichment:
            workflow.logger.info("Phase 3: Enriching data")
            enriched_data = await workflow.execute_activity(
                "enrich_data",
                transformed_data,
                start_to_close_timeout=timedelta(seconds=10),
            )
            result["final_data"] = enriched_data
        else:
            result["final_data"] = transformed_data

        workflow.logger.info("Dynamic workflow completed")
        return result


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker with all activities registered
    async with Worker(
        client,
        task_queue="3-advanced-dynamic-activity-task-queue",
        workflows=[DynamicActivityWorkflow],
        activities=[
            validate_email,
            validate_phone,
            validate_age,
            validate_address,
            transform_uppercase,
            transform_lowercase,
            enrich_data,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        # Example 1: Validate email and phone, transform to uppercase
        print("\n" + "=" * 60)
        print("Example 1: Email + Phone validation, Uppercase transform")
        print("=" * 60)

        config1 = WorkflowConfig(
            validation_rules=["validate_email", "validate_phone"],
            transformations=["transform_uppercase"],
            enrichment=True,
        )

        data1 = {
            "email": "user@example.com",
            "phone": "555-1234-5678",
            "name": "john doe",
        }

        result1 = await client.execute_workflow(
            DynamicActivityWorkflow.run,
            args=[data1, config1],
            id="3-advanced-dynamic-activity-example-1",
            task_queue="3-advanced-dynamic-activity-task-queue",
        )

        print(f"\nResult 1:")
        print(f"  Validations: {len(result1['validation_results'])} executed")
        for validation in result1["validation_results"]:
            print(f"    - {validation['field']}: {validation['valid']}")
        print(f"  Transformations: {result1['transformations']}")
        print(f"  Final data: {result1['final_data']}")

        # Example 2: Different configuration - validate age and address, lowercase
        print("\n" + "=" * 60)
        print("Example 2: Age + Address validation, Lowercase transform")
        print("=" * 60)

        config2 = WorkflowConfig(
            validation_rules=["validate_age", "validate_address"],
            transformations=["transform_lowercase"],
            enrichment=False,
        )

        data2 = {
            "age": 25,
            "address": "123 Main Street, Springfield",
            "name": "JANE SMITH",
        }

        result2 = await client.execute_workflow(
            DynamicActivityWorkflow.run,
            args=[data2, config2],
            id="3-advanced-dynamic-activity-example-2",
            task_queue="3-advanced-dynamic-activity-task-queue",
        )

        print(f"\nResult 2:")
        print(f"  Validations: {len(result2['validation_results'])} executed")
        for validation in result2["validation_results"]:
            print(f"    - {validation['field']}: {validation['valid']}")
        print(f"  Transformations: {result2['transformations']}")
        print(f"  Final data: {result2['final_data']}")

        # Example 3: All validations, multiple transformations
        print("\n" + "=" * 60)
        print("Example 3: All validations, Multiple transformations")
        print("=" * 60)

        config3 = WorkflowConfig(
            validation_rules=[
                "validate_email",
                "validate_phone",
                "validate_age",
                "validate_address",
            ],
            transformations=["transform_uppercase", "enrich_data"],
            enrichment=True,
        )

        data3 = {
            "email": "admin@company.com",
            "phone": "555-9876-5432",
            "age": 30,
            "address": "456 Oak Avenue, Portland",
            "name": "bob johnson",
        }

        result3 = await client.execute_workflow(
            DynamicActivityWorkflow.run,
            args=[data3, config3],
            id="3-advanced-dynamic-activity-example-3",
            task_queue="3-advanced-dynamic-activity-task-queue",
        )

        print(f"\nResult 3:")
        print(f"  Validations: {len(result3['validation_results'])} executed")
        for validation in result3["validation_results"]:
            print(f"    - {validation['field']}: {validation['valid']}")
        print(f"  Transformations: {result3['transformations']}")
        print(f"  Final data: {result3['final_data']}")


if __name__ == "__main__":
    asyncio.run(main())
