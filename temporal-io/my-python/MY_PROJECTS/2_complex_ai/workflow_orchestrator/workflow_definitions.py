"""
Orchestrator Workflow - Routes user messages to appropriate sub-workflows
Uses LLM to classify user intent and route to:
- code_analysis
- content_generation
- deep_research
- direct_llm (for simple questions like "Tell me a joke")
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from agents import Agent, RunConfig, Runner, trace
from pydantic import BaseModel, Field
from temporalio import activity, workflow


@dataclass
class OrchestratorRequest:
    """Request from user to orchestrator."""

    message: str
    user_id: str = "unknown"


@dataclass
class RoutingDecision:
    """Decision on which workflow to route to."""

    workflow_type: (
        str  # "code_analysis", "content_generation", "deep_research", "direct_llm"
    )
    confidence: float
    reasoning: str
    extracted_params: dict


@dataclass
class OrchestratorResult:
    """Final result from orchestrator."""

    original_message: str
    selected_workflow: str
    routing_confidence: float
    routing_reasoning: str
    result: dict
    execution_time_seconds: float


# Structured output models for LLM responses


class CodeAnalysisParams(BaseModel):
    """Parameters for code analysis workflow."""

    repository_path: str = Field(description="Path to the repository to analyze")
    analysis_type: Literal["security", "performance", "quality", "refactoring"] = Field(
        default="security", description="Type of analysis to perform"
    )


class ContentGenerationParams(BaseModel):
    """Parameters for content generation workflow."""

    topic: str = Field(description="Topic for the content")
    content_type: Literal["blog", "documentation", "marketing", "technical"] = Field(
        default="blog", description="Type of content to generate"
    )
    target_audience: str = Field(
        default="general audience", description="Target audience for the content"
    )
    tone: Literal["professional", "casual", "technical", "friendly"] = Field(
        default="professional", description="Tone of the content"
    )
    length: Literal["short", "medium", "long"] = Field(
        default="medium", description="Length of the content"
    )


class DeepResearchParams(BaseModel):
    """Parameters for deep research workflow."""

    task: str = Field(description="Research task or question")


class ClassificationOutput(BaseModel):
    """Structured output from intent classification agent."""

    workflow_type: Literal[
        "deep_research", "code_analysis", "content_generation", "direct_llm"
    ] = Field(description="The workflow to route to")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(description="Explanation of why this workflow was chosen")
    code_analysis_params: CodeAnalysisParams | None = Field(
        default=None, description="Parameters if workflow_type is code_analysis"
    )
    content_generation_params: ContentGenerationParams | None = Field(
        default=None, description="Parameters if workflow_type is content_generation"
    )
    deep_research_params: DeepResearchParams | None = Field(
        default=None, description="Parameters if workflow_type is deep_research"
    )


# Activities


@activity.defn
async def classify_user_intent(user_message: str) -> RoutingDecision:
    """Classify user intent using LLM with structured outputs to determine which workflow to use."""
    activity.logger.info(f"Classifying user intent: {user_message}")

    agent = Agent(
        name="Intent Classifier",
        model="gpt-5-mini",
        instructions="""You are an intent classification agent. Analyze the user message and determine which workflow to route to.

Available workflows:
1. **deep_research**: For research questions, investigation, analysis of topics, gathering information
   - Examples: "Research AI trends", "Investigate quantum computing", "Analyze market data"
   - Required parameters: task (the research question)

2. **code_analysis**: For code review, security analysis, repository scanning, code quality checks
   - Examples: "Analyze my repository", "Check code for security issues", "Review code quality"
   - Required parameters: repository_path, analysis_type (security/performance/quality/refactoring)

3. **content_generation**: For creating blog posts, documentation, articles, marketing content
   - Examples: "Write a blog post about X", "Create documentation for Y", "Generate article on Z"
   - Required parameters: topic, content_type, tone, target_audience, length

4. **direct_llm**: For simple questions, jokes, greetings, general chat that doesn't need a workflow
   - Examples: "Tell me a joke", "Hello", "What's the weather?", "Explain X briefly"
   - No parameters required

Analyze the user message and classify it into one of these workflows, extracting relevant parameters.""",
        output_type=ClassificationOutput,  # Structured output ensures proper format
    )

    try:
        result = await Runner.run(agent, input=user_message, run_config=RunConfig())

        # The output is guaranteed to be ClassificationOutput due to output_type
        assert isinstance(result.final_output, ClassificationOutput)
        classification = result.final_output

        # Convert structured output to RoutingDecision with extracted params
        extracted_params = {}

        if (
            classification.workflow_type == "code_analysis"
            and classification.code_analysis_params
        ):
            extracted_params = {
                "repository_path": classification.code_analysis_params.repository_path,
                "analysis_type": classification.code_analysis_params.analysis_type,
            }
        elif (
            classification.workflow_type == "content_generation"
            and classification.content_generation_params
        ):
            extracted_params = {
                "topic": classification.content_generation_params.topic,
                "content_type": classification.content_generation_params.content_type,
                "target_audience": classification.content_generation_params.target_audience,
                "tone": classification.content_generation_params.tone,
                "length": classification.content_generation_params.length,
            }
        elif (
            classification.workflow_type == "deep_research"
            and classification.deep_research_params
        ):
            extracted_params = {
                "task": classification.deep_research_params.task,
            }
        # direct_llm has no parameters

        return RoutingDecision(
            workflow_type=classification.workflow_type,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            extracted_params=extracted_params,
        )

    except Exception as e:
        activity.logger.warning(
            f"Failed to classify intent: {e}. Using direct_llm fallback."
        )
        # Default to direct LLM if classification fails
        return RoutingDecision(
            workflow_type="direct_llm",
            confidence=0.5,
            reasoning=f"Classification failed: {str(e)}. Using fallback.",
            extracted_params={},
        )


@activity.defn
async def handle_direct_llm_call(user_message: str) -> str:
    """Handle simple questions directly with LLM without a workflow."""
    activity.logger.info(f"Handling direct LLM call: {user_message}")

    agent = Agent(
        name="Direct Assistant",
        model="gpt-5-mini",
        instructions="""You are a helpful AI assistant. Answer user questions directly,
        provide jokes, have conversations, and help with simple tasks.
        Be concise, friendly, and helpful.""",
        output_type=str,  # Ensure string output
    )

    result = await Runner.run(agent, input=user_message, run_config=RunConfig())

    # Output is guaranteed to be a string due to output_type
    assert isinstance(result.final_output, str)
    return result.final_output


# Main Orchestrator Workflow


@workflow.defn
class OrchestratorWorkflow:
    """
    Orchestrator workflow that:
    1. Classifies user intent using LLM
    2. Routes to appropriate sub-workflow or handles directly
    3. Returns unified result with routing information
    """

    def __init__(self) -> None:
        self._current_status = "initializing"
        self._routing_decision: RoutingDecision | None = None
        self._sub_workflow_id: str | None = None

    @workflow.run
    async def run(self, request: OrchestratorRequest) -> OrchestratorResult:
        """Execute orchestrator workflow."""
        workflow.logger.info(f"Orchestrator received: {request.message}")

        start_time = workflow.now()

        with trace("Orchestrator workflow"):
            # Step 1: Classify user intent
            self._current_status = "classifying_intent"
            self._routing_decision = await workflow.execute_activity(
                classify_user_intent,
                args=[request.message],
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info(
                f"Routed to: {self._routing_decision.workflow_type} "
                f"(confidence: {self._routing_decision.confidence})"
            )

            # Step 2: Route to appropriate workflow or handle directly
            result = await self._handle_routing(request)

            # Step 3: Create unified result
            execution_time = (workflow.now() - start_time).total_seconds()

            final_result = OrchestratorResult(
                original_message=request.message,
                selected_workflow=self._routing_decision.workflow_type,
                routing_confidence=self._routing_decision.confidence,
                routing_reasoning=self._routing_decision.reasoning,
                result=result,
                execution_time_seconds=execution_time,
            )

        self._current_status = "completed"
        return final_result

    async def _handle_routing(self, request: OrchestratorRequest) -> dict:
        """Route to appropriate workflow based on classification."""

        if not self._routing_decision:
            raise ValueError("Routing decision not available")

        workflow_type = self._routing_decision.workflow_type
        params = self._routing_decision.extracted_params

        # Import here to avoid circular dependencies
        from workflow_code_analysis.workflow_definitions import (
            CodeAnalysisRequest,
            CodeAnalysisWorkflow,
        )
        from workflow_content_generation.workflow_definitions import (
            ContentGenerationWorkflow,
            ContentRequest,
        )
        from workflow_deep_research.workflow_definitions import (
            DeepResearchWorkflow,
            ResearchRequest,
        )

        if workflow_type == "deep_research":
            self._current_status = "executing_deep_research"
            self._sub_workflow_id = f"sub-research-{workflow.info().workflow_id}"

            research_request = ResearchRequest(
                task=params.get("task", request.message), user_id=request.user_id
            )

            result = await workflow.execute_child_workflow(
                DeepResearchWorkflow.run,
                research_request,
                id=self._sub_workflow_id,
                task_queue="complex-ai-task-queue",
            )

            return (
                result.__dict__
                if hasattr(result, "__dict__")
                else {"result": str(result)}
            )

        elif workflow_type == "code_analysis":
            self._current_status = "executing_code_analysis"
            self._sub_workflow_id = f"sub-code-{workflow.info().workflow_id}"

            code_request = CodeAnalysisRequest(
                repository_path=params.get("repository_path", "/tmp"),
                analysis_type=params.get("analysis_type", "security"),
                user_id=request.user_id,
            )

            result = await workflow.execute_child_workflow(
                CodeAnalysisWorkflow.run,
                code_request,
                id=self._sub_workflow_id,
                task_queue="complex-ai-task-queue",
            )

            return (
                result.__dict__
                if hasattr(result, "__dict__")
                else {"result": str(result)}
            )

        elif workflow_type == "content_generation":
            self._current_status = "executing_content_generation"
            self._sub_workflow_id = f"sub-content-{workflow.info().workflow_id}"

            content_request = ContentRequest(
                topic=params.get("topic", request.message),
                content_type=params.get("content_type", "blog"),
                target_audience=params.get("target_audience", "general audience"),
                tone=params.get("tone", "professional"),
                length=params.get("length", "medium"),
                user_id=request.user_id,
            )

            result = await workflow.execute_child_workflow(
                ContentGenerationWorkflow.run,
                content_request,
                id=self._sub_workflow_id,
                task_queue="complex-ai-task-queue",
            )

            return (
                result.__dict__
                if hasattr(result, "__dict__")
                else {"result": str(result)}
            )

        else:  # direct_llm
            self._current_status = "executing_direct_llm"

            response = await workflow.execute_activity(
                handle_direct_llm_call,
                args=[request.message],
                start_to_close_timeout=timedelta(seconds=30),
            )

            return {"response": response, "type": "direct_llm"}

    @workflow.query
    def get_status(self) -> dict:
        """Get current orchestrator status."""
        return {
            "current_status": self._current_status,
            "routing_decision": (
                {
                    "workflow_type": self._routing_decision.workflow_type,
                    "confidence": self._routing_decision.confidence,
                    "reasoning": self._routing_decision.reasoning,
                }
                if self._routing_decision
                else None
            ),
            "sub_workflow_id": self._sub_workflow_id,
        }

    @workflow.query
    def get_routing_decision(self) -> dict | None:
        """Get routing decision for UI display."""
        if not self._routing_decision:
            return None

        return {
            "workflow_type": self._routing_decision.workflow_type,
            "confidence": self._routing_decision.confidence,
            "reasoning": self._routing_decision.reasoning,
            "extracted_params": self._routing_decision.extracted_params,
        }
