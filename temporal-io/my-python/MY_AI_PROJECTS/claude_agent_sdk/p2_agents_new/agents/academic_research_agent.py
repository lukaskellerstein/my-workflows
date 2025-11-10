import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from shared.sdk_wrapper import Agent

from models.research import ResearchFact, ResearchSource, SourceType

from main_workflow.state import WorkflowState

from shared.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)


class AcademicResearchAgent:
    """Agent for academic paper research."""

    def __init__(self):
        self.logger = logging.getLogger("agent.academic_research")

    async def execute(
        self, state: WorkflowState, db: MongoDBClient, max_papers: int = 5
    ) -> List[ResearchSource]:
        """
        Search for academic papers and store in MongoDB.

        This is a simplified implementation that simulates academic research.
        In production, this would use Academia MCP integration.
        """
        self.logger.info(f"Starting academic research for run_id: {state.run_id}")

        # Use SDK Agent for academic research with Academia MCP
        async with Agent(
            name="academic_researcher",
            description="Academic paper research specialist using Academia MCP to search and analyze scientific papers",
            system_prompt="""You are an academic research agent with access to Academia MCP tools.

INSTRUCTIONS:
1. Use ArXiv MCP tools (search_papers, download_paper, list_papers) to find peer-reviewed papers
2. For each paper, fetch the full text or at minimum the abstract
3. Extract detailed information including full content
4. Return ONLY a JSON array, no additional text before or after

IMPORTANT: Your entire response must be a valid JSON array wrapped in ```json``` markdown code block.

For each paper, extract:
- title: Full academic title
- doi: Digital Object Identifier (if available)
- authors: List of author names
- date_published: Publication date in ISO format (YYYY-MM-DD)
- credibility_score: Assessment 0.9-1.0 for peer-reviewed papers
- abstract: Full abstract text
- content: Full paper text if available (if not available, leave empty)
- summary: A concise 2-3 sentence summary of the paper's contribution
- key_facts: Array of key findings with confidence and supporting text
- topics: List of research topics and keywords
- citations: List of cited paper DOIs (if available)

Response format:
```json
[
  {
    "title": "Paper Title",
    "doi": "10.1234/example.2024.001",
    "authors": ["Dr. First Last", "Prof. Another Name"],
    "date_published": "2024-01-15",
    "credibility_score": 0.95,
    "abstract": "Full abstract text from the paper...",
    "content": "Full paper text if accessible...",
    "summary": "Brief summary of the paper's main contribution",
    "key_facts": [
      {"fact": "Key finding from paper", "confidence": 0.95, "supporting_text": "Quote from paper"}
    ],
    "topics": ["AI", "machine learning", "code generation"],
    "citations": []
  }
]
```""",
            mcp_servers=["arxiv"],  # Enable Arxiv MCP (stdio transport)
        ) as agent:
            response_text = await agent.query(
                f"Research query: {state.query}\n\nGenerate academic paper results."
            )

        # Log the full response for debugging
        self.logger.info(f"Agent response length: {len(response_text)} characters")
        self.logger.info(f"FULL ACADEMIC AGENT RESPONSE:\n{response_text}\n{'='*80}")

        # Parse response
        json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            self.logger.info("Found JSON in markdown code block")
        else:
            json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
            json_str = json_match.group(0) if json_match else "[]"
            if json_match:
                self.logger.info("Found JSON array in response")
            else:
                self.logger.warning("No JSON found in agent response")
                self.logger.warning(f"Full response: {response_text}")

        try:
            papers_data = json.loads(json_str)
            self.logger.info(f"Successfully parsed {len(papers_data)} papers from JSON")
        except Exception as e:
            self.logger.error(f"Failed to parse academic research response: {e}")
            self.logger.error(f"JSON string attempted: {json_str[:200]}")
            papers_data = []

        # Convert to ResearchSource objects and store in MongoDB
        sources: List[ResearchSource] = []

        for paper_data in papers_data[:max_papers]:
            source = ResearchSource(
                id="",
                run_id=state.run_id,
                type=SourceType.ACADEMIC,
                title=paper_data.get("title", ""),
                doi=paper_data.get("doi", ""),
                authors=paper_data.get("authors", []),
                date_published=(
                    datetime.fromisoformat(paper_data["date_published"])
                    if "date_published" in paper_data
                    else None
                ),
                date_collected=datetime.now(),
                credibility_score=paper_data.get("credibility_score", 0.9),
                # Content fields
                content=paper_data.get("content"),
                abstract=paper_data.get("abstract"),
                summary=paper_data.get("summary"),
                raw_content=None,  # Could store PDF text if needed
                # Extracted information
                key_facts=[
                    ResearchFact(**fact) for fact in paper_data.get("key_facts", [])
                ],
                topics=paper_data.get("topics", []),
                citations=paper_data.get("citations", []),
            )

            # Store in MongoDB
            source_dict = source.model_dump(exclude={"id"})
            source_dict["date_published"] = (
                source.date_published.isoformat() if source.date_published else None
            )
            source_dict["date_collected"] = source.date_collected.isoformat()

            source_id = await db.insert_document("research_sources", source_dict)
            source.id = source_id

            sources.append(source)
            self.logger.info(f"Stored academic paper: {source.title}")

        self.logger.info(f"Academic research complete: {len(sources)} papers collected")
        return sources
