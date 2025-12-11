"""
ML Model Models for Microsoft Fabric SDK

Contains models for machine learning model operations including:
- Create/Update ML models
- Endpoint management and scoring
- Version management

Converted from: knowledge/fabric/mlmodel/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class EndpointDefaultVersionConfigurationPolicy(str, Enum):
    """Default version assignment behavior."""
    SYSTEM_PROMOTED = "SystemPromoted"
    USER_PROMOTED = "UserPromoted"


class ModelEndpointVersionStatus(str, Enum):
    """Status of a machine learning model endpoint version."""
    ACTIVATING = "Activating"
    ACTIVATED = "Activated"
    ACTIVATION_FAILED = "ActivationFailed"
    DEACTIVATING = "Deactivating"
    DEACTIVATED = "Deactivated"


class ScaleRule(str, Enum):
    """Machine learning model endpoint scale rule."""
    SCALE_TO_ZERO = "ScaleToZero"
    NO_SCALE_TO_ZERO = "NoScaleToZero"


class FormatType(str, Enum):
    """Format type of data."""
    PANDAS_SPLIT = "pandas_split"


class Orientation(str, Enum):
    """Orientation of data."""
    SPLIT = "split"


# =============================================================================
# MODELS
# =============================================================================

class DataSchema(BaseModel):
    """Machine learning model data schema."""

    name: str = Field(..., description="The name of the signature")
    required: bool = Field(..., description="Whether the signature is required")
    type: str = Field(..., description="The type of the signature")

    class Config:
        populate_by_name = True


class ErrorRelatedResource(BaseModel):
    """The error related resource details object."""

    resource_id: Optional[str] = Field(None, alias="resourceId")
    resource_type: Optional[str] = Field(None, alias="resourceType")

    class Config:
        populate_by_name = True


class EndpointVersionInfoFailureDetails(BaseModel):
    """Activation Failure details."""

    error_code: Optional[str] = Field(None, alias="errorCode")
    message: Optional[str] = None
    related_resource: Optional[ErrorRelatedResource] = Field(None, alias="relatedResource")

    class Config:
        populate_by_name = True


class EndpointVersionInfo(BaseModel):
    """Machine Learning Model Endpoint version information."""

    status: Optional[ModelEndpointVersionStatus] = None
    version_name: Optional[str] = Field(None, alias="versionName")
    failure_details: Optional[EndpointVersionInfoFailureDetails] = Field(None, alias="failureDetails")
    scale_rule: Optional[ScaleRule] = Field(None, alias="scaleRule")
    input_signature: Optional[List[DataSchema]] = Field(None, alias="inputSignature")
    output_signature: Optional[List[DataSchema]] = Field(None, alias="outputSignature")

    class Config:
        populate_by_name = True
        use_enum_values = True


class Endpoint(BaseModel):
    """A machine learning model endpoint object."""

    default_version_assignment_behavior: EndpointDefaultVersionConfigurationPolicy = Field(
        ..., alias="defaultVersionAssignmentBehavior"
    )
    default_version_info: EndpointVersionInfo = Field(..., alias="defaultVersionInfo")
    default_version_name: str = Field(..., alias="defaultVersionName")

    class Config:
        populate_by_name = True
        use_enum_values = True


class EndpointVersions(BaseModel):
    """All MLModel Versions Endpoints info."""

    value: List[EndpointVersionInfo] = Field(..., description="All versions available as endpoint")
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class MLModel(BaseModel):
    """A machine learning model object."""

    type: ItemType = Field(..., description="The item type")
    description: Optional[str] = None
    display_name: Optional[str] = Field(None, alias="displayName")

    # Read-only fields
    folder_id: Optional[str] = Field(None, alias="folderId")
    id: Optional[str] = None
    tags: Optional[List[ItemTag]] = None
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True
        use_enum_values = True


class MLModels(BaseModel):
    """A list of machine learning models."""

    value: List[MLModel] = Field(..., description="A list of machine learning models")
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class ScoreDataRequest(BaseModel):
    """Machine learning model endpoint request to score the given input data."""

    inputs: List[List[Any]] = Field(..., description="Machine learning inputs to score")
    format_type: Optional[FormatType] = Field(None, alias="formatType")
    orientation: Optional[Orientation] = None

    class Config:
        populate_by_name = True
        use_enum_values = True


class ScoreDataResponse(BaseModel):
    """Machine learning model endpoint response to score the given input data."""

    format_type: FormatType = Field(..., alias="formatType")
    orientation: Orientation = Field(...)
    predictions: Optional[List[List[Any]]] = None

    class Config:
        populate_by_name = True
        use_enum_values = True


class CreateMLModelRequest(BaseModel):
    """Create machine learning model request payload."""

    display_name: str = Field(..., alias="displayName")
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class UpdateMLModelRequest(BaseModel):
    """Update machine learning model request."""

    description: Optional[str] = Field(None, max_length=256)

    class Config:
        populate_by_name = True


class UpdateMLModelEndpointRequest(BaseModel):
    """Machine learning model endpoint request body to update Model Endpoint properties."""

    default_version_assignment_behavior: Optional[EndpointDefaultVersionConfigurationPolicy] = Field(
        None, alias="defaultVersionAssignmentBehavior"
    )
    default_version_name: Optional[str] = Field(None, alias="defaultVersionName")

    class Config:
        populate_by_name = True
        use_enum_values = True


class UpdateMLModelEndpointVersionRequest(BaseModel):
    """Machine learning model endpoint version configuration info."""

    scale_rule: Optional[ScaleRule] = Field(None, alias="scaleRule")

    class Config:
        populate_by_name = True
        use_enum_values = True
