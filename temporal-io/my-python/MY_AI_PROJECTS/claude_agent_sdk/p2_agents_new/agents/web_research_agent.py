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


class WebResearchAgent:
    """Agent for web research using Tavily search."""

    def __init__(self):
        self.logger = logging.getLogger("agent.web_research")

    async def execute(
        self, state: WorkflowState, db: MongoDBClient, max_sources: int = 5
    ) -> List[ResearchSource]:
        """
        Search web using Tavily and store results in MongoDB.

        This is a simplified implementation that simulates web research.
        In production, this would use actual Tavily MCP integration.
        """
        self.logger.info(f"Starting web research for run_id: {state.run_id}")

        # Use SDK Agent for web research with Tavily MCP
        async with Agent(
            name="web_researcher",
            description="Web research specialist using Tavily search to find and analyze web sources",
            system_prompt="""You are a web research agent with access to Tavily search via MCP.

INSTRUCTIONS:
1. Use the mcp__tavily__tavily_search tool to find relevant web sources for the query
2. For each URL found, use mcp__tavily__tavily_extract to get the full content
3. Extract information from each search result AND its full content
4. Return ONLY a JSON array, no additional text before or after

IMPORTANT: Your entire response must be a valid JSON array wrapped in ```json``` markdown code block.

For each source, extract:
- title: Article title from search result
- url: URL from search result
- authors: List of authors if available (can be empty list)
- date_published: Publication date in ISO format (YYYY-MM-DD) if available
- credibility_score: Your assessment 0.0-1.0 based on source quality
- content: The full article text extracted from the URL
- summary: A concise 2-3 sentence summary of the content
- key_facts: Array of extracted facts with confidence and supporting text
- topics: List of topic keywords

Response format:
```json
[
  {
    "title": "Article Title",
    "url": "https://example.com/article",
    "authors": ["Author Name"],
    "date_published": "2024-01-15",
    "credibility_score": 0.85,
    "content": "Full article text extracted from the webpage...",
    "summary": "Brief summary of the article's main points",
    "key_facts": [
      {"fact": "Key finding from article", "confidence": 0.9, "supporting_text": "Quote or summary"}
    ],
    "topics": ["AI", "code generation", "productivity"]
  }
]
```""",
            mcp_servers=["tavily"],  # Enable Tavily MCP (HTTP transport)
        ) as agent:
            response_text = await agent.query(
                f"Research query: {state.query}\n\nGenerate web research results."
            )

        # Log the full response for debugging
        self.logger.info(f"Agent response length: {len(response_text)} characters")
        self.logger.info(f"FULL WEB AGENT RESPONSE:\n{response_text}\n{'='*80}")

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
            sources_data = json.loads(json_str)
            self.logger.info(
                f"Successfully parsed {len(sources_data)} sources from JSON"
            )
        except Exception as e:
            self.logger.error(f"Failed to parse web research response: {e}")
            self.logger.error(f"JSON string attempted: {json_str[:200]}")
            sources_data = []

        # Convert to ResearchSource objects and store in MongoDB
        sources: List[ResearchSource] = []

        for source_data in sources_data[:max_sources]:
            # Create ResearchSource
            source = ResearchSource(
                id="",  # Will be set by MongoDB
                run_id=state.run_id,
                type=SourceType.WEB,
                title=source_data.get("title", ""),
                url=source_data.get("url", ""),
                authors=source_data.get("authors", []),
                date_published=(
                    datetime.fromisoformat(source_data["date_published"])
                    if "date_published" in source_data
                    else None
                ),
                date_collected=datetime.now(),
                credibility_score=source_data.get("credibility_score", 0.7),
                # Content fields
                content=source_data.get("content"),
                summary=source_data.get("summary"),
                abstract=None,  # Web sources don't have abstracts
                raw_content=None,  # Could store raw HTML if needed
                # Extracted information
                key_facts=[
                    ResearchFact(**fact) for fact in source_data.get("key_facts", [])
                ],
                topics=source_data.get("topics", []),
                citations=[],
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
            self.logger.info(f"Stored web source: {source.title}")

        self.logger.info(f"Web research complete: {len(sources)} sources collected")
        return sources
