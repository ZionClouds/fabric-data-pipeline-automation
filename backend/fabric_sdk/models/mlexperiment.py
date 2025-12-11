"""
ML Experiment Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/mlexperiment/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    ML_EXPERIMENT = "MLExperiment"


class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName")
    id: str = Field(...)

    class Config:
        populate_by_name = True


class Properties(BaseModel):
    """The machine learning experiment properties."""
    ml_flow_experiment_id: Optional[str] = Field(None, alias="mlFlowExperimentId")

    class Config:
        populate_by_name = True


class CreateMLExperimentRequest(BaseModel):
    """Create machine learning experiment request payload."""
    display_name: str = Field(..., alias="displayName")
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class MLExperiment(BaseModel):
    """A machine learning experiment object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    properties: Optional[Properties] = Field(None)
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class MLExperiments(BaseModel):
    """A list of machine learning experiments."""
    value: List[MLExperiment] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateMLExperimentRequest(BaseModel):
    """Update machine learning experiment request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "ItemTag",
    "Properties",
    "CreateMLExperimentRequest",
    "MLExperiment",
    "MLExperiments",
    "UpdateMLExperimentRequest",
]
