# Project 1: Content Publishing Pipeline

This project demonstrates how to integrate LLM calls within Temporal workflows, combining deterministic activities with AI-powered content analysis and optimization.

## Workflow Overview

The Content Publishing Pipeline processes user-submitted articles through multiple stages:

```
┌─────────────────┐
│ Article Input   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ 1. Input Validation     │ ◄── Deterministic
│    - Format check       │
│    - Word count         │
│    - Metadata check     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 2. Content Analysis     │ ◄── LLM Call
│    - Tone analysis      │
│    - Readability score  │
│    - Topic extraction   │
│    - Summary generation │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 3. SEO Optimization     │ ◄── LLM Call
│    - Title alternatives │
│    - Meta descriptions  │
│    - Keyword suggestions│
│    - Internal links     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 4. Image Processing     │ ◄── Deterministic
│    - Extract images     │
│    - Optimize formats   │
│    - Generate variants  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ 5. Final Assembly       │ ◄── Deterministic
│    - Combine metadata   │
│    - Generate manifest  │
│    - Create pub URL     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ Publication     │
│ Manifest        │
└─────────────────┘
```

## Features

### Deterministic Activities
- **Input Validation**: Validates article format, word count, and required metadata
- **Image Processing**: Extracts and processes images from content
- **Final Assembly**: Combines all data into a publication manifest

### LLM-Powered Activities
- **Content Analysis**: Uses GPT-5-mini to analyze tone, readability, and extract topics
- **SEO Optimization**: Generates SEO-friendly titles, descriptions, and keywords

### Resilience Features
- Retry policies for LLM calls with exponential backoff
- Graceful degradation with default values if LLM parsing fails
- Workflow state persistence for resumption after failures

## Project Structure

```
1_llm_call/
├── models/
│   └── __init__.py           # Data models (ArticleInput, ValidationResult, etc.)
├── activities/
│   ├── __init__.py           # Deterministic activities
│   └── llm_activities.py     # LLM-powered activities
├── workflows/
│   └── __init__.py           # ContentPublishingWorkflow
├── run_worker.py             # Worker script
├── run_workflow.py           # Client script with sample data
└── README.md                 # This file
```

## Prerequisites

1. **Temporal Server**: Run locally with `temporal server start-dev`
2. **Environment Variables**: Copy `.env.example` to `.env` and set:
   ```
   OPENAI_API_KEY=your_key_here
   TEMPORAL_ADDRESS=localhost:7233
   ```
3. **Dependencies**: Install with `uv sync` from project root

## Running the Example

### Start Temporal Server

```bash
temporal server start-dev
```

### Start the Worker

In one terminal:

```bash
source .venv/bin/activate
python 1_llm_call/run_worker.py
```

You should see:
```
Starting Content Publishing Worker...
Connected to Temporal at localhost:7233
Task queue: content-publishing-task-queue

Waiting for workflow tasks...
```

### Execute the Workflow

In another terminal:

```bash
source .venv/bin/activate
python 1_llm_call/run_workflow.py
```

## Expected Output

The workflow execution will display:

```
================================================================================
Content Publishing Pipeline - Workflow Execution
================================================================================

Article: The Future of AI-Powered Development Tools
Author: Jane Developer
Format: markdown
Tags: AI, development, automation, productivity

Executing workflow...

================================================================================
Publication Complete!
================================================================================

Publication ID: pub_20251101_143022_The_Future_of_AI-Po
Publication URL: https://example.com/articles/pub_20251101_143022_The_Future_of_AI-Po

Metadata:
  Word Count: 387
  Tone: professional
  Readability: 72.5
  Topics: AI, development tools, productivity, automation, future trends

SEO Optimization:
  Meta Description: Discover how AI is revolutionizing software development...
  Keywords: AI, development tools, automation, productivity, coding assistants
  Alternative Titles:
    1. How AI-Powered Tools Are Transforming Software Development
    2. The Developer's Guide to AI Coding Assistants
    3. Future of Development: AI Tools Reshaping the Industry

Images Processed: 1
  - https://example.com/images/ai-development.jpg -> 3 variants

Published at: 2025-11-01T14:30:22.123456
================================================================================
```

## Key Concepts Demonstrated

### 1. Mixed Activity Types

The workflow combines:
- **Fast deterministic** activities (validation, assembly)
- **Slower LLM-powered** activities (analysis, SEO)

This shows how to architect workflows with varying execution characteristics.

### 2. Retry Policies

LLM activities use custom retry policies:

```python
llm_retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=10),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)
```

This handles transient API failures gracefully.

### 3. Structured Data Flow

Each activity returns well-defined data structures that flow through the workflow, ensuring type safety and clear contracts between components.

### 4. Error Handling

The workflow includes:
- Early validation to fail fast on invalid inputs
- Try-catch in LLM activities for parsing errors
- Default fallback values when LLM responses are malformed

## Customization

### Using Different Models

Edit `activities/llm_activities.py` to change the model:

```python
agent = Agent(
    name="Content Analyzer",
    model="gpt-4o",  # Change model here
    instructions="...",
)
```

### Adding More Activities

Add new activities to the workflow by:

1. Define activity in `activities/` or `activities/llm_activities.py`
2. Import in `workflows/__init__.py`
3. Call with `workflow.execute_activity()`

### Custom Article Content

Modify `run_workflow.py` to test with your own content:

```python
article = ArticleInput(
    title="Your Title",
    author="Your Name",
    format="markdown",
    tags=["tag1", "tag2"],
    content="Your article content...",
)
```

## Monitoring

View workflow execution in Temporal Web UI:
- Navigate to `http://localhost:8233`
- Find your workflow by ID or search
- Inspect activity execution, retries, and results

## Next Steps

- See **Project 2** for using full AI agents with MCP tools
- See **Project 3** for multi-agent teams with supervision
- See **Project 4** for combining all patterns
