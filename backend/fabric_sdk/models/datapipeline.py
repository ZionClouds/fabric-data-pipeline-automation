"""
Data Pipeline Models for Microsoft Fabric SDK

Contains models for data pipeline operations including:
- Create/Update/Delete data pipelines
- Pipeline definitions
- Pipeline activities

Converted from: knowledge/fabric/datapipeline/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, PayloadType, Definition, DefinitionPart


# =============================================================================
# ENUMS
# =============================================================================

class DataPipelineItemType(str, Enum):
    """Data pipeline item type."""
    DATA_PIPELINE = "DataPipeline"


# =============================================================================
# DATA PIPELINE MODELS
# =============================================================================

class CreateDataPipelineRequest(BaseModel):
    """Create data pipeline request payload."""
    display_name: str = Field(..., alias="displayName", description="The data pipeline display name")
    description: Optional[str] = Field(None, description="The data pipeline description. Max 256 characters.")
    definition: Optional[Definition] = Field(None, description="The data pipeline public definition")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")

    class Config:
        populate_by_name = True


class DataPipeline(BaseModel):
    """A data pipeline object."""
    id: Optional[str] = Field(None, description="The item ID")
    type: Optional[ItemType] = Field(None, description="The item type")
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)

    class Config:
        populate_by_name = True


class DataPipelines(BaseModel):
    """A list of data pipelines."""
    value: List[DataPipeline] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateDataPipelineRequest(BaseModel):
    """Update data pipeline request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class UpdateDataPipelineDefinitionRequest(BaseModel):
    """Update data pipeline definition request."""
    definition: Definition = Field(..., description="Data pipeline public definition object")

    class Config:
        populate_by_name = True


class DataPipelineDefinitionResponse(BaseModel):
    """Data pipeline definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


# =============================================================================
# PIPELINE CONTENT MODELS (JSON Definition Structure)
# =============================================================================

class Expression(BaseModel):
    """Expression object for dynamic values."""
    value: str = Field(..., description="The expression value")
    type: str = Field(default="Expression", description="The expression type")

    class Config:
        populate_by_name = True


class ActivityDependency(BaseModel):
    """Dependency configuration for an activity."""
    activity: str = Field(..., description="The name of the activity to depend on")
    dependency_conditions: List[str] = Field(
        default_factory=lambda: ["Succeeded"],
        alias="dependencyConditions",
        description="Conditions: Succeeded, Failed, Skipped, Completed"
    )

    class Config:
        populate_by_name = True


class ActivityPolicy(BaseModel):
    """Policy configuration for an activity."""
    timeout: str = Field(default="0.12:00:00", description="Activity timeout")
    retry: int = Field(default=0, description="Number of retries")
    retry_interval_in_seconds: int = Field(
        default=30, alias="retryIntervalInSeconds", description="Retry interval"
    )
    secure_output: bool = Field(default=False, alias="secureOutput")
    secure_input: bool = Field(default=False, alias="secureInput")

    class Config:
        populate_by_name = True


class PipelineVariable(BaseModel):
    """Pipeline variable definition."""
    type: str = Field(..., description="Variable type: String, Bool, Array, Object")
    default_value: Any = Field(None, alias="defaultValue", description="Default value")

    class Config:
        populate_by_name = True


class PipelineParameter(BaseModel):
    """Pipeline parameter definition."""
    type: str = Field(..., description="Parameter type: String, Int, Float, Bool, Array, Object, SecureString")
    default_value: Any = Field(None, alias="defaultValue", description="Default value")

    class Config:
        populate_by_name = True


# =============================================================================
# ACTIVITY TYPE PROPERTIES
# =============================================================================

class CopySourceSettings(BaseModel):
    """Copy activity source settings."""
    type: str = Field(..., description="Source type (e.g., BinarySource, DelimitedTextSource)")
    store_settings: Optional[Dict[str, Any]] = Field(None, alias="storeSettings")
    format_settings: Optional[Dict[str, Any]] = Field(None, alias="formatSettings")

    class Config:
        populate_by_name = True


class CopySinkSettings(BaseModel):
    """Copy activity sink settings."""
    type: str = Field(..., description="Sink type (e.g., BinarySink, LakehouseTableSink)")
    store_settings: Optional[Dict[str, Any]] = Field(None, alias="storeSettings")
    table_action_option: Optional[str] = Field(None, alias="tableActionOption")

    class Config:
        populate_by_name = True


class DatasetReference(BaseModel):
    """Reference to a dataset."""
    reference_name: str = Field(..., alias="referenceName")
    type: str = Field(default="DatasetReference")
    parameters: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class LinkedServiceReference(BaseModel):
    """Reference to a linked service."""
    reference_name: str = Field(..., alias="referenceName")
    type: str = Field(default="LinkedServiceReference")
    parameters: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class ExternalReferences(BaseModel):
    """External references for activities (e.g., connection ID)."""
    connection: Optional[str] = Field(None, description="Connection ID (GUID)")

    class Config:
        populate_by_name = True


class DatasetSettings(BaseModel):
    """Inline dataset settings for activities."""
    type: str = Field(..., description="Dataset type (e.g., LakehouseFolder, Binary)")
    linked_service: Optional[Dict[str, Any]] = Field(None, alias="linkedService")
    type_properties: Optional[Dict[str, Any]] = Field(None, alias="typeProperties")

    class Config:
        populate_by_name = True


# =============================================================================
# ACTIVITY DEFINITIONS
# =============================================================================

class BaseActivity(BaseModel):
    """Base activity model."""
    name: str = Field(..., description="Activity name")
    type: str = Field(..., description="Activity type")
    depends_on: List[ActivityDependency] = Field(default_factory=list, alias="dependsOn")
    policy: Optional[ActivityPolicy] = Field(None)
    user_properties: Optional[List[Dict[str, Any]]] = Field(None, alias="userProperties")

    class Config:
        populate_by_name = True


class CopyActivityTypeProperties(BaseModel):
    """Type properties for Copy activity."""
    source: CopySourceSettings = Field(...)
    sink: CopySinkSettings = Field(...)
    enable_staging: bool = Field(default=False, alias="enableStaging")
    translator: Optional[Dict[str, Any]] = Field(None)
    parallel_copies: Optional[int] = Field(None, alias="parallelCopies")
    data_integration_units: Optional[int] = Field(None, alias="dataIntegrationUnits")

    class Config:
        populate_by_name = True


class CopyActivity(BaseActivity):
    """Copy activity definition."""
    type: str = Field(default="Copy")
    type_properties: CopyActivityTypeProperties = Field(..., alias="typeProperties")
    inputs: Optional[List[DatasetReference]] = Field(None)
    outputs: Optional[List[DatasetReference]] = Field(None)
    external_references: Optional[ExternalReferences] = Field(None, alias="externalReferences")

    class Config:
        populate_by_name = True


class ForEachActivityTypeProperties(BaseModel):
    """Type properties for ForEach activity."""
    items: Expression = Field(..., description="Items to iterate over")
    is_sequential: bool = Field(default=False, alias="isSequential")
    batch_count: Optional[int] = Field(None, alias="batchCount", description="Max parallel iterations")
    activities: List[Dict[str, Any]] = Field(default_factory=list, description="Nested activities")

    class Config:
        populate_by_name = True


class ForEachActivity(BaseActivity):
    """ForEach activity definition."""
    type: str = Field(default="ForEach")
    type_properties: ForEachActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class IfConditionActivityTypeProperties(BaseModel):
    """Type properties for IfCondition activity."""
    expression: Expression = Field(..., description="Condition expression")
    if_true_activities: List[Dict[str, Any]] = Field(
        default_factory=list, alias="ifTrueActivities"
    )
    if_false_activities: List[Dict[str, Any]] = Field(
        default_factory=list, alias="ifFalseActivities"
    )

    class Config:
        populate_by_name = True


class IfConditionActivity(BaseActivity):
    """IfCondition activity definition."""
    type: str = Field(default="IfCondition")
    type_properties: IfConditionActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class SetVariableActivityTypeProperties(BaseModel):
    """Type properties for SetVariable activity."""
    variable_name: str = Field(..., alias="variableName")
    value: Any = Field(..., description="Value to set (can be Expression)")
    set_system_variable: Optional[bool] = Field(None, alias="setSystemVariable")

    class Config:
        populate_by_name = True


class SetVariableActivity(BaseActivity):
    """SetVariable activity definition."""
    type: str = Field(default="SetVariable")
    type_properties: SetVariableActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class AppendVariableActivityTypeProperties(BaseModel):
    """Type properties for AppendVariable activity."""
    variable_name: str = Field(..., alias="variableName")
    value: Any = Field(..., description="Value to append")

    class Config:
        populate_by_name = True


class AppendVariableActivity(BaseActivity):
    """AppendVariable activity definition."""
    type: str = Field(default="AppendVariable")
    type_properties: AppendVariableActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class FilterActivityTypeProperties(BaseModel):
    """Type properties for Filter activity."""
    items: Expression = Field(..., description="Items to filter")
    condition: Expression = Field(..., description="Filter condition")

    class Config:
        populate_by_name = True


class FilterActivity(BaseActivity):
    """Filter activity definition."""
    type: str = Field(default="Filter")
    type_properties: FilterActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class GetMetadataActivityTypeProperties(BaseModel):
    """Type properties for GetMetadata activity."""
    field_list: List[str] = Field(
        default_factory=lambda: ["childItems"],
        alias="fieldList",
        description="Fields to retrieve: childItems, itemName, itemType, size, lastModified, etc."
    )
    dataset: Optional[DatasetReference] = Field(None)
    dataset_settings: Optional[DatasetSettings] = Field(None, alias="datasetSettings")
    store_settings: Optional[Dict[str, Any]] = Field(None, alias="storeSettings")
    format_settings: Optional[Dict[str, Any]] = Field(None, alias="formatSettings")

    class Config:
        populate_by_name = True


class GetMetadataActivity(BaseActivity):
    """GetMetadata activity definition."""
    type: str = Field(default="GetMetadata")
    type_properties: GetMetadataActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class ScriptActivityTypeProperties(BaseModel):
    """Type properties for Script activity."""
    scripts: List[Dict[str, Any]] = Field(..., description="SQL scripts to execute")
    script_block_execution_timeout: Optional[str] = Field(
        None, alias="scriptBlockExecutionTimeout"
    )
    log_settings: Optional[Dict[str, Any]] = Field(None, alias="logSettings")
    database: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ScriptActivity(BaseActivity):
    """Script activity definition."""
    type: str = Field(default="Script")
    type_properties: ScriptActivityTypeProperties = Field(..., alias="typeProperties")
    external_references: Optional[ExternalReferences] = Field(None, alias="externalReferences")
    linked_service: Optional[LinkedServiceReference] = Field(None, alias="linkedService")

    class Config:
        populate_by_name = True


class TridentNotebookActivityTypeProperties(BaseModel):
    """Type properties for TridentNotebook (Fabric Notebook) activity."""
    notebook_id: str = Field(..., alias="notebookId")
    workspace_id: str = Field(..., alias="workspaceId")
    parameters: Optional[Dict[str, Any]] = Field(None)
    spark_pool: Optional[str] = Field(None, alias="sparkPool")
    configuration: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class TridentNotebookActivity(BaseActivity):
    """TridentNotebook (Fabric Notebook) activity definition."""
    type: str = Field(default="TridentNotebook")
    type_properties: TridentNotebookActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class WaitActivityTypeProperties(BaseModel):
    """Type properties for Wait activity."""
    wait_time_in_seconds: int = Field(..., alias="waitTimeInSeconds")

    class Config:
        populate_by_name = True


class WaitActivity(BaseActivity):
    """Wait activity definition."""
    type: str = Field(default="Wait")
    type_properties: WaitActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class FailActivityTypeProperties(BaseModel):
    """Type properties for Fail activity."""
    message: Any = Field(..., description="Error message (can be Expression)")
    error_code: Any = Field(..., alias="errorCode", description="Error code (can be Expression)")

    class Config:
        populate_by_name = True


class FailActivity(BaseActivity):
    """Fail activity definition."""
    type: str = Field(default="Fail")
    type_properties: FailActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class WebActivityTypeProperties(BaseModel):
    """Type properties for Web activity."""
    method: str = Field(..., description="HTTP method: GET, POST, PUT, DELETE, PATCH")
    url: Any = Field(..., description="URL (can be Expression)")
    headers: Optional[Dict[str, Any]] = Field(None)
    body: Optional[Any] = Field(None)
    authentication: Optional[Dict[str, Any]] = Field(None)
    disable_cert_validation: Optional[bool] = Field(None, alias="disableCertValidation")
    timeout: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class WebActivity(BaseActivity):
    """Web activity definition."""
    type: str = Field(default="WebActivity")
    type_properties: WebActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class LookupActivityTypeProperties(BaseModel):
    """Type properties for Lookup activity."""
    source: Dict[str, Any] = Field(..., description="Source configuration")
    dataset: Optional[DatasetReference] = Field(None)
    first_row_only: Optional[bool] = Field(None, alias="firstRowOnly")

    class Config:
        populate_by_name = True


class LookupActivity(BaseActivity):
    """Lookup activity definition."""
    type: str = Field(default="Lookup")
    type_properties: LookupActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class ExecutePipelineActivityTypeProperties(BaseModel):
    """Type properties for ExecutePipeline activity."""
    pipeline: Dict[str, Any] = Field(..., description="Pipeline reference")
    wait_on_completion: Optional[bool] = Field(None, alias="waitOnCompletion")
    parameters: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class ExecutePipelineActivity(BaseActivity):
    """ExecutePipeline activity definition."""
    type: str = Field(default="ExecutePipeline")
    type_properties: ExecutePipelineActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class SwitchActivityTypeProperties(BaseModel):
    """Type properties for Switch activity."""
    on: Expression = Field(..., description="Expression to evaluate")
    cases: List[Dict[str, Any]] = Field(default_factory=list, description="Case definitions")
    default_activities: List[Dict[str, Any]] = Field(
        default_factory=list, alias="defaultActivities"
    )

    class Config:
        populate_by_name = True


class SwitchActivity(BaseActivity):
    """Switch activity definition."""
    type: str = Field(default="Switch")
    type_properties: SwitchActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class UntilActivityTypeProperties(BaseModel):
    """Type properties for Until activity."""
    expression: Expression = Field(..., description="Loop condition")
    timeout: Optional[str] = Field(None)
    activities: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class UntilActivity(BaseActivity):
    """Until activity definition."""
    type: str = Field(default="Until")
    type_properties: UntilActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class Office365EmailActivityTypeProperties(BaseModel):
    """Type properties for Office365Email activity."""
    to: str = Field(..., description="Recipient email address")
    subject: Any = Field(..., description="Email subject (can be Expression)")
    body: Any = Field(..., description="Email body (can be Expression)")
    cc: Optional[str] = Field(None)
    bcc: Optional[str] = Field(None)
    attachments: Optional[List[Dict[str, Any]]] = Field(None)

    class Config:
        populate_by_name = True


class Office365EmailActivity(BaseActivity):
    """Office365Email activity definition."""
    type: str = Field(default="Office365Email")
    type_properties: Office365EmailActivityTypeProperties = Field(..., alias="typeProperties")
    external_references: Optional[ExternalReferences] = Field(None, alias="externalReferences")

    class Config:
        populate_by_name = True


class RefreshDataflowActivityTypeProperties(BaseModel):
    """Type properties for RefreshDataflow (Dataflow Gen2) activity."""
    dataflow_id: str = Field(..., alias="dataflowId")
    workspace_id: str = Field(..., alias="workspaceId")
    notify_option: str = Field(
        default="NoNotification",
        alias="notifyOption",
        description="NoNotification, OnCompletion, OnFailure"
    )
    dataflow_type: str = Field(default="DataflowFabric", alias="dataflowType")

    class Config:
        populate_by_name = True


class RefreshDataflowActivity(BaseActivity):
    """RefreshDataflow activity definition."""
    type: str = Field(default="RefreshDataflow")
    type_properties: RefreshDataflowActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


class InvokeCopyJobActivityTypeProperties(BaseModel):
    """Type properties for InvokeCopyJob activity."""
    copy_job_id: str = Field(..., alias="copyJobId")
    workspace_id: str = Field(..., alias="workspaceId")

    class Config:
        populate_by_name = True


class InvokeCopyJobActivity(BaseActivity):
    """InvokeCopyJob activity definition."""
    type: str = Field(default="InvokeCopyJob")
    type_properties: InvokeCopyJobActivityTypeProperties = Field(..., alias="typeProperties")

    class Config:
        populate_by_name = True


# =============================================================================
# PIPELINE DEFINITION (Complete Pipeline JSON Structure)
# =============================================================================

class PipelineProperties(BaseModel):
    """Pipeline properties containing activities and configuration."""
    activities: List[Dict[str, Any]] = Field(default_factory=list, description="List of activities")
    variables: Optional[Dict[str, PipelineVariable]] = Field(None)
    parameters: Optional[Dict[str, PipelineParameter]] = Field(None)
    annotations: Optional[List[str]] = Field(None)
    folder: Optional[Dict[str, str]] = Field(None)
    concurrency: Optional[int] = Field(None)
    last_publish_time: Optional[str] = Field(None, alias="lastPublishTime")

    class Config:
        populate_by_name = True


class PipelineDefinitionContent(BaseModel):
    """Complete pipeline definition content (JSON structure)."""
    properties: PipelineProperties = Field(...)

    class Config:
        populate_by_name = True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_expression(value: str) -> Expression:
    """Create an expression object."""
    return Expression(value=value, type="Expression")


def create_dependency(activity_name: str, conditions: List[str] = None) -> ActivityDependency:
    """Create an activity dependency."""
    return ActivityDependency(
        activity=activity_name,
        dependency_conditions=conditions or ["Succeeded"]
    )


def create_variable(var_type: str, default_value: Any = None) -> PipelineVariable:
    """Create a pipeline variable."""
    return PipelineVariable(type=var_type, default_value=default_value)
