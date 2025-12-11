"""
Eventstream Models for Microsoft Fabric SDK

Contains models for eventstream operations including:
- Sources (Kafka, Event Hub, IoT Hub, Custom, Sample Data, etc.)
- Destinations (Lakehouse, Eventhouse, Activator, Custom Endpoint)
- Operators (Filter, Aggregate, Expand, Join, GroupBy, etc.)
- Streaming data transformations

Converted from: knowledge/fabric/eventstream/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType


# =============================================================================
# ENUMS
# =============================================================================

class AggregationFunction(str, Enum):
    """The aggregation function."""
    AVERAGE = "Average"
    COUNT = "Count"
    MAXIMUM = "Maximum"
    MINIMUM = "Minimum"
    PERCENTILE_CONTINUOUS = "PercentileContinuous"
    PERCENTILE_DISCRETE = "PercentileDiscrete"
    STANDARD_DEVIATION = "StandardDeviation"
    STANDARD_DEVIATION_POPULATION = "StandardDeviationPopulation"
    SUM = "Sum"
    VARIANCE = "Variance"
    VARIANCE_POPULATION = "VariancePopulation"


class AmazonKinesisSourcePropertiesRegion(str, Enum):
    """The Amazon Kinesis region name."""
    AF_SOUTH_1 = "af-south-1"
    AP_EAST_1 = "ap-east-1"
    AP_NORTHEAST_1 = "ap-northeast-1"
    AP_NORTHEAST_2 = "ap-northeast-2"
    AP_NORTHEAST_3 = "ap-northeast-3"
    AP_SOUTH_1 = "ap-south-1"
    AP_SOUTH_2 = "ap-south-2"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_SOUTHEAST_2 = "ap-southeast-2"
    AP_SOUTHEAST_3 = "ap-southeast-3"
    AP_SOUTHEAST_4 = "ap-southeast-4"
    AP_SOUTHEAST_5 = "ap-southeast-5"
    CA_CENTRAL_1 = "ca-central-1"
    CA_WEST_1 = "ca-west-1"
    EU_CENTRAL_1 = "eu-central-1"
    EU_CENTRAL_2 = "eu-central-2"
    EU_NORTH_1 = "eu-north-1"
    EU_SOUTH_1 = "eu-south-1"
    EU_SOUTH_2 = "eu-south-2"
    EU_WEST_1 = "eu-west-1"
    EU_WEST_2 = "eu-west-2"
    EU_WEST_3 = "eu-west-3"
    IL_CENTRAL_1 = "il-central-1"
    ME_CENTRAL_1 = "me-central-1"
    ME_SOUTH_1 = "me-south-1"
    SA_EAST_1 = "sa-east-1"
    US_EAST_1 = "us-east-1"
    US_EAST_2 = "us-east-2"
    US_GOV_EAST_1 = "us-gov-east-1"
    US_GOV_WEST_1 = "us-gov-west-1"
    US_WEST_1 = "us-west-1"
    US_WEST_2 = "us-west-2"


class AmazonMSKKafkaSourcePropertiesSaslMechanism(str, Enum):
    """The SASL mechanism."""
    PLAIN = "PLAIN"
    SCRAM_SHA_256 = "SCRAM-SHA-256"
    SCRAM_SHA_512 = "SCRAM-SHA-512"


class AmazonMSKKafkaSourcePropertiesSecurityProtocol(str, Enum):
    """The security protocol."""
    PLAINTEXT = "PLAINTEXT"
    SASL_PLAINTEXT = "SASL_PLAINTEXT"
    SASL_SSL = "SASL_SSL"
    SSL = "SSL"


class ApacheKafkaSourcePropertiesSaslMechanism(str, Enum):
    """The SASL mechanism."""
    PLAIN = "PLAIN"
    SCRAM_SHA_256 = "SCRAM-SHA-256"
    SCRAM_SHA_512 = "SCRAM-SHA-512"


class ApacheKafkaSourcePropertiesSecurityProtocol(str, Enum):
    """The security protocol."""
    PLAINTEXT = "PLAINTEXT"
    SASL_PLAINTEXT = "SASL_PLAINTEXT"
    SASL_SSL = "SASL_SSL"
    SSL = "SSL"


class AzureBlobStorageEventsIncludedEventTypesItem(str, Enum):
    """Azure Blob Storage event types."""
    MICROSOFT_STORAGE_ASYNC_OPERATION_INITIATED = "Microsoft.Storage.AsyncOperationInitiated"
    MICROSOFT_STORAGE_BLOB_CREATED = "Microsoft.Storage.BlobCreated"
    MICROSOFT_STORAGE_BLOB_DELETED = "Microsoft.Storage.BlobDeleted"
    MICROSOFT_STORAGE_BLOB_INVENTORY_POLICY_COMPLETED = "Microsoft.Storage.BlobInventoryPolicyCompleted"
    MICROSOFT_STORAGE_BLOB_RENAMED = "Microsoft.Storage.BlobRenamed"
    MICROSOFT_STORAGE_BLOB_TIER_CHANGED = "Microsoft.Storage.BlobTierChanged"
    MICROSOFT_STORAGE_DIRECTORY_CREATED = "Microsoft.Storage.DirectoryCreated"
    MICROSOFT_STORAGE_DIRECTORY_DELETED = "Microsoft.Storage.DirectoryDeleted"
    MICROSOFT_STORAGE_DIRECTORY_RENAMED = "Microsoft.Storage.DirectoryRenamed"
    MICROSOFT_STORAGE_LIFECYCLE_POLICY_COMPLETED = "Microsoft.Storage.LifecyclePolicyCompleted"


class AzureCosmosDBCDCSourcePropertiesOffsetPolicy(str, Enum):
    """The offset policy."""
    EARLIEST = "Earliest"
    LATEST = "Latest"


class BaseKafkaSourcePropertiesAutoOffsetReset(str, Enum):
    """The auto offset reset property."""
    EARLIEST = "Earliest"
    LATEST = "Latest"
    NONE = "None"


class CSVSerializationPropertiesEncoding(str, Enum):
    """The encoding type."""
    UTF8 = "UTF8"


class CSVSerializationPropertiesFormat(str, Enum):
    """The format type."""
    WITH_HEADERS = "WithHeaders"
    WITHOUT_HEADERS = "WithoutHeaders"


class CompatibilityLevel(str, Enum):
    """Represents the compatibility level of the Eventstream topology."""
    ONE_0 = "1.0"


class DataSourceStartType(str, Enum):
    """Represents the start type of the data source."""
    CUSTOM_TIME = "CustomTime"
    NOW = "Now"
    WHEN_LAST_STOPPED = "WhenLastStopped"


class DataType(str, Enum):
    """Represents the data type."""
    ANY = "Any"
    ARRAY = "Array"
    BIG_INT = "BigInt"
    BIT = "Bit"
    DATE_TIME = "DateTime"
    FLOAT = "Float"
    NVARCHAR_MAX = "Nvarchar(max)"
    RECORD = "Record"


class DestinationType(str, Enum):
    """Represents the type of the destination."""
    ACTIVATOR = "Activator"
    CUSTOM_ENDPOINT = "CustomEndpoint"
    EVENTHOUSE = "Eventhouse"
    LAKEHOUSE = "Lakehouse"


class EventhouseDestinationPropertiesDataIngestionMode(str, Enum):
    """The data ingestion mode."""
    DIRECT_INGESTION = "DirectIngestion"
    PROCESSED_INGESTION = "ProcessedIngestion"


class FabricCapacityUtilizationEventsSourcePropertiesEventScope(str, Enum):
    """Fabric event scope."""
    CAPACITY = "Capacity"
    ITEM = "Item"
    SUB_ITEM = "SubItem"
    TENANT = "Tenant"
    WORKSPACE = "Workspace"


class FabricJobEventsSourcePropertiesEventScope(str, Enum):
    """Fabric job event scope."""
    CAPACITY = "Capacity"
    ITEM = "Item"
    SUB_ITEM = "SubItem"
    TENANT = "Tenant"
    WORKSPACE = "Workspace"


class FabricWorkspaceItemEventsSourcePropertiesEventScope(str, Enum):
    """Fabric workspace item event scope."""
    CAPACITY = "Capacity"
    ITEM = "Item"
    SUB_ITEM = "SubItem"
    TENANT = "Tenant"
    WORKSPACE = "Workspace"


class FilterConditionOperatorType(str, Enum):
    """The operator type."""
    CONTAINS = "Contains"
    DOES_NOT_CONTAIN = "DoesNotContain"
    DOES_NOT_END_WITH = "DoesNotEndWith"
    DOES_NOT_START_WITH = "DoesNotStartWith"
    ENDS_WITH = "EndsWith"
    EQUALS = "Equals"
    GREATER_THAN = "GreaterThan"
    GREATER_THAN_OR_EQUALS = "GreaterThanOrEquals"
    IS_EMPTY = "IsEmpty"
    IS_NOT_NULL = "IsNotNull"
    IS_NOT_NULL_OR_EMPTY = "IsNotNullOrEmpty"
    IS_NULL = "IsNull"
    LESS_THAN = "LessThan"
    LESS_THAN_OR_EQUALS = "LessThanOrEquals"
    NOT_EQUALS = "NotEquals"
    STARTS_WITH = "StartsWith"


class GroupByWindowType(str, Enum):
    """The type of the window."""
    HOPPING = "Hopping"
    SESSION = "Session"
    SLIDING = "Sliding"
    SNAPSHOT = "Snapshot"
    TUMBLING = "Tumbling"


class JSONSerializationPropertiesEncoding(str, Enum):
    """The encoding type."""
    UTF8 = "UTF8"


class JoinOperatorPropertiesJoinType(str, Enum):
    """The type of the join."""
    INNER = "Inner"
    LEFT_OUTER = "LeftOuter"


class NodeStatus(str, Enum):
    """The status of the node."""
    CREATED = "Created"
    CREATING = "Creating"
    DELETING = "Deleting"
    EXTERNAL = "External"
    FAILED = "Failed"
    PAUSED = "Paused"
    PAUSING = "Pausing"
    RESUMING = "Resuming"
    RUNNING = "Running"
    UNKNOWN = "Unknown"
    UPDATING = "Updating"
    WARNING = "Warning"


class OperatorCommonDurationUnit(str, Enum):
    """The unit of the duration."""
    DAY = "Day"
    DAY_OF_YEAR = "DayOfYear"
    HOUR = "Hour"
    MICROSECOND = "Microsecond"
    MILLISECOND = "Millisecond"
    MINUTE = "Minute"
    MONTH = "Month"
    QUARTER = "Quarter"
    SECOND = "Second"
    WEEK = "Week"
    WEEKDAY = "Weekday"
    YEAR = "Year"


class OperatorType(str, Enum):
    """The type of the operator."""
    AGGREGATE = "Aggregate"
    EXPAND = "Expand"
    FILTER = "Filter"
    GROUP_BY = "GroupBy"
    JOIN = "Join"
    MANAGE_FIELDS = "ManageFields"
    UNION = "Union"


class PayloadType(str, Enum):
    """The type of the definition part payload."""
    INLINE_BASE64 = "InlineBase64"


class SampleDataSourcePropertiesType(str, Enum):
    """The sample data type."""
    BICYCLES = "Bicycles"
    STOCK_MARKET = "StockMarket"
    YELLOW_TAXI = "YellowTaxi"


class SerializationType(str, Enum):
    """The serialization type."""
    AVRO = "Avro"
    CSV = "Csv"
    JSON = "Json"


class SourceType(str, Enum):
    """Represents the type of the source."""
    AMAZON_KINESIS = "AmazonKinesis"
    AMAZON_MSK_KAFKA = "AmazonMSKKafka"
    APACHE_KAFKA = "ApacheKafka"
    AZURE_BLOB_STORAGE_EVENTS = "AzureBlobStorageEvents"
    AZURE_COSMOS_DB_CDC = "AzureCosmosDBCDC"
    AZURE_EVENT_HUB = "AzureEventHub"
    AZURE_IOT_HUB = "AzureIoTHub"
    AZURE_SQL_DB_CDC = "AzureSQLDBCDC"
    AZURE_SQL_MI_DB_CDC = "AzureSQLMIDBCDC"
    CONFLUENT_CLOUD = "ConfluentCloud"
    CUSTOM_ENDPOINT = "CustomEndpoint"
    FABRIC_CAPACITY_UTILIZATION_EVENTS = "FabricCapacityUtilizationEvents"
    FABRIC_JOB_EVENTS = "FabricJobEvents"
    FABRIC_ONE_LAKE_EVENTS = "FabricOneLakeEvents"
    FABRIC_WORKSPACE_ITEM_EVENTS = "FabricWorkspaceItemEvents"
    GOOGLE_PUB_SUB = "GooglePubSub"
    MY_SQL_CDC = "MySQLCDC"
    POSTGRE_SQL_CDC = "PostgreSQLCDC"
    SQL_SERVER_ON_VM_DB_CDC = "SQLServerOnVMDBCDC"
    SAMPLE_DATA = "SampleData"


class StreamType(str, Enum):
    """Represents the type of the stream."""
    DEFAULT_STREAM = "DefaultStream"
    DERIVED_STREAM = "DerivedStream"


class Type(str, Enum):
    """The operation type."""
    CAST = "Cast"
    FUNCTION_CALL = "FunctionCall"
    RENAME = "Rename"


# =============================================================================
# MODELS
# =============================================================================

class DefinitionPart(BaseModel):
    """Eventstream definition part object."""
    path: str = Field(..., description="The eventstream part path")
    payload: str = Field(..., description="The eventstream part payload")
    payload_type: PayloadType = Field(..., alias="payloadType", description="The payload type")


class Definition(BaseModel):
    """Eventstream public definition object."""
    parts: List[DefinitionPart] = Field(..., description="A list of definition parts")
    format: Optional[str] = Field(None, description="The format of the item definition")


class DefinitionResponse(BaseModel):
    """Eventstream public definition response."""
    definition: Optional[Definition] = Field(None, description="Eventstream public definition object")


class CreateEventstreamRequest(BaseModel):
    """Create eventstream request payload."""
    display_name: str = Field(..., alias="displayName", description="The eventstream display name")
    definition: Optional[Definition] = Field(None, description="The eventstream public definition")
    description: Optional[str] = Field(None, description="The eventstream description. Maximum length is 256 characters")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")


class Properties(BaseModel):
    """The eventstream properties."""
    owner: Optional[str] = Field(None, description="The owner of the eventstream")


class Eventstream(BaseModel):
    """An eventstream object."""
    type: ItemType = Field(..., description="The item type")
    description: Optional[str] = Field(None, description="The item description")
    display_name: Optional[str] = Field(None, alias="displayName", description="The item display name")
    properties: Optional[Properties] = Field(None, description="The eventstream properties")
    folder_id: Optional[str] = Field(None, alias="folderId", description="The folder ID")
    id: Optional[str] = Field(None, description="The item ID")
    tags: Optional[List[ItemTag]] = Field(None, description="List of applied tags")
    workspace_id: Optional[str] = Field(None, alias="workspaceId", description="The workspace ID")


class Eventstreams(BaseModel):
    """A list of eventstreams."""
    value: List[Eventstream] = Field(..., description="A list of eventstreams")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="The token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="The URI of the next result set batch")


class UpdateEventstreamDefinitionRequest(BaseModel):
    """Update eventstream public definition request payload."""
    definition: Definition = Field(..., description="Eventstream public definition object")


class UpdateEventstreamRequest(BaseModel):
    """Update eventstream request."""
    description: Optional[str] = Field(None, description="The eventstream description. Maximum length is 256 characters")
    display_name: Optional[str] = Field(None, alias="displayName", description="The eventstream display name")


# Source Models
class SourceProperties(BaseModel):
    """Base properties for sources."""
    pass


class AmazonKinesisSourceProperties(SourceProperties):
    """Amazon Kinesis source properties."""
    access_key: str = Field(..., alias="accessKey", description="The access key")
    region: AmazonKinesisSourcePropertiesRegion = Field(..., description="The region")
    secret_key: str = Field(..., alias="secretKey", description="The secret key")
    stream_name: str = Field(..., alias="streamName", description="The stream name")


class AmazonMSKKafkaSourceProperties(SourceProperties):
    """Amazon MSK Kafka source properties."""
    bootstrap_servers: str = Field(..., alias="bootstrapServers", description="Bootstrap servers")
    consumer_group_id: str = Field(..., alias="consumerGroupId", description="Consumer group ID")
    password: str = Field(..., description="Password")
    sasl_mechanism: AmazonMSKKafkaSourcePropertiesSaslMechanism = Field(..., alias="saslMechanism", description="SASL mechanism")
    security_protocol: AmazonMSKKafkaSourcePropertiesSecurityProtocol = Field(..., alias="securityProtocol", description="Security protocol")
    topic_name: str = Field(..., alias="topicName", description="Topic name")
    username: str = Field(..., description="Username")
    auto_offset_reset: Optional[BaseKafkaSourcePropertiesAutoOffsetReset] = Field(None, alias="autoOffsetReset", description="Auto offset reset")


class ApacheKafkaSourceProperties(SourceProperties):
    """Apache Kafka source properties."""
    bootstrap_servers: str = Field(..., alias="bootstrapServers", description="Bootstrap servers")
    consumer_group_id: str = Field(..., alias="consumerGroupId", description="Consumer group ID")
    password: str = Field(..., description="Password")
    sasl_mechanism: ApacheKafkaSourcePropertiesSaslMechanism = Field(..., alias="saslMechanism", description="SASL mechanism")
    security_protocol: ApacheKafkaSourcePropertiesSecurityProtocol = Field(..., alias="securityProtocol", description="Security protocol")
    topic_name: str = Field(..., alias="topicName", description="Topic name")
    username: str = Field(..., description="Username")
    auto_offset_reset: Optional[BaseKafkaSourcePropertiesAutoOffsetReset] = Field(None, alias="autoOffsetReset", description="Auto offset reset")


class SampleDataSourceProperties(SourceProperties):
    """Sample data source properties."""
    type: SampleDataSourcePropertiesType = Field(..., description="The sample data type")


# Destination Models
class DestinationProperties(BaseModel):
    """Base properties for destinations."""
    pass


class LakehouseDestinationProperties(DestinationProperties):
    """Lakehouse destination properties."""
    lakehouse_id: str = Field(..., alias="lakehouseId", description="The lakehouse ID")
    workspace_id: str = Field(..., alias="workspaceId", description="The workspace ID")


class EventhouseDestinationProperties(DestinationProperties):
    """Eventhouse destination properties."""
    data_ingestion_mode: EventhouseDestinationPropertiesDataIngestionMode = Field(..., alias="dataIngestionMode", description="Data ingestion mode")
    eventhouse_id: str = Field(..., alias="eventhouseId", description="The eventhouse ID")
    kql_database_id: str = Field(..., alias="kqlDatabaseId", description="The KQL database ID")
    kql_table_name: str = Field(..., alias="kqlTableName", description="The KQL table name")
    workspace_id: str = Field(..., alias="workspaceId", description="The workspace ID")


class ActivatorDestinationProperties(DestinationProperties):
    """Activator destination properties."""
    activator_id: str = Field(..., alias="activatorId", description="The activator ID")
    workspace_id: str = Field(..., alias="workspaceId", description="The workspace ID")


class CustomEndpointDestinationProperties(DestinationProperties):
    """Custom endpoint destination properties."""
    endpoint_url: str = Field(..., alias="endpointUrl", description="The endpoint URL")


# Operator Models
class OperatorProperties(BaseModel):
    """Base properties for operators."""
    pass


class FilterCondition(BaseModel):
    """Filter condition."""
    field_name: str = Field(..., alias="fieldName", description="The field name")
    operator: FilterConditionOperatorType = Field(..., description="The operator")
    value: Optional[str] = Field(None, description="The value")


class FilterOperatorProperties(OperatorProperties):
    """Filter operator properties."""
    conditions: List[FilterCondition] = Field(..., description="List of filter conditions")
    logic: Optional[str] = Field(None, description="Logic for combining conditions (AND/OR)")


class AggregateColumn(BaseModel):
    """Aggregate column definition."""
    function: AggregationFunction = Field(..., description="The aggregation function")
    input_column_name: str = Field(..., alias="inputColumnName", description="Input column name")
    output_column_name: str = Field(..., alias="outputColumnName", description="Output column name")


class AggregateOperatorProperties(OperatorProperties):
    """Aggregate operator properties."""
    columns: List[AggregateColumn] = Field(..., description="List of aggregate columns")


class GroupByWindow(BaseModel):
    """Group by window configuration."""
    type: GroupByWindowType = Field(..., description="The window type")
    duration: Optional[int] = Field(None, description="Duration for the window")
    unit: Optional[OperatorCommonDurationUnit] = Field(None, description="Duration unit")


class GroupByOperatorProperties(OperatorProperties):
    """Group by operator properties."""
    group_by_columns: List[str] = Field(..., alias="groupByColumns", description="Columns to group by")
    window: Optional[GroupByWindow] = Field(None, description="Window configuration")


class JoinOperatorProperties(OperatorProperties):
    """Join operator properties."""
    join_type: JoinOperatorPropertiesJoinType = Field(..., alias="joinType", description="The join type")
    left_input: str = Field(..., alias="leftInput", description="Left input")
    right_input: str = Field(..., alias="rightInput", description="Right input")
    on_clause: str = Field(..., alias="onClause", description="Join condition")


# Stream Models
class Stream(BaseModel):
    """A stream in the eventstream."""
    id: str = Field(..., description="The stream ID")
    name: str = Field(..., description="The stream name")
    type: StreamType = Field(..., description="The stream type")


class Node(BaseModel):
    """A node in the eventstream topology."""
    id: str = Field(..., description="The node ID")
    name: str = Field(..., description="The node name")
    status: Optional[NodeStatus] = Field(None, description="The node status")
    type: Optional[str] = Field(None, description="The node type")


class Source(Node):
    """A source node."""
    source_type: SourceType = Field(..., alias="sourceType", description="The source type")
    properties: Optional[SourceProperties] = Field(None, description="Source properties")


class Destination(Node):
    """A destination node."""
    destination_type: DestinationType = Field(..., alias="destinationType", description="The destination type")
    properties: Optional[DestinationProperties] = Field(None, description="Destination properties")


class Operator(Node):
    """An operator node."""
    operator_type: OperatorType = Field(..., alias="operatorType", description="The operator type")
    properties: Optional[OperatorProperties] = Field(None, description="Operator properties")


class Topology(BaseModel):
    """The eventstream topology."""
    compatibility_level: CompatibilityLevel = Field(..., alias="compatibilityLevel", description="The compatibility level")
    nodes: Optional[List[Node]] = Field(None, description="List of nodes in the topology")
    streams: Optional[List[Stream]] = Field(None, description="List of streams")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AggregationFunction",
    "AmazonKinesisSourcePropertiesRegion",
    "AmazonMSKKafkaSourcePropertiesSaslMechanism",
    "AmazonMSKKafkaSourcePropertiesSecurityProtocol",
    "ApacheKafkaSourcePropertiesSaslMechanism",
    "ApacheKafkaSourcePropertiesSecurityProtocol",
    "AzureBlobStorageEventsIncludedEventTypesItem",
    "AzureCosmosDBCDCSourcePropertiesOffsetPolicy",
    "BaseKafkaSourcePropertiesAutoOffsetReset",
    "CSVSerializationPropertiesEncoding",
    "CSVSerializationPropertiesFormat",
    "CompatibilityLevel",
    "DataSourceStartType",
    "DataType",
    "DestinationType",
    "EventhouseDestinationPropertiesDataIngestionMode",
    "FabricCapacityUtilizationEventsSourcePropertiesEventScope",
    "FabricJobEventsSourcePropertiesEventScope",
    "FabricWorkspaceItemEventsSourcePropertiesEventScope",
    "FilterConditionOperatorType",
    "GroupByWindowType",
    "JSONSerializationPropertiesEncoding",
    "JoinOperatorPropertiesJoinType",
    "NodeStatus",
    "OperatorCommonDurationUnit",
    "OperatorType",
    "PayloadType",
    "SampleDataSourcePropertiesType",
    "SerializationType",
    "SourceType",
    "StreamType",
    "Type",
    # Models
    "DefinitionPart",
    "Definition",
    "DefinitionResponse",
    "CreateEventstreamRequest",
    "Properties",
    "Eventstream",
    "Eventstreams",
    "UpdateEventstreamDefinitionRequest",
    "UpdateEventstreamRequest",
    "SourceProperties",
    "AmazonKinesisSourceProperties",
    "AmazonMSKKafkaSourceProperties",
    "ApacheKafkaSourceProperties",
    "SampleDataSourceProperties",
    "DestinationProperties",
    "LakehouseDestinationProperties",
    "EventhouseDestinationProperties",
    "ActivatorDestinationProperties",
    "CustomEndpointDestinationProperties",
    "OperatorProperties",
    "FilterCondition",
    "FilterOperatorProperties",
    "AggregateColumn",
    "AggregateOperatorProperties",
    "GroupByWindow",
    "GroupByOperatorProperties",
    "JoinOperatorProperties",
    "Stream",
    "Node",
    "Source",
    "Destination",
    "Operator",
    "Topology",
]
