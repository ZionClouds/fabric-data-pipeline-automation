"""
Paginated Report Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/paginatedreport/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    PAGINATED_REPORT = "PaginatedReport"


class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName")
    id: str = Field(...)

    class Config:
        populate_by_name = True


class PaginatedReport(BaseModel):
    """A paginated report object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class PaginatedReports(BaseModel):
    """A list of paginated reports."""
    value: List[PaginatedReport] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdatePaginatedReportRequest(BaseModel):
    """Update paginated report request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "ItemTag",
    "PaginatedReport",
    "PaginatedReports",
    "UpdatePaginatedReportRequest",
]
