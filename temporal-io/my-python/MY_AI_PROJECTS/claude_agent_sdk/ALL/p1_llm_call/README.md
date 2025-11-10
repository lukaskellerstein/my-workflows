# Project 1: Content Publishing Pipeline

A content publishing workflow that processes user-submitted articles through multiple stages, combining deterministic validation with LLM-powered content enhancement.

## Workflow Overview

This workflow demonstrates integration of LLM calls within Temporal activities:

```
┌─────────────────────────────────────────────────────────────────┐
│                  Content Publishing Workflow                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  1. Validate     │
                    │  Input           │ (Deterministic)
                    │  - Format check  │
                    │  - Word count    │
                    │  - Metadata      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  2. Analyze      │
                    │  Content         │ (LLM Call)
                    │  - Tone          │
                    │  - Readability   │
                    │  - Topics        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  3. Optimize     │
                    │  SEO             │ (LLM Call)
                    │  - Titles        │
                    │  - Keywords      │
                    │  - Meta tags     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  4. Process      │
                    │  Images          │ (Deterministic)
                    │  - Resize        │
                    │  - Convert       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  5. Assemble &   │
                    │  Publish         │ (Deterministic)
                    │  - Combine       │
                    │  - Publish       │
                    └──────────────────┘
```

## Features

- **Deterministic Validation**: Input validation with clear error reporting
- **LLM-Powered Analysis**: Content tone, readability, and topic extraction
- **SEO Optimization**: AI-generated titles, descriptions, and keywords
- **Image Processing**: Simulated image optimization pipeline
- **Retry Logic**: Exponential backoff for LLM calls
- **Type Safety**: Full Pydantic model validation

## Running the Project

### Prerequisites

1. Temporal server running (see main README)
2. Python environment with dependencies installed
3. Claude API key configured in `.env`

### Start the Worker

```bash
# From project root
uv run python -m 1_llm_call.worker
```

### Execute a Workflow

```bash
# From project root
uv run python -m 1_llm_call.starter
```

## Activities

### 1. `validate_article_input` (Deterministic)

Validates article format, word count, and metadata. Returns validation errors if any.

### 2. `analyze_content_with_llm` (LLM)

Uses Claude to analyze:
- Content tone (formal, casual, technical, etc.)
- Readability score (0.0-1.0)
- Key topics (3-5 main themes)
- Content summary
- Sensitive topics requiring careful handling

### 3. `optimize_for_seo` (LLM)

Generates SEO optimizations:
- 3 alternative title variations
- Meta description
- 5+ relevant keywords
- Internal linking suggestions

### 4. `process_images` (Deterministic)

Simulates image processing:
- Extract image URLs from content
- Generate resized versions
- Create WebP formats
- Build responsive variants

### 5. `assemble_and_publish` (Deterministic)

Final assembly:
- Combine all optimized components
- Generate publication manifest
- Create article ID
- Return publication URL

## Error Handling

- **Validation Failures**: Workflow stops with clear error message
- **LLM Failures**: Automatic retry with exponential backoff (3 attempts)
- **Timeouts**: Configured per activity type (30s-120s)
- **Graceful Degradation**: Falls back to safe defaults if LLM parsing fails

## Key Implementation Patterns

### Retry Policy for LLM Calls

```python
llm_retry_policy = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=30),
    backoff_coefficient=2.0,
    maximum_attempts=3,
)
```

### Activity Timeouts

- **Deterministic activities**: 30-60 seconds
- **LLM activities**: 120 seconds
- **Image processing**: 60 seconds

## Sample Output

```
Article ID: 7d3f91a8c2b4
Publication URL: https://example.com/articles/7d3f91a8c2b4
Optimized Title: AI-Powered Development Tools: The Future is Here
Keywords: AI, Development, Automation, Code Assistants, Productivity
Readability Score: 0.87
```

## Monitoring

View workflow execution in Temporal UI:
```
http://localhost:8233
```

Look for workflows in task queue: `content-publishing-queue`
