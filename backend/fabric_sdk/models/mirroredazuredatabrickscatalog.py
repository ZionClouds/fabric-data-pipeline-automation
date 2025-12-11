"""
Mirroredazuredatabrickscatalog Models for Microsoft Fabric SDK

Contains models for mirrored Azure Databricks catalog operations.

Converted from: knowledge/fabric/mirroredazuredatabrickscatalog/models.go and constants.go
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

class AutoSync(str, Enum):
    """Enable or disable automatic synchronization for the catalog."""
    DISABLED = "Disabled"
    ENABLED = "Enabled"


class CatalogType(str, Enum):
    """The type of the catalog."""
    MANAGED_CATALOG = "MANAGED_CATALOG"


class DataSourceFormat(str, Enum):
    """The data source format of the table."""
    DELTA = "DELTA"


class MirrorStatus(str, Enum):
    """Status of mirroring."""
    MIRRORED = "Mirrored"
    NOT_MIRRORED = "NotMirrored"


class MirroringModes(str, Enum):
    """Mode for mirroring."""
    FULL = "Full"
    PARTIAL = "Partial"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


class Status(str, Enum):
    """The sync status."""
    FAILED = "Failed"
    IN_PROGRESS = "InProgress"
    NOT_STARTED = "NotStarted"
    SUCCESS = "Success"


class TableType(str, Enum):
    """The type of the table."""
    EXTERNAL = "EXTERNAL"
    MANAGED = "MANAGED"


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


class ErrorInfo(BaseModel):
    """The error information."""
    error_code: str = Field(..., alias="errorCode", description="The error code")
    error_message: str = Field(..., alias="errorMessage", description="The error message")
    error_details: Optional[str] = Field(None, alias="errorDetails", description="The error details")


class CreationPayload(BaseModel):
    """MirroredAzureDatabricksCatalog create item payload."""
    catalog_name: str = Field(..., alias="catalogName", description="Azure databricks catalog name")
    databricks_workspace_connection_id: str = Field(..., alias="databricksWorkspaceConnectionId", description="The Azure databricks workspace connection id")
    mirroring_mode: MirroringModes = Field(..., alias="mirroringMode", description="Mirroring mode")
    storage_connection_id: Optional[str] = Field(None, alias="storageConnectionId", description="The storage connection id")


class PublicDefinitionPart(BaseModel):
    """MirroredAzureDatabricksCatalog definition part object."""
    path: str = Field(..., description="The MirroredAzureDatabricksCatalog part path")
    payload: str = Field(..., description="The MirroredAzureDatabricksCatalog part payload")
    payload_type: PayloadType = Field(..., alias="payloadType", description="The payload type")


class PublicDefinition(BaseModel):
    """MirroredAzureDatabricksCatalog public definition object."""
    parts: List[PublicDefinitionPart] = Field(..., description="A list of definition parts")
    format: Optional[str] = Field(None, description="The format of the item definition")


class CreateMirroredAzureDatabricksCatalogRequest(BaseModel):
    """Create MirroredAzureDatabricksCatalog request payload."""
    display_name: str = Field(..., alias="displayName", description="The MirroredAzureDatabricksCatalog display name")
    creation_payload: Optional[CreationPayload] = Field(None, alias="creationPayload", description="The MirroredAzureDatabricksCatalog creation payload")
    definition: Optional[PublicDefinition] = Field(None, description="The MirroredAzureDatabricksCatalog public definition")
    description: Optional[str] = Field(None, description="The MirroredAzureDatabricksCatalog description. Maximum length is 256 characters")


class DatabricksCatalog(BaseModel):
    """A catalog from Unity Catalog."""
    catalog_type: CatalogType = Field(..., alias="catalogType", description="The type of the catalog")
    full_name: str = Field(..., alias="fullName", description="The full name of the catalog")
    name: str = Field(..., description="The name of the catalog")
    storage_location: str = Field(..., alias="storageLocation", description="The storage location of the catalog")


class DatabricksCatalogs(BaseModel):
    """A list of catalogs from Unity Catalog."""
    value: List[DatabricksCatalog] = Field(..., description="A list of Catalogs")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")
    error: Optional[ErrorResponse] = Field(None, description="Error is set if unable to fetch catalogs")


class DatabricksSchema(BaseModel):
    """A schema from Unity Catalog."""
    full_name: str = Field(..., alias="fullName", description="The full name of the schema")
    name: str = Field(..., description="The name of the schema")
    storage_location: Optional[str] = Field(None, alias="storageLocation", description="The storage location of the schema")


class DatabricksSchemas(BaseModel):
    """A list of schemas from Unity Catalog."""
    value: List[DatabricksSchema] = Field(..., description="A list of Databricks schemas")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")
    error: Optional[ErrorResponse] = Field(None, description="Error is set if unable to fetch schemas")


class DatabricksTable(BaseModel):
    """A table from Unity Catalog."""
    data_source_format: DataSourceFormat = Field(..., alias="dataSourceFormat", description="The data source format of the table")
    full_name: str = Field(..., alias="fullName", description="The full name of the table")
    name: str = Field(..., description="The name of the table")
    storage_location: str = Field(..., alias="storageLocation", description="The storage location of the table")
    table_type: TableType = Field(..., alias="tableType", description="The type of the table")


class DatabricksTables(BaseModel):
    """A list of tables from Unity Catalog."""
    value: List[DatabricksTable] = Field(..., description="A list of Databricks tables")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")
    error: Optional[ErrorResponse] = Field(None, description="Error is set if unable to fetch tables")


class DefinitionResponse(BaseModel):
    """API for mirroredAzureDatabricksCatalog public definition response."""
    definition: Optional[PublicDefinition] = Field(None, description="MirroredAzureDatabricksCatalog public definition object")


class SQLEndpointProperties(BaseModel):
    """An object containing the properties of the SQL endpoint."""
    connection_string: str = Field(..., alias="connectionString", description="SQL endpoint connection string")
    id: str = Field(..., description="SQL endpoint ID")


class SyncDetails(BaseModel):
    """The MirroredAzureDatabricksCatalog mirroring status."""
    last_sync_date_time: datetime = Field(..., alias="lastSyncDateTime", description="The last sync date time in UTC")
    status: Status = Field(..., description="The sync status")
    error_info: Optional[ErrorInfo] = Field(None, alias="errorInfo", description="The error information")


class Properties(BaseModel):
    """The MirroredAzureDatabricksCatalog properties."""
    auto_sync: AutoSync = Field(..., alias="autoSync", description="Auto sync the catalog")
    catalog_name: str = Field(..., alias="catalogName", description="Azure databricks catalog name")
    databricks_workspace_connection_id: str = Field(..., alias="databricksWorkspaceConnectionId", description="The Azure databricks workspace connection id")
    mirroring_mode: MirroringModes = Field(..., alias="mirroringMode", description="Mirroring mode")
    one_lake_tables_path: str = Field(..., alias="oneLakeTablesPath", description="OneLake path to the MirroredAzureDatabricksCatalog tables directory")
    mirror_status: Optional[MirrorStatus] = Field(None, alias="mirrorStatus", description="The MirroredAzureDatabricksCatalog sync status")
    sql_endpoint_properties: Optional[SQLEndpointProperties] = Field(None, alias="sqlEndpointProperties", description="An object containing the properties of the SQL endpoint")
    storage_connection_id: Optional[str] = Field(None, alias="storageConnectionId", description="The storage connection id")
    sync_details: Optional[SyncDetails] = Field(None, alias="syncDetails", description="The MirroredAzureDatabricksCatalog sync status")


class MirroredAzureDatabricksCatalog(BaseModel):
    """A MirroredAzureDatabricksCatalog item."""
    type: ItemType = Field(..., description="The item type")
    description: Optional[str] = Field(None, description="The item description")
    display_name: Optional[str] = Field(None, alias="displayName", description="The item display name")
    properties: Optional[Properties] = Field(None, description="The MirroredAzureDatabricksCatalog properties")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")
    id: Optional[str] = Field(None, description="The item ID")
    tags: Optional[List[ItemTag]] = Field(None, description="List of applied tags")
    workspace_id: Optional[str] = Field(None, alias="workspaceId", description="The workspace ID")


class MirroredAzureDatabricksCatalogs(BaseModel):
    """A list of MirroredAzureDatabricksCatalogs."""
    value: List[MirroredAzureDatabricksCatalog] = Field(..., description="A list of MirroredAzureDatabricksCatalogs")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")


class UpdatePayload(BaseModel):
    """MirroredAzureDatabricksCatalog update item payload."""
    auto_sync: Optional[AutoSync] = Field(None, alias="autoSync", description="Auto sync the catalog")
    mirroring_mode: Optional[MirroringModes] = Field(None, alias="mirroringMode", description="Mirroring mode")
    storage_connection_id: Optional[str] = Field(None, alias="storageConnectionId", description="The storage connection id")


class UpdateMirroredAzureDatabricksCatalogRequest(BaseModel):
    """Update MirroredAzureDatabricksCatalog request."""
    description: Optional[str] = Field(None, description="The MirroredAzureDatabricksCatalog description. Maximum length is 256 characters")
    display_name: Optional[str] = Field(None, alias="displayName", description="The MirroredAzureDatabricksCatalog display name")
    public_updateable_extended_properties: Optional[UpdatePayload] = Field(None, alias="publicUpdateableExtendedProperties", description="The MirroredAzureDatabricksCatalog updateable properties payload")


class UpdatemirroredAzureDatabricksCatalogDefinitionRequest(BaseModel):
    """Update MirroredAzureDatabricksCatalog public definition request payload."""
    definition: PublicDefinition = Field(..., description="MirroredAzureDatabricksCatalog public definition object")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AutoSync",
    "CatalogType",
    "DataSourceFormat",
    "MirrorStatus",
    "MirroringModes",
    "PayloadType",
    "Status",
    "TableType",
    # Models
    "ErrorRelatedResource",
    "ErrorResponseDetails",
    "ErrorResponse",
    "ErrorInfo",
    "CreationPayload",
    "PublicDefinitionPart",
    "PublicDefinition",
    "CreateMirroredAzureDatabricksCatalogRequest",
    "DatabricksCatalog",
    "DatabricksCatalogs",
    "DatabricksSchema",
    "DatabricksSchemas",
    "DatabricksTable",
    "DatabricksTables",
    "DefinitionResponse",
    "SQLEndpointProperties",
    "SyncDetails",
    "Properties",
    "MirroredAzureDatabricksCatalog",
    "MirroredAzureDatabricksCatalogs",
    "UpdatePayload",
    "UpdateMirroredAzureDatabricksCatalogRequest",
    "UpdatemirroredAzureDatabricksCatalogDefinitionRequest",
]
