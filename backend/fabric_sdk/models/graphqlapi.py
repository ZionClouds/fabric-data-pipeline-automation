"""
GraphQL API Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/graphqlapi/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    GRAPHQL_API = "GraphQLApi"


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
    """GraphQL API definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class PublicDefinition(BaseModel):
    """GraphQL API public definition object."""
    parts: List[PublicDefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CreateGraphQLAPIRequest(BaseModel):
    """Create API for GraphQL request payload."""
    display_name: str = Field(..., alias="displayName")
    definition: Optional[PublicDefinition] = Field(None)
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class GraphQLAPI(BaseModel):
    """An API for GraphQL item."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class GraphQLApis(BaseModel):
    """A list of API for GraphQL items."""
    value: List[GraphQLAPI] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """API for GraphQL public definition response."""
    definition: Optional[PublicDefinition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateGraphQLAPIDefinitionRequest(BaseModel):
    """Update API for GraphQL public definition request payload."""
    definition: PublicDefinition = Field(...)

    class Config:
        populate_by_name = True


class UpdateGraphQLAPIRequest(BaseModel):
    """Update API for GraphQL request."""
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
    "CreateGraphQLAPIRequest",
    "GraphQLAPI",
    "GraphQLApis",
    "DefinitionResponse",
    "UpdateGraphQLAPIDefinitionRequest",
    "UpdateGraphQLAPIRequest",
]
