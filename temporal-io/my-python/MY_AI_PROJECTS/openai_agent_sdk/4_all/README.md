# Project 4: Product Launch Automation System

This project demonstrates the **complete integration** of all patterns: LLM calls, single AI agents with MCP tools, and multi-agent teams, orchestrated in a sophisticated product launch workflow.

## Comprehensive Workflow Architecture

```
Product Launch Automation
│
├─ Phase 1: Planning (Deterministic)
│  └─ Parse product specs, create timeline
│
├─ Phase 2: Market Research (Multi-Agent Swarm)
│  ├─ Competitor Analysis Swarm (3 agents)
│  │  └─ Agents share findings in real-time
│  └─ Customer Sentiment Swarm (3 agents)
│      └─ Analyze social media, reviews
│
├─ Phase 3: Content Creation (LLM Calls)
│  ├─ Product descriptions (LLM)
│  ├─ Marketing copy (LLM)
│  ├─ Technical docs (LLM)
│  └─ FAQ generation (LLM)
│
├─ Phase 4: Technical Deployment (Single Agent)
│  └─ Deployment Agent (with E2B)
│      ├─ Create deployment scripts
│      ├─ Configure monitoring
│      └─ Validate readiness
│
├─ Phase 5: Media Creation (Multi-Agent Supervision)
│  └─ Creative Director (Supervisor)
│      ├─ Copywriter Agent
│      ├─ Voice Agent (ElevenLabs)
│      ├─ Research Agent (Academia)
│      └─ Review Agent
│
├─ Phase 6: Campaign Setup (Deterministic)
│  └─ Schedule publishing, configure analytics
│
├─ Phase 7: Launch Monitoring (Single Agent + Mem0)
│  └─ Monitor metrics, recall past launches
│
├─ Phase 8: Customer Engagement (LLM Calls)
│  └─ Generate personalized responses
│
└─ Phase 9: Post-Launch Analysis (Multi-Agent)
   └─ Analysis Team
       ├─ Analytics Agent
       ├─ Feedback Agent
       └─ Improvement Agent
```

## Pattern Integration

### 1. LLM Calls (Simple)
```python
# Phase 3: Content Generation
content = await workflow.execute_activity(
    generate_marketing_copy,  # LLM call
    product_specs,
)
```

### 2. Single Agents with MCP
```python
# Phase 4: Technical Deployment
deployment_agent = Agent(
    name="Deployment Specialist",
    mcp_servers=[e2b_server],  # E2B sandbox
)
deployment = await Runner.run(deployment_agent, ...)
```

### 3. Multi-Agent Swarm
```python
# Phase 2: Market Research (agents share state)
swarm = AgentSwarm(
    agents=[competitor_agent1, competitor_agent2, competitor_agent3],
    shared_memory=True,
)
insights = await swarm.execute(research_task)
```

### 4. Multi-Agent Supervision
```python
# Phase 5: Media Creation
creative_director = Agent(name="Creative Director")
team = [copywriter, voice_agent, research_agent]

result = await creative_director.coordinate(
    team=team,
    task=create_media_assets,
)
```

## Key Features

### Pattern Diversity
- **Deterministic**: Fast, predictable operations
- **LLM Calls**: Quick AI enhancements
- **Single Agents**: Specialized tasks with tools
- **Multi-Agent Swarm**: Emergent insights from collaboration
- **Multi-Agent Supervision**: Coordinated complex tasks

### Dynamic Workflow Composition
```python
# Workflow can add/remove activities based on AI recommendations
if ai_recommends_additional_research:
    extra_research = await workflow.execute_activity(deep_dive_research, ...)
```

### Intelligent Retry Logic
```python
# AI determines optimal retry strategy
retry_strategy = await workflow.execute_activity(
    ai_analyze_failure,
    last_error,
)

result = await workflow.execute_activity(
    failing_activity,
    retry_policy=retry_strategy.to_policy(),
)
```

### Cross-Activity Learning
```python
# Later agents query outcomes from earlier ones
market_insights = workflow.get_activity_result("market_research")

content_agent = Agent(
    instructions=f"Create content based on insights: {market_insights}"
)
```

### Human-in-the-Loop
```python
# Critical decisions require approval
if critical_decision:
    approval = await workflow.wait_signal("human_approval")
    if not approval:
        return "Launch cancelled"
```

## Workflow Execution

```bash
# Start worker with all capabilities
python 4_all/run_worker.py

# Execute full product launch
python 4_all/run_workflow.py
```

## Sample Output

```
================================================================================
PRODUCT LAUNCH AUTOMATION - COMPLETE
================================================================================

Product: AI-Powered Analytics Platform v2.0
Launch Date: 2025-11-15

PHASE 1: PLANNING ✓
Timeline: 14 days
Resources allocated: $50k budget

PHASE 2: MARKET RESEARCH (Multi-Agent Swarm) ✓
Duration: 8.5 minutes
Competitor Analysis:
  - 12 competitors analyzed
  - Market gap identified: real-time collaboration
  - Pricing strategy: $49/month (vs avg $75/month)

Customer Sentiment:
  - 2,500 reviews analyzed
  - Top requested features: API access, mobile app
  - Sentiment: 72% positive

PHASE 3: CONTENT GENERATION (LLM) ✓
Created:
  - Product descriptions: 5 variants
  - Marketing copy: 12 pieces
  - Technical docs: 45 pages
  - FAQ: 32 questions

PHASE 4: DEPLOYMENT (Single Agent + E2B) ✓
  ✓ Infrastructure provisioned
  ✓ Monitoring configured
  ✓ A/B testing setup (3 variants)
  ✓ Production validation passed

PHASE 5: MEDIA ASSETS (Multi-Agent Supervision) ✓
Creative Director coordinated:
  - Video script: 2:30 duration
  - Voice-over: Professional narration (ElevenLabs)
  - Supporting research: 8 academic citations
  - Quality score: 94/100

PHASE 6: CAMPAIGN ORCHESTRATION ✓
  ✓ Email campaign: 15,000 subscribers
  ✓ Social media: 8 platforms
  ✓ Analytics tracking: Configured

PHASE 7: LAUNCH MONITORING (Agent + Mem0) ✓
Real-time metrics:
  - Sign-ups: 342 (first hour)
  - Server load: 34% (healthy)
  - Recall from past launches: Similar trajectory to successful launch #7

PHASE 8: CUSTOMER ENGAGEMENT (LLM) ✓
  - 156 inquiries processed
  - 98% automated responses
  - 12 escalations to human support

PHASE 9: POST-LAUNCH ANALYSIS (Multi-Agent Team) ✓
Analytics Agent: Launch exceeded projections by 23%
Feedback Agent: 89% positive sentiment
Improvement Agent: 7 actionable recommendations

================================================================================
LAUNCH STATUS: SUCCESS
Overall Confidence: 94%
Next Steps: Implement week-2 optimizations
================================================================================
```

## Advanced Capabilities

### 1. Graceful Degradation
If AI services fail, workflow continues with deterministic fallbacks.

### 2. Cost Tracking
```python
total_cost = sum([
    llm_calls_cost,      # $2.45
    agent_execution_cost, # $5.67
    mcp_tools_cost,      # $1.23
])
# Total: $9.35
```

### 3. Comprehensive Audit Trail
Every AI decision is logged for compliance and debugging.

### 4. Progressive Enhancement
Workflow starts with minimal AI, adds intelligence as needed.

## Customization

This project serves as a template for building sophisticated AI-powered workflows. Customize by:

1. Replace product launch with your domain
2. Add/remove AI agents based on needs
3. Adjust LLM vs Agent vs Multi-Agent balance
4. Configure MCP tools for your use case

## Summary

Project 4 demonstrates the **full power** of combining:
- Temporal's durable workflow execution
- OpenAI Agents SDK for AI capabilities
- MCP tools for specialized functions
- MongoDB for persistent knowledge
- Multiple agent coordination patterns

This creates production-ready AI-powered automation systems.
