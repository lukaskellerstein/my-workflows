"""
Example: OpenAI Agent SDK in Workflow

Demonstrates using OpenAI's official Agent SDK within Prefect tasks.
Requires: pip install openai-agents
"""

import os
from prefect import flow, task, get_run_logger
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if present

# ========== Agent Tasks ==========


@task
def create_agent_with_tools() -> dict:
    """
    Creates an OpenAI agent with custom tools/functions.
    """
    logger = get_run_logger()
    logger.info("Creating OpenAI agent with tools")

    try:
        from agents import Agent, function_tool
    except ImportError:
        logger.error(
            "openai-agents not installed. Install with: pip install openai-agents"
        )
        return {"error": "openai-agents not installed"}

    # Define tools using @function_tool decorator
    @function_tool
    def get_weather(location: str) -> str:
        """Get the weather for a location.

        Args:
            location: The city name to get weather for
        """
        # In reality, this would call a weather API
        return f"The weather in {location} is sunny and 72°F."

    @function_tool
    def calculate(expression: str) -> str:
        """Calculate a mathematical expression.

        Args:
            expression: The mathematical expression to evaluate
        """
        try:
            result = eval(expression)
            return f"The result is {result}"
        except Exception as e:
            return f"Error calculating: {e}"

    @function_tool
    def search_database(query: str) -> str:
        """Search the database for information.

        Args:
            query: The search query (e.g., 'orders', 'customers', 'products')
        """
        # Simulate database search
        database = {
            "orders": "Found 5 recent orders totaling $1,234.56",
            "customers": "Found 142 active customers",
            "products": "Found 28 products in stock",
        }
        return database.get(query, f"No results found for: {query}")

    # Create agent with tools
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant with access to weather, calculator, and database tools.",
        tools=[get_weather, calculate, search_database],
    )

    return {"agent": agent, "tools": ["get_weather", "calculate", "search_database"]}


@task(retries=2, retry_delay_seconds=1)
def run_agent(agent_config: dict, user_message: str) -> dict:
    """
    Runs the OpenAI agent with a user message.
    """
    logger = get_run_logger()
    logger.info(f"Running agent with message: {user_message}")

    if "error" in agent_config:
        return agent_config

    try:
        from agents import Runner
    except ImportError:
        return {"error": "openai-agents not installed"}

    agent = agent_config["agent"]

    # Run agent synchronously
    result = Runner.run_sync(agent=agent, input=user_message)

    response = {
        "user_message": user_message,
        "response": result.final_output,
        "messages": len(result.messages) if hasattr(result, "messages") else 0,
    }

    logger.info(f"Agent completed")
    return response


@task
def create_multi_agent_system() -> dict:
    """
    Creates a multi-agent system with specialized agents using handoffs.
    """
    logger = get_run_logger()
    logger.info("Creating multi-agent system")

    try:
        from agents import Agent, function_tool
    except ImportError:
        return {"error": "openai-agents not installed"}

    # Define tools for specialized agents

    # Sales agent tools
    @function_tool
    def get_product_info(product: str) -> str:
        """Get information about a product.

        Args:
            product: The product name (widget, gadget, or device)
        """
        products = {
            "widget": "The Widget Pro costs $99 and has 5-star reviews.",
            "gadget": "The Gadget Plus costs $149 and includes free shipping.",
            "device": "The Smart Device costs $299 and comes with a 2-year warranty.",
        }
        return products.get(product.lower(), "Product not found.")

    # Support agent tools
    @function_tool
    def check_order_status(order_id: str) -> str:
        """Check the status of an order.

        Args:
            order_id: The order ID to check
        """
        return f"Order {order_id} is currently in transit and will arrive in 2 days."

    @function_tool
    def create_return(order_id: str) -> str:
        """Create a return for an order.

        Args:
            order_id: The order ID to return
        """
        return f"Return created for order {order_id}. You will receive a refund in 5-7 business days."

    # Create specialized agents
    sales_agent = Agent(
        name="Sales Agent",
        instructions="You are a sales agent. Help customers find and purchase products. Use get_product_info to look up product details.",
        tools=[get_product_info],
    )

    support_agent = Agent(
        name="Support Agent",
        instructions="You are a support agent. Help customers with orders, returns, and issues. Use check_order_status and create_return tools.",
        tools=[check_order_status, create_return],
    )

    # Create triage agent with handoff capabilities
    triage_agent = Agent(
        name="Triage Agent",
        instructions="""You are a triage agent. Determine if the customer needs sales or support.
        - For product questions, pricing, or purchasing -> handoff to Sales Agent
        - For order status, returns, or issues -> handoff to Support Agent

        Use handoffs to transfer the customer to the appropriate agent.""",
        handoffs=[sales_agent, support_agent],  # Enable handoffs to these agents
    )

    return {
        "triage_agent": triage_agent,
        "sales_agent": sales_agent,
        "support_agent": support_agent,
        "agents": ["triage", "sales", "support"],
    }


@task
def run_multi_agent(agent_system: dict, user_message: str) -> dict:
    """
    Runs the multi-agent system with automatic routing via handoffs.
    """
    logger = get_run_logger()
    logger.info(f"Running multi-agent system with message: {user_message}")

    if "error" in agent_system:
        return agent_system

    try:
        from agents import Runner
    except ImportError:
        return {"error": "openai-agents not installed"}

    triage_agent = agent_system["triage_agent"]

    # Run with triage agent (will handoff to appropriate agent)
    result = Runner.run_sync(agent=triage_agent, input=user_message)

    response = {
        "user_message": user_message,
        "response": result.final_output,
        "final_agent": (
            result.agent.name if hasattr(result, "agent") else "Triage Agent"
        ),
    }

    logger.info(f"Handled by agent: {response['final_agent']}")
    return response


# ========== Advanced Example: Agents as Tools ==========


@task
def create_orchestrator_agent() -> dict:
    """
    Creates an orchestrator agent that uses other agents as tools.
    """
    logger = get_run_logger()
    logger.info("Creating orchestrator agent")

    try:
        from agents import Agent, function_tool
    except ImportError:
        return {"error": "openai-agents not installed"}

    # Helper agent for translation
    @function_tool
    def translate_to_spanish(text: str) -> str:
        """Translate text to Spanish.

        Args:
            text: The text to translate
        """
        # Simplified translation (in reality, would use translation API)
        translations = {
            "hello": "hola",
            "goodbye": "adiós",
            "thank you": "gracias",
            "yes": "sí",
            "no": "no",
        }
        return translations.get(text.lower(), f"Spanish translation of: {text}")

    @function_tool
    def analyze_sentiment(text: str) -> str:
        """Analyze the sentiment of text.

        Args:
            text: The text to analyze
        """
        # Simplified sentiment analysis
        positive_words = ["good", "great", "excellent", "happy", "love"]
        negative_words = ["bad", "terrible", "sad", "hate", "awful"]

        text_lower = text.lower()
        if any(word in text_lower for word in positive_words):
            return "Positive sentiment detected"
        elif any(word in text_lower for word in negative_words):
            return "Negative sentiment detected"
        else:
            return "Neutral sentiment detected"

    # Create orchestrator
    orchestrator = Agent(
        name="Orchestrator",
        instructions="You are an orchestrator. Use the available tools to help users with translation and sentiment analysis.",
        tools=[translate_to_spanish, analyze_sentiment],
    )

    return {
        "orchestrator": orchestrator,
        "tools": ["translate_to_spanish", "analyze_sentiment"],
    }


@task
def run_orchestrator(orchestrator_config: dict, user_message: str) -> dict:
    """
    Runs the orchestrator agent.
    """
    logger = get_run_logger()
    logger.info(f"Running orchestrator with message: {user_message}")

    if "error" in orchestrator_config:
        return orchestrator_config

    try:
        from agents import Runner
    except ImportError:
        return {"error": "openai-agents not installed"}

    orchestrator = orchestrator_config["orchestrator"]
    result = Runner.run_sync(agent=orchestrator, input=user_message)

    return {"user_message": user_message, "response": result.final_output}


# ========== Workflows ==========


@flow(name="Simple Agent Flow", log_prints=True)
def simple_agent_flow():
    """
    Simple flow using an OpenAI agent with tools.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("SIMPLE OPENAI AGENT")
    print(f"{'='*60}\n")

    # Create agent
    print("Creating agent with tools...")
    agent_config = create_agent_with_tools()

    if "error" in agent_config:
        print(f"Error: {agent_config['error']}")
        print("\nInstall with: pip install openai-agents")
        return agent_config

    print(f"✓ Agent created with tools: {', '.join(agent_config['tools'])}\n")

    # Test queries
    queries = [
        "What's the weather in San Francisco?",
        "Calculate 15 * 8 + 23",
        "Search the database for orders",
    ]

    results = []
    for query in queries:
        print(f"User: {query}")
        result = run_agent(agent_config, query)

        if "error" not in result:
            print(f"Agent: {result['response']}\n")
            results.append(result)
        else:
            print(f"Error: {result['error']}\n")

    return results


@flow(name="Multi-Agent Flow", log_prints=True)
def multi_agent_flow():
    """
    Flow using multiple specialized agents with automatic handoffs.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("MULTI-AGENT SYSTEM WITH HANDOFFS")
    print(f"{'='*60}\n")

    # Create multi-agent system
    print("Creating multi-agent system...")
    agent_system = create_multi_agent_system()

    if "error" in agent_system:
        print(f"Error: {agent_system['error']}")
        print("\nInstall with: pip install openai-agents")
        return agent_system

    print(f"✓ Created agents: {', '.join(agent_system['agents'])}\n")

    # Test queries that should route to different agents
    queries = [
        "How much does the widget cost?",
        "I need to return order #12345",
        "Tell me about the gadget",
        "What's the status of my order #67890?",
    ]

    results = []
    for query in queries:
        print(f"User: {query}")
        result = run_multi_agent(agent_system, query)

        if "error" not in result:
            print(f"Agent ({result['final_agent']}): {result['response']}\n")
            results.append(result)
        else:
            print(f"Error: {result['error']}\n")

    return results


@flow(name="Orchestrator Agent Flow", log_prints=True)
def orchestrator_agent_flow():
    """
    Flow using an orchestrator agent with multiple tools.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("ORCHESTRATOR AGENT")
    print(f"{'='*60}\n")

    # Create orchestrator
    print("Creating orchestrator agent...")
    orchestrator_config = create_orchestrator_agent()

    if "error" in orchestrator_config:
        print(f"Error: {orchestrator_config['error']}")
        return orchestrator_config

    print(
        f"✓ Orchestrator created with tools: {', '.join(orchestrator_config['tools'])}\n"
    )

    # Test queries
    queries = [
        "Translate 'hello' to Spanish",
        "Analyze the sentiment of: This is a great product!",
        "What's the sentiment of: This is terrible",
    ]

    results = []
    for query in queries:
        print(f"User: {query}")
        result = run_orchestrator(orchestrator_config, query)

        if "error" not in result:
            print(f"Orchestrator: {result['response']}\n")
            results.append(result)
        else:
            print(f"Error: {result['error']}\n")

    return results


@flow(name="Agent Workflow Pipeline", log_prints=True)
def agent_workflow_pipeline():
    """
    Complex workflow using agents at different stages of a pipeline.
    """
    logger = get_run_logger()
    print(f"\n{'='*60}")
    print("AGENT WORKFLOW PIPELINE")
    print(f"{'='*60}\n")

    # Simulate customer support pipeline
    customer_messages = [
        "I want to buy the widget, how much is it?",
        "Can you check the status of order #99999?",
        "I'd like to return my gadget",
    ]

    # Create agent system
    print("Step 1: Creating agent system...")
    agent_system = create_multi_agent_system()

    if "error" in agent_system:
        print(f"Error: {agent_system['error']}")
        return agent_system

    print("✓ Agent system ready\n")

    # Process messages through pipeline
    print("Step 2: Processing customer messages...")
    results = []

    for i, message in enumerate(customer_messages, 1):
        print(f"\nMessage {i}: {message}")

        # Agent handles the message
        result = run_multi_agent(agent_system, message)

        if "error" not in result:
            print(f"Handled by: {result['final_agent']}")
            print(f"Response: {result['response']}")

            results.append(
                {
                    "message": message,
                    "agent": result["final_agent"],
                    "response": result["response"],
                }
            )
        else:
            print(f"Error: {result['error']}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Pipeline Summary:")
    print(f"  Messages processed: {len(results)}")
    print(f"  Agents used: {len(set(r['agent'] for r in results))}")
    print(f"{'='*60}")

    return results


# ========== Comprehensive Demo ==========


@flow(name="OpenAI Agent Comprehensive Demo", log_prints=True)
def comprehensive_agent_demo():
    """Runs all OpenAI agent examples."""

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("=" * 70)
        print("⚠️  WARNING: OPENAI_API_KEY not set")
        print("=" * 70)
        print("\nTo run these examples, set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("\nInstall the OpenAI Agents SDK:")
        print("pip install openai-agents")
        print("\nDocumentation: https://openai.github.io/openai-agents-python/")
        print("=" * 70)
        return

    print("=" * 70)
    print("COMPREHENSIVE OPENAI AGENT DEMONSTRATION")
    print("=" * 70)

    # Run all examples
    simple_agent_flow()
    multi_agent_flow()
    orchestrator_agent_flow()
    agent_workflow_pipeline()

    print("\n" + "=" * 70)
    print("All OpenAI agent examples completed")
    print("=" * 70)


if __name__ == "__main__":
    comprehensive_agent_demo()
