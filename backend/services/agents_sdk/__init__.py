"""
Fabric Pipeline Agents SDK - Production Ready

Multi-agent system for designing and deploying Microsoft Fabric data pipelines.
Built on the OpenAI Agents SDK for robust orchestration and handoffs.

Usage:
    from services.agents_sdk import (
        PipelineAgentRunner,
        create_runner,
        get_runner,
        initialize_runner,
    )

    # Initialize runner on app startup
    runner = initialize_runner(
        model="gpt-4o",
        fabric_service=fabric_service,
    )

    # Run agent for user message
    response = await runner.run(
        message="I need to migrate data from PostgreSQL to Fabric",
        workspace_id="your-workspace-id",
        user_id="user-123",
    )

    print(response.message)
"""

# Context and state management
from .context import (
    PipelineContext,
    PipelineStage,
    SourceInfo,
    BusinessContext,
    TransformationNeeds,
    DestinationConfig,
    OperationalConfig,
    ArchitectureDesign,
    ContextManager,
    context_manager,
)

# Agents
from .agents import (
    orchestrator_agent,
    discovery_agent,
    source_analyst_agent,
    fabric_architect_agent,
    transform_expert_agent,
    deploy_agent,
    get_agent,
    get_entry_agent,
    get_agent_for_stage,
    AGENTS,
)

# Tools
from .tools import (
    update_source_info,
    update_business_context,
    update_schedule,
    analyze_source_requirements,
    design_architecture,
    update_transformations,
    generate_pipeline,
    get_deployment_preview,
    deploy_to_fabric,
    get_current_status,
    reset_conversation,
)

# Guardrails
from .guardrails import (
    validate_user_input,
    check_pipeline_context,
    sanitize_agent_output,
    validate_deployment_output,
    detect_pii_in_text,
    validate_workspace_id,
    sanitize_for_logging,
    STANDARD_INPUT_GUARDRAILS,
    STANDARD_OUTPUT_GUARDRAILS,
)

# Runner
from .runner import (
    PipelineAgentRunner,
    AgentResponse,
    AgentMetrics,
    RunMetrics,
    create_runner,
    get_runner,
    initialize_runner,
)

__all__ = [
    # Context
    "PipelineContext",
    "PipelineStage",
    "SourceInfo",
    "BusinessContext",
    "TransformationNeeds",
    "DestinationConfig",
    "OperationalConfig",
    "ArchitectureDesign",
    "ContextManager",
    "context_manager",
    # Agents
    "orchestrator_agent",
    "discovery_agent",
    "source_analyst_agent",
    "fabric_architect_agent",
    "transform_expert_agent",
    "deploy_agent",
    "get_agent",
    "get_entry_agent",
    "get_agent_for_stage",
    "AGENTS",
    # Tools
    "update_source_info",
    "update_business_context",
    "update_schedule",
    "analyze_source_requirements",
    "design_architecture",
    "update_transformations",
    "generate_pipeline",
    "get_deployment_preview",
    "deploy_to_fabric",
    "get_current_status",
    "reset_conversation",
    # Guardrails
    "validate_user_input",
    "check_pipeline_context",
    "sanitize_agent_output",
    "validate_deployment_output",
    "detect_pii_in_text",
    "validate_workspace_id",
    "sanitize_for_logging",
    "STANDARD_INPUT_GUARDRAILS",
    "STANDARD_OUTPUT_GUARDRAILS",
    # Runner
    "PipelineAgentRunner",
    "AgentResponse",
    "AgentMetrics",
    "RunMetrics",
    "create_runner",
    "get_runner",
    "initialize_runner",
]

__version__ = "1.0.0"
