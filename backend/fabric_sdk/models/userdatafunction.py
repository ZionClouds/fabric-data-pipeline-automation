"""
User Data Function Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/userdatafunction/models.go
"""

from __future__ import annotations
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Item type."""
    USER_DATA_FUNCTION = "UserDataFunction"


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


class Properties(BaseModel):
    """The User Data Function properties."""
    one_lake_root_path: str = Field(..., alias="oneLakeRootPath")

    class Config:
        populate_by_name = True


class PublicDefinitionPart(BaseModel):
    """User Data Function definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class PublicDefinition(BaseModel):
    """User Data Function public definition object."""
    parts: List[PublicDefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CreateUserDataFunctionRequest(BaseModel):
    """Create User Data Function request payload."""
    display_name: str = Field(..., alias="displayName")
    definition: Optional[PublicDefinition] = Field(None)
    description: Optional[str] = Field(None, max_length=256)

    class Config:
        populate_by_name = True


class UserDataFunction(BaseModel):
    """A User Data Function object."""
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


class UserDataFunctions(BaseModel):
    """A list of User Data Functions."""
    value: List[UserDataFunction] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """User Data Function public definition response."""
    definition: Optional[PublicDefinition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateUserDataFunctionDefinitionRequest(BaseModel):
    """Update User Data Function public definition request payload."""
    definition: PublicDefinition = Field(...)

    class Config:
        populate_by_name = True


class UpdateUserDataFunctionRequest(BaseModel):
    """Update User Data Function request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


__all__ = [
    "ItemType",
    "PayloadType",
    "ItemTag",
    "Properties",
    "PublicDefinitionPart",
    "PublicDefinition",
    "CreateUserDataFunctionRequest",
    "UserDataFunction",
    "UserDataFunctions",
    "DefinitionResponse",
    "UpdateUserDataFunctionDefinitionRequest",
    "UpdateUserDataFunctionRequest",
]
