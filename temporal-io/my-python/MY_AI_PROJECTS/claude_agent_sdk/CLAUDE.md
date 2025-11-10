# Claude Agent SDK + Temporal.io Integration Projects

## Overview

This document describes four progressive projects demonstrating the integration of Claude Agent SDK within temporal.io workflows. Each project builds upon the previous one, showcasing different aspects of AI integration in deterministic workflow orchestration.

## Technical Stack

- **Language**: Python
- **Package Manager**: uv
- **Workflow Engine**: temporal.io
- **AI Framework**: Claude Agent SDK
- **MCP Tools**: Tavily Search, E2B, Mem0, Academia, ElevenLabs, MongoDB

Claude Agent SDK Examples: `/home/lukas/Projects/Github/lukaskellerstein/ai/14_Claude_Agent_SDK/claude_agent_sdk`

---

## Project 1: Content Publishing Pipeline

**Folder**: `1_llm_call`

### Workflow Description

A content publishing workflow that processes user-submitted articles through multiple stages, combining deterministic validation with LLM-powered content enhancement.

#### Workflow Activities:

1. **Input Validation** (Deterministic)

   - Validate article format (markdown/HTML)
   - Check minimum/maximum word count
   - Verify required metadata fields
   - Return validation errors if any

2. **Content Analysis** (LLM Call)

   - Use Claude to analyze content tone and readability
   - Extract key topics and themes
   - Generate content summary
   - Identify potential sensitive topics

3. **SEO Optimization** (LLM Call)

   - Generate SEO-friendly title alternatives
   - Create meta descriptions
   - Suggest relevant keywords
   - Propose internal linking opportunities

4. **Image Processing** (Deterministic)

   - Resize and optimize images
   - Generate responsive image variants
   - Create WebP versions
   - Update image references in content

5. **Final Assembly** (Deterministic)
   - Combine optimized content with metadata
   - Generate publication manifest
   - Store in content management system
   - Return publication URL

### Implementation Requirements:

- Use temporal.io activities for each step
- Implement retry logic for LLM calls with exponential backoff
- Store intermediate results for workflow resumption
- Handle LLM rate limits gracefully

---

## Project 2: Research Assistant Workflow with Knowledge Base

**Folder**: `2_agents`

### Workflow Description

An automated research workflow that gathers, analyzes, and synthesizes information from multiple sources using AI agents equipped with MCP tools, with MongoDB serving as a persistent knowledge base for storing and retrieving research data.

#### Workflow Activities:

1. **Query Parsing & Context Retrieval** (Deterministic + MongoDB)

   - Parse research query
   - Extract key terms and constraints
   - Query MongoDB for related past research
   - Identify knowledge gaps to fill
   - Define search parameters based on existing data

2. **Web Research Agent** (AI Agent with Tavily + MongoDB)

   - Agent searches for relevant articles using Tavily
   - Analyzes search results and extracts key information
   - Stores structured findings in MongoDB:
     - Article metadata (title, URL, date, author)
     - Key facts and claims
     - Extracted quotes and statistics
     - Credibility score
   - Checks MongoDB to avoid duplicate research
   - Tags content with topics for future retrieval

3. **Academic Research Agent** (AI Agent with Academia MCP + MongoDB)

   - Searches for peer-reviewed papers
   - Downloads and analyzes abstracts
   - Stores in MongoDB:
     - Paper metadata (DOI, authors, journal)
     - Key findings and methodologies
     - Citations and references
     - Research impact metrics
   - Links papers to related web articles in database
   - Creates citation network in MongoDB

4. **Data Processing & Enrichment** (Deterministic + MongoDB)

   - Query MongoDB for all collected data
   - Deduplicate findings across sources
   - Create cross-references between web and academic sources
   - Calculate source reliability scores
   - Update MongoDB with enriched metadata
   - Generate statistics on source distribution

5. **Knowledge Graph Builder** (AI Agent with MongoDB)

   - Analyzes all stored research data
   - Identifies entities, relationships, and concepts
   - Creates knowledge graph in MongoDB:
     - Nodes: concepts, people, organizations, events
     - Edges: relationships, citations, contradictions
   - Detects conflicting information between sources
   - Stores confidence scores for each relationship

6. **Synthesis Agent** (AI Agent with Mem0 + MongoDB)

   - Queries MongoDB for all relevant research data
   - Retrieves knowledge graph for context
   - Uses Mem0 to recall related past research sessions
   - Generates comprehensive research report with:
     - Main findings with source attribution
     - Conflicting viewpoints analysis
     - Knowledge gaps identified
     - Confidence levels for conclusions
   - Stores synthesis in MongoDB for future reference
   - Updates Mem0 with key insights

7. **Audio Report Generation** (AI Agent with ElevenLabs + MongoDB)
   - Retrieves final report from MongoDB
   - Converts report to natural speech
   - Creates audio podcast of findings
   - Stores audio metadata in MongoDB:
     - Audio file reference
     - Chapter markers with timestamps
     - Transcript alignment
   - Links audio to source documents

### MongoDB Collections Structure:

```javascript
// research_sources collection
{
  "_id": "source_id",
  "type": "web|academic",
  "title": "...",
  "url": "...",
  "doi": "...",
  "authors": [],
  "date_published": "...",
  "date_collected": "...",
  "credibility_score": 0.95,

  // Content fields - the actual text
  "content": "Full article or paper text...",
  "abstract": "Abstract for academic papers...",
  "summary": "AI-generated 2-3 sentence summary...",
  "raw_content": "Raw HTML or PDF text if needed...",

  // Extracted information
  "key_facts": [
    {
      "fact": "...",
      "confidence": 0.9,
      "supporting_text": "..."
    }
  ],
  "topics": ["AI", "machine learning"],
  "citations": ["source_id_2", "source_id_3"],
  "query_id": "research_session_id"
}

// knowledge_graph collection
{
  "_id": "node_id",
  "type": "concept|person|organization|event",
  "name": "...",
  "description": "...",
  "relationships": [
    {
      "target_id": "node_id_2",
      "relationship_type": "related_to|contradicts|supports",
      "confidence": 0.85,
      "source_ids": ["source_id_1", "source_id_2"]
    }
  ],
  "first_seen": "...",
  "last_updated": "..."
}

// research_sessions collection
{
  "_id": "session_id",
  "query": "original research query",
  "timestamp": "...",
  "sources_collected": 42,
  "synthesis_id": "synthesis_doc_id",
  "audio_report_id": "audio_id",
  "total_tokens_used": 15000,
  "duration_seconds": 180
}
```

### Implementation Requirements:

- Initialize MongoDB connection pool at workflow start
- Implement MongoDB transactions for multi-document updates
- Create indexes on frequently queried fields (topics, dates, credibility_score)
- Implement TTL indexes for temporary research data
- Use MongoDB aggregation pipelines for complex queries
- Implement versioning for evolving research over time
- Create backup strategy for research knowledge base
- Monitor MongoDB performance metrics
- Implement data retention policies

---

## Project 3: Code Review and Testing Pipeline

**Folder**: `3_multi-agents`

### Workflow Description

A sophisticated code review system using a team of specialized AI agents working together to analyze, test, and improve submitted code using a supervision pattern.

#### Workflow Activities:

1. **Code Intake** (Deterministic)

   - Receive code submission
   - Validate file formats
   - Extract language and framework metadata
   - Create review ticket

2. **Multi-Agent Code Review** (Team of AI Agents - Supervision Pattern)

   - **Supervisor Agent**: Coordinates the review team

     - Assigns tasks to specialist agents
     - Aggregates findings
     - Resolves conflicting recommendations

   - **Security Agent** (with E2B):

     - Scans for vulnerabilities
     - Tests for injection attacks
     - Validates authentication logic

   - **Performance Agent** (with E2B):

     - Analyzes algorithmic complexity
     - Runs performance benchmarks
     - Suggests optimizations

   - **Style Agent** (with Academia MCP):

     - Checks coding standards
     - Reviews documentation
     - Validates naming conventions

   - **Test Agent** (with E2B):
     - Writes unit tests
     - Creates integration tests
     - Generates test coverage reports

3. **Test Execution** (Deterministic)

   - Run generated test suites
   - Execute performance benchmarks
   - Generate coverage reports
   - Compile results matrix

4. **Report Generation** (AI Agent with Mem0)

   - Synthesizes all agent findings
   - Recalls similar past reviews
   - Generates actionable recommendations
   - Creates priority-ranked issue list

5. **Notification** (Deterministic)
   - Format review report
   - Send notifications to stakeholders
   - Update project management tools
   - Archive review artifacts

### Implementation Requirements:

- Implement supervisor-worker communication protocol
- Use temporal child workflows for agent teams
- Implement consensus mechanisms for conflicting opinions
- Store all agent deliberations for audit trail

---

## Project 4: Product Launch Automation System

**Folder**: `4_all`

### Workflow Description

A comprehensive product launch workflow that orchestrates market research, content creation, technical deployment, and customer engagement using a sophisticated combination of LLM calls, individual agents, and multi-agent teams.

#### Workflow Activities:

1. **Launch Planning** (Deterministic)

   - Parse product specifications
   - Define launch timeline
   - Allocate resources
   - Create workflow blueprint

2. **Market Research** (Team of AI Agents - Swarm Pattern)

   - **Competitor Analysis Swarm**:
     - Multiple agents use Tavily to research competitors
     - Agents share findings in real-time
     - Emergent insights from collective analysis
   - **Customer Sentiment Swarm**:
     - Agents analyze social media and reviews
     - Identify market gaps and opportunities
     - Predict customer reception

3. **Content Generation Pipeline** (LLM Calls)

   - Generate product descriptions for different audiences
   - Create marketing copy variations
   - Produce technical documentation
   - Generate FAQ content

4. **Technical Deployment** (AI Agent with E2B)

   - Agent creates deployment scripts
   - Sets up monitoring and alerts
   - Configures A/B testing parameters
   - Validates production readiness

5. **Media Asset Creation** (Multi-Agent Team - Supervision)

   - **Creative Director Agent**: Oversees asset creation
   - **Copy Agent**: Writes scripts and descriptions
   - **Voice Agent** (with ElevenLabs): Creates voice-overs
   - **Research Agent** (with Academia): Backs claims with research

6. **Campaign Orchestration** (Deterministic)

   - Schedule content publishing
   - Configure email campaigns
   - Set up analytics tracking
   - Initialize customer support resources

7. **Launch Monitoring** (AI Agent with Mem0)

   - Monitor launch metrics in real-time
   - Recall successful past launch patterns
   - Identify and flag anomalies
   - Generate hourly status reports

8. **Customer Engagement** (LLM Calls)

   - Generate personalized responses to inquiries
   - Create dynamic FAQ updates
   - Produce thank-you messages
   - Generate follow-up content

9. **Post-Launch Analysis** (Team of AI Agents)

   - **Analytics Agent**: Processes performance data
   - **Feedback Agent**: Analyzes customer feedback
   - **Improvement Agent**: Suggests optimizations
   - **Report Agent**: Creates executive summary

10. **Archive and Learn** (Deterministic + AI Agent with Mem0)
    - Store all launch artifacts
    - Agent extracts key learnings
    - Updates organizational memory
    - Generates best practices document

### Implementation Requirements:

- Implement complex workflow branching based on agent decisions
- Use temporal saga pattern for distributed transactions
- Implement circuit breakers for external service calls
- Create comprehensive observability with OpenTelemetry
- Use temporal versioning for workflow updates
- Implement graceful degradation when AI services are unavailable
- Store complete audit trail of all AI decisions
- Implement cost tracking for AI service usage

### Advanced Features:

- **Dynamic Workflow Composition**: Workflow can add/remove activities based on AI recommendations
- **Intelligent Retry Logic**: AI agents determine optimal retry strategies
- **Cross-Activity Learning**: Agents in later activities can query outcomes from earlier ones
- **Human-in-the-Loop**: Critical decisions require human approval via temporal signals
- **Progressive Enhancement**: Workflow continues with deterministic fallbacks if AI fails

---

## Common Implementation Guidelines

### Error Handling

- Implement exponential backoff for AI service calls
- Use circuit breakers to prevent cascade failures
- Log all AI interactions for debugging
- Implement fallback strategies for each AI-powered activity

### Monitoring and Observability

- Track token usage and costs per activity
- Monitor AI response times and quality scores
- Create dashboards for workflow performance
- Implement alerting for anomalous AI behavior

### Testing Strategy

- Unit tests for deterministic activities
- Mock AI responses for integration tests
- Implement replay testing using temporal's replay capability
- Create benchmark suites for AI agent performance

### Security Considerations

- Sanitize all inputs before sending to AI services
- Implement rate limiting per workflow instance
- Use secure storage for API keys
- Audit log all AI-generated decisions

### Development Workflow

1. Start with deterministic skeleton
2. Add LLM calls incrementally
3. Introduce single agents
4. Implement multi-agent coordination
5. Add monitoring and observability
6. Optimize for performance and cost

### Package Structure

```
project_folder/
├── workflows/
│   ├── __init__.py
│   └── main_workflow.py
├── activities/
│   ├── deterministic/
│   ├── llm_activities/
│   ├── agent_activities/
│   └── multi_agent_activities/
├── agents/
│   ├── base_agent.py
│   ├── specialized_agents/
│   └── agent_teams/
├── mcp_configs/
│   └── mcp_servers.json
├── tests/
│   ├── unit/
│   └── integration/
├── pyproject.toml
├── requirements.txt
└── README.md
```

# MCP list

## Tavily search

Tavily Search is an AI-powered search engine designed to deliver fast, accurate, and source-backed answers tailored for developers and AI applications.

```envVar
api_key=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
```

```json
{
  "mcpServers": {
      "tavily": {
        "transport": "streamable_http",
        "url": "https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"
    }
}
```

## E2B

The E2B MCP server allows you to add code interpreting capabilities to your Claude Desktop app via the E2B Sandbox.

```envVar
api_key=e2b_185bf1ec07e37cb14efcf2bb592e92feb9b3ea41
```

```json
{
  "mcpServers": {
    "e2b-mcp-server": {
      "command": "uvx",
      "args": ["e2b-mcp-server"],
      "env": { "E2B_API_KEY": "<api_key>" }
    }
  }
}
```

## Mem0

Mem0 is an open-source memory framework that enables AI agents to store, recall, and reason over past interactions to build long-term contextual awareness.

```envVar
api_key=om-9pasijokujjgzsw2mhwyourn1234zwbx
```

```json
{
  "mcpServers": {
      "tavily": {
        "command": "npx",
        "args": ["@openmemory/install", "--client", "claude"],
        "env": { "OPENMEMORY_API_KEY": "<api_key>" }
    }
}
```

## MongoDB

MongoDB is a document-oriented NoSQL database that stores data in flexible, JSON-like documents, allowing for scalable, schema-free data management.

```json
{
  "mcpServers": {
    "MongoDB": {
      "command": "npx",
      "args": ["-y", "mongodb-mcp-server@latest"],
      "env": {
        "MDB_MCP_CONNECTION_STRING": "mongodb://localhost:27017/myDatabase"
      }
    }
  }
}
```

## MinIO

MinIO is a high-performance, open-source object storage system compatible with the Amazon S3 API, designed for storing and managing unstructured data such as photos, videos, and backups at any scale.

```json
{
  "mcpServers": {
    "aistor": {
      "transport": "streamable_http",
      "url": "http://localhost:8090/mcp"
    }
  }
}
```

```json
{
  "mcpServers": {
    "aistor": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/home/lukas/Temp/Minio:/Downloads",
        "-e",
        "MINIO_ENDPOINT=http://localhost:9000",
        "-e",
        "MINIO_ACCESS_KEY=admin",
        "-e",
        "MINIO_SECRET_KEY=password123",
        "-e",
        "MINIO_USE_SSL=false",
        "quay.io/minio/aistor/mcp-server-aistor:latest",
        "--allowed-directories",
        "/Downloads",
        "--allow-write",
        "--allow-delete",
        "--allow-admin"
      ]
    }
  }
}
```

## Arxiv

MCP server with tools to search, fetch, analyze, and report on scientific papers and datasets.

https://github.com/blazickjp/arxiv-mcp-server

```json
{
  "mcpServers": {
    "arxiv": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "arxiv-mcp-server",
        "--storage-path",
        "/tmp/arxiv_papers"
      ]
    }
  }
}
```

## ElevenLabs

ElevenLabs is an AI-powered platform that creates highly realistic and expressive synthetic voices for text-to-speech and voice cloning applications.

```envVar
api_key=sk_2ccc539363f5f25c5201c40d356df73ce785f59c193dab75
```

```json
{
  "mcpServers": {
    "ElevenLabs": {
      "command": "uvx",
      "args": ["elevenlabs-mcp"],
      "env": {
        "ELEVENLABS_API_KEY": "<api_key>"
      }
    }
  }
}
```

# Documentation

Temporal source code: `/home/lukas/Projects/Github/temporalio/temporal`

Temporal samples: `/home/lukas/Projects/Github/temporalio/samples-python`

My Temporal Examples: `/home/lukas/Projects/Github/temporalio/MY`
