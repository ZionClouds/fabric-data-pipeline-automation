"""
Report Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/report/models.go
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
    REPORT = "Report"


class DefinitionPart(BaseModel):
    """Report definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class Definition(BaseModel):
    """
    Report public definition object.

    Refer to Fabric documentation for how to craft a report public definition.
    """
    parts: List[DefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CreateReportRequest(BaseModel):
    """Create report request payload."""
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


class Report(BaseModel):
    """A report object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class Reports(BaseModel):
    """A list of reports."""
    value: List[Report] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """Report public definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateReportDefinitionRequest(BaseModel):
    """Update report public definition request payload."""
    definition: Definition = Field(...)

    class Config:
        populate_by_name = True


class UpdateReportRequest(BaseModel):
    """Update report request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "PayloadType",
    "ItemType",
    "DefinitionPart",
    "Definition",
    "CreateReportRequest",
    "ItemTag",
    "Report",
    "Reports",
    "DefinitionResponse",
    "UpdateReportDefinitionRequest",
    "UpdateReportRequest",
]
