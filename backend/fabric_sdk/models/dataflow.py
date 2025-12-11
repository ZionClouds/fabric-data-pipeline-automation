"""
Dataflow Models for Microsoft Fabric SDK

Contains models for Dataflow Gen2 operations.

Converted from: knowledge/fabric/dataflow/models.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, Definition


class DataflowType(str, Enum):
    """Dataflow type."""
    DATAFLOW_FABRIC = "DataflowFabric"
    DATAFLOW_GEN1 = "DataflowGen1"


class CreateDataflowRequest(BaseModel):
    """Create dataflow request payload."""
    display_name: str = Field(..., alias="displayName")
    description: Optional[str] = Field(None)
    definition: Optional[Definition] = Field(None)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class Dataflow(BaseModel):
    """A dataflow object."""
    id: Optional[str] = Field(None)
    type: Optional[ItemType] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)

    class Config:
        populate_by_name = True


class Dataflows(BaseModel):
    """A list of dataflows."""
    value: List[Dataflow] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateDataflowRequest(BaseModel):
    """Update dataflow request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True
