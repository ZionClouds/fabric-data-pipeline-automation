"""
All Remaining Service Models for Microsoft Fabric SDK

Contains models for all remaining Fabric services:
- admin, anomalydetector, apacheairflowjob, dashboard, datamart
- digitaltwinbuilder, digitaltwinbuilderflow, environment, eventhouse
- eventstream, graphmodel, graphqlapi, graphqueryset, kqldashboard
- kqldatabase, kqlqueryset, maps, mirroredazuredatabrickscatalog
- mirroreddatabase, mirroredwarehouse, mlexperiment, mlmodel
- mounteddatafactory, paginatedreport, reflex, report, semanticmodel
- spark, sparkjobdefinition, sqldatabase, sqlendpoint, userdatafunction
- variablelibrary, warehousesnapshot

Converted from: knowledge/fabric/*/models.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, Definition, Principal


# =============================================================================
# COMMON BASE MODELS
# =============================================================================

class BaseItemRequest(BaseModel):
    """Base request for creating items."""
    display_name: str = Field(..., alias="displayName")
    description: Optional[str] = Field(None)
    folder_id: Optional[str] = Field(None, alias="folderId")

    class Config:
        populate_by_name = True


class BaseItem(BaseModel):
    """Base item model."""
    id: Optional[str] = Field(None)
    type: Optional[ItemType] = Field(None)
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)

    class Config:
        populate_by_name = True


class BaseItemList(BaseModel):
    """Base list of items."""
    value: List[BaseItem] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class BaseUpdateRequest(BaseModel):
    """Base update request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


# =============================================================================
# EVENTSTREAM MODELS
# =============================================================================

class EventstreamItemType(str, Enum):
    EVENTSTREAM = "Eventstream"


class CreateEventstreamRequest(BaseItemRequest):
    """Create eventstream request."""
    definition: Optional[Definition] = Field(None)


class Eventstream(BaseItem):
    """An eventstream object."""
    pass


class Eventstreams(BaseModel):
    """A list of eventstreams."""
    value: List[Eventstream] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# SPARK MODELS
# =============================================================================

class SparkPoolType(str, Enum):
    """Spark pool type."""
    STARTER = "Starter"
    WORKSPACE = "Workspace"


class AutoScaleProperties(BaseModel):
    """Auto scale properties."""
    enabled: bool = Field(...)
    min_node_count: int = Field(..., alias="minNodeCount")
    max_node_count: int = Field(..., alias="maxNodeCount")

    class Config:
        populate_by_name = True


class DynamicExecutorAllocationProperties(BaseModel):
    """Dynamic executor allocation properties."""
    enabled: bool = Field(...)
    min_executors: int = Field(..., alias="minExecutors")
    max_executors: int = Field(..., alias="maxExecutors")

    class Config:
        populate_by_name = True


class SparkPoolProperties(BaseModel):
    """Spark pool properties."""
    name: Optional[str] = Field(None)
    type: Optional[SparkPoolType] = Field(None)
    node_family: Optional[str] = Field(None, alias="nodeFamily")
    node_size: Optional[str] = Field(None, alias="nodeSize")
    auto_scale: Optional[AutoScaleProperties] = Field(None, alias="autoScale")
    dynamic_executor_allocation: Optional[DynamicExecutorAllocationProperties] = Field(
        None, alias="dynamicExecutorAllocation"
    )

    class Config:
        populate_by_name = True


class SparkSettings(BaseModel):
    """Spark settings."""
    pool: Optional[SparkPoolProperties] = Field(None)
    driver_cores: Optional[int] = Field(None, alias="driverCores")
    driver_memory: Optional[str] = Field(None, alias="driverMemory")
    executor_cores: Optional[int] = Field(None, alias="executorCores")
    executor_memory: Optional[str] = Field(None, alias="executorMemory")
    runtime_version: Optional[str] = Field(None, alias="runtimeVersion")

    class Config:
        populate_by_name = True


# =============================================================================
# SPARKJOBDEFINITION MODELS
# =============================================================================

class CreateSparkJobDefinitionRequest(BaseItemRequest):
    """Create Spark job definition request."""
    definition: Optional[Definition] = Field(None)


class SparkJobDefinition(BaseItem):
    """A Spark job definition object."""
    pass


class SparkJobDefinitions(BaseModel):
    """A list of Spark job definitions."""
    value: List[SparkJobDefinition] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# ENVIRONMENT MODELS
# =============================================================================

class PublishState(str, Enum):
    """Publish state."""
    RUNNING = "Running"
    SUCCESS = "Success"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class CreateEnvironmentRequest(BaseItemRequest):
    """Create environment request."""
    pass


class EnvironmentPublishInfo(BaseModel):
    """Environment publish information."""
    state: Optional[PublishState] = Field(None)
    target_version: Optional[str] = Field(None, alias="targetVersion")
    start_time: Optional[datetime] = Field(None, alias="startTime")
    end_time: Optional[datetime] = Field(None, alias="endTime")
    component_publish_info: Optional[Dict[str, Any]] = Field(None, alias="componentPublishInfo")

    class Config:
        populate_by_name = True


class EnvironmentProperties(BaseModel):
    """Environment properties."""
    publish_details: Optional[EnvironmentPublishInfo] = Field(None, alias="publishDetails")

    class Config:
        populate_by_name = True


class Environment(BaseItem):
    """An environment object."""
    properties: Optional[EnvironmentProperties] = Field(None)


class Environments(BaseModel):
    """A list of environments."""
    value: List[Environment] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# EVENTHOUSE / KQL DATABASE MODELS
# =============================================================================

class CreateEventhouseRequest(BaseItemRequest):
    """Create eventhouse request."""
    pass


class EventhouseProperties(BaseModel):
    """Eventhouse properties."""
    query_service_uri: Optional[str] = Field(None, alias="queryServiceUri")
    ingestion_service_uri: Optional[str] = Field(None, alias="ingestionServiceUri")
    databases_item_ids: Optional[List[str]] = Field(None, alias="databasesItemIds")
    minimum_consumption_units: Optional[int] = Field(None, alias="minimumConsumptionUnits")

    class Config:
        populate_by_name = True


class Eventhouse(BaseItem):
    """An eventhouse object."""
    properties: Optional[EventhouseProperties] = Field(None)


class Eventhouses(BaseModel):
    """A list of eventhouses."""
    value: List[Eventhouse] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateKQLDatabaseRequest(BaseItemRequest):
    """Create KQL database request."""
    creation_payload: Optional[Dict[str, Any]] = Field(None, alias="creationPayload")


class KQLDatabaseProperties(BaseModel):
    """KQL database properties."""
    database_type: Optional[str] = Field(None, alias="databaseType")
    parent_eventhouse_item_id: Optional[str] = Field(None, alias="parentEventhouseItemId")
    query_service_uri: Optional[str] = Field(None, alias="queryServiceUri")
    ingestion_service_uri: Optional[str] = Field(None, alias="ingestionServiceUri")
    onelake_caching_period: Optional[str] = Field(None, alias="onelakeCachingPeriod")
    onelake_standard_storage_period: Optional[str] = Field(None, alias="onelakeStandardStoragePeriod")

    class Config:
        populate_by_name = True


class KQLDatabase(BaseItem):
    """A KQL database object."""
    properties: Optional[KQLDatabaseProperties] = Field(None)


class KQLDatabases(BaseModel):
    """A list of KQL databases."""
    value: List[KQLDatabase] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# ML EXPERIMENT / ML MODEL MODELS
# =============================================================================

class CreateMLExperimentRequest(BaseItemRequest):
    """Create ML experiment request."""
    pass


class MLExperiment(BaseItem):
    """An ML experiment object."""
    pass


class MLExperiments(BaseModel):
    """A list of ML experiments."""
    value: List[MLExperiment] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateMLModelRequest(BaseItemRequest):
    """Create ML model request."""
    definition: Optional[Definition] = Field(None)


class MLModel(BaseItem):
    """An ML model object."""
    pass


class MLModels(BaseModel):
    """A list of ML models."""
    value: List[MLModel] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# REPORT / SEMANTIC MODEL MODELS
# =============================================================================

class CreateReportRequest(BaseItemRequest):
    """Create report request."""
    definition: Optional[Definition] = Field(None)


class Report(BaseItem):
    """A report object."""
    pass


class Reports(BaseModel):
    """A list of reports."""
    value: List[Report] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateSemanticModelRequest(BaseItemRequest):
    """Create semantic model request."""
    definition: Optional[Definition] = Field(None)


class SemanticModel(BaseItem):
    """A semantic model object."""
    pass


class SemanticModels(BaseModel):
    """A list of semantic models."""
    value: List[SemanticModel] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# DASHBOARD / PAGINATED REPORT MODELS
# =============================================================================

class CreateDashboardRequest(BaseItemRequest):
    """Create dashboard request."""
    definition: Optional[Definition] = Field(None)


class Dashboard(BaseItem):
    """A dashboard object."""
    pass


class Dashboards(BaseModel):
    """A list of dashboards."""
    value: List[Dashboard] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreatePaginatedReportRequest(BaseItemRequest):
    """Create paginated report request."""
    definition: Optional[Definition] = Field(None)


class PaginatedReport(BaseItem):
    """A paginated report object."""
    pass


class PaginatedReports(BaseModel):
    """A list of paginated reports."""
    value: List[PaginatedReport] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# SQL DATABASE / SQL ENDPOINT MODELS
# =============================================================================

class CreateSQLDatabaseRequest(BaseItemRequest):
    """Create SQL database request."""
    creation_payload: Optional[Dict[str, Any]] = Field(None, alias="creationPayload")


class SQLDatabaseProperties(BaseModel):
    """SQL database properties."""
    connection_string: Optional[str] = Field(None, alias="connectionString")
    server_full_name: Optional[str] = Field(None, alias="serverFullName")
    database_name: Optional[str] = Field(None, alias="databaseName")

    class Config:
        populate_by_name = True


class SQLDatabase(BaseItem):
    """A SQL database object."""
    properties: Optional[SQLDatabaseProperties] = Field(None)


class SQLDatabases(BaseModel):
    """A list of SQL databases."""
    value: List[SQLDatabase] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class SQLEndpointProperties(BaseModel):
    """SQL endpoint properties."""
    connection_string: Optional[str] = Field(None, alias="connectionString")
    provisioning_status: Optional[str] = Field(None, alias="provisioningStatus")

    class Config:
        populate_by_name = True


class SQLEndpoint(BaseItem):
    """A SQL endpoint object."""
    properties: Optional[SQLEndpointProperties] = Field(None)


class SQLEndpoints(BaseModel):
    """A list of SQL endpoints."""
    value: List[SQLEndpoint] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# DATAMART MODELS
# =============================================================================

class CreateDatamartRequest(BaseItemRequest):
    """Create datamart request."""
    definition: Optional[Definition] = Field(None)


class Datamart(BaseItem):
    """A datamart object."""
    pass


class Datamarts(BaseModel):
    """A list of datamarts."""
    value: List[Datamart] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# MIRRORED DATABASE / WAREHOUSE MODELS
# =============================================================================

class CreateMirroredDatabaseRequest(BaseItemRequest):
    """Create mirrored database request."""
    definition: Optional[Definition] = Field(None)


class MirroredDatabaseProperties(BaseModel):
    """Mirrored database properties."""
    onelake_tables_path: Optional[str] = Field(None, alias="oneLakeTablesPath")
    sql_endpoint_properties: Optional[Dict[str, Any]] = Field(None, alias="sqlEndpointProperties")
    default_schema: Optional[str] = Field(None, alias="defaultSchema")

    class Config:
        populate_by_name = True


class MirroredDatabase(BaseItem):
    """A mirrored database object."""
    properties: Optional[MirroredDatabaseProperties] = Field(None)


class MirroredDatabases(BaseModel):
    """A list of mirrored databases."""
    value: List[MirroredDatabase] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateMirroredWarehouseRequest(BaseItemRequest):
    """Create mirrored warehouse request."""
    definition: Optional[Definition] = Field(None)


class MirroredWarehouse(BaseItem):
    """A mirrored warehouse object."""
    pass


class MirroredWarehouses(BaseModel):
    """A list of mirrored warehouses."""
    value: List[MirroredWarehouse] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# GRAPHQL API MODELS
# =============================================================================

class CreateGraphQLApiRequest(BaseItemRequest):
    """Create GraphQL API request."""
    definition: Optional[Definition] = Field(None)


class GraphQLApi(BaseItem):
    """A GraphQL API object."""
    pass


class GraphQLApis(BaseModel):
    """A list of GraphQL APIs."""
    value: List[GraphQLApi] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# VARIABLE LIBRARY MODELS
# =============================================================================

class CreateVariableLibraryRequest(BaseItemRequest):
    """Create variable library request."""
    definition: Optional[Definition] = Field(None)


class VariableLibrary(BaseItem):
    """A variable library object."""
    pass


class VariableLibraries(BaseModel):
    """A list of variable libraries."""
    value: List[VariableLibrary] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# APACHE AIRFLOW JOB MODELS
# =============================================================================

class CreateApacheAirflowJobRequest(BaseItemRequest):
    """Create Apache Airflow job request."""
    definition: Optional[Definition] = Field(None)


class ApacheAirflowJob(BaseItem):
    """An Apache Airflow job object."""
    pass


class ApacheAirflowJobs(BaseModel):
    """A list of Apache Airflow jobs."""
    value: List[ApacheAirflowJob] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# REFLEX / ANOMALY DETECTOR MODELS
# =============================================================================

class CreateReflexRequest(BaseItemRequest):
    """Create reflex request."""
    definition: Optional[Definition] = Field(None)


class Reflex(BaseItem):
    """A reflex (Data Activator) object."""
    pass


class Reflexes(BaseModel):
    """A list of reflexes."""
    value: List[Reflex] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateAnomalyDetectorRequest(BaseItemRequest):
    """Create anomaly detector request."""
    definition: Optional[Definition] = Field(None)


class AnomalyDetector(BaseItem):
    """An anomaly detector object."""
    pass


class AnomalyDetectors(BaseModel):
    """A list of anomaly detectors."""
    value: List[AnomalyDetector] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# GRAPH MODEL / KQL QUERYSET / KQL DASHBOARD MODELS
# =============================================================================

class CreateGraphModelRequest(BaseItemRequest):
    """Create graph model request."""
    definition: Optional[Definition] = Field(None)


class GraphModel(BaseItem):
    """A graph model object."""
    pass


class GraphModels(BaseModel):
    """A list of graph models."""
    value: List[GraphModel] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateKQLQuerysetRequest(BaseItemRequest):
    """Create KQL queryset request."""
    definition: Optional[Definition] = Field(None)


class KQLQueryset(BaseItem):
    """A KQL queryset object."""
    pass


class KQLQuerysets(BaseModel):
    """A list of KQL querysets."""
    value: List[KQLQueryset] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class CreateKQLDashboardRequest(BaseItemRequest):
    """Create KQL dashboard request."""
    definition: Optional[Definition] = Field(None)


class KQLDashboard(BaseItem):
    """A KQL dashboard object."""
    pass


class KQLDashboards(BaseModel):
    """A list of KQL dashboards."""
    value: List[KQLDashboard] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# ADMIN MODELS
# =============================================================================

class TenantSettings(BaseModel):
    """Tenant settings."""
    settings_group: Optional[str] = Field(None, alias="settingsGroup")
    setting_name: Optional[str] = Field(None, alias="settingName")
    title: Optional[str] = Field(None)
    enabled: Optional[bool] = Field(None)
    can_specify_security_groups: Optional[bool] = Field(None, alias="canSpecifySecurityGroups")
    tenant_setting_group: Optional[str] = Field(None, alias="tenantSettingGroup")
    properties: Optional[Dict[str, Any]] = Field(None)

    class Config:
        populate_by_name = True


class TenantSettingsList(BaseModel):
    """A list of tenant settings."""
    value: List[TenantSettings] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# WAREHOUSE SNAPSHOT MODELS
# =============================================================================

class CreateWarehouseSnapshotRequest(BaseModel):
    """Create warehouse snapshot request."""
    display_name: str = Field(..., alias="displayName")
    description: Optional[str] = Field(None)
    source_warehouse_item_id: str = Field(..., alias="sourceWarehouseItemId")
    snapshot_date_time: datetime = Field(..., alias="snapshotDateTime")

    class Config:
        populate_by_name = True


class WarehouseSnapshotProperties(BaseModel):
    """Warehouse snapshot properties."""
    connection_string: Optional[str] = Field(None, alias="connectionString")
    source_warehouse_item_id: Optional[str] = Field(None, alias="sourceWarehouseItemId")
    snapshot_date_time: Optional[datetime] = Field(None, alias="snapshotDateTime")

    class Config:
        populate_by_name = True


class WarehouseSnapshot(BaseItem):
    """A warehouse snapshot object."""
    properties: Optional[WarehouseSnapshotProperties] = Field(None)


class WarehouseSnapshots(BaseModel):
    """A list of warehouse snapshots."""
    value: List[WarehouseSnapshot] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True
