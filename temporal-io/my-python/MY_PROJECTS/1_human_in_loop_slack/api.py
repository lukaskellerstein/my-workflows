"""
FastAPI - Slack Human in the Loop
REST API with Slack Events API integration to receive thread replies.
"""

import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from temporalio.client import Client

from workflow_definitions import Question, SlackAnswer, SlackQuestionWorkflow

# Configuration
TEMPORAL_HOST = "localhost:7233"
TASK_QUEUE = "slack-question-task-queue"
SLACK_VERIFICATION_TOKEN = os.getenv("SLACK_VERIFICATION_TOKEN")

app = FastAPI(
    title="Slack Question Workflow API",
    description="API for workflows that post questions to Slack and wait for answers",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    """Request to start a question workflow."""

    question: str = Field(
        ..., description="The question to ask", example="Deploy to production?"
    )
    context: str = Field(
        ..., description="Additional context", example="All tests passed"
    )
    channel: str = Field(
        default="human-in-loop", description="Slack channel to post in"
    )
    workflow_id: Optional[str] = Field(None, description="Optional workflow ID")


class WorkflowResponse(BaseModel):
    """Response for workflow operations."""

    workflow_id: str
    message: str
    status: str


class AnswerRequest(BaseModel):
    """Manual answer request (for testing)."""

    answer: str = Field(..., description="The answer text", example="yes")
    user: str = Field(default="test-user", description="User providing answer")


# In-memory mapping of thread_ts to workflow_id
# In production, use Redis or database
thread_to_workflow = {}


@app.get("/")
async def root():
    """API information."""
    return {
        "name": "Slack Question Workflow API",
        "version": "1.0.0",
        "description": "Post questions to Slack and wait for text answers",
        "endpoints": {
            "start_question": "/question/start",
            "slack_events": "/slack/events",
            "manual_answer": "/question/{workflow_id}/answer",
            "status": "/question/{workflow_id}/status",
            "result": "/question/{workflow_id}/result",
        },
    }


@app.get("/health")
async def health():
    """Health check."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        slack_configured = bool(os.getenv("SLACK_BOT_TOKEN"))
        return {
            "status": "healthy",
            "temporal_connected": True,
            "slack_configured": slack_configured,
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Temporal connection failed: {str(e)}"
        )


@app.post("/question/start", response_model=WorkflowResponse)
async def start_question(request: QuestionRequest):
    """
    Start a question workflow that posts to Slack.

    The workflow will:
    1. Post the question to Slack channel
    2. Wait for a reply in the thread
    3. If answer is "yes" → Execute Path YES
    4. If answer is anything else → Execute Path NO
    """
    try:
        client = await Client.connect(TEMPORAL_HOST)

        workflow_id = request.workflow_id or f"slack-question-{uuid.uuid4()}"

        question = Question(
            text=request.question, context=request.context, channel=request.channel
        )

        # Start workflow
        handle = await client.start_workflow(
            SlackQuestionWorkflow.run,
            question,
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )

        # Wait a moment for thread_ts to be available
        import asyncio

        await asyncio.sleep(2)  # Increased wait time

        # Get thread_ts and store mapping
        try:
            thread_ts = await handle.query(SlackQuestionWorkflow.get_thread_ts)
            if thread_ts:
                thread_to_workflow[thread_ts] = workflow_id
                print(f"✓ Stored mapping: {thread_ts} -> {workflow_id}")
            else:
                print(f"✗ Thread TS not available yet")
        except Exception as e:
            print(f"✗ Failed to query thread_ts: {e}")

        return WorkflowResponse(
            workflow_id=workflow_id,
            message="Question posted to Slack. Waiting for answer in thread.",
            status="waiting_for_answer",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start workflow: {str(e)}"
        )


@app.post("/slack/events")
async def slack_events(request: Request):
    """
    Slack Events API endpoint.

    Receives events from Slack including thread replies.
    When a user replies to the question thread, this sends
    the answer to the workflow via signal.
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
            # Check if this is a bot message (our workflow question)
            if event.get("bot_id"):
                # Extract and store workflow ID from bot's own message
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
                                thread_to_workflow[message_ts] = workflow_id
                                print(f"✓ Cached workflow ID from bot message: {message_ts} -> {workflow_id}")
                                break
                return {"ok": True}

            # Ignore message changes
            if event.get("subtype"):
                return {"ok": True}

            # Check if this is a thread reply
            thread_ts = event.get("thread_ts")
            if not thread_ts:
                return {"ok": True}

            # Look up workflow ID for this thread
            print(f"Looking for thread_ts: {thread_ts}")
            print(f"Available mappings: {thread_to_workflow}")
            workflow_id = thread_to_workflow.get(thread_ts)

            # If not in mapping, try to extract from the thread parent message
            if not workflow_id:
                print(f"No mapping found, trying to extract from parent message...")
                try:
                    from slack_sdk.web.async_client import AsyncWebClient

                    slack_token = os.getenv("SLACK_BOT_TOKEN")
                    if slack_token:
                        client = AsyncWebClient(token=slack_token)
                        # Fetch the parent message
                        result = await client.conversations_history(
                            channel=event.get("channel"),
                            latest=thread_ts,
                            limit=1,
                            inclusive=True,
                        )
                        if result["messages"]:
                            parent_msg = result["messages"][0]
                            print(f"DEBUG: Parent message: {parent_msg}")
                            # Extract workflow ID from message text or blocks
                            import re

                            # Try text field first
                            text = parent_msg.get("text", "")
                            print(f"DEBUG: Text field: {text}")
                            match = re.search(r"Workflow: `([^`]+)`", text)

                            # If not found, try blocks
                            if not match and "blocks" in parent_msg:
                                for block in parent_msg["blocks"]:
                                    if block.get("type") == "context":
                                        for element in block.get("elements", []):
                                            element_text = element.get("text", "")
                                            match = re.search(r"Workflow: `([^`]+)`", element_text)
                                            if match:
                                                break
                                        if match:
                                            break

                            if match:
                                workflow_id = match.group(1)
                                print(
                                    f"✓ Extracted workflow ID from message: {workflow_id}"
                                )
                                # Store for future use
                                thread_to_workflow[thread_ts] = workflow_id
                except Exception as e:
                    print(f"Failed to extract workflow ID: {e}")

            if not workflow_id:
                print(f"✗ No workflow found for thread {thread_ts}")
                return {"ok": True}

            # Extract answer details
            answer_text = event.get("text", "").strip()
            user = event.get("user", "unknown")
            message_ts = event.get("ts", "")

            print(f"Received answer for workflow {workflow_id}: {answer_text}")

            # Send signal to workflow
            client = await Client.connect(TEMPORAL_HOST)
            handle = client.get_workflow_handle(workflow_id)

            answer = SlackAnswer(
                text=answer_text,
                user=f"<@{user}>",
                user_id=user,
                timestamp=message_ts,
                thread_ts=thread_ts,
            )

            await handle.signal(SlackQuestionWorkflow.receive_answer, answer)

            print(f"Answer sent to workflow {workflow_id}")

            # Clean up mapping
            thread_to_workflow.pop(thread_ts, None)

        return {"ok": True}

    except Exception as e:
        print(f"Error handling Slack event: {e}")
        return {"ok": False, "error": str(e)}


@app.post("/question/{workflow_id}/answer", response_model=WorkflowResponse)
async def manual_answer(workflow_id: str, request: AnswerRequest):
    """
    Manually send an answer to a workflow (for testing).

    Args:
        workflow_id: The workflow ID
        request: Answer details
    """
    try:
        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        answer = SlackAnswer(
            text=request.answer,
            user=request.user,
            user_id=request.user,
            timestamp="manual",
            thread_ts="manual",
        )

        await handle.signal(SlackQuestionWorkflow.receive_answer, answer)

        return WorkflowResponse(
            workflow_id=workflow_id,
            message=f"Answer '{request.answer}' sent by {request.user}",
            status="answer_received",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send answer: {str(e)}")


@app.get("/question/{workflow_id}/status")
async def get_status(workflow_id: str):
    """Query workflow status."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        status = await handle.query(SlackQuestionWorkflow.get_status)

        return {"workflow_id": workflow_id, "status": status}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query status: {str(e)}")


@app.get("/question/{workflow_id}/result")
async def get_result(workflow_id: str):
    """Get workflow result (waits for completion)."""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        handle = client.get_workflow_handle(workflow_id)

        result = await handle.result()

        return {"workflow_id": workflow_id, "result": result, "status": "completed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
