"""
Example 2: AI Agent with Tools using OpenAI Agent SDK
This demonstrates using an AI agent that can call workflow activities as tools.
The agent can reason about which tools to use and orchestrate multiple tool calls.

Requirements:
    pip install openai agents
    export OPENAI_API_KEY="your-api-key"
"""
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from agents import Agent, Runner
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.contrib import openai_agents as temporal_agents
from temporalio.worker import Worker
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file if present

api_key = os.getenv("OPENAI_API_KEY")

# Tool Activities - These will be available to the AI agent


@activity.defn
async def get_current_weather(city: str) -> str:
    """Get the current weather for a city."""
    activity.logger.info(f"Getting weather for {city}")
    # In real scenario: call weather API
    weather_data = {
        "Tokyo": {"temp": 18, "condition": "Partly Cloudy", "humidity": 65},
        "London": {"temp": 12, "condition": "Rainy", "humidity": 80},
        "New York": {"temp": 22, "condition": "Sunny", "humidity": 55},
        "Paris": {"temp": 15, "condition": "Overcast", "humidity": 70},
    }
    data = weather_data.get(city, {"temp": 20, "condition": "Clear", "humidity": 60})
    return f"Weather in {city}: {data['temp']}°C, {data['condition']}, Humidity: {data['humidity']}%"


@activity.defn
async def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for available flights."""
    activity.logger.info(f"Searching flights from {origin} to {destination} on {date}")
    # In real scenario: call flight search API
    return f"Found 3 flights from {origin} to {destination} on {date}: Flight AA101 ($450), Flight BA202 ($520), Flight UA303 ($480)"


@activity.defn
async def get_hotel_recommendations(city: str, budget: str) -> str:
    """Get hotel recommendations for a city."""
    activity.logger.info(f"Getting hotel recommendations for {city} with budget: {budget}")
    # In real scenario: call hotel API
    if budget.lower() == "low":
        return f"Budget hotels in {city}: City Inn ($80/night), Comfort Lodge ($95/night)"
    elif budget.lower() == "medium":
        return f"Mid-range hotels in {city}: Grand Plaza ($150/night), Royal Hotel ($180/night)"
    else:
        return f"Luxury hotels in {city}: The Ritz ($400/night), Palace Hotel ($500/night)"


@activity.defn
async def calculate_total_cost(flight_price: float, hotel_price: float, nights: int) -> str:
    """Calculate total trip cost."""
    activity.logger.info(f"Calculating total cost")
    total = flight_price + (hotel_price * nights)
    return f"Total trip cost: ${total:.2f} (Flight: ${flight_price}, Hotel: ${hotel_price}/night × {nights} nights)"


@activity.defn
async def get_travel_advisories(destination: str) -> str:
    """Get travel advisories for a destination."""
    activity.logger.info(f"Getting travel advisories for {destination}")
    # In real scenario: call government travel API
    advisories = {
        "Tokyo": "No travel restrictions. Safe for travel.",
        "London": "No travel restrictions. Check visa requirements.",
        "Paris": "Occasional strikes may affect transportation.",
    }
    return advisories.get(destination, "No specific advisories. Check official sources before travel.")


# AI Agent Workflow


@workflow.defn
class TravelPlannerAgentWorkflow:
    """
    AI Agent that helps plan trips using multiple tools.
    The agent can:
    - Check weather
    - Search flights
    - Recommend hotels
    - Calculate costs
    - Provide travel advisories
    """

    @workflow.run
    async def run(self, user_request: str) -> str:
        workflow.logger.info(f"Travel planner agent started with request: {user_request}")

        if not api_key:
            return (
                "ERROR: OPENAI_API_KEY environment variable not set.\n"
                "Please set it to use this example:\n"
                "export OPENAI_API_KEY='your-api-key-here'"
            )

        # Create an AI agent with access to workflow activities as tools
        agent = Agent(
            name="Travel Planner",
            instructions="""You are a helpful travel planning assistant.
            You help users plan their trips by:
            1. Checking weather at destinations
            2. Finding flights
            3. Recommending hotels based on budget
            4. Calculating total costs
            5. Providing travel advisories

            Always be thorough and provide all relevant information.
            When calculating costs, extract prices from the flight and hotel data you receive.""",
            tools=[
                # Convert Temporal activities to agent tools
                temporal_agents.workflow.activity_as_tool(
                    get_current_weather,
                    start_to_close_timeout=timedelta(seconds=10)
                ),
                temporal_agents.workflow.activity_as_tool(
                    search_flights,
                    start_to_close_timeout=timedelta(seconds=10)
                ),
                temporal_agents.workflow.activity_as_tool(
                    get_hotel_recommendations,
                    start_to_close_timeout=timedelta(seconds=10)
                ),
                temporal_agents.workflow.activity_as_tool(
                    calculate_total_cost,
                    start_to_close_timeout=timedelta(seconds=10)
                ),
                temporal_agents.workflow.activity_as_tool(
                    get_travel_advisories,
                    start_to_close_timeout=timedelta(seconds=10)
                ),
            ],
        )

        # Run the agent
        result = await Runner.run(agent, input=user_request)

        workflow.logger.info("Travel planner agent completed")
        return result.final_output


async def main():
    # Start client
    client = await Client.connect(
        "localhost:7233",
        plugins=[
            temporal_agents.OpenAIAgentsPlugin(),
        ],
    )

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue="5-ai-agent-with-tools-task-queue",
        workflows=[TravelPlannerAgentWorkflow],
        activities=[
            get_current_weather,
            search_flights,
            get_hotel_recommendations,
            calculate_total_cost,
            get_travel_advisories,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        print("=== Travel Planning AI Agent ===\n")

        # Example 1: Simple weather query
        print("Example 1: Weather Query")
        print("-" * 50)
        result1 = await client.execute_workflow(
            TravelPlannerAgentWorkflow.run,
            "What's the weather like in Tokyo?",
            id="5-ai-agent-weather-query",
            task_queue="5-ai-agent-with-tools-task-queue",
        )
        print(f"Agent: {result1}\n")

        # Example 2: Complex trip planning
        print("\nExample 2: Complete Trip Planning")
        print("-" * 50)
        result2 = await client.execute_workflow(
            TravelPlannerAgentWorkflow.run,
            "I want to plan a 5-night trip from New York to Tokyo in July. "
            "I have a medium budget. Can you help me find flights, hotels, "
            "check the weather, and calculate total costs?",
            id="5-ai-agent-trip-planning",
            task_queue="5-ai-agent-with-tools-task-queue",
        )
        print(f"Agent: {result2}\n")

        # Example 3: Travel advisory
        print("\nExample 3: Travel Advisory")
        print("-" * 50)
        result3 = await client.execute_workflow(
            TravelPlannerAgentWorkflow.run,
            "Are there any travel advisories for Paris?",
            id="5-ai-agent-advisory",
            task_queue="5-ai-agent-with-tools-task-queue",
        )
        print(f"Agent: {result3}\n")


if __name__ == "__main__":
    asyncio.run(main())
