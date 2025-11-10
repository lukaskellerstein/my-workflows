"""
Example 2: Dynamic Child Workflows
This demonstrates how to dynamically spawn child workflows at runtime based on
input data, allowing for flexible, data-driven workflow orchestration.
"""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


# Activities for different processing types
@activity.defn
async def process_image(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Processing image: {data.get('url')}")
    return {
        "id": data.get("id"),
        "type": "image",
        "url": data.get("url"),
        "width": 1920,
        "height": 1080,
        "processed": True,
    }


@activity.defn
async def process_video(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Processing video: {data.get('url')}")
    return {
        "id": data.get("id"),
        "type": "video",
        "url": data.get("url"),
        "duration": 120,
        "format": "mp4",
        "processed": True,
    }


@activity.defn
async def process_document(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Processing document: {data.get('url')}")
    return {
        "id": data.get("id"),
        "type": "document",
        "url": data.get("url"),
        "pages": 10,
        "format": "pdf",
        "processed": True,
    }


@activity.defn
async def process_audio(data: Dict[str, Any]) -> Dict[str, Any]:
    activity.logger.info(f"Processing audio: {data.get('url')}")
    return {
        "id": data.get("id"),
        "type": "audio",
        "url": data.get("url"),
        "duration": 180,
        "format": "mp3",
        "processed": True,
    }


# Child workflow for image processing
@workflow.defn
class ImageProcessingWorkflow:
    @workflow.run
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info(f"ImageProcessingWorkflow started: {data}")
        result = await workflow.execute_activity(
            process_image,
            data,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info(f"ImageProcessingWorkflow completed")
        return result


# Child workflow for video processing
@workflow.defn
class VideoProcessingWorkflow:
    @workflow.run
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info(f"VideoProcessingWorkflow started: {data}")
        result = await workflow.execute_activity(
            process_video,
            data,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info(f"VideoProcessingWorkflow completed")
        return result


# Child workflow for document processing
@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info(f"DocumentProcessingWorkflow started: {data}")
        result = await workflow.execute_activity(
            process_document,
            data,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info(f"DocumentProcessingWorkflow completed")
        return result


# Child workflow for audio processing
@workflow.defn
class AudioProcessingWorkflow:
    @workflow.run
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        workflow.logger.info(f"AudioProcessingWorkflow started: {data}")
        result = await workflow.execute_activity(
            process_audio,
            data,
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info(f"AudioProcessingWorkflow completed")
        return result


@dataclass
class MediaItem:
    """Represents a media item to be processed"""

    id: str
    type: str  # image, video, document, audio
    url: str
    metadata: Dict[str, Any]


# Parent workflow that dynamically spawns child workflows
@workflow.defn
class DynamicMediaProcessingWorkflow:
    @workflow.run
    async def run(self, items: List[MediaItem]) -> Dict[str, Any]:
        workflow.logger.info(f"Starting dynamic media processing for {len(items)} items")

        # Map of media types to their corresponding workflow classes
        workflow_map = {
            "image": ImageProcessingWorkflow,
            "video": VideoProcessingWorkflow,
            "document": DocumentProcessingWorkflow,
            "audio": AudioProcessingWorkflow,
        }

        results = []
        child_workflow_ids = []

        # Dynamically spawn child workflows based on media type
        for item in items:
            workflow.logger.info(
                f"Processing item {item.id} of type {item.type}"
            )

            # Determine which workflow to use based on type
            workflow_class = workflow_map.get(item.type)

            if workflow_class is None:
                workflow.logger.warning(f"Unknown media type: {item.type}")
                results.append({
                    "id": item.id,
                    "type": item.type,
                    "error": "Unknown media type",
                })
                continue

            # Prepare data for child workflow
            child_data = {
                "id": item.id,
                "url": item.url,
                "metadata": item.metadata,
            }

            # Dynamically execute child workflow with unique ID
            child_workflow_id = f"media-processing-{item.id}-{workflow.uuid4()}"
            child_workflow_ids.append(child_workflow_id)

            workflow.logger.info(
                f"Spawning {workflow_class.__name__} for item {item.id}"
            )

            result = await workflow.execute_child_workflow(
                workflow_class.run,
                child_data,
                id=child_workflow_id,
            )

            results.append(result)
            workflow.logger.info(f"Completed processing item {item.id}")

        workflow.logger.info(f"All {len(items)} items processed")

        return {
            "total_items": len(items),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "results": results,
            "child_workflow_ids": child_workflow_ids,
        }


# Advanced example: Dynamic workflow selection by name (string-based)
@workflow.defn
class DynamicWorkflowOrchestratorWorkflow:
    @workflow.run
    async def run(
        self, workflow_specs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes child workflows dynamically based on string names.
        workflow_specs format: [{"workflow": "ImageProcessingWorkflow", "data": {...}}, ...]
        """
        workflow.logger.info(
            f"Starting dynamic orchestrator for {len(workflow_specs)} workflows"
        )

        results = []

        for idx, spec in enumerate(workflow_specs):
            workflow_name = spec.get("workflow")
            workflow_data = spec.get("data", {})

            workflow.logger.info(
                f"Executing workflow {idx + 1}/{len(workflow_specs)}: {workflow_name}"
            )

            # Execute child workflow by name (dynamic string-based invocation) with unique ID
            child_workflow_id = f"dynamic-orchestrator-{idx}-{workflow.uuid4()}"

            result = await workflow.execute_child_workflow(
                workflow_name,  # Workflow name as string
                workflow_data,
                id=child_workflow_id,
            )

            results.append({
                "workflow": workflow_name,
                "result": result,
            })

            workflow.logger.info(f"Completed {workflow_name}")

        workflow.logger.info("All dynamic workflows completed")

        return {
            "total_workflows": len(workflow_specs),
            "results": results,
        }


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker with all workflows and activities
    async with Worker(
        client,
        task_queue="3-advanced-dynamic-child-workflows-task-queue",
        workflows=[
            DynamicMediaProcessingWorkflow,
            DynamicWorkflowOrchestratorWorkflow,
            ImageProcessingWorkflow,
            VideoProcessingWorkflow,
            DocumentProcessingWorkflow,
            AudioProcessingWorkflow,
        ],
        activities=[
            process_image,
            process_video,
            process_document,
            process_audio,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        # Example 1: Mixed media processing - dynamically spawn different child workflows
        print("\n" + "=" * 60)
        print("Example 1: Mixed Media Processing")
        print("=" * 60)

        media_items = [
            MediaItem(
                id="img-001",
                type="image",
                url="https://example.com/photo.jpg",
                metadata={"source": "camera"},
            ),
            MediaItem(
                id="vid-001",
                type="video",
                url="https://example.com/video.mp4",
                metadata={"source": "upload"},
            ),
            MediaItem(
                id="doc-001",
                type="document",
                url="https://example.com/report.pdf",
                metadata={"source": "scan"},
            ),
            MediaItem(
                id="aud-001",
                type="audio",
                url="https://example.com/podcast.mp3",
                metadata={"source": "recording"},
            ),
            MediaItem(
                id="img-002",
                type="image",
                url="https://example.com/screenshot.png",
                metadata={"source": "screenshot"},
            ),
        ]

        result1 = await client.execute_workflow(
            DynamicMediaProcessingWorkflow.run,
            media_items,
            id=f"3-advanced-dynamic-child-workflows-example-1-{uuid.uuid4()}",
            task_queue="3-advanced-dynamic-child-workflows-task-queue",
        )

        print(f"\nResult 1:")
        print(f"  Total items: {result1['total_items']}")
        print(f"  Successful: {result1['successful']}")
        print(f"  Failed: {result1['failed']}")
        print(f"  Child workflows spawned: {len(result1['child_workflow_ids'])}")
        for result in result1["results"]:
            print(f"    - {result['type']}: {result.get('url', 'N/A')}")

        # Example 2: Dynamic orchestration by workflow name (string-based)
        print("\n" + "=" * 60)
        print("Example 2: String-Based Dynamic Workflow Orchestration")
        print("=" * 60)

        workflow_specs = [
            {
                "workflow": "ImageProcessingWorkflow",
                "data": {"id": "img-100", "url": "https://example.com/image1.jpg"},
            },
            {
                "workflow": "VideoProcessingWorkflow",
                "data": {"id": "vid-100", "url": "https://example.com/video1.mp4"},
            },
            {
                "workflow": "DocumentProcessingWorkflow",
                "data": {"id": "doc-100", "url": "https://example.com/doc1.pdf"},
            },
        ]

        result2 = await client.execute_workflow(
            DynamicWorkflowOrchestratorWorkflow.run,
            workflow_specs,
            id=f"3-advanced-dynamic-child-workflows-example-2-{uuid.uuid4()}",
            task_queue="3-advanced-dynamic-child-workflows-task-queue",
        )

        print(f"\nResult 2:")
        print(f"  Total workflows executed: {result2['total_workflows']}")
        for result in result2["results"]:
            print(f"    - {result['workflow']}: {result['result']['type']}")

        # Example 3: Data-driven workflow selection
        print("\n" + "=" * 60)
        print("Example 3: Data-Driven Workflow Selection")
        print("=" * 60)

        # Simulate receiving data that determines what workflows to run
        incoming_data = [
            {"type": "image", "id": "img-200", "url": "https://example.com/img.png"},
            {"type": "image", "id": "img-201", "url": "https://example.com/img2.png"},
            {"type": "audio", "id": "aud-200", "url": "https://example.com/audio.mp3"},
        ]

        media_items_3 = [
            MediaItem(
                id=item["id"],
                type=item["type"],
                url=item["url"],
                metadata={"batch": "3"},
            )
            for item in incoming_data
        ]

        result3 = await client.execute_workflow(
            DynamicMediaProcessingWorkflow.run,
            media_items_3,
            id=f"3-advanced-dynamic-child-workflows-example-3-{uuid.uuid4()}",
            task_queue="3-advanced-dynamic-child-workflows-task-queue",
        )

        print(f"\nResult 3:")
        print(f"  Total items: {result3['total_items']}")
        print(f"  Successful: {result3['successful']}")
        print(f"  Workflows dynamically selected based on data type:")
        for result in result3["results"]:
            print(f"    - {result['id']}: {result['type']} -> processed")


if __name__ == "__main__":
    asyncio.run(main())
