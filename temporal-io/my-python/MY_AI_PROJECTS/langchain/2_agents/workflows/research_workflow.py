"""Research Assistant Workflow with MongoDB integration."""

from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from ..activities.deterministic.query_parsing import (
        QueryContext,
        parse_research_query,
    )
    from ..activities.agent_activities.web_research_agent import (
        WebResearchResult,
        research_web_sources,
    )


@workflow.defn
class ResearchAssistantWorkflow:
    """
    Workflow for automated research with MongoDB knowledge base.

    This workflow demonstrates:
    - Deterministic query parsing
    - AI agent for web research
    - MongoDB for persistent storage
    """

    @workflow.run
    async def run(
        self, query: str, mongodb_uri: str = "mongodb://localhost:27017/", db_name: str = "langchain_temporal"
    ) -> dict:
        """
        Execute the research workflow.

        Args:
            query: Research question
            mongodb_uri: MongoDB connection string
            db_name: Database name

        Returns:
            Research results dictionary
        """
        workflow.logger.info(f"Starting research for query: {query}")

        # Generate session ID
        import hashlib

        session_id = hashlib.md5(
            f"{query}-{workflow.info().workflow_id}".encode()
        ).hexdigest()[:12]

        # Initialize MongoDB session (simplified - normally would use activity)
        past_sessions = []  # Would query MongoDB here

        # Activity 1: Parse query (Deterministic)
        query_context: QueryContext = await workflow.execute_activity(
            parse_research_query,
            args=[query, past_sessions],
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info(
            f"Query parsed. Type: {query_context.query_type}, Terms: {query_context.key_terms[:3]}"
        )

        # Activity 2: Web research (AI Agent)
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
            backoff_coefficient=2.0,
        )

        web_results: WebResearchResult = await workflow.execute_activity(
            research_web_sources,
            args=[
                query,
                query_context.key_terms,
                session_id,
                mongodb_uri,
                db_name,
            ],
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"Web research completed. Found {web_results.sources_found} sources")

        # Compile results
        result = {
            "session_id": session_id,
            "query": query,
            "query_context": {
                "type": query_context.query_type,
                "key_terms": query_context.key_terms,
                "time_range": query_context.time_range,
            },
            "sources_found": web_results.sources_found,
            "summary": web_results.summary,
            "top_sources": [
                {
                    "title": s.get("title", ""),
                    "url": s.get("url", ""),
                    "credibility": s.get("credibility_score", 0),
                }
                for s in web_results.sources_data[:5]
            ],
        }

        workflow.logger.info(f"Research workflow completed for session: {session_id}")

        return result
