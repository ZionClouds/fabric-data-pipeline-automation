"""
Warehouse Models for Microsoft Fabric SDK

Contains models for warehouse operations including:
- Create/Update/Delete warehouses
- SQL endpoints

Converted from: knowledge/fabric/warehouse/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, Definition


# =============================================================================
# ENUMS
# =============================================================================

class WarehouseItemType(str, Enum):
    """Warehouse item type."""
    WAREHOUSE = "Warehouse"


# =============================================================================
# WAREHOUSE MODELS
# =============================================================================

class CreateWarehouseRequest(BaseModel):
    """Create warehouse request payload."""
    display_name: str = Field(..., alias="displayName", description="The warehouse display name")
    description: Optional[str] = Field(None, description="The warehouse description. Max 256 characters.")
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class WarehouseProperties(BaseModel):
    """Warehouse properties."""
    connection_string: Optional[str] = Field(None, alias="connectionString")
    created_date: Optional[str] = Field(None, alias="createdDate")
    last_updated_time: Optional[str] = Field(None, alias="lastUpdatedTime")

    class Config:
        populate_by_name = True


class Warehouse(BaseModel):
    """A warehouse object."""
    id: Optional[str] = Field(None, description="The item ID")
    type: Optional[ItemType] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)
    properties: Optional[WarehouseProperties] = Field(None)

    class Config:
        populate_by_name = True


class Warehouses(BaseModel):
    """A list of warehouses."""
    value: List[Warehouse] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateWarehouseRequest(BaseModel):
    """Update warehouse request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True
