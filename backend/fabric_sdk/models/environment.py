"""
Environment Models for Microsoft Fabric SDK

Converted from: knowledge/fabric/environment/models.go
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from enum import Enum
from pydantic import BaseModel, Field


class PayloadType(str, Enum):
    """Payload type for definition parts."""
    INLINE_BASE64 = "InlineBase64"
    VSO_GIT = "VsoGit"


class ItemType(str, Enum):
    """Item type."""
    ENVIRONMENT = "Environment"


class PublishState(str, Enum):
    """Publish state."""
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class LibraryType(str, Enum):
    """Library type."""
    JAR = "Jar"
    WHEEL = "Wheel"
    PY_FILE = "PyFile"
    R_TAR = "RTar"
    PYPI = "PyPi"
    CONDA = "Conda"


class CustomPoolType(str, Enum):
    """Custom pool type."""
    WORKSPACE = "Workspace"
    CAPACITY = "Capacity"


class CustomPoolMemory(str, Enum):
    """Custom pool memory."""
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    XLARGE = "XLarge"
    XXLARGE = "XXLarge"


class DefinitionPart(BaseModel):
    """Environment definition part object."""
    path: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class Definition(BaseModel):
    """Environment public definition object."""
    parts: List[DefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName")
    id: str = Field(...)

    class Config:
        populate_by_name = True


class SparkLibraries(BaseModel):
    """Spark libraries publish information."""
    state: Optional[PublishState] = Field(None)

    class Config:
        populate_by_name = True


class SparkSettings(BaseModel):
    """Spark settings publish information."""
    state: Optional[PublishState] = Field(None)

    class Config:
        populate_by_name = True


class ComponentPublishInfo(BaseModel):
    """Publish info for each components in environment."""
    spark_libraries: Optional[SparkLibraries] = Field(None, alias="sparkLibraries")
    spark_settings: Optional[SparkSettings] = Field(None, alias="sparkSettings")

    class Config:
        populate_by_name = True


class PublishDetails(BaseModel):
    """Details of publish operation."""
    component_publish_info: Optional[ComponentPublishInfo] = Field(None, alias="componentPublishInfo")
    end_time: Optional[datetime] = Field(None, alias="endTime")
    start_time: Optional[datetime] = Field(None, alias="startTime")
    state: Optional[PublishState] = Field(None)
    target_version: Optional[str] = Field(None, alias="targetVersion")

    class Config:
        populate_by_name = True


class Properties(BaseModel):
    """Environment properties."""
    publish_details: PublishDetails = Field(..., alias="publishDetails")

    class Config:
        populate_by_name = True


class DynamicExecutorAllocationProperties(BaseModel):
    """Dynamic executor allocation properties."""
    enabled: bool = Field(...)
    max_executors: int = Field(..., alias="maxExecutors")
    min_executors: int = Field(..., alias="minExecutors")

    class Config:
        populate_by_name = True


class InstancePool(BaseModel):
    """An instance of a pool."""
    id: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    type: Optional[CustomPoolType] = Field(None)

    class Config:
        populate_by_name = True


class SparkProperty(BaseModel):
    """A Spark property key and its value."""
    key: Optional[str] = Field(None)
    value: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class SparkCompute(BaseModel):
    """Spark compute configuration."""
    driver_cores: Optional[int] = Field(None, alias="driverCores")
    driver_memory: Optional[CustomPoolMemory] = Field(None, alias="driverMemory")
    dynamic_executor_allocation: Optional[DynamicExecutorAllocationProperties] = Field(
        None, alias="dynamicExecutorAllocation"
    )
    executor_cores: Optional[int] = Field(None, alias="executorCores")
    executor_memory: Optional[CustomPoolMemory] = Field(None, alias="executorMemory")
    instance_pool: Optional[InstancePool] = Field(None, alias="instancePool")
    runtime_version: Optional[str] = Field(None, alias="runtimeVersion")
    spark_properties: Optional[List[SparkProperty]] = Field(None, alias="sparkProperties")

    class Config:
        populate_by_name = True


class CustomLibraries(BaseModel):
    """Custom libraries."""
    jar_files: Optional[List[str]] = Field(None, alias="jarFiles")
    py_files: Optional[List[str]] = Field(None, alias="pyFiles")
    r_tar_files: Optional[List[str]] = Field(None, alias="rTarFiles")
    wheel_files: Optional[List[str]] = Field(None, alias="wheelFiles")

    class Config:
        populate_by_name = True


class Library(BaseModel):
    """Custom or external library."""
    library_type: LibraryType = Field(..., alias="libraryType")
    name: str = Field(...)

    class Config:
        populate_by_name = True


class CustomLibrary(Library):
    """Custom library."""
    pass


class ExternalLibrary(Library):
    """External library."""
    version: str = Field(...)

    class Config:
        populate_by_name = True


class Libraries(BaseModel):
    """Environment libraries."""
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")
    libraries: Optional[List[Library]] = Field(None)

    class Config:
        populate_by_name = True


class LibrariesPreview(BaseModel):
    """Environment libraries preview."""
    custom_libraries: Optional[CustomLibraries] = Field(None, alias="customLibraries")
    environment_yml: Optional[str] = Field(None, alias="environmentYml")

    class Config:
        populate_by_name = True


class CreateEnvironmentRequest(BaseModel):
    """Create environment request payload."""
    display_name: str = Field(..., alias="displayName")
    definition: Optional[Definition] = Field(None)
    description: Optional[str] = Field(None, max_length=256)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class Environment(BaseModel):
    """An Environment item."""
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


class Environments(BaseModel):
    """A list of environments."""
    value: List[Environment] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """Environment public definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


class UpdateEnvironmentDefinitionRequest(BaseModel):
    """Update environment public definition request payload."""
    definition: Definition = Field(...)

    class Config:
        populate_by_name = True


class UpdateEnvironmentRequest(BaseModel):
    """Update environment request."""
    description: Optional[str] = Field(None, max_length=256)
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


class UpdateEnvironmentSparkComputeRequest(BaseModel):
    """Update environment spark compute request."""
    driver_cores: Optional[int] = Field(None, alias="driverCores")
    driver_memory: Optional[CustomPoolMemory] = Field(None, alias="driverMemory")
    dynamic_executor_allocation: Optional[DynamicExecutorAllocationProperties] = Field(
        None, alias="dynamicExecutorAllocation"
    )
    executor_cores: Optional[int] = Field(None, alias="executorCores")
    executor_memory: Optional[CustomPoolMemory] = Field(None, alias="executorMemory")
    instance_pool: Optional[InstancePool] = Field(None, alias="instancePool")
    runtime_version: Optional[str] = Field(None, alias="runtimeVersion")
    spark_properties: Optional[List[SparkProperty]] = Field(None, alias="sparkProperties")

    class Config:
        populate_by_name = True


class RemoveExternalLibrariesRequest(BaseModel):
    """Request to delete an external library."""
    name: str = Field(...)
    version: str = Field(...)

    class Config:
        populate_by_name = True


__all__ = [
    "PayloadType",
    "ItemType",
    "PublishState",
    "LibraryType",
    "CustomPoolType",
    "CustomPoolMemory",
    "DefinitionPart",
    "Definition",
    "ItemTag",
    "SparkLibraries",
    "SparkSettings",
    "ComponentPublishInfo",
    "PublishDetails",
    "Properties",
    "DynamicExecutorAllocationProperties",
    "InstancePool",
    "SparkProperty",
    "SparkCompute",
    "CustomLibraries",
    "Library",
    "CustomLibrary",
    "ExternalLibrary",
    "Libraries",
    "LibrariesPreview",
    "CreateEnvironmentRequest",
    "Environment",
    "Environments",
    "DefinitionResponse",
    "UpdateEnvironmentDefinitionRequest",
    "UpdateEnvironmentRequest",
    "UpdateEnvironmentSparkComputeRequest",
    "RemoveExternalLibrariesRequest",
]
