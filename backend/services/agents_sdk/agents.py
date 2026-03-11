"""
Multi-Agent System for Fabric Pipeline Design - Production Ready

This module defines specialized agents that collaborate to design and deploy
Microsoft Fabric data pipelines. Uses OpenAI Agents SDK for orchestration.
"""

from typing import List, Optional
import logging

from agents import Agent, handoff, RunContextWrapper

from .context import PipelineContext, PipelineStage
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

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Definitions (without handoffs first)
# ============================================================================

# Discovery Agent - Entry point for conversations
discovery_agent: Agent[PipelineContext] = Agent[PipelineContext](
    name="Discovery Agent",
    instructions="""You are a friendly data pipeline discovery specialist for Microsoft Fabric.

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
- Once you have source type and basic use case, transfer to Source Analyst for deeper analysis
- If user asks technical source questions, transfer to Source Analyst
- If user wants to discuss architecture, transfer to Fabric Architect

Always use update_source_info and update_business_context tools to record information.
Keep responses concise and focused.""",
    tools=[
        update_source_info,
        update_business_context,
        update_schedule,
        get_current_status,
        reset_conversation,
    ],
)


# Source Analyst Agent - Deep dive into source systems
source_analyst_agent: Agent[PipelineContext] = Agent[PipelineContext](
    name="Source Analyst",
    instructions="""You are a technical data source analyst specializing in connectivity and integration.

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
- Once source analysis is complete, transfer to Fabric Architect
- If user wants to discuss transformations, mention you'll transfer to Transform Expert after architecture design

Use analyze_source_requirements to perform technical analysis.
Keep explanations clear and actionable.""",
    tools=[
        update_source_info,
        analyze_source_requirements,
        get_current_status,
    ],
)


# Fabric Architect Agent - Design pipeline architecture
fabric_architect_agent: Agent[PipelineContext] = Agent[PipelineContext](
    name="Fabric Architect",
    instructions="""You are a Microsoft Fabric data architecture expert.

Your role is to:
1. Design optimal pipeline architecture based on requirements
2. Select appropriate Fabric components
3. Apply medallion architecture patterns
4. Provide architecture recommendations

ARCHITECTURE PATTERNS:
- **Simple Copy**: Direct data movement, no transformations
- **Medallion (Silver)**: Bronze (raw) -> Silver (cleaned)
- **Medallion (Full)**: Bronze -> Silver -> Gold (analytics-ready)
- **Streaming**: Real-time data processing

COMPONENT SELECTION:
- **Copy Activity**: Direct data movement, best for simple sources
- **Dataflow Gen2**: Visual transformations, good for moderate complexity
- **Notebook**: PySpark processing, best for complex logic and large data

DESIGN PRINCIPLES:
- Start simple, add complexity only when needed
- Use Copy Activity for straightforward migrations
- Use Notebooks for PII masking and complex transformations
- Use Dataflow Gen2 for business user-friendly transformations
- Consider data volume for component selection

WHEN TO HANDOFF:
- If PII handling is needed, transfer to Transform Expert
- Once architecture is designed, transfer to Deploy Agent for implementation

Use design_architecture tool to create the architecture.
Explain your design decisions clearly.""",
    tools=[
        design_architecture,
        update_business_context,
        update_schedule,
        get_current_status,
    ],
)


# Transform Expert Agent - Handle transformations and PII
transform_expert_agent: Agent[PipelineContext] = Agent[PipelineContext](
    name="Transform Expert",
    instructions="""You are a data transformation and privacy expert for Microsoft Fabric.

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

NOTEBOOK CODE PATTERNS:
- Use PySpark for scalable transformations
- Implement idempotent operations
- Add data quality checks
- Log transformation metrics

WHEN TO HANDOFF:
- Once transformations are defined, transfer to Deploy Agent
- If architecture changes are needed, transfer to Fabric Architect

Use update_transformations tool to record transformation requirements.
Provide specific examples when discussing transformations.""",
    tools=[
        update_transformations,
        update_business_context,
        get_current_status,
    ],
)


# Deploy Agent - Generate and deploy pipeline
deploy_agent: Agent[PipelineContext] = Agent[PipelineContext](
    name="Deploy Agent",
    instructions="""You are a Microsoft Fabric deployment specialist.

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
    tools=[
        generate_pipeline,
        get_deployment_preview,
        deploy_to_fabric,
        get_current_status,
    ],
)


# Orchestrator Agent - Main entry point with routing capability
orchestrator_agent: Agent[PipelineContext] = Agent[PipelineContext](
    name="Fabric Pipeline Assistant",
    instructions="""You are the main assistant for Microsoft Fabric data pipeline design.

Your role is to:
1. Understand what the user needs
2. Route them to the appropriate specialist
3. Maintain conversation continuity
4. Provide helpful responses

ROUTING LOGIC:
- New conversations or source questions -> Discovery Agent
- Technical source details -> Source Analyst
- Architecture and design -> Fabric Architect
- Transformations and PII -> Transform Expert
- Deployment questions -> Deploy Agent

ALWAYS:
- Be helpful and professional
- Keep responses concise
- Use tools to track progress
- Transfer to specialists for detailed work

Start by understanding what the user wants to accomplish, then route appropriately.""",
    tools=[
        update_source_info,
        update_business_context,
        update_schedule,
        get_current_status,
        reset_conversation,
    ],
)


# ============================================================================
# Add Handoffs After All Agents Are Defined
# ============================================================================

# Discovery Agent handoffs
discovery_agent.handoffs = [
    handoff(
        agent=source_analyst_agent,
        tool_name_override="transfer_to_source_analyst",
        tool_description_override="Transfer to Source Analyst for detailed source system analysis"
    ),
    handoff(
        agent=fabric_architect_agent,
        tool_name_override="transfer_to_architect",
        tool_description_override="Transfer to Fabric Architect for pipeline design"
    ),
]

# Source Analyst Agent handoffs
source_analyst_agent.handoffs = [
    handoff(
        agent=fabric_architect_agent,
        tool_name_override="transfer_to_architect",
        tool_description_override="Transfer to Fabric Architect for pipeline design"
    ),
    handoff(
        agent=discovery_agent,
        tool_name_override="transfer_to_discovery",
        tool_description_override="Return to Discovery for more requirements gathering"
    ),
]

# Fabric Architect Agent handoffs
fabric_architect_agent.handoffs = [
    handoff(
        agent=transform_expert_agent,
        tool_name_override="transfer_to_transform_expert",
        tool_description_override="Transfer to Transform Expert for transformation design"
    ),
    handoff(
        agent=deploy_agent,
        tool_name_override="transfer_to_deploy",
        tool_description_override="Transfer to Deploy Agent for pipeline generation"
    ),
    handoff(
        agent=source_analyst_agent,
        tool_name_override="transfer_to_source_analyst",
        tool_description_override="Return to Source Analyst for more technical details"
    ),
]

# Transform Expert Agent handoffs
transform_expert_agent.handoffs = [
    handoff(
        agent=deploy_agent,
        tool_name_override="transfer_to_deploy",
        tool_description_override="Transfer to Deploy Agent for pipeline generation"
    ),
    handoff(
        agent=fabric_architect_agent,
        tool_name_override="transfer_to_architect",
        tool_description_override="Return to Fabric Architect to adjust architecture"
    ),
]

# Deploy Agent handoffs
deploy_agent.handoffs = [
    handoff(
        agent=fabric_architect_agent,
        tool_name_override="transfer_to_architect",
        tool_description_override="Return to Fabric Architect to modify design"
    ),
    handoff(
        agent=transform_expert_agent,
        tool_name_override="transfer_to_transform_expert",
        tool_description_override="Return to Transform Expert to modify transformations"
    ),
    handoff(
        agent=discovery_agent,
        tool_name_override="start_new_pipeline",
        tool_description_override="Start designing a new pipeline"
    ),
]

# Orchestrator Agent handoffs
orchestrator_agent.handoffs = [
    handoff(
        agent=discovery_agent,
        tool_name_override="start_discovery",
        tool_description_override="Start requirements gathering with Discovery Agent"
    ),
    handoff(
        agent=source_analyst_agent,
        tool_name_override="analyze_source",
        tool_description_override="Get detailed source analysis from Source Analyst"
    ),
    handoff(
        agent=fabric_architect_agent,
        tool_name_override="design_pipeline",
        tool_description_override="Design pipeline architecture with Fabric Architect"
    ),
    handoff(
        agent=transform_expert_agent,
        tool_name_override="design_transforms",
        tool_description_override="Design transformations with Transform Expert"
    ),
    handoff(
        agent=deploy_agent,
        tool_name_override="deploy_pipeline",
        tool_description_override="Generate and deploy pipeline with Deploy Agent"
    ),
]


# ============================================================================
# Agent Registry
# ============================================================================

# Map agent names to agent objects for easy lookup
AGENTS = {
    "orchestrator": orchestrator_agent,
    "discovery": discovery_agent,
    "source_analyst": source_analyst_agent,
    "fabric_architect": fabric_architect_agent,
    "transform_expert": transform_expert_agent,
    "deploy": deploy_agent,
}


def get_agent(name: str) -> Optional[Agent]:
    """Get agent by name"""
    return AGENTS.get(name)


def get_entry_agent() -> Agent:
    """Get the main entry point agent"""
    return orchestrator_agent


def get_agent_for_stage(stage: PipelineStage) -> Agent:
    """Get the appropriate agent for a pipeline stage"""
    stage_agent_map = {
        PipelineStage.INITIAL: orchestrator_agent,
        PipelineStage.DISCOVERY: discovery_agent,
        PipelineStage.ANALYZING: source_analyst_agent,
        PipelineStage.DESIGNING: fabric_architect_agent,
        PipelineStage.REVIEWING: deploy_agent,
        PipelineStage.DEPLOYING: deploy_agent,
        PipelineStage.COMPLETED: orchestrator_agent,
    }
    return stage_agent_map.get(stage, orchestrator_agent)
