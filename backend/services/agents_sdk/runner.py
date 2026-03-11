"""
Production Runner for Fabric Pipeline Agents

This module provides the main execution engine for running the multi-agent
pipeline design system with tracing, monitoring, and error handling.
"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from agents import Runner, Agent, RunConfig, ModelSettings, set_default_openai_client
from agents.tracing import TracingProcessor, Span, Trace
from agents.items import ModelResponse
from openai import AzureOpenAI

from .context import PipelineContext, PipelineStage, context_manager
from .agents import get_entry_agent, get_agent_for_stage, AGENTS
from .guardrails import (
    STANDARD_INPUT_GUARDRAILS,
    STANDARD_OUTPUT_GUARDRAILS,
    sanitize_for_logging,
)

# Import settings for Azure OpenAI configuration
import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Azure OpenAI Configuration
# ============================================================================

def _initialize_azure_openai():
    """Initialize Azure OpenAI client and set as default for agents SDK"""
    try:
        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        set_default_openai_client(client)
        logger.info(f"Azure OpenAI client initialized with endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI client: {e}")
        raise

# Initialize Azure OpenAI on module load
_azure_client = _initialize_azure_openai()


# ============================================================================
# Tracing and Monitoring
# ============================================================================

@dataclass
class AgentMetrics:
    """Metrics for agent execution"""
    agent_name: str
    start_time: float
    end_time: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    handoffs: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "duration_ms": self.duration_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "tool_calls": self.tool_calls,
            "handoffs": self.handoffs,
            "errors": self.errors,
        }


@dataclass
class RunMetrics:
    """Metrics for a complete run"""
    run_id: str
    workspace_id: str
    user_id: str
    start_time: float
    end_time: Optional[float] = None
    agent_metrics: List[AgentMetrics] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    final_stage: Optional[str] = None
    success: bool = False
    error: Optional[str] = None

    @property
    def total_duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "total_duration_ms": self.total_duration_ms,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "agent_metrics": [m.to_dict() for m in self.agent_metrics],
            "final_stage": self.final_stage,
            "success": self.success,
            "error": self.error,
        }


class PipelineTracingProcessor(TracingProcessor):
    """Custom tracing processor for pipeline metrics"""

    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.current_metrics: Optional[RunMetrics] = None

    def on_trace_start(self, trace: Trace) -> None:
        self.traces[trace.trace_id] = trace
        logger.debug(f"Trace started: {trace.trace_id}")

    def on_trace_end(self, trace: Trace) -> None:
        logger.debug(f"Trace ended: {trace.trace_id}")

    def on_span_start(self, span: Span) -> None:
        logger.debug(f"Span started: {span.span_id} - {span.span_data}")

    def on_span_end(self, span: Span) -> None:
        logger.debug(f"Span ended: {span.span_id}")

        # Extract metrics from span
        if self.current_metrics and hasattr(span, 'span_data'):
            data = span.span_data
            if hasattr(data, 'input_tokens'):
                self.current_metrics.total_input_tokens += data.input_tokens or 0
            if hasattr(data, 'output_tokens'):
                self.current_metrics.total_output_tokens += data.output_tokens or 0

    def shutdown(self) -> None:
        """Shutdown the tracing processor"""
        self.traces.clear()
        self.current_metrics = None
        logger.debug("Tracing processor shutdown")

    def force_flush(self) -> None:
        """Force flush any pending traces"""
        logger.debug("Tracing processor force flush")


# Global tracing processor
_tracing_processor = PipelineTracingProcessor()


# ============================================================================
# Response Classes
# ============================================================================

@dataclass
class AgentResponse:
    """Response from agent execution"""
    success: bool
    message: str
    agent_name: str
    stage: str
    context_summary: str
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    pipeline_ready: bool = False
    deployment_preview: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "message": self.message,
            "agent_name": self.agent_name,
            "stage": self.stage,
            "context_summary": self.context_summary,
            "pipeline_ready": self.pipeline_ready,
        }
        if self.metrics:
            result["metrics"] = self.metrics
        if self.error:
            result["error"] = self.error
        if self.deployment_preview:
            result["deployment_preview"] = self.deployment_preview
        return result


# ============================================================================
# Pipeline Runner
# ============================================================================

class PipelineAgentRunner:
    """
    Production-ready runner for the Fabric pipeline agent system.

    Features:
    - Context management across sessions
    - Automatic agent routing based on stage
    - Tracing and metrics collection
    - Error handling and recovery
    - Guardrails integration
    """

    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        fabric_service: Optional[Any] = None,
    ):
        # Use Azure OpenAI settings as defaults
        self.model = model or settings.AZURE_OPENAI_DEPLOYMENT
        self.temperature = temperature if temperature is not None else settings.AZURE_OPENAI_TEMPERATURE
        self.max_tokens = max_tokens or settings.AZURE_OPENAI_MAX_TOKENS
        self.fabric_service = fabric_service
        self._run_count = 0

    def _get_run_id(self) -> str:
        """Generate unique run ID"""
        self._run_count += 1
        return f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self._run_count}"

    def _get_context(
        self,
        workspace_id: str,
        user_id: str,
        lakehouse_name: Optional[str] = None,
        warehouse_name: Optional[str] = None,
    ) -> PipelineContext:
        """Get or create pipeline context"""
        return context_manager.get_context(
            workspace_id=workspace_id,
            user_id=user_id,
            lakehouse_name=lakehouse_name,
            warehouse_name=warehouse_name,
            fabric_service=self.fabric_service,
        )

    def _select_agent(self, context: PipelineContext, message: str) -> Agent:
        """Select the appropriate agent based on context and message"""
        message_lower = message.lower()

        # Check for explicit routing keywords
        if any(word in message_lower for word in ["start over", "reset", "new pipeline"]):
            context.stage = PipelineStage.INITIAL
            return get_entry_agent()

        if any(word in message_lower for word in ["deploy", "create pipeline", "generate"]):
            if context.architecture.pattern:
                return AGENTS["deploy"]

        if any(word in message_lower for word in ["transform", "mask", "pii", "clean"]):
            return AGENTS["transform_expert"]

        if any(word in message_lower for word in ["architecture", "design", "pattern", "medallion"]):
            return AGENTS["fabric_architect"]

        if any(word in message_lower for word in ["connect", "gateway", "network", "credentials"]):
            return AGENTS["source_analyst"]

        # Default: route based on current stage
        return get_agent_for_stage(context.stage)

    async def run(
        self,
        message: str,
        workspace_id: str,
        user_id: str,
        lakehouse_name: Optional[str] = None,
        warehouse_name: Optional[str] = None,
    ) -> AgentResponse:
        """
        Execute agent pipeline for a user message.

        Args:
            message: User's input message
            workspace_id: Fabric workspace ID
            user_id: User identifier
            lakehouse_name: Optional lakehouse name
            warehouse_name: Optional warehouse name

        Returns:
            AgentResponse with the result
        """
        run_id = self._get_run_id()
        start_time = time.time()

        metrics = RunMetrics(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
            start_time=start_time,
        )
        _tracing_processor.current_metrics = metrics

        logger.info(f"[{run_id}] Starting agent run for user {user_id}")
        logger.debug(f"[{run_id}] Message: {sanitize_for_logging(message)}")

        try:
            # Get or create context
            context = self._get_context(
                workspace_id=workspace_id,
                user_id=user_id,
                lakehouse_name=lakehouse_name,
                warehouse_name=warehouse_name,
            )

            # Extract information from message
            extracted = context.update_from_message(message)
            if extracted:
                logger.info(f"[{run_id}] Extracted from message: {extracted}")

            # Select appropriate agent
            agent = self._select_agent(context, message)
            logger.info(f"[{run_id}] Selected agent: {agent.name}")

            # Configure the run
            run_config = RunConfig(
                model=self.model,
                model_settings=ModelSettings(
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                ),
                tracing_disabled=False,
            )

            # Add conversation to history
            context.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Run the agent
            agent_metrics = AgentMetrics(
                agent_name=agent.name,
                start_time=time.time(),
            )

            result = await Runner.run(
                starting_agent=agent,
                input=message,
                context=context,
                run_config=run_config,
            )

            agent_metrics.end_time = time.time()

            # Extract response
            response_text = ""
            if result.final_output:
                response_text = str(result.final_output)
            elif result.new_items:
                # Get the last model response
                for item in reversed(result.new_items):
                    if hasattr(item, 'content'):
                        response_text = str(item.content)
                        break

            # Count tool calls from result
            if hasattr(result, 'new_items'):
                for item in result.new_items:
                    if hasattr(item, 'type') and 'tool' in str(item.type).lower():
                        agent_metrics.tool_calls += 1

            metrics.agent_metrics.append(agent_metrics)

            # Add response to history
            context.conversation_history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": agent.name,
            })

            # Determine if pipeline is ready
            pipeline_ready = (
                context.architecture.pattern is not None and
                context.stage in [PipelineStage.REVIEWING, PipelineStage.COMPLETED]
            )

            # Build deployment preview if ready
            deployment_preview = None
            if pipeline_ready:
                deployment_preview = context.to_dict()

            metrics.end_time = time.time()
            metrics.final_stage = context.stage.value
            metrics.success = True

            logger.info(f"[{run_id}] Run completed successfully in {metrics.total_duration_ms:.0f}ms")

            return AgentResponse(
                success=True,
                message=response_text,
                agent_name=result.last_agent.name if result.last_agent else agent.name,
                stage=context.stage.value,
                context_summary=context.get_summary(),
                metrics=metrics.to_dict(),
                pipeline_ready=pipeline_ready,
                deployment_preview=deployment_preview,
            )

        except Exception as e:
            metrics.end_time = time.time()
            metrics.success = False
            metrics.error = str(e)

            logger.error(f"[{run_id}] Agent run failed: {e}")
            logger.debug(traceback.format_exc())

            return AgentResponse(
                success=False,
                message="I encountered an error processing your request. Please try again.",
                agent_name="error_handler",
                stage=PipelineStage.INITIAL.value,
                context_summary="Error occurred",
                error=str(e),
                metrics=metrics.to_dict(),
            )

    async def run_streaming(
        self,
        message: str,
        workspace_id: str,
        user_id: str,
        lakehouse_name: Optional[str] = None,
        warehouse_name: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Execute agent pipeline with streaming response.

        Yields response chunks as they become available.
        """
        run_id = self._get_run_id()
        logger.info(f"[{run_id}] Starting streaming agent run")

        try:
            # Get context
            context = self._get_context(
                workspace_id=workspace_id,
                user_id=user_id,
                lakehouse_name=lakehouse_name,
                warehouse_name=warehouse_name,
            )

            # Extract and select agent
            context.update_from_message(message)
            agent = self._select_agent(context, message)

            # Configure streaming run
            run_config = RunConfig(
                model=self.model,
                model_settings=ModelSettings(
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                ),
            )

            # Run with streaming
            async for chunk in Runner.run_streamed(
                starting_agent=agent,
                input=message,
                context=context,
                run_config=run_config,
            ):
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                elif hasattr(chunk, 'content') and chunk.content:
                    yield str(chunk.content)

        except Exception as e:
            logger.error(f"[{run_id}] Streaming run failed: {e}")
            yield f"\n\nError: {str(e)}"

    def clear_context(self, workspace_id: str, user_id: str) -> bool:
        """Clear context for a user/workspace"""
        return context_manager.clear_context(workspace_id, user_id)

    def get_context_summary(self, workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current context summary"""
        if context_manager.has_context(workspace_id, user_id):
            ctx = context_manager.get_context(workspace_id, user_id)
            return ctx.to_dict()
        return None


# ============================================================================
# Factory Functions
# ============================================================================

def create_runner(
    model: str = None,
    temperature: float = None,
    max_tokens: int = None,
    fabric_service: Optional[Any] = None,
) -> PipelineAgentRunner:
    """Create a configured pipeline agent runner using Azure OpenAI settings"""
    return PipelineAgentRunner(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        fabric_service=fabric_service,
    )


# Global runner instance (can be initialized on startup)
_runner: Optional[PipelineAgentRunner] = None


def get_runner() -> PipelineAgentRunner:
    """Get the global runner instance"""
    global _runner
    if _runner is None:
        _runner = create_runner()
    return _runner


def initialize_runner(
    model: str = None,
    temperature: float = None,
    max_tokens: int = None,
    fabric_service: Optional[Any] = None,
) -> PipelineAgentRunner:
    """Initialize the global runner instance with Azure OpenAI settings"""
    global _runner
    _runner = create_runner(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        fabric_service=fabric_service,
    )
    actual_model = _runner.model
    logger.info(f"Pipeline Agent Runner initialized with Azure OpenAI model: {actual_model}")
    return _runner
