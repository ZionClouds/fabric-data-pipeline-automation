"""
Graph Model Models for Microsoft Fabric SDK

Contains models for graph model operations including:
- Create/Update/Delete graph models
- Graph types (nodes and edges)
- Query execution

Converted from: knowledge/fabric/graphmodel/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class DefinitionFormat(str, Enum):
    """Definition format for graph models."""
    GRAPH_MODEL_V1 = "GraphModelV1"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

class Property(BaseModel):
    """A graph element property."""

    name: str = Field(
        ...,
        description="The property name"
    )
    type: str = Field(
        ...,
        description="The property type"
    )

    class Config:
        populate_by_name = True


class NodeTypeReference(BaseModel):
    """A reference to a node type."""

    alias: str = Field(
        ...,
        description="The node type alias"
    )

    class Config:
        populate_by_name = True


class NodeType(BaseModel):
    """A graph node type."""

    alias: str = Field(
        ...,
        description="The node type alias"
    )
    labels: List[str] = Field(
        ...,
        description="The node type labels"
    )
    primary_key_properties: List[str] = Field(
        ...,
        alias="primaryKeyProperties",
        description="A list of node type primary key properties"
    )
    properties: Optional[List[Property]] = Field(
        None,
        description="A list of node type properties"
    )

    class Config:
        populate_by_name = True


class EdgeType(BaseModel):
    """A graph edge type."""

    alias: str = Field(
        ...,
        description="The edge type alias"
    )
    destination_node_type: NodeTypeReference = Field(
        ...,
        alias="destinationNodeType",
        description="The target node type"
    )
    labels: List[str] = Field(
        ...,
        description="The edge type labels"
    )
    source_node_type: NodeTypeReference = Field(
        ...,
        alias="sourceNodeType",
        description="The source node type"
    )
    properties: Optional[List[Property]] = Field(
        None,
        description="A list of edge type properties"
    )

    class Config:
        populate_by_name = True


class GraphType(BaseModel):
    """The graph type that specifies the structure of a graph."""

    edge_types: Optional[List[EdgeType]] = Field(
        None,
        alias="edgeTypes",
        description="A list of graph edge types"
    )
    node_types: Optional[List[NodeType]] = Field(
        None,
        alias="nodeTypes",
        description="A list of graph node types"
    )

    class Config:
        populate_by_name = True


class Properties(BaseModel):
    """The GraphModel properties."""

    onelake_root_path: str = Field(
        ...,
        alias="oneLakeRootPath",
        description="OneLake path to the GraphModel root directory"
    )

    class Config:
        populate_by_name = True


class PublicDefinitionPart(BaseModel):
    """GraphModel definition part object."""

    path: Optional[str] = Field(
        None,
        description="The GraphModel public definition part path"
    )
    payload: Optional[str] = Field(
        None,
        description="The GraphModel public definition part payload"
    )
    payload_type: Optional[PayloadType] = Field(
        None,
        alias="payloadType",
        description="The payload type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class PublicDefinition(BaseModel):
    """GraphModel public definition object."""

    parts: List[PublicDefinitionPart] = Field(
        ...,
        description="A list of definition parts"
    )
    format: Optional[DefinitionFormat] = Field(
        None,
        description="The format of the item definition"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class GraphModel(BaseModel):
    """A GraphModel object."""

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
        description="The GraphModel properties"
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


class GraphModels(BaseModel):
    """A list of GraphModels."""

    value: List[GraphModel] = Field(
        ...,
        description="A list of GraphModels"
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


class ExecuteQueryRequest(BaseModel):
    """Execute query request payload."""

    query: str = Field(
        ...,
        description="The query string"
    )

    class Config:
        populate_by_name = True


class CreateGraphModelRequest(BaseModel):
    """Create GraphModel request payload."""

    display_name: str = Field(
        ...,
        alias="displayName",
        description="The GraphModel display name"
    )
    definition: Optional[PublicDefinition] = Field(
        None,
        description="The GraphModel public definition"
    )
    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The GraphModel description"
    )
    folder_id: Optional[str] = Field(
        None,
        alias="folderId",
        description="The folder ID"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateGraphModelRequest(BaseModel):
    """Update GraphModel request."""

    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The GraphModel description"
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="The GraphModel display name"
    )

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """GraphModel public definition response."""

    definition: Optional[PublicDefinition] = Field(
        None,
        description="GraphModel public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateGraphModelDefinitionRequest(BaseModel):
    """Update GraphModel public definition request payload."""

    definition: PublicDefinition = Field(
        ...,
        description="GraphModel public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True
