"""
Mirrored Warehouse Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/mirroredwarehouse/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    MIRRORED_WAREHOUSE = "MirroredWarehouse"


class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName")
    id: str = Field(...)

    class Config:
        populate_by_name = True


class MirroredWarehouse(BaseModel):
    """A mirrored warehouse object."""
    type: ItemType = Field(...)
    description: Optional[str] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = Field(None)
    tags: Optional[List[ItemTag]] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class MirroredWarehouses(BaseModel):
    """A list of mirrored warehouses."""
    value: List[MirroredWarehouse] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "ItemTag",
    "MirroredWarehouse",
    "MirroredWarehouses",
]
