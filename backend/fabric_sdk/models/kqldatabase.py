"""
KQL Database Models for Microsoft Fabric SDK

Contains models for KQL database operations including:
- Create/Update/Delete KQL databases
- Database types (ReadWrite, Shortcut)
- Parent eventhouse references

Converted from: knowledge/fabric/kqldatabase/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class Type(str, Enum):
    """The type of the KQL database."""
    READ_WRITE = "ReadWrite"
    SHORTCUT = "Shortcut"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

class CreationPayload(BaseModel):
    """KQL database item payload."""

    database_type: Type = Field(
        ...,
        alias="databaseType",
        description="The type of the KQL database"
    )
    parent_eventhouse_item_id: str = Field(
        ...,
        alias="parentEventhouseItemId",
        description="Parent eventhouse item ID"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class ReadWriteDatabaseCreationPayload(CreationPayload):
    """ReadWrite KQL database item creation payload."""
    pass


class ShortcutDatabaseCreationPayload(BaseModel):
    """Shortcut KQL database item creation payload."""

    database_type: Type = Field(
        ...,
        alias="databaseType",
        description="The type of the KQL database"
    )
    parent_eventhouse_item_id: str = Field(
        ...,
        alias="parentEventhouseItemId",
        description="Parent eventhouse item ID"
    )
    invitation_token: Optional[str] = Field(
        None,
        alias="invitationToken",
        description="Invitation token to follow the source database"
    )
    source_cluster_uri: Optional[str] = Field(
        None,
        alias="sourceClusterUri",
        description="The URI of the source Eventhouse or Azure Data Explorer cluster"
    )
    source_database_name: Optional[str] = Field(
        None,
        alias="sourceDatabaseName",
        description="The name of the database to follow in the source cluster"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class DefinitionPart(BaseModel):
    """KQL database definition part object."""

    path: Optional[str] = Field(
        None,
        description="The KQL database part path"
    )
    payload: Optional[str] = Field(
        None,
        description="The KQL database part payload"
    )
    payload_type: Optional[PayloadType] = Field(
        None,
        alias="payloadType",
        description="The payload type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class Definition(BaseModel):
    """KQL database public definition object."""

    parts: List[DefinitionPart] = Field(
        ...,
        description="A list of definition parts"
    )
    format: Optional[str] = Field(
        None,
        description="The format of the item definition"
    )

    class Config:
        populate_by_name = True


class Properties(BaseModel):
    """The KQL database properties."""

    ingestion_service_uri: str = Field(
        ...,
        alias="ingestionServiceUri",
        description="Ingestion service URI"
    )
    query_service_uri: str = Field(
        ...,
        alias="queryServiceUri",
        description="Query service URI"
    )
    database_type: Optional[Type] = Field(
        None,
        alias="databaseType",
        description="The type of the database"
    )
    parent_eventhouse_item_id: Optional[str] = Field(
        None,
        alias="parentEventhouseItemId",
        description="Parent eventhouse ID"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class KQLDatabase(BaseModel):
    """A KQL database object."""

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
    properties: Optional[Properties] = Field(
        None,
        description="The KQL database properties"
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


class KQLDatabases(BaseModel):
    """A list of KQL databases."""

    value: List[KQLDatabase] = Field(
        ...,
        description="A list of KQL databases"
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


class CreateKQLDatabaseRequest(BaseModel):
    """Create KQL database request payload."""

    display_name: str = Field(
        ...,
        alias="displayName",
        description="The KQL database display name"
    )
    creation_payload: Optional[Union[CreationPayload, ReadWriteDatabaseCreationPayload, ShortcutDatabaseCreationPayload]] = Field(
        None,
        alias="creationPayload",
        description="The KQL database creation payload"
    )
    definition: Optional[Definition] = Field(
        None,
        description="The KQL database public definition"
    )
    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The KQL database description"
    )
    folder_id: Optional[str] = Field(
        None,
        alias="folderId",
        description="The folder ID"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateKQLDatabaseRequest(BaseModel):
    """Update KQL database request."""

    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The KQL database description"
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="The KQL database display name"
    )

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """KQL database public definition response."""

    definition: Optional[Definition] = Field(
        None,
        description="KQL database public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateKQLDatabaseDefinitionRequest(BaseModel):
    """Update KQL database public definition request payload."""

    definition: Definition = Field(
        ...,
        description="KQL database public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True
