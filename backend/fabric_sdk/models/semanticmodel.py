"""
Semantic Model Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/semanticmodel/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class PayloadType(str, Enum):
    """Payload type for definition parts."""
    INLINE_BASE64 = "InlineBase64"
    VSO_GIT = "VsoGit"


class ItemType(str, Enum):
    """Item type."""
    SEMANTIC_MODEL = "SemanticModel"


class ConnectivityType(str, Enum):
    """Connectivity type."""
    SHAREABLE_CLOUD = "ShareableCloud"
    PERSONAL_CLOUD = "PersonalCloud"
    ON_PREMISES_GATEWAY = "OnPremisesGateway"
    VIRTUAL_NETWORK_GATEWAY = "VirtualNetworkGateway"


class DefinitionPart(BaseModel):
    """Semantic model definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class Definition(BaseModel):
    """Semantic model public definition object."""
    parts: List[DefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ListConnectionDetails(BaseModel):
    """The connection details output for list operations."""
    path: str = Field(...)
    type: str = Field(...)

    class Config:
        populate_by_name = True


class ConnectionBinding(BaseModel):
    """The details of the connection binding."""
    connection_details: ListConnectionDetails = Field(..., alias="connectionDetails")
    connectivity_type: Optional[ConnectivityType] = Field(None, alias="connectivityType")
    id: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class BindSemanticModelConnectionRequest(BaseModel):
    """Request to bind a data source reference of a semantic model to a data connection."""
    connection_binding: ConnectionBinding = Field(..., alias="connectionBinding")

    class Config:
        populate_by_name = True


class CreateSemanticModelRequest(BaseModel):
    """Create semantic model request payload."""
    definition: Definition = Field(...)
    display_name: str = Field(..., alias="displayName")
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName")
    id: str = Field(...)

    class Config:
        populate_by_name = True


class SemanticModel(BaseModel):
    """A semantic model object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class SemanticModels(BaseModel):
    """A list of semantic models."""
    value: List[SemanticModel] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """Semantic model public definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateSemanticModelDefinitionRequest(BaseModel):
    """Update semantic model public definition request payload."""
    definition: Definition = Field(...)

    class Config:
        populate_by_name = True


class UpdateSemanticModelRequest(BaseModel):
    """Update semantic model request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "PayloadType",
    "ItemType",
    "ConnectivityType",
    "DefinitionPart",
    "Definition",
    "ListConnectionDetails",
    "ConnectionBinding",
    "BindSemanticModelConnectionRequest",
    "CreateSemanticModelRequest",
    "ItemTag",
    "SemanticModel",
    "SemanticModels",
    "DefinitionResponse",
    "UpdateSemanticModelDefinitionRequest",
    "UpdateSemanticModelRequest",
]
