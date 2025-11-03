GOAL: I want to design a sufficient architecture for our AI software solution. Our software consist of cloud and client app. Cloud will be based on kubernetes. Client app will be most likely a CLI app that can communicate with UI where will be a WebGL canvas (VSCode extension or our own UI - probably React app).

Workflows: Our AI software will be chat based. User will give via chat a task, it will trigger a AI agent. AI agent can ask additional questions in the chat. Then proceed with task, once he is done, he will write into the chat back. AI agent will control (draw, change, remove, add) things on the UI canvas (via MCP server). AI agent is basically represented with "workflow". This workflow has multiple nodes, and it can be a multiple levels of abstraction. Main workflow consist of nodes, each node can be simple, but also a very complex (sub-workflow), as well as it can contain a LLM call or AI agents.

Local vs. Remote workflows: Some workflows will need to be running on client machine. It means they will need to be lighweight and quickly running. Some workflows can be running on our cloud infra (These can leverage a more complex workflow structures and more resources available. They can also be a long running or have a scheduled runs).

Workflows capabilites: We expect that workflows will be able to Manage files on client computer (Add, Edit, Remove ... etc.), Do a web searches, Write and run code.

Notes:
I want to design unified, yet robust architecture for our tasks/workflows. I am thinking to use temporal.io as main workflow system, but I don't know if it is not a overkill for locally running tasks.

We want to use ANY given (python based or NodeJS based) AI frameworks (Langgraph, OpenAI agent SDK, Claude Agent SDK ... etc.).

We consider options (for remoter workflows in k8s) such as:

- Temporal.io
- Prefect.io

We do not know options for running the local workflows.

Ideally the stack will not be so different.

New questions: 5. If I use temporal as my primary workfow engine. What If as one of the "node"/"activity" in the workflow I will trriger a langgraph agent, or openai agent, how will look observability? Can we have a unified observability software Ex. Jaeger,Langfuse to observe execution of temporal as well as langgraph or openai agents?

# Notes

**Complex workflows**
Prefect vs. Temporal.io ??? Which is better?

- Why Prefect over Temporal: While Temporal offers superior durability guarantees, it adds operational complexity (multiple services, databases, Kubernetes expertise required). MediumMedium Prefect provides 90% of the benefits with 50% of the complexity. Procycons Your use case—AI chat workflows—typically don't need the extreme reliability Temporal provides for financial transactions or critical infrastructure.

**Local Workflows**
Orbits - NodeJS - https://orbits.do/blog/workflows-orchestrate-microservices/
DBOS - Python, NodeJS - https://docs.dbos.dev/quickstart

**Background tasks** - Celery (Python), BullMQ (NodeJS)

- Task queues add minimal overhead (<5ms) and are battle-tested at massive scale. They complement rather than replace workflow orchestration.
