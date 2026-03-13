"""
Fabric Pipeline Tools - Production Ready

Function tools for Microsoft Fabric pipeline design and deployment.
These tools are used by agents to interact with the pipeline context and Fabric APIs.
"""

from typing import Dict, Any, List, Optional
import logging
import json

from agents import function_tool, RunContextWrapper
from .context import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


# ============================================================================
# Discovery & Information Extraction Tools
# ============================================================================

@function_tool
def update_source_info(
    ctx: RunContextWrapper[PipelineContext],
    source_type: str,
    location: Optional[str] = None,
    database_name: Optional[str] = None,
    host: Optional[str] = None,
    tables: Optional[List[str]] = None,
    volume_gb: Optional[float] = None,
    change_pattern: Optional[str] = None,
) -> str:
    """
    Update source system information based on user input.
    Call this when the user provides details about their data source.

    Args:
        source_type: Type of source (postgresql, sql_server, mysql, oracle, blob_storage, sharepoint, rest_api, snowflake, databricks)
        location: Where source is hosted (cloud, on_premise)
        database_name: Name of the database
        host: Host/server address
        tables: List of tables to migrate
        volume_gb: Estimated data volume in GB
        change_pattern: How data changes (static, insert_only, updates, deletes)
    """
    context = ctx.context
    context.source.type = source_type
    if location:
        context.source.location = location
    if database_name:
        context.source.database = database_name
    if host:
        context.source.host = host
    if tables:
        context.source.objects = tables
    if volume_gb:
        context.source.volume_gb = volume_gb
    if change_pattern:
        context.source.change_pattern = change_pattern

    context.stage = PipelineStage.DISCOVERY
    logger.info(f"Updated source info: {source_type} ({location})")

    result = f"Source information recorded: {source_type}"
    if location:
        result += f" hosted {location}"
    if database_name:
        result += f", database: {database_name}"
    return result


@function_tool
def update_business_context(
    ctx: RunContextWrapper[PipelineContext],
    use_case: str,
    consumers: Optional[List[str]] = None,
    has_pii: bool = False,
    compliance_requirements: Optional[List[str]] = None,
    criticality: Optional[str] = None,
    sla_hours: Optional[int] = None,
) -> str:
    """
    Update business context and use case information.
    Call this when the user describes what they want to do with the data.

    Args:
        use_case: Primary use case (analytics, ml, operational, archive)
        consumers: Who will use the data (power_bi, data_scientists, applications, reports)
        has_pii: Whether data contains PII/PHI
        compliance_requirements: Compliance needs (hipaa, gdpr, sox, pci)
        criticality: Project criticality (poc, development, production)
        sla_hours: Required data freshness in hours
    """
    context = ctx.context
    context.business.use_case = use_case
    if consumers:
        context.business.consumers = consumers
    context.business.pii_likely = has_pii
    if compliance_requirements:
        context.business.compliance_requirements = compliance_requirements
    if criticality:
        context.business.criticality = criticality
    if sla_hours:
        context.business.sla_hours = sla_hours

    logger.info(f"Updated business context: {use_case}, PII: {has_pii}")

    pii_note = " (PII handling required)" if has_pii else ""
    consumers_str = f" for {', '.join(consumers)}" if consumers else ""
    return f"Business context recorded: {use_case}{consumers_str}{pii_note}"


@function_tool
def update_schedule(
    ctx: RunContextWrapper[PipelineContext],
    frequency: str,
    schedule_time: Optional[str] = None,
    timezone: Optional[str] = "UTC",
) -> str:
    """
    Update pipeline scheduling requirements.
    Call this when the user specifies how often the pipeline should run.

    Args:
        frequency: How often to run (manual, hourly, daily, weekly, realtime)
        schedule_time: When to run (e.g., "2:00 AM", "every 6 hours")
        timezone: Timezone for schedule (default: UTC)
    """
    context = ctx.context
    context.operations.frequency = frequency
    if schedule_time:
        context.operations.schedule_time = schedule_time
    if timezone:
        context.operations.timezone = timezone

    logger.info(f"Updated schedule: {frequency}")

    if frequency == "manual":
        return "Schedule recorded: One-time/manual execution"
    elif frequency == "realtime":
        return "Schedule recorded: Real-time/streaming pipeline"
    else:
        time_str = f" at {schedule_time}" if schedule_time else ""
        return f"Schedule recorded: {frequency}{time_str} ({timezone})"


# ============================================================================
# Analysis Tools
# ============================================================================

@function_tool
def analyze_source_requirements(
    ctx: RunContextWrapper[PipelineContext],
) -> str:
    """
    Analyze the source system and determine connection requirements.
    Call this after source information has been gathered to get technical analysis.
    """
    context = ctx.context
    source = context.source

    if not source.type:
        return "Error: Source type not specified. Please gather source information first."

    requirements = []
    complexity = "low"
    warnings = []

    # Connection requirements based on source type
    if source.location == "on_premise":
        requirements.append("On-Premises Data Gateway required")
        requirements.append("Firewall rules may need configuration")
        complexity = "medium"
        warnings.append("Gateway must be installed and registered in Fabric")

    # Source-specific requirements
    db_sources = ["postgresql", "sql_server", "mysql", "oracle", "snowflake"]
    if source.type in db_sources:
        requirements.append("Database credentials (username/password or service principal)")
        requirements.append("Network connectivity from Fabric to database")
        if source.type == "oracle":
            complexity = "high"
            requirements.append("Oracle client libraries may be needed")
    elif source.type == "blob_storage":
        requirements.append("Storage account name and access key (or SAS token)")
        requirements.append("Container name and path")
    elif source.type == "adls_gen2":
        requirements.append("Storage account with hierarchical namespace")
        requirements.append("Service principal or managed identity access")
    elif source.type == "sharepoint":
        requirements.append("SharePoint site URL")
        requirements.append("Azure AD app registration with SharePoint permissions")
        complexity = "medium"
    elif source.type == "rest_api":
        requirements.append("API endpoint URL")
        requirements.append("Authentication method (API key, OAuth, etc.)")
        complexity = "medium"

    # Volume considerations
    if source.volume_gb and source.volume_gb > 100:
        warnings.append(f"Large dataset ({source.volume_gb}GB) - consider incremental loading")
        complexity = "high" if source.volume_gb > 500 else "medium"

    # Store analysis
    context.agent_insights["source_analysis"] = {
        "requirements": requirements,
        "complexity": complexity,
        "warnings": warnings,
    }

    # Format response
    result = f"## Source Analysis: {source.type.upper()}\n\n"
    result += f"**Complexity:** {complexity.upper()}\n\n"

    result += "**Connection Requirements:**\n"
    for req in requirements:
        result += f"- {req}\n"

    if warnings:
        result += "\n**Considerations:**\n"
        for warn in warnings:
            result += f"- {warn}\n"

    return result


# ============================================================================
# Architecture Design Tools
# ============================================================================

@function_tool
def design_architecture(
    ctx: RunContextWrapper[PipelineContext],
) -> str:
    """
    Design the optimal pipeline architecture based on gathered requirements.
    Call this after source and business context are complete.
    """
    context = ctx.context

    if not context.source.type:
        return "Error: Source type required. Please gather source information first."
    if not context.business.use_case:
        return "Error: Use case required. Please gather business context first."

    # Determine architecture pattern
    volume = context.source.volume_gb or 0
    has_pii = context.business.pii_likely
    use_case = context.business.use_case
    frequency = context.operations.frequency or "daily"

    # Pattern selection
    if frequency == "realtime":
        pattern = "streaming"
        layers = ["bronze", "silver"]
    elif has_pii or use_case == "ml" or volume > 100:
        pattern = "medallion_full"
        layers = ["bronze", "silver", "gold"]
    elif use_case == "analytics":
        pattern = "medallion_silver"
        layers = ["bronze", "silver"]
    else:
        pattern = "simple_copy"
        layers = ["bronze"]

    # Component selection for each layer
    components = {}
    recommendations = []
    warnings = []

    for layer in layers:
        if layer == "bronze":
            # Bronze layer - data ingestion
            simple_sources = ["postgresql", "sql_server", "mysql", "blob_storage", "adls_gen2"]
            if context.source.type in simple_sources:
                components["bronze"] = "Copy Activity"
            else:
                components["bronze"] = "Dataflow Gen2"

        elif layer == "silver":
            # Silver layer - cleaning & transformations
            if has_pii:
                components["silver"] = "Notebook"
                recommendations.append("Using Notebook for PII masking - provides fine-grained control")
            elif volume > 100:
                components["silver"] = "Notebook"
                recommendations.append("Using Notebook for large dataset - better PySpark performance")
            else:
                components["silver"] = "Dataflow Gen2"
                recommendations.append("Using Dataflow Gen2 for visual transformation design")

        elif layer == "gold":
            components["gold"] = "Notebook"
            recommendations.append("Gold layer uses Notebook for business aggregations")

    # Add warnings
    if context.source.location == "on_premise" and not context.source.gateway_available:
        warnings.append("On-Premises Data Gateway required but not confirmed")

    if volume > 500:
        warnings.append(f"Large dataset ({volume}GB) - implement incremental refresh strategy")

    # Update context
    context.architecture.pattern = pattern
    context.architecture.layers = layers
    context.architecture.components = components
    context.architecture.recommendations = recommendations
    context.architecture.warnings = warnings
    context.stage = PipelineStage.DESIGNING

    # Format response
    result = "## Pipeline Architecture Design\n\n"
    result += f"**Pattern:** {pattern.replace('_', ' ').title()}\n\n"

    result += "**Data Flow:**\n"
    result += "```\n"
    flow_parts = []
    for layer in layers:
        component = components.get(layer, "?")
        flow_parts.append(f"{layer.upper()} ({component})")
    result += " -> ".join(flow_parts)
    result += "\n```\n\n"

    result += "**Layer Details:**\n"
    for layer in layers:
        component = components.get(layer, "Unknown")
        result += f"- **{layer.title()}**: {component}\n"

    if recommendations:
        result += "\n**Recommendations:**\n"
        for rec in recommendations:
            result += f"- {rec}\n"

    if warnings:
        result += "\n**Warnings:**\n"
        for warn in warnings:
            result += f"- {warn}\n"

    return result


@function_tool
def update_transformations(
    ctx: RunContextWrapper[PipelineContext],
    pii_columns: Optional[List[str]] = None,
    cleaning_steps: Optional[List[str]] = None,
    aggregations: Optional[List[str]] = None,
    custom_logic: Optional[str] = None,
) -> str:
    """
    Update transformation requirements for the pipeline.
    Call this when user specifies data transformations needed.

    Args:
        pii_columns: Columns containing PII that need masking
        cleaning_steps: Data cleaning needed (dedupe, null_handling, type_conversion)
        aggregations: Aggregations needed (sum, count, average by dimensions)
        custom_logic: Description of custom transformation logic
    """
    context = ctx.context
    context.transformations.needed = True

    if pii_columns:
        context.transformations.pii_columns = pii_columns
        context.transformations.pii_handling = "mask"
    if cleaning_steps:
        context.transformations.cleaning = cleaning_steps
    if aggregations:
        context.transformations.aggregations = aggregations
    if custom_logic:
        context.transformations.custom_logic = custom_logic

    result = "## Transformation Plan Updated\n\n"

    if pii_columns:
        result += f"**PII Masking:** {len(pii_columns)} columns\n"
        result += f"- Columns: {', '.join(pii_columns)}\n\n"

    if cleaning_steps:
        result += "**Data Cleaning:**\n"
        for step in cleaning_steps:
            result += f"- {step}\n"
        result += "\n"

    if aggregations:
        result += "**Aggregations:**\n"
        for agg in aggregations:
            result += f"- {agg}\n"

    return result


# ============================================================================
# Deployment Tools
# ============================================================================

@function_tool
def generate_pipeline(
    ctx: RunContextWrapper[PipelineContext],
) -> str:
    """
    Generate the pipeline definition based on the designed architecture.
    Call this when the architecture is complete and user is ready for deployment.
    """
    context = ctx.context

    if not context.architecture.pattern:
        return "Error: Architecture not designed. Please design the architecture first."

    pipeline_name = f"pl_{context.source.type or 'source'}_to_lakehouse"

    # Generate activities
    activities = []
    previous_activity = None

    for layer in context.architecture.layers:
        component = context.architecture.components.get(layer, "Copy Activity")
        activity = _create_activity_definition(context, layer, component, previous_activity)
        activities.append(activity)
        previous_activity = activity["name"]

    # Create pipeline definition
    pipeline_def = {
        "name": pipeline_name,
        "properties": {
            "activities": activities,
            "parameters": {
                "tables": {
                    "type": "array",
                    "defaultValue": context.source.objects or []
                }
            },
        }
    }

    context.architecture.activities = activities
    context.architecture.pipeline_json = pipeline_def
    context.stage = PipelineStage.REVIEWING

    # Format response
    result = "## Pipeline Definition Generated\n\n"
    result += f"**Pipeline Name:** `{pipeline_name}`\n\n"
    result += f"**Activities:** {len(activities)}\n\n"

    result += "**Pipeline Flow:**\n"
    result += "```\n"
    for i, activity in enumerate(activities):
        prefix = "-> " if i > 0 else ""
        result += f"{prefix}{activity['name']} ({activity.get('type', 'Activity')})\n"
    result += "```\n\n"

    result += "**Status:** Ready for review and deployment\n"

    return result


@function_tool
def get_deployment_preview(
    ctx: RunContextWrapper[PipelineContext],
) -> str:
    """
    Get a complete preview of what will be deployed.
    Call this to show the user what they're about to deploy.
    """
    context = ctx.context

    result = "## Deployment Preview\n\n"

    # Summary
    result += f"**Stage:** {context.stage.value}\n"
    result += f"**Workspace:** {context.workspace_id}\n"
    result += f"**Lakehouse:** {context.lakehouse_name or 'Not specified'}\n\n"

    # Source
    result += "### Source Configuration\n"
    result += f"- Type: {context.source.type or 'Not specified'}\n"
    result += f"- Location: {context.source.location or 'Not specified'}\n"
    if context.source.database:
        result += f"- Database: {context.source.database}\n"
    if context.source.objects:
        result += f"- Objects: {len(context.source.objects)} items\n"
    if context.source.volume_gb:
        result += f"- Volume: ~{context.source.volume_gb}GB\n"
    result += "\n"

    # Business Context
    result += "### Business Context\n"
    result += f"- Use Case: {context.business.use_case or 'Not specified'}\n"
    result += f"- PII Present: {'Yes' if context.business.pii_likely else 'No'}\n"
    if context.business.consumers:
        result += f"- Consumers: {', '.join(context.business.consumers)}\n"
    result += "\n"

    # Architecture
    if context.architecture.pattern:
        result += "### Pipeline Architecture\n"
        result += f"- Pattern: {context.architecture.pattern}\n"
        result += f"- Layers: {' -> '.join(context.architecture.layers)}\n"
        for layer, component in context.architecture.components.items():
            result += f"- {layer.title()}: {component}\n"
        result += "\n"

    # Schedule
    result += "### Schedule\n"
    result += f"- Frequency: {context.operations.frequency or 'Not specified'}\n"
    if context.operations.schedule_time:
        result += f"- Time: {context.operations.schedule_time}\n"
    result += "\n"

    # Readiness check
    missing = context.get_missing_requirements()
    if missing:
        result += "### Missing Information\n"
        for item in missing:
            result += f"- {item.replace('_', ' ').title()}\n"
        result += "\n**Status:** Not ready for deployment\n"
    else:
        result += "### Status\n"
        result += "**Ready for deployment!**\n"

    return result


@function_tool
def deploy_to_fabric(
    ctx: RunContextWrapper[PipelineContext],
    confirmed: bool = False,
) -> str:
    """
    Deploy the pipeline to Microsoft Fabric.
    Call this only after user explicitly confirms deployment.

    Args:
        confirmed: User has confirmed they want to deploy
    """
    context = ctx.context

    if not confirmed:
        return "Deployment requires explicit confirmation. Please confirm you want to deploy."

    if not context.architecture.pipeline_json:
        return "Error: Pipeline not generated. Please generate the pipeline first."

    fabric_service = context.fabric_service
    if not fabric_service:
        # Preview mode
        context.stage = PipelineStage.COMPLETED
        return """## Deployment Preview Mode

The pipeline definition has been generated successfully.

**To deploy manually:**
1. Go to your Fabric workspace
2. Create a new Data Pipeline
3. Import the generated pipeline definition

**Generated Artifacts:**
- Pipeline JSON definition
- Notebook code (if applicable)

**Status:** Ready for manual deployment (Fabric service not connected)"""

    try:
        pipeline_def = context.architecture.pipeline_json

        # Deploy to Fabric
        result = fabric_service.create_pipeline(
            workspace_id=context.workspace_id,
            pipeline_name=pipeline_def["name"],
            pipeline_definition=pipeline_def
        )

        if result.get("success"):
            context.stage = PipelineStage.COMPLETED

            return f"""## Deployment Successful!

**Pipeline ID:** {result.get('pipeline_id', 'N/A')}
**Pipeline Name:** {pipeline_def['name']}

**Next Steps:**
1. Configure connection credentials in Fabric
2. Run a test execution
3. Enable the schedule

**Status:** Deployed successfully!"""
        else:
            return f"Deployment failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        logger.error(f"Deployment error: {e}")
        return f"Deployment error: {str(e)}"


# ============================================================================
# Utility Tools
# ============================================================================

@function_tool
def get_current_status(
    ctx: RunContextWrapper[PipelineContext],
) -> str:
    """
    Get the current status of the pipeline design conversation.
    Call this to check progress or summarize what's been gathered.
    """
    context = ctx.context

    result = "## Current Status\n\n"
    result += f"**Stage:** {context.stage.value}\n"
    result += f"**Summary:** {context.get_summary()}\n\n"

    missing = context.get_missing_requirements()
    if missing:
        result += "**Still Needed:**\n"
        for item in missing:
            result += f"- {item.replace('_', ' ').title()}\n"
    else:
        result += "**All requirements gathered!**\n"

    return result


@function_tool
def reset_conversation(
    ctx: RunContextWrapper[PipelineContext],
) -> str:
    """
    Reset the conversation and start fresh.
    Call this when user wants to start over.
    """
    context = ctx.context

    # Reset all fields
    context.stage = PipelineStage.INITIAL
    context.source = type(context.source)()
    context.business = type(context.business)()
    context.transformations = type(context.transformations)()
    context.destination = type(context.destination)()
    context.operations = type(context.operations)()
    context.architecture = type(context.architecture)()
    context.conversation_history = []
    context.agent_insights = {}

    return "Conversation reset. Let's start fresh! What kind of data pipeline would you like to build?"


# ============================================================================
# Helper Functions
# ============================================================================

def _create_activity_definition(
    context: PipelineContext,
    layer: str,
    component: str,
    depends_on: Optional[str],
) -> Dict[str, Any]:
    """Create a pipeline activity definition"""

    activity_name = f"{layer}_{component.lower().replace(' ', '_')}"

    base = {
        "name": activity_name,
        "type": _get_activity_type(component),
        "dependsOn": [{"activity": depends_on, "dependencyConditions": ["Succeeded"]}] if depends_on else [],
    }

    if component == "Copy Activity":
        base["typeProperties"] = {
            "source": {"type": _get_source_type(context.source.type)},
            "sink": {"type": "LakehouseTableSink", "tableActionOption": "Overwrite"}
        }
    elif component == "Dataflow Gen2":
        base["typeProperties"] = {
            "dataflow": {"referenceName": f"df_{layer}_transforms", "type": "DataflowReference"}
        }
    elif component == "Notebook":
        base["typeProperties"] = {
            "notebookId": f"nb_{layer}_processing",
            "parameters": {"layer": {"value": layer, "type": "string"}}
        }

    return base


def _get_activity_type(component: str) -> str:
    return {
        "Copy Activity": "Copy",
        "Dataflow Gen2": "DataFlow",
        "Notebook": "TridentNotebook",
    }.get(component, "Unknown")


def _get_source_type(source_type: Optional[str]) -> str:
    return {
        "postgresql": "PostgreSqlSource",
        "sql_server": "SqlServerSource",
        "mysql": "MySqlSource",
        "oracle": "OracleSource",
        "blob_storage": "BlobSource",
        "adls_gen2": "AzureBlobFSSource",
        "sharepoint": "SharePointOnlineListSource",
        "rest_api": "RestSource",
        "snowflake": "SnowflakeSource",
        "databricks": "DatabricksSource",
        "cosmosdb": "CosmosDbSqlApiSource",
    }.get(source_type, "SqlSource")


# ============================================================================
# Tool Registry for Claude Runner
# ============================================================================

TOOL_REGISTRY = {
    "update_source_info": {
        "description": "Update source system information based on user input",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_type": {"type": "string", "description": "Type of source (postgresql, sql_server, mysql, oracle, blob_storage, sharepoint, rest_api)"},
                "location": {"type": "string", "description": "Where source is hosted (cloud, on_premise)"},
                "database_name": {"type": "string", "description": "Name of the database"},
                "host": {"type": "string", "description": "Host/server address"},
                "tables": {"type": "array", "items": {"type": "string"}, "description": "List of tables to migrate"},
                "volume_gb": {"type": "number", "description": "Estimated data volume in GB"},
                "change_pattern": {"type": "string", "description": "How data changes (static, insert_only, updates, deletes)"},
            },
            "required": ["source_type"]
        }
    },
    "update_business_context": {
        "description": "Update business context and use case information",
        "input_schema": {
            "type": "object",
            "properties": {
                "use_case": {"type": "string", "description": "Primary use case (analytics, ml, operational, archive)"},
                "consumers": {"type": "array", "items": {"type": "string"}, "description": "Who will use the data"},
                "has_pii": {"type": "boolean", "description": "Whether data contains PII/PHI"},
                "compliance_requirements": {"type": "array", "items": {"type": "string"}, "description": "Compliance needs"},
                "criticality": {"type": "string", "description": "Project criticality (poc, development, production)"},
                "sla_hours": {"type": "integer", "description": "Required data freshness in hours"},
            },
            "required": ["use_case"]
        }
    },
    "update_schedule": {
        "description": "Update pipeline scheduling requirements",
        "input_schema": {
            "type": "object",
            "properties": {
                "frequency": {"type": "string", "description": "How often to run (manual, hourly, daily, weekly, realtime)"},
                "schedule_time": {"type": "string", "description": "When to run (e.g., '2:00 AM')"},
                "timezone": {"type": "string", "description": "Timezone for schedule"},
            },
            "required": ["frequency"]
        }
    },
    "analyze_source_requirements": {
        "description": "Analyze the source system and determine connection requirements",
        "input_schema": {"type": "object", "properties": {}}
    },
    "design_architecture": {
        "description": "Design the optimal pipeline architecture based on gathered requirements",
        "input_schema": {"type": "object", "properties": {}}
    },
    "update_transformations": {
        "description": "Update transformation requirements for the pipeline",
        "input_schema": {
            "type": "object",
            "properties": {
                "pii_columns": {"type": "array", "items": {"type": "string"}, "description": "Columns containing PII that need masking"},
                "cleaning_steps": {"type": "array", "items": {"type": "string"}, "description": "Data cleaning needed"},
                "aggregations": {"type": "array", "items": {"type": "string"}, "description": "Aggregations needed"},
                "custom_logic": {"type": "string", "description": "Description of custom transformation logic"},
            }
        }
    },
    "generate_pipeline": {
        "description": "Generate the pipeline definition based on the designed architecture",
        "input_schema": {"type": "object", "properties": {}}
    },
    "get_deployment_preview": {
        "description": "Get a complete preview of what will be deployed",
        "input_schema": {"type": "object", "properties": {}}
    },
    "deploy_to_fabric": {
        "description": "Deploy the pipeline to Microsoft Fabric (requires confirmation)",
        "input_schema": {
            "type": "object",
            "properties": {
                "confirmed": {"type": "boolean", "description": "User has confirmed deployment"}
            },
            "required": ["confirmed"]
        }
    },
    "get_current_status": {
        "description": "Get the current status of the pipeline design conversation",
        "input_schema": {"type": "object", "properties": {}}
    },
    "reset_conversation": {
        "description": "Reset the conversation and start fresh",
        "input_schema": {"type": "object", "properties": {}}
    },
}


class MockContextWrapper:
    """Mock context wrapper for Claude runner compatibility"""
    def __init__(self, context: PipelineContext):
        self.context = context


async def execute_tool(tool_name: str, tool_input: Dict[str, Any], context: PipelineContext) -> Any:
    """Execute a tool by name with the given input"""

    # Create mock wrapper for compatibility with existing tool functions
    ctx = MockContextWrapper(context)

    tool_functions = {
        "update_source_info": lambda: update_source_info.__wrapped__(
            ctx,
            source_type=tool_input.get("source_type", ""),
            location=tool_input.get("location"),
            database_name=tool_input.get("database_name"),
            host=tool_input.get("host"),
            tables=tool_input.get("tables"),
            volume_gb=tool_input.get("volume_gb"),
            change_pattern=tool_input.get("change_pattern"),
        ),
        "update_business_context": lambda: update_business_context.__wrapped__(
            ctx,
            use_case=tool_input.get("use_case", ""),
            consumers=tool_input.get("consumers"),
            has_pii=tool_input.get("has_pii", False),
            compliance_requirements=tool_input.get("compliance_requirements"),
            criticality=tool_input.get("criticality"),
            sla_hours=tool_input.get("sla_hours"),
        ),
        "update_schedule": lambda: update_schedule.__wrapped__(
            ctx,
            frequency=tool_input.get("frequency", "daily"),
            schedule_time=tool_input.get("schedule_time"),
            timezone=tool_input.get("timezone", "UTC"),
        ),
        "analyze_source_requirements": lambda: analyze_source_requirements.__wrapped__(ctx),
        "design_architecture": lambda: design_architecture.__wrapped__(ctx),
        "update_transformations": lambda: update_transformations.__wrapped__(
            ctx,
            pii_columns=tool_input.get("pii_columns"),
            cleaning_steps=tool_input.get("cleaning_steps"),
            aggregations=tool_input.get("aggregations"),
            custom_logic=tool_input.get("custom_logic"),
        ),
        "generate_pipeline": lambda: generate_pipeline.__wrapped__(ctx),
        "get_deployment_preview": lambda: get_deployment_preview.__wrapped__(ctx),
        "deploy_to_fabric": lambda: deploy_to_fabric.__wrapped__(
            ctx,
            confirmed=tool_input.get("confirmed", False),
        ),
        "get_current_status": lambda: get_current_status.__wrapped__(ctx),
        "reset_conversation": lambda: reset_conversation.__wrapped__(ctx),
    }

    if tool_name in tool_functions:
        try:
            result = tool_functions[tool_name]()
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {"success": False, "error": str(e)}
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
