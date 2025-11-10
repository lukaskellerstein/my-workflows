# Architecture Improvements: MongoDB-Centric Design

## Overview

Based on user feedback, the Project 2 workflow architecture has been significantly improved to follow a **MongoDB-centric** design pattern where AI agents interact directly with MongoDB instead of passing large data structures through the workflow state.

## Problems Identified

### 1. Research Activities Not Using MCP Tools

- **Issue**: `research_academic_sources` was simulating research instead of using Academia MCP
- **Fix**: Added arXiv MCP integration using `arxiv-mcp-server`
- **Status**: ✅ Implemented - Now uses real arXiv search

### 2. Research Activities Not Storing to MongoDB

- **Issue**: Research activities returned data to workflow, which then stored it separately
- **Problem**: Inefficient - large data passing through workflow state
- **Fix**: Research activities now store directly to MongoDB
- **Status**: ✅ Implemented

### 3. Knowledge Graph Not Using MongoDB

- **Issue**: `build_knowledge_graph` received sources as parameter from workflow
- **Problem**: Tight coupling and data duplication
- **Fix**: Now queries MongoDB directly for sources
- **Status**: ✅ Implemented

## New Architecture

### Before (Old Architecture)

```
┌──────────────────────────────────────────────────────────┐
│                    Workflow State                         │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│  │ Web      │──┐   │ Academic │──┐   │ All      │       │
│  │ Sources  │  │   │ Sources  │  │   │ Sources  │       │
│  │ (List)   │  │   │ (List)   │  │   │ (List)   │       │
│  └──────────┘  │   └──────────┘  │   └──────────┘       │
│                 │                 │        │              │
│                 └─────────────────┘        │              │
│                          │                  │              │
│                          ▼                  ▼              │
│                 ┌────────────────┐  ┌──────────────┐     │
│                 │ Store to       │  │ Knowledge    │     │
│                 │ MongoDB        │  │ Graph        │     │
│                 └────────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────┘
```

**Problems**:

- ❌ Large lists passed through workflow state
- ❌ High memory usage
- ❌ Data duplication (in state + MongoDB)
- ❌ Tight coupling between activities
- ❌ Difficult to scale with many sources

### After (New Architecture)

```
┌──────────────────────────────────────────────────────────┐
│                    Workflow State                         │
│  ┌────────────┐      ┌────────────┐                      │
│  │ Web Count  │      │ Academic   │                      │
│  │ (Integer)  │      │ Count (Int)│                      │
│  └─────┬──────┘      └──────┬─────┘                      │
│        │                     │                             │
│        └──────────┬──────────┘                             │
│                   │                                         │
│          ┌────────▼────────┐                               │
│          │ Total Sources   │                               │
│          │    (Integer)    │                               │
│          └─────────────────┘                               │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │           MongoDB                     │
        │  ┌────────────────────────────┐      │
        │  │  research_sources          │      │
        │  │  - web sources             │      │
        │  │  - academic sources        │◄─────┼── Research agents write
        │  └────────┬───────────────────┘      │
        │           │                           │
        │           ▼                           │
        │  ┌────────────────────────────┐      │
        │  │  knowledge_graph           │      │
        │  │  - nodes                   │◄─────┼── KG builder queries & writes
        │  │  - relationships           │      │
        │  └────────────────────────────┘      │
        └──────────────────────────────────────┘
```

**Benefits**:

- ✅ Minimal data in workflow state (just counts)
- ✅ Low memory usage
- ✅ Single source of truth (MongoDB)
- ✅ Loose coupling between activities
- ✅ Easily scales to thousands of sources

## Changes Made

### 1. `research_web_sources` Activity

**File**: `2_agents/activities/agent_activities.py:132-291`

**Signature Change**:

```python
# Before
async def research_web_sources(
    query: ResearchQuery,
    context: ResearchContext,
    session_id: str,
) -> list[SourceDocument]:

# After
async def research_web_sources(
    query: ResearchQuery,
    context: ResearchContext,
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
) -> int:  # Returns count instead of list
```

**New Behavior**:

1. Research using Tavily MCP
2. **Store sources directly to MongoDB**
3. Return count of sources stored

**Code Addition**:

```python
# Store sources directly in MongoDB
if sources:
    from pymongo import MongoClient
    from datetime import datetime

    client = MongoClient(mongodb_uri)
    db = client[mongodb_database]
    collection = db["research_sources"]

    # Insert with upsert to avoid duplicates
    for source in sources:
        doc = {
            "_id": source.source_id,
            "session_id": session_id,
            "type": source.type,
            # ... other fields
        }
        collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    client.close()
    activity.logger.info(f"Stored {len(sources)} web sources in MongoDB")

return len(sources)
```

### 2. `research_academic_sources` Activity

**File**: `2_agents/activities/agent_activities.py:294-470`

**Similar Changes**:

- Added `mongodb_uri` and `mongodb_database` parameters
- Returns `int` instead of `list[SourceDocument]`
- Stores directly to MongoDB
- ✅ **Now uses arXiv MCP server** (not simulation!)

**arXiv MCP Integration**:

```python
# Uses arxiv-mcp-server for real academic paper search
async with MCPServerStdio(
    name="arXiv Research",
    params={
        "command": "uv",
        "args": ["tool", "run", "arxiv-mcp-server", "--storage-path", arxiv_storage_path],
    },
) as arxiv_server:
    agent = Agent(
        name="Academic Research Agent",
        model="gpt-4o-mini",
        mcp_servers=[arxiv_server],
        model_settings=ModelSettings(tool_choice="auto"),
    )
```

**Model Name Fix**:

```python
# Before
model="gpt-5-mini"  # Wrong model name

# After
model="gpt-4o-mini"  # Correct model name
```

**Environment Variable**:

```bash
ARXIV_STORAGE_PATH=/tmp/arxiv_papers  # Where to store downloaded papers
```

### 3. `build_knowledge_graph` Activity

**File**: `2_agents/activities/agent_activities.py:418-533`

**Signature Change**:

```python
# Before
async def build_knowledge_graph(
    session_id: str,
    all_sources: list[SourceDocument],  # Received from workflow
) -> list[KnowledgeGraphNode]:

# After
async def build_knowledge_graph(
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
) -> list[KnowledgeGraphNode]:  # Queries MongoDB
```

**New Behavior**:

1. **Query MongoDB** for session sources
2. Build knowledge graph from queried data
3. Return nodes (still returned for storage)

**Code Addition**:

```python
# Query sources from MongoDB
from pymongo import MongoClient

client = MongoClient(mongodb_uri)
db = client[mongodb_database]
collection = db["research_sources"]

# Get all sources for this session
sources_cursor = collection.find({"session_id": session_id})
sources_summary = []

for source in sources_cursor:
    summary = {
        "id": source.get("_id"),
        "title": source.get("title"),
        "topics": source.get("topics", []),
        "summary": source.get("content_summary") or source.get("abstract", ""),
    }
    sources_summary.append(summary)
    if len(sources_summary) >= 15:  # Limit to avoid token limits
        break

client.close()
```

### 4. `synthesize_research` Activity

**File**: `2_agents/activities/agent_activities.py:536-690`

**Signature Change**:

```python
# Before
async def synthesize_research(
    query: ResearchQuery,
    all_sources: list[SourceDocument],  # Received from workflow
    kg_nodes_count: int,
) -> ResearchSynthesis:

# After
async def synthesize_research(
    query: ResearchQuery,
    session_id: str,
    mongodb_uri: str,
    mongodb_database: str,
    kg_nodes_count: int,
) -> ResearchSynthesis:  # Queries MongoDB
```

**New Behavior**:

1. **Query MongoDB** for session sources
2. Synthesize research from queried data
3. Return synthesis

**Model Name Fix**:

```python
# Before
model="gpt-5-mini"  # Wrong model name

# After
model="gpt-4o-mini"  # Correct model name
```

### 5. Workflow Updates

**File**: `2_agents/workflows/__init__.py`

**Step 2-3 Changes** (Research activities):

```python
# Before: Returns lists
web_sources, academic_sources = await asyncio.gather(
    web_future, academic_future
)

# After: Returns counts
web_count, academic_count = await asyncio.gather(
    web_future, academic_future
)
```

**Note**: Also added `import asyncio` to use standard Python async utilities.

**Step 4 Removed** (Store sources):

```python
# REMOVED - No longer needed
# if all_sources:
#     stored_count = await workflow.execute_activity(
#         store_sources_in_mongodb,
#         args=[all_sources, session_id, mongodb_uri, mongodb_database],
#     )
```

**Step 5 Changes** (Build knowledge graph):

```python
# Before: Pass sources
kg_nodes = await workflow.execute_activity(
    build_knowledge_graph,
    args=[session_id, all_sources],  # Pass sources
)

# After: Pass MongoDB connection
kg_nodes = await workflow.execute_activity(
    build_knowledge_graph,
    args=[session_id, mongodb_uri, mongodb_database],  # Queries MongoDB
)
```

**Step 6 Changes** (Synthesize research):

```python
# Before: Pass sources
synthesis = await workflow.execute_activity(
    synthesize_research,
    args=[query, all_sources, kg_count],
)

# After: Pass session_id and MongoDB connection
synthesis = await workflow.execute_activity(
    synthesize_research,
    args=[query, session_id, mongodb_uri, mongodb_database, kg_count],
)
```

## Benefits

### 1. Performance

- **Memory**: Workflow state reduced from ~MB (with source lists) to ~bytes (just counts)
- **Scalability**: Can handle thousands of sources without workflow state explosion
- **Network**: Less data transferred between worker and Temporal server

### 2. Maintainability

- **Single Source of Truth**: MongoDB is the only place where sources are stored
- **Loose Coupling**: Activities don't depend on each other's output format
- **Easier Testing**: Each activity can be tested independently

### 3. Flexibility

- **Query Flexibility**: Activities can query exactly what they need from MongoDB
- **Reusability**: Knowledge graph and synthesis can work with any session
- **Incremental Updates**: Can add sources later without rerunning workflow

### 4. Cost

- **Reduced Workflow State**: Lower Temporal storage costs
- **Efficient Retries**: Failed activities don't need to re-receive large datasets

## Migration Notes

### Breaking Changes

1. **Research activities now return `int` instead of `list[SourceDocument]`**

   - Workflow must be updated to handle counts
   - Client code expecting source lists must query MongoDB

2. **`build_knowledge_graph` and `synthesize_research` require MongoDB parameters**

   - Must pass `mongodb_uri` and `mongodb_database`
   - Must have `session_id` to query correct data

### Non-Breaking Changes

- MongoDB schema unchanged
- MCP integrations still work the same way
- Workflow interface (input/output) unchanged

## Testing

### Unit Tests

Each activity can now be tested independently:

```python
# Test web research
async def test_web_research():
    count = await research_web_sources(
        query=test_query,
        context=test_context,
        session_id="test-123",
        mongodb_uri="mongodb://localhost:27017/",
        mongodb_database="test_db",
    )

    # Verify in MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    sources = list(client["test_db"]["research_sources"].find(
        {"session_id": "test-123"}
    ))
    assert len(sources) == count
```

### Integration Tests

```python
# Test full workflow
async def test_workflow():
    result = await client.execute_workflow(
        ResearchAssistantWorkflow.run,
        args=[query, mongodb_uri, mongodb_database],
    )

    # Verify in MongoDB
    client = MongoClient(mongodb_uri)
    db = client[mongodb_database]

    sources = list(db["research_sources"].find(
        {"session_id": result.session_id}
    ))
    assert len(sources) > 0

    kg_nodes = list(db["knowledge_graph"].find())
    assert len(kg_nodes) > 0
```

## Future Improvements

### 1. MCP Integrations - Complete!

All planned MCP integrations are now implemented:

- ✅ **Tavily MCP**: Web search using Tavily API
- ✅ **arXiv MCP**: Academic papers using arxiv-mcp-server
- ✅ **ElevenLabs MCP**: Text-to-speech using elevenlabs-mcp
- ✅ **MinIO MCP**: Object storage using aistor/mcp-server-aistor

### 2. Add Caching

```python
# Cache MongoDB queries
@lru_cache(maxsize=100)
def get_sources_for_session(session_id: str) -> list:
    # Query MongoDB
    pass
```

### 3. Add Streaming

```python
# Stream sources as they're found
async def research_web_sources_streaming(...):
    async for source in tavily_search(...):
        # Store immediately
        store_to_mongodb(source)
        yield source  # Stream to workflow
```

### 4. Add Incremental Updates

```python
# Allow adding sources to existing sessions
async def add_sources_to_session(
    session_id: str,
    new_sources: list[SourceDocument],
):
    # Store additional sources
    # Trigger re-synthesis
    pass
```

## Summary

The new MongoDB-centric architecture:

✅ **Reduces workflow state** from large lists to simple counts
✅ **Improves performance** and scalability
✅ **Simplifies maintenance** with loose coupling
✅ **Enables flexibility** with query-based access
✅ **Reduces costs** with efficient state management

All activities now interact directly with MongoDB, creating a more scalable and maintainable system! 🚀
