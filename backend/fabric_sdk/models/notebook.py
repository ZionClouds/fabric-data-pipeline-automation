"""
Notebook Models for Microsoft Fabric SDK

Contains models for notebook operations including:
- Create/Update/Delete notebooks
- Notebook definitions
- Livy sessions

Converted from: knowledge/fabric/notebook/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, PayloadType, Definition, DefinitionPart, Principal


# =============================================================================
# ENUMS
# =============================================================================

class NotebookItemType(str, Enum):
    """Notebook item type."""
    NOTEBOOK = "Notebook"


class NotebookFormat(str, Enum):
    """Notebook definition format."""
    IPYNB = "ipynb"
    FABRIC_GIT_SOURCE = "fabricGitSource"


class CellType(str, Enum):
    """Notebook cell type."""
    CODE = "code"
    MARKDOWN = "markdown"
    RAW = "raw"


class KernelName(str, Enum):
    """Notebook kernel name."""
    SYNAPSE_PYSPARK = "synapse_pyspark"
    SYNAPSE_SPARK = "synapse_spark"
    PYTHON3 = "python3"


class TimeUnit(str, Enum):
    """Time unit for duration."""
    MINUTE = "Minute"
    HOUR = "Hour"
    DAY = "Day"
    SECOND = "Second"


class State(str, Enum):
    """Livy session state."""
    NOT_STARTED = "NotStarted"
    STARTING = "Starting"
    RUNNING = "Running"
    IDLE = "Idle"
    BUSY = "Busy"
    SHUTTING_DOWN = "ShuttingDown"
    ERROR = "Error"
    DEAD = "Dead"
    KILLED = "Killed"
    SUCCESS = "Success"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class JobType(str, Enum):
    """Job type."""
    SPARK_JOB = "SparkJob"
    NOTEBOOK = "Notebook"


class Origin(str, Enum):
    """Job origin."""
    PIPELINE = "Pipeline"
    MANUAL = "Manual"
    SCHEDULED = "Scheduled"
    API = "Api"


class LivySessionItemType(str, Enum):
    """Livy session item type."""
    NOTEBOOK = "Notebook"
    SPARK_JOB_DEFINITION = "SparkJobDefinition"


class ItemReferenceType(str, Enum):
    """Item reference type."""
    ID = "Id"
    NAME = "Name"


class GroupType(str, Enum):
    """Group type."""
    DISTRIBUTION_LIST = "DistributionList"
    SECURITY_GROUP = "SecurityGroup"
    UNKNOWN = "Unknown"


class PrincipalType(str, Enum):
    """Principal type."""
    GROUP = "Group"
    SERVICE_PRINCIPAL = "ServicePrincipal"
    SERVICE_PRINCIPAL_PROFILE = "ServicePrincipalProfile"
    USER = "User"


# =============================================================================
# NOTEBOOK MODELS
# =============================================================================

class CreateNotebookRequest(BaseModel):
    """Create notebook request payload."""
    display_name: str = Field(..., alias="displayName", description="The notebook display name")
    description: Optional[str] = Field(None, description="The notebook description. Max 256 characters.")
    definition: Optional[Definition] = Field(None, description="The notebook public definition")
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class Notebook(BaseModel):
    """A notebook object."""
    id: Optional[str] = Field(None, description="The item ID")
    type: Optional[ItemType] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)

    class Config:
        populate_by_name = True


class Notebooks(BaseModel):
    """A list of notebooks."""
    value: List[Notebook] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateNotebookRequest(BaseModel):
    """Update notebook request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class UpdateNotebookDefinitionRequest(BaseModel):
    """Update notebook definition request."""
    definition: Definition = Field(...)

    class Config:
        populate_by_name = True


class NotebookDefinitionResponse(BaseModel):
    """Notebook definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


# =============================================================================
# NOTEBOOK CONTENT MODELS (ipynb format)
# =============================================================================

class CellMetadata(BaseModel):
    """Notebook cell metadata."""
    tags: Optional[List[str]] = Field(None)
    collapsed: Optional[bool] = Field(None)
    scrolled: Optional[bool] = Field(None)
    trusted: Optional[bool] = Field(None)
    editable: Optional[bool] = Field(None)
    deletable: Optional[bool] = Field(None)
    name: Optional[str] = Field(None)
    execution: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class CellOutput(BaseModel):
    """Notebook cell output."""
    output_type: str = Field(..., alias="output_type")
    name: Optional[str] = Field(None)
    text: Optional[List[str]] = Field(None)
    data: Optional[Dict[str, Any]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)
    execution_count: Optional[int] = Field(None, alias="execution_count")
    ename: Optional[str] = Field(None)
    evalue: Optional[str] = Field(None)
    traceback: Optional[List[str]] = Field(None)

    class Config:
        populate_by_name = True


class NotebookCell(BaseModel):
    """A notebook cell."""
    cell_type: CellType = Field(..., alias="cell_type")
    source: Any = Field(..., description="Cell source code (string or list of strings)")
    metadata: Optional[CellMetadata] = Field(default_factory=CellMetadata)
    outputs: Optional[List[CellOutput]] = Field(default_factory=list)
    execution_count: Optional[int] = Field(None, alias="execution_count")

    class Config:
        populate_by_name = True


class KernelSpec(BaseModel):
    """Notebook kernel specification."""
    name: str = Field(default="synapse_pyspark")
    display_name: str = Field(default="Synapse PySpark", alias="display_name")
    language: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class LanguageInfo(BaseModel):
    """Notebook language information."""
    name: str = Field(default="python")
    version: Optional[str] = Field(None)
    mimetype: Optional[str] = Field(None)
    file_extension: Optional[str] = Field(None, alias="file_extension")
    pygments_lexer: Optional[str] = Field(None, alias="pygments_lexer")
    codemirror_mode: Optional[Any] = Field(None, alias="codemirror_mode")
    nbconvert_exporter: Optional[str] = Field(None, alias="nbconvert_exporter")

    class Config:
        populate_by_name = True


class NotebookMetadata(BaseModel):
    """Notebook metadata."""
    kernelspec: Optional[KernelSpec] = Field(default_factory=lambda: KernelSpec())
    language_info: Optional[LanguageInfo] = Field(default_factory=lambda: LanguageInfo(), alias="language_info")
    spark_compute: Optional[Dict[str, Any]] = Field(None, alias="spark_compute")
    dependencies: Optional[Dict[str, Any]] = Field(None)
    widgets: Optional[Dict[str, Any]] = Field(None)
    microsoft: Optional[Dict[str, Any]] = Field(None)
    nteract: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class NotebookContent(BaseModel):
    """Complete notebook content (ipynb format)."""
    nbformat: int = Field(default=4)
    nbformat_minor: int = Field(default=2)
    cells: List[NotebookCell] = Field(default_factory=list)
    metadata: Optional[NotebookMetadata] = Field(default_factory=lambda: NotebookMetadata())

    class Config:
        populate_by_name = True


# =============================================================================
# LIVY SESSION MODELS
# =============================================================================

class Duration(BaseModel):
    """A duration object."""
    time_unit: TimeUnit = Field(..., alias="timeUnit")
    value: float = Field(...)

    class Config:
        populate_by_name = True


class ItemReference(BaseModel):
    """An item reference object."""
    reference_type: ItemReferenceType = Field(..., alias="referenceType")

    class Config:
        populate_by_name = True


class ItemReferenceByID(ItemReference):
    """An item reference by ID."""
    reference_type: ItemReferenceType = Field(default=ItemReferenceType.ID, alias="referenceType")
    item_id: str = Field(..., alias="itemId")
    workspace_id: str = Field(..., alias="workspaceId")

    class Config:
        populate_by_name = True


class PrincipalGroupDetails(BaseModel):
    """Group specific details."""
    group_type: Optional[GroupType] = Field(None, alias="groupType")

    class Config:
        populate_by_name = True


class PrincipalServicePrincipalDetails(BaseModel):
    """Service principal specific details."""
    aad_app_id: Optional[str] = Field(None, alias="aadAppId")

    class Config:
        populate_by_name = True


class PrincipalServicePrincipalProfileDetails(BaseModel):
    """Service principal profile details."""
    parent_principal: Optional["NotebookPrincipal"] = Field(None, alias="parentPrincipal")

    class Config:
        populate_by_name = True


class PrincipalUserDetails(BaseModel):
    """User principal specific details."""
    user_principal_name: Optional[str] = Field(None, alias="userPrincipalName")

    class Config:
        populate_by_name = True


class NotebookPrincipal(BaseModel):
    """Represents an identity or a Microsoft Entra group."""
    id: str = Field(...)
    type: PrincipalType = Field(...)
    display_name: Optional[str] = Field(None, alias="displayName")
    group_details: Optional[PrincipalGroupDetails] = Field(None, alias="groupDetails")
    service_principal_details: Optional[PrincipalServicePrincipalDetails] = Field(
        None, alias="servicePrincipalDetails"
    )
    service_principal_profile_details: Optional[PrincipalServicePrincipalProfileDetails] = Field(
        None, alias="servicePrincipalProfileDetails"
    )
    user_details: Optional[PrincipalUserDetails] = Field(None, alias="userDetails")

    class Config:
        populate_by_name = True


class LivySession(BaseModel):
    """Livy session response for notebooks."""
    livy_id: Optional[str] = Field(None, alias="livyId")
    livy_name: Optional[str] = Field(None, alias="livyName")
    spark_application_id: Optional[str] = Field(None, alias="sparkApplicationId")
    state: Optional[State] = Field(None)
    job_type: Optional[JobType] = Field(None, alias="jobType")
    origin: Optional[Origin] = Field(None)
    item: Optional[ItemReferenceByID] = Field(None)
    item_name: Optional[str] = Field(None, alias="itemName")
    item_type: Optional[LivySessionItemType] = Field(None, alias="itemType")
    submitter: Optional[NotebookPrincipal] = Field(None)
    submitted_date_time: Optional[datetime] = Field(None, alias="submittedDateTime")
    start_date_time: Optional[datetime] = Field(None, alias="startDateTime")
    end_date_time: Optional[datetime] = Field(None, alias="endDateTime")
    queued_duration: Optional[Duration] = Field(None, alias="queuedDuration")
    running_duration: Optional[Duration] = Field(None, alias="runningDuration")
    total_duration: Optional[Duration] = Field(None, alias="totalDuration")
    driver_cores: Optional[int] = Field(None, alias="driverCores")
    driver_memory: Optional[int] = Field(None, alias="driverMemory")
    executor_cores: Optional[Any] = Field(None, alias="executorCores")
    executor_memory: Optional[int] = Field(None, alias="executorMemory")
    num_executors: Optional[int] = Field(None, alias="numExecutors")
    is_dynamic_allocation_enabled: Optional[bool] = Field(None, alias="isDynamicAllocationEnabled")
    dynamic_allocation_max_executors: Optional[int] = Field(None, alias="dynamicAllocationMaxExecutors")
    is_high_concurrency: Optional[bool] = Field(None, alias="isHighConcurrency")
    capacity_id: Optional[str] = Field(None, alias="capacityId")
    runtime_version: Optional[str] = Field(None, alias="runtimeVersion")
    operation_name: Optional[str] = Field(None, alias="operationName")
    attempt_number: Optional[int] = Field(None, alias="attemptNumber")
    max_number_of_attempts: Optional[int] = Field(None, alias="maxNumberOfAttempts")
    cancellation_reason: Optional[str] = Field(None, alias="cancellationReason")

    class Config:
        populate_by_name = True


class LivySessions(BaseModel):
    """A list of livy sessions."""
    value: List[LivySession] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_code_cell(source: str, tags: List[str] = None) -> NotebookCell:
    """Create a code cell."""
    metadata = CellMetadata(tags=tags) if tags else CellMetadata()
    return NotebookCell(
        cell_type=CellType.CODE,
        source=source,
        metadata=metadata,
        outputs=[],
        execution_count=None
    )


def create_markdown_cell(source: str) -> NotebookCell:
    """Create a markdown cell."""
    return NotebookCell(
        cell_type=CellType.MARKDOWN,
        source=source,
        metadata=CellMetadata(),
        outputs=[]
    )


def create_parameters_cell(parameters: Dict[str, Any]) -> NotebookCell:
    """Create a parameters cell with tags."""
    lines = ["# Parameters"]
    for name, value in parameters.items():
        if isinstance(value, str):
            lines.append(f'{name} = "{value}"')
        else:
            lines.append(f'{name} = {value}')

    return NotebookCell(
        cell_type=CellType.CODE,
        source="\n".join(lines),
        metadata=CellMetadata(tags=["parameters"]),
        outputs=[],
        execution_count=None
    )


def create_notebook(
    cells: List[NotebookCell],
    kernel_name: str = "synapse_pyspark",
    kernel_display_name: str = "Synapse PySpark"
) -> NotebookContent:
    """Create a complete notebook content."""
    return NotebookContent(
        nbformat=4,
        nbformat_minor=2,
        cells=cells,
        metadata=NotebookMetadata(
            kernelspec=KernelSpec(name=kernel_name, display_name=kernel_display_name),
            language_info=LanguageInfo(name="python")
        )
    )


def create_pyspark_notebook(
    code_cells: List[str],
    parameters: Dict[str, Any] = None
) -> NotebookContent:
    """Create a PySpark notebook with optional parameters."""
    cells = []

    # Add parameters cell if provided
    if parameters:
        cells.append(create_parameters_cell(parameters))

    # Add code cells
    for code in code_cells:
        cells.append(create_code_cell(code))

    return create_notebook(cells)


# Update forward references
PrincipalServicePrincipalProfileDetails.model_rebuild()
