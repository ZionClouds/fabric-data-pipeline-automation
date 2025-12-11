"""
KQL Dashboard Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/kqldashboard/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    KQL_DASHBOARD = "KQLDashboard"


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
    """KQL dashboard definition part object."""
    path: str = Field(...)
    payload: str = Field(...)
    payload_type: PayloadType = Field(..., alias="payloadType")

    class Config:
        populate_by_name = True


class Definition(BaseModel):
    """KQL dashboard public definition object."""
    parts: List[DefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CreateKQLDashboardRequest(BaseModel):
    """Create KQL dashboard request payload."""
    display_name: str = Field(..., alias="displayName")
    definition: Optional[Definition] = Field(None)
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class KQLDashboard(BaseModel):
    """A KQL dashboard object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class KQLDashboards(BaseModel):
    """A list of KQL dashboards."""
    value: List[KQLDashboard] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """KQL dashboard public definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateKQLDashboardDefinitionRequest(BaseModel):
    """Update KQL dashboard public definition request payload."""
    definition: Definition = Field(...)

    class Config:
        populate_by_name = True


class UpdateKQLDashboardRequest(BaseModel):
    """Update KQL dashboard request."""
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
    "CreateKQLDashboardRequest",
    "KQLDashboard",
    "KQLDashboards",
    "DefinitionResponse",
    "UpdateKQLDashboardDefinitionRequest",
    "UpdateKQLDashboardRequest",
]
