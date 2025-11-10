# Project 2: Research Assistant with Knowledge Base

This project demonstrates how to use AI agents equipped with **real MCP tools** in Temporal workflows, combined with MongoDB for persistent knowledge storage.

## 🎉 MCP Tools Status - All Active!

- ✅ **Tavily Web Search**: Real web search using Tavily MCP
- ✅ **arXiv Academic Search**: Real academic paper search using arXiv MCP
- ✅ **ElevenLabs Text-to-Speech**: Real audio generation using ElevenLabs MCP
- ✅ **MinIO Object Storage**: Store audio files in MinIO using aistor MCP

**Documentation**:
- [ARXIV_MCP_ENABLED.md](./ARXIV_MCP_ENABLED.md) - arXiv academic search integration
- [ELEVENLABS_MCP_ENABLED.md](./ELEVENLABS_MCP_ENABLED.md) - ElevenLabs text-to-speech integration
- [MINIO_MCP_ENABLED.md](./MINIO_MCP_ENABLED.md) - MinIO object storage integration

## Workflow Overview

The Research Assistant orchestrates multiple specialized AI agents to conduct comprehensive research, building a persistent knowledge base:

```
┌──────────────────┐
│ Research Query   │
└────────┬─────────┘
         │
         ▼
┌───────────────────────────┐
│ 1. Query Context          │ ◄── Deterministic + MongoDB
│    - Past research        │
│    - Known topics         │
│    - Knowledge gaps       │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 2. Web Research Agent     │ ◄── AI Agent + Tavily MCP
│    - Search articles      │     (Parallel)
│    - Extract facts        │
│    - Assess credibility   │──┐
└────────┬──────────────────┘  │
         │                      │
         ▼                      │
┌───────────────────────────┐  │
│ 3. Academic Agent         │ ◄┘ AI Agent + Academia MCP
│    - Search papers        │     (Parallel)
│    - Extract findings     │
│    - Build citations      │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 4. Store in MongoDB       │ ◄── Deterministic + MongoDB
│    - Save all sources     │
│    - Index by topics      │
│    - Tag with metadata    │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 5. Enrich & Deduplicate   │ ◄── Deterministic + MongoDB
│    - Remove duplicates    │
│    - Create cross-refs    │
│    - Calculate scores     │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 6. Knowledge Graph Agent  │ ◄── AI Agent + MongoDB
│    - Identify entities    │
│    - Extract relationships│
│    - Detect conflicts     │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 7. Synthesis Agent        │ ◄── AI Agent + Mem0
│    - Recall past research │
│    - Generate summary     │
│    - Identify gaps        │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 8. Audio Report Agent     │ ◄── AI Agent + ElevenLabs
│    - Convert to speech    │     (Optional)
│    - Create chapters      │
│    - Generate transcript  │
└────────┬──────────────────┘
         │
         ▼
┌───────────────────────────┐
│ 9. Store Session          │ ◄── Deterministic + MongoDB
│    - Save complete report │
│    - Update knowledge base│
└────────┬──────────────────┘
         │
         ▼
┌──────────────────┐
│ Research Session │
└──────────────────┘
```

## Features

### AI Agents with MCP Tools
- **Web Research Agent**: Uses Tavily MCP for web search and analysis
- **Academic Research Agent**: Uses Academia MCP for peer-reviewed papers
- **Knowledge Graph Builder**: Constructs entity-relationship graphs from sources
- **Synthesis Agent**: Uses Mem0 MCP to recall past research and generate insights
- **Audio Report Generator**: Uses ElevenLabs MCP for text-to-speech conversion

### MongoDB Knowledge Base
- **Persistent Storage**: All research sources stored for future reference
- **Indexed Collections**: Fast retrieval by topics, dates, credibility
- **Knowledge Graph**: Entity and relationship storage
- **Research Sessions**: Complete audit trail of all research workflows
- **Cross-Referencing**: Automatic linking of related sources

### Advanced Features
- Parallel execution of web and academic research
- Deduplication across sources
- Credibility scoring
- Topic extraction and clustering
- Knowledge gap identification
- Confidence scoring for findings
- Audio podcast generation with chapter markers

## MongoDB Collections

### research_sources
```javascript
{
  "_id": "source_id",
  "type": "web|academic",
  "title": "...",
  "url": "...",
  "doi": "...",
  "authors": [],
  "date_published": "...",
  "credibility_score": 0.95,
  "key_facts": [{fact, confidence, supporting_text}],
  "topics": ["AI", "machine learning"],
  "citations": ["source_id_2"],
  "query_id": "research_session_id"
}
```

### knowledge_graph
```javascript
{
  "_id": "node_id",
  "type": "concept|person|organization|event",
  "name": "...",
  "description": "...",
  "relationships": [
    {
      "target_id": "node_id_2",
      "type": "related_to|contradicts|supports",
      "confidence": 0.85,
      "source_ids": ["src1", "src2"]
    }
  ]
}
```

### research_sessions
```javascript
{
  "_id": "session_id",
  "query": "...",
  "sources_collected": 42,
  "knowledge_graph_nodes": 15,
  "confidence_level": 0.87,
  "knowledge_gaps": ["gap1", "gap2"],
  "timestamp": "..."
}
```

## Project Structure

```
2_agents/
├── models/
│   └── __init__.py              # Data models
├── activities/
│   ├── __init__.py              # MongoDB activities
│   └── agent_activities.py      # AI agent activities
├── workflows/
│   └── __init__.py              # ResearchAssistantWorkflow
├── mcp_configs/
│   └── (MCP server configs)
├── run_worker.py                # Worker script
├── run_workflow.py              # Client script
└── README.md                    # This file
```

## Prerequisites

1. **Temporal Server**: `temporal server start-dev`
2. **MongoDB**: Running on `mongodb://localhost:27017/`
   ```bash
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```
3. **Environment Variables**: Set in `.env`:
   ```
   OPENAI_API_KEY=your_key_here
   TEMPORAL_ADDRESS=localhost:7233
   MONGODB_URI=mongodb://admin:admin123@localhost:27017/
   MONGODB_DATABASE=research_assistant
   ```
   **Note**: The MongoDB URI includes authentication credentials (username: `admin`, password: `admin123`)

4. **Dependencies**: `uv sync` from project root

## Running the Example

### Start MongoDB

```bash
# Start MongoDB with authentication
docker run -d -p 27017:27017 \
  --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin123 \
  mongo:latest
```

**Alternative: MongoDB without authentication** (for development only):
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
# Then update .env to: MONGODB_URI=mongodb://localhost:27017/
```

### Start Temporal Server

```bash
temporal server start-dev
```

### Start the Worker

```bash
source .venv/bin/activate
python 2_agents/run_worker.py
```

### Execute the Workflow

```bash
source .venv/bin/activate
python 2_agents/run_workflow.py
```

## Expected Output

```
================================================================================
 Research Assistant Workflow - Execution
================================================================================

Research Query: What are the latest developments in AI-powered code generation...
Max Sources: 15
Include Web: True
Include Academic: True
Generate Audio: True

MongoDB: mongodb://localhost:27017/research_assistant

Executing workflow...
================================================================================
 Research Session Complete!
================================================================================

Session ID: research_research-assistant-what-are-the-latest-de

CONTEXT FROM PAST RESEARCH
--------------------------------------------------------------------------------
Related Past Sessions: 2
  1. AI code generation trends (12 sources)
  2. IDE evolution analysis (8 sources)
Existing Sources in DB: 45
Known Topics: AI, code generation, IDE, automation, productivity
Knowledge Gaps Identified: real-time collaboration, code quality metrics

SOURCES COLLECTED
--------------------------------------------------------------------------------
Web Sources: 8
  1. The Rise of AI-Powered Development Tools
     URL: https://example.com/ai-dev-tools
     Credibility: 0.85
     Topics: AI, development, automation

Academic Sources: 7
  1. Large Language Models for Code Generation: A Survey
     DOI: 10.1234/example.5678
     Authors: Smith, J., Johnson, A.
     Credibility: 0.95

DATA ENRICHMENT
--------------------------------------------------------------------------------
Total Sources Collected: 15
Unique Sources (after dedup): 14
Cross-References Created: 23
Average Credibility Score: 0.87

KNOWLEDGE GRAPH
--------------------------------------------------------------------------------
Entities Identified: 12
Entity types: Concepts, People, Organizations, Events
Relationships: Related-to, Contradicts, Supports, Cites

RESEARCH SYNTHESIS
--------------------------------------------------------------------------------
Title: AI-Powered Code Generation: State of the Art and Comparative Analysis

Executive Summary:
Recent developments in AI-powered code generation have transformed software
development workflows. This research examines 14 high-quality sources...

Main Findings (5):
  1. AI assistants improve developer productivity by 30-50%
     Confidence: 0.92
     Sources: 5 source(s)

Conflicting Viewpoints (1):
  1. Code quality vs speed trade-offs
     - View A: Quality maintained
     - View B: Requires more review

Knowledge Gaps Identified:
  - Long-term code maintainability impact
  - Enterprise security implications

Overall Confidence Level: 87.00%
Based on 14 sources

AUDIO REPORT
--------------------------------------------------------------------------------
Duration: 245.3 seconds (4.1 minutes)
Chapters (6):
  00:00 - Introduction
  00:10 - Executive Summary
  00:30 - Main Findings
  02:27 - Conflicting Viewpoints
  03:16 - Knowledge Gaps
  03:40 - Conclusion
```

## Key Concepts Demonstrated

### 1. AI Agents with MCP Tools

Each agent uses MCP servers for specialized capabilities:
- Tavily for web search
- Academia for paper search
- Mem0 for memory/context
- ElevenLabs for audio generation

### 2. MongoDB Integration

Persistent knowledge base that:
- Grows over time
- Enables context-aware research
- Supports knowledge graph construction
- Provides audit trail

### 3. Parallel Agent Execution

Web and academic research run concurrently:

```python
web_future = workflow.execute_activity(research_web_sources, ...)
academic_future = workflow.execute_activity(research_academic_sources, ...)
web_sources, academic_sources = await workflow.wait_all([web_future, academic_future])
```

### 4. Knowledge Graph Construction

Automatically builds entity-relationship graphs showing:
- Key concepts and their relationships
- People and organizations involved
- Supporting vs conflicting evidence
- Confidence scores

### 5. Contextual Awareness

Each new research session:
- Queries past research
- Identifies knowledge gaps
- Avoids duplicating existing work
- Builds on previous findings

## Customization

### Add More MCP Tools

Configure additional MCP servers in workflow:

```python
from agents.mcp import MCPServer
from temporalio.contrib import openai_agents

server = openai_agents.workflow.stateless_mcp_server("TavilyServer")
agent = Agent(
    name="Web Research Agent",
    mcp_servers=[server],
    ...
)
```

### Customize MongoDB Schema

Modify collections in `activities/__init__.py`:

```python
db.custom_collection.create_index([("custom_field", ASCENDING)])
```

### Adjust Agent Behavior

Edit agent instructions in `activities/agent_activities.py`:

```python
agent = Agent(
    name="Custom Agent",
    model="gpt-4o",
    instructions="Your custom instructions...",
)
```

## Monitoring

### MongoDB

View stored data:
```bash
mongosh
use research_assistant
db.research_sources.find().limit(5)
db.knowledge_graph.find()
db.research_sessions.find().sort({timestamp: -1})
```

### Temporal Web UI

- Navigate to `http://localhost:8233`
- View workflow execution timeline
- Inspect activity inputs/outputs
- Monitor agent interactions

## Next Steps

- See **Project 3** for multi-agent teams with supervision
- See **Project 4** for combining all patterns
