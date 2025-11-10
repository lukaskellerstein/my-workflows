"""
Example 1: Simple LLM Call in Workflow
This demonstrates calling an LLM (Large Language Model) as part of a workflow activity.
Uses OpenAI's API to generate text completions.

Requirements:
    pip install openai
    export OPENAI_API_KEY="your-api-key"
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta

from openai import AsyncOpenAI
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present


@dataclass
class TextAnalysisRequest:
    text: str
    task: str  # "summarize", "sentiment", "keywords", "translate"


@dataclass
class TextAnalysisResult:
    original_text: str
    task: str
    result: str
    model: str


# Activity that calls the LLM
@activity.defn
async def analyze_text_with_llm(request: TextAnalysisRequest) -> TextAnalysisResult:
    """
    Analyze text using an LLM.
    This is a workflow activity that makes an external LLM API call.
    """
    activity.logger.info(f"Analyzing text with task: {request.task}")

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        activity.logger.warning("OPENAI_API_KEY not set, using mock response")
        # Return mock response for demo
        return TextAnalysisResult(
            original_text=request.text,
            task=request.task,
            result=f"[MOCK] This is a simulated {request.task} result",
            model="mock-model",
        )

    client = AsyncOpenAI(api_key=api_key)

    # Create prompt based on task
    prompts = {
        "summarize": f"Summarize the following text in 2-3 sentences:\n\n{request.text}",
        "sentiment": f"Analyze the sentiment (positive/negative/neutral) of this text and explain why:\n\n{request.text}",
        "keywords": f"Extract 5-7 key topics or keywords from this text:\n\n{request.text}",
        "translate": f"Translate the following text to Spanish:\n\n{request.text}",
    }

    prompt = prompts.get(request.task, f"Analyze this text:\n\n{request.text}")

    # Call LLM API
    response = await client.chat.completions.create(
        model="gpt-5-mini",  # or "gpt-3.5-turbo" for cheaper option
        messages=[
            {"role": "system", "content": "You are a helpful text analysis assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    result_text = response.choices[0].message.content

    activity.logger.info(f"LLM analysis completed using {response.model}")

    return TextAnalysisResult(
        original_text=request.text,
        task=request.task,
        result=result_text,
        model=response.model,
    )


# Workflow that orchestrates text analysis
@workflow.defn
class TextAnalysisWorkflow:
    @workflow.run
    async def run(self, text: str) -> str:
        workflow.logger.info("Starting text analysis workflow")

        # Perform multiple analyses in parallel
        tasks = ["summarize", "sentiment", "keywords"]

        # Execute activities in parallel
        results = await asyncio.gather(
            *[
                workflow.execute_activity(
                    analyze_text_with_llm,
                    TextAnalysisRequest(text=text, task=task),
                    start_to_close_timeout=timedelta(seconds=30),
                )
                for task in tasks
            ]
        )

        # Format results
        output = f"Text Analysis Results\n{'=' * 50}\n\n"
        output += f"Original Text:\n{text}\n\n"

        for result in results:
            output += f"\n{result.task.upper()}:\n"
            output += f"{result.result}\n"
            output += f"(Model: {result.model})\n"
            output += "-" * 50 + "\n"

        workflow.logger.info("Text analysis workflow completed")
        return output


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="5-ai-simple-llm-task-queue",
        workflows=[TextAnalysisWorkflow],
        activities=[analyze_text_with_llm],
        activity_executor=ThreadPoolExecutor(5),
    ):
        # Sample text to analyze
        sample_text = """
        Artificial Intelligence is transforming how we work and live.
        Machine learning models can now understand and generate human language,
        recognize images, and make predictions based on data. This technology
        is being applied across industries from healthcare to finance,
        enabling new capabilities and improving efficiency. However, it also
        raises important questions about ethics, privacy, and the future of work.
        """

        # Execute the workflow
        result = await client.execute_workflow(
            TextAnalysisWorkflow.run,
            sample_text.strip(),
            id="5-ai-simple-llm-workflow",
            task_queue="5-ai-simple-llm-task-queue",
        )
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
