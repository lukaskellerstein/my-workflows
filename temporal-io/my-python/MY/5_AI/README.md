# 5_AI - AI Integration Examples

This folder demonstrates how to integrate AI capabilities (LLMs, AI Agents, ReAct Agents) with Temporal workflows.

## Prerequisites

### 1. Temporal Server

```bash
temporal server start-dev
```

### 2. Python Dependencies

```bash
cd /path/to/temporalio
# If using uv:
uv venv
source .venv/bin/activate
uv sync

# Install AI dependencies:
pip install openai agents
```

### 3. OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Get your API key from: https://platform.openai.com/api-keys

## Examples

### 1. Simple LLM Call (`simple_llm_call.py`)

**Basic integration of LLM calls as workflow activities.**

**Demonstrates:**
- Calling OpenAI API within workflow activities
- Parallel LLM operations
- Text analysis: summarization, sentiment analysis, keyword extraction
- Error handling and mock responses for testing without API key

**Architecture:**
```
Workflow
├── Activity: Summarize text (LLM call)
├── Activity: Analyze sentiment (LLM call)
└── Activity: Extract keywords (LLM call)
```

**Run:**
```bash
python MY/5_AI/simple_llm_call.py
```

**Use Cases:**
- Content moderation
- Text classification
- Translation services
- Document summarization
- Sentiment analysis

### 2. AI Agent with Tools (`ai_agent_with_tools.py`)

**AI agent using OpenAI Agent SDK with access to workflow activities as tools.**

**Demonstrates:**
- OpenAI Agent SDK integration
- Converting Temporal activities to agent tools
- Agent reasoning and tool selection
- Multi-step agent workflows
- Complex query handling

**Architecture:**
```
AI Agent (OpenAI)
├── Tool: get_current_weather
├── Tool: search_flights
├── Tool: get_hotel_recommendations
├── Tool: calculate_total_cost
└── Tool: get_travel_advisories

Agent autonomously decides which tools to call and in what order
```

**Run:**
```bash
python MY/5_AI/ai_agent_with_tools.py
```

**Use Cases:**
- Customer service bots
- Travel planning assistants
- Research assistants
- Data analysis tools
- Task automation agents

**Example Interaction:**
```
User: "Plan a 5-night trip from New York to Tokyo in July"

Agent (internal reasoning):
1. Search flights from NY to Tokyo
2. Get weather in Tokyo for July
3. Find mid-range hotels
4. Calculate total cost
5. Check travel advisories
6. Provide comprehensive plan
```

### 3. ReAct Agent (`react_agent.py`)

**Complete ReAct (Reasoning + Acting) agent implementation as a Temporal workflow.**

**What is ReAct?**
ReAct is an AI agent pattern that combines:
- **Reasoning**: Thinking about what to do next
- **Acting**: Executing actions based on reasoning
- **Observing**: Learning from action results

Reference: [ReAct Paper (2022)](https://arxiv.org/abs/2210.03629)

**Demonstrates:**
- Full ReAct loop implementation
- Iterative problem-solving
- Multi-step reasoning
- Dynamic action selection
- Workflow-based agent orchestration

**Architecture:**
```
ReAct Loop (up to N iterations):
┌─────────────────────────────────────┐
│ 1. Reason (LLM)                     │
│    ├─ Thought: "I need to..."      │
│    ├─ Action: search_web            │
│    └─ Action Input: "query"         │
├─────────────────────────────────────┤
│ 2. Act (Execute Activity)           │
│    └─ Execute chosen action         │
├─────────────────────────────────────┤
│ 3. Observe (Get Result)             │
│    └─ Observation: "result..."      │
└─────────────────────────────────────┘
         │
         ├─ If more reasoning needed: Repeat
         └─ If complete: Return answer
```

**Available Actions:**
- `search_web` - Search for information
- `calculate` - Perform calculations
- `get_date` - Get current date
- `finish` - Complete with final answer

**Run:**
```bash
python MY/5_AI/react_agent.py
```

**Use Cases:**
- Complex question answering
- Multi-step problem solving
- Research and analysis
- Planning and scheduling
- Decision support systems

**Example Execution:**
```
Question: "What is Temporal and how does it help?"

Step 1:
  Thought: I need to search for information about Temporal
  Action: search_web
  Action Input: Temporal workflow engine
  Observation: Temporal is a durable execution platform...

Step 2:
  Thought: I have enough information to answer
  Action: finish
  Action Input: Temporal is a durable execution platform that...

Final Answer: [Complete answer based on gathered information]
```

## Key Concepts

### LLM Integration Patterns

#### 1. Activity-based LLM Calls
```python
@activity.defn
async def llm_activity(prompt: str) -> str:
    client = AsyncOpenAI()
    response = await client.chat.completions.create(...)
    return response.choices[0].message.content
```

**Pros:**
- Simple integration
- Easy error handling and retries
- Temporal handles durability

**Cons:**
- Each call is a separate activity
- No conversational context by default

#### 2. Agent-based Integration
```python
agent = Agent(
    name="Assistant",
    instructions="...",
    tools=[activity_as_tool(my_activity)]
)
result = await Runner.run(agent, input=question)
```

**Pros:**
- Agent handles tool selection
- Multi-step reasoning
- Conversational context

**Cons:**
- More complex setup
- Less control over execution flow

#### 3. ReAct Loop Pattern
```python
for iteration in range(max_iterations):
    reasoning = await llm_reason(...)
    observation = await execute_action(reasoning["action"])
    if reasoning["action"] == "finish":
        return observation
```

**Pros:**
- Full control over agent loop
- Visible reasoning steps
- Workflow-native implementation

**Cons:**
- More code to write
- Need to handle termination conditions

## Best Practices

### 1. Error Handling
```python
try:
    result = await llm_call()
except Exception as e:
    # Handle API failures gracefully
    return fallback_response()
```

### 2. Timeout Configuration
```python
await workflow.execute_activity(
    llm_activity,
    input_data,
    start_to_close_timeout=timedelta(seconds=30),  # LLM calls can be slow
)
```

### 3. Cost Management
- Use smaller models when possible (`gpt-4o-mini` vs `gpt-4`)
- Cache responses when appropriate
- Set max tokens limits
- Monitor usage

### 4. Prompt Engineering
```python
system_prompt = """You are a helpful assistant.
Be concise and specific.
Always format responses as JSON when requested."""
```

### 5. Mock Responses for Testing
```python
if not os.getenv("OPENAI_API_KEY"):
    return mock_response()  # Allow testing without API key
```

## Common Patterns

### Pattern 1: Analysis Pipeline
```
Input → [Classify] → [Process] → [Summarize] → Output
         (LLM)       (Logic)      (LLM)
```

### Pattern 2: Agent with Human Oversight
```
User Question → Agent Processes → [Approval Signal] → Execute
```

### Pattern 3: Multi-Agent System
```
Coordinator Agent
├── Research Agent (Child Workflow)
├── Analysis Agent (Child Workflow)
└── Summary Agent (Child Workflow)
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"
**Solution:** Export your API key:
```bash
export OPENAI_API_KEY="sk-..."
```

### Issue: Timeout errors
**Solution:** Increase activity timeout:
```python
start_to_close_timeout=timedelta(seconds=60)
```

### Issue: Rate limiting
**Solution:**
- Add retry logic
- Use exponential backoff
- Implement request queuing

### Issue: Non-deterministic workflows
**Problem:** LLM responses are non-deterministic
**Solution:** This is OK! Temporal handles non-determinism in activities

## Cost Considerations

| Model | Cost (per 1M tokens) | Use Case |
|-------|---------------------|----------|
| gpt-4o | $2.50 - $10.00 | Complex reasoning |
| gpt-4o-mini | $0.15 - $0.60 | Most use cases |
| gpt-3.5-turbo | $0.50 - $1.50 | Simple tasks |

**Tips:**
- Start with `gpt-4o-mini` for development
- Use streaming for better UX
- Cache common responses
- Set reasonable max_tokens

## Security Considerations

1. **API Key Management**
   - Never commit API keys
   - Use environment variables
   - Rotate keys regularly

2. **Input Validation**
   - Sanitize user inputs
   - Validate LLM outputs
   - Implement guardrails

3. **Content Filtering**
   - Filter sensitive information
   - Monitor for policy violations
   - Log all interactions

## Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Agents SDK](https://github.com/openai/agent-sdk)
- [Temporal OpenAI Integration](https://docs.temporal.io/develop/python/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)

## Next Steps

- Experiment with different models
- Build custom agents for your domain
- Implement agent memory and context
- Create multi-agent systems
- Add human-in-the-loop approvals (see `2_intermediate/`)
