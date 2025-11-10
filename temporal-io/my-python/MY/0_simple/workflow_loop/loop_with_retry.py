"""
Example: Workflow with CONDITIONAL LOOP-BACK
This demonstrates a workflow that can return to previous activities based on conditions.

Use Case: Document Processing Pipeline
- Validate document
- Process document
- Review quality
- If quality check fails, return to processing with corrections
- If quality check passes, finalize
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker


@dataclass
class Document:
    id: str
    content: str
    attempt: int = 0
    corrections: Optional[str] = None


@dataclass
class ValidationResult:
    is_valid: bool
    message: str


@dataclass
class ProcessingResult:
    processed_content: str
    quality_score: float


@dataclass
class QualityCheckResult:
    passed: bool
    score: float
    corrections_needed: Optional[str] = None


# Activity 1: Validate document
@activity.defn
def validate_document(doc: Document) -> ValidationResult:
    activity.logger.info(f"[VALIDATE] Validating document {doc.id} (attempt {doc.attempt})")

    # Simple validation: check if content is not empty
    if not doc.content or len(doc.content) < 10:
        return ValidationResult(
            is_valid=False,
            message="Document content is too short"
        )

    return ValidationResult(
        is_valid=True,
        message="Document is valid"
    )


# Activity 2: Process document
@activity.defn
def process_document(doc: Document) -> ProcessingResult:
    activity.logger.info(f"[PROCESS] Processing document {doc.id} (attempt {doc.attempt})")

    # Simulate processing
    processed = doc.content.upper()

    # If corrections were provided, apply them
    if doc.corrections:
        activity.logger.info(f"[PROCESS] Applying corrections: {doc.corrections}")
        processed += f" [CORRECTED: {doc.corrections}]"

    # Quality score decreases with more attempts (simulating improvement)
    base_score = 0.5 + (doc.attempt * 0.2)
    quality_score = min(base_score, 0.95)

    return ProcessingResult(
        processed_content=processed,
        quality_score=quality_score
    )


# Activity 3: Quality check
@activity.defn
def check_quality(result: ProcessingResult, attempt: int) -> QualityCheckResult:
    activity.logger.info(f"[QUALITY CHECK] Checking quality (attempt {attempt})")
    activity.logger.info(f"[QUALITY CHECK] Quality score: {result.quality_score}")

    # Quality threshold: must be > 0.75
    threshold = 0.75
    passed = result.quality_score > threshold

    if not passed:
        corrections = "Add more details and improve formatting"
        activity.logger.warning(
            f"[QUALITY CHECK] FAILED - Score {result.quality_score} < {threshold}. "
            f"Corrections needed: {corrections}"
        )
        return QualityCheckResult(
            passed=False,
            score=result.quality_score,
            corrections_needed=corrections
        )

    activity.logger.info(f"[QUALITY CHECK] PASSED - Score {result.quality_score} > {threshold}")
    return QualityCheckResult(
        passed=True,
        score=result.quality_score
    )


# Activity 4: Finalize document
@activity.defn
def finalize_document(doc_id: str, final_content: str) -> str:
    activity.logger.info(f"[FINALIZE] Finalizing document {doc_id}")
    return f"Document {doc_id} finalized successfully!"


# Workflow with conditional loop-back
@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, doc: Document) -> str:
        workflow.logger.info(f"=== Starting workflow for document {doc.id} ===")

        max_attempts = 3
        current_doc = doc

        # Step 1: Initial validation (only once)
        workflow.logger.info(f"Step 1: Validating document {current_doc.id}")
        validation = await workflow.execute_activity(
            validate_document,
            current_doc,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not validation.is_valid:
            return f"Workflow failed: {validation.message}"

        workflow.logger.info(f"Validation passed: {validation.message}")

        # THIS IS THE LOOP: Steps 2-3 can repeat based on quality check
        while current_doc.attempt < max_attempts:
            current_doc.attempt += 1
            workflow.logger.info(f"\n=== LOOP ITERATION {current_doc.attempt} ===")

            # Step 2: Process document
            workflow.logger.info(f"Step 2: Processing document (attempt {current_doc.attempt})")
            processing_result = await workflow.execute_activity(
                process_document,
                current_doc,
                start_to_close_timeout=timedelta(seconds=10),
            )

            workflow.logger.info(
                f"Processing complete. Quality score: {processing_result.quality_score}"
            )

            # Step 3: Quality check
            workflow.logger.info(f"Step 3: Quality check (attempt {current_doc.attempt})")
            quality_check = await workflow.execute_activity(
                check_quality,
                args=[processing_result, current_doc.attempt],
                start_to_close_timeout=timedelta(seconds=10),
            )

            # LOOP DECISION POINT
            if quality_check.passed:
                workflow.logger.info(
                    f"✓ Quality check PASSED after {current_doc.attempt} attempt(s)"
                )
                # Exit the loop - proceed to finalization
                break
            else:
                workflow.logger.warning(
                    f"✗ Quality check FAILED on attempt {current_doc.attempt}"
                )

                if current_doc.attempt >= max_attempts:
                    workflow.logger.error(
                        f"Max attempts ({max_attempts}) reached. Workflow failed."
                    )
                    return (
                        f"Workflow failed after {max_attempts} attempts. "
                        f"Final quality score: {quality_check.score}"
                    )

                # LOOP BACK: Update document with corrections and go back to Step 2
                workflow.logger.info(
                    f"↻ LOOPING BACK to processing with corrections: "
                    f"{quality_check.corrections_needed}"
                )
                current_doc.corrections = quality_check.corrections_needed
                # Loop continues - will return to Step 2 (process_document)

        # Step 4: Finalize (only reached if quality check passed)
        workflow.logger.info(f"Step 4: Finalizing document")
        finalization = await workflow.execute_activity(
            finalize_document,
            args=[current_doc.id, processing_result.processed_content],
            start_to_close_timeout=timedelta(seconds=10),
        )

        workflow.logger.info(f"=== Workflow completed successfully ===")

        return (
            f"{finalization}\n"
            f"Total attempts: {current_doc.attempt}\n"
            f"Final quality score: {quality_check.score}"
        )


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="0-simple-workflow-loop-task-queue",
        workflows=[DocumentProcessingWorkflow],
        activities=[
            validate_document,
            process_document,
            check_quality,
            finalize_document,
        ],
        activity_executor=ThreadPoolExecutor(5),
    ):
        # Test case 1: Document that will need corrections (short content = low quality)
        print("\n" + "="*60)
        print("TEST 1: Document with initially low quality (will loop)")
        print("="*60)

        doc1 = Document(
            id="doc-001",
            content="Short content",  # This will have low quality initially
            attempt=0
        )

        result1 = await client.execute_workflow(
            DocumentProcessingWorkflow.run,
            doc1,
            id="workflow-loop-test-1",
            task_queue="0-simple-workflow-loop-task-queue",
        )
        print(f"\nWorkflow result:\n{result1}\n")

        # Test case 2: Document with better content (may pass on first try)
        print("\n" + "="*60)
        print("TEST 2: Document with better initial quality")
        print("="*60)

        doc2 = Document(
            id="doc-002",
            content="This is a much longer and more detailed document content that should have better quality",
            attempt=0
        )

        result2 = await client.execute_workflow(
            DocumentProcessingWorkflow.run,
            doc2,
            id="workflow-loop-test-2",
            task_queue="0-simple-workflow-loop-task-queue",
        )
        print(f"\nWorkflow result:\n{result2}\n")


if __name__ == "__main__":
    asyncio.run(main())
