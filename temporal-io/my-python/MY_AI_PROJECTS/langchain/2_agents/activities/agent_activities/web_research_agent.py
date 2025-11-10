"""Web research agent using Langchain with Tavily MCP."""

from dataclasses import dataclass
from datetime import datetime, timezone
from temporalio import activity
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import hashlib
import os


@dataclass
class WebResearchResult:
    """Result from web research."""

    sources_found: int
    sources_data: list[dict]
    summary: str
    credibility_scores: dict[str, float]


@activity.defn
async def research_web_sources(
    query: str, key_terms: list[str], session_id: str, mongodb_uri: str, db_name: str
) -> WebResearchResult:
    """
    Conduct web research using AI agent with Tavily MCP.

    This agent uses Tavily MCP for actual web search.

    Args:
        query: Research query
        key_terms: Key terms to search
        session_id: Research session ID
        mongodb_uri: MongoDB connection string
        db_name: Database name

    Returns:
        WebResearchResult with findings
    """
    activity.logger.info(f"Conducting web research for: {query[:50]}...")

    def get_tavily_mcp_url():
        """Get Tavily MCP URL with API key."""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        return f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"

    async def get_mcp_tools():
        """Load tools from Tavily MCP server."""
        client = MultiServerMCPClient({
            "tavily": {
                "url": get_tavily_mcp_url(),
                "transport": "streamable_http",
            }
        })
        tools = await client.get_tools()
        return tools, client

    try:
        # Get Tavily MCP tools
        activity.logger.info("Initializing Tavily MCP client...")
        mcp_tools, mcp_client = await get_mcp_tools()

        # Create LLM
        llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.5)

        # Create agent with Tavily tools
        agent = create_agent(
            llm,
            tools=mcp_tools,
            system_prompt=(
                "You are a professional research assistant. Use the Tavily search tools to find "
                "credible, up-to-date information on the web. Search for relevant sources, "
                "analyze the findings, and provide a comprehensive summary with key facts "
                "from each source."
            )
        )

        # Prepare agent input
        search_query = f"{query} {' '.join(key_terms[:3])}"
        conversation = {
            "messages": [
                {
                    "role": "user",
                    "content": f"Search for information about: '{search_query}'\n\n"
                              f"Use the Tavily search tool to find 3-5 credible sources. "
                              f"For each source, extract: title, URL, key facts. "
                              f"Provide a summary of your findings."
                }
            ]
        }

        # Invoke agent
        activity.logger.info("Invoking Tavily research agent...")
        agent_response = await agent.ainvoke(conversation)

        # Extract messages from agent response
        messages = agent_response.get("messages", [])

        # Parse tool results and agent analysis
        sources = []
        summary_parts = []

        for msg in messages:
            # Extract information from ToolMessage (Tavily results)
            if msg.__class__.__name__ == 'ToolMessage':
                try:
                    # Parse tool content
                    import json
                    tool_content = msg.content

                    # Try to parse as JSON
                    if isinstance(tool_content, str):
                        try:
                            tavily_data = json.loads(tool_content)
                        except json.JSONDecodeError:
                            # If not JSON, treat as plain text
                            activity.logger.info(f"Tool response: {tool_content[:200]}")
                            continue
                    else:
                        tavily_data = tool_content

                    # Extract sources from Tavily response
                    # Tavily typically returns: {"results": [...], "answer": "..."}
                    if isinstance(tavily_data, dict):
                        tavily_results = tavily_data.get("results", [])
                        for idx, result in enumerate(tavily_results[:5]):
                            source = {
                                "title": result.get("title", f"Source {idx+1}"),
                                "url": result.get("url", ""),
                                "key_facts": [
                                    result.get("content", "")[:200]  # First 200 chars as key fact
                                ],
                                "credibility": result.get("score", 0.8),
                                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")
                            }
                            sources.append(source)

                        # Add Tavily's answer if available
                        if tavily_data.get("answer"):
                            summary_parts.append(f"Search Results: {tavily_data['answer']}")

                except Exception as e:
                    activity.logger.warning(f"Error parsing Tavily result: {e}")

            # Extract agent's analysis from final AIMessage
            if msg.__class__.__name__ == 'AIMessage':
                if hasattr(msg, 'content') and msg.content:
                    # Get content from content blocks if available
                    content = None
                    if hasattr(msg, 'content_blocks') and msg.content_blocks:
                        # Extract text from content blocks
                        for block in msg.content_blocks:
                            if hasattr(block, 'text'):
                                content = block.text
                                break
                    elif isinstance(msg.content, str):
                        content = msg.content

                    # Add to summary if it's final analysis (not a tool call)
                    if content and (not hasattr(msg, 'tool_calls') or not msg.tool_calls):
                        summary_parts.append(f"Agent Analysis: {content}")

        # Compile final summary
        summary = "\n\n".join(summary_parts) if summary_parts else "Research completed via Tavily."

        # Store in MongoDB
        from ...agents.mongodb_client import ResearchMongoClient

        mongo_client = ResearchMongoClient(mongodb_uri, db_name)

        sources_data = []
        credibility_scores = {}

        for source in sources:
            source_id = hashlib.md5(source["url"].encode()).hexdigest()[:12]

            source_doc = {
                "_id": source_id,
                "type": "web",
                "title": source["title"],
                "url": source["url"],
                "key_facts": [
                    {
                        "fact": fact,
                        "confidence": 0.8,
                        "supporting_text": fact,
                    }
                    for fact in source["key_facts"]
                ],
                "credibility_score": source["credibility"],
                "topics": key_terms[:5],
                "query_id": session_id,
                "date_published": source["date"],
                "date_collected": datetime.now(timezone.utc).isoformat(),
            }

            try:
                mongo_client.add_source(source_doc)
                sources_data.append(source_doc)
                credibility_scores[source_id] = source["credibility"]
            except Exception as e:
                activity.logger.warning(f"Failed to store source: {e}")

        mongo_client.close()

        activity.logger.info(f"Web research completed. Found {len(sources)} sources")

        return WebResearchResult(
            sources_found=len(sources),
            sources_data=sources_data,
            summary=summary,
            credibility_scores=credibility_scores,
        )

    except Exception as e:
        activity.logger.error(f"Error during web research: {e}")
        return WebResearchResult(
            sources_found=0,
            sources_data=[],
            summary="Research failed",
            credibility_scores={},
        )
