"""
SQL Database Models for Microsoft Fabric SDK

Contains models for SQL database operations including:
- Create/Update SQL databases
- Restore operations
- Database properties and connections

Converted from: knowledge/fabric/sqldatabase/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class CreationMode(str, Enum):
    """The creation mode of the SQL database creation."""
    NEW = "New"
    RESTORE = "Restore"


class ItemReferenceType(str, Enum):
    """Item reference type."""
    BY_ID = "ById"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

class ItemReference(BaseModel):
    """An item reference object."""

    reference_type: ItemReferenceType = Field(..., alias="referenceType")

    class Config:
        populate_by_name = True
        use_enum_values = True


class ItemReferenceByID(BaseModel):
    """An item reference by ID object."""

    item_id: str = Field(..., alias="itemId")
    reference_type: ItemReferenceType = Field(..., alias="referenceType")
    workspace_id: str = Field(..., alias="workspaceId")

    class Config:
        populate_by_name = True
        use_enum_values = True


class CreationPayload(BaseModel):
    """SQL database item payload."""

    creation_mode: CreationMode = Field(..., alias="creationMode")
    backup_retention_days: Optional[int] = Field(None, alias="backupRetentionDays")
    restore_point_in_time: Optional[datetime] = Field(None, alias="restorePointInTime")
    source_database_reference: Optional[Union[ItemReference, ItemReferenceByID]] = Field(
        None, alias="sourceDatabaseReference"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class NewSQLDatabaseCreationPayload(CreationPayload):
    """Create a SQL database item creation payload with supported settings."""
    pass


class RestoreSQLDatabaseCreationPayload(CreationPayload):
    """Create a SQL database item creation payload with restoring from a source database."""
    pass


class PublicDefinitionPart(BaseModel):
    """SQL database definition part object."""

    path: Optional[str] = None
    payload: Optional[str] = None
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True
        use_enum_values = True


class Definition(BaseModel):
    """The SQL database public definition object."""

    parts: List[PublicDefinitionPart] = Field(...)

    class Config:
        populate_by_name = True


class Properties(BaseModel):
    """The SQL database properties."""

    connection_string: str = Field(..., alias="connectionString")
    database_name: str = Field(..., alias="databaseName")
    server_fqdn: str = Field(..., alias="serverFqdn")
    backup_retention_days: Optional[int] = Field(None, alias="backupRetentionDays")
    earliest_restore_point: Optional[datetime] = Field(None, alias="earliestRestorePoint")
    latest_restore_point: Optional[datetime] = Field(None, alias="latestRestorePoint")

    class Config:
        populate_by_name = True


class SQLDatabase(BaseModel):
    """A SQL database object."""

    type: ItemType = Field(...)
    description: Optional[str] = None
    display_name: Optional[str] = Field(None, alias="displayName")
    properties: Optional[Properties] = None

    # Read-only fields
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = None
    tags: Optional[List[ItemTag]] = None
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True
        use_enum_values = True


class SQLDatabases(BaseModel):
    """A list of SQL databases."""

    value: List[SQLDatabase] = Field(...)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateSQLDatabaseRequest(BaseModel):
    """Create SQL database request payload."""

    display_name: str = Field(..., alias="displayName")
    creation_payload: Optional[Union[CreationPayload, NewSQLDatabaseCreationPayload, RestoreSQLDatabaseCreationPayload]] = Field(
        None, alias="creationPayload"
    )
    definition: Optional[Definition] = None
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateSQLDatabaseRequest(BaseModel):
    """Update SQL database request."""

    description: Optional[str] = Field(None, max_length=256)

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """The SQL database public definition response."""

    definition: Optional[Definition] = None

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateSQLDatabaseDefinitionRequest(BaseModel):
    """Update SQL database public definition request payload."""

    definition: Definition = Field(...)

    class Config:
        populate_by_name = True
        use_enum_values = True
