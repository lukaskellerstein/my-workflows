# Quick Start Guide

Get up and running with Langchain + Temporal.io integration in 5 minutes.

## Step 1: Prerequisites

```bash
# 1. Start Temporal server
docker run -d -p 7233:7233 temporalio/auto-setup:latest

# 2. Start MongoDB (for Project 2)
docker run -d -p 27017:27017 mongo:latest

# 3. Verify services are running
docker ps
```

## Step 2: Setup Environment

```bash
# Navigate to project
cd /path/to/langchain

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv sync
```

## Step 3: Configure API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# Minimum required: ANTHROPIC_API_KEY
nano .env  # or use your preferred editor
```

Example `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxx...
TEMPORAL_HOST=localhost:7233
MONGODB_URI=mongodb://localhost:27017/
```

## Step 4: Run Project 1 (Content Publishing)

```bash
cd 1_llm_call

# Terminal 1: Start the worker
python main.py worker

# Terminal 2: Execute the workflow
python main.py
```

Expected output:
```
================================================================================
CONTENT PUBLISHING WORKFLOW COMPLETED
================================================================================

Article ID: a3b7c9d1e2f4
Title: The Future of AI in Content Creation
Publication URL: https://example.com/articles/a3b7c9d1e2f4
Published At: 2024-11-01T12:34:56
Status: published

SEO Metadata:
  Keywords: AI, content creation, technology, future, automation
  Topics: artificial intelligence, content creation, technology

Images: 0 processed
================================================================================
```

## Step 5: Run Project 2 (Research Assistant)

```bash
cd ../2_agents

# Terminal 1: Start the worker
python main.py worker

# Terminal 2: Execute the workflow
python main.py
```

Expected output:
```
================================================================================
RESEARCH ASSISTANT WORKFLOW COMPLETED
================================================================================

Session ID: f8e7d6c5b4a3
Query: What are the latest developments in large language models for code generation?

Query Context:
  Type: academic
  Key Terms: latest, developments, large, language, models

Sources Found: 4

Summary:
Recent developments in LLMs for code generation include improved context windows,
better code completion, and enhanced debugging capabilities...

Top Sources:
  1. Advances in Code Generation with LLMs
     URL: https://example.com/article1
     Credibility: 0.92
  2. LLM Code Completion Benchmarks
     URL: https://example.com/article2
     Credibility: 0.88
================================================================================
```

## Step 6: Explore Temporal UI

```bash
# Open browser to: http://localhost:8080
# (if using Temporal UI docker container)

# Or connect Temporal CLI
temporal workflow list
```

## Troubleshooting

### "Connection refused" to Temporal
```bash
# Check if Temporal is running
docker ps | grep temporal

# Restart Temporal
docker restart <container_id>
```

### "Connection refused" to MongoDB
```bash
# Check if MongoDB is running
docker ps | grep mongo

# Start MongoDB
docker run -d -p 27017:27017 mongo:latest
```

### "No module named 'temporalio'"
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
uv sync
```

### LLM API errors
```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Or check .env file
cat .env | grep ANTHROPIC_API_KEY
```

## Next Steps

1. ✅ Review Project 1 code in `1_llm_call/`
2. ✅ Review Project 2 code in `2_agents/`
3. 📖 Read main README.md for architecture details
4. 🔨 Implement Projects 3 and 4 (see respective READMEs)
5. 🧪 Write tests for your workflows
6. 📊 Add monitoring and observability

## Useful Commands

```bash
# Format code
black .

# Type check
mypy .

# Run tests
pytest

# Check Temporal worker logs
# (in worker terminal, observe output)

# View MongoDB data
docker exec -it <mongo_container> mongosh
> use langchain_temporal
> db.research_sources.find().pretty()
```

## Learn More

- **Temporal Concepts**: https://docs.temporal.io/concepts
- **Langchain Docs**: https://python.langchain.com/
- **Project Architecture**: See README.md
- **Sample Code**: Review `1_llm_call/` and `2_agents/`

---

**Ready to build robust AI workflows!** 🚀
