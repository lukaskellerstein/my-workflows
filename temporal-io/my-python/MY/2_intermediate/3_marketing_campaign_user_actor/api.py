"""REST API for marketing campaign system with User Actor pattern."""

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from temporalio.client import Client

from models import (
    CampaignMessage,
    CampaignPriority,
    CampaignType,
    FrequencyCap,
    FrequencyCheckResult,
    UserState,
)
from user_actor_workflow import UserActorWorkflow
from campaign_workflow import CampaignWorkflow

app = FastAPI(title="Marketing Campaign API - User Actor Pattern Demo")

# Global client (initialized on startup)
temporal_client: Optional[Client] = None


class InitUserActorRequest(BaseModel):
    """Request to initialize a user actor."""
    user_id: str
    max_messages_per_day: int = 3
    max_messages_per_week: int = 10
    max_messages_per_month: int = 30
    min_hours_between_messages: int = 2
    max_emails_per_week: int = 5
    max_sms_per_week: int = 3


class LaunchCampaignRequest(BaseModel):
    """Request to launch a campaign."""
    campaign_id: str
    campaign_name: str
    campaign_type: CampaignType
    priority: CampaignPriority
    message_content: str
    target_user_ids: list[str]
    metadata: dict = {}


class OptOutRequest(BaseModel):
    """Request to opt out of a channel."""
    channel: CampaignType


@app.on_event("startup")
async def startup():
    """Initialize Temporal client on startup."""
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")
    print("✅ Connected to Temporal server")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if temporal_client:
        await temporal_client.close()


@app.post("/users/{user_id}/init", status_code=201)
async def init_user_actor(user_id: str, request: InitUserActorRequest):
    """
    Initialize a User Actor workflow for a user.

    This creates a long-running workflow that maintains all state for this user.
    You only need to do this once per user.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"user-actor-{user_id}"

    try:
        # Check if already exists
        try:
            handle = temporal_client.get_workflow_handle(workflow_id)
            await handle.query(UserActorWorkflow.get_user_state)
            return {
                "message": "User actor already exists",
                "user_id": user_id,
                "workflow_id": workflow_id
            }
        except:
            pass

        # Create frequency cap
        frequency_cap = FrequencyCap(
            max_messages_per_day=request.max_messages_per_day,
            max_messages_per_week=request.max_messages_per_week,
            max_messages_per_month=request.max_messages_per_month,
            min_hours_between_messages=request.min_hours_between_messages,
            max_emails_per_week=request.max_emails_per_week,
            max_sms_per_week=request.max_sms_per_week,
        )

        # Start User Actor workflow
        handle = await temporal_client.start_workflow(
            UserActorWorkflow.run,
            args=[user_id, frequency_cap],
            id=workflow_id,
            task_queue="marketing-campaign-queue",
        )

        return {
            "message": "User actor initialized successfully",
            "user_id": user_id,
            "workflow_id": handle.id,
            "frequency_cap": {
                "max_messages_per_day": frequency_cap.max_messages_per_day,
                "max_messages_per_week": frequency_cap.max_messages_per_week,
                "max_messages_per_month": frequency_cap.max_messages_per_month,
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize user actor: {str(e)}"
        )


@app.post("/campaigns/launch", status_code=201)
async def launch_campaign(request: LaunchCampaignRequest):
    """
    Launch a marketing campaign.

    This will:
    1. Create a Campaign workflow
    2. For each user, the workflow will query their User Actor
    3. Only send if frequency caps allow
    4. Record send in User Actor
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    # Create campaign message
    message = CampaignMessage(
        campaign_id=request.campaign_id,
        campaign_name=request.campaign_name,
        campaign_type=request.campaign_type,
        priority=request.priority,
        message_content=request.message_content,
        metadata=request.metadata,
    )

    workflow_id = f"campaign-{request.campaign_id}"

    try:
        # Start Campaign workflow
        handle = await temporal_client.start_workflow(
            CampaignWorkflow.run,
            args=[message, request.target_user_ids],
            id=workflow_id,
            task_queue="marketing-campaign-queue",
        )

        return {
            "message": "Campaign launched successfully",
            "campaign_id": request.campaign_id,
            "campaign_name": request.campaign_name,
            "workflow_id": handle.id,
            "target_users": len(request.target_user_ids),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to launch campaign: {str(e)}"
        )


@app.get("/users/{user_id}/state")
async def get_user_state(user_id: str):
    """
    Get the complete state for a user from their User Actor.

    This demonstrates querying the User Actor for state.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"user-actor-{user_id}"

    try:
        # Get User Actor handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Query state
        state: UserState = await handle.query(UserActorWorkflow.get_user_state)

        return {
            "user_id": state.user_id,
            "total_messages_sent": state.total_messages_sent,
            "last_message_time": state.last_message_time.isoformat() if state.last_message_time else None,
            "opted_out_channels": [ch.value for ch in state.opted_out_channels],
            "preferences": state.preferences,
            "recent_messages": [
                {
                    "timestamp": attempt.timestamp.isoformat(),
                    "campaign_id": attempt.campaign_id,
                    "campaign_name": attempt.campaign_name,
                    "campaign_type": attempt.campaign_type.value,
                    "success": attempt.success,
                }
                for attempt in state.message_history[-10:]  # Last 10 messages
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"User actor not found. Initialize it first: {str(e)}"
        )


@app.post("/users/{user_id}/check-frequency")
async def check_frequency(
    user_id: str,
    campaign_type: CampaignType,
    campaign_id: str = "test",
    campaign_name: str = "Test Campaign"
):
    """
    Check if a message can be sent to a user based on frequency caps.

    This demonstrates the frequency checking query.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"user-actor-{user_id}"

    try:
        # Get User Actor handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Create test message
        test_message = CampaignMessage(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            priority=CampaignPriority.MEDIUM,
            message_content="Test message",
        )

        # Query frequency check
        result: FrequencyCheckResult = await handle.query(
            UserActorWorkflow.can_send_message,
            test_message
        )

        return {
            "user_id": user_id,
            "campaign_type": campaign_type.value,
            "allowed": result.allowed,
            "reason": result.reason,
            "messages_sent_today": result.messages_sent_today,
            "messages_sent_this_week": result.messages_sent_this_week,
            "messages_sent_this_month": result.messages_sent_this_month,
            "hours_since_last_message": result.hours_since_last_message,
        }

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"User actor not found: {str(e)}"
        )


@app.post("/users/{user_id}/opt-out")
async def opt_out_channel(user_id: str, request: OptOutRequest):
    """
    Opt user out of a communication channel.

    This demonstrates signaling the User Actor to update preferences.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"user-actor-{user_id}"

    try:
        # Get User Actor handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Signal to opt out
        await handle.signal(UserActorWorkflow.opt_out_channel, request.channel)

        return {
            "message": f"User {user_id} opted out of {request.channel.value}",
            "user_id": user_id,
            "channel": request.channel.value,
        }

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"User actor not found: {str(e)}"
        )


@app.post("/users/{user_id}/opt-in")
async def opt_in_channel(user_id: str, request: OptOutRequest):
    """
    Opt user back in to a communication channel.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"user-actor-{user_id}"

    try:
        # Get User Actor handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Signal to opt in
        await handle.signal(UserActorWorkflow.opt_in_channel, request.channel)

        return {
            "message": f"User {user_id} opted in to {request.channel.value}",
            "user_id": user_id,
            "channel": request.channel.value,
        }

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"User actor not found: {str(e)}"
        )


@app.get("/campaigns/{campaign_id}/progress")
async def get_campaign_progress(campaign_id: str):
    """
    Get campaign progress.

    Query the Campaign workflow for current status.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"campaign-{campaign_id}"

    try:
        # Get Campaign handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Query progress
        progress = await handle.query(CampaignWorkflow.get_progress)

        return progress

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign not found: {str(e)}"
        )


@app.get("/campaigns/{campaign_id}/result")
async def get_campaign_result(campaign_id: str):
    """
    Get campaign final result.

    This waits for the campaign to complete and returns results.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"campaign-{campaign_id}"

    try:
        # Get Campaign handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Wait for result (with timeout)
        result = await handle.result()

        return result

    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Campaign not found: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "temporal_connected": temporal_client is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
