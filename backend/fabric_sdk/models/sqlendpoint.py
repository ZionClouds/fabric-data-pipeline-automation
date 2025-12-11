"""
SQL Endpoint Models for Microsoft Fabric SDK

Contains models for SQL endpoint operations including:
- Audit settings
- Connection strings
- Table synchronization status
- Metadata refresh

Converted from: knowledge/fabric/sqlendpoint/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class AuditSettingsState(str, Enum):
    """Audit settings state."""
    DISABLED = "Disabled"
    ENABLED = "Enabled"


class SyncStatus(str, Enum):
    """The status of the synchronization operation."""
    FAILURE = "Failure"
    NOT_RUN = "NotRun"
    SUCCESS = "Success"


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

    time_unit: TimeUnit = Field(
        ...,
        alias="timeUnit",
        description="The unit of time for the duration"
    )
    value: float = Field(
        ...,
        description="The number of timeUnits in the duration"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class ErrorRelatedResource(BaseModel):
    """The error related resource details object."""

    resource_id: Optional[str] = Field(
        None,
        alias="resourceId",
        description="The resource ID that's involved in the error"
    )
    resource_type: Optional[str] = Field(
        None,
        alias="resourceType",
        description="The type of the resource that's involved in the error"
    )

    class Config:
        populate_by_name = True


class ErrorResponseDetails(BaseModel):
    """The error response details."""

    error_code: Optional[str] = Field(
        None,
        alias="errorCode",
        description="A specific identifier that provides information about an error condition"
    )
    message: Optional[str] = Field(
        None,
        description="A human readable representation of the error"
    )
    related_resource: Optional[ErrorRelatedResource] = Field(
        None,
        alias="relatedResource",
        description="The error related resource details"
    )

    class Config:
        populate_by_name = True


class RefreshMetadataRequest(BaseModel):
    """Refresh SQL analytics endpoint request payload."""

    timeout: Optional[Duration] = Field(
        None,
        description="The request duration before timing out. The default value is 15 minutes"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class SQLAuditSettings(BaseModel):
    """The current state of audit settings for an item."""

    audit_actions_and_groups: List[str] = Field(
        ...,
        alias="auditActionsAndGroups",
        description="Audit actions and groups"
    )
    retention_days: int = Field(
        ...,
        alias="retentionDays",
        description="Retention days. 0 indicates indefinite retention period"
    )
    state: AuditSettingsState = Field(
        ...,
        description="Audit settings state type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class SQLAuditSettingsUpdate(BaseModel):
    """Audit settings update request."""

    retention_days: Optional[int] = Field(
        None,
        alias="retentionDays",
        description="Retention days"
    )
    state: Optional[AuditSettingsState] = Field(
        None,
        description="Audit settings state type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class SQLEndpoint(BaseModel):
    """A SQL endpoint object."""

    type: ItemType = Field(
        ...,
        description="The item type"
    )
    description: Optional[str] = Field(
        None,
        description="The item description"
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="The item display name"
    )

    # Read-only fields
    folder_id: Optional[str] = Field(
        None,
        alias="folderId",
        description="The folder ID"
    )
    id: Optional[str] = Field(
        None,
        description="The item ID"
    )
    tags: Optional[List[ItemTag]] = Field(
        None,
        description="List of applied tags"
    )
    workspace_id: Optional[str] = Field(
        None,
        alias="workspaceId",
        description="The workspace ID"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class SQLEndpoints(BaseModel):
    """A list of SQL endpoints."""

    value: List[SQLEndpoint] = Field(
        ...,
        description="A list of SQL endpoints"
    )
    continuation_token: Optional[str] = Field(
        None,
        alias="continuationToken",
        description="The token for the next result set batch"
    )
    continuation_uri: Optional[str] = Field(
        None,
        alias="continuationUri",
        description="The URI of the next result set batch"
    )

    class Config:
        populate_by_name = True


class TableSyncStatus(BaseModel):
    """A table synchronization status object."""

    end_date_time: datetime = Field(
        ...,
        alias="endDateTime",
        description="The date and time when the table synchronization completed in UTC"
    )
    last_successful_sync_date_time: datetime = Field(
        ...,
        alias="lastSuccessfulSyncDateTime",
        description="The date and time when the table synchronization was successful in UTC"
    )
    start_date_time: datetime = Field(
        ...,
        alias="startDateTime",
        description="The date and time when the table synchronization started in UTC"
    )
    status: SyncStatus = Field(
        ...,
        description="Whether the table synchronized without errors"
    )
    table_name: str = Field(
        ...,
        alias="tableName",
        description="The name of the table that synchronized"
    )
    error: Optional[ErrorResponseDetails] = Field(
        None,
        description="The error response details"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class TableSyncStatuses(BaseModel):
    """A list of table synchronization statuses."""

    value: List[TableSyncStatus] = Field(
        ...,
        description="A list of table synchronization statuses"
    )

    class Config:
        populate_by_name = True


class ConnectionStringResponse(BaseModel):
    """The SQL connection string for the workspace containing this SQL endpoint."""

    connection_string: Optional[str] = Field(
        None,
        alias="connectionString",
        description="The SQL connection string for the workspace containing this SQL endpoint"
    )

    class Config:
        populate_by_name = True
