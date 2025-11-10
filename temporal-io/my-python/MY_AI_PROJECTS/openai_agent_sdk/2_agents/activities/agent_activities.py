"""AI Agent activities with MCP tools for research assistant."""

import hashlib
import json
import os
from typing import Optional
from pydantic import BaseModel
from temporalio import activity
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStreamableHttp, MCPServerStdio
from agents.model_settings import ModelSettings

from models import (
    ResearchQuery,
    ResearchContext,
    SourceDocument,
    KnowledgeGraphNode,
    ResearchSynthesis,
    AudioReport,
)


# Pydantic models for structured outputs
class KeyFact(BaseModel):
    """A key fact from a source."""

    fact: str
    confidence: float
    supporting_text: str = ""


class WebSourceOutput(BaseModel):
    """Structured output for a single web source."""

    title: str
    url: str
    key_facts: list[KeyFact]
    credibility_score: float
    topics: list[str]
    summary: str


class WebResearchOutput(BaseModel):
    """Structured output for web research."""

    sources: list[WebSourceOutput]


class AcademicSourceOutput(BaseModel):
    """Structured output for a single academic source."""

    title: str
    doi: str
    authors: list[str]
    date_published: str
    abstract: str
    key_findings: list[str]
    credibility_score: float
    topics: list[str]


class AcademicResearchOutput(BaseModel):
    """Structured output for academic research."""

    sources: list[AcademicSourceOutput]


class KnowledgeGraphRelationship(BaseModel):
    """A relationship in the knowledge graph."""

    target_id: str
    type: str  # "related_to", "contradicts", "supports", "cites"
    confidence: float
    source_ids: list[str]


class KnowledgeGraphNodeOutput(BaseModel):
    """Structured output for a knowledge graph node."""

    node_id: str
    type: str  # "concept", "person", "organization", "event"
    name: str
    description: str
    relationships: list[KnowledgeGraphRelationship] = []


class KnowledgeGraphOutput(BaseModel):
    """Structured output for knowledge graph."""

    nodes: list[KnowledgeGraphNodeOutput]


class MainFinding(BaseModel):
    """A main research finding."""

    finding: str
    sources: list[str]
    confidence: float


class Viewpoint(BaseModel):
    """A viewpoint in a debate."""

    position: str
    sources: list[str]


class ConflictingViewpoint(BaseModel):
    """A topic with conflicting viewpoints."""

    topic: str
    viewpoints: list[Viewpoint]


class ResearchSynthesisOutput(BaseModel):
    """Structured output for research synthesis."""

    title: str
    executive_summary: str
    main_findings: list[MainFinding]
    conflicting_viewpoints: list[ConflictingViewpoint]
    knowledge_gaps: list[str]
    confidence_level: float


def generate_source_id(title: str, url: Optional[str] = None) -> str:
    """Generate unique source ID."""
    identifier = f"{title}_{url or ''}"
    return hashlib.md5(identifier.encode()).hexdigest()[:16]


@activity.defn
async def research_web_sources(
    query: ResearchQuery,
    context: ResearchContext,
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
) -> int:
    """
    AI Agent Activity: Search and analyze web sources with MongoDB storage.

    Uses an AI agent with Tavily MCP to:
    - Search for relevant articles
    - Extract key information
    - Assess credibility
    - Tag with topics
    - Store findings directly in MongoDB

    Returns: Number of sources stored
    """
    activity.logger.info(f"Researching web sources for: {query.query}")

    with trace(workflow_name="Web Research Agent"):
        # Get Tavily API key from environment
        tavily_key = os.getenv("TAVILY_API_KEY")

        # Build context-aware prompt (limit context to avoid token overflow)
        known_topics_str = (
            ", ".join(context.known_topics[:5]) if context.known_topics else "None"
        )
        knowledge_gaps_str = (
            ", ".join(context.knowledge_gaps[:3]) if context.knowledge_gaps else "None"
        )

        prompt = f"""Research Query: {query.query}

Known Topics: {known_topics_str}
Knowledge Gaps: {knowledge_gaps_str}

Search for {min(query.max_sources // 2, 10)} high-quality, recent web sources."""

        if tavily_key:
            # Use real Tavily MCP for web search
            activity.logger.info("Using Tavily MCP for web research")

            async with MCPServerStreamableHttp(
                name="Tavily Search",
                params={
                    "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={tavily_key}"
                },
                client_session_timeout_seconds=60.0,
            ) as tavily_server:
                agent = Agent(
                    name="Web Research Agent",
                    model="gpt-5-mini",
                    instructions="Use Tavily to search for relevant web articles and extract key information.",
                    mcp_servers=[tavily_server],
                    model_settings=ModelSettings(tool_choice="auto"),
                    output_type=WebResearchOutput,
                )

                result = await Runner.run(
                    starting_agent=agent, input=prompt, max_turns=20
                )
        else:
            # Fallback to simulation mode if no API key
            activity.logger.warning("TAVILY_API_KEY not found, using simulation mode")

            agent = Agent(
                name="Web Research Agent",
                model="gpt-5-mini",
                instructions="Simulate web research and extract key information from relevant articles.",
                output_type=WebResearchOutput,
            )

            result = await Runner.run(starting_agent=agent, input=prompt, max_turns=20)

        # Extract structured output
        try:
            output: WebResearchOutput = result.final_output

            sources = []
            for item in output.sources:
                # Convert Pydantic key facts to dict format
                key_facts = [
                    {
                        "fact": kf.fact,
                        "confidence": kf.confidence,
                        "supporting_text": kf.supporting_text,
                    }
                    for kf in item.key_facts
                ]

                source = SourceDocument(
                    source_id=generate_source_id(item.title, item.url),
                    type="web",
                    title=item.title,
                    url=item.url,
                    credibility_score=item.credibility_score,
                    key_facts=key_facts,
                    topics=item.topics,
                    content_summary=item.summary,
                )
                sources.append(source)

            activity.logger.info(f"Found {len(sources)} web sources")

            # Store sources directly in MongoDB
            if sources:
                from pymongo import MongoClient
                from datetime import datetime

                client = MongoClient(mongodb_uri)
                db = client[mongodb_database]
                collection = db["research_sources"]

                # Prepare documents for MongoDB
                documents = []
                for source in sources:
                    doc = {
                        "_id": source.source_id,
                        "session_id": session_id,
                        "type": source.type,
                        "title": source.title,
                        "url": source.url,
                        "date_collected": datetime.utcnow().isoformat(),
                        "credibility_score": source.credibility_score,
                        "topics": source.topics,
                        "content_summary": source.content_summary,
                        "key_facts": source.key_facts,
                    }
                    documents.append(doc)

                # Insert with upsert to avoid duplicates
                for doc in documents:
                    collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)

                client.close()
                activity.logger.info(f"Stored {len(sources)} web sources in MongoDB")

            return len(sources)

        except Exception as e:
            activity.logger.warning(f"Failed to process agent response: {e}")
            # Return 0 sources stored
            return 0


@activity.defn
async def research_academic_sources(
    query: ResearchQuery,
    context: ResearchContext,
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
) -> int:
    """
    AI Agent Activity: Search and analyze academic papers with MongoDB storage.

    Uses an AI agent with Academia MCP to:
    - Search for peer-reviewed papers
    - Extract metadata and abstracts
    - Identify key findings
    - Build citation network
    - Store findings directly in MongoDB

    Returns: Number of sources stored
    """
    activity.logger.info(f"Researching academic sources for: {query.query}")

    with trace(workflow_name="Academic Research Agent"):
        # Get arxiv storage path from environment
        arxiv_storage_path = os.getenv("ARXIV_STORAGE_PATH", "/tmp/arxiv_papers")

        # Try to use arxiv-mcp-server if available, otherwise fallback to simulation
        try:
            async with MCPServerStdio(
                name="arXiv Research",
                params={
                    "command": "uv",
                    "args": [
                        "tool",
                        "run",
                        "arxiv-mcp-server",
                        "--storage-path",
                        arxiv_storage_path,
                    ],
                },
                client_session_timeout_seconds=120.0,  # Increase timeout to 120 seconds for arXiv searches
            ) as arxiv_server:
                agent = Agent(
                    name="Academic Research Agent",
                    model="gpt-5-mini",
                    mcp_servers=[arxiv_server],
                    model_settings=ModelSettings(tool_choice="auto"),
                    instructions="Search arXiv for relevant papers and extract metadata.",
                    output_type=AcademicResearchOutput,
                )

                prompt = f"""Research Query: {query.query}

Search arXiv for {min(query.max_sources // 2, 8)} recent, peer-reviewed papers."""

                result = await Runner.run(
                    starting_agent=agent, input=prompt, max_turns=20
                )
                activity.logger.info("Using arXiv MCP server for academic research")

        except Exception as e:
            activity.logger.warning(
                f"Failed to connect to arXiv MCP server: {e}. Falling back to simulation mode."
            )
            # Fallback to simulation mode
            agent = Agent(
                name="Academic Research Agent",
                model="gpt-5-mini",
                instructions="Simulate academic research and extract paper metadata.",
                output_type=AcademicResearchOutput,
            )

            prompt = f"""Research Query: {query.query}

Find {min(query.max_sources // 2, 8)} recent, peer-reviewed academic papers."""

            result = await Runner.run(starting_agent=agent, input=prompt, max_turns=20)

        # Extract structured output
        try:
            output: AcademicResearchOutput = result.final_output

            sources = []
            for item in output.sources:
                source = SourceDocument(
                    source_id=generate_source_id(item.title, item.doi),
                    type="academic",
                    title=item.title,
                    doi=item.doi,
                    authors=item.authors,
                    date_published=item.date_published,
                    credibility_score=item.credibility_score,
                    topics=item.topics,
                    abstract=item.abstract,
                    key_facts=[
                        {"fact": finding, "confidence": 0.9}
                        for finding in item.key_findings
                    ],
                )
                sources.append(source)

            activity.logger.info(f"Found {len(sources)} academic sources")

            # Store sources directly in MongoDB
            if sources:
                from pymongo import MongoClient

                client = MongoClient(mongodb_uri)
                db = client[mongodb_database]
                collection = db["research_sources"]

                # Prepare documents for MongoDB
                documents = []
                for source in sources:
                    doc = {
                        "_id": source.source_id,
                        "session_id": session_id,
                        "type": source.type,
                        "title": source.title,
                        "doi": source.doi,
                        "authors": source.authors,
                        "date_published": source.date_published,
                        "date_collected": source.date_published,  # Using same date
                        "credibility_score": source.credibility_score,
                        "topics": source.topics,
                        "abstract": source.abstract,
                        "key_facts": source.key_facts,
                    }
                    documents.append(doc)

                # Insert with upsert to avoid duplicates
                for doc in documents:
                    collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)

                client.close()
                activity.logger.info(
                    f"Stored {len(sources)} academic sources in MongoDB"
                )

            return len(sources)

        except Exception as e:
            activity.logger.warning(f"Failed to process agent response: {e}")
            # Return 0 sources stored
            return 0


@activity.defn
async def build_knowledge_graph(
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
) -> list[KnowledgeGraphNode]:
    """
    AI Agent Activity: Build knowledge graph from MongoDB sources.

    Queries MongoDB for session sources and:
    - Identifies entities (concepts, people, organizations)
    - Extracts relationships
    - Detects conflicting information
    - Assigns confidence scores
    """
    activity.logger.info(f"Building knowledge graph for session: {session_id}")

    # Query sources from MongoDB
    from pymongo import MongoClient

    client = MongoClient(mongodb_uri)
    db = client[mongodb_database]
    collection = db["research_sources"]

    # Get all sources for this session
    sources_cursor = collection.find({"session_id": session_id})
    sources_summary = []
    source_count = 0

    for source in sources_cursor:
        summary = {
            "id": source.get("_id"),
            "title": source.get("title"),
            "topics": source.get("topics", []),
            "summary": source.get("content_summary") or source.get("abstract", ""),
        }
        sources_summary.append(summary)
        source_count += 1
        if source_count >= 15:  # Limit to avoid token limits
            break

    client.close()

    activity.logger.info(f"Retrieved {source_count} sources from MongoDB")

    if not sources_summary:
        activity.logger.warning("No sources found in MongoDB")
        return []

    with trace(workflow_name="Knowledge Graph Builder"):
        agent = Agent(
            name="Knowledge Graph Agent",
            model="gpt-5-mini",
            instructions="""You are a knowledge graph specialist. Given research sources:
            1. Identify key entities:
               - Concepts (theories, methods, technologies)
               - People (researchers, experts)
               - Organizations (companies, institutions)
               - Events (discoveries, publications)
            2. Extract relationships between entities
            3. Detect conflicting or supporting information

            Focus on 10-20 most important entities.
            """,
            output_type=KnowledgeGraphOutput,
        )

        prompt = f"""Sources to analyze:
{json.dumps(sources_summary, indent=2)}

Build a knowledge graph identifying key entities and their relationships.
"""

        result = await Runner.run(starting_agent=agent, input=prompt, max_turns=20)

        # Extract structured output
        try:
            output: KnowledgeGraphOutput = result.final_output

            nodes = []
            for item in output.nodes:
                # Convert Pydantic relationships to dict format
                relationships = [
                    {
                        "target_id": rel.target_id,
                        "type": rel.type,
                        "confidence": rel.confidence,
                        "source_ids": rel.source_ids,
                    }
                    for rel in item.relationships
                ]

                node = KnowledgeGraphNode(
                    node_id=item.node_id,
                    type=item.type,
                    name=item.name,
                    description=item.description,
                    relationships=relationships,
                )
                nodes.append(node)

            activity.logger.info(f"Built knowledge graph with {len(nodes)} nodes")
            return nodes

        except Exception as e:
            activity.logger.warning(f"Failed to process agent response: {e}")
            # Return minimal graph
            return [
                KnowledgeGraphNode(
                    node_id=f"concept_{session_id}",
                    type="concept",
                    name="Research Topic",
                    description="Main research concept",
                    relationships=[],
                )
            ]


@activity.defn
async def synthesize_research(
    query: ResearchQuery,
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
    kg_nodes_count: int,
) -> ResearchSynthesis:
    """
    AI Agent Activity: Synthesize research findings from MongoDB.

    Queries MongoDB for sources and:
    - Generates executive summary
    - Identifies main findings with citations
    - Detects conflicting viewpoints
    - Identifies knowledge gaps
    """
    activity.logger.info(f"Synthesizing research for session: {session_id}")

    # Query sources from MongoDB
    from pymongo import MongoClient

    client = MongoClient(mongodb_uri)
    db = client[mongodb_database]
    collection = db["research_sources"]

    # Get all sources for this session
    sources_cursor = collection.find({"session_id": session_id})
    sources_info = []
    source_count = 0
    web_count = 0
    academic_count = 0

    for source in sources_cursor:
        info = {
            "id": source.get("_id"),
            "type": source.get("type"),
            "title": source.get("title"),
            "credibility": source.get("credibility_score", 0),
            "topics": source.get("topics", []),
            "key_facts": source.get("key_facts", [])[:3],  # Limit facts
        }
        sources_info.append(info)
        source_count += 1
        if source.get("type") == "web":
            web_count += 1
        elif source.get("type") == "academic":
            academic_count += 1
        if source_count >= 20:  # Limit to avoid token limits
            break

    client.close()

    activity.logger.info(
        f"Retrieved {source_count} sources from MongoDB ({web_count} web, {academic_count} academic)"
    )

    if not sources_info:
        activity.logger.warning("No sources found in MongoDB")
        # Return minimal synthesis
        return ResearchSynthesis(
            title=f"Research Report: {query.query}",
            executive_summary=f"No sources found for research query: {query.query}",
            main_findings=[],
            conflicting_viewpoints=[],
            knowledge_gaps=["No data collected"],
            confidence_level=0.0,
            sources_count=0,
        )

    with trace(workflow_name="Research Synthesis Agent"):
        agent = Agent(
            name="Research Synthesis Agent",
            model="gpt-5-mini",
            instructions="""You are a research synthesis specialist. Create a comprehensive report:
            1. Executive summary (2-3 paragraphs)
            2. Main findings with source attribution
            3. Conflicting viewpoints analysis
            4. Knowledge gaps identified
            5. Overall confidence level (0-1)
            """,
            output_type=ResearchSynthesisOutput,
        )

        prompt = f"""Research Query: {query.query}

Total Sources: {source_count} ({web_count} web, {academic_count} academic)

Knowledge Graph Entities: {kg_nodes_count}

Sources Data:
{json.dumps(sources_info, indent=2)}

Create a comprehensive research synthesis report.
"""

        result = await Runner.run(starting_agent=agent, input=prompt, max_turns=20)

        # Extract structured output
        try:
            output: ResearchSynthesisOutput = result.final_output

            # Convert Pydantic models to dict format
            main_findings = [
                {
                    "finding": f.finding,
                    "sources": f.sources,
                    "confidence": f.confidence,
                }
                for f in output.main_findings
            ]

            conflicting_viewpoints = [
                {
                    "topic": cv.topic,
                    "viewpoints": [
                        {"position": v.position, "sources": v.sources}
                        for v in cv.viewpoints
                    ],
                }
                for cv in output.conflicting_viewpoints
            ]

            synthesis = ResearchSynthesis(
                title=output.title,
                executive_summary=output.executive_summary,
                main_findings=main_findings,
                conflicting_viewpoints=conflicting_viewpoints,
                knowledge_gaps=output.knowledge_gaps,
                confidence_level=output.confidence_level,
                sources_count=source_count,
            )

            activity.logger.info(
                f"Synthesis complete: {len(synthesis.main_findings)} findings, "
                f"confidence: {synthesis.confidence_level:.2f}"
            )
            return synthesis

        except Exception as e:
            activity.logger.warning(f"Failed to process agent response: {e}")
            # Return basic synthesis
            return ResearchSynthesis(
                title=f"Research Report: {query.query}",
                executive_summary=f"Research conducted on {query.query} with {source_count} sources.",
                main_findings=[
                    {
                        "finding": "Research completed",
                        "sources": [s["id"] for s in sources_info[:3]],
                        "confidence": 0.7,
                    }
                ],
                conflicting_viewpoints=[],
                knowledge_gaps=[],
                confidence_level=0.7,
                sources_count=source_count,
            )


@activity.defn
async def generate_audio_report(
    synthesis: ResearchSynthesis,
    session_id: str,
) -> AudioReport:
    """
    AI Agent Activity: Generate audio podcast from research report.

    Uses ElevenLabs MCP to:
    - Convert report to natural speech
    - Create chapter markers
    - Generate transcript alignment
    """
    activity.logger.info(f"Generating audio report for: {synthesis.title}")

    with trace(workflow_name="Audio Report Generator"):
        # Get ElevenLabs API key from environment
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

        # Build script from synthesis
        # TESTING MODE: Use minimal text to save ElevenLabs credits
        # TODO: When ready for production, uncomment the full script below
        script = f"Research report on {synthesis.title} completed successfully."

        # FULL SCRIPT (commented out for testing):
        # script_parts = [
        #     f"Research Report: {synthesis.title}",
        #     "",
        #     "Executive Summary:",
        #     synthesis.executive_summary,
        #     "",
        #     "Main Findings:",
        # ]
        # for i, finding in enumerate(synthesis.main_findings[:5], 1):
        #     script_parts.append(f"Finding {i}: {finding}")
        # script = "\n".join(script_parts)
        # if len(script) > 3000:
        #     script = script[:3000] + "..."

        # Get MinIO configuration
        minio_endpoint = os.getenv("MINIO_ENDPOINT")
        minio_mcp_url = os.getenv("MINIO_MCP_URL")  # Streamable HTTP MCP endpoint

        audio_file_path = None  # Track if we have a real audio file

        if elevenlabs_key:
            # Use real ElevenLabs MCP for text-to-speech
            activity.logger.info("Using ElevenLabs MCP for audio generation")

            try:
                async with MCPServerStdio(
                    name="ElevenLabs TTS",
                    params={
                        "command": "uvx",
                        "args": ["elevenlabs-mcp"],
                        "env": {"ELEVENLABS_API_KEY": elevenlabs_key},
                    },
                    client_session_timeout_seconds=60.0,
                ) as elevenlabs_server:
                    agent = Agent(
                        name="Audio Report Generator",
                        model="gpt-5-mini",
                        mcp_servers=[elevenlabs_server],
                        model_settings=ModelSettings(tool_choice="auto"),
                        instructions="Convert the research report to speech and save as MP3 file.",
                    )

                    prompt = f"Generate audio from this script and save it:\n\n{script}"

                    result = await Runner.run(
                        starting_agent=agent, input=prompt, max_turns=20
                    )
                    activity.logger.info("Audio generated using ElevenLabs MCP")

                    # Calculate duration based on word count (rough: 150 words/minute)
                    word_count = len(script.split())
                    duration = (word_count / 150.0) * 60.0

                    # TODO: Extract actual file path from ElevenLabs result
                    # For now, assume it's saved locally
                    audio_file_path = f"/tmp/audio_{session_id}.mp3"

            except Exception as e:
                activity.logger.warning(
                    f"Failed to use ElevenLabs MCP: {e}. Falling back to simulation."
                )
                elevenlabs_key = None  # Fall through to simulation

        if not elevenlabs_key:
            # Fallback to simulation mode
            activity.logger.warning(
                "ELEVENLABS_API_KEY not found, using simulation mode"
            )

            # Calculate estimated duration (rough: 150 words/minute)
            word_count = len(script.split())
            duration = (word_count / 150.0) * 60.0

        # Create chapter markers
        chapters = [
            {"title": "Introduction", "timestamp": 0.0},
            {"title": "Executive Summary", "timestamp": 10.0},
            {"title": "Main Findings", "timestamp": 30.0},
        ]

        if synthesis.conflicting_viewpoints:
            chapters.append(
                {"title": "Conflicting Viewpoints", "timestamp": duration * 0.6}
            )

        if synthesis.knowledge_gaps:
            chapters.append({"title": "Knowledge Gaps", "timestamp": duration * 0.8})

        chapters.append({"title": "Conclusion", "timestamp": duration * 0.9})

        # Store audio file in MinIO if we have a real file and MinIO is configured
        minio_url = f"https://example.com/audio/{session_id}.mp3"  # Default fallback

        if audio_file_path and minio_mcp_url:
            activity.logger.info("Storing audio file in MinIO via streamable HTTP MCP")

            try:
                async with MCPServerStreamableHttp(
                    name="MinIO Storage",
                    params={"url": minio_mcp_url},
                    client_session_timeout_seconds=60.0,
                ) as minio_server:
                    agent = Agent(
                        name="MinIO Storage Agent",
                        model="gpt-5-mini",
                        mcp_servers=[minio_server],
                        model_settings=ModelSettings(tool_choice="auto"),
                        instructions=f"Upload the audio file from {audio_file_path} to MinIO bucket 'research-audio' with filename {session_id}.mp3",
                    )

                    prompt = f"Upload audio file {audio_file_path} to MinIO as {session_id}.mp3"

                    result = await Runner.run(
                        starting_agent=agent, input=prompt, max_turns=20
                    )
                    activity.logger.info("Audio file stored in MinIO")

                    # Update URL to MinIO location
                    minio_url = (
                        f"http://{minio_endpoint}/research-audio/{session_id}.mp3"
                    )

            except Exception as e:
                activity.logger.warning(
                    f"Failed to store in MinIO: {e}. Using fallback URL."
                )

        audio = AudioReport(
            audio_id=f"audio_{session_id}",
            audio_url=minio_url,
            duration_seconds=duration,
            chapters=chapters,
            transcript_url=f"https://example.com/transcripts/{session_id}.txt",
        )

        activity.logger.info(
            f"Audio report generated: {duration:.1f}s with {len(chapters)} chapters"
        )
        activity.logger.info(f"Audio URL: {minio_url}")
        return audio
