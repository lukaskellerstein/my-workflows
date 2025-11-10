# Quick Start Guide

Get the Complex AI Workflows running in 5 minutes.

## Try these messages:

- "Tell me a joke"
- "Research quantum computing"
- "Analyze /tmp for security issues"
- "Write a blog post about Docker"

## Prerequisites Check

```bash
# Check Python version (need 3.12+)
python --version

# Check Node version (need 18+)
node --version

# Check Temporal Server
temporal server start-dev
```

## Setup (One-time)

```bash
# 1. Navigate to project
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_complex_ai

# 2. Python setup
uv venv
source .venv/bin/activate
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your keys

# 4. UI setup
cd ui
npm install
cd ..
```

## Run (Every time)

**Terminal 1 - Temporal Server:**

```bash
temporal server start-dev
```

**Terminal 2 - Worker:**

```bash
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_complex_ai
source .venv/bin/activate
uv run python worker.py
```

**Terminal 3 - API:**

```bash
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_complex_ai
source .venv/bin/activate
uv run python global_api/api.py
```

**Terminal 4 - UI:**

```bash
cd /home/lukas/Projects/Github/temporalio/MY_PROJECTS/2_complex_ai/ui
npm run dev
```

## Access

- **UI**: http://localhost:3000
- **API**: http://localhost:8010
- **Temporal Web**: http://localhost:8233

## Test It

1. Open UI at http://localhost:3000
2. Select "Deep Research" workflow
3. Type: "Research the benefits of temporal workflows"
4. Click Send
5. Watch for Slack message in #human-in-loop
6. Reply to Slack thread with your answer
7. See workflow complete in UI

## Environment Variables

Required in `.env`:

```bash
# Get from Slack: https://api.slack.com/apps
SLACK_BOT_TOKEN=xoxb-...

# Get from OpenAI: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...
```

## Troubleshooting

**"Module not found" errors:**

```bash
# Make sure you're in the venv
source .venv/bin/activate

# Reinstall dependencies
uv sync
```

**Slack not responding:**

- Check bot is in #human-in-loop channel
- Verify SLACK_BOT_TOKEN in .env
- Check worker logs for errors

**UI can't connect:**

- Verify API is running on port 8010
- Check `http://localhost:8010/health`

## Next Steps

See [README.md](README.md) for:

- Detailed workflow explanations
- API documentation
- Slack setup instructions
- Architecture details
