"""
Eventhouse Models for Microsoft Fabric SDK

Contains models for eventhouse operations including:
- Create/Update/Delete eventhouses
- Definition management
- Minimum consumption configuration

Converted from: knowledge/fabric/eventhouse/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

class CreationPayload(BaseModel):
    """Eventhouse item payload."""

    minimum_consumption_units: Optional[float] = Field(
        None,
        alias="minimumConsumptionUnits",
        description="Minimum consumption units for the eventhouse"
    )

    class Config:
        populate_by_name = True


class DefinitionPart(BaseModel):
    """Eventhouse definition part object."""

    path: str = Field(
        ...,
        description="The eventhouse part path"
    )
    payload: str = Field(
        ...,
        description="The eventhouse part payload"
    )
    payload_type: PayloadType = Field(
        ...,
        alias="payloadType",
        description="The payload type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class Definition(BaseModel):
    """Eventhouse public definition object."""

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
    """The eventhouse properties."""

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
    databases_item_ids: Optional[List[str]] = Field(
        None,
        alias="databasesItemIds",
        description="List of all KQL database children"
    )
    minimum_consumption_units: Optional[float] = Field(
        None,
        alias="minimumConsumptionUnits",
        description="Minimum consumption units"
    )

    class Config:
        populate_by_name = True


class Eventhouse(BaseModel):
    """An eventhouse object."""

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
        description="The eventhouse properties"
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


class Eventhouses(BaseModel):
    """A list of eventhouses."""

    value: List[Eventhouse] = Field(
        ...,
        description="A list of eventhouses"
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


class CreateEventhouseRequest(BaseModel):
    """Create eventhouse request."""

    display_name: str = Field(
        ...,
        alias="displayName",
        description="The eventhouse display name"
    )
    creation_payload: Optional[CreationPayload] = Field(
        None,
        alias="creationPayload",
        description="The eventhouse creation payload"
    )
    definition: Optional[Definition] = Field(
        None,
        description="The eventhouse public definition"
    )
    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The eventhouse description. Maximum length is 256 characters"
    )
    folder_id: Optional[str] = Field(
        None,
        alias="folderId",
        description="The folder ID"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateEventhouseRequest(BaseModel):
    """Update eventhouse request."""

    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The eventhouse description. Maximum length is 256 characters"
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="The eventhouse display name"
    )

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """Eventhouse public definition response."""

    definition: Optional[Definition] = Field(
        None,
        description="Eventhouse public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateEventhouseDefinitionRequest(BaseModel):
    """Update eventhouse public definition request payload."""

    definition: Definition = Field(
        ...,
        description="Eventhouse public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True
