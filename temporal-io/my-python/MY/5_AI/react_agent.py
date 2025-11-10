"""
Example 3: ReAct (Reasoning + Acting) Agent as Workflow
This demonstrates implementing a complete ReAct agent pattern using Temporal workflows.
The agent iteratively:
1. Reasons about what to do next (Thought)
2. Decides on an action (Action)
3. Executes the action (Observation)
4. Repeats until the task is complete

ReAct Paper: https://arxiv.org/abs/2210.03629

Requirements:
    pip install openai
    export OPENAI_API_KEY="your-api-key"
"""

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import List, Dict, Any

from openai import AsyncOpenAI
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present


class ActionType(str, Enum):
    SEARCH_WEB = "search_web"
    CALCULATE = "calculate"
    GET_DATE = "get_date"
    FINISH = "finish"


@dataclass
class ReActStep:
    thought: str
    action: str  # Store as string instead of enum for better serialization
    action_input: str
    observation: str


@dataclass
class ReActResult:
    question: str
    steps: List[ReActStep]
    final_answer: str
    total_iterations: int


@dataclass
class LLMReasonInput:
    question: str
    previous_steps: List[Dict[str, str]]
    available_tools: List[str]


# Tool Activities


@activity.defn
async def search_web(query: str) -> str:
    """Simulate web search."""
    activity.logger.info(f"Searching web for: {query}")
    # Mock search results - in reality, would call a search API
    mock_results = {
        "python": "Python is a high-level programming language known for simplicity and readability. Created by Guido van Rossum in 1991.",
        "temporal": "Temporal is a durable execution platform that makes applications resilient to failures. It enables developers to write code as if failures don't happen.",
        "machine learning": "Machine Learning is a subset of AI that enables systems to learn from data. Common frameworks include TensorFlow, PyTorch, and scikit-learn.",
        "weather": "Weather APIs provide current conditions and forecasts. Popular services include OpenWeatherMap, WeatherAPI, and AccuWeather.",
    }

    # Simple keyword matching
    for key, value in mock_results.items():
        if key.lower() in query.lower():
            return value

    return (
        f"Search results for '{query}': Information about {query} and related topics."
    )


@activity.defn
async def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions."""
    activity.logger.info(f"Calculating: {expression}")
    try:
        # Simple safe evaluation (in production, use a proper math parser)
        result = eval(expression, {"__builtins__": {}}, {})
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


@activity.defn
async def get_current_date() -> str:
    """Get the current date."""
    activity.logger.info("Getting current date")
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d")


# LLM Activity for reasoning


@activity.defn
async def llm_reason(input_data: LLMReasonInput) -> Dict[str, str]:
    """
    Use LLM to reason about the next step.
    Returns: {"thought": "...", "action": "...", "action_input": "..."}
    """
    activity.logger.info("LLM reasoning about next step")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Mock response for demo
        if not input_data.previous_steps:
            return {
                "thought": "I need to search for information about the question",
                "action": "search_web",
                "action_input": input_data.question,
            }
        else:
            return {
                "thought": "I have enough information to answer",
                "action": "finish",
                "action_input": "Based on the information gathered, here is the answer.",
            }

    client = AsyncOpenAI(api_key=api_key)

    # Build context from previous steps
    context = "Previous steps:\n"
    for i, step in enumerate(input_data.previous_steps):
        context += f"Step {i+1}:\n"
        context += f"  Thought: {step['thought']}\n"
        context += f"  Action: {step['action']} with input: {step['action_input']}\n"
        context += f"  Observation: {step['observation']}\n\n"

    prompt = f"""You are a ReAct (Reasoning + Acting) agent. Answer the question by reasoning and taking actions.

Question: {input_data.question}

{context}

Available actions:
{', '.join(input_data.available_tools)}

Think about what to do next. Respond in this exact format:
Thought: [your reasoning about what to do next]
Action: [one of the available actions: {', '.join(input_data.available_tools)}]
Action Input: [the input for the action]

If you have enough information to answer the question, use:
Action: finish
Action Input: [your final answer]
"""

    response = await client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful ReAct agent that reasons step by step.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    text = response.choices[0].message.content

    # Parse response
    lines = text.strip().split("\n")
    thought = action = action_input = ""

    for line in lines:
        if line.startswith("Thought:"):
            thought = line.replace("Thought:", "").strip()
        elif line.startswith("Action:"):
            action = line.replace("Action:", "").strip()
        elif line.startswith("Action Input:"):
            action_input = line.replace("Action Input:", "").strip()

    return {
        "thought": thought or "Continuing to work on the problem",
        "action": action or "finish",
        "action_input": action_input or "Task completed",
    }


# ReAct Agent Workflow


@workflow.defn
class ReActAgentWorkflow:
    """
    A complete ReAct agent implemented as a Temporal workflow.
    The workflow loops through reasoning and acting until the task is complete.
    """

    @workflow.run
    async def run(self, question: str, max_iterations: int = 5) -> ReActResult:
        workflow.logger.info(f"ReAct agent started with question: {question}")

        available_tools = [
            ActionType.SEARCH_WEB.value,
            ActionType.CALCULATE.value,
            ActionType.GET_DATE.value,
            ActionType.FINISH.value,
        ]

        steps: List[ReActStep] = []
        previous_steps: List[Dict[str, str]] = []

        # ReAct loop
        for iteration in range(max_iterations):
            workflow.logger.info(f"ReAct iteration {iteration + 1}")

            # Step 1: Reason (Thought + Action decision)
            reasoning = await workflow.execute_activity(
                llm_reason,
                LLMReasonInput(
                    question=question,
                    previous_steps=previous_steps,
                    available_tools=available_tools,
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

            thought = reasoning["thought"]
            action = reasoning["action"]
            action_input = reasoning["action_input"]

            workflow.logger.info(f"Thought: {thought}")
            workflow.logger.info(f"Action: {action}({action_input})")

            # Step 2: Act (Execute action and observe)
            if action == ActionType.FINISH.value:
                # Agent decided it has the answer
                final_step = ReActStep(
                    thought=thought,
                    action=ActionType.FINISH.value,  # Convert to string
                    action_input=action_input,
                    observation="Task completed",
                )
                steps.append(final_step)

                return ReActResult(
                    question=question,
                    steps=steps,
                    final_answer=action_input,
                    total_iterations=iteration + 1,
                )

            # Execute the chosen action
            observation = ""
            if action == ActionType.SEARCH_WEB.value:
                observation = await workflow.execute_activity(
                    search_web,
                    action_input,
                    start_to_close_timeout=timedelta(seconds=10),
                )
            elif action == ActionType.CALCULATE.value:
                observation = await workflow.execute_activity(
                    calculate,
                    action_input,
                    start_to_close_timeout=timedelta(seconds=10),
                )
            elif action == ActionType.GET_DATE.value:
                observation = await workflow.execute_activity(
                    get_current_date,
                    start_to_close_timeout=timedelta(seconds=10),
                )
            else:
                observation = f"Unknown action: {action}"

            workflow.logger.info(f"Observation: {observation}")

            # Record step
            step = ReActStep(
                thought=thought,
                action=action,  # Store as string
                action_input=action_input,
                observation=observation,
            )
            steps.append(step)

            # Add to history for next iteration
            previous_steps.append(
                {
                    "thought": thought,
                    "action": action,
                    "action_input": action_input,
                    "observation": observation,
                }
            )

        # Max iterations reached
        return ReActResult(
            question=question,
            steps=steps,
            final_answer="Max iterations reached without completing the task",
            total_iterations=max_iterations,
        )


async def main():
    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="5-ai-react-agent-task-queue",
        workflows=[ReActAgentWorkflow],
        activities=[
            search_web,
            calculate,
            get_current_date,
            llm_reason,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        print("=== ReAct Agent Example ===\n")

        # Example 1: Simple question
        print("Example 1: Information Gathering")
        print("-" * 70)
        question1 = "What is Temporal and how does it help with building applications?"

        result1 = await client.execute_workflow(
            ReActAgentWorkflow.run,
            args=[question1, 5],
            id=f"5-ai-react-agent-example-1-{uuid.uuid4()}",
            task_queue="5-ai-react-agent-task-queue",
        )

        print(f"Question: {result1.question}\n")
        for i, step in enumerate(result1.steps):
            print(f"Step {i+1}:")
            print(f"  Thought: {step.thought}")
            print(f"  Action: {step.action}")  # Now it's already a string
            print(f"  Action Input: {step.action_input}")
            print(f"  Observation: {step.observation}")
            print()

        print(f"Final Answer: {result1.final_answer}")
        print(f"Total Iterations: {result1.total_iterations}")

        print("\n" + "=" * 70 + "\n")

        # Example 2: Calculation question
        print("Example 2: Multi-step Problem Solving")
        print("-" * 70)
        question2 = "If I have 15 apples and I buy 23 more, then give away 10, how many do I have?"

        result2 = await client.execute_workflow(
            ReActAgentWorkflow.run,
            args=[question2, 5],
            id=f"5-ai-react-agent-example-2-{uuid.uuid4()}",
            task_queue="5-ai-react-agent-task-queue",
        )

        print(f"Question: {result2.question}\n")
        for i, step in enumerate(result2.steps):
            print(f"Step {i+1}:")
            print(f"  Thought: {step.thought}")
            print(f"  Action: {step.action}")  # Now it's already a string
            print(f"  Action Input: {step.action_input}")
            print(f"  Observation: {step.observation}")
            print()

        print(f"Final Answer: {result2.final_answer}")
        print(f"Total Iterations: {result2.total_iterations}")


if __name__ == "__main__":
    asyncio.run(main())
