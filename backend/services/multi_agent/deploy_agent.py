"""
Deploy Agent

Builds and deploys the actual pipeline to Microsoft Fabric.
The Builder of the pipeline architect team.
"""

from typing import Dict, Any, List, Optional
import logging
import json

from .base_agent import BaseAgent, AgentResponse
from .state_manager import PipelineState

logger = logging.getLogger(__name__)


class DeployAgent(BaseAgent):
    """
    Deploy Agent - Builds and deploys pipelines.

    Responsibilities:
    - Generate pipeline JSON definition
    - Create necessary connections
    - Generate notebook code
    - Deploy to Fabric workspace
    - Configure schedules
    """

    def __init__(self, ai_service=None, fabric_service=None):
        super().__init__(
            name="deploy",
            role="Pipeline Builder",
            ai_service=ai_service
        )
        self.fabric_service = fabric_service

    @property
    def system_prompt(self) -> str:
        return """You are the Deploy Agent - a Pipeline Builder specialist.

## YOUR ROLE
Build and deploy the designed pipeline to Microsoft Fabric:
1. Generate pipeline JSON definition
2. Create connections if needed
3. Generate notebook code for transforms
4. Deploy to workspace
5. Configure schedules

## OUTPUT FORMAT
Provide deployment status and any issues encountered."""

    @property
    def required_info(self) -> List[str]:
        return [
            "source_type",
            "destination_type",
        ]

    @property
    def thinking_rules(self) -> Dict[str, Any]:
        return {}

    async def process(self, state: PipelineState, user_message: str) -> AgentResponse:
        """Build and prepare pipeline for deployment"""

        # Generate pipeline definition
        pipeline_def = self._generate_pipeline_definition(state)

        # Generate notebooks if needed
        notebooks = self._generate_notebooks(state)

        # Check prerequisites
        prerequisites = self._check_prerequisites(state)

        # Store in state
        state.architecture.activities = pipeline_def.get("activities", [])
        state.architecture.notebooks = notebooks

        insights = {
            "pipeline_name": pipeline_def.get("name"),
            "activity_count": len(pipeline_def.get("activities", [])),
            "notebook_count": len(notebooks),
            "prerequisites_met": all(p["status"] == "ready" for p in prerequisites),
        }

        recommendations = []
        warnings = [p["message"] for p in prerequisites if p["status"] != "ready"]

        if not warnings:
            recommendations.append("All prerequisites met - ready to deploy!")

        message = self._format_deployment(state, pipeline_def, notebooks, prerequisites)

        return AgentResponse(
            message=message,
            insights=insights,
            recommendations=recommendations,
            warnings=warnings,
            state_updates={
                "pipeline_definition": pipeline_def,
                "notebooks": notebooks,
            },
            is_complete=True,
        )

    def _generate_pipeline_definition(self, state: PipelineState) -> Dict[str, Any]:
        """Generate Fabric pipeline JSON definition"""

        pipeline_name = f"pl_{state.source.type or 'source'}_to_lakehouse"

        pipeline = {
            "name": pipeline_name,
            "properties": {
                "activities": [],
                "parameters": {
                    "tables": {
                        "type": "array",
                        "defaultValue": state.source.objects or []
                    }
                },
            }
        }

        activities = []
        previous_activity = None

        # Generate activities based on architecture
        for layer_spec in state.architecture.layers or []:
            if isinstance(layer_spec, dict):
                layer = layer_spec.get("name", "bronze")
                component = layer_spec.get("component", "Copy Activity")
            else:
                layer = layer_spec
                component = state.architecture.components.get(layer, "Copy Activity")

            activity = self._create_activity(state, layer, component, previous_activity)
            activities.append(activity)
            previous_activity = activity["name"]

        pipeline["properties"]["activities"] = activities

        return pipeline

    def _create_activity(
        self,
        state: PipelineState,
        layer: str,
        component: str,
        depends_on: Optional[str]
    ) -> Dict[str, Any]:
        """Create a single pipeline activity"""

        activity_name = f"{layer}_{component.lower().replace(' ', '_')}"

        base_activity = {
            "name": activity_name,
            "dependsOn": [{"activity": depends_on, "dependencyConditions": ["Succeeded"]}] if depends_on else [],
        }

        if component == "Copy Activity":
            return self._create_copy_activity(base_activity, state, layer)
        elif component == "Dataflow Gen2":
            return self._create_dataflow_activity(base_activity, state, layer)
        elif component == "Notebook":
            return self._create_notebook_activity(base_activity, state, layer)
        else:
            return base_activity

    def _create_copy_activity(self, base: Dict, state: PipelineState, layer: str) -> Dict:
        """Create Copy Activity definition"""

        # Check if we need ForEach for multiple tables
        needs_foreach = len(state.source.objects or []) > 1 or not state.source.objects

        if needs_foreach:
            return {
                **base,
                "type": "ForEach",
                "typeProperties": {
                    "isSequential": False,
                    "batchCount": 10,
                    "items": {"value": "@pipeline().parameters.tables", "type": "Expression"},
                    "activities": [
                        {
                            "name": f"Copy_to_{layer}",
                            "type": "Copy",
                            "typeProperties": {
                                "source": {
                                    "type": self._get_source_type(state.source.type),
                                    "query": {
                                        "value": "@concat('SELECT * FROM ', item().schema, '.', item().name)",
                                        "type": "Expression"
                                    }
                                },
                                "sink": {
                                    "type": "LakehouseTableSink",
                                    "tableActionOption": "Overwrite"
                                }
                            }
                        }
                    ]
                }
            }
        else:
            return {
                **base,
                "type": "Copy",
                "typeProperties": {
                    "source": {
                        "type": self._get_source_type(state.source.type),
                    },
                    "sink": {
                        "type": "LakehouseTableSink",
                        "tableActionOption": "Overwrite"
                    }
                }
            }

    def _create_dataflow_activity(self, base: Dict, state: PipelineState, layer: str) -> Dict:
        """Create Dataflow Gen2 activity definition"""

        return {
            **base,
            "type": "DataFlow",
            "typeProperties": {
                "dataflow": {
                    "referenceName": f"df_{layer}_transforms",
                    "type": "DataflowReference"
                },
                "compute": {
                    "coreCount": 8,
                    "computeType": "General"
                }
            }
        }

    def _create_notebook_activity(self, base: Dict, state: PipelineState, layer: str) -> Dict:
        """Create Notebook activity definition"""

        return {
            **base,
            "type": "TridentNotebook",
            "typeProperties": {
                "notebookId": f"nb_{layer}_processing",
                "parameters": {
                    "source_layer": {"value": "silver" if layer == "gold" else "bronze", "type": "string"},
                    "target_layer": {"value": layer, "type": "string"}
                }
            }
        }

    def _get_source_type(self, source_type: Optional[str]) -> str:
        """Map source type to Fabric source type name"""

        mapping = {
            "postgresql": "PostgreSqlSource",
            "sql_server": "SqlServerSource",
            "mysql": "MySqlSource",
            "oracle": "OracleSource",
            "blob_storage": "BlobSource",
            "adls": "AzureBlobFSSource",
            "sharepoint": "SharePointOnlineListSource",
            "rest_api": "RestSource",
        }
        return mapping.get(source_type, "SqlSource")

    def _generate_notebooks(self, state: PipelineState) -> List[Dict[str, Any]]:
        """Generate notebook definitions for transform layers"""

        notebooks = []

        for layer_spec in state.architecture.layers or []:
            if isinstance(layer_spec, dict):
                layer = layer_spec.get("name")
                component = layer_spec.get("component")
            else:
                layer = layer_spec
                component = state.architecture.components.get(layer, "")

            if component == "Notebook":
                notebook = self._generate_notebook_code(state, layer)
                notebooks.append(notebook)

        return notebooks

    def _generate_notebook_code(self, state: PipelineState, layer: str) -> Dict[str, Any]:
        """Generate PySpark notebook code for a layer"""

        notebook_name = f"nb_{layer}_processing"

        if layer == "silver":
            code = self._generate_silver_notebook(state)
        elif layer == "gold":
            code = self._generate_gold_notebook(state)
        else:
            code = self._generate_bronze_notebook(state)

        return {
            "name": notebook_name,
            "layer": layer,
            "code": code,
            "language": "python",
        }

    def _generate_silver_notebook(self, state: PipelineState) -> str:
        """Generate Silver layer notebook code"""

        pii_columns = state.transformations.pii_columns or []
        pii_code = ""

        if pii_columns:
            mask_statements = []
            for col in pii_columns:
                mask_statements.append(
                    f'    .withColumn("{col}", regexp_replace(col("{col}"), r".(?=.{{4}})", "*"))'
                )
            pii_code = f"""
# PII Masking
from pyspark.sql.functions import regexp_replace, col

df = df{chr(10).join(mask_statements)}
"""

        return f'''# Silver Layer Processing
# Auto-generated by Pipeline Architect

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

# Read from Bronze
bronze_path = "Tables/bronze_*"
df = spark.read.format("delta").load(bronze_path)

# Deduplication
df = df.dropDuplicates()

# Handle nulls
df = df.na.fill({{"string_columns": "", "numeric_columns": 0}})

# Type standardization
# Add column-specific type casts here
{pii_code}
# Write to Silver
silver_path = "Tables/silver_{state.source.type or 'data'}"
df.write.format("delta").mode("overwrite").save(silver_path)

print(f"Silver layer processing complete. Rows: {{df.count()}}")
'''

    def _generate_gold_notebook(self, state: PipelineState) -> str:
        """Generate Gold layer notebook code"""

        return f'''# Gold Layer Processing
# Auto-generated by Pipeline Architect

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

# Read from Silver
silver_path = "Tables/silver_*"
df = spark.read.format("delta").load(silver_path)

# Business Aggregations
# Modify based on your business requirements
aggregated_df = df.groupBy("date", "category").agg(
    count("*").alias("record_count"),
    sum("amount").alias("total_amount"),
    avg("amount").alias("avg_amount")
)

# Write to Gold
gold_path = "Tables/gold_aggregated"
aggregated_df.write.format("delta").mode("overwrite").save(gold_path)

# Optimize for Power BI
spark.sql("OPTIMIZE gold_aggregated")

print(f"Gold layer processing complete. Rows: {{aggregated_df.count()}}")
'''

    def _generate_bronze_notebook(self, state: PipelineState) -> str:
        """Generate Bronze layer notebook code"""

        return f'''# Bronze Layer Processing
# Auto-generated by Pipeline Architect

from pyspark.sql import SparkSession

# This notebook handles raw data ingestion
# Typically Bronze layer uses Copy Activity, but this notebook
# can be used for custom ingestion logic

print("Bronze layer processing - using Copy Activity")
'''

    def _check_prerequisites(self, state: PipelineState) -> List[Dict[str, Any]]:
        """Check deployment prerequisites"""

        prerequisites = []

        # Gateway check for on-premise
        if state.source.location == "on_premise":
            prerequisites.append({
                "name": "On-Premises Data Gateway",
                "status": "required" if not state.source.gateway_available else "ready",
                "message": "On-Premises Data Gateway must be installed and configured" if not state.source.gateway_available else "Gateway available",
            })

        # Workspace check
        prerequisites.append({
            "name": "Fabric Workspace",
            "status": "ready" if state.workspace_id else "required",
            "message": "Workspace ID configured" if state.workspace_id else "Workspace ID required",
        })

        # Lakehouse check
        prerequisites.append({
            "name": "Lakehouse",
            "status": "ready" if state.destination.lakehouse_id else "will_create",
            "message": "Lakehouse configured" if state.destination.lakehouse_id else "Lakehouse will be selected during deployment",
        })

        return prerequisites

    def _format_deployment(
        self,
        state: PipelineState,
        pipeline_def: Dict,
        notebooks: List[Dict],
        prerequisites: List[Dict]
    ) -> str:
        """Format deployment information"""

        parts = ["## Deployment Package\n"]

        # Pipeline summary
        parts.append(f"### Pipeline: {pipeline_def.get('name')}")
        activities = pipeline_def.get("properties", {}).get("activities", [])
        parts.append(f"- Activities: {len(activities)}")
        for activity in activities:
            parts.append(f"  - {activity.get('name')} ({activity.get('type')})")

        # Notebooks
        if notebooks:
            parts.append(f"\n### Notebooks: {len(notebooks)}")
            for nb in notebooks:
                parts.append(f"- {nb['name']} ({nb['layer']} layer)")

        # Prerequisites
        parts.append("\n### Prerequisites Check")
        all_ready = True
        for prereq in prerequisites:
            status_icon = "✅" if prereq["status"] == "ready" else "⚠️"
            parts.append(f"- {status_icon} {prereq['name']}: {prereq['message']}")
            if prereq["status"] not in ["ready", "will_create"]:
                all_ready = False

        # Deployment status
        parts.append("\n### Deployment Status")
        if all_ready:
            parts.append("✅ Ready to deploy! Click 'Deploy to Fabric Workspace' to proceed.")
        else:
            parts.append("⚠️ Please resolve prerequisites before deployment.")

        return "\n".join(parts)

    async def deploy(self, state: PipelineState) -> Dict[str, Any]:
        """Actually deploy the pipeline to Fabric"""

        if not self.fabric_service:
            return {
                "success": False,
                "error": "Fabric service not configured"
            }

        try:
            # Generate pipeline definition
            pipeline_def = self._generate_pipeline_definition(state)

            # Deploy pipeline
            result = await self.fabric_service.create_pipeline(
                workspace_id=state.workspace_id,
                pipeline_name=pipeline_def["name"],
                pipeline_definition=pipeline_def
            )

            if result.get("success"):
                # Deploy notebooks if any
                for notebook in self._generate_notebooks(state):
                    await self.fabric_service.create_notebook(
                        workspace_id=state.workspace_id,
                        notebook_name=notebook["name"],
                        notebook_content=notebook["code"]
                    )

            return result

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
