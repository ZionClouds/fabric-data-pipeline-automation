"""
Mirroreddatabase Models for Microsoft Fabric SDK

Contains models for mirrored database operations.

Converted from: knowledge/fabric/mirroreddatabase/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, Principal


# =============================================================================
# ENUMS
# =============================================================================

class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


class MirroringStatus(str, Enum):
    """The mirroring status type."""
    INITIALIZED = "Initialized"
    INITIALIZING = "Initializing"
    RUNNING = "Running"
    STARTING = "Starting"
    STOPPED = "Stopped"
    STOPPING = "Stopping"


class SQLEndpointProvisioningStatus(str, Enum):
    """The SQL endpoint provisioning status type."""
    FAILED = "Failed"
    IN_PROGRESS = "InProgress"
    SUCCESS = "Success"


class TableMirroringStatus(str, Enum):
    """The table mirroring status type."""
    FAILED = "Failed"
    INITIALIZED = "Initialized"
    REPLICATING = "Replicating"
    RESEEDING = "Reseeding"
    SNAPSHOTTING = "Snapshotting"
    STOPPED = "Stopped"


class TableSourceObjectType(str, Enum):
    """The table source object type."""
    TABLE = "Table"
    VIEW = "View"


# =============================================================================
# MODELS
# =============================================================================

class ErrorRelatedResource(BaseModel):
    """The error related resource details object."""
    resource_id: Optional[str] = Field(None, alias="resourceId", description="The resource ID that's involved in the error")
    resource_type: Optional[str] = Field(None, alias="resourceType", description="The type of the resource that's involved in the error")


class ErrorResponseDetails(BaseModel):
    """The error response details."""
    error_code: Optional[str] = Field(None, alias="errorCode", description="A specific identifier that provides information about an error condition")
    message: Optional[str] = Field(None, description="A human readable representation of the error")
    related_resource: Optional[ErrorRelatedResource] = Field(None, alias="relatedResource", description="The error related resource details")


class ErrorResponse(BaseModel):
    """The error response."""
    error_code: Optional[str] = Field(None, alias="errorCode", description="A specific identifier that provides information about an error condition")
    message: Optional[str] = Field(None, description="A human readable representation of the error")
    more_details: Optional[List[ErrorResponseDetails]] = Field(None, alias="moreDetails", description="List of additional error details")
    related_resource: Optional[ErrorRelatedResource] = Field(None, alias="relatedResource", description="The error related resource details")
    request_id: Optional[str] = Field(None, alias="requestId", description="ID of the request associated with the error")


class DefinitionPart(BaseModel):
    """Mirrored database definition part object."""
    path: Optional[str] = Field(None, description="The mirrored database part path")
    payload: Optional[str] = Field(None, description="The mirrored database part payload")
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType", description="The payload type")


class Definition(BaseModel):
    """Mirrored database public definition object."""
    parts: List[DefinitionPart] = Field(..., description="A list of definition parts")


class DefinitionResponse(BaseModel):
    """Mirrored database public definition response."""
    definition: Optional[Definition] = Field(None, description="Mirrored database public definition object")


class CreateMirroredDatabaseRequest(BaseModel):
    """Create mirrored database request payload."""
    definition: Definition = Field(..., description="The mirrored database public definition")
    display_name: str = Field(..., alias="displayName", description="The mirrored database display name")
    description: Optional[str] = Field(None, description="The mirrored database description. Maximum length is 256 characters")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")


class SQLEndpointProperties(BaseModel):
    """An object containing the properties of the SQL endpoint."""
    provisioning_status: SQLEndpointProvisioningStatus = Field(..., alias="provisioningStatus", description="The SQL endpoint provisioning status")
    connection_string: Optional[str] = Field(None, alias="connectionString", description="SQL endpoint connection string")
    id: Optional[str] = Field(None, description="SQL endpoint ID")


class Properties(BaseModel):
    """The mirrored database properties."""
    default_schema: Optional[str] = Field(None, alias="defaultSchema", description="Default schema of the mirrored database")
    one_lake_tables_path: Optional[str] = Field(None, alias="oneLakeTablesPath", description="OneLake path to the mirrored database tables directory")
    sql_endpoint_properties: Optional[SQLEndpointProperties] = Field(None, alias="sqlEndpointProperties", description="An object containing the properties of the SQL endpoint")


class MirroredDatabase(BaseModel):
    """A mirrored database item."""
    type: ItemType = Field(..., description="The item type")
    description: Optional[str] = Field(None, description="The item description")
    display_name: Optional[str] = Field(None, alias="displayName", description="The item display name")
    properties: Optional[Properties] = Field(None, description="The mirrored database properties")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")
    id: Optional[str] = Field(None, description="The item ID")
    tags: Optional[List[ItemTag]] = Field(None, description="List of applied tags")
    workspace_id: Optional[str] = Field(None, alias="workspaceId", description="The workspace ID")


class MirroredDatabases(BaseModel):
    """A list of mirrored databases."""
    value: List[MirroredDatabase] = Field(..., description="A list of mirrored databases")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")


class MirroringStatusResponse(BaseModel):
    """Response of getting mirroring status."""
    status: MirroringStatus = Field(..., description="The status of mirroring")
    error: Optional[ErrorResponse] = Field(None, description="Error is set if error happens in mirroring")


class TableMirroringMetrics(BaseModel):
    """Table mirroring metrics."""
    last_sync_date_time: datetime = Field(..., alias="lastSyncDateTime", description="Last processed time of the table in UTC")
    processed_bytes: int = Field(..., alias="processedBytes", description="Processed bytes for this table")
    processed_rows: int = Field(..., alias="processedRows", description="Processed row count for this table")
    last_sync_latency_in_seconds: Optional[int] = Field(None, alias="lastSyncLatencyInSeconds", description="Latency in seconds between source commit time and target commit time")


class TableMirroringStatusResponse(BaseModel):
    """Table mirroring status response."""
    source_object_type: TableSourceObjectType = Field(..., alias="sourceObjectType", description="Source object type")
    status: TableMirroringStatus = Field(..., description="The mirroring status type of table")
    metrics: Optional[TableMirroringMetrics] = Field(None, description="The mirroring metrics of table")
    source_schema_name: Optional[str] = Field(None, alias="sourceSchemaName", description="Source table schema name")
    source_table_name: Optional[str] = Field(None, alias="sourceTableName", description="Source table name")
    error: Optional[ErrorResponse] = Field(None, description="Table level error is set if error happens in mirroring for this table")


class TablesMirroringStatusResponse(BaseModel):
    """A paginated list of table mirroring statuses."""
    data: List[TableMirroringStatusResponse] = Field(..., description="A list of table mirroring statuses")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")


class UpdateMirroredDatabaseDefinitionRequest(BaseModel):
    """Update mirrored database public definition request payload."""
    definition: Definition = Field(..., description="Mirrored database public definition object")


class UpdateMirroredDatabaseRequest(BaseModel):
    """Update mirrored database request."""
    description: Optional[str] = Field(None, description="The mirrored database description. Maximum length is 256 characters")
    display_name: Optional[str] = Field(None, alias="displayName", description="The mirrored database display name")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "PayloadType",
    "MirroringStatus",
    "SQLEndpointProvisioningStatus",
    "TableMirroringStatus",
    "TableSourceObjectType",
    # Models
    "ErrorRelatedResource",
    "ErrorResponseDetails",
    "ErrorResponse",
    "DefinitionPart",
    "Definition",
    "DefinitionResponse",
    "CreateMirroredDatabaseRequest",
    "SQLEndpointProperties",
    "Properties",
    "MirroredDatabase",
    "MirroredDatabases",
    "MirroringStatusResponse",
    "TableMirroringMetrics",
    "TableMirroringStatusResponse",
    "TablesMirroringStatusResponse",
    "UpdateMirroredDatabaseDefinitionRequest",
    "UpdateMirroredDatabaseRequest",
]
