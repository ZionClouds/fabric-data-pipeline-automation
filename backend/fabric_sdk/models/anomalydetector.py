"""
Anomaly Detector Models for Microsoft Fabric SDK

Contains models for anomaly detector operations including:
- Create/Update/Delete anomaly detectors
- Definition management

Converted from: knowledge/fabric/anomalydetector/models.go and constants.go
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
    """Format for the AnomalyDetector definition."""
    ANOMALY_DETECTOR_V1 = "AnomalyDetectorV1"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

class Properties(BaseModel):
    """The AnomalyDetector properties."""

    onelake_root_path: str = Field(
        ...,
        alias="oneLakeRootPath",
        description="OneLake path to the AnomalyDetector root directory"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class DefinitionPart(BaseModel):
    """AnomalyDetector definition part object."""

    path: Optional[str] = Field(
        None,
        description="The AnomalyDetector definition part path"
    )
    payload: Optional[str] = Field(
        None,
        description="The AnomalyDetector definition part payload"
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
    """AnomalyDetector definition object."""

    parts: List[DefinitionPart] = Field(
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


class AnomalyDetector(BaseModel):
    """A AnomalyDetector object."""

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
        description="The AnomalyDetector properties"
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


class AnomalyDetectors(BaseModel):
    """A list of AnomalyDetectors."""

    value: List[AnomalyDetector] = Field(
        ...,
        description="A list of AnomalyDetectors"
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


class CreateAnomalyDetectorRequest(BaseModel):
    """Create AnomalyDetector request payload."""

    display_name: str = Field(
        ...,
        alias="displayName",
        description="The AnomalyDetector display name"
    )
    definition: Optional[Definition] = Field(
        None,
        description="The AnomalyDetector definition"
    )
    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The AnomalyDetector description. Maximum length is 256 characters"
    )
    folder_id: Optional[str] = Field(
        None,
        alias="folderId",
        description="The folder ID. If not specified or null, the AnomalyDetector is created with the workspace as its folder"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateAnomalyDetectorRequest(BaseModel):
    """Update AnomalyDetector request."""

    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The AnomalyDetector description. Maximum length is 256 characters"
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="The AnomalyDetector display name"
    )

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """AnomalyDetector definition response."""

    definition: Optional[Definition] = Field(
        None,
        description="AnomalyDetector definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateAnomalyDetectorDefinitionRequest(BaseModel):
    """Update AnomalyDetector definition request payload."""

    definition: Definition = Field(
        ...,
        description="AnomalyDetector definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True
