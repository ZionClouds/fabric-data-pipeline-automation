"""
Sparkjobdefinition Models for Microsoft Fabric SDK

Contains models for spark job definition operations.

Converted from: knowledge/fabric/sparkjobdefinition/models.go and constants.go
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


class Origin(str, Enum):
    """Origin of the job."""
    PENDING_JOB = "PendingJob"
    SUBMITTED_JOB = "SubmittedJob"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


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


class ExecutionData(BaseModel):
    """Execution data for spark job definition run if customer wants to override default values."""
    additional_library_uris: Optional[List[str]] = Field(None, alias="additionalLibraryUris", description="List of additional library paths needed for execution")
    command_line_arguments: Optional[str] = Field(None, alias="commandLineArguments", description="Command line arguments. The arguments are space separated")
    default_lakehouse_id: Optional[Union[ItemReference, ItemReferenceByID]] = Field(None, alias="defaultLakehouseId", description="The lakehouse ID that will be used as the default lakehouse")
    environment_id: Optional[Union[ItemReference, ItemReferenceByID]] = Field(None, alias="environmentId", description="The environment ID that will be used for the Spark job definition")
    executable_file: Optional[str] = Field(None, alias="executableFile", description="Executable main file to be used. The path must be an abfs path")
    main_class: Optional[str] = Field(None, alias="mainClass", description="Main class name to be used. This is not needed for python and r executable files")


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


class Properties(BaseModel):
    """The spark job definition properties."""
    one_lake_root_path: str = Field(..., alias="oneLakeRootPath", description="OneLake path to the SparkJobDefinition root directory")


class PublicDefinitionPart(BaseModel):
    """Spark job definition definition part object."""
    path: Optional[str] = Field(None, description="The spark job definition public definition part path")
    payload: Optional[str] = Field(None, description="The spark job definition public definition part payload")
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType", description="The payload type")


class PublicDefinition(BaseModel):
    """Spark job definition public definition object."""
    parts: List[PublicDefinitionPart] = Field(..., description="A list of definition parts")
    format: Optional[str] = Field(None, description="The format of the item definition. Supported format: SparkJobDefinitionV1")


class Response(BaseModel):
    """Spark job definition public definition response."""
    definition: Optional[PublicDefinition] = Field(None, description="Spark job definition public definition object")


class RunSparkJobDefinitionRequest(BaseModel):
    """Run spark job definition request with executionData."""
    execution_data: Optional[ExecutionData] = Field(None, alias="executionData", description="The spark job definition parameters to be used during execution")


class SparkJobDefinition(BaseModel):
    """A spark job definition object."""
    type: ItemType = Field(..., description="The item type")
    description: Optional[str] = Field(None, description="The item description")
    display_name: Optional[str] = Field(None, alias="displayName", description="The item display name")
    properties: Optional[Properties] = Field(None, description="The spark job definition properties")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")
    id: Optional[str] = Field(None, description="The item ID")
    tags: Optional[List[ItemTag]] = Field(None, description="List of applied tags")
    workspace_id: Optional[str] = Field(None, alias="workspaceId", description="The workspace ID")


class SparkJobDefinitions(BaseModel):
    """A list of spark job definitions."""
    value: List[SparkJobDefinition] = Field(..., description="A list of spark job definitions")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")


class CreateSparkJobDefinitionRequest(BaseModel):
    """Create spark job definition request payload."""
    display_name: str = Field(..., alias="displayName", description="The spark job definition display name")
    definition: Optional[PublicDefinition] = Field(None, description="The spark job definition public definition")
    description: Optional[str] = Field(None, description="The spark job definition description. Maximum length is 256 characters")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")


class UpdateSparkJobDefinitionDefinitionRequest(BaseModel):
    """Update spark job definition public definition request payload."""
    definition: PublicDefinition = Field(..., description="Spark job definition public definition object")


class UpdateSparkJobDefinitionRequest(BaseModel):
    """Update spark job definition request."""
    description: Optional[str] = Field(None, description="The spark job definition description. Maximum length is 256 characters")
    display_name: Optional[str] = Field(None, alias="displayName", description="The spark job definition display name")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ItemReferenceType",
    "JobType",
    "LivySessionItemType",
    "Origin",
    "PayloadType",
    "State",
    "TimeUnit",
    # Models
    "Duration",
    "ItemReference",
    "ItemReferenceByID",
    "ExecutionData",
    "PrincipalGroupDetails",
    "PrincipalServicePrincipalDetails",
    "PrincipalServicePrincipalProfileDetails",
    "PrincipalUserDetails",
    "LivySession",
    "LivySessions",
    "Properties",
    "PublicDefinitionPart",
    "PublicDefinition",
    "Response",
    "RunSparkJobDefinitionRequest",
    "SparkJobDefinition",
    "SparkJobDefinitions",
    "CreateSparkJobDefinitionRequest",
    "UpdateSparkJobDefinitionDefinitionRequest",
    "UpdateSparkJobDefinitionRequest",
]
