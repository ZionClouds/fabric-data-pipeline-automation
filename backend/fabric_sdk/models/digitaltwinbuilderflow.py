"""
Digital Twin Builder Flow Models for Microsoft Fabric SDK

Contains models for digital twin builder flow operations including:
- Create/Update/Delete digital twin builder flows
- Definition management
- Item references

Converted from: knowledge/fabric/digitaltwinbuilderflow/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class ItemReferenceType(str, Enum):
    """Item reference type."""
    BY_ID = "ById"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


# =============================================================================
# MODELS
# =============================================================================

class ItemReference(BaseModel):
    """An item reference object."""

    reference_type: ItemReferenceType = Field(
        ...,
        alias="referenceType",
        description="The item reference type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class ItemReferenceByID(BaseModel):
    """An item reference by ID object."""

    item_id: str = Field(
        ...,
        alias="itemId",
        description="The ID of the item"
    )
    reference_type: ItemReferenceType = Field(
        ...,
        alias="referenceType",
        description="The item reference type"
    )
    workspace_id: str = Field(
        ...,
        alias="workspaceId",
        description="The workspace ID of the item"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class Properties(BaseModel):
    """The Digital Twin Builder Flow properties."""

    digital_twin_builder_item_reference: Union[ItemReference, ItemReferenceByID] = Field(
        ...,
        alias="digitalTwinBuilderItemReference",
        description="The Digital Twin Builder Item Reference"
    )

    class Config:
        populate_by_name = True


class PublicDefinitionPart(BaseModel):
    """Digital Twin Builder Flow definition part object."""

    path: Optional[str] = Field(
        None,
        description="The Digital Twin Builder Flow public definition part path"
    )
    payload: Optional[str] = Field(
        None,
        description="The Digital Twin Builder Flow public definition part payload"
    )
    payload_type: Optional[PayloadType] = Field(
        None,
        alias="payloadType",
        description="The payload type"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class PublicDefinition(BaseModel):
    """The Digital Twin Builder Flow public definition object."""

    parts: List[PublicDefinitionPart] = Field(
        ...,
        description="A list of definition parts"
    )

    class Config:
        populate_by_name = True


class CreationPayload(BaseModel):
    """The Digital Twin Builder Flow creation payload."""

    digital_twin_builder_item_reference: Union[ItemReference, ItemReferenceByID] = Field(
        ...,
        alias="digitalTwinBuilderItemReference",
        description="The Digital Twin Builder Item Reference"
    )

    class Config:
        populate_by_name = True


class DigitalTwinBuilderFlow(BaseModel):
    """A Digital Twin Builder Flow object."""

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
        description="The Digital Twin Builder Flow properties"
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


class DigitalTwinBuilderFlows(BaseModel):
    """A list of Digital Twin Builder Flows."""

    value: List[DigitalTwinBuilderFlow] = Field(
        ...,
        description="A list of Digital Twin Builder Flows"
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


class CreateDigitalTwinBuilderFlowRequest(BaseModel):
    """Create Digital Twin Builder Flow request payload."""

    display_name: str = Field(
        ...,
        alias="displayName",
        description="The Digital Twin Builder Flow display name"
    )
    creation_payload: Optional[CreationPayload] = Field(
        None,
        alias="creationPayload",
        description="The creation payload"
    )
    definition: Optional[PublicDefinition] = Field(
        None,
        description="The Digital Twin Builder Flow public definition"
    )
    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The Digital Twin Builder Flow description"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateDigitalTwinBuilderFlowRequest(BaseModel):
    """Update Digital Twin Builder Flow request."""

    description: Optional[str] = Field(
        None,
        max_length=256,
        description="The Digital Twin Builder Flow description"
    )
    display_name: Optional[str] = Field(
        None,
        alias="displayName",
        description="The Digital Twin Builder Flow display name"
    )

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """The Digital Twin Builder Flow public definition response."""

    definition: Optional[PublicDefinition] = Field(
        None,
        description="The Digital Twin Builder Flow public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateDigitalTwinBuilderFlowDefinitionRequest(BaseModel):
    """Update Digital Twin Builder Flow public definition request payload."""

    definition: PublicDefinition = Field(
        ...,
        description="The Digital Twin Builder Flow public definition object"
    )

    class Config:
        populate_by_name = True
        use_enum_values = True
