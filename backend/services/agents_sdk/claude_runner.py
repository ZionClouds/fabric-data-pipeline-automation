"""
Claude-based Runner for Fabric Pipeline Agents

This module provides a Claude Opus 4.6 based execution engine that replaces
the OpenAI Agents SDK runner while maintaining the same multi-agent behavior.
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from anthropic import AnthropicVertex

from .context import PipelineContext, PipelineStage, context_manager
from .tools import TOOL_REGISTRY, execute_tool

import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Definitions for Claude
# ============================================================================

AGENT_PROMPTS = {
    "orchestrator": """You are the main assistant for Microsoft Fabric data pipeline design.

Your role is to:
1. Understand what the user needs
2. Route them to the appropriate specialist
3. Maintain conversation continuity
4. Provide helpful responses

ROUTING LOGIC:
- New conversations or source questions -> Use transfer_to_discovery
- Technical source details -> Use transfer_to_source_analyst
- Architecture and design -> Use transfer_to_architect
- Transformations and PII -> Use transfer_to_transform_expert
- Deployment questions -> Use transfer_to_deploy

ALWAYS:
- Be helpful and professional
- Keep responses concise
- Use tools to track progress
- Transfer to specialists for detailed work

Start by understanding what the user wants to accomplish, then route appropriately.""",

    "discovery": """You are a friendly data pipeline discovery specialist for Microsoft Fabric.

Your role is to:
1. Welcome users and understand their data pipeline needs
2. Extract key information about their data source
3. Understand their business use case and goals
4. Guide them through the initial requirements gathering

CONVERSATION STYLE:
- Be conversational and helpful, not interrogative
- Ask one or two questions at a time
- Extract information naturally from user responses
- Use the tools to record what you learn

KEY INFORMATION TO GATHER:
- Source system type (database, files, APIs, etc.)
- Source location (cloud vs on-premise)
- Volume and scale of data
- Business use case (analytics, ML, operational)
- Whether data contains PII/sensitive information
- Required frequency (one-time, daily, real-time)

WHEN TO HANDOFF:
- Once you have source type and basic use case, use transfer_to_source_analyst
- If user asks technical source questions, use transfer_to_source_analyst
- If user wants to discuss architecture, use transfer_to_architect

Always use update_source_info and update_business_context tools to record information.
Keep responses concise and focused.""",

    "source_analyst": """You are a technical data source analyst specializing in connectivity and integration.

Your role is to:
1. Perform detailed analysis of the source system
2. Determine connectivity requirements
3. Assess complexity and potential challenges
4. Recommend connection approach

FOCUS AREAS:
- Database connection requirements (ports, drivers, authentication)
- Network considerations (firewalls, VPNs, gateways)
- Data volume and performance implications
- Schema analysis and data types
- Change data capture capabilities

FOR ON-PREMISE SOURCES:
- Always mention On-Premises Data Gateway requirement
- Explain firewall considerations
- Discuss service account requirements

FOR CLOUD SOURCES:
- Authentication methods (SAS, managed identity, service principal)
- Network security (private endpoints, VNet integration)
- Cross-tenant access considerations

WHEN TO HANDOFF:
- Once source analysis is complete, use transfer_to_architect
- If user wants to discuss transformations, mention you'll transfer after architecture design

Use analyze_source_requirements to perform technical analysis.
Keep explanations clear and actionable.""",

    "fabric_architect": """You are a Microsoft Fabric data architecture expert.

Your role is to:
1. Design optimal pipeline architecture based on requirements
2. Select appropriate Fabric components
3. Apply medallion architecture patterns
4. Provide architecture recommendations

ARCHITECTURE PATTERNS:
- **Simple Copy**: Direct data movement, no transformations
- **Medallion (Silver)**: Bronze (raw) -> Silver (cleaned)
- **Medallion (Full)**: Bronze -> Silver -> Gold (analytics-ready)

COMPONENT SELECTION:
- **Copy Activity**: Direct data movement, best for simple sources
- **Dataflow Gen2**: Visual transformations, good for moderate complexity
- **Notebook**: PySpark processing, best for complex logic and large data

DESIGN PRINCIPLES:
- Start simple, add complexity only when needed
- Use Copy Activity for straightforward migrations
- Use Notebooks for PII masking and complex transformations
- Consider data volume for component selection

WHEN TO HANDOFF:
- If PII handling is needed, use transfer_to_transform_expert
- Once architecture is designed, use transfer_to_deploy for implementation

Use design_architecture tool to create the architecture.
Explain your design decisions clearly.""",

    "transform_expert": """You are a data transformation and privacy expert for Microsoft Fabric.

Your role is to:
1. Design data transformation logic
2. Implement PII/PHI masking strategies
3. Define data quality rules
4. Create aggregation logic

PII/PHI HANDLING:
- Identify sensitive columns (email, SSN, phone, name, address, etc.)
- Recommend masking techniques (hash, mask, tokenize, redact)
- Ensure compliance with HIPAA, GDPR, etc.
- Always use Notebooks for PII transformations (better control)

TRANSFORMATION TYPES:
- **Cleaning**: Null handling, deduplication, type conversion
- **Enrichment**: Lookups, derived columns, geocoding
- **Aggregation**: Sum, count, average by dimensions
- **PII Masking**: Hash, mask, encrypt sensitive data

WHEN TO HANDOFF:
- Once transformations are defined, use transfer_to_deploy
- If architecture changes are needed, use transfer_to_architect

Use update_transformations tool to record transformation requirements.
Provide specific examples when discussing transformations.""",

    "deploy": """You are a Microsoft Fabric deployment specialist.

Your role is to:
1. Generate pipeline definitions
2. Show deployment previews
3. Handle the deployment process
4. Guide post-deployment steps

DEPLOYMENT PROCESS:
1. Generate pipeline definition using generate_pipeline
2. Show preview using get_deployment_preview
3. Get explicit user confirmation
4. Deploy using deploy_to_fabric (only with confirmation!)

PREVIEW INCLUDES:
- Complete source configuration
- Pipeline architecture and activities
- Schedule configuration
- Any warnings or missing items

POST-DEPLOYMENT GUIDANCE:
- How to configure credentials in Fabric
- How to run a test execution
- How to set up monitoring
- How to enable the schedule

IMPORTANT:
- Never deploy without explicit user confirmation
- Always show preview first
- Explain what each artifact does
- Guide through credential setup

Use generate_pipeline, get_deployment_preview, and deploy_to_fabric tools.
Be thorough in explaining the deployment process.""",
}


# Tool definitions for each agent
AGENT_TOOLS = {
    "orchestrator": [
        "update_source_info", "update_business_context", "update_schedule",
        "get_current_status", "reset_conversation",
        "transfer_to_discovery", "transfer_to_source_analyst", "transfer_to_architect",
        "transfer_to_transform_expert", "transfer_to_deploy",
    ],
    "discovery": [
        "update_source_info", "update_business_context", "update_schedule",
        "get_current_status", "reset_conversation",
        "transfer_to_source_analyst", "transfer_to_architect",
    ],
    "source_analyst": [
        "update_source_info", "analyze_source_requirements", "get_current_status",
        "transfer_to_architect", "transfer_to_discovery",
    ],
    "fabric_architect": [
        "design_architecture", "update_business_context", "update_schedule", "get_current_status",
        "transfer_to_transform_expert", "transfer_to_deploy", "transfer_to_source_analyst",
    ],
    "transform_expert": [
        "update_transformations", "update_business_context", "get_current_status",
        "transfer_to_deploy", "transfer_to_architect",
    ],
    "deploy": [
        "generate_pipeline", "get_deployment_preview", "deploy_to_fabric", "get_current_status",
        "transfer_to_architect", "transfer_to_transform_expert", "start_new_pipeline",
    ],
}


# Claude tool definitions
def get_claude_tools(agent_name: str) -> List[Dict[str, Any]]:
    """Get Claude-formatted tool definitions for an agent."""
    tool_names = AGENT_TOOLS.get(agent_name, [])
    tools = []

    # Add regular tools from registry
    for name in tool_names:
        if name.startswith("transfer_to_") or name == "start_new_pipeline":
            # Handoff tools
            target = name.replace("transfer_to_", "").replace("start_new_pipeline", "discovery")
            tools.append({
                "name": name,
                "description": f"Transfer conversation to {target} agent for specialized handling",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Brief reason for the transfer"
                        }
                    },
                    "required": []
                }
            })
        elif name in TOOL_REGISTRY:
            tool_def = TOOL_REGISTRY[name]
            tools.append({
                "name": name,
                "description": tool_def.get("description", f"Execute {name}"),
                "input_schema": tool_def.get("input_schema", {"type": "object", "properties": {}})
            })

    return tools


# ============================================================================
# Metrics and Response Classes
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
            "llm_provider": "vertex_claude",
            "model": settings.CLAUDE_MODEL,
        }


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
# Claude Pipeline Runner
# ============================================================================

class ClaudePipelineRunner:
    """
    Production-ready runner for the Fabric pipeline agent system using Claude.

    Features:
    - Claude Opus 4.6 via Vertex AI
    - Context management across sessions
    - Automatic agent routing based on stage
    - Tool execution and handoffs
    - Metrics collection
    """

    def __init__(
        self,
        project_id: str = None,
        region: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        fabric_service: Optional[Any] = None,
    ):
        self.project_id = project_id or settings.GCP_PROJECT_ID
        self.region = region or settings.GCP_REGION
        self.model = model or settings.CLAUDE_MODEL
        self.temperature = temperature if temperature is not None else settings.CLAUDE_TEMPERATURE
        self.max_tokens = max_tokens or settings.CLAUDE_MAX_TOKENS
        self.fabric_service = fabric_service
        self._run_count = 0

        # Initialize Claude client
        self.client = AnthropicVertex(
            project_id=self.project_id,
            region=self.region,
        )

        logger.info(
            f"Claude Pipeline Runner initialized: "
            f"model={self.model}, region={self.region}"
        )

    def _get_run_id(self) -> str:
        """Generate unique run ID"""
        self._run_count += 1
        return f"claude_run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{self._run_count}"

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

    def _select_agent(self, context: PipelineContext, message: str) -> str:
        """Select the appropriate agent based on context and message"""
        message_lower = message.lower()

        # Check for explicit routing keywords
        if any(word in message_lower for word in ["start over", "reset", "new pipeline"]):
            context.stage = PipelineStage.INITIAL
            return "orchestrator"

        if any(word in message_lower for word in ["deploy", "create pipeline", "generate"]):
            if context.architecture.pattern:
                return "deploy"

        if any(word in message_lower for word in ["transform", "mask", "pii", "clean"]):
            return "transform_expert"

        if any(word in message_lower for word in ["architecture", "design", "pattern", "medallion"]):
            return "fabric_architect"

        if any(word in message_lower for word in ["connect", "gateway", "network", "credentials"]):
            return "source_analyst"

        # Default: route based on current stage
        stage_agent_map = {
            PipelineStage.INITIAL: "orchestrator",
            PipelineStage.DISCOVERY: "discovery",
            PipelineStage.ANALYZING: "source_analyst",
            PipelineStage.DESIGNING: "fabric_architect",
            PipelineStage.REVIEWING: "deploy",
            PipelineStage.DEPLOYING: "deploy",
            PipelineStage.COMPLETED: "orchestrator",
        }
        return stage_agent_map.get(context.stage, "orchestrator")

    def _build_messages(
        self,
        context: PipelineContext,
        user_message: str,
    ) -> List[Dict[str, Any]]:
        """Build message history for Claude"""
        messages = []

        # Add conversation history (last 10 turns)
        for turn in context.conversation_history[-10:]:
            messages.append({
                "role": turn["role"],
                "content": turn["content"],
            })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message,
        })

        return messages

    def _build_system_prompt(self, agent_name: str, context: PipelineContext) -> str:
        """Build system prompt with context"""
        base_prompt = AGENT_PROMPTS.get(agent_name, AGENT_PROMPTS["orchestrator"])

        # Add context summary
        context_info = f"""

CURRENT CONTEXT:
- Stage: {context.stage.value}
- Source Type: {context.source.source_type or 'Not specified'}
- Tables: {', '.join(context.source.tables) if context.source.tables else 'Not specified'}
- Architecture: {context.architecture.pattern or 'Not designed'}
- Has PII: {context.transformations.pii_columns is not None}
- Workspace: {context.workspace_id}
- Lakehouse: {context.lakehouse_name or 'Not specified'}
"""
        return base_prompt + context_info

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        context: PipelineContext,
    ) -> str:
        """Execute a tool and return result"""
        # Handle handoff tools
        if tool_name.startswith("transfer_to_") or tool_name == "start_new_pipeline":
            target = tool_name.replace("transfer_to_", "").replace("start_new_pipeline", "discovery")
            return json.dumps({"handoff": target, "reason": tool_input.get("reason", "User request")})

        # Execute regular tool
        try:
            result = await execute_tool(tool_name, tool_input, context)
            return json.dumps(result) if isinstance(result, dict) else str(result)
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return json.dumps({"error": str(e)})

    async def run(
        self,
        message: str,
        workspace_id: str,
        user_id: str,
        lakehouse_name: Optional[str] = None,
        warehouse_name: Optional[str] = None,
    ) -> AgentResponse:
        """
        Execute agent pipeline for a user message using Claude.
        """
        run_id = self._get_run_id()
        start_time = time.time()

        metrics = RunMetrics(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
            start_time=start_time,
        )

        logger.info(f"[{run_id}] Starting Claude agent run for user {user_id}")

        try:
            # Get or create context
            context = self._get_context(
                workspace_id=workspace_id,
                user_id=user_id,
                lakehouse_name=lakehouse_name,
                warehouse_name=warehouse_name,
            )

            # Extract information from message
            context.update_from_message(message)

            # Select appropriate agent
            current_agent = self._select_agent(context, message)
            logger.info(f"[{run_id}] Selected agent: {current_agent}")

            # Add user message to history
            context.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Agent loop (handle handoffs)
            max_iterations = 5
            iteration = 0
            final_response = ""

            while iteration < max_iterations:
                iteration += 1
                agent_metrics = AgentMetrics(
                    agent_name=current_agent,
                    start_time=time.time(),
                )

                # Build request
                system_prompt = self._build_system_prompt(current_agent, context)
                messages = self._build_messages(context, message)
                tools = get_claude_tools(current_agent)

                # Call Claude
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=messages,
                    tools=tools if tools else None,
                )

                # Update metrics
                agent_metrics.input_tokens = response.usage.input_tokens
                agent_metrics.output_tokens = response.usage.output_tokens
                metrics.total_input_tokens += response.usage.input_tokens
                metrics.total_output_tokens += response.usage.output_tokens

                # Process response
                handoff_target = None
                text_response = ""

                for block in response.content:
                    if block.type == "text":
                        text_response += block.text
                    elif block.type == "tool_use":
                        agent_metrics.tool_calls += 1
                        tool_result = await self._execute_tool(
                            block.name,
                            block.input,
                            context,
                        )

                        # Check for handoff
                        try:
                            result_data = json.loads(tool_result)
                            if "handoff" in result_data:
                                handoff_target = result_data["handoff"]
                                agent_metrics.handoffs += 1
                        except:
                            pass

                agent_metrics.end_time = time.time()
                metrics.agent_metrics.append(agent_metrics)

                # Handle handoff or finish
                if handoff_target:
                    current_agent = handoff_target
                    logger.info(f"[{run_id}] Handoff to {handoff_target}")
                    # Continue loop with new agent
                else:
                    final_response = text_response
                    break

            # Add response to history
            context.conversation_history.append({
                "role": "assistant",
                "content": final_response,
                "timestamp": datetime.utcnow().isoformat(),
                "agent": current_agent,
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

            logger.info(f"[{run_id}] Run completed in {metrics.total_duration_ms:.0f}ms")

            return AgentResponse(
                success=True,
                message=final_response,
                agent_name=current_agent,
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

_runner: Optional[ClaudePipelineRunner] = None


def get_runner() -> ClaudePipelineRunner:
    """Get the global runner instance"""
    global _runner
    if _runner is None:
        _runner = ClaudePipelineRunner()
    return _runner


def create_runner(
    project_id: str = None,
    region: str = None,
    model: str = None,
    temperature: float = None,
    max_tokens: int = None,
    fabric_service: Optional[Any] = None,
) -> ClaudePipelineRunner:
    """Create a configured Claude pipeline runner"""
    return ClaudePipelineRunner(
        project_id=project_id,
        region=region,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        fabric_service=fabric_service,
    )


def initialize_runner(
    project_id: str = None,
    region: str = None,
    model: str = None,
    temperature: float = None,
    max_tokens: int = None,
    fabric_service: Optional[Any] = None,
) -> ClaudePipelineRunner:
    """Initialize the global runner instance with Claude"""
    global _runner
    _runner = create_runner(
        project_id=project_id,
        region=region,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        fabric_service=fabric_service,
    )
    logger.info(f"Claude Pipeline Runner initialized with model: {_runner.model}")
    return _runner
