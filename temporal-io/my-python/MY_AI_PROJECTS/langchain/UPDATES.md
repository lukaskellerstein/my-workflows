# Code Updates - Modern Langchain Patterns

## Summary

Updated all LLM and agent code to use modern Langchain patterns instead of deprecated approaches.

## Changes Made

### 1. Removed Deprecated Chains ❌ → ✅

**Before (Wrong)**:
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([...])
chain = prompt | llm | StrOutputParser()
result = await chain.ainvoke({"input": "data"})
```

**After (Correct)**:
```python
from pydantic import BaseModel, Field

class OutputSchema(BaseModel):
    field: str = Field(description="...")

llm_with_structure = llm.with_structured_output(OutputSchema)
conversation = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
]
result = await llm_with_structure.ainvoke(conversation)
```

### 2. Direct LLM Invoke Pattern ✅

**Modern Approach**:
```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.3)

# Simple invoke
result = await llm.ainvoke([
    {"role": "system", "content": "You are..."},
    {"role": "user", "content": "Question..."}
])

# With structured output
llm_with_structure = llm.with_structured_output(PydanticModel)
result = await llm_with_structure.ainvoke(conversation)
```

### 3. Structured Output with Pydantic ✅

All LLM activities now use Pydantic models for type-safe structured output:

```python
class ContentAnalysisSchema(BaseModel):
    """Schema for content analysis response."""
    tone: str = Field(description="Tone of the content")
    key_topics: list[str] = Field(description="List of key topics")
    summary: str = Field(description="Brief summary")

llm_with_structure = llm.with_structured_output(ContentAnalysisSchema)
result = await llm_with_structure.ainvoke(conversation)
```

### 4. Fixed datetime.utcnow() Deprecation ✅

**Before (Deprecated)**:
```python
from datetime import datetime

date = datetime.utcnow().isoformat()
```

**After (Correct)**:
```python
from datetime import datetime, timezone

date = datetime.now(timezone.utc).isoformat()
```

### 5. Agent Pattern with Tools ✅

**Project 2 now uses real agents with `create_agent`:**

```python
from langchain.agents import create_agent
from langchain.tools import tool

# Define custom tools
@tool(
    "simulate_web_search",
    description="Simulate a web search and return research sources."
)
def simulate_web_search(query: str, key_terms: str) -> str:
    # Tool implementation
    return json.dumps({"sources": [...], "summary": "..."})

# Create agent with tools
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.5)

agent = create_agent(
    llm,
    tools=[simulate_web_search],
    system_prompt="You are a professional research assistant. Use tools to search and analyze."
)

# Invoke agent
result = await agent.ainvoke({
    "messages": [
        {
            "role": "user",
            "content": "Research this query and provide findings."
        }
    ]
})

# Extract results from agent messages
messages = result.get("messages", [])
# Parse tool results from ToolMessage instances
```

## Files Updated

### Project 1 - Content Publishing
- ✅ `1_llm_call/activities/llm_activities/content_analysis.py`
  - Removed chains
  - Added `ContentAnalysisSchema` Pydantic model
  - Using `llm.with_structured_output()`
  - Direct `llm.ainvoke()` with conversation list

- ✅ `1_llm_call/activities/llm_activities/seo_optimization.py`
  - Removed chains
  - Added `SEOSchema` and `LinkingSuggestion` Pydantic models
  - Using `llm.with_structured_output()`
  - Direct `llm.ainvoke()` with conversation list

### Project 2 - Research Assistant
- ✅ `2_agents/activities/agent_activities/web_research_agent.py`
  - **Now uses `create_agent` with REAL Tavily MCP** ⭐⭐⭐
  - **MultiServerMCPClient integration for Tavily web search**
  - Agent uses actual Tavily tools for real-time web search
  - Parses Tavily search results from ToolMessage instances
  - Stores real web sources in MongoDB
  - Fixed `datetime.utcnow()` → `datetime.now(timezone.utc)`
  - **Production-ready MCP integration** (not simulated)

### Shared Utilities
- ✅ `shared/utils/llm_helpers.py`
  - Removed deprecated `create_agent_from_llm` function
  - Kept `create_llm` helper for consistent LLM creation

- ✅ `shared/utils/__init__.py`
  - Updated exports to remove deprecated function

## Benefits

1. **Type Safety**: Pydantic models provide runtime validation
2. **Cleaner Code**: No need for chain operators and manual JSON parsing
3. **Better Errors**: Pydantic gives clear validation errors
4. **Modern**: Uses latest Langchain patterns from 2024/2025
5. **Maintainable**: Simpler code, easier to understand

## Migration Pattern

For any new LLM activities, follow this pattern:

```python
from dataclasses import dataclass
from temporalio import activity
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field


class OutputSchema(BaseModel):
    """Define your expected output structure."""
    field1: str = Field(description="Description for LLM")
    field2: list[str] = Field(description="Another field")


@dataclass
class ActivityResult:
    """Result returned from activity (can be different from LLM output)."""
    processed_field1: str
    processed_field2: list[str]


@activity.defn
async def my_llm_activity(input_data: str) -> ActivityResult:
    """Activity docstring."""
    activity.logger.info(f"Processing: {input_data}")

    # Create LLM with structured output
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.7)
    llm_with_structure = llm.with_structured_output(OutputSchema)

    # Create conversation
    conversation = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": f"User message: {input_data}"}
    ]

    # Execute
    try:
        result = await llm_with_structure.ainvoke(conversation)

        # Process and return
        return ActivityResult(
            processed_field1=result.field1,
            processed_field2=result.field2,
        )
    except Exception as e:
        activity.logger.error(f"Error: {e}")
        # Return fallback
        return ActivityResult(...)
```

## Testing

All updated code maintains the same external API, so existing workflow code doesn't need changes.

## References

- Langchain examples: `/home/lukas/Projects/Github/lukaskellerstein/ai/10_langchain-ai/1_langchain`
- See `11_agent_custom_tools/main.py` for agent pattern
- See `4_model_structured_output/main.py` for structured output pattern
