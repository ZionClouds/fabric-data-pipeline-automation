"""
Reflex Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/reflex/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    REFLEX = "Reflex"


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


class DefinitionPart(BaseModel):
    """Reflex definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class Definition(BaseModel):
    """Reflex public definition object."""
    parts: List[DefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CreateReflexRequest(BaseModel):
    """Create Reflex request payload."""
    display_name: str = Field(..., alias="displayName")
    definition: Optional[Definition] = Field(None)
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class Reflex(BaseModel):
    """A Reflex object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class Reflexes(BaseModel):
    """A list of Reflexes."""
    value: List[Reflex] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """Reflex public definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateReflexDefinitionRequest(BaseModel):
    """Update Reflex public definition request payload."""
    definition: Definition = Field(...)

    class Config:
        populate_by_name = True


class UpdateReflexRequest(BaseModel):
    """Update Reflex request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "PayloadType",
    "ItemTag",
    "DefinitionPart",
    "Definition",
    "CreateReflexRequest",
    "Reflex",
    "Reflexes",
    "DefinitionResponse",
    "UpdateReflexDefinitionRequest",
    "UpdateReflexRequest",
]
