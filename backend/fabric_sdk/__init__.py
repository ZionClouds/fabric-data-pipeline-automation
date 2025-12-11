"""
Microsoft Fabric SDK for Python

A comprehensive Python SDK for Microsoft Fabric REST APIs, converted from the official Go SDK.
This SDK provides Pydantic models and async clients for all Fabric services.

Services included:
- admin: Admin APIs for tenant management
- anomalydetector: Anomaly detection service
- apacheairflowjob: Apache Airflow job management
- copyjob: Copy job operations
- core: Core APIs (connections, shortcuts, workspaces, items)
- dashboard: Dashboard management
- dataflow: Dataflow Gen2 operations
- datamart: Datamart management
- datapipeline: Data pipeline CRUD operations
- digitaltwinbuilder: Digital twin builder
- digitaltwinbuilderflow: Digital twin builder flow
- environment: Environment configuration
- eventhouse: Event house (KQL) operations
- eventstream: Event streaming
- graphmodel: Graph model service
- graphqlapi: GraphQL API management
- graphqueryset: Graph query set
- kqldashboard: KQL dashboard
- kqldatabase: KQL database operations
- kqlqueryset: KQL query set
- lakehouse: Lakehouse management
- maps: Maps service
- mirroredazuredatabrickscatalog: Mirrored Azure Databricks catalog
- mirroreddatabase: Mirrored database operations
- mirroredwarehouse: Mirrored warehouse
- mlexperiment: ML experiment management
- mlmodel: ML model operations
- mounteddatafactory: Mounted data factory
- notebook: Notebook operations
- paginatedreport: Paginated report management
- reflex: Reflex service
- report: Report management
- semanticmodel: Semantic model operations
- spark: Spark operations
- sparkjobdefinition: Spark job definition
- sqldatabase: SQL database management
- sqlendpoint: SQL endpoint operations
- userdatafunction: User data function
- variablelibrary: Variable library
- warehouse: Warehouse management
- warehousesnapshot: Warehouse snapshot

Usage:
    from fabric_sdk.models import core, datapipeline, lakehouse
    from fabric_sdk.clients import DataPipelineClient, LakehouseClient
    from fabric_sdk.activities import CopyActivity, ForEachActivity
"""

__version__ = "1.0.0"
__author__ = "Fabric Data Pipeline Automation"

# Import all models
from fabric_sdk.models import (
    core,
    datapipeline,
    lakehouse,
    notebook,
    copyjob,
    warehouse,
    dataflow,
    eventstream,
    spark,
)

# Import clients
from fabric_sdk.clients import (
    FabricBaseClient,
    DataPipelineClient,
    LakehouseClient,
    NotebookClient,
    CopyJobClient,
)

# Import activity builders
from fabric_sdk.activities import (
    CopyActivity,
    ForEachActivity,
    IfConditionActivity,
    SetVariableActivity,
    GetMetadataActivity,
    FilterActivity,
    ScriptActivity,
    NotebookActivity,
)

__all__ = [
    # Version
    "__version__",
    # Models
    "core",
    "datapipeline",
    "lakehouse",
    "notebook",
    "copyjob",
    "warehouse",
    "dataflow",
    "eventstream",
    "spark",
    # Clients
    "FabricBaseClient",
    "DataPipelineClient",
    "LakehouseClient",
    "NotebookClient",
    "CopyJobClient",
    # Activities
    "CopyActivity",
    "ForEachActivity",
    "IfConditionActivity",
    "SetVariableActivity",
    "GetMetadataActivity",
    "FilterActivity",
    "ScriptActivity",
    "NotebookActivity",
]
