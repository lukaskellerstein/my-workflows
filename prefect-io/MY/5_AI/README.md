# 5_AI - AI Integration Examples

This folder demonstrates AI and LLM integration with Prefect workflows.

## Prerequisites

```bash
# Install required packages
pip install openai openai-agents

# Set your OpenAI API key
export OPENAI_API_KEY='your-api-key-here'
```

## Examples

### 1. LLM in Task (`01_llm_in_task.py`)
Demonstrates LLM API calls within Prefect tasks.

**Demonstrates:**
- **Simple LLM Call**: Basic OpenAI API integration
- **Text Extraction**: Extract structured data from unstructured text
- **Text Classification**: Classify text into categories
- **Summarization**: Summarize documents in parallel
- **Conversational Flow**: Multi-turn conversation with context

**Key Patterns:**
```python
@task(retries=2, retry_delay_seconds=1)
def call_llm(prompt: str, model: str = "gpt-3.5-turbo") -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return {"response": response.choices[0].message.content}

@flow
def llm_workflow():
    # Use LLM in workflow
    result = call_llm("Explain Prefect in one sentence")

    # Parallel LLM calls
    summaries = summarize_text.map(documents)
```

**Run:**
```bash
python 01_llm_in_task.py
```

### 2. OpenAI Agent SDK (`02_openai_agent.py`)
Demonstrates using OpenAI's official Agent SDK in workflows.

**Demonstrates:**
- **Agent with Tools**: Create agent with custom functions
- **Multi-Agent System**: Multiple specialized agents with handoffs
- **Orchestrator Pattern**: Agents with multiple tools
- **Agent Pipeline**: Integrate agents into workflow stages

**Key Concepts:**

**Single Agent with Tools:**
```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(location: str) -> str:
    """Get the weather for a location.

    Args:
        location: The city name
    """
    return f"Weather in {location}: Sunny, 72°F"

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant",
    tools=[get_weather]
)

# Run the agent
result = Runner.run_sync(agent=agent, input="What's the weather in NYC?")
print(result.final_output)
```

**Multi-Agent System with Handoffs:**
```python
from agents import Agent, function_tool

# Define tools for specialized agents
@function_tool
def get_product_info(product: str) -> str:
    """Get product information."""
    return f"Product info for {product}"

@function_tool
def check_order_status(order_id: str) -> str:
    """Check order status."""
    return f"Order {order_id} status"

# Create specialized agents
sales_agent = Agent(
    name="Sales",
    instructions="Help with sales",
    tools=[get_product_info]
)

support_agent = Agent(
    name="Support",
    instructions="Help with support",
    tools=[check_order_status]
)

# Triage agent with handoffs
triage_agent = Agent(
    name="Triage",
    instructions="Route to appropriate agent",
    handoffs=[sales_agent, support_agent]  # Enable handoffs
)

# Agent will automatically handoff to correct specialist
result = Runner.run_sync(agent=triage_agent, input="What's the price of widget?")
```

**Run:**
```bash
python 02_openai_agent.py
```

### 3. ReAct Agent Workflow (`03_react_agent_workflow.py`)
Complete ReAct (Reasoning + Acting) agent implemented as a Prefect workflow.

**Demonstrates:**
- **ReAct Loop**: Thought → Action → Observation cycle
- **Tool Execution**: Agent uses tools to solve problems
- **Multi-Step Reasoning**: Agent breaks down complex tasks
- **Parallel Agents**: Run multiple ReAct agents concurrently

**ReAct Pattern:**
```
1. THOUGHT: "I need to calculate something"
2. ACTION: calculate: 25 + 15
3. OBSERVATION: 40
4. THOUGHT: "Now I need to multiply by 3"
5. ACTION: calculate: 40 * 3
6. OBSERVATION: 120
7. THOUGHT: "I have the answer"
8. ANSWER: 120
```

**Workflow Structure:**
```python
@flow
def react_agent_flow(task: str, max_iterations: int = 10):
    conversation_history = []

    for iteration in range(max_iterations):
        # Generate thought
        thought = generate_thought(conversation_history, task)

        # Parse action from thought
        action = parse_action(thought)

        # Check if final answer
        if action["type"] == "answer":
            return action["content"]

        # Execute action
        observation = execute_action(action)

        # Add to history for next iteration
        conversation_history.append({"observation": observation})

    return "Max iterations reached"
```

**Run:**
```bash
python 03_react_agent_workflow.py
```

## Use Cases

### LLM in Tasks
- **Data Enrichment**: Add AI-generated descriptions, tags, or classifications
- **Content Generation**: Generate reports, summaries, or documentation
- **Data Extraction**: Parse unstructured text into structured data
- **Quality Assurance**: AI-powered data validation and anomaly detection
- **Translation**: Translate content across languages
- **Sentiment Analysis**: Analyze customer feedback or reviews

### OpenAI Agents
- **Customer Support**: Multi-agent system handling different support types
- **Sales Pipeline**: Route leads to appropriate sales agents
- **Data Analysis**: Agents with specialized tools for different analyses
- **Process Automation**: Agents that execute business processes
- **Research Assistant**: Agents that gather and synthesize information

### ReAct Agents
- **Complex Problem Solving**: Break down and solve multi-step problems
- **Data Pipeline Orchestration**: Agent decides what data operations to run
- **Adaptive Workflows**: Workflow that changes based on agent decisions
- **Research and Analysis**: Agent explores data and generates insights
- **Automated Debugging**: Agent investigates and fixes issues

## Architecture Patterns

### 1. LLM as Data Processor
```python
@flow
def data_pipeline():
    raw_data = extract_data()
    enriched = enrich_with_llm.map(raw_data)  # Parallel LLM calls
    load_data(enriched)
```

### 2. Agent as Decision Maker
```python
@flow
def intelligent_pipeline():
    data = prepare_data()

    # Agent decides what to do
    decision = agent_analyze(data)

    # Branch based on agent decision
    if decision["action"] == "process_a":
        process_type_a(data)
    else:
        process_type_b(data)
```

### 3. ReAct Agent as Orchestrator
```python
@flow
def agent_orchestrated_workflow():
    task = "Analyze sales data and generate report"

    # Agent decides and executes steps
    result = react_agent_flow(task)

    # Agent has full control of workflow execution
    return result
```

### 4. Hybrid: Workflow + Agents
```python
@flow
def hybrid_workflow():
    # Fixed workflow steps
    data = extract_data()
    validated = validate_data(data)

    # Agent handles complex analysis
    insights = agent_analyze(validated)

    # Back to fixed workflow
    report = generate_report(insights)
    send_report(report)
```

## Performance Considerations

### Token Usage
- Monitor token consumption for cost control
- Cache LLM responses when possible
- Use smaller models for simple tasks
- Batch similar requests

### Concurrency
- Use `.map()` for parallel LLM calls
- Set appropriate rate limits
- Handle API throttling with retries
- Consider using async for I/O-bound LLM calls

### Error Handling
```python
@task(retries=3, retry_delay_seconds=[1, 2, 5])
def resilient_llm_call(prompt: str) -> dict:
    try:
        return call_llm(prompt)
    except RateLimitError:
        # Handle rate limiting
        raise  # Will retry
    except Exception as e:
        # Handle other errors
        return {"error": str(e)}
```

## Best Practices

1. **API Key Management**: Use environment variables, never hardcode
2. **Error Handling**: Always handle API errors and rate limits
3. **Retry Strategy**: Use retries for transient failures
4. **Token Monitoring**: Track and log token usage
5. **Model Selection**: Choose appropriate model for task (GPT-4 vs GPT-3.5)
6. **Prompt Engineering**: Design clear, specific prompts
7. **Response Parsing**: Validate and parse LLM responses carefully
8. **Cost Control**: Set budgets and monitor spending
9. **Caching**: Cache responses for identical requests
10. **Testing**: Test with various inputs and edge cases

## Cost Optimization

```python
# Use cheaper models for simple tasks
@task
def simple_classification(text: str):
    return call_llm(text, model="gpt-3.5-turbo")  # Cheaper

# Use expensive models only when needed
@task
def complex_analysis(text: str):
    return call_llm(text, model="gpt-4")  # More expensive but better

# Batch processing to reduce API calls
@flow
def batch_processing():
    # Process multiple items in single LLM call
    batch_prompt = f"Classify these texts:\n{'\n'.join(texts)}"
    return call_llm(batch_prompt)
```

## Next Steps

- Explore LangChain integration with Prefect
- Implement vector database integration (Chroma, Qdrant)
- Build RAG (Retrieval Augmented Generation) pipelines
- Integrate with LangGraph for complex agent workflows
- Implement human-in-the-loop AI workflows
- Build AI-powered data quality monitoring
