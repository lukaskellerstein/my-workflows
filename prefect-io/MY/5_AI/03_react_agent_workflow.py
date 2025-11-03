"""
Example: ReAct Agent as Prefect Workflow

Implements a complete ReAct (Reasoning + Acting) agent using Prefect workflows.
The agent uses a thought → action → observation loop to solve problems.

Requires: pip install openai
"""

import os
import json
from typing import List, Dict, Any
from prefect import flow, task, get_run_logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

# ========== Tool Definitions ==========

TOOLS = {
    "calculate": {
        "description": "Performs mathematical calculations. Input: expression (string)",
        "function": lambda expr: str(eval(expr)),
    },
    "search": {
        "description": "Searches for information. Input: query (string)",
        "function": lambda query: f"Search results for '{query}': Found relevant information about {query}.",
    },
    "get_current_date": {
        "description": "Gets the current date. No input required.",
        "function": lambda: "2024-01-15",
    },
    "lookup_fact": {
        "description": "Looks up a fact from knowledge base. Input: topic (string)",
        "function": lambda topic: {
            "python": "Python is a high-level programming language created by Guido van Rossum in 1991.",
            "prefect": "Prefect is a workflow orchestration platform for building data pipelines.",
            "ai": "Artificial Intelligence is the simulation of human intelligence by machines.",
        }.get(topic.lower(), f"No information found for {topic}"),
    },
}


# ========== ReAct Agent Tasks ==========


@task
def generate_thought(conversation_history: List[Dict], task_description: str) -> str:
    """
    Generates the agent's reasoning/thought step.
    """
    logger = get_run_logger()
    logger.info("Generating thought...")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build prompt for LLM
    tools_description = "\n".join(
        f"- {name}: {info['description']}" for name, info in TOOLS.items()
    )

    system_prompt = f"""You are a ReAct agent. Your task is to solve problems using this process:

1. THOUGHT: Reason about what you need to do next
2. ACTION: Choose a tool to use and provide input
3. OBSERVATION: See the result of the action
4. Repeat until you have the answer

Available tools:
{tools_description}

Respond in this exact format:
THOUGHT: <your reasoning>
ACTION: <tool_name>: <input>

Or if you have the final answer:
THOUGHT: <reasoning>
ANSWER: <final answer>

Current task: {task_description}
"""

    # Format conversation history
    messages = [{"role": "system", "content": system_prompt}]

    for entry in conversation_history:
        if entry["type"] == "thought":
            messages.append({"role": "assistant", "content": entry["content"]})
        elif entry["type"] == "observation":
            messages.append(
                {"role": "user", "content": f"OBSERVATION: {entry['content']}"}
            )

    # Get LLM response
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", messages=messages, temperature=0.7, max_tokens=200
    )

    thought = response.choices[0].message.content
    logger.info(f"Thought generated: {thought[:100]}...")

    return thought


@task
def parse_action(thought: str) -> Dict[str, Any]:
    """
    Parses the thought to extract action and input.
    """
    logger = get_run_logger()

    # Check if this is a final answer
    if "ANSWER:" in thought:
        answer = thought.split("ANSWER:", 1)[1].strip()
        logger.info("Final answer detected")
        return {"type": "answer", "content": answer}

    # Parse action
    if "ACTION:" in thought:
        action_part = thought.split("ACTION:", 1)[1].strip()

        # Format: "tool_name: input"
        if ":" in action_part:
            tool_name, tool_input = action_part.split(":", 1)
            tool_name = tool_name.strip()
            tool_input = tool_input.strip()

            if tool_name in TOOLS:
                logger.info(f"Action parsed: {tool_name}({tool_input})")
                return {"type": "action", "tool": tool_name, "input": tool_input}

    logger.warning("Could not parse action from thought")
    return {"type": "error", "content": "Could not parse action"}


@task
def execute_action(action: Dict[str, Any]) -> str:
    """
    Executes the action using the specified tool.
    """
    logger = get_run_logger()

    if action["type"] != "action":
        return "No action to execute"

    tool_name = action["tool"]
    tool_input = action["input"]

    logger.info(f"Executing {tool_name} with input: {tool_input}")

    try:
        tool_function = TOOLS[tool_name]["function"]

        # Handle tools that don't need input
        if tool_name == "get_current_date":
            result = tool_function()
        else:
            result = tool_function(tool_input)

        logger.info(f"Tool result: {result}")
        return str(result)

    except Exception as e:
        error_msg = f"Error executing {tool_name}: {str(e)}"
        logger.error(error_msg)
        return error_msg


# ========== ReAct Agent Flow ==========


@flow(name="ReAct Agent", log_prints=True)
def react_agent_flow(task_description: str, max_iterations: int = 10) -> Dict[str, Any]:
    """
    Implements a ReAct agent as a Prefect workflow.

    The agent follows the ReAct pattern:
    1. Think about what to do (THOUGHT)
    2. Take an action using a tool (ACTION)
    3. Observe the result (OBSERVATION)
    4. Repeat until task is complete
    """
    logger = get_run_logger()

    print(f"\n{'='*70}")
    print("ReAct AGENT WORKFLOW")
    print(f"{'='*70}")
    print(f"Task: {task_description}")
    print(f"{'='*70}\n")

    conversation_history = []
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---\n")

        # Step 1: Generate thought
        thought = generate_thought(conversation_history, task_description)
        print(f"💭 THOUGHT:\n{thought}\n")

        conversation_history.append({"type": "thought", "content": thought})

        # Step 2: Parse action from thought
        action = parse_action(thought)

        # Check if we have a final answer
        if action["type"] == "answer":
            print(f"✅ FINAL ANSWER:\n{action['content']}\n")
            print(f"{'='*70}")
            print(f"Agent completed in {iteration} iterations")
            print(f"{'='*70}")

            return {
                "status": "success",
                "answer": action["content"],
                "iterations": iteration,
                "history": conversation_history,
            }

        # Check for errors
        if action["type"] == "error":
            print(f"❌ ERROR: {action['content']}\n")
            # Try to continue
            conversation_history.append(
                {
                    "type": "observation",
                    "content": f"Error: {action['content']}. Please try again with a valid action.",
                }
            )
            continue

        # Step 3: Execute action
        print(f"🔧 ACTION: {action['tool']}({action['input']})")
        observation = execute_action(action)
        print(f"👁️  OBSERVATION: {observation}\n")

        conversation_history.append({"type": "observation", "content": observation})

    # Max iterations reached
    print(f"{'='*70}")
    print(f"⚠️  Max iterations ({max_iterations}) reached without answer")
    print(f"{'='*70}")

    return {
        "status": "incomplete",
        "iterations": iteration,
        "history": conversation_history,
    }


# ========== Multi-Step ReAct Examples ==========


@flow(name="ReAct Agent - Math Problem", log_prints=True)
def react_math_problem():
    """
    Solves a math problem using the ReAct agent.
    """
    task = (
        "Calculate (25 + 15) * 3, then add 50 to the result. What is the final answer?"
    )

    result = react_agent_flow(task, max_iterations=5)

    return result


@flow(name="ReAct Agent - Information Gathering", log_prints=True)
def react_information_gathering():
    """
    Gathers information and synthesizes an answer.
    """
    task = "Look up information about Python and Prefect, then explain how they work together."

    result = react_agent_flow(task, max_iterations=7)

    return result


@flow(name="ReAct Agent - Multi-Tool Task", log_prints=True)
def react_multi_tool_task():
    """
    Solves a task requiring multiple tools.
    """
    task = """
    First, get the current date. Then search for information about AI.
    Finally, calculate how many days are in 3 weeks.
    Provide a summary of all findings.
    """

    result = react_agent_flow(task, max_iterations=10)

    return result


# ========== Parallel ReAct Agents ==========


@flow(name="Parallel ReAct Agents", log_prints=True)
def parallel_react_agents():
    """
    Runs multiple ReAct agents in parallel on different tasks.
    """
    logger = get_run_logger()

    print(f"\n{'='*70}")
    print("PARALLEL ReAct AGENTS")
    print(f"{'='*70}\n")

    tasks = [
        "Calculate 15 * 8 + 100",
        "Look up information about AI",
        "Get the current date and explain what day of the week it is",
    ]

    print(f"Running {len(tasks)} agents in parallel...\n")

    # Run agents in parallel using map
    results = react_agent_flow.map(tasks, max_iterations=[5] * len(tasks))

    # Summary
    print(f"\n{'='*70}")
    print("PARALLEL EXECUTION SUMMARY")
    print(f"{'='*70}\n")

    for i, (task, result) in enumerate(zip(tasks, results), 1):
        status_emoji = "✅" if result["status"] == "success" else "⚠️"
        print(f"{status_emoji} Task {i}: {task[:50]}...")
        print(f"   Status: {result['status']}")
        print(f"   Iterations: {result['iterations']}")
        if result["status"] == "success":
            print(f"   Answer: {result['answer'][:100]}...")
        print()

    return results


# ========== Comprehensive Demo ==========


@flow(name="ReAct Agent Comprehensive Demo", log_prints=True)
def comprehensive_react_demo():
    """Runs all ReAct agent examples."""

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("=" * 70)
        print("⚠️  WARNING: OPENAI_API_KEY not set")
        print("=" * 70)
        print("\nTo run these examples, set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("=" * 70)
        return

    print("=" * 70)
    print("COMPREHENSIVE ReAct AGENT DEMONSTRATION")
    print("=" * 70)

    # Run examples
    print("\n\n" + "=" * 70)
    print("EXAMPLE 1: Math Problem")
    print("=" * 70)
    react_math_problem()

    print("\n\n" + "=" * 70)
    print("EXAMPLE 2: Information Gathering")
    print("=" * 70)
    react_information_gathering()

    print("\n\n" + "=" * 70)
    print("EXAMPLE 3: Multi-Tool Task")
    print("=" * 70)
    react_multi_tool_task()

    print("\n\n" + "=" * 70)
    print("EXAMPLE 4: Parallel Agents")
    print("=" * 70)
    parallel_react_agents()

    print("\n" + "=" * 70)
    print("All ReAct agent examples completed")
    print("=" * 70)


if __name__ == "__main__":
    comprehensive_react_demo()
