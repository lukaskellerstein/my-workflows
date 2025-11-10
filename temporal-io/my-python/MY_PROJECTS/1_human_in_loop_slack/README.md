# Slack Human in the Loop - Question & Answer

Posts questions to Slack channel `#human-in-loop`, waits for text answers in thread replies, and executes different workflow paths based on the answer.

## How It Works

1. **Workflow starts** � Question posted to Slack #human-in-loop
2. **User replies in thread** with any text
3. **Workflow receives answer** via Slack Events API
4. **Path execution**:
   - Answer is "yes" (case-insensitive) � Execute **Path YES** 
   - Answer is anything else � Execute **Path NO** L
5. **Workflow updates thread** with completion status

## Architecture

- **`workflow_definitions.py`** - Workflow with Slack integration and path logic
- **`worker.py`** - Temporal worker processing workflows
- **`start_workflow.py`** - CLI to start workflows and send test answers
- **`api.py`** - FastAPI with Slack Events API endpoint

## Prerequisites

1. Temporal server running on `localhost:7233`
2. Python dependencies installed
3. Slack App configured (see setup below)

## Slack App Setup

### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" � "From scratch"
3. Name: "Question Bot"
4. Select your workspace

### Step 2: Bot Permissions

Go to **OAuth & Permissions**, add these scopes:

- `chat:write` - Post messages
- `chat:write.public` - Post to public channels

Click **Install to Workspace** and copy the **Bot User OAuth Token** (starts with `xoxb-`)

### Step 3: Enable Events API

1. Go to **Event Subscriptions**
2. Toggle **Enable Events** to ON
3. Set **Request URL**: `https://your-domain.com/slack/events`
   - For local dev, use ngrok: `ngrok http 8005`
   - Use ngrok URL: `https://abc123.ngrok.io/slack/events`
4. Under **Subscribe to bot events**, add:
   - `message.channels` - Messages in public channels
5. **Save Changes**

### Step 4: Create Channel

1. Create Slack channel: `#human-in-loop`
2. Invite bot: `/invite @Question Bot`

### Step 5: Environment Setup

Create `.env` file:

```bash
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_VERIFICATION_TOKEN=your-verification-token
```

## Installation

```bash
cd MY_PROJECTS/1_human_in_loop_slack
uv add slack-sdk
```

## Usage

### 1. Start Worker

```bash
uv run python worker.py
```

### 2. Start API (Required for Slack Events)

```bash
uv run python api.py
```

Running on `http://localhost:8005`

**For local development with Slack:**

```bash
ngrok http 8005
```

Update Slack App Events URL with ngrok URL.

### 3. Start Workflows

#### Python CLI

**Start default workflow:**

```bash
uv run python start_workflow.py
```

**Start custom workflow:**

```bash
uv run python start_workflow.py start "Should we deploy?" "Tests passed"
```

**Send test answer (without Slack):**

```bash
uv run python start_workflow.py answer <workflow_id> yes
uv run python start_workflow.py answer <workflow_id> no thanks
```

**Check status:**

```bash
uv run python start_workflow.py status <workflow_id>
```

**Get result:**

```bash
uv run python start_workflow.py result <workflow_id>
```

#### REST API

**Start workflow:**

```bash
curl -X POST http://localhost:8005/question/start \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Should we proceed with deployment?",
    "context": "All tests passed. QA approved."
  }'
```

**Manual answer (testing):**

```bash
curl -X POST http://localhost:8005/question/{workflow_id}/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "yes", "user": "john"}'
```

## Configuration

- **Temporal Host**: `localhost:7233`
- **Task Queue**: `slack-question-task-queue`
- **API Port**: 8005
- **Slack Channel**: `human-in-loop`
- **Answer Timeout**: 2 hours
- **Yes Path**: Triggered only by "yes" (case-insensitive)
- **No Path**: Triggered by any other text or timeout

## Key Features

- Posts questions to Slack with rich formatting
- Waits for thread replies (not button clicks)
- Executes different paths based on answer
- Real-time updates via Slack Events API
- Mock mode for testing without Slack
- CLI and REST API interfaces

API Documentation: `http://localhost:8005/docs`
