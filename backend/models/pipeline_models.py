from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class SourceType(str, Enum):
    AZURE_SQL = "azure_sql"
    BLOB_STORAGE = "blob_storage"
    DB2 = "db2"
    SQL_SERVER = "sql_server"
    REST_API = "rest_api"

class PipelineStatus(str, Enum):
    DRAFT = "draft"
    DEPLOYED = "deployed"
    FAILED = "failed"
    RUNNING = "running"

class ExecutionStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MedallionLayer(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"

class TransformationType(str, Enum):
    DEDUPLICATION = "deduplication"
    TYPE_CONVERSION = "type_conversion"
    FILTERING = "filtering"
    JOIN = "join"
    AGGREGATION = "aggregation"
    WINDOW_FUNCTION = "window_function"

# Request Models
class SourceConnectionRequest(BaseModel):
    workspace_id: str
    source_type: SourceType
    host: str
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None
    additional_config: Optional[Dict[str, Any]] = None

class ValidateConnectionRequest(BaseModel):
    source_type: SourceType
    host: str
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    workspace_id: str
    pipeline_id: Optional[int] = None
    messages: List[ChatMessage]
    context: Optional[Dict[str, Any]] = None
    lakehouse_name: Optional[str] = None  # Selected lakehouse from dropdown
    warehouse_name: Optional[str] = None  # Selected warehouse from dropdown

class TransformationRequest(BaseModel):
    transformation_type: TransformationType
    description: str
    source_table: str
    target_table: str
    layer: MedallionLayer
    columns: Optional[List[str]] = None
    logic: Optional[str] = None  # SQL or Python code

class PipelineGenerateRequest(BaseModel):
    workspace_id: str
    pipeline_name: str
    source_type: SourceType
    source_config: Dict[str, Any]
    tables: List[str]
    transformations: List[TransformationRequest]
    use_medallion: bool = True
    schedule: str = "manual"
    created_by: str
    lakehouse_name: Optional[str] = None  # Selected lakehouse from dropdown
    warehouse_name: Optional[str] = None  # Selected warehouse from dropdown

class PipelineDeployRequest(BaseModel):
    pipeline_id: int
    workspace_id: str

# Response Models
class ConnectionValidationResponse(BaseModel):
    success: bool
    message: str
    tables: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class SchemaInfo(BaseModel):
    table_name: str
    columns: List[Dict[str, str]]  # [{"name": "col1", "type": "int"}, ...]
    row_count: Optional[int] = None

class ChatResponse(BaseModel):
    role: str
    content: str
    suggestions: Optional[List[str]] = None
    pipeline_preview: Optional[Dict[str, Any]] = None
    shortcut_info: Optional[Dict[str, Any]] = None  # Info about created shortcuts
    needs_confirmation: Optional[bool] = None  # Flag if waiting for user confirmation
    confirmation_action: Optional[str] = None  # What action needs confirmation (e.g., "create_shortcut")

class NotebookCode(BaseModel):
    notebook_name: str
    layer: MedallionLayer
    code: str
    description: str

class PipelineActivity(BaseModel):
    name: str
    type: str  # 'Copy', 'Notebook', 'ForEach', 'Lookup'
    config: Dict[str, Any]
    depends_on: Optional[List[str]] = None

class PipelineGenerateResponse(BaseModel):
    pipeline_id: int
    pipeline_name: str
    activities: List[PipelineActivity]
    notebooks: List[NotebookCode]
    fabric_pipeline_json: Dict[str, Any]
    reasoning: str

class PipelineDeployResponse(BaseModel):
    success: bool
    pipeline_id: int
    fabric_pipeline_id: Optional[str] = None
    message: str
    deployed_notebooks: Optional[List[str]] = None
    error: Optional[str] = None

class PipelineConfigResponse(BaseModel):
    id: int
    workspace_id: str
    pipeline_name: str
    pipeline_id: Optional[str] = None
    source_type: SourceType
    status: PipelineStatus
    medallion_enabled: bool
    bronze_table: Optional[str] = None
    silver_table: Optional[str] = None
    gold_table: Optional[str] = None
    schedule: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime] = None

class PipelineExecutionResponse(BaseModel):
    id: int
    pipeline_config_id: int
    execution_id: Optional[str] = None
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    rows_processed: Optional[int] = None
    duration_seconds: Optional[int] = None
    triggered_by: str

class WorkspaceInfo(BaseModel):
    id: str
    name: str
    lakehouse_id: Optional[str] = None
    lakehouse_name: Optional[str] = None
    capacity_id: Optional[str] = None

# Linked Service Models
class AuthenticationType(str, Enum):
    ACCOUNT_KEY = "AccountKey"
    SAS_TOKEN = "SasToken"
    MANAGED_IDENTITY = "ManagedIdentity"
    SQL_AUTH = "SqlAuth"
    SERVICE_PRINCIPAL = "ServicePrincipal"
    ANONYMOUS = "Anonymous"

class LinkedServiceRequest(BaseModel):
    workspace_id: str
    linked_service_name: str
    source_type: str  # blob, adls, azuresql, sqlserver, rest
    auth_type: AuthenticationType
    connection_config: Dict[str, Any]  # Varies by source type

class BlobStorageConfig(BaseModel):
    account_name: str
    auth_type: AuthenticationType = AuthenticationType.ACCOUNT_KEY
    account_key: Optional[str] = None
    sas_uri: Optional[str] = None

class ADLSConfig(BaseModel):
    account_name: str
    auth_type: AuthenticationType = AuthenticationType.ACCOUNT_KEY
    account_key: Optional[str] = None

class AzureSQLConfig(BaseModel):
    server: str
    database: str
    username: str
    password: str

class SQLServerConfig(BaseModel):
    server: str
    database: str
    username: str
    password: str

class RESTAPIConfig(BaseModel):
    base_url: str
    auth_type: AuthenticationType = AuthenticationType.ANONYMOUS
    headers: Optional[Dict[str, str]] = None

class LinkedServiceResponse(BaseModel):
    success: bool
    linked_service_id: Optional[str] = None
    linked_service_name: str
    source_type: str
    error: Optional[str] = None

# Automated Pipeline Generation Models (with Connection Creation)
class ConnectionConfig(BaseModel):
    """Configuration for creating a connection"""
    connection_name: str
    connection_type: str  # "blob", "adls", "sharepoint", "azuresql", etc.
    auth_type: str  # "ServicePrincipal", "AccountKey", "SasToken", "WorkspaceIdentity"
    properties: Dict[str, Any]  # Connection-specific properties

class PipelineArchitecture(str, Enum):
    """Pipeline architecture type"""
    MEDALLION = "medallion"  # Bronze -> Silver -> Gold
    SIMPLE_COPY = "simple_copy"  # Direct copy from source to destination

class LayerConfig(BaseModel):
    """Configuration for a medallion layer"""
    layer_name: str  # "bronze", "silver", "gold"
    storage_type: str  # "blob", "onelake_tables", "onelake_files"
    transformations: Optional[List[str]] = None  # List of transformation descriptions
    component_type: Optional[str] = None  # "copy_activity", "dataflow_gen2", "notebook"

class AutomatedPipelineGenerateRequest(BaseModel):
    """Request for automated pipeline generation with connection creation"""
    workspace_id: str
    pipeline_name: str
    architecture: PipelineArchitecture

    # Source connection details
    source_connection: ConnectionConfig

    # Destination connection details (for Bronze/Silver if using Blob)
    bronze_connection: Optional[ConnectionConfig] = None
    silver_connection: Optional[ConnectionConfig] = None

    # Gold layer configuration (OneLake)
    gold_lakehouse_id: Optional[str] = None
    gold_table_name: Optional[str] = None

    # Layer configurations
    layers: Optional[List[LayerConfig]] = None

    # Schedule
    schedule: Optional[str] = "manual"

    # User info
    created_by: str

class AutomatedPipelineGenerateResponse(BaseModel):
    """Response for automated pipeline generation"""
    success: bool
    pipeline_id: Optional[str] = None
    pipeline_name: str
    workspace_id: str

    # Created resources
    connections_created: List[Dict[str, str]]  # [{"name": "...", "id": "...", "type": "..."}]
    activities_created: List[str]  # List of activity names
    notebooks_created: Optional[List[str]] = None  # List of notebook names if any

    # Details
    architecture: str
    layers: Optional[List[str]] = None  # ["bronze", "silver", "gold"]

    # Error handling
    error: Optional[str] = None
    manual_instructions: Optional[str] = None  # Fallback manual instructions if automation fails

class FileProcessingPipelineRequest(BaseModel):
    """Request for generating file processing pipeline with incremental loading"""
    workspace_id: str
    lakehouse_id: str
    pipeline_name: str
    source_container: str  # "bronze" or "silver"
    bronze_shortcut_name: Optional[str] = "azure_blob_bronze"
    deploy_immediately: Optional[bool] = False

class FileProcessingPipelineResponse(BaseModel):
    """Response for file processing pipeline generation"""
    success: bool
    pipeline_name: str
    pipeline_id: Optional[str] = None
    lakehouse_name: Optional[str] = None
    sql_endpoint: Optional[str] = None
    activities_count: Optional[int] = None
    pipeline_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
