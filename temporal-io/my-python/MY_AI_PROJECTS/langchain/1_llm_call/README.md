# Project 1: Content Publishing Pipeline

A real-world workflow demonstrating integration of deterministic and LLM-powered activities in Temporal.io for automated content publishing.

## Overview

This workflow processes user-submitted articles through multiple stages:

1. **Input Validation** (Deterministic) - Validates article format, word count, and metadata
2. **Content Analysis** (LLM) - Analyzes tone, readability, topics, and sensitive content using Claude
3. **SEO Optimization** (LLM) - Generates SEO-friendly titles, descriptions, and keywords using Claude
4. **Image Processing** (Deterministic) - Processes and optimizes images
5. **Publication** (Deterministic) - Assembles and publishes the final article

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            Content Publishing Workflow                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ├──► 1. Validate Article (Deterministic)
                          │
                          ├──► 2. Analyze Content (LLM - Claude)
                          │
                          ├──► 3. Optimize SEO (LLM - Claude)
                          │
                          ├──► 4. Process Images (Deterministic)
                          │
                          └──► 5. Assemble & Publish (Deterministic)
```

## Running the Workflow

### Prerequisites

1. Temporal server running on `localhost:7233`
2. Anthropic API key in `.env` file

### Start the Worker

```bash
source .venv/bin/activate
cd 1_llm_call
python main.py worker
```

### Execute the Workflow

In another terminal:

```bash
source .venv/bin/activate
cd 1_llm_call
python main.py
```

## Key Features

- **Retry Logic**: LLM activities have exponential backoff retry policy
- **Error Handling**: Graceful fallbacks for LLM failures
- **Observability**: Comprehensive logging throughout the pipeline
- **Type Safety**: Full type hints using dataclasses

## Activity Breakdown

### Deterministic Activities

- `validate_article`: Checks format, word count, title, and metadata
- `process_images`: Extracts and optimizes images (simulated)
- `assemble_and_publish`: Combines all data and publishes to CMS

### LLM Activities

- `analyze_content`: Uses Claude to analyze tone, topics, and readability
- `optimize_seo`: Uses Claude to generate SEO metadata and recommendations

## Customization

Modify the sample article in `main.py` to test with different content types.

## Output

The workflow returns a `PublicationManifest` containing:
- Article ID
- Optimized title
- Publication URL
- SEO metadata
- Image processing results
- Publication timestamp
