"""Client to execute Research Assistant Workflow."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

from temporalio.client import Client
from temporalio.contrib.openai_agents import OpenAIAgentsPlugin
from temporalio.common import (
    TypedSearchAttributes,
    SearchAttributeKey,
    SearchAttributePair,
)

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workflows import ResearchAssistantWorkflow
from models import ResearchQuery


# Define search attribute key for tagging workflows
ai_agent_type = SearchAttributeKey.for_text("AIAgentType")


def print_separator(char="=", length=80):
    """Print a separator line."""
    print(char * length)


def print_header(title):
    """Print a formatted header."""
    print_separator()
    print(f" {title}")
    print_separator()


async def main():
    """Execute the research assistant workflow."""
    # Load environment variables
    load_dotenv()

    # Get configuration
    temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    mongodb_database = os.getenv("MONGODB_DATABASE", "research_assistant")

    # Connect to Temporal server
    client = await Client.connect(
        temporal_address,
        plugins=[OpenAIAgentsPlugin()],
    )

    # Create research query
    query = ResearchQuery(
        query="What are the latest developments in AI-powered code generation and how do they compare to traditional IDEs?",
        max_sources=15,
        include_academic=True,
        include_web=True,
        generate_audio=True,
    )

    print_header("Research Assistant Workflow - Execution")
    print(f"\nResearch Query: {query.query}")
    print(f"Max Sources: {query.max_sources}")
    print(f"Include Web: {query.include_web}")
    print(f"Include Academic: {query.include_academic}")
    print(f"Generate Audio: {query.generate_audio}")
    print(f"\nMongoDB: {mongodb_uri}{mongodb_database}")
    print("\nExecuting workflow...")
    print_separator()

    # Execute workflow
    result = await client.execute_workflow(
        ResearchAssistantWorkflow.run,
        args=[query, mongodb_uri, mongodb_database],
        id=f"research-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        task_queue="research-assistant-task-queue",
        search_attributes=TypedSearchAttributes(
            [SearchAttributePair(ai_agent_type, "OpenAIAgentSDK")]
        ),
    )

    # Display results
    print_header("Research Session Complete!")

    print(f"\nSession ID: {result.session_id}")
    print(f"Query: {result.query}")

    print("\n" + "-" * 80)
    print("CONTEXT FROM PAST RESEARCH")
    print("-" * 80)
    print(f"Related Past Sessions: {len(result.context.related_sessions)}")
    for i, session in enumerate(result.context.related_sessions, 1):
        print(f"  {i}. {session['query']} ({session['sources_count']} sources)")

    print(f"Existing Sources in DB: {result.context.existing_sources}")
    print(
        f"Known Topics: {', '.join(result.context.known_topics) if result.context.known_topics else 'None'}"
    )
    if result.context.knowledge_gaps:
        print(f"Knowledge Gaps Identified: {', '.join(result.context.knowledge_gaps)}")

    print("\n" + "-" * 80)
    print("SOURCES COLLECTED")
    print("-" * 80)
    print(f"Web Sources: {len(result.web_sources)}")
    for i, source in enumerate(result.web_sources[:5], 1):
        print(f"  {i}. {source.title}")
        print(f"     URL: {source.url}")
        print(f"     Credibility: {source.credibility_score:.2f}")
        print(f"     Topics: {', '.join(source.topics[:3])}")

    if len(result.web_sources) > 5:
        print(f"  ... and {len(result.web_sources) - 5} more")

    print(f"\nAcademic Sources: {len(result.academic_sources)}")
    for i, source in enumerate(result.academic_sources[:5], 1):
        print(f"  {i}. {source.title}")
        print(f"     DOI: {source.doi}")
        print(f"     Authors: {', '.join(source.authors[:3])}")
        print(f"     Credibility: {source.credibility_score:.2f}")

    if len(result.academic_sources) > 5:
        print(f"  ... and {len(result.academic_sources) - 5} more")

    print("\n" + "-" * 80)
    print("DATA ENRICHMENT")
    print("-" * 80)
    print(f"Total Sources Collected: {result.enrichment.total_sources}")
    print(f"Unique Sources (after dedup): {result.enrichment.deduplicated_sources}")
    print(f"Cross-References Created: {result.enrichment.cross_references}")
    print(f"Average Credibility Score: {result.enrichment.average_credibility:.2f}")

    print("\n" + "-" * 80)
    print("KNOWLEDGE GRAPH")
    print("-" * 80)
    print(f"Entities Identified: {result.knowledge_graph_nodes}")
    print("Entity types: Concepts, People, Organizations, Events")
    print("Relationships: Related-to, Contradicts, Supports, Cites")

    print("\n" + "-" * 80)
    print("RESEARCH SYNTHESIS")
    print("-" * 80)
    print(f"Title: {result.synthesis.title}")
    print(f"\nExecutive Summary:")
    print(f"{result.synthesis.executive_summary}")

    print(f"\nMain Findings ({len(result.synthesis.main_findings)}):")
    for i, finding in enumerate(result.synthesis.main_findings[:5], 1):
        print(f"  {i}. {finding['finding']}")
        print(f"     Confidence: {finding['confidence']:.2f}")
        print(f"     Sources: {len(finding['sources'])} source(s)")

    if len(result.synthesis.main_findings) > 5:
        print(f"  ... and {len(result.synthesis.main_findings) - 5} more findings")

    if result.synthesis.conflicting_viewpoints:
        print(
            f"\nConflicting Viewpoints ({len(result.synthesis.conflicting_viewpoints)}):"
        )
        for i, conflict in enumerate(result.synthesis.conflicting_viewpoints, 1):
            print(f"  {i}. {conflict['topic']}")
            for viewpoint in conflict.get("viewpoints", []):
                print(f"     - {viewpoint.get('position', 'N/A')}")

    if result.synthesis.knowledge_gaps:
        print(f"\nKnowledge Gaps Identified:")
        for gap in result.synthesis.knowledge_gaps:
            print(f"  - {gap}")

    print(f"\nOverall Confidence Level: {result.synthesis.confidence_level:.2%}")
    print(f"Based on {result.synthesis.sources_count} sources")

    if result.audio_report:
        print("\n" + "-" * 80)
        print("AUDIO REPORT")
        print("-" * 80)
        print(f"Audio ID: {result.audio_report.audio_id}")
        print(
            f"Duration: {result.audio_report.duration_seconds:.1f} seconds ({result.audio_report.duration_seconds / 60:.1f} minutes)"
        )
        print(f"Audio URL: {result.audio_report.audio_url}")
        print(f"\nChapters ({len(result.audio_report.chapters)}):")
        for chapter in result.audio_report.chapters:
            minutes = int(chapter["timestamp"] // 60)
            seconds = int(chapter["timestamp"] % 60)
            print(f"  {minutes:02d}:{seconds:02d} - {chapter['title']}")
        if result.audio_report.transcript_url:
            print(f"\nTranscript: {result.audio_report.transcript_url}")

    print("\n" + "-" * 80)
    print("SESSION METADATA")
    print("-" * 80)
    print(f"Created: {result.created_at}")
    print(f"Total Tokens Used: {result.total_tokens_used}")
    print(f"Duration: {result.duration_seconds:.2f} seconds")

    print_separator()
    print("Research session stored in MongoDB for future reference")
    print_separator()


if __name__ == "__main__":
    asyncio.run(main())
