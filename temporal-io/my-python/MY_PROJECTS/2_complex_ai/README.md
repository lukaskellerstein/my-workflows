# Complex AI Workflows

Three real-world complex workflows powered by Temporal, OpenAI Agents SDK, and Slack integration.

## Overview

This project demonstrates advanced Temporal workflows with:
- **LLM calls** using OpenAI Agents SDK
- **AI agents with tools** for autonomous task execution
- **Human-in-the-loop** via Slack for approvals and clarifications
- **React UI** for chat-based workflow interaction
- **Real-time status updates** showing workflow activities

## Workflows

### 0. Orchestrator Workflow (`workflow_orchestrator`) ⭐ NEW

**Purpose**: Intelligent routing system that automatically classifies user messages and routes to the best workflow

**Features**:
- LLM-based intent classification with **structured outputs** (Pydantic models)
- Type-safe automatic parameter extraction
- Routes to appropriate sub-workflow or handles directly
- Real-time routing decision display in UI
- Handles simple questions without complex workflows
- Guaranteed valid output format - no parsing errors

**Workflow Types Supported**:
- **Deep Research**: Research questions and investigations
- **Code Analysis**: Code review and security audits
- **Content Generation**: Blog posts, docs, articles
- **Direct LLM**: Simple questions, jokes, greetings

**API Endpoint**: `POST /orchestrator/start`

**Example**:
```json
{
  "message": "Research quantum computing trends",
  "user_id": "user123"
}
```

**UI Experience**:
- Select "Smart Routing (Recommended)" from dropdown
- Type any message
- See which workflow was selected and why
- View confidence score and reasoning
- Watch real-time processing state

**See Documentation**:
- [ORCHESTRATOR.md](./ORCHESTRATOR.md) - Detailed orchestrator documentation
- [STRUCTURED_OUTPUTS.md](./STRUCTURED_OUTPUTS.md) - How structured outputs improve reliability

### 1. Deep Research Workflow (`workflow_deep_research`)

**Purpose**: Conducts comprehensive research on a topic with clarifying questions

**Features**:
- Asks 2-3 clarifying questions via Slack to narrow scope
- Performs 15-minute deep research using AI agents
- Uses web search and content analysis tools
- Provides comprehensive, well-sourced answer

**Use Cases**:
- Market research
- Technical investigation
- Competitive analysis
- Literature review

**API Endpoint**: `POST /research/start`

**Example**:
```json
{
  "task": "Research the latest trends in AI agent frameworks",
  "user_id": "user123"
}
```

### 2. Code Analysis Workflow (`workflow_code_analysis`)

**Purpose**: Analyzes codebase with AI agents and requests approval for changes

**Features**:
- Scans repository and identifies files
- Analyzes code for security, performance, or quality issues
- Runs security scans with AI
- Requests Slack approval before implementing recommendations

**Use Cases**:
- Security audits
- Code quality reviews
- Performance optimization
- Refactoring planning

**API Endpoint**: `POST /code-analysis/start`

**Example**:
```json
{
  "repository_path": "/path/to/repo",
  "analysis_type": "security",
  "user_id": "user123"
}
```

### 3. Content Generation Workflow (`workflow_content_generation`)

**Purpose**: Generates content with AI and iterates based on human review

**Features**:
- Creates content outline and performs SEO research
- Generates content using AI with specified tone and audience
- Checks readability and quality metrics
- Requests Slack review and revises based on feedback (up to 3 revisions)

**Use Cases**:
- Blog post creation
- Technical documentation
- Marketing content
- Educational materials

**API Endpoint**: `POST /content/start`

**Example**:
```json
{
  "topic": "Introduction to Temporal Workflows",
  "content_type": "blog",
  "target_audience": "developers",
  "tone": "professional",
  "length": "medium",
  "user_id": "user123"
}
```

## Architecture

```
┌─────────────┐
│  React UI   │  (Port 3000)
│ Chat Interface
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│ Global API  │  (Port 8010)
│  FastAPI    │
└──────┬──────┘
       │
       ├─── Start Workflows
       ├─── Query Status
       └─── Receive Slack Events
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  Temporal   │────▶│    Worker    │
│   Server    │     │ (All Workflows)
└─────────────┘     └──────────────┘
       │
       ▼
┌─────────────┐
│   Slack     │
│ #human-in-loop
└─────────────┘
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Temporal Server running locally
- Slack workspace with bot configured
- OpenAI API key

### 1. Install Python Dependencies

```bash
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_complex_ai

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv sync
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_VERIFICATION_TOKEN=your-verification-token

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. Install UI Dependencies

```bash
cd ui
npm install
```

### 4. Start Temporal Server

```bash
temporal server start-dev
```

### 5. Start Worker

```bash
# From project root
uv run python worker.py
```

### 6. Start Global API

```bash
# From project root
uv run python global_api/api.py
```

### 7. Start React UI

```bash
cd ui
npm run dev
```

## Usage

### Option 1: React UI with Smart Routing (Recommended)

1. Open http://localhost:3000
2. Select "Smart Routing (Recommended)" from dropdown (default)
3. Type any message - the system will automatically choose the best workflow:
   - "Research AI trends" → Deep Research
   - "Analyze /path/to/code" → Code Analysis
   - "Write a blog post about Docker" → Content Generation
   - "Tell me a joke" → Direct LLM response
4. Click Send
5. See which workflow was selected and why
6. Watch workflow status in real-time
7. Reply to Slack messages in #human-in-loop channel (for complex workflows)

### Option 2: React UI with Manual Selection

1. Open http://localhost:3000
2. Select specific workflow from dropdown
3. Type your message/task
4. Click Send
5. Watch workflow status in real-time
6. Reply to Slack messages in #human-in-loop channel

### Option 3: API with Smart Routing

**Start Orchestrator (Auto-routing)**:
```bash
curl -X POST http://localhost:8010/orchestrator/start \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Research the latest AI developments",
    "user_id": "user123"
  }'
```

**Get Routing Decision**:
```bash
curl http://localhost:8010/orchestrator/{workflow_id}/routing
```

### Option 4: API Direct to Specific Workflow

**Start Deep Research:**
```bash
curl -X POST http://localhost:8010/research/start \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Research quantum computing applications in cryptography",
    "user_id": "user123"
  }'
```

**Start Code Analysis:**
```bash
curl -X POST http://localhost:8010/code-analysis/start \
  -H "Content-Type: application/json" \
  -d '{
    "repository_path": "/home/user/my-project",
    "analysis_type": "security",
    "user_id": "user123"
  }'
```

**Start Content Generation:**
```bash
curl -X POST http://localhost:8010/content/start \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Microservices Best Practices",
    "content_type": "blog",
    "target_audience": "senior developers",
    "tone": "professional",
    "length": "long",
    "user_id": "user123"
  }'
```

**Check Status:**
```bash
curl http://localhost:8010/workflow/{workflow_id}/status
```

**Get Result:**
```bash
curl http://localhost:8010/workflow/{workflow_id}/result
```

## Slack Integration

### Setup Slack Bot

1. Create a Slack app at https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `chat:write`
   - `channels:history`
   - `channels:read`
3. Install app to workspace
4. Copy Bot User OAuth Token to `.env`
5. Create `#human-in-loop` channel
6. Invite bot to channel: `/invite @YourBotName`

### Event Subscriptions

1. Enable Event Subscriptions in Slack app
2. Set Request URL: `http://your-server:8010/slack/events`
3. Subscribe to bot events:
   - `message.channels`
4. Save changes

### Interacting with Workflows

**Deep Research** - Reply to clarifying questions:
```
Answer: I'm interested in practical applications for enterprises
```

**Code Analysis** - Approve or reject:
```
yes
```
or
```
no
```

**Content Generation** - Approve or request revision:
```
approve
```
or
```
revise: Please add more technical examples and code snippets
```

## Workflow Details

### Deep Research Workflow Flow

```
1. Receive research task
2. Generate clarifying questions (AI)
3. Post questions to Slack → Wait for answers
4. Perform web searches (AI agents with tools)
5. Analyze content (AI)
6. Generate comprehensive report (AI)
7. Post results to Slack
```

**Timeout**: 2 hours per clarifying question

### Code Analysis Workflow Flow

```
1. Receive repository path and analysis type
2. Scan repository files
3. Analyze code with AI agents
4. Run security scans (AI)
5. Post analysis summary to Slack → Wait for approval
6. Generate final report with recommendations
```

**Timeout**: 24 hours for approval

### Content Generation Workflow Flow

```
1. Receive content request
2. Generate outline (AI)
3. Perform SEO research
4. Generate content (AI with tools)
5. Check readability
6. Post to Slack for review → Wait for feedback
7. If revisions requested:
   - Revise content (AI)
   - Post again for review
   - Repeat up to 3 times
8. Finalize and return
```

**Timeout**: 48 hours per review cycle

## Project Structure

```
2_complex_ai/
├── workflow_orchestrator/         ⭐ NEW
│   └── workflow_definitions.py    # Orchestrator workflow + routing logic
├── workflow_deep_research/
│   └── workflow_definitions.py    # Deep research workflow + activities
├── workflow_code_analysis/
│   └── workflow_definitions.py    # Code analysis workflow + activities
├── workflow_content_generation/
│   └── workflow_definitions.py    # Content generation workflow + activities
├── global_api/
│   └── api.py                     # Global FastAPI server (port 8010)
├── ui/
│   ├── src/
│   │   ├── App.tsx               # Main React app with Smart Routing
│   │   └── main.tsx              # Entry point
│   ├── package.json              # UI dependencies
│   └── vite.config.ts            # Vite config
├── worker.py                      # Global worker (all workflows)
├── pyproject.toml                # Python dependencies
├── .env.example                  # Environment variables template
├── README.md                     # This file
└── ORCHESTRATOR.md               # Orchestrator documentation
```

## Development

### Adding a New Workflow

1. Create `workflow_<name>/workflow_definitions.py`
2. Define workflow class with `@workflow.defn`
3. Add activities with `@activity.defn`
4. Import in `worker.py`
5. Import in `global_api/api.py`
6. Add endpoint in API
7. Add option in React UI dropdown

### Debugging

**View workflow execution**:
```bash
temporal workflow show --workflow-id <workflow-id>
```

**View workflow history**:
```bash
temporal workflow describe --workflow-id <workflow-id>
```

**Worker logs**:
Worker outputs detailed logs including activity execution and AI agent calls.

**API logs**:
API outputs Slack event processing and workflow start confirmations.

## Troubleshooting

**Slack not receiving messages**:
- Check `SLACK_BOT_TOKEN` in `.env`
- Verify bot is in `#human-in-loop` channel
- Check worker logs for errors

**AI agents not working**:
- Verify `OPENAI_API_KEY` in `.env`
- Check OpenAI API quota/limits
- Review worker logs for API errors

**Workflows not starting**:
- Ensure Temporal server is running
- Verify worker is running
- Check API logs for errors

**UI not connecting**:
- Verify API is running on port 8010
- Check CORS settings in API
- Open browser console for errors

## License

MIT
