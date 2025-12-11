"""
Pipeline Generator for AI Pipeline Service

Generates Microsoft Fabric pipeline JSON using the SDK activity builders.
"""

from __future__ import annotations
import json
import logging
from typing import Optional, List, Dict, Any

from services.ai_pipeline.models import (
    PipelineConfig,
    DestinationType,
)

# Import activity builders from fabric_sdk
try:
    from fabric_sdk.activities import (
        PipelineBuilder,
        CopyActivity,
        ForEachActivity,
        GetMetadataActivity,
        NotebookActivity,
        SetVariableActivity,
        IfConditionActivity,
    )
    ACTIVITY_BUILDERS_AVAILABLE = True
except ImportError:
    ACTIVITY_BUILDERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class PipelineGenerator:
    """
    Generates Fabric pipeline definitions from configuration.

    Uses the SDK activity builders to create properly structured
    pipeline JSON for deployment to Microsoft Fabric.
    """

    def __init__(self):
        """Initialize the pipeline generator."""
        pass

    # =========================================================================
    # MAIN GENERATION METHOD
    # =========================================================================

    def generate_pipeline(
        self,
        config: PipelineConfig,
        notebook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete pipeline definition.

        Args:
            config: Pipeline configuration from chat service
            notebook_id: ID of the generated notebook (if PII/transformations needed)

        Returns:
            Pipeline definition ready for Fabric API
        """
        pipeline_name = config.pipeline_name or "GeneratedPipeline"

        # Determine pipeline type based on configuration
        if config.pii.enabled or config.transformations.enabled:
            # Complex pipeline with notebook
            return self._generate_pipeline_with_notebook(config, notebook_id)
        else:
            # Simple copy pipeline
            return self._generate_simple_copy_pipeline(config)

    # =========================================================================
    # PIPELINE GENERATORS
    # =========================================================================

    def _generate_simple_copy_pipeline(
        self,
        config: PipelineConfig
    ) -> Dict[str, Any]:
        """Generate a simple copy pipeline without transformations."""

        pipeline_name = config.pipeline_name or "SimpleCopyPipeline"

        # Build activities
        activities = []

        # Activity 1: GetMetadata - List files
        get_metadata = self._create_get_metadata_activity(config)
        activities.append(get_metadata)

        # Activity 2: ForEach - Iterate files
        # Activity 3: Copy - Inside ForEach
        copy_activity = self._create_copy_activity(config)
        foreach = self._create_foreach_activity(
            config,
            inner_activities=[copy_activity]
        )
        activities.append(foreach)

        # Build pipeline
        pipeline = {
            "name": pipeline_name,
            "properties": {
                "activities": activities,
                "parameters": self._generate_parameters(config),
                "variables": self._generate_variables(config),
                "annotations": [
                    "auto-generated",
                    "ai-pipeline-service"
                ]
            }
        }

        return pipeline

    def _generate_pipeline_with_notebook(
        self,
        config: PipelineConfig,
        notebook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a pipeline with notebook for PII/transformations."""

        pipeline_name = config.pipeline_name or "DataProcessingPipeline"

        activities = []

        # Activity 1: GetMetadata - List files
        get_metadata = self._create_get_metadata_activity(config)
        activities.append(get_metadata)

        # Activity 2: ForEach with Copy
        copy_activity = self._create_copy_activity(config, to_files=True)
        foreach = self._create_foreach_activity(
            config,
            inner_activities=[copy_activity]
        )
        activities.append(foreach)

        # Activity 3: Notebook - Process data (PII masking, transformations)
        notebook = self._create_notebook_activity(config, notebook_id)
        notebook["dependsOn"] = [
            {
                "activity": foreach["name"],
                "dependencyConditions": ["Succeeded"]
            }
        ]
        activities.append(notebook)

        # Build pipeline
        pipeline = {
            "name": pipeline_name,
            "properties": {
                "activities": activities,
                "parameters": self._generate_parameters(config),
                "variables": self._generate_variables(config),
                "annotations": [
                    "auto-generated",
                    "ai-pipeline-service",
                    "pii-detection" if config.pii.enabled else "no-pii"
                ]
            }
        }

        return pipeline

    # =========================================================================
    # ACTIVITY CREATORS
    # =========================================================================

    def _create_get_metadata_activity(self, config: PipelineConfig) -> Dict[str, Any]:
        """Create GetMetadata activity to list source files."""

        folder_path = config.source.folder_path or ""
        # Handle both enum and string file format
        file_format = config.source.file_format
        if file_format:
            format_value = file_format.value if hasattr(file_format, 'value') else file_format
            file_pattern = f"*.{format_value}"
        else:
            file_pattern = "*"

        return {
            "name": "GetFileList",
            "type": "GetMetadata",
            "dependsOn": [],
            "policy": {
                "timeout": "0.00:10:00",
                "retry": 2,
                "retryIntervalInSeconds": 30
            },
            "typeProperties": {
                "dataset": {
                    "referenceName": "SourceDataset",
                    "type": "DatasetReference",
                    "parameters": {
                        "folderPath": folder_path,
                        "filePattern": file_pattern
                    }
                },
                "fieldList": [
                    "childItems"
                ],
                "storeSettings": {
                    "type": "AzureBlobStorageReadSettings",
                    "recursive": True,
                    "enablePartitionDiscovery": False
                }
            }
        }

    def _create_foreach_activity(
        self,
        config: PipelineConfig,
        inner_activities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create ForEach activity to iterate over files."""

        return {
            "name": "ForEachFile",
            "type": "ForEach",
            "dependsOn": [
                {
                    "activity": "GetFileList",
                    "dependencyConditions": ["Succeeded"]
                }
            ],
            "typeProperties": {
                "items": {
                    "value": "@activity('GetFileList').output.childItems",
                    "type": "Expression"
                },
                "isSequential": False,
                "batchCount": 10,
                "activities": inner_activities
            }
        }

    def _create_copy_activity(
        self,
        config: PipelineConfig,
        to_files: bool = False
    ) -> Dict[str, Any]:
        """Create Copy activity."""

        # Determine sink location - handle both enum and string target values
        target = config.destination.target
        target_value = target.value if hasattr(target, 'value') else target
        if to_files or target_value == "Files":
            sink_path = f"Files/raw/{config.source.folder_path or 'data'}"
        else:
            sink_path = f"Tables/{config.destination.table_name or 'output'}"

        return {
            "name": "CopyData",
            "type": "Copy",
            "dependsOn": [],
            "policy": {
                "timeout": "0.01:00:00",
                "retry": 2,
                "retryIntervalInSeconds": 30
            },
            "typeProperties": {
                "source": {
                    "type": "BinarySource",
                    "storeSettings": {
                        "type": "AzureBlobStorageReadSettings",
                        "recursive": False
                    }
                },
                "sink": {
                    "type": "LakehouseTableSink",
                    "storeSettings": {
                        "type": "LakehouseWriteSettings"
                    },
                    "tableActionOption": "Append"
                },
                "enableStaging": False
            },
            "inputs": [
                {
                    "referenceName": "SourceDataset",
                    "type": "DatasetReference",
                    "parameters": {
                        "fileName": "@item().name"
                    }
                }
            ],
            "outputs": [
                {
                    "referenceName": "LakehouseDataset",
                    "type": "DatasetReference",
                    "parameters": {
                        "path": sink_path
                    }
                }
            ]
        }

    def _create_notebook_activity(
        self,
        config: PipelineConfig,
        notebook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Notebook activity for data processing."""

        notebook_name = f"{config.pipeline_name}_Notebook"

        activity = {
            "name": "ProcessData",
            "type": "TridentNotebook",
            "dependsOn": [],
            "policy": {
                "timeout": "0.02:00:00",
                "retry": 1,
                "retryIntervalInSeconds": 60
            },
            "typeProperties": {
                "notebookId": notebook_id or f"@pipeline().parameters.notebookId",
                "workspaceId": config.workspace_id or "@pipeline().parameters.workspaceId",
                "parameters": {
                    "source_path": {
                        "value": f"Files/raw/{config.source.folder_path or 'data'}/",
                        "type": "string"
                    },
                    "output_table": {
                        "value": config.destination.table_name or "output_table",
                        "type": "string"
                    }
                }
            }
        }

        # Add environment if PII detection is enabled
        if config.pii.enabled and config.environment_id:
            activity["typeProperties"]["environmentId"] = config.environment_id

        return activity

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _generate_parameters(self, config: PipelineConfig) -> Dict[str, Any]:
        """Generate pipeline parameters."""

        params = {
            "workspaceId": {
                "type": "string",
                "defaultValue": config.workspace_id or ""
            },
            "lakehouseId": {
                "type": "string",
                "defaultValue": config.lakehouse_id or ""
            }
        }

        if config.pii.enabled or config.transformations.enabled:
            params["notebookId"] = {
                "type": "string",
                "defaultValue": config.notebook_id or ""
            }

        return params

    def _generate_variables(self, config: PipelineConfig) -> Dict[str, Any]:
        """Generate pipeline variables."""

        return {
            "fileCount": {
                "type": "Integer",
                "defaultValue": 0
            },
            "processedCount": {
                "type": "Integer",
                "defaultValue": 0
            }
        }

    # =========================================================================
    # SCHEDULE GENERATION
    # =========================================================================

    def generate_schedule(self, config: PipelineConfig) -> Dict[str, Any]:
        """Generate schedule/trigger configuration."""

        if not config.schedule.enabled:
            return {}

        # Parse time
        time_parts = (config.schedule.time or "02:00").split(":")
        hour = int(time_parts[0]) if time_parts else 2
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        schedule = {
            "name": f"{config.pipeline_name}_Trigger",
            "properties": {
                "type": "ScheduleTrigger",
                "typeProperties": {
                    "recurrence": {
                        "frequency": self._map_frequency(config.schedule.frequency),
                        "interval": 1,
                        "startTime": "2024-01-01T00:00:00Z",
                        "timeZone": config.schedule.timezone or "UTC",
                        "schedule": {
                            "hours": [hour],
                            "minutes": [minute]
                        }
                    }
                },
                "pipelines": [
                    {
                        "pipelineReference": {
                            "referenceName": config.pipeline_name,
                            "type": "PipelineReference"
                        }
                    }
                ]
            }
        }

        return schedule

    def _map_frequency(self, frequency: str) -> str:
        """Map frequency string to Fabric schedule frequency."""

        frequency_map = {
            "hourly": "Hour",
            "daily": "Day",
            "weekly": "Week",
            "monthly": "Month"
        }

        return frequency_map.get(frequency.lower(), "Day")

    # =========================================================================
    # USING ACTIVITY BUILDERS (if available)
    # =========================================================================

    def generate_pipeline_with_builders(
        self,
        config: PipelineConfig,
        notebook_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate pipeline using SDK activity builders.

        This method uses the fluent API from fabric_sdk.activities.
        """

        if not ACTIVITY_BUILDERS_AVAILABLE:
            logger.warning("Activity builders not available, using fallback")
            return self.generate_pipeline(config, notebook_id)

        try:
            builder = PipelineBuilder(config.pipeline_name or "GeneratedPipeline")

            # Add variables
            builder.add_variable("fileCount", "Int", 0)
            builder.add_variable("processedCount", "Int", 0)

            # Add parameters
            builder.add_parameter("workspaceId", "String", config.workspace_id or "")
            builder.add_parameter("lakehouseId", "String", config.lakehouse_id or "")

            # Build GetMetadata activity
            get_metadata = GetMetadataActivity("GetFileList") \
                .for_dataset("SourceDataset") \
                .with_field_list(["childItems"]) \
                .build()

            builder.add_activity(get_metadata)

            # Build Copy activity
            copy = CopyActivity("CopyData") \
                .from_blob(
                    config.source.container or "container",
                    config.source.folder_path or ""
                ) \
                .to_lakehouse_files(
                    config.workspace_id or "",
                    config.lakehouse_id or "",
                    f"raw/{config.source.folder_path or 'data'}"
                ) \
                .build()

            # Build ForEach activity
            foreach = ForEachActivity("ForEachFile") \
                .iterate_over("@activity('GetFileList').output.childItems") \
                .with_activities([copy]) \
                .depends_on("GetFileList") \
                .build()

            builder.add_activity(foreach)

            # Add notebook if needed
            if config.pii.enabled or config.transformations.enabled:
                notebook = NotebookActivity("ProcessData") \
                    .with_notebook(
                        config.workspace_id or "",
                        notebook_id or ""
                    ) \
                    .depends_on("ForEachFile") \
                    .build()

                builder.add_activity(notebook)

            return builder.build()

        except Exception as e:
            logger.error(f"Failed to use activity builders: {e}")
            return self.generate_pipeline(config, notebook_id)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate_pipeline(self, pipeline: Dict[str, Any]) -> List[str]:
        """
        Validate a pipeline definition.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if "name" not in pipeline:
            errors.append("Pipeline must have a name")

        if "properties" not in pipeline:
            errors.append("Pipeline must have properties")
            return errors

        props = pipeline["properties"]

        if "activities" not in props or not props["activities"]:
            errors.append("Pipeline must have at least one activity")

        # Validate each activity
        for activity in props.get("activities", []):
            if "name" not in activity:
                errors.append("Each activity must have a name")
            if "type" not in activity:
                errors.append(f"Activity '{activity.get('name', 'unknown')}' must have a type")

        return errors
