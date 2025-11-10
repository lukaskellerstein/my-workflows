"""Research Assistant Workflow with AI Agents and MongoDB."""

import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models import ResearchQuery, ResearchSession
    from activities import (
        query_context_from_mongodb,
        enrich_and_deduplicate,
        store_knowledge_graph,
        store_research_session,
    )
    from activities.agent_activities import (
        research_web_sources,
        research_academic_sources,
        build_knowledge_graph,
        synthesize_research,
        generate_audio_report,
    )


@workflow.defn
class ResearchAssistantWorkflow:
    """
    Research Assistant Workflow demonstrating AI agents with MCP tools and MongoDB.

    NEW ARCHITECTURE (MongoDB-centric):
    1. Query MongoDB for related past research (deterministic + MongoDB)
    2. Web research agent with Tavily MCP → stores directly to MongoDB (AI agent + MongoDB)
    3. Academic research agent with Academia MCP → stores directly to MongoDB (AI agent + MongoDB)
    4. Enrich and deduplicate data in MongoDB (deterministic + MongoDB)
    5. Build knowledge graph from MongoDB sources (AI agent queries MongoDB)
    6. Synthesize research from MongoDB sources (AI agent queries MongoDB)
    7. Generate audio report (AI agent, optional)
    8. Store complete research session (deterministic + MongoDB)

    Key improvement: Research agents and synthesis agents query/store MongoDB directly,
    reducing data passed through workflow state.
    """

    @workflow.run
    async def run(
        self,
        query: ResearchQuery,
        mongodb_uri: str,
        mongodb_database: str,
    ) -> ResearchSession:
        """Execute the research assistant workflow."""

        workflow.logger.info(f"Starting research workflow for: {query.query}")

        # Generate session ID
        session_id = f"research_{workflow.info().workflow_id}"

        # Agent retry policy
        agent_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=30),
            backoff_coefficient=2.0,
            maximum_attempts=3,
        )

        # Step 1: Query context from MongoDB
        context = await workflow.execute_activity(
            query_context_from_mongodb,
            args=[query, mongodb_uri, mongodb_database],
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info(
            f"Context retrieved: {len(context.related_sessions)} related sessions, "
            f"{context.existing_sources} existing sources"
        )

        # Step 2 & 3: Research agents store directly to MongoDB (parallel execution)
        web_count = 0
        academic_count = 0

        if query.include_web and query.include_academic:
            # Run both in parallel - each stores to MongoDB
            web_future = workflow.execute_activity(
                research_web_sources,
                args=[query, context, session_id, mongodb_uri, mongodb_database],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=agent_retry_policy,
            )

            academic_future = workflow.execute_activity(
                research_academic_sources,
                args=[query, context, session_id, mongodb_uri, mongodb_database],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=agent_retry_policy,
            )

            web_count, academic_count = await asyncio.gather(
                web_future, academic_future
            )

        elif query.include_web:
            web_count = await workflow.execute_activity(
                research_web_sources,
                args=[query, context, session_id, mongodb_uri, mongodb_database],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=agent_retry_policy,
            )

        elif query.include_academic:
            academic_count = await workflow.execute_activity(
                research_academic_sources,
                args=[query, context, session_id, mongodb_uri, mongodb_database],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=agent_retry_policy,
            )

        total_sources = web_count + academic_count
        workflow.logger.info(
            f"Research complete: {web_count} web sources, "
            f"{academic_count} academic sources stored in MongoDB"
        )

        # Step 4: Enrich and deduplicate (now happens after research stores data)
        enrichment = await workflow.execute_activity(
            enrich_and_deduplicate,
            args=[session_id, mongodb_uri, mongodb_database],
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info(
            f"Data enriched: {enrichment.deduplicated_sources} unique sources, "
            f"{enrichment.cross_references} cross-references"
        )

        # Step 5: Build knowledge graph (queries MongoDB for sources)
        kg_nodes = await workflow.execute_activity(
            build_knowledge_graph,
            args=[session_id, mongodb_uri, mongodb_database],
            start_to_close_timeout=timedelta(seconds=120),
            retry_policy=agent_retry_policy,
        )

        # Store knowledge graph
        kg_count = 0
        if kg_nodes:
            kg_count = await workflow.execute_activity(
                store_knowledge_graph,
                args=[kg_nodes, mongodb_uri, mongodb_database],
                start_to_close_timeout=timedelta(seconds=60),
            )
            workflow.logger.info(f"Stored {kg_count} knowledge graph nodes")

        # Step 6: Synthesize research (queries MongoDB for sources)
        synthesis = await workflow.execute_activity(
            synthesize_research,
            args=[query, session_id, mongodb_uri, mongodb_database, kg_count],
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=agent_retry_policy,
        )

        workflow.logger.info(
            f"Research synthesized: {len(synthesis.main_findings)} findings, "
            f"confidence: {synthesis.confidence_level:.2f}"
        )

        # Step 8: Generate audio report (optional)
        audio_report = None
        if query.generate_audio:
            audio_report = await workflow.execute_activity(
                generate_audio_report,
                args=[synthesis, session_id],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=agent_retry_policy,
            )
            workflow.logger.info(
                f"Audio report generated: {audio_report.duration_seconds:.1f}s"
            )

        # Step 7: Store complete research session
        session_data = {
            "session_id": session_id,
            "query": query.query,
            "sources_collected": total_sources,
            "web_sources": web_count,
            "academic_sources": academic_count,
            "knowledge_graph_nodes": kg_count,
            "synthesis_title": synthesis.title,
            "confidence_level": synthesis.confidence_level,
            "knowledge_gaps": synthesis.knowledge_gaps,
            "has_audio": audio_report is not None,
        }

        await workflow.execute_activity(
            store_research_session,
            args=[session_data, mongodb_uri, mongodb_database],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Build final result
        # Note: web_sources and academic_sources are now empty lists since data is in MongoDB
        # The client can query MongoDB directly to get sources if needed
        result = ResearchSession(
            session_id=session_id,
            query=query.query,
            context=context,
            web_sources=[],  # Sources stored in MongoDB
            academic_sources=[],  # Sources stored in MongoDB
            enrichment=enrichment,
            knowledge_graph_nodes=kg_count,
            synthesis=synthesis,
            audio_report=audio_report,
            total_tokens_used=0,  # Would track in real implementation
            duration_seconds=0.0,  # Would calculate in real implementation
        )

        workflow.logger.info(
            f"Research session complete: {session_id} "
            f"({total_sources} sources in MongoDB, {kg_count} KG nodes)"
        )

        return result
