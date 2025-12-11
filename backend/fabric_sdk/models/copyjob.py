"""
CopyJob Models for Microsoft Fabric SDK

Contains models for CopyJob operations including:
- Create/Update/Delete copy jobs
- Copy job definitions
- Source and sink configurations

Converted from: knowledge/fabric/copyjob/models.go and constants.go
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, PayloadType, Definition, DefinitionPart


# =============================================================================
# ENUMS
# =============================================================================

class CopyJobItemType(str, Enum):
    """CopyJob item type."""
    COPY_JOB = "CopyJob"


class JobMode(str, Enum):
    """Copy job mode."""
    BATCH = "Batch"
    INCREMENTAL = "Incremental"


class TableActionType(str, Enum):
    """Table action for sink."""
    APPEND = "Append"
    OVERWRITE = "Overwrite"


class DataSourceType(str, Enum):
    """Data source type for copy job."""
    AZURE_BLOB_STORAGE = "AzureBlobStorage"
    AZURE_DATA_LAKE_STORAGE = "AzureDataLakeStorage"
    LAKEHOUSE = "Lakehouse"
    WAREHOUSE = "Warehouse"
    AMAZON_S3 = "AmazonS3"
    GOOGLE_CLOUD_STORAGE = "GoogleCloudStorage"
    HTTP = "Http"
    SHAREPOINT = "SharePoint"
    SQL_SERVER = "SqlServer"
    AZURE_SQL = "AzureSql"
    ORACLE = "Oracle"
    MYSQL = "MySql"
    POSTGRESQL = "PostgreSql"
    SNOWFLAKE = "Snowflake"


class FormatType(str, Enum):
    """Data format type."""
    DELIMITED_TEXT = "DelimitedText"
    PARQUET = "Parquet"
    JSON = "Json"
    AVRO = "Avro"
    ORC = "Orc"
    BINARY = "Binary"
    EXCEL = "Excel"
    XML = "Xml"


# =============================================================================
# COPYJOB MODELS
# =============================================================================

class CreateCopyJobRequest(BaseModel):
    """Create CopyJob request payload."""
    display_name: str = Field(..., alias="displayName", description="The CopyJob display name")
    description: Optional[str] = Field(None, description="The CopyJob description. Max 256 characters.")
    definition: Optional[Definition] = Field(None, description="The CopyJob public definition")
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class CopyJob(BaseModel):
    """A CopyJob object."""
    id: Optional[str] = Field(None, description="The item ID")
    type: Optional[ItemType] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)

    class Config:
        populate_by_name = True


class CopyJobs(BaseModel):
    """A list of CopyJobs."""
    value: List[CopyJob] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateCopyJobRequest(BaseModel):
    """Update CopyJob request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class UpdateCopyJobDefinitionRequest(BaseModel):
    """Update CopyJob definition request."""
    definition: Definition = Field(...)

    class Config:
        populate_by_name = True


class CopyJobDefinitionResponse(BaseModel):
    """CopyJob definition response."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


# =============================================================================
# COPYJOB DEFINITION CONTENT MODELS
# =============================================================================

class FormatOptions(BaseModel):
    """Format configuration for copy job data."""
    type: FormatType = Field(..., description="Format type")
    first_row_as_header: Optional[bool] = Field(None, alias="firstRowAsHeader")
    column_delimiter: Optional[str] = Field(None, alias="columnDelimiter")
    row_delimiter: Optional[str] = Field(None, alias="rowDelimiter")
    encoding: Optional[str] = Field(None)
    quote_char: Optional[str] = Field(None, alias="quoteChar")
    escape_char: Optional[str] = Field(None, alias="escapeChar")
    null_value: Optional[str] = Field(None, alias="nullValue")
    compression_codec: Optional[str] = Field(None, alias="compressionCodec")

    class Config:
        populate_by_name = True


class CopyJobSource(BaseModel):
    """Source configuration for copy job."""
    name: str = Field(default="Source", description="Source name")
    connection_id: str = Field(..., alias="connectionId", description="Connection ID (GUID)")
    data_source_type: DataSourceType = Field(..., alias="dataSourceType")
    container: Optional[str] = Field(None, description="Container/bucket name")
    folder_path: Optional[str] = Field(None, alias="folderPath")
    file_name: Optional[str] = Field(None, alias="fileName")
    wildcard_file_name: Optional[str] = Field(None, alias="wildcardFileName", description="File pattern (e.g., *.csv)")
    recursive: Optional[bool] = Field(None)
    format: Optional[FormatOptions] = Field(None)
    # For database sources
    schema_name: Optional[str] = Field(None, alias="schemaName")
    table_name: Optional[str] = Field(None, alias="tableName")
    query: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CopyJobSink(BaseModel):
    """Sink configuration for copy job."""
    name: str = Field(default="Sink", description="Sink name")
    data_source_type: DataSourceType = Field(..., alias="dataSourceType")
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    lakehouse_id: Optional[str] = Field(None, alias="lakehouseId")
    warehouse_id: Optional[str] = Field(None, alias="warehouseId")
    table_name: Optional[str] = Field(None, alias="tableName")
    table_action: Optional[TableActionType] = Field(None, alias="tableAction")
    folder_path: Optional[str] = Field(None, alias="folderPath")
    file_name: Optional[str] = Field(None, alias="fileName")
    format: Optional[FormatOptions] = Field(None)
    # Connection-based sink
    connection_id: Optional[str] = Field(None, alias="connectionId")
    container: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class CopyJobMapping(BaseModel):
    """Mapping configuration for copy job."""
    source: str = Field(default="Source")
    sink: str = Field(default="Sink")
    column_mappings: Optional[List[Dict[str, str]]] = Field(None, alias="columnMappings")

    class Config:
        populate_by_name = True


class CopyJobProperties(BaseModel):
    """Properties of a copy job definition."""
    job_mode: JobMode = Field(default=JobMode.BATCH, alias="jobMode")
    sources: List[CopyJobSource] = Field(default_factory=list)
    sinks: List[CopyJobSink] = Field(default_factory=list)
    mappings: List[CopyJobMapping] = Field(default_factory=list)
    settings: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class CopyJobDefinitionContent(BaseModel):
    """Complete CopyJob definition content (JSON structure)."""
    properties: CopyJobProperties = Field(...)

    class Config:
        populate_by_name = True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_blob_to_lakehouse_copy_job(
    connection_id: str,
    container: str,
    file_pattern: str,
    workspace_id: str,
    lakehouse_id: str,
    table_name: str,
    table_action: TableActionType = TableActionType.APPEND
) -> CopyJobDefinitionContent:
    """Create a copy job definition from Azure Blob Storage to Lakehouse."""
    return CopyJobDefinitionContent(
        properties=CopyJobProperties(
            job_mode=JobMode.BATCH,
            sources=[
                CopyJobSource(
                    name="Source",
                    connection_id=connection_id,
                    data_source_type=DataSourceType.AZURE_BLOB_STORAGE,
                    container=container,
                    wildcard_file_name=file_pattern,
                    recursive=True,
                    format=FormatOptions(
                        type=FormatType.DELIMITED_TEXT,
                        first_row_as_header=True,
                        column_delimiter=","
                    )
                )
            ],
            sinks=[
                CopyJobSink(
                    name="Sink",
                    data_source_type=DataSourceType.LAKEHOUSE,
                    workspace_id=workspace_id,
                    lakehouse_id=lakehouse_id,
                    table_name=table_name,
                    table_action=table_action
                )
            ],
            mappings=[
                CopyJobMapping(source="Source", sink="Sink")
            ]
        )
    )


def create_adls_to_lakehouse_copy_job(
    connection_id: str,
    container: str,
    folder_path: str,
    file_pattern: str,
    workspace_id: str,
    lakehouse_id: str,
    table_name: str,
    table_action: TableActionType = TableActionType.APPEND
) -> CopyJobDefinitionContent:
    """Create a copy job definition from ADLS Gen2 to Lakehouse."""
    return CopyJobDefinitionContent(
        properties=CopyJobProperties(
            job_mode=JobMode.BATCH,
            sources=[
                CopyJobSource(
                    name="Source",
                    connection_id=connection_id,
                    data_source_type=DataSourceType.AZURE_DATA_LAKE_STORAGE,
                    container=container,
                    folder_path=folder_path,
                    wildcard_file_name=file_pattern,
                    recursive=True,
                    format=FormatOptions(
                        type=FormatType.DELIMITED_TEXT,
                        first_row_as_header=True,
                        column_delimiter=","
                    )
                )
            ],
            sinks=[
                CopyJobSink(
                    name="Sink",
                    data_source_type=DataSourceType.LAKEHOUSE,
                    workspace_id=workspace_id,
                    lakehouse_id=lakehouse_id,
                    table_name=table_name,
                    table_action=table_action
                )
            ],
            mappings=[
                CopyJobMapping(source="Source", sink="Sink")
            ]
        )
    )


def create_s3_to_lakehouse_copy_job(
    connection_id: str,
    bucket: str,
    prefix: str,
    file_pattern: str,
    workspace_id: str,
    lakehouse_id: str,
    table_name: str,
    table_action: TableActionType = TableActionType.APPEND
) -> CopyJobDefinitionContent:
    """Create a copy job definition from Amazon S3 to Lakehouse."""
    return CopyJobDefinitionContent(
        properties=CopyJobProperties(
            job_mode=JobMode.BATCH,
            sources=[
                CopyJobSource(
                    name="Source",
                    connection_id=connection_id,
                    data_source_type=DataSourceType.AMAZON_S3,
                    container=bucket,
                    folder_path=prefix,
                    wildcard_file_name=file_pattern,
                    recursive=True,
                    format=FormatOptions(
                        type=FormatType.DELIMITED_TEXT,
                        first_row_as_header=True,
                        column_delimiter=","
                    )
                )
            ],
            sinks=[
                CopyJobSink(
                    name="Sink",
                    data_source_type=DataSourceType.LAKEHOUSE,
                    workspace_id=workspace_id,
                    lakehouse_id=lakehouse_id,
                    table_name=table_name,
                    table_action=table_action
                )
            ],
            mappings=[
                CopyJobMapping(source="Source", sink="Sink")
            ]
        )
    )
