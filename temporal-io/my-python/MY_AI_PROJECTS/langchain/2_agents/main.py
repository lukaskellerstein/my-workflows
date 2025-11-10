"""Main runner for Research Assistant Workflow (Project 2)."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from temporalio.client import Client
from temporalio.worker import Worker

from workflows.research_workflow import ResearchAssistantWorkflow
from activities.deterministic.query_parsing import parse_research_query
from activities.agent_activities.web_research_agent import research_web_sources


async def run_worker():
    """Run the Temporal worker for research assistant."""
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="research-assistant-queue",
        workflows=[ResearchAssistantWorkflow],
        activities=[parse_research_query, research_web_sources],
        activity_executor=ThreadPoolExecutor(max_workers=10),
    )

    print("Research Assistant Worker started. Press Ctrl+C to exit.")
    await worker.run()


async def run_workflow():
    """Execute a sample research workflow."""
    client = await Client.connect("localhost:7233")

    # Sample research query
    query = "What are the latest developments in large language models for code generation?"

    result = await client.execute_workflow(
        ResearchAssistantWorkflow.run,
        query,
        id=f"research-{query[:20]}",
        task_queue="research-assistant-queue",
    )

    print("\n" + "=" * 80)
    print("RESEARCH ASSISTANT WORKFLOW COMPLETED")
    print("=" * 80)
    print(f"\nSession ID: {result['session_id']}")
    print(f"Query: {result['query']}")
    print(f"\nQuery Context:")
    print(f"  Type: {result['query_context']['type']}")
    print(f"  Key Terms: {', '.join(result['query_context']['key_terms'][:5])}")
    print(f"\nSources Found: {result['sources_found']}")
    print(f"\nSummary:\n{result['summary']}")
    print(f"\nTop Sources:")
    for i, source in enumerate(result['top_sources'], 1):
        print(f"  {i}. {source['title']}")
        print(f"     URL: {source['url']}")
        print(f"     Credibility: {source['credibility']:.2f}")
    print("=" * 80)


async def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        await run_worker()
    else:
        await run_workflow()


if __name__ == "__main__":
    asyncio.run(main())
