"""
Data Models for AI Pipeline Generation Service

Contains Pydantic models for configuration, requests, and responses.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class FileFormat(str, Enum):
    """Supported file formats."""
    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"
    DELTA = "delta"
    AVRO = "avro"


class MaskingType(str, Enum):
    """PII/PHI masking types."""
    REDACT = "redact"      # john@email.com → <EMAIL_ADDRESS>
    PARTIAL = "partial"    # john@email.com → j***@***.com
    FAKE = "fake"          # john@email.com → user_8x7k@masked.com
    HASH = "hash"          # john@email.com → a1b2c3d4e5f6...


class DestinationType(str, Enum):
    """Destination types in Lakehouse."""
    FILES = "Files"
    TABLES = "Tables"


class TransformationType(str, Enum):
    """Transformation types."""
    FILTER = "filter"
    SELECT = "select"
    RENAME = "rename"
    AGGREGATE = "aggregate"
    JOIN = "join"
    CUSTOM = "custom"


class ConversationState(str, Enum):
    """State of the conversation."""
    INITIAL = "initial"
    GATHERING_SOURCE = "gathering_source"
    GATHERING_PII = "gathering_pii"
    GATHERING_TRANSFORMATIONS = "gathering_transformations"
    GATHERING_DESTINATION = "gathering_destination"
    GATHERING_SCHEDULE = "gathering_schedule"
    CONFIRMING = "confirming"
    DEPLOYING = "deploying"
    COMPLETED = "completed"


# =============================================================================
# SOURCE CONFIGURATION
# =============================================================================

class SourceConfig(BaseModel):
    """Source configuration for data ingestion."""
    storage_account: Optional[str] = Field(None, description="Azure storage account name")
    container: Optional[str] = Field(None, description="Container name")
    folder_path: Optional[str] = Field(None, description="Folder path within container")
    file_format: Optional[FileFormat] = Field(None, description="File format")
    file_pattern: Optional[str] = Field(default="*", description="File pattern (e.g., *.csv)")

    class Config:
        use_enum_values = True


# =============================================================================
# PII/PHI CONFIGURATION
# =============================================================================

class PIIConfig(BaseModel):
    """PII/PHI detection and masking configuration."""
    enabled: bool = Field(default=False, description="Whether PII detection is enabled")
    masking_type: Optional[MaskingType] = Field(None, description="Type of masking to apply")

    class Config:
        use_enum_values = True


# =============================================================================
# TRANSFORMATION CONFIGURATION
# =============================================================================

class TransformationStep(BaseModel):
    """A single transformation step."""
    type: TransformationType = Field(..., description="Type of transformation")
    condition: Optional[str] = Field(None, description="Condition for filter")
    columns: Optional[List[str]] = Field(None, description="Columns for select/rename")
    custom_code: Optional[str] = Field(None, description="Custom transformation code")

    class Config:
        use_enum_values = True


class TransformationConfig(BaseModel):
    """Transformation configuration."""
    enabled: bool = Field(default=False, description="Whether transformations are needed")
    steps: List[TransformationStep] = Field(default_factory=list, description="List of transformation steps")


# =============================================================================
# DESTINATION CONFIGURATION
# =============================================================================

class DestinationConfig(BaseModel):
    """Destination configuration."""
    target: DestinationType = Field(default=DestinationType.TABLES, description="Target type")
    table_name: Optional[str] = Field(None, description="Target table name")
    write_mode: str = Field(default="overwrite", description="Write mode: overwrite, append")

    class Config:
        use_enum_values = True


# =============================================================================
# SCHEDULE CONFIGURATION
# =============================================================================

class ScheduleConfig(BaseModel):
    """Schedule configuration."""
    enabled: bool = Field(default=True, description="Whether scheduling is enabled")
    frequency: str = Field(default="daily", description="Frequency: hourly, daily, weekly")
    time: Optional[str] = Field(None, description="Time in HH:MM format")
    timezone: str = Field(default="UTC", description="Timezone")


# =============================================================================
# COMPLETE PIPELINE CONFIGURATION
# =============================================================================

class PipelineConfig(BaseModel):
    """Complete pipeline configuration."""
    # Workspace context (from UI selection)
    workspace_id: Optional[str] = Field(None, description="Selected workspace ID")
    workspace_name: Optional[str] = Field(None, description="Selected workspace name")

    # Pipeline metadata
    pipeline_name: Optional[str] = Field(None, description="Generated pipeline name")
    pipeline_description: Optional[str] = Field(None, description="Pipeline description")

    # Configurations
    source: SourceConfig = Field(default_factory=SourceConfig)
    pii: PIIConfig = Field(default_factory=PIIConfig)
    transformations: TransformationConfig = Field(default_factory=TransformationConfig)
    destination: DestinationConfig = Field(default_factory=DestinationConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)

    # Resource IDs (resolved during processing)
    connection_id: Optional[str] = Field(None, description="Resolved connection ID")
    lakehouse_id: Optional[str] = Field(None, description="Resolved lakehouse ID")
    environment_id: Optional[str] = Field(None, description="Presidio environment ID")
    notebook_id: Optional[str] = Field(None, description="Generated notebook ID")


# =============================================================================
# CONVERSATION MODELS
# =============================================================================

class ConversationMessage(BaseModel):
    """A single message in the conversation."""
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")


class ConversationContext(BaseModel):
    """Context for the ongoing conversation."""
    session_id: str = Field(..., description="Unique session ID")
    workspace_id: str = Field(..., description="Selected workspace ID")
    workspace_name: str = Field(..., description="Selected workspace name")
    state: ConversationState = Field(default=ConversationState.INITIAL)
    messages: List[ConversationMessage] = Field(default_factory=list)
    config: PipelineConfig = Field(default_factory=PipelineConfig)

    # Tracking what's been collected
    collected_fields: List[str] = Field(default_factory=list)
    pending_questions: List[str] = Field(default_factory=list)


# =============================================================================
# USE CASE ANALYSIS
# =============================================================================

class IdentifiedActivity(BaseModel):
    """An identified activity for the pipeline."""
    type: str = Field(..., description="Activity type")
    reason: str = Field(..., description="Why this activity is needed")
    order: int = Field(..., description="Order in pipeline")


class UseCaseAnalysis(BaseModel):
    """Result of use case analysis."""
    use_case_type: str = Field(..., description="Type of use case identified")
    description: str = Field(..., description="Description of what user wants")
    activities: List[IdentifiedActivity] = Field(default_factory=list)
    needs_pii_detection: bool = Field(default=False)
    needs_transformation: bool = Field(default=False)
    needs_scheduling: bool = Field(default=True)


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================

class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    session_id: str = Field(..., description="Session ID")
    workspace_id: str = Field(..., description="Workspace ID")
    workspace_name: str = Field(..., description="Workspace name")
    message: str = Field(..., description="User message")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="AI response message")
    state: ConversationState = Field(..., description="Current conversation state")
    config: Optional[PipelineConfig] = Field(None, description="Current pipeline config")
    options: Optional[List[str]] = Field(None, description="Options for user to choose")
    is_complete: bool = Field(default=False, description="Whether pipeline is ready to deploy")


class DeployRequest(BaseModel):
    """Request to deploy the pipeline."""
    session_id: str = Field(..., description="Session ID")
    config: PipelineConfig = Field(..., description="Pipeline configuration")


class DeployResponse(BaseModel):
    """Response from deploy endpoint."""
    success: bool = Field(..., description="Whether deployment was successful")
    pipeline_id: Optional[str] = Field(None, description="Created pipeline ID")
    pipeline_name: Optional[str] = Field(None, description="Created pipeline name")
    notebook_id: Optional[str] = Field(None, description="Created notebook ID")
    message: str = Field(..., description="Status message")
    fabric_url: Optional[str] = Field(None, description="URL to view in Fabric portal")
