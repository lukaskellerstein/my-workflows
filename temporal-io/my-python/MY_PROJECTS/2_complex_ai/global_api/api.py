"""
Global API - Complex AI Workflows
Handles all workflows, Slack validation, and React UI requests
UI is used for user interaction, Slack is used ONLY for final validation
"""

import asyncio
import os
import sys
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from temporalio.client import Client

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_code_analysis.workflow_definitions import (
    CodeAnalysisRequest,
    CodeAnalysisWorkflow,
    SlackValidation as CodeSlackValidation,
)
from workflow_content_generation.workflow_definitions import (
    ContentGenerationWorkflow,
    ContentRequest,
    SlackValidation as ContentSlackValidation,
)
from workflow_deep_research.workflow_definitions import (
    DeepResearchWorkflow,
    ResearchRequest,
    SlackValidation as ResearchSlackValidation,
    UIAnswer,
)
from workflow_orchestrator.workflow_definitions import (
    OrchestratorRequest,
    OrchestratorWorkflow,
)

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "complex-ai-task-queue"

app = FastAPI(
    title="Complex AI Workflows API",
    description="API for AI workflows with LLM, agents, and Slack validation",
    version="1.0.0",
)

# Add CORS middleware for React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models


class WorkflowResponse(BaseModel):
    """Response for workflow operations."""

    workflow_id: str
    workflow_type: str
    message: str
    status: str


class DeepResearchStartRequest(BaseModel):
    """Request to start deep research workflow."""

    task: str = Field(..., description="Research task")
    user_id: Optional[str] = Field("unknown", description="User ID")
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID")


class CodeAnalysisStartRequest(BaseModel):
    """Request to start code analysis workflow."""

    repository_path: str = Field(..., description="Path to repository")
    analysis_type: str = Field(
        ..., description="Type: security, performance, quality, refactoring"
    )
    user_id: Optional[str] = Field("unknown", description="User ID")
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID")


class ContentGenerationStartRequest(BaseModel):
    """Request to start content generation workflow."""

    topic: str = Field(..., description="Content topic")
    content_type: str = Field(
        ..., description="Type: blog, documentation, marketing, technical"
    )
    target_audience: str = Field(..., description="Target audience")
    tone: str = Field(
        ..., description="Tone: professional, casual, technical, friendly"
    )
    length: str = Field(..., description="Length: short, medium, long")
    user_id: Optional[str] = Field("unknown", description="User ID")
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID")


class OrchestratorStartRequest(BaseModel):
    """Request to start orchestrator workflow."""

    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field("unknown", description="User ID")
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID")


class UIAnswerRequest(BaseModel):
    """Request to answer a clarifying question from UI."""

    answer: str = Field(..., description="Answer text")
    question_index: int = Field(..., description="Question index")


# In-memory mapping of thread_ts to workflow_id and type
# In production, use Redis or database
thread_to_workflow = {}


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception:
                self.disconnect(client_id)


manager = ConnectionManager()


@app.get("/")
async def root():
    """API information."""
    return {
        "name": "Complex AI Workflows API",
        "version": "1.0.0",
        "description": "AI workflows with LLM, agents, and Slack validation",
        "architecture": {
            "ui_usage": "User interaction (questions, input)",
            "slack_usage": "Final validation before sending to user",
        },
        "workflows": {
            "orchestrator": "/orchestrator/start (NEW - Auto-routes to best workflow)",
            "deep_research": "/research/start",
            "code_analysis": "/code-analysis/start",
            "content_generation": "/content/start",
        },
        "endpoints": {
            "answer_question": "/workflow/{workflow_id}/answer",
            "get_questions": "/workflow/{workflow_id}/questions",
            "slack_events": "/slack/events",
            "workflow_status": "/workflow/{workflow_id}/status",
            "workflow_result": "/workflow/{workflow_id}/result",
        },
    }


@app.get("/health")
async def health():
    """Health check."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        slack_configured = bool(os.getenv("SLACK_BOT_TOKEN"))
        openai_configured = bool(os.getenv("OPENAI_API_KEY"))

        return {
            "status": "healthy",
            "temporal_connected": True,
            "slack_configured": slack_configured,
            "openai_configured": openai_configured,
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Temporal connection failed: {str(e)}"
        )


# Orchestrator Workflow Endpoints


@app.post("/orchestrator/start", response_model=WorkflowResponse)
async def start_orchestrator(request: OrchestratorStartRequest):
    """Start orchestrator workflow - auto-routes to best sub-workflow or handles directly."""
    try:
        client = await Client.connect(TEMPORAL_HOST)

        workflow_id = request.workflow_id or f"orchestrator-{uuid.uuid4()}"

        orchestrator_request = OrchestratorRequest(
            message=request.message, user_id=request.user_id
        )

        await client.start_workflow(
            OrchestratorWorkflow.run,
            orchestrator_request,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        # Start background monitoring task to send result via WebSocket
        asyncio.create_task(monitor_workflow_and_notify(workflow_id, request.user_id))

        return WorkflowResponse(
            workflow_id=workflow_id,
            workflow_type="orchestrator",
            message="Orchestrator workflow started. Classifying intent and routing...",
            status="running",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {str(e)}"
        )


@app.get("/orchestrator/{workflow_id}/routing")
async def get_routing_decision(workflow_id: str):
    """Get routing decision from orchestrator workflow."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        routing = await handle.query(OrchestratorWorkflow.get_routing_decision)

        return {
            "workflow_id": workflow_id,
            "routing_decision": routing,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get routing decision: {str(e)}"
        )


# Deep Research Workflow Endpoints


@app.post("/research/start", response_model=WorkflowResponse)
async def start_deep_research(request: DeepResearchStartRequest):
    """Start deep research workflow."""
    try:
        client = await Client.connect(TEMPORAL_HOST)

        workflow_id = request.workflow_id or f"deep-research-{uuid.uuid4()}"

        research_request = ResearchRequest(task=request.task, user_id=request.user_id)

        await client.start_workflow(
            DeepResearchWorkflow.run,
            research_request,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        # Start background monitoring task to send result via WebSocket
        asyncio.create_task(monitor_workflow_and_notify(workflow_id, request.user_id))

        return WorkflowResponse(
            workflow_id=workflow_id,
            workflow_type="deep_research",
            message="Deep research workflow started. Asking clarifying questions...",
            status="running",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {str(e)}"
        )


@app.get("/workflow/{workflow_id}/questions")
async def get_clarifying_questions(workflow_id: str):
    """Get clarifying questions for deep research workflow."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        questions = await handle.query(DeepResearchWorkflow.get_clarifying_questions)

        return {
            "workflow_id": workflow_id,
            "questions": questions,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get questions: {str(e)}"
        )


@app.post("/workflow/{workflow_id}/answer")
async def answer_question(workflow_id: str, request: UIAnswerRequest):
    """Answer a clarifying question from UI."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        answer = UIAnswer(
            text=request.answer,
            question_index=request.question_index,
            timestamp=str(uuid.uuid4()),  # Using UUID as timestamp
        )

        await handle.signal(DeepResearchWorkflow.answer_question, answer)

        return {
            "workflow_id": workflow_id,
            "question_index": request.question_index,
            "message": "Answer received",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send answer: {str(e)}")


# Code Analysis Workflow Endpoints


@app.post("/code-analysis/start", response_model=WorkflowResponse)
async def start_code_analysis(request: CodeAnalysisStartRequest):
    """Start code analysis workflow."""
    try:
        client = await Client.connect(TEMPORAL_HOST)

        workflow_id = request.workflow_id or f"code-analysis-{uuid.uuid4()}"

        analysis_request = CodeAnalysisRequest(
            repository_path=request.repository_path,
            analysis_type=request.analysis_type,
            user_id=request.user_id,
        )

        await client.start_workflow(
            CodeAnalysisWorkflow.run,
            analysis_request,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            workflow_type="code_analysis",
            message="Code analysis workflow started. Scanning repository...",
            status="running",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {str(e)}"
        )


# Content Generation Workflow Endpoints


@app.post("/content/start", response_model=WorkflowResponse)
async def start_content_generation(request: ContentGenerationStartRequest):
    """Start content generation workflow."""
    try:
        client = await Client.connect(TEMPORAL_HOST)

        workflow_id = request.workflow_id or f"content-gen-{uuid.uuid4()}"

        content_request = ContentRequest(
            topic=request.topic,
            content_type=request.content_type,
            target_audience=request.target_audience,
            tone=request.tone,
            length=request.length,
            user_id=request.user_id,
        )

        await client.start_workflow(
            ContentGenerationWorkflow.run,
            content_request,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        return WorkflowResponse(
            workflow_id=workflow_id,
            workflow_type="content_generation",
            message="Content generation workflow started. Creating outline...",
            status="running",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {str(e)}"
        )


# Slack Events Endpoint


@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Slack Events API endpoint.
    Receives validation responses from Slack and routes to appropriate workflow.
    """
    try:
        body = await request.json()

        print(f"Received Slack event: {body}")

        # Slack URL verification challenge
        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge")}

        # Handle event
        event = body.get("event", {})
        event_type = event.get("type")

        # We're interested in message events
        if event_type == "message":
            # Check if this is a bot message (cache workflow ID)
            if event.get("bot_id"):
                message_ts = event.get("ts")
                blocks = event.get("blocks", [])
                for block in blocks:
                    if block.get("type") == "context":
                        for element in block.get("elements", []):
                            text = element.get("text", "")
                            import re

                            match = re.search(r"Workflow: `([^`]+)`", text)
                            if match:
                                workflow_id = match.group(1)
                                # Determine workflow type from ID
                                # Check sub-workflows first to avoid false matches
                                if "sub-research" in workflow_id or "deep-research" in workflow_id:
                                    wf_type = "deep_research"
                                elif "sub-code" in workflow_id or "code-analysis" in workflow_id:
                                    wf_type = "code_analysis"
                                elif "sub-content" in workflow_id or "content-gen" in workflow_id:
                                    wf_type = "content_generation"
                                else:
                                    wf_type = "unknown"

                                thread_to_workflow[message_ts] = {
                                    "workflow_id": workflow_id,
                                    "type": wf_type,
                                }
                                print(
                                    f"✓ Cached workflow ID from bot message: {message_ts} -> {workflow_id} (type: {wf_type})"
                                )
                                break
                return {"ok": True}

            # Ignore message changes
            if event.get("subtype"):
                return {"ok": True}

            # Check if this is a thread reply
            thread_ts = event.get("thread_ts")
            if not thread_ts:
                return {"ok": True}

            # Look up workflow
            print(f"Looking for thread_ts: {thread_ts}")
            print(f"Available mappings: {thread_to_workflow}")

            workflow_info = thread_to_workflow.get(thread_ts)
            if not workflow_info:
                print(f"✗ No workflow found for thread {thread_ts}")
                return {"ok": True}

            workflow_id = workflow_info["workflow_id"]
            workflow_type = workflow_info["type"]

            # Extract validation details
            validation_text = event.get("text", "").strip()
            user = event.get("user", "unknown")
            message_ts = event.get("ts", "")

            print(
                f"Received validation for workflow {workflow_id} ({workflow_type}): {validation_text}"
            )

            # Send validation to workflow
            client = await Client.connect(TEMPORAL_HOST)
            handle = client.get_workflow_handle(workflow_id)

            # Parse validation (yes/no)
            approved = validation_text.lower() == "yes"

            # All workflows now use SlackValidation
            if workflow_type == "deep_research":
                validation = ResearchSlackValidation(
                    approved=approved,
                    user=f"<@{user}>",
                    user_id=user,
                    feedback=validation_text,
                    timestamp=message_ts,
                    thread_ts=thread_ts,
                )
                await handle.signal(DeepResearchWorkflow.receive_validation, validation)

            elif workflow_type == "code_analysis":
                validation = CodeSlackValidation(
                    approved=approved,
                    user=f"<@{user}>",
                    user_id=user,
                    feedback=validation_text,
                    timestamp=message_ts,
                    thread_ts=thread_ts,
                )
                await handle.signal(CodeAnalysisWorkflow.receive_validation, validation)

            elif workflow_type == "content_generation":
                validation = ContentSlackValidation(
                    approved=approved,
                    user=f"<@{user}>",
                    user_id=user,
                    feedback=validation_text,
                    timestamp=message_ts,
                    thread_ts=thread_ts,
                )
                await handle.signal(
                    ContentGenerationWorkflow.receive_validation, validation
                )

            print(f"Validation sent to workflow {workflow_id}")

        return {"ok": True}

    except Exception as e:
        print(f"Error handling Slack event: {e}")
        return {"ok": False, "error": str(e)}


# Workflow Status/Result Endpoints


@app.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get workflow status."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        # Determine workflow type from ID
        # IMPORTANT: Check sub-workflows BEFORE orchestrator to avoid false matches
        if "sub-research" in workflow_id or "deep-research" in workflow_id:
            status = await handle.query(DeepResearchWorkflow.get_status)
            return {
                "workflow_id": workflow_id,
                "type": "deep_research",
                "status": status,
            }
        elif "sub-code" in workflow_id or "code-analysis" in workflow_id:
            status = await handle.query(CodeAnalysisWorkflow.get_status)
            return {
                "workflow_id": workflow_id,
                "type": "code_analysis",
                "status": status,
            }
        elif "sub-content" in workflow_id or "content-gen" in workflow_id:
            status = await handle.query(ContentGenerationWorkflow.get_status)
            return {
                "workflow_id": workflow_id,
                "type": "content_generation",
                "status": status,
            }
        elif "orchestrator" in workflow_id:
            status = await handle.query(OrchestratorWorkflow.get_status)
            return {
                "workflow_id": workflow_id,
                "type": "orchestrator",
                "status": status,
            }
        else:
            return {"workflow_id": workflow_id, "type": "unknown", "status": {}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query status: {str(e)}")


@app.get("/workflow/{workflow_id}/result")
async def get_workflow_result(workflow_id: str):
    """Get workflow result (waits for completion)."""
    try:
        import dataclasses

        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        result = await handle.result()

        # Serialize result properly
        if dataclasses.is_dataclass(result):
            result_dict = dataclasses.asdict(result)
        elif isinstance(result, dict):
            result_dict = result
        elif hasattr(result, "__dict__"):
            result_dict = result.__dict__
        else:
            result_dict = {"value": str(result)}

        return {
            "workflow_id": workflow_id,
            "result": result_dict,
            "status": "completed",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection for real-time workflow updates."""
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and receive any messages from client
            data = await websocket.receive_text()
            # Client can send workflow IDs to monitor
            # For now, just keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(client_id)


async def monitor_workflow_and_notify(workflow_id: str, client_id: str):
    """Monitor workflow completion and send result via WebSocket."""
    try:
        import dataclasses
        import json
        import ast

        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        # Wait for workflow to complete
        result = await handle.result()

        # Serialize result properly - handle various formats
        if dataclasses.is_dataclass(result):
            # Convert dataclass to dict
            result_dict = dataclasses.asdict(result)
        elif isinstance(result, dict):
            # Check if it's a wrapped string value
            if "value" in result and isinstance(result["value"], str):
                try:
                    # Try to parse Python dict string representation
                    result_dict = ast.literal_eval(result["value"])
                except (ValueError, SyntaxError):
                    try:
                        # Try JSON parsing
                        result_dict = json.loads(result["value"])
                    except (json.JSONDecodeError, TypeError):
                        result_dict = result
            else:
                result_dict = result
        elif hasattr(result, "__dict__"):
            result_dict = result.__dict__
        elif isinstance(result, str):
            # Try to parse if it's a string representation
            try:
                result_dict = ast.literal_eval(result)
            except (ValueError, SyntaxError):
                try:
                    result_dict = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    result_dict = {"value": result}
        else:
            result_dict = {"value": str(result)}

        # Send result to UI via WebSocket
        await manager.send_personal_message(
            {
                "type": "workflow_result",
                "workflow_id": workflow_id,
                "result": result_dict,
                "status": "completed",
            },
            client_id,
        )

    except Exception as e:
        # Send error to UI
        await manager.send_personal_message(
            {
                "type": "workflow_error",
                "workflow_id": workflow_id,
                "error": str(e),
                "status": "failed",
            },
            client_id,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
