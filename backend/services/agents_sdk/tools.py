"""
Fabric Pipeline Tools - Production Ready

Function tools for Microsoft Fabric pipeline design and deployment.
These tools are used by agents to interact with the pipeline context and Fabric APIs.
"""

from typing import Dict, Any, List, Optional
import logging
import re

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
    """Create a Fabric-compatible pipeline activity definition"""

    activity_name = f"{layer}_{component.lower().replace(' ', '_')}"

    base = {
        "name": activity_name,
        "type": _get_activity_type(component),
        "dependsOn": [{"activity": depends_on, "dependencyConditions": ["Succeeded"]}] if depends_on else [],
    }

    if component == "Copy Activity":
        source_config = _build_source_config(context)
        sink_config = _build_sink_config(context, layer)
        base["typeProperties"] = {
            "source": source_config,
            "sink": sink_config,
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


def _build_source_config(context: PipelineContext) -> Dict[str, Any]:
    """Build Fabric-compatible source configuration with datasetSettings"""
    source_type = context.source.type or "rest_api"
    source_info = _get_source_info(source_type)

    # Build connection URL from context
    connection_url = ""
    if context.source.host:
        connection_url = context.source.host
    elif hasattr(context, 'source_url') and context.source_url:
        connection_url = context.source_url

    # Try to find URL from conversation history
    if not connection_url:
        for turn in getattr(context, 'conversation_history', []):
            content = turn.get('content', '')
            url_match = re.search(r'https?://[^\s,]+\.dynamics\.com', content)
            if url_match:
                connection_url = url_match.group(0)
                break
            url_match = re.search(r'https?://[^\s,]+', content)
            if url_match and not connection_url:
                connection_url = url_match.group(0)

    # Get table name
    table_name = context.source.objects[0] if context.source.objects else "data"

    config = {
        "type": source_info["source_type"],
        "datasetSettings": {
            "annotations": [],
            "type": source_info["dataset_type"],
            "typeProperties": source_info.get("source_type_properties", {}),
            "linkedService": {
                "name": f"{source_type}_connection",
                "properties": {
                    "annotations": [],
                    "type": source_info["linked_service_type"],
                    "typeProperties": {
                        "url": connection_url,
                        "authenticationType": source_info.get("auth_type", "Anonymous"),
                    }
                }
            },
        }
    }
    return config


def _build_sink_config(context: PipelineContext, layer: str) -> Dict[str, Any]:
    """Build Fabric-compatible Lakehouse sink configuration"""
    table_name = context.source.objects[0] if context.source.objects else "data"
    lakehouse_name = context.lakehouse_name or "default_lakehouse"
    lakehouse_id = context.lakehouse_id

    sink_config = {
        "type": "LakehouseTableSink",
        "tableActionOption": "Overwrite",
        "datasetSettings": {
            "annotations": [],
            "type": "LakehouseTable",
            "typeProperties": {
                "table": table_name,
            },
            "linkedService": {
                "name": lakehouse_name,
                "properties": {
                    "annotations": [],
                    "type": "Lakehouse",
                    "typeProperties": {
                        "workspaceId": context.workspace_id,
                        "artifactId": lakehouse_id,
                    }
                }
            },
        }
    }
    return sink_config


def _get_activity_type(component: str) -> str:
    return {
        "Copy Activity": "Copy",
        "Dataflow Gen2": "DataFlow",
        "Notebook": "TridentNotebook",
    }.get(component, "Unknown")


def _get_source_info(source_type: str) -> Dict[str, str]:
    """Get Fabric-compatible source/dataset/linkedService type mapping"""
    source_map = {
        "rest_api": {
            "source_type": "RestSource",
            "dataset_type": "RestResource",
            "linked_service_type": "RestService",
            "auth_type": "Anonymous",
            "source_type_properties": {},
        },
        "postgresql": {
            "source_type": "PostgreSqlSource",
            "dataset_type": "PostgreSqlTable",
            "linked_service_type": "PostgreSql",
            "auth_type": "Basic",
            "source_type_properties": {},
        },
        "sql_server": {
            "source_type": "SqlServerSource",
            "dataset_type": "SqlServerTable",
            "linked_service_type": "SqlServer",
            "auth_type": "Basic",
            "source_type_properties": {},
        },
        "mysql": {
            "source_type": "MySqlSource",
            "dataset_type": "MySqlTable",
            "linked_service_type": "MySql",
            "auth_type": "Basic",
            "source_type_properties": {},
        },
        "blob_storage": {
            "source_type": "BlobSource",
            "dataset_type": "Binary",
            "linked_service_type": "AzureBlobStorage",
            "auth_type": "Key",
            "source_type_properties": {},
        },
        "adls_gen2": {
            "source_type": "AzureBlobFSSource",
            "dataset_type": "Binary",
            "linked_service_type": "AzureBlobFS",
            "auth_type": "Key",
            "source_type_properties": {},
        },
        "snowflake": {
            "source_type": "SnowflakeSource",
            "dataset_type": "SnowflakeTable",
            "linked_service_type": "Snowflake",
            "auth_type": "Basic",
            "source_type_properties": {},
        },
        "cosmosdb": {
            "source_type": "CosmosDbSqlApiSource",
            "dataset_type": "CosmosDbSqlApiCollection",
            "linked_service_type": "CosmosDb",
            "auth_type": "Key",
            "source_type_properties": {},
        },
    }
    return source_map.get(source_type, source_map["rest_api"])


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


# ============================================================================
# Plain function wrappers for Claude Runner (bypass @function_tool decorator)
# ============================================================================

def _exec_update_source_info(ctx, source_type="", location=None, database_name=None, host=None, tables=None, volume_gb=None, change_pattern=None):
    context = ctx.context
    context.source.type = source_type
    if location: context.source.location = location
    if database_name: context.source.database = database_name
    if host: context.source.host = host
    if tables: context.source.objects = tables
    if volume_gb: context.source.volume_gb = volume_gb
    if change_pattern: context.source.change_pattern = change_pattern
    context.stage = PipelineStage.DISCOVERY
    logger.info(f"Updated source info: {source_type} ({location})")
    result = f"Source information recorded: {source_type}"
    if location: result += f" hosted {location}"
    if database_name: result += f", database: {database_name}"
    return result

def _exec_update_business_context(ctx, use_case="", consumers=None, has_pii=False, compliance_requirements=None, criticality=None, sla_hours=None):
    context = ctx.context
    context.business.use_case = use_case
    if consumers: context.business.consumers = consumers
    context.business.pii_likely = has_pii
    if compliance_requirements: context.business.compliance_requirements = compliance_requirements
    if criticality: context.business.criticality = criticality
    if sla_hours: context.business.sla_hours = sla_hours
    logger.info(f"Updated business context: {use_case}, PII: {has_pii}")
    pii_note = " (PII handling required)" if has_pii else ""
    consumers_str = f" for {', '.join(consumers)}" if consumers else ""
    return f"Business context recorded: {use_case}{consumers_str}{pii_note}"

def _exec_update_schedule(ctx, frequency="daily", schedule_time=None, timezone="UTC"):
    context = ctx.context
    context.operations.frequency = frequency
    if schedule_time: context.operations.schedule_time = schedule_time
    if timezone: context.operations.timezone = timezone
    logger.info(f"Updated schedule: {frequency}")
    if frequency == "manual": return "Schedule recorded: One-time/manual execution"
    elif frequency == "realtime": return "Schedule recorded: Real-time/streaming pipeline"
    time_str = f" at {schedule_time}" if schedule_time else ""
    return f"Schedule recorded: {frequency}{time_str} ({timezone})"

def _exec_analyze_source(ctx):
    context = ctx.context
    source = context.source
    if not source.type: return "Error: Source type not specified."
    requirements, complexity, warnings = [], "low", []
    if source.location == "on_premise":
        requirements.append("On-Premises Data Gateway required")
        complexity = "medium"
    db_sources = ["postgresql", "sql_server", "mysql", "oracle", "snowflake"]
    if source.type in db_sources:
        requirements.append("Database credentials required")
    elif source.type in ["blob_storage", "adls_gen2"]:
        requirements.append("Storage account access required")
    if source.volume_gb and source.volume_gb > 100:
        warnings.append(f"Large dataset ({source.volume_gb}GB) - consider incremental loading")
        complexity = "high" if source.volume_gb > 500 else "medium"
    context.agent_insights["source_analysis"] = {"requirements": requirements, "complexity": complexity, "warnings": warnings}
    result = f"## Source Analysis: {source.type.upper()}\n\n**Complexity:** {complexity.upper()}\n\n**Requirements:**\n"
    for req in requirements: result += f"- {req}\n"
    if warnings:
        result += "\n**Considerations:**\n"
        for w in warnings: result += f"- {w}\n"
    return result

def _exec_design_architecture(ctx):
    context = ctx.context
    if not context.source.type: return "Error: Source type required."
    if not context.business.use_case: return "Error: Use case required."
    volume = context.source.volume_gb or 0
    has_pii = context.business.pii_likely
    use_case = context.business.use_case
    frequency = context.operations.frequency or "daily"
    needs_transforms = context.transformations.needed if hasattr(context.transformations, 'needed') else False
    if frequency == "realtime": pattern, layers = "streaming", ["bronze", "silver"]
    elif has_pii or use_case == "ml" or volume > 100: pattern, layers = "medallion_full", ["bronze", "silver", "gold"]
    elif use_case == "analytics" and needs_transforms: pattern, layers = "medallion_silver", ["bronze", "silver"]
    else: pattern, layers = "simple_copy", ["bronze"]
    components, recommendations = {}, []
    # Check if transformations are actually needed
    needs_transforms = context.transformations.needed if hasattr(context.transformations, 'needed') else False
    for layer in layers:
        if layer == "bronze":
            # Use Copy Activity for all source types in bronze layer (ingestion)
            components["bronze"] = "Copy Activity"
        elif layer == "silver":
            if not needs_transforms and not has_pii:
                # No transformations needed — skip or use simple copy
                components["silver"] = "Copy Activity"
            elif has_pii or volume > 100:
                components["silver"] = "Notebook"
            else:
                components["silver"] = "Dataflow Gen2"
        elif layer == "gold": components["gold"] = "Notebook"
    context.architecture.pattern = pattern
    context.architecture.layers = layers
    context.architecture.components = components
    context.architecture.recommendations = recommendations
    context.stage = PipelineStage.DESIGNING
    result = f"## Pipeline Architecture Design\n\n**Pattern:** {pattern.replace('_',' ').title()}\n\n**Layers:**\n"
    for layer in layers: result += f"- **{layer.title()}**: {components.get(layer,'?')}\n"
    return result

def _exec_update_transformations(ctx, pii_columns=None, cleaning_steps=None, aggregations=None, custom_logic=None):
    context = ctx.context
    context.transformations.needed = True
    if pii_columns: context.transformations.pii_columns = pii_columns; context.transformations.pii_handling = "mask"
    if cleaning_steps: context.transformations.cleaning = cleaning_steps
    if aggregations: context.transformations.aggregations = aggregations
    if custom_logic: context.transformations.custom_logic = custom_logic
    result = "## Transformation Plan Updated\n\n"
    if pii_columns: result += f"**PII Masking:** {len(pii_columns)} columns ({', '.join(pii_columns)})\n\n"
    if cleaning_steps: result += "**Cleaning:** " + ", ".join(cleaning_steps) + "\n"
    return result

def _exec_generate_pipeline(ctx):
    context = ctx.context
    if not context.architecture.pattern: return "Error: Architecture not designed."
    pipeline_name = f"pl_{context.source.type or 'source'}_to_lakehouse"
    activities = []
    prev = None
    for layer in context.architecture.layers:
        component = context.architecture.components.get(layer, "Copy Activity")
        activity = _create_activity_definition(context, layer, component, prev)
        activities.append(activity)
        prev = activity["name"]
    pipeline_def = {"name": pipeline_name, "properties": {"activities": activities}}
    context.architecture.activities = activities
    context.architecture.pipeline_json = pipeline_def
    context.stage = PipelineStage.REVIEWING
    result = f"## Pipeline Generated\n\n**Name:** `{pipeline_name}`\n**Activities:** {len(activities)}\n**Status:** Ready for review\n"
    return result

def _exec_get_deployment_preview(ctx):
    context = ctx.context
    result = f"## Deployment Preview\n\n**Workspace:** {context.workspace_id}\n**Lakehouse:** {context.lakehouse_name or 'N/A'}\n"
    result += f"**Source:** {context.source.type or 'N/A'} ({context.source.location or 'N/A'})\n"
    if context.architecture.pattern: result += f"**Architecture:** {context.architecture.pattern}\n"
    missing = context.get_missing_requirements()
    if missing: result += f"\n**Missing:** {', '.join(missing)}\n"
    else: result += "\n**Status:** Ready for deployment!\n"
    return result

def _exec_deploy_to_fabric(ctx, confirmed=False):
    """Sync stub — actual deployment handled in execute_tool via _async_deploy_to_fabric"""
    context = ctx.context
    if not confirmed: return "Deployment requires explicit confirmation."
    if not context.architecture.pipeline_json: return "Error: Pipeline not generated."
    # This path is only reached if execute_tool doesn't intercept first
    context.stage = PipelineStage.COMPLETED
    return "## Deployment Preview Mode\n\nPipeline definition generated. Ready for manual deployment."


async def _async_deploy_to_fabric(context, confirmed=False):
    """Async deployment that actually calls the Fabric API"""
    if not confirmed:
        return {"success": False, "result": "Deployment requires explicit confirmation."}
    if not context.architecture.pipeline_json:
        return {"success": False, "result": "Error: Pipeline not generated."}

    fabric_service = context.fabric_service
    if not fabric_service:
        context.stage = PipelineStage.COMPLETED
        return {"success": True, "result": "## Deployment Preview Mode\n\nPipeline definition generated. Ready for manual deployment (Fabric service not connected)."}

    try:
        pipeline_def = context.architecture.pipeline_json
        pipeline_name = pipeline_def.get("name", "ai_generated_pipeline")

        result = await fabric_service.create_pipeline(
            workspace_id=context.workspace_id,
            pipeline_name=pipeline_name,
            pipeline_definition=pipeline_def
        )

        if result.get("success"):
            context.stage = PipelineStage.COMPLETED
            return {"success": True, "result": f"## Deployment Successful!\n\n**Pipeline ID:** {result.get('pipeline_id', 'N/A')}\n**Pipeline Name:** {pipeline_name}\n\n**Next Steps:**\n1. Configure connection credentials in Fabric\n2. Run a test execution\n3. Enable the schedule\n\n**Status:** Deployed successfully to Microsoft Fabric!"}
        else:
            return {"success": False, "result": f"Deployment failed: {result.get('error', 'Unknown error')}"}

    except Exception as e:
        logger.error(f"Deployment error: {e}")
        return {"success": False, "result": f"Deployment error: {str(e)}"}

def _exec_get_current_status(ctx):
    context = ctx.context
    result = f"## Current Status\n\n**Stage:** {context.stage.value}\n**Summary:** {context.get_summary()}\n"
    missing = context.get_missing_requirements()
    if missing: result += "**Still Needed:** " + ", ".join(m.replace('_',' ').title() for m in missing) + "\n"
    else: result += "**All requirements gathered!**\n"
    return result

def _exec_reset_conversation(ctx):
    context = ctx.context
    context.stage = PipelineStage.INITIAL
    context.source = type(context.source)()
    context.business = type(context.business)()
    context.transformations = type(context.transformations)()
    context.destination = type(context.destination)()
    context.operations = type(context.operations)()
    context.architecture = type(context.architecture)()
    context.conversation_history = []
    context.agent_insights = {}
    return "Conversation reset. Let's start fresh!"


async def execute_tool(tool_name: str, tool_input: Dict[str, Any], context: PipelineContext) -> Any:
    """Execute a tool by name with the given input"""

    # Create mock wrapper for compatibility with existing tool functions
    ctx = MockContextWrapper(context)

    tool_functions = {
        "update_source_info": lambda: _exec_update_source_info(
            ctx,
            source_type=tool_input.get("source_type", ""),
            location=tool_input.get("location"),
            database_name=tool_input.get("database_name"),
            host=tool_input.get("host"),
            tables=tool_input.get("tables"),
            volume_gb=tool_input.get("volume_gb"),
            change_pattern=tool_input.get("change_pattern"),
        ),
        "update_business_context": lambda: _exec_update_business_context(
            ctx,
            use_case=tool_input.get("use_case", ""),
            consumers=tool_input.get("consumers"),
            has_pii=tool_input.get("has_pii", False),
            compliance_requirements=tool_input.get("compliance_requirements"),
            criticality=tool_input.get("criticality"),
            sla_hours=tool_input.get("sla_hours"),
        ),
        "update_schedule": lambda: _exec_update_schedule(
            ctx,
            frequency=tool_input.get("frequency", "daily"),
            schedule_time=tool_input.get("schedule_time"),
            timezone=tool_input.get("timezone", "UTC"),
        ),
        "analyze_source_requirements": lambda: _exec_analyze_source(ctx),
        "design_architecture": lambda: _exec_design_architecture(ctx),
        "update_transformations": lambda: _exec_update_transformations(
            ctx,
            pii_columns=tool_input.get("pii_columns"),
            cleaning_steps=tool_input.get("cleaning_steps"),
            aggregations=tool_input.get("aggregations"),
            custom_logic=tool_input.get("custom_logic"),
        ),
        "generate_pipeline": lambda: _exec_generate_pipeline(ctx),
        "get_deployment_preview": lambda: _exec_get_deployment_preview(ctx),
        "deploy_to_fabric": lambda: _exec_deploy_to_fabric(
            ctx,
            confirmed=tool_input.get("confirmed", False),
        ),
        "get_current_status": lambda: _exec_get_current_status(ctx),
        "reset_conversation": lambda: _exec_reset_conversation(ctx),
    }

    # Special handling for deploy_to_fabric — needs async for Fabric API call
    if tool_name == "deploy_to_fabric":
        try:
            result = await _async_deploy_to_fabric(
                context,
                confirmed=tool_input.get("confirmed", False),
            )
            return result
        except Exception as e:
            logger.error(f"Async deploy error: {tool_name} - {e}")
            return {"success": False, "error": str(e)}

    if tool_name in tool_functions:
        try:
            result = tool_functions[tool_name]()
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {"success": False, "error": str(e)}
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
