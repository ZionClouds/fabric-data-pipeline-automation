"""
Graph Query Set Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/graphqueryset/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    GRAPH_QUERY_SET = "GraphQuerySet"


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


class PublicDefinitionPart(BaseModel):
    """Graph Query Set definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class PublicDefinition(BaseModel):
    """Graph Query Set public definition object."""
    parts: List[PublicDefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CreateGraphQuerySetRequest(BaseModel):
    """Create Graph Query Set request payload."""
    display_name: str = Field(..., alias="displayName")
    definition: Optional[PublicDefinition] = Field(None)
    description: Optional[str] = Field(None, max_length=256)

    class Config:
        populate_by_name = True


class GraphQuerySet(BaseModel):
    """A graph queryset object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class GraphQuerySets(BaseModel):
    """A list of graph queryset objects."""
    value: List[GraphQuerySet] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """Graph Query Set public definition response."""
    definition: Optional[PublicDefinition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateGraphQuerySetDefinitionRequest(BaseModel):
    """Update Graph Query Set public definition request payload."""
    definition: PublicDefinition = Field(...)

    class Config:
        populate_by_name = True


class UpdateGraphQuerySetRequest(BaseModel):
    """Update Graph Query Set request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "PayloadType",
    "ItemTag",
    "PublicDefinitionPart",
    "PublicDefinition",
    "CreateGraphQuerySetRequest",
    "GraphQuerySet",
    "GraphQuerySets",
    "DefinitionResponse",
    "UpdateGraphQuerySetDefinitionRequest",
    "UpdateGraphQuerySetRequest",
]
