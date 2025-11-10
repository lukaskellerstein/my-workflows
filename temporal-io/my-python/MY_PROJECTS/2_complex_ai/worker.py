"""
Global Worker - Complex AI Workflows
Runs all workflows and activities for the complex AI system
"""

import asyncio
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from dotenv import load_dotenv
from temporalio.client import Client
from temporalio.contrib.openai_agents import ModelActivityParameters, OpenAIAgentsPlugin
from temporalio.worker import Worker

# Load environment variables
load_dotenv()

# Add workflow directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all workflows and activities
from workflow_code_analysis.workflow_definitions import (
    CodeAnalysisWorkflow,
    analyze_code_file,
    post_validation_request_to_slack as code_post_validation,
    run_security_scan,
    scan_repository,
    update_slack_thread as code_update_slack,
)
from workflow_content_generation.workflow_definitions import (
    ContentGenerationWorkflow,
    check_readability,
    generate_outline,
    perform_seo_research,
    post_validation_request_to_slack as content_post_validation,
    update_slack_thread as content_update_slack,
)
from workflow_deep_research.workflow_definitions import (
    DeepResearchWorkflow,
    analyze_content,
    perform_web_search,
    post_validation_request_to_slack as research_post_validation,
    update_slack_thread as research_update_slack,
)
from workflow_orchestrator.workflow_definitions import (
    OrchestratorWorkflow,
    classify_user_intent,
    handle_direct_llm_call,
)

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "complex-ai-task-queue"
MAX_CONCURRENT_ACTIVITIES = 20


async def main():
    """Start and run the global worker."""
    # Check required environment variables
    required_vars = ["SLACK_BOT_TOKEN", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("⚠️  WARNING: Missing environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nSome functionality may not work properly.")
        print("Please set these in your .env file.\n")

    # Connect to Temporal server with OpenAI Agents plugin
    client = await Client.connect(
        TEMPORAL_HOST,
        plugins=[
            OpenAIAgentsPlugin(
                model_params=ModelActivityParameters(
                    start_to_close_timeout=timedelta(seconds=60)
                )
            ),
        ],
    )
    print(f"✓ Connected to Temporal at {TEMPORAL_HOST}")
    print(f"✓ OpenAI Agents plugin enabled")

    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            OrchestratorWorkflow,
            DeepResearchWorkflow,
            CodeAnalysisWorkflow,
            ContentGenerationWorkflow,
        ],
        activities=[
            # Orchestrator activities
            classify_user_intent,
            handle_direct_llm_call,
            # Deep Research activities
            perform_web_search,
            analyze_content,
            research_post_validation,
            research_update_slack,
            # Code Analysis activities
            scan_repository,
            analyze_code_file,
            run_security_scan,
            code_post_validation,
            code_update_slack,
            # Content Generation activities
            generate_outline,
            perform_seo_research,
            check_readability,
            content_post_validation,
            content_update_slack,
        ],
        activity_executor=ThreadPoolExecutor(MAX_CONCURRENT_ACTIVITIES),
    )

    print(f"✓ Worker started on task queue: {TASK_QUEUE}")
    print(f"✓ Max concurrent activities: {MAX_CONCURRENT_ACTIVITIES}")
    print("\n" + "=" * 70)
    print("REGISTERED WORKFLOWS")
    print("=" * 70)
    print("  0. OrchestratorWorkflow (NEW)")
    print("     - Classifies user intent with LLM")
    print("     - Routes to appropriate sub-workflow or handles directly")
    print("     - Returns unified result with routing information")
    print()
    print("  1. DeepResearchWorkflow")
    print("     - User interacts via UI for clarifying questions")
    print("     - Performs 15-minute deep research with AI agents")
    print("     - Validates result via Slack before sending to user")
    print()
    print("  2. CodeAnalysisWorkflow")
    print("     - Scans repository and analyzes code with AI")
    print("     - Runs security/quality checks")
    print("     - Validates result via Slack before sending to user")
    print()
    print("  3. ContentGenerationWorkflow")
    print("     - Generates content with AI and SEO optimization")
    print("     - Checks readability and quality")
    print("     - Validates result via Slack before sending to user")
    print()
    print("=" * 70)
    print("SLACK USAGE")
    print("=" * 70)
    print("  Slack is used ONLY for final validation before sending")
    print("  results to the user. All user interaction happens via UI.")
    print()
    print("=" * 70)
    print("CONFIGURATION")
    print("=" * 70)
    print(f"  Temporal Host: {TEMPORAL_HOST}")
    print(f"  Task Queue: {TASK_QUEUE}")
    print(f"  Slack Configured: {bool(os.getenv('SLACK_BOT_TOKEN'))}")
    print(f"  OpenAI Configured: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"  Validation Channel: #human-in-loop")
    print("=" * 70)
    print("\n✓ Worker is running. Press Ctrl+C to stop.\n")

    # Run the worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
