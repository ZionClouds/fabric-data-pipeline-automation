"""
Variable Library Models for Microsoft Fabric SDK

Contains models for variable library operations including:
- Create/Update/Delete variable libraries
- Definition management
- Value set management

Converted from: knowledge/fabric/variablelibrary/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

class Properties(BaseModel):
    """The VariableLibrary properties."""

    active_value_set_name: str = Field(
        ...,
        alias="activeValueSetName",
        description="The VariableLibrary current active value set"
    )

    class Config:
        populate_by_name = True


class PublicDefinitionPart(BaseModel):
    """VariableLibrary definition part object."""

    path: str = Field(
        ...,
        description="The VariableLibrary public definition part path"
    )
    payload: str = Field(
        ...,
        description="The VariableLibrary public definition part payload"
    )
    payload_type: PayloadType = Field(
        ...,
        alias="payloadType",
        description="The payload type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class PublicDefinition(BaseModel):
    """VariableLibrary public definition object."""

    parts: List[PublicDefinitionPart] = Field(
        ...,
        description="A list of definition parts"
    )
    format: Optional[str] = Field(
        None,
        description="The format of the item definition. Supported format: VariableLibraryV1"
    )

    class Config:
        populate_by_name = True


class VariableLibrary(BaseModel):
    """A VariableLibrary object."""

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
        description="The VariableLibrary properties"
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


class VariableLibraries(BaseModel):
    """A list of VariableLibraries."""

    value: List[VariableLibrary] = Field(
        ...,
        description="A list of VariableLibraries"
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


class CreateVariableLibraryRequest(BaseModel):
    """Create VariableLibrary request payload."""

    display_name: str = Field(
        ...,
        alias="displayName",
        description="The VariableLibrary display name"
    )
    definition: Optional[PublicDefinition] = Field(
        None,
        description="The VariableLibrary public definition"
    )
    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The VariableLibrary description. Maximum length is 256 characters"
    )
    folder_id: Optional[str] = Field(
        None,
        alias="folderId",
        description="The folder ID. If not specified or null, the VariableLibrary is created with the workspace as its folder"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateVariableLibraryRequest(BaseModel):
    """Update VariableLibrary request."""

    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The VariableLibrary description. Maximum length is 256 characters"
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="The VariableLibrary display name"
    )
    properties: Optional[Properties] = Field(
        None,
        description="The VariableLibrary properties"
    )

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """VariableLibrary public definition response."""

    definition: Optional[PublicDefinition] = Field(
        None,
        description="VariableLibrary public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateVariableLibraryDefinitionRequest(BaseModel):
    """Update VariableLibrary public definition request payload."""

    definition: PublicDefinition = Field(
        ...,
        description="VariableLibrary public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True
