"""
Warehouse Snapshot Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/warehousesnapshot/models.go
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    WAREHOUSE_SNAPSHOT = "WarehouseSnapshot"


class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName")
    id: str = Field(...)

    class Config:
        populate_by_name = True


class CreationPayload(BaseModel):
    """The Warehouse snapshot creation payload."""
    parent_warehouse_id: str = Field(..., alias="parentWarehouseId")
    snapshot_date_time: Optional[datetime] = Field(None, alias="snapshotDateTime")

    class Config:
        populate_by_name = True


class Properties(BaseModel):
    """The Warehouse snapshot properties."""
    connection_string: str = Field(..., alias="connectionString")
    parent_warehouse_id: str = Field(..., alias="parentWarehouseId")
    snapshot_date_time: datetime = Field(..., alias="snapshotDateTime")

    class Config:
        populate_by_name = True


class UpdateProperties(BaseModel):
    """The Warehouse snapshot update properties payload."""
    snapshot_date_time: datetime = Field(..., alias="snapshotDateTime")

    class Config:
        populate_by_name = True


class CreateWarehouseSnapshotRequest(BaseModel):
    """Create Warehouse snapshot request payload."""
    display_name: str = Field(..., alias="displayName")
    creation_payload: Optional[CreationPayload] = Field(None, alias="creationPayload")
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class WarehouseSnapshot(BaseModel):
    """A Warehouse snapshot object."""
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


class WarehouseSnapshots(BaseModel):
    """A list of Warehouse snapshots."""
    value: List[WarehouseSnapshot] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateWarehouseSnapshotRequest(BaseModel):
    """Update Warehouse snapshot request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")
    properties: Optional[UpdateProperties] = Field(None)

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "ItemTag",
    "CreationPayload",
    "Properties",
    "UpdateProperties",
    "CreateWarehouseSnapshotRequest",
    "WarehouseSnapshot",
    "WarehouseSnapshots",
    "UpdateWarehouseSnapshotRequest",
]
