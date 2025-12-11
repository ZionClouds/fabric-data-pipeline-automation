"""
Map Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/maps/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    MAP = "Map"


class PayloadType(str, Enum):
    """Payload type for definition parts."""
    INLINE_BASE64 = "InlineBase64"
    VSO_GIT = "VsoGit"


class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName")
    id: str = Field(...)

    class Config:
        populate_by_name = True


class MapPublicDefinitionPart(BaseModel):
    """Map definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class MapPublicDefinition(BaseModel):
    """Map public definition object."""
    parts: List[MapPublicDefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CreateMapRequest(BaseModel):
    """Create Map request payload."""
    display_name: str = Field(..., alias="displayName")
    definition: Optional[MapPublicDefinition] = Field(None)
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class Map(BaseModel):
    """A Map object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class Maps(BaseModel):
    """A list of Maps."""
    value: List[Map] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class MapDefinitionResponse(BaseModel):
    """Map public definition response."""
    definition: Optional[MapPublicDefinition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateMapDefinitionRequest(BaseModel):
    """Update Map public definition request payload."""
    definition: MapPublicDefinition = Field(...)

    class Config:
        populate_by_name = True


class UpdateMapRequest(BaseModel):
    """Update Map request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "PayloadType",
    "ItemTag",
    "MapPublicDefinitionPart",
    "MapPublicDefinition",
    "CreateMapRequest",
    "Map",
    "Maps",
    "MapDefinitionResponse",
    "UpdateMapDefinitionRequest",
    "UpdateMapRequest",
]
