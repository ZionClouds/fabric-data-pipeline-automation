"""
Lakehouse Models for Microsoft Fabric SDK

Contains models for lakehouse operations including:
- Create/Update/Delete lakehouses
- Tables and table maintenance
- SQL endpoints
- Livy sessions
- Scheduling

Converted from: knowledge/fabric/lakehouse/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, Principal


# =============================================================================
# ENUMS
# =============================================================================

class FileFormat(str, Enum):
    """Data file format types."""
    CSV = "Csv"
    PARQUET = "Parquet"
    JSON = "Json"
    AVRO = "Avro"
    ORC = "Orc"
    DELTA = "Delta"


class PathType(str, Enum):
    """Path type for load table operations."""
    FILE = "File"
    FOLDER = "Folder"


class ModeType(str, Enum):
    """Load table mode types."""
    OVERWRITE = "Overwrite"
    APPEND = "Append"


class TableType(str, Enum):
    """Table type in lakehouse."""
    MANAGED = "Managed"
    EXTERNAL = "External"


class SQLEndpointProvisioningStatus(str, Enum):
    """SQL endpoint provisioning status."""
    SUCCESS = "Success"
    IN_PROGRESS = "InProgress"
    FAILED = "Failed"


class ScheduleType(str, Enum):
    """Schedule configuration type."""
    CRON = "Cron"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


class TimeUnit(str, Enum):
    """Time unit for duration."""
    MINUTE = "Minute"
    HOUR = "Hour"
    DAY = "Day"
    SECOND = "Second"


class DayOfWeek(str, Enum):
    """Day of the week."""
    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"


class WeekIndex(str, Enum):
    """Week index for monthly schedules."""
    FIRST = "First"
    SECOND = "Second"
    THIRD = "Third"
    FOURTH = "Fourth"
    LAST = "Last"


class OccurrenceType(str, Enum):
    """Occurrence type for monthly schedules."""
    DAY_OF_MONTH = "DayOfMonth"
    ORDINAL_WEEKDAY = "OrdinalWeekday"


class State(str, Enum):
    """Livy session/job state."""
    NOT_STARTED = "NotStarted"
    STARTING = "Starting"
    RUNNING = "Running"
    IDLE = "Idle"
    BUSY = "Busy"
    SHUTTING_DOWN = "ShuttingDown"
    ERROR = "Error"
    DEAD = "Dead"
    KILLED = "Killed"
    SUCCESS = "Success"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class JobType(str, Enum):
    """Livy job type."""
    SPARK_JOB = "SparkJob"
    NOTEBOOK = "Notebook"


class Origin(str, Enum):
    """Job origin."""
    PIPELINE = "Pipeline"
    MANUAL = "Manual"
    SCHEDULED = "Scheduled"
    API = "Api"


class LivySessionItemType(str, Enum):
    """Livy session item type."""
    NOTEBOOK = "Notebook"
    SPARK_JOB_DEFINITION = "SparkJobDefinition"


class ItemReferenceType(str, Enum):
    """Item reference type."""
    ID = "Id"
    NAME = "Name"


# =============================================================================
# FILE FORMAT OPTIONS
# =============================================================================

class FileFormatOptions(BaseModel):
    """Base file format options."""
    format: FileFormat = Field(..., description="Data file format name")

    class Config:
        populate_by_name = True


class CSVFormatOptions(FileFormatOptions):
    """CSV format options."""
    format: FileFormat = Field(default=FileFormat.CSV)
    delimiter: Optional[str] = Field(",", description="CSV delimiter")
    header: Optional[bool] = Field(True, description="First row is header")

    class Config:
        populate_by_name = True


class ParquetFormatOptions(FileFormatOptions):
    """Parquet format options."""
    format: FileFormat = Field(default=FileFormat.PARQUET)

    class Config:
        populate_by_name = True


# =============================================================================
# LAKEHOUSE MODELS
# =============================================================================

class CreationPayload(BaseModel):
    """Lakehouse creation payload for schema-enabled lakehouse."""
    enable_schemas: bool = Field(..., alias="enableSchemas", description="Create schema enabled lakehouse")

    class Config:
        populate_by_name = True


class CreateLakehouseRequest(BaseModel):
    """Create lakehouse request payload."""
    display_name: str = Field(..., alias="displayName", description="The lakehouse display name")
    description: Optional[str] = Field(None, description="The lakehouse description. Max 256 characters.")
    folder_id: Optional[str] = Field(None, alias="folderId")
    creation_payload: Optional[CreationPayload] = Field(None, alias="creationPayload")

    class Config:
        populate_by_name = True


class SQLEndpointProperties(BaseModel):
    """SQL endpoint properties."""
    provisioning_status: SQLEndpointProvisioningStatus = Field(..., alias="provisioningStatus")
    connection_string: Optional[str] = Field(None, alias="connectionString")
    id: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class LakehouseProperties(BaseModel):
    """Lakehouse properties."""
    one_lake_files_path: str = Field(..., alias="oneLakeFilesPath", description="OneLake path to Files directory")
    one_lake_tables_path: str = Field(..., alias="oneLakeTablesPath", description="OneLake path to Tables directory")
    default_schema: Optional[str] = Field(None, alias="defaultSchema")
    sql_endpoint_properties: Optional[SQLEndpointProperties] = Field(None, alias="sqlEndpointProperties")

    class Config:
        populate_by_name = True


class Lakehouse(BaseModel):
    """A lakehouse item."""
    id: Optional[str] = Field(None, description="The item ID")
    type: Optional[ItemType] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)
    properties: Optional[LakehouseProperties] = Field(None)

    class Config:
        populate_by_name = True


class Lakehouses(BaseModel):
    """A list of lakehouses."""
    value: List[Lakehouse] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateLakehouseRequest(BaseModel):
    """Update lakehouse request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


# =============================================================================
# TABLE MODELS
# =============================================================================

class Table(BaseModel):
    """Table information in lakehouse."""
    name: str = Field(..., description="Table name")
    type: TableType = Field(..., description="Table type")
    format: str = Field(..., description="Table format")
    location: str = Field(..., description="Table location")

    class Config:
        populate_by_name = True


class Tables(BaseModel):
    """A list of tables."""
    data: List[Table] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class LoadTableRequest(BaseModel):
    """Load table operation request."""
    path_type: PathType = Field(..., alias="pathType")
    relative_path: str = Field(..., alias="relativePath", description="Relative path of data file/folder")
    file_extension: Optional[str] = Field(None, alias="fileExtension")
    format_options: Optional[FileFormatOptions] = Field(None, alias="formatOptions")
    mode: Optional[ModeType] = Field(None)
    recursive: Optional[bool] = Field(None)

    class Config:
        populate_by_name = True


# =============================================================================
# TABLE MAINTENANCE
# =============================================================================

class OptimizeSettings(BaseModel):
    """Table optimization settings."""
    v_order: Optional[bool] = Field(None, alias="vOrder", description="Enable V-Order optimization")
    z_order_by: Optional[List[str]] = Field(None, alias="zOrderBy", description="Columns for Z-Ordering")

    class Config:
        populate_by_name = True


class VacuumSettings(BaseModel):
    """Table vacuum settings."""
    retention_period: Optional[str] = Field(
        None, alias="retentionPeriod",
        description="Retention period (d:hh:mm:ss format)"
    )

    class Config:
        populate_by_name = True


class TableMaintenanceExecutionData(BaseModel):
    """Table maintenance execution data."""
    table_name: str = Field(..., alias="tableName", description="Name of table to maintain")
    schema_name: Optional[str] = Field(None, alias="schemaName")
    optimize_settings: Optional[OptimizeSettings] = Field(None, alias="optimizeSettings")
    vacuum_settings: Optional[VacuumSettings] = Field(None, alias="vacuumSettings")

    class Config:
        populate_by_name = True


class RunOnDemandTableMaintenanceRequest(BaseModel):
    """Run on-demand table maintenance request."""
    execution_data: TableMaintenanceExecutionData = Field(..., alias="executionData")

    class Config:
        populate_by_name = True


# =============================================================================
# SCHEDULING MODELS
# =============================================================================

class ScheduleConfig(BaseModel):
    """Base schedule configuration."""
    type: ScheduleType = Field(...)
    start_date_time: datetime = Field(..., alias="startDateTime")
    end_date_time: datetime = Field(..., alias="endDateTime")
    local_time_zone_id: str = Field(..., alias="localTimeZoneId")

    class Config:
        populate_by_name = True


class CronScheduleConfig(ScheduleConfig):
    """Cron schedule configuration."""
    type: ScheduleType = Field(default=ScheduleType.CRON)
    interval: int = Field(..., description="Time interval in minutes (1 to 5270400)")

    class Config:
        populate_by_name = True


class DailyScheduleConfig(ScheduleConfig):
    """Daily schedule configuration."""
    type: ScheduleType = Field(default=ScheduleType.DAILY)
    times: List[str] = Field(..., description="Time slots in hh:mm format")

    class Config:
        populate_by_name = True


class WeeklyScheduleConfig(ScheduleConfig):
    """Weekly schedule configuration."""
    type: ScheduleType = Field(default=ScheduleType.WEEKLY)
    times: List[str] = Field(..., description="Time slots in hh:mm format")
    weekdays: List[DayOfWeek] = Field(..., description="Days of the week")

    class Config:
        populate_by_name = True


class DayOfMonth(BaseModel):
    """Day of month occurrence."""
    occurrence_type: OccurrenceType = Field(default=OccurrenceType.DAY_OF_MONTH, alias="occurrenceType")
    day_of_month: int = Field(..., alias="dayOfMonth", description="Day of month (1-31)")

    class Config:
        populate_by_name = True


class OrdinalWeekday(BaseModel):
    """Ordinal weekday occurrence."""
    occurrence_type: OccurrenceType = Field(default=OccurrenceType.ORDINAL_WEEKDAY, alias="occurrenceType")
    week_index: WeekIndex = Field(..., alias="weekIndex")
    weekday: DayOfWeek = Field(...)

    class Config:
        populate_by_name = True


class MonthlyScheduleConfig(ScheduleConfig):
    """Monthly schedule configuration."""
    type: ScheduleType = Field(default=ScheduleType.MONTHLY)
    times: List[str] = Field(..., description="Time slots in hh:mm format")
    recurrence: int = Field(..., description="Monthly repeat interval")
    occurrence: Any = Field(..., description="DayOfMonth or OrdinalWeekday")

    class Config:
        populate_by_name = True


class CreateLakehouseRefreshMaterializedLakeViewsScheduleRequest(BaseModel):
    """Create refresh schedule request."""
    enabled: bool = Field(...)
    configuration: ScheduleConfig = Field(...)

    class Config:
        populate_by_name = True


class RefreshMaterializedLakeViewsSchedule(BaseModel):
    """Refresh schedule response."""
    id: str = Field(...)
    enabled: bool = Field(...)
    configuration: Optional[ScheduleConfig] = Field(None)
    created_date_time: Optional[datetime] = Field(None, alias="createdDateTime")
    owner: Optional[Principal] = Field(None)

    class Config:
        populate_by_name = True


class UpdateLakehouseRefreshMaterializedLakeViewsScheduleRequest(BaseModel):
    """Update refresh schedule request."""
    enabled: bool = Field(...)
    configuration: ScheduleConfig = Field(...)

    class Config:
        populate_by_name = True


# =============================================================================
# LIVY SESSION MODELS
# =============================================================================

class Duration(BaseModel):
    """A duration object."""
    time_unit: TimeUnit = Field(..., alias="timeUnit")
    value: float = Field(...)

    class Config:
        populate_by_name = True


class ItemReference(BaseModel):
    """An item reference object."""
    reference_type: ItemReferenceType = Field(..., alias="referenceType")

    class Config:
        populate_by_name = True


class ItemReferenceByID(ItemReference):
    """An item reference by ID."""
    reference_type: ItemReferenceType = Field(default=ItemReferenceType.ID, alias="referenceType")
    item_id: str = Field(..., alias="itemId")
    workspace_id: str = Field(..., alias="workspaceId")

    class Config:
        populate_by_name = True


class LivySession(BaseModel):
    """Livy session response."""
    livy_id: Optional[str] = Field(None, alias="livyId")
    livy_name: Optional[str] = Field(None, alias="livyName")
    spark_application_id: Optional[str] = Field(None, alias="sparkApplicationId")
    state: Optional[State] = Field(None)
    job_type: Optional[JobType] = Field(None, alias="jobType")
    origin: Optional[Origin] = Field(None)
    item: Optional[ItemReferenceByID] = Field(None)
    item_name: Optional[str] = Field(None, alias="itemName")
    item_type: Optional[LivySessionItemType] = Field(None, alias="itemType")
    submitter: Optional[Principal] = Field(None)
    submitted_date_time: Optional[datetime] = Field(None, alias="submittedDateTime")
    start_date_time: Optional[datetime] = Field(None, alias="startDateTime")
    end_date_time: Optional[datetime] = Field(None, alias="endDateTime")
    queued_duration: Optional[Duration] = Field(None, alias="queuedDuration")
    running_duration: Optional[Duration] = Field(None, alias="runningDuration")
    total_duration: Optional[Duration] = Field(None, alias="totalDuration")
    driver_cores: Optional[int] = Field(None, alias="driverCores")
    driver_memory: Optional[int] = Field(None, alias="driverMemory")
    executor_cores: Optional[Any] = Field(None, alias="executorCores")
    executor_memory: Optional[int] = Field(None, alias="executorMemory")
    num_executors: Optional[int] = Field(None, alias="numExecutors")
    is_dynamic_allocation_enabled: Optional[bool] = Field(None, alias="isDynamicAllocationEnabled")
    dynamic_allocation_max_executors: Optional[int] = Field(None, alias="dynamicAllocationMaxExecutors")
    is_high_concurrency: Optional[bool] = Field(None, alias="isHighConcurrency")
    capacity_id: Optional[str] = Field(None, alias="capacityId")
    runtime_version: Optional[str] = Field(None, alias="runtimeVersion")
    operation_name: Optional[str] = Field(None, alias="operationName")
    attempt_number: Optional[int] = Field(None, alias="attemptNumber")
    max_number_of_attempts: Optional[int] = Field(None, alias="maxNumberOfAttempts")
    cancellation_reason: Optional[str] = Field(None, alias="cancellationReason")
    job_instance_id: Optional[str] = Field(None, alias="jobInstanceId")
    livy_session_item_resource_uri: Optional[str] = Field(None, alias="livySessionItemResourceUri")
    consumer_id: Optional[Principal] = Field(None, alias="consumerId")
    creator_item: Optional[ItemReferenceByID] = Field(None, alias="creatorItem")

    class Config:
        populate_by_name = True


class LivySessions(BaseModel):
    """A list of livy sessions."""
    value: List[LivySession] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True
