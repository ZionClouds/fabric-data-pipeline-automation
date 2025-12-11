"""
Spark Models for Microsoft Fabric SDK

Contains models for spark operations including custom pools and livy sessions.

Converted from: knowledge/fabric/spark/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, Principal, GroupType, PrincipalType


# =============================================================================
# ENUMS
# =============================================================================

class CustomPoolType(str, Enum):
    """Custom pool type."""
    CAPACITY = "Capacity"
    WORKSPACE = "Workspace"


class ItemReferenceType(str, Enum):
    """The Item reference type."""
    BY_ID = "ById"


class JobType(str, Enum):
    """Type of the job."""
    JUPYTER_SESSION = "JupyterSession"
    SPARK_BATCH = "SparkBatch"
    SPARK_SESSION = "SparkSession"
    UNKNOWN = "Unknown"


class LivySessionItemType(str, Enum):
    """The item type."""
    LAKEHOUSE = "Lakehouse"
    NOTEBOOK = "Notebook"
    SPARK_JOB_DEFINITION = "SparkJobDefinition"


class NodeFamily(str, Enum):
    """Node family."""
    MEMORY_OPTIMIZED = "MemoryOptimized"


class NodeSize(str, Enum):
    """Node size."""
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    X_LARGE = "XLarge"
    XX_LARGE = "XXLarge"


class Origin(str, Enum):
    """Origin of the job."""
    PENDING_JOB = "PendingJob"
    SUBMITTED_JOB = "SubmittedJob"


class State(str, Enum):
    """Current state of the job."""
    CANCELLED = "Cancelled"
    FAILED = "Failed"
    IN_PROGRESS = "InProgress"
    NOT_STARTED = "NotStarted"
    SUCCEEDED = "Succeeded"
    UNKNOWN = "Unknown"


class TimeUnit(str, Enum):
    """The unit of time for the duration."""
    DAYS = "Days"
    HOURS = "Hours"
    MINUTES = "Minutes"
    SECONDS = "Seconds"


# =============================================================================
# MODELS
# =============================================================================

class AutoScale(BaseModel):
    """Auto scale properties."""
    enabled: bool = Field(..., description="Whether the auto scale is enabled")
    max_node_count: int = Field(..., alias="maxNodeCount", description="The maximum node count")
    min_node_count: int = Field(..., alias="minNodeCount", description="The minimum node count")


class DynamicExecutorAllocation(BaseModel):
    """Dynamic executor allocation properties."""
    enabled: bool = Field(..., description="Whether the dynamic executor allocation is enabled")
    max_executors: int = Field(..., alias="maxExecutors", description="The maximum number of executors")
    min_executors: int = Field(..., alias="minExecutors", description="The minimum number of executors")


class SparkProperties(BaseModel):
    """Spark properties."""
    auto_scale: Optional[AutoScale] = Field(None, alias="autoScale", description="Auto scale properties")
    default_spark_pool_id: Optional[str] = Field(None, alias="defaultSparkPoolId", description="The default spark pool id")
    dynamic_executor_allocation: Optional[DynamicExecutorAllocation] = Field(None, alias="dynamicExecutorAllocation", description="Dynamic executor allocation properties")


class CreateCustomPoolRequest(BaseModel):
    """Create custom pool request."""
    name: str = Field(..., description="Name of the custom pool")
    auto_scale: Optional[AutoScale] = Field(None, alias="autoScale", description="Auto scale settings")
    dynamic_executor_allocation: Optional[DynamicExecutorAllocation] = Field(None, alias="dynamicExecutorAllocation", description="Dynamic executor allocation settings")
    node_family: Optional[NodeFamily] = Field(None, alias="nodeFamily", description="Node family")
    node_size: Optional[NodeSize] = Field(None, alias="nodeSize", description="Node size")


class CustomPool(BaseModel):
    """A custom pool."""
    id: str = Field(..., description="ID of the custom pool")
    name: str = Field(..., description="Name of the custom pool")
    type: CustomPoolType = Field(..., description="Type of the custom pool")
    auto_scale: Optional[AutoScale] = Field(None, alias="autoScale", description="Auto scale settings")
    dynamic_executor_allocation: Optional[DynamicExecutorAllocation] = Field(None, alias="dynamicExecutorAllocation", description="Dynamic executor allocation settings")
    node_family: Optional[NodeFamily] = Field(None, alias="nodeFamily", description="Node family")
    node_size: Optional[NodeSize] = Field(None, alias="nodeSize", description="Node size")


class CustomPools(BaseModel):
    """A paginated list of custom pools."""
    value: List[CustomPool] = Field(..., description="A list of custom pools")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")


class Duration(BaseModel):
    """A duration."""
    time_unit: TimeUnit = Field(..., alias="timeUnit", description="The unit of time for the duration")
    value: float = Field(..., description="The number of timeUnits in the duration")


class ItemReference(BaseModel):
    """An item reference object."""
    reference_type: ItemReferenceType = Field(..., alias="referenceType", description="The item reference type")


class ItemReferenceByID(ItemReference):
    """An item reference by ID object."""
    item_id: str = Field(..., alias="itemId", description="The ID of the item")
    workspace_id: str = Field(..., alias="workspaceId", description="The workspace ID of the item")


class PrincipalGroupDetails(BaseModel):
    """Group specific details. Applicable when the principal type is Group."""
    group_type: Optional[GroupType] = Field(None, alias="groupType", description="The type of the group")


class PrincipalServicePrincipalDetails(BaseModel):
    """Service principal specific details. Applicable when the principal type is ServicePrincipal."""
    aad_app_id: Optional[str] = Field(None, alias="aadAppId", description="The service principal's Microsoft Entra AppId")


class PrincipalServicePrincipalProfileDetails(BaseModel):
    """Service principal profile details. Applicable when the principal type is ServicePrincipalProfile."""
    parent_principal: Optional[Principal] = Field(None, alias="parentPrincipal", description="The service principal profile's parent principal")


class PrincipalUserDetails(BaseModel):
    """User principal specific details. Applicable when the principal type is User."""
    user_principal_name: Optional[str] = Field(None, alias="userPrincipalName", description="The user principal name")


class LivySession(BaseModel):
    """The livy session response."""
    attempt_number: Optional[int] = Field(None, alias="attemptNumber", description="Current attempt number")
    cancellation_reason: Optional[str] = Field(None, alias="cancellationReason", description="Reason for the job cancellation")
    capacity_id: Optional[str] = Field(None, alias="capacityId", description="ID of the capacity")
    consumer_id: Optional[Principal] = Field(None, alias="consumerId", description="ID of the consumer")
    creator_item: Optional[ItemReferenceByID] = Field(None, alias="creatorItem", description="ID of the item creator")
    driver_cores: Optional[int] = Field(None, alias="driverCores", description="The number of CPU cores allocated to the Spark driver")
    driver_memory: Optional[int] = Field(None, alias="driverMemory", description="The amount of memory (in GB) assigned to the Spark driver process")
    dynamic_allocation_max_executors: Optional[int] = Field(None, alias="dynamicAllocationMaxExecutors", description="Sets the maximum number of executors")
    end_date_time: Optional[datetime] = Field(None, alias="endDateTime", description="Timestamp when the job ended in UTC")
    executor_cores: Optional[Any] = Field(None, alias="executorCores", description="The number of CPU cores allocated to each Spark executor")
    executor_memory: Optional[int] = Field(None, alias="executorMemory", description="The amount of memory (in GB) assigned to each Spark executor process")
    is_dynamic_allocation_enabled: Optional[bool] = Field(None, alias="isDynamicAllocationEnabled", description="Flag indicating whether dynamic allocation is enabled")
    is_high_concurrency: Optional[bool] = Field(None, alias="isHighConcurrency", description="Flag indicating high concurrency")
    item: Optional[ItemReferenceByID] = Field(None, description="ID of the item")
    item_name: Optional[str] = Field(None, alias="itemName", description="Name of the item")
    item_type: Optional[LivySessionItemType] = Field(None, alias="itemType", description="The item type")
    job_instance_id: Optional[str] = Field(None, alias="jobInstanceId", description="ID of the job instance")
    job_type: Optional[JobType] = Field(None, alias="jobType", description="Current state of the job")
    livy_id: Optional[str] = Field(None, alias="livyId", description="ID of the Livy session or Livy batch")
    livy_name: Optional[str] = Field(None, alias="livyName", description="Name of the Livy session or Livy batch")
    livy_session_item_resource_uri: Optional[str] = Field(None, alias="livySessionItemResourceUri", description="The URI used to retrieve all Livy sessions for a given item")
    max_number_of_attempts: Optional[int] = Field(None, alias="maxNumberOfAttempts", description="Maximum number of attempts")
    num_executors: Optional[int] = Field(None, alias="numExecutors", description="The total number of executors requested for the Spark job")
    operation_name: Optional[str] = Field(None, alias="operationName", description="Name of the operation")
    origin: Optional[Origin] = Field(None, description="Origin of the job")
    queued_duration: Optional[Duration] = Field(None, alias="queuedDuration", description="Duration for which the job was queued")
    running_duration: Optional[Duration] = Field(None, alias="runningDuration", description="Time it took the job to run")
    runtime_version: Optional[str] = Field(None, alias="runtimeVersion", description="The fabric runtime version")
    spark_application_id: Optional[str] = Field(None, alias="sparkApplicationId", description="A Spark application ID")
    start_date_time: Optional[datetime] = Field(None, alias="startDateTime", description="Timestamp when the job started in UTC")
    state: Optional[State] = Field(None, description="Current state of the job")
    submitted_date_time: Optional[datetime] = Field(None, alias="submittedDateTime", description="Timestamp when the job was submitted in UTC")
    submitter: Optional[Principal] = Field(None, description="ID of the submitter")
    total_duration: Optional[Duration] = Field(None, alias="totalDuration", description="Total duration of the job")


class LivySessions(BaseModel):
    """A paginated list of livy sessions."""
    value: List[LivySession] = Field(..., description="A list of livy sessions")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")


class UpdateCustomPoolRequest(BaseModel):
    """Update custom pool request."""
    auto_scale: Optional[AutoScale] = Field(None, alias="autoScale", description="Auto scale settings")
    dynamic_executor_allocation: Optional[DynamicExecutorAllocation] = Field(None, alias="dynamicExecutorAllocation", description="Dynamic executor allocation settings")
    name: Optional[str] = Field(None, description="Name of the custom pool")
    node_family: Optional[NodeFamily] = Field(None, alias="nodeFamily", description="Node family")
    node_size: Optional[NodeSize] = Field(None, alias="nodeSize", description="Node size")


class UpdateWorkspaceSparkSettingsRequest(BaseModel):
    """Update workspace spark settings request."""
    automatic_log: Optional[bool] = Field(None, alias="automaticLog", description="Enable automatic log for the workspace")
    environment: Optional[ItemReferenceByID] = Field(None, description="Environment for the workspace")
    high_concurrency: Optional[bool] = Field(None, alias="highConcurrency", description="Enable high concurrency for the workspace")
    pool: Optional[CustomPool] = Field(None, description="Pool for the workspace")
    spark_properties: Optional[SparkProperties] = Field(None, alias="sparkProperties", description="Spark properties for the workspace")


class WorkspaceSparkSettings(BaseModel):
    """Workspace spark settings."""
    automatic_log: Optional[bool] = Field(None, alias="automaticLog", description="Enable automatic log for the workspace")
    environment: Optional[ItemReferenceByID] = Field(None, description="Environment for the workspace")
    high_concurrency: Optional[bool] = Field(None, alias="highConcurrency", description="Enable high concurrency for the workspace")
    pool: Optional[CustomPool] = Field(None, description="Pool for the workspace")
    spark_properties: Optional[SparkProperties] = Field(None, alias="sparkProperties", description="Spark properties for the workspace")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "CustomPoolType",
    "ItemReferenceType",
    "JobType",
    "LivySessionItemType",
    "NodeFamily",
    "NodeSize",
    "Origin",
    "State",
    "TimeUnit",
    # Models
    "AutoScale",
    "DynamicExecutorAllocation",
    "SparkProperties",
    "CreateCustomPoolRequest",
    "CustomPool",
    "CustomPools",
    "Duration",
    "ItemReference",
    "ItemReferenceByID",
    "PrincipalGroupDetails",
    "PrincipalServicePrincipalDetails",
    "PrincipalServicePrincipalProfileDetails",
    "PrincipalUserDetails",
    "LivySession",
    "LivySessions",
    "UpdateCustomPoolRequest",
    "UpdateWorkspaceSparkSettingsRequest",
    "WorkspaceSparkSettings",
]
