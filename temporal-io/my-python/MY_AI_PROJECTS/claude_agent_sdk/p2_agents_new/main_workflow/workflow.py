"""Workflow for Research Assistant with MongoDB."""

import asyncio
import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .activities import (
        adjust_memory,
        web_research_activity,
        academic_research_activity,
        enrich_and_cross_reference,
        build_knowledge_graph,
        synthesize_research,
        generate_audio_report,
    )

from .state import WorkflowState

logger = logging.getLogger(__name__)


@workflow.defn
class ResearchAssistantWorkflow:
    """
    Workflow orchestrating the research assistant pipeline with AI agents.

    Steps:
    1. Store query in memory (AI Agent + Mem0)
    2-3. Web and Academic research in PARALLEL (AI Agents + MongoDB)
    4. Enrich and cross-reference (Deterministic + MongoDB)
    5. Build knowledge graph (AI Agent + MongoDB)
    6. Synthesize research (AI Agent + MongoDB)
    7. Generate audio report (AI Agent + ElevenLabs + MongoDB)

    Performance optimization: Web and academic research run concurrently
    to reduce total workflow execution time.
    """

    @workflow.run
    async def run(self, query: str) -> dict:
        """Execute the research assistant workflow."""

        # Get workflow run_id to use for all data storage
        run_id = workflow.info().run_id
        workflow.logger.info(f"Starting research assistant workflow for: {query}")
        workflow.logger.info(f"Workflow run_id: {run_id}")

        # Create a State
        state = WorkflowState(
            query=query,
            run_id=run_id,
            web_sources=[],
            academic_sources=[],
            knowledge_graph=[],
            synthesis=None,
        )

        # Retry policy for AI agent activities
        agent_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=120),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Step 1: Store query in long-term memory (AI Agent + Mem0)
        workflow.logger.info("Storing query in long-term memory")
        memory_result = await workflow.execute_activity_method(
            activity=adjust_memory,
            args=[state],
            start_to_close_timeout=timedelta(seconds=180),  # 3 minutes for memory storage
            retry_policy=agent_retry_policy,
        )
        workflow.logger.info(f"Memory stored: {memory_result.get('success')}")

        # Steps 2 & 3: Web and Academic research in parallel (AI Agents)
        workflow.logger.info("Starting web and academic research in parallel")

        web_research_task = workflow.execute_activity_method(
            activity=web_research_activity,
            args=[state],
            start_to_close_timeout=timedelta(seconds=900),  # 15 minutes for AI agent operations
            retry_policy=agent_retry_policy,
        )

        academic_research_task = workflow.execute_activity_method(
            activity=academic_research_activity,
            args=[state],
            start_to_close_timeout=timedelta(seconds=900),  # 15 minutes for AI agent operations
            retry_policy=agent_retry_policy,
        )

        # Wait for both to complete
        web_sources, academic_sources = await asyncio.gather(
            web_research_task, academic_research_task
        )

        # Update state with research results
        state.web_sources = web_sources
        state.academic_sources = academic_sources

        workflow.logger.info(f"Web research complete: {len(web_sources)} sources")
        workflow.logger.info(f"Academic research complete: {len(academic_sources)} papers")

        # Step 4: Enrich and cross-reference (Deterministic)
        stats = await workflow.execute_activity_method(
            activity=enrich_and_cross_reference,
            args=[state],
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info(f"Data enrichment complete: {stats['total_sources']} total sources")

        # Step 5: Build knowledge graph (AI Agent)
        graph_nodes = await workflow.execute_activity_method(
            activity=build_knowledge_graph,
            args=[state],
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=agent_retry_policy,
        )

        # Update state with knowledge graph
        state.knowledge_graph = graph_nodes

        workflow.logger.info(f"Knowledge graph built: {len(graph_nodes)} nodes")

        # Step 6: Synthesize research (AI Agent + Mem0)
        # Now generates both text_report and audio_script, needs more time
        synthesis = await workflow.execute_activity_method(
            activity=synthesize_research,
            args=[state],
            start_to_close_timeout=timedelta(seconds=480),  # 8 minutes for dual text generation
            retry_policy=agent_retry_policy,
        )

        # Update state with synthesis for audio generation
        state.synthesis = synthesis

        workflow.logger.info(
            f"Research synthesis complete: {len(synthesis['main_findings'])} findings"
        )

        # Step 7: Generate audio report (AI Agent + ElevenLabs + MinIO)
        # Using run_id as the folder name in MinIO (matches Temporal UI Run ID)
        audio_result = await workflow.execute_activity_method(
            activity=generate_audio_report,
            args=[state],
            start_to_close_timeout=timedelta(seconds=300),  # 5 minutes for audio generation
            retry_policy=agent_retry_policy,
        )

        workflow.logger.info(f"Audio report generated: {audio_result.get('audio_id')}")
        workflow.logger.info(f"Text report MinIO URL: {audio_result.get('text_minio_url')}")
        if audio_result.get("success"):
            workflow.logger.info(f"Audio file MinIO URL: {audio_result.get('audio_minio_url')}")

        # Return comprehensive results
        result = {
            "run_id": run_id,
            "query": query,
            "statistics": stats,
            "web_sources_count": len(web_sources),
            "academic_sources_count": len(academic_sources),
            "knowledge_graph_nodes": len(graph_nodes),
            "main_findings": synthesis.get("main_findings", []),
            "conflicting_viewpoints": synthesis.get("conflicting_viewpoints", []),
            "knowledge_gaps": synthesis.get("knowledge_gaps", []),
            "audio_report_id": audio_result.get("audio_id"),
            "text_minio_url": audio_result.get("text_minio_url"),
            "audio_minio_url": audio_result.get("audio_minio_url"),
            "audio_generation_success": audio_result.get("success", False),
        }

        workflow.logger.info("Research assistant workflow complete")

        return result
