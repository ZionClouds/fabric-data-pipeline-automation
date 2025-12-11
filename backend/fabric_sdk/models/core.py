"""
Core Models for Microsoft Fabric SDK

Contains fundamental models used across all Fabric services including:
- Connections (Azure Blob, ADLS Gen2, S3, etc.)
- OneLake Shortcuts
- Workspaces
- Items
- Principals
- Credentials
- Git Integration

Converted from: knowledge/fabric/core/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Union
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS (from constants.go)
# =============================================================================

class AttributeName(str, Enum):
    """Specifies the name of the attribute being evaluated for access permissions."""
    ACTION = "Action"
    PATH = "Path"


class CapacityAssignmentProgress(str, Enum):
    """Workspace assignment to capacity progress status."""
    COMPLETED = "Completed"
    FAILED = "Failed"
    IN_PROGRESS = "InProgress"


class CapacityRegion(str, Enum):
    """The region of the capacity associated with this workspace."""
    AUSTRALIA_EAST = "Australia East"
    AUSTRALIA_SOUTHEAST = "Australia Southeast"
    BRAZIL_SOUTH = "Brazil South"
    BRAZIL_SOUTHEAST = "Brazil Southeast"
    CANADA_CENTRAL = "Canada Central"
    CANADA_EAST = "Canada East"
    CENTRAL_INDIA = "Central India"
    CENTRAL_US = "Central US"
    CENTRAL_US_EUAP = "Central US EUAP"
    CHINA_EAST = "China East"
    CHINA_EAST_2 = "China East 2"
    CHINA_EAST_3 = "China East 3"
    CHINA_NORTH = "China North"
    CHINA_NORTH_2 = "China North 2"
    CHINA_NORTH_3 = "China North 3"
    EAST_ASIA = "East Asia"
    EAST_US = "East US"
    EAST_US_2 = "East US 2"
    FRANCE_CENTRAL = "France Central"
    FRANCE_SOUTH = "France South"
    GERMANY_CENTRAL = "Germany Central"
    GERMANY_NORTH = "Germany North"
    GERMANY_NORTHEAST = "Germany Northeast"
    GERMANY_WEST_CENTRAL = "Germany West Central"
    ISRAEL_CENTRAL = "Israel Central"
    ITALY_NORTH = "Italy North"
    JAPAN_EAST = "Japan East"
    JAPAN_WEST = "Japan West"
    KOREA_CENTRAL = "Korea Central"
    KOREA_SOUTH = "Korea South"
    MEXICO_CENTRAL = "Mexico Central"
    NORTH_CENTRAL_US = "North Central US"
    NORTH_EUROPE = "North Europe"
    NORWAY_EAST = "Norway East"
    NORWAY_WEST = "Norway West"
    POLAND_CENTRAL = "Poland Central"
    QATAR_CENTRAL = "Qatar Central"
    SOUTH_AFRICA_NORTH = "South Africa North"
    SOUTH_AFRICA_WEST = "South Africa West"
    SOUTH_CENTRAL_US = "South Central US"
    SOUTH_INDIA = "South India"
    SOUTHEAST_ASIA = "Southeast Asia"
    SPAIN_CENTRAL = "Spain Central"
    SWEDEN_CENTRAL = "Sweden Central"
    SWITZERLAND_NORTH = "Switzerland North"
    SWITZERLAND_WEST = "Switzerland West"
    UAE_CENTRAL = "UAE Central"
    UAE_NORTH = "UAE North"
    UK_SOUTH = "UK South"
    UK_WEST = "UK West"
    WEST_CENTRAL_US = "West Central US"
    WEST_EUROPE = "West Europe"
    WEST_INDIA = "West India"
    WEST_US = "West US"
    WEST_US_2 = "West US 2"
    WEST_US_3 = "West US 3"


class CapacityState(str, Enum):
    """Capacity state."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class ChangeType(str, Enum):
    """A change of an item."""
    ADDED = "Added"
    DELETED = "Deleted"
    MODIFIED = "Modified"


class CredentialType(str, Enum):
    """The credential type of the connection."""
    ANONYMOUS = "Anonymous"
    BASIC = "Basic"
    KEY = "Key"
    OAUTH2 = "OAuth2"
    SERVICE_PRINCIPAL = "ServicePrincipal"
    SHARED_ACCESS_SIGNATURE = "SharedAccessSignature"
    WINDOWS = "Windows"
    WORKSPACE_IDENTITY = "WorkspaceIdentity"


class ConnectionRole(str, Enum):
    """The connection role of the principal."""
    OWNER = "Owner"
    USER = "User"
    USER_WITH_RESHARE = "UserWithReshare"


class ConnectivityType(str, Enum):
    """The connectivity type of the connection."""
    AUTOMATIC = "Automatic"
    ON_PREMISES_GATEWAY = "OnPremisesGateway"
    PERSONAL_CLOUD = "PersonalCloud"
    SHAREABLE_CLOUD = "ShareableCloud"
    VIRTUAL_NETWORK_GATEWAY = "VirtualNetworkGateway"


class DataSourceType(str, Enum):
    """The type of data source."""
    AZURE_BLOB_STORAGE = "AzureBlobStorage"
    AZURE_DATA_LAKE_STORAGE = "AzureDataLakeStorage"
    AZURE_SQL = "AzureSql"
    AZURE_SQL_DATABASE = "AzureSqlDatabase"
    AZURE_SQL_DATA_WAREHOUSE = "AzureSqlDataWarehouse"
    AMAZON_S3 = "AmazonS3"
    GOOGLE_CLOUD_STORAGE = "GoogleCloudStorage"
    SHAREPOINT = "SharePoint"
    ORACLE = "Oracle"
    MYSQL = "MySql"
    POSTGRESQL = "PostgreSql"
    SNOWFLAKE = "Snowflake"
    DATABRICKS = "Databricks"
    HTTP = "Http"
    REST = "Rest"
    ODATA = "OData"
    FILE = "File"
    FOLDER = "Folder"
    WEB = "Web"


class GitProviderType(str, Enum):
    """Git provider type."""
    AZURE_DEV_OPS = "AzureDevOps"
    GITHUB = "GitHub"


class GitCredentialsSource(str, Enum):
    """The Git credentials source."""
    AUTOMATIC = "Automatic"
    CONFIGURED_CONNECTION = "ConfiguredConnection"
    NONE = "None"


class GroupType(str, Enum):
    """The type of the group."""
    DISTRIBUTION_LIST = "DistributionList"
    SECURITY_GROUP = "SecurityGroup"
    UNKNOWN = "Unknown"


class ItemType(str, Enum):
    """The item type in Fabric."""
    DASHBOARD = "Dashboard"
    DATA_PIPELINE = "DataPipeline"
    DATAFLOW = "Dataflow"
    DATAMART = "Datamart"
    DATASET = "Dataset"  # Semantic Model
    ENVIRONMENT = "Environment"
    EVENTHOUSE = "Eventhouse"
    EVENTSTREAM = "Eventstream"
    KQL_DATABASE = "KQLDatabase"
    KQL_QUERYSET = "KQLQueryset"
    LAKEHOUSE = "Lakehouse"
    ML_EXPERIMENT = "MLExperiment"
    ML_MODEL = "MLModel"
    MIRRORED_DATABASE = "MirroredDatabase"
    MIRRORED_WAREHOUSE = "MirroredWarehouse"
    NOTEBOOK = "Notebook"
    PAGINATED_REPORT = "PaginatedReport"
    REFLEX = "Reflex"
    REPORT = "Report"
    SEMANTIC_MODEL = "SemanticModel"
    SPARK_JOB_DEFINITION = "SparkJobDefinition"
    SQL_DATABASE = "SQLDatabase"
    SQL_ENDPOINT = "SQLEndpoint"
    WAREHOUSE = "Warehouse"
    COPY_JOB = "CopyJob"
    VARIABLE_LIBRARY = "VariableLibrary"
    GRAPH_QL_API = "GraphQLApi"
    APACHE_AIRFLOW_JOB = "ApacheAirflowJob"


class PayloadType(str, Enum):
    """The payload type for definitions."""
    INLINE_BASE64 = "InlineBase64"
    VSO_GIT = "VSOGit"


class PrincipalType(str, Enum):
    """The type of the principal."""
    GROUP = "Group"
    SERVICE_PRINCIPAL = "ServicePrincipal"
    SERVICE_PRINCIPAL_PROFILE = "ServicePrincipalProfile"
    USER = "User"


class TransformType(str, Enum):
    """The type of transform for shortcuts."""
    CSV_TO_DELTA = "CsvToDelta"


class WorkspaceRole(str, Enum):
    """The workspace role of the principal."""
    ADMIN = "Admin"
    CONTRIBUTOR = "Contributor"
    MEMBER = "Member"
    VIEWER = "Viewer"


class DeploymentPipelineRole(str, Enum):
    """The deployment pipeline role."""
    ADMIN = "Admin"


class GatewayRole(str, Enum):
    """The gateway role."""
    ADMIN = "Admin"
    CONNECTION_CREATOR = "ConnectionCreator"
    CONNECTION_CREATOR_WITH_RESHARE = "ConnectionCreatorWithReshare"


class WorkspaceIdentity(str, Enum):
    """Workspace identity type."""
    NONE = "None"
    WORKSPACE = "Workspace"


# =============================================================================
# BASE MODELS
# =============================================================================

class ItemTag(BaseModel):
    """Represents a tag applied on an item."""
    display_name: str = Field(..., alias="displayName", description="The name of the tag")
    id: str = Field(..., description="The tag ID")

    class Config:
        populate_by_name = True


class Principal(BaseModel):
    """Represents an identity or a Microsoft Entra group."""
    id: str = Field(..., description="The principal's ID")
    type: PrincipalType = Field(..., description="The type of the principal")
    display_name: Optional[str] = Field(None, alias="displayName", description="The principal's display name")
    group_details: Optional["PrincipalGroupDetails"] = Field(None, alias="groupDetails")
    service_principal_details: Optional["PrincipalServicePrincipalDetails"] = Field(
        None, alias="servicePrincipalDetails"
    )
    service_principal_profile_details: Optional["PrincipalServicePrincipalProfileDetails"] = Field(
        None, alias="servicePrincipalProfileDetails"
    )
    user_details: Optional["PrincipalUserDetails"] = Field(None, alias="userDetails")

    class Config:
        populate_by_name = True


class PrincipalGroupDetails(BaseModel):
    """Group specific details."""
    group_type: Optional[GroupType] = Field(None, alias="groupType")

    class Config:
        populate_by_name = True


class PrincipalServicePrincipalDetails(BaseModel):
    """Service principal specific details."""
    aad_app_id: Optional[str] = Field(None, alias="aadAppId", description="The service principal's Microsoft Entra AppId")

    class Config:
        populate_by_name = True


class PrincipalServicePrincipalProfileDetails(BaseModel):
    """Service principal profile details."""
    parent_principal: Optional[Principal] = Field(None, alias="parentPrincipal")

    class Config:
        populate_by_name = True


class PrincipalUserDetails(BaseModel):
    """User principal specific details."""
    user_principal_name: Optional[str] = Field(None, alias="userPrincipalName")

    class Config:
        populate_by_name = True


# =============================================================================
# CREDENTIALS
# =============================================================================

class Credentials(BaseModel):
    """Base credentials model."""
    credential_type: CredentialType = Field(..., alias="credentialType")

    class Config:
        populate_by_name = True


class AnonymousCredentials(Credentials):
    """Credentials for Anonymous CredentialType."""
    credential_type: CredentialType = Field(default=CredentialType.ANONYMOUS, alias="credentialType")


class BasicCredentials(Credentials):
    """Credentials for Basic CredentialType."""
    credential_type: CredentialType = Field(default=CredentialType.BASIC, alias="credentialType")
    username: str = Field(..., description="The username")
    password: str = Field(..., description="The password")


class KeyCredentials(Credentials):
    """Credentials for Key CredentialType."""
    credential_type: CredentialType = Field(default=CredentialType.KEY, alias="credentialType")
    key: str = Field(..., description="The key/account key")


class ServicePrincipalCredentials(Credentials):
    """Credentials for ServicePrincipal CredentialType."""
    credential_type: CredentialType = Field(default=CredentialType.SERVICE_PRINCIPAL, alias="credentialType")
    tenant_id: str = Field(..., alias="tenantId", description="The tenant ID")
    service_principal_client_id: str = Field(..., alias="servicePrincipalClientId", description="The client ID")
    service_principal_secret: str = Field(..., alias="servicePrincipalSecret", description="The client secret")


class SharedAccessSignatureCredentials(Credentials):
    """Credentials for SharedAccessSignature CredentialType."""
    credential_type: CredentialType = Field(default=CredentialType.SHARED_ACCESS_SIGNATURE, alias="credentialType")
    token: str = Field(..., description="The SAS token")


class OAuth2Credentials(Credentials):
    """Credentials for OAuth2 CredentialType."""
    credential_type: CredentialType = Field(default=CredentialType.OAUTH2, alias="credentialType")


class WorkspaceIdentityCredentials(Credentials):
    """Credentials for WorkspaceIdentity CredentialType."""
    credential_type: CredentialType = Field(default=CredentialType.WORKSPACE_IDENTITY, alias="credentialType")


# =============================================================================
# CONNECTIONS
# =============================================================================

class ConnectionDetails(BaseModel):
    """Connection details including type and path."""
    type: DataSourceType = Field(..., description="The data source type")
    path: str = Field(..., description="The connection path/URL")
    creation_method: Optional[str] = Field(None, alias="creationMethod")

    class Config:
        populate_by_name = True


class CreateConnectionRequest(BaseModel):
    """Create connection request payload."""
    connectivity_type: ConnectivityType = Field(..., alias="connectivityType")
    connection_details: ConnectionDetails = Field(..., alias="connectionDetails")
    display_name: str = Field(..., alias="displayName", description="The connection display name")
    credential_details: Credentials = Field(..., alias="credentialDetails")
    privacy_level: Optional[str] = Field(None, alias="privacyLevel")

    class Config:
        populate_by_name = True


class Connection(BaseModel):
    """A connection object."""
    id: Optional[str] = Field(None, description="The connection ID (GUID)")
    display_name: Optional[str] = Field(None, alias="displayName")
    connectivity_type: Optional[ConnectivityType] = Field(None, alias="connectivityType")
    connection_details: Optional[ConnectionDetails] = Field(None, alias="connectionDetails")
    credential_details: Optional[Credentials] = Field(None, alias="credentialDetails")
    privacy_level: Optional[str] = Field(None, alias="privacyLevel")
    gateway_id: Optional[str] = Field(None, alias="gatewayId")

    class Config:
        populate_by_name = True


class Connections(BaseModel):
    """A list of connections."""
    value: List[Connection] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# SHORTCUT TARGETS
# =============================================================================

class AzureBlobStorage(BaseModel):
    """Target Azure Blob Storage data source for shortcuts."""
    connection_id: str = Field(..., alias="connectionId", description="The connection ID (GUID)")
    location: str = Field(..., description="The storage account URL (https://[account-name].blob.core.windows.net)")
    subpath: str = Field(..., description="Container and subfolder path (e.g., /mycontainer/mysubfolder)")

    class Config:
        populate_by_name = True


class AdlsGen2(BaseModel):
    """Target ADLS Gen2 data source for shortcuts."""
    connection_id: str = Field(..., alias="connectionId", description="The connection ID (GUID)")
    location: str = Field(..., description="The ADLS account URL (https://[account-name].dfs.core.windows.net)")
    subpath: str = Field(..., description="Container and subfolder path")

    class Config:
        populate_by_name = True


class AmazonS3(BaseModel):
    """Target Amazon S3 data source for shortcuts."""
    connection_id: str = Field(..., alias="connectionId", description="The connection ID (GUID)")
    location: str = Field(..., description="The S3 bucket URL (https://[bucket-name].s3.[region].amazonaws.com)")
    subpath: Optional[str] = Field(None, description="Target folder or subfolder within the S3 bucket")

    class Config:
        populate_by_name = True


class GoogleCloudStorage(BaseModel):
    """Target Google Cloud Storage data source for shortcuts."""
    connection_id: str = Field(..., alias="connectionId", description="The connection ID (GUID)")
    location: str = Field(..., description="The GCS bucket URL")
    subpath: Optional[str] = Field(None, description="Target folder path")

    class Config:
        populate_by_name = True


class OneLakeTarget(BaseModel):
    """Target OneLake location for shortcuts."""
    workspace_id: str = Field(..., alias="workspaceId", description="Target workspace ID")
    item_id: str = Field(..., alias="itemId", description="Target item (lakehouse) ID")
    path: str = Field(..., description="Path within the target item")

    class Config:
        populate_by_name = True


class ExternalDataShareTarget(BaseModel):
    """Target external data share for shortcuts."""
    connection_unique_name: str = Field(..., alias="connectionUniqueName")

    class Config:
        populate_by_name = True


class ShortcutTarget(BaseModel):
    """Target for a shortcut - can be one of multiple types."""
    azure_blob_storage: Optional[AzureBlobStorage] = Field(None, alias="azureBlobStorage")
    adls_gen2: Optional[AdlsGen2] = Field(None, alias="adlsGen2")
    amazon_s3: Optional[AmazonS3] = Field(None, alias="amazonS3")
    google_cloud_storage: Optional[GoogleCloudStorage] = Field(None, alias="googleCloudStorage")
    one_lake: Optional[OneLakeTarget] = Field(None, alias="oneLake")
    external_data_share: Optional[ExternalDataShareTarget] = Field(None, alias="externalDataShare")

    class Config:
        populate_by_name = True


# =============================================================================
# SHORTCUTS
# =============================================================================

class CSVToDeltaTransformProperties(BaseModel):
    """Properties for the CSV to Delta transform."""
    delimiter: Optional[str] = Field(",", description="CSV delimiter")
    skip_files_with_errors: Optional[bool] = Field(True, alias="skipFilesWithErrors")
    use_first_row_as_header: Optional[bool] = Field(True, alias="useFirstRowAsHeader")

    class Config:
        populate_by_name = True


class Transform(BaseModel):
    """Transform configuration for shortcuts."""
    type: TransformType = Field(..., description="The transform type")
    properties: Optional[CSVToDeltaTransformProperties] = Field(None)

    class Config:
        populate_by_name = True


class CreateShortcutRequest(BaseModel):
    """Create shortcut request payload."""
    name: str = Field(..., description="The shortcut name")
    path: str = Field(..., description="The shortcut path (Files or Tables)")
    target: ShortcutTarget = Field(..., description="The shortcut target")

    class Config:
        populate_by_name = True


class CreateShortcutWithTransformRequest(BaseModel):
    """Create shortcut request with optional transform."""
    name: str = Field(..., description="The shortcut name")
    path: str = Field(..., description="The shortcut path")
    target: ShortcutTarget = Field(..., description="The shortcut target")
    transform: Optional[Transform] = Field(None, description="Optional transform configuration")

    class Config:
        populate_by_name = True


class Shortcut(BaseModel):
    """A shortcut object."""
    name: Optional[str] = Field(None, description="The shortcut name")
    path: Optional[str] = Field(None, description="The shortcut path")
    target: Optional[ShortcutTarget] = Field(None, description="The shortcut target")

    class Config:
        populate_by_name = True


class CreateShortcutResponse(BaseModel):
    """Response from creating a shortcut."""
    name: Optional[str] = Field(None)
    path: Optional[str] = Field(None)
    target: Optional[ShortcutTarget] = Field(None)

    class Config:
        populate_by_name = True


class Shortcuts(BaseModel):
    """A list of shortcuts."""
    value: List[Shortcut] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class BulkCreateShortcutsRequest(BaseModel):
    """Bulk create shortcuts request."""
    create_shortcut_requests: List[CreateShortcutWithTransformRequest] = Field(
        ..., alias="createShortcutRequests"
    )

    class Config:
        populate_by_name = True


class BulkCreateShortcutResponse(BaseModel):
    """Response from bulk creating shortcuts."""
    value: List[CreateShortcutResponse] = Field(default_factory=list)

    class Config:
        populate_by_name = True


# =============================================================================
# WORKSPACES
# =============================================================================

class CreateWorkspaceRequest(BaseModel):
    """Create workspace request payload."""
    display_name: str = Field(..., alias="displayName", description="The workspace display name")
    description: Optional[str] = Field(None, description="The workspace description")
    capacity_id: Optional[str] = Field(None, alias="capacityId", description="The capacity ID to assign")

    class Config:
        populate_by_name = True


class Workspace(BaseModel):
    """A workspace object."""
    id: Optional[str] = Field(None, description="The workspace ID")
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    type: Optional[str] = Field(None, description="The workspace type")
    capacity_id: Optional[str] = Field(None, alias="capacityId")
    capacity_assignment_progress: Optional[CapacityAssignmentProgress] = Field(
        None, alias="capacityAssignmentProgress"
    )

    class Config:
        populate_by_name = True


class Workspaces(BaseModel):
    """A list of workspaces."""
    value: List[Workspace] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class UpdateWorkspaceRequest(BaseModel):
    """Update workspace request."""
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class AssignWorkspaceToCapacityRequest(BaseModel):
    """Assign workspace to capacity request."""
    capacity_id: str = Field(..., alias="capacityId")

    class Config:
        populate_by_name = True


# =============================================================================
# ITEMS (Generic)
# =============================================================================

class Item(BaseModel):
    """A generic Fabric item."""
    id: Optional[str] = Field(None, description="The item ID")
    type: Optional[ItemType] = Field(None, description="The item type")
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    workspace_id: Optional[str] = Field(None, alias="workspaceId")
    folder_id: Optional[str] = Field(None, alias="folderId")
    tags: Optional[List[ItemTag]] = Field(None)

    class Config:
        populate_by_name = True


class Items(BaseModel):
    """A list of items."""
    value: List[Item] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# DEFINITIONS
# =============================================================================

class DefinitionPart(BaseModel):
    """Definition part for items (pipelines, notebooks, etc.)."""
    path: Optional[str] = Field(None, description="The part path")
    payload: Optional[str] = Field(None, description="The base64-encoded payload")
    payload_type: Optional[PayloadType] = Field(None, alias="payloadType")

    class Config:
        populate_by_name = True


class Definition(BaseModel):
    """Item definition containing parts."""
    parts: List[DefinitionPart] = Field(default_factory=list)
    format: Optional[str] = Field(None, description="The definition format")

    class Config:
        populate_by_name = True


class DefinitionResponse(BaseModel):
    """Response containing an item definition."""
    definition: Optional[Definition] = Field(None)

    class Config:
        populate_by_name = True


# =============================================================================
# CAPACITIES
# =============================================================================

class Capacity(BaseModel):
    """A capacity object."""
    id: Optional[str] = Field(None, description="The capacity ID")
    display_name: Optional[str] = Field(None, alias="displayName")
    sku: Optional[str] = Field(None, description="The capacity SKU")
    region: Optional[CapacityRegion] = Field(None)
    state: Optional[CapacityState] = Field(None)

    class Config:
        populate_by_name = True


class Capacities(BaseModel):
    """A list of capacities."""
    value: List[Capacity] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# GIT INTEGRATION
# =============================================================================

class AzureDevOpsDetails(BaseModel):
    """Azure DevOps Git provider details."""
    git_provider_type: GitProviderType = Field(
        default=GitProviderType.AZURE_DEV_OPS, alias="gitProviderType"
    )
    organization_name: str = Field(..., alias="organizationName")
    project_name: str = Field(..., alias="projectName")
    repository_name: str = Field(..., alias="repositoryName")
    branch_name: str = Field(..., alias="branchName")
    directory_name: str = Field(..., alias="directoryName")

    class Config:
        populate_by_name = True


class GitHubDetails(BaseModel):
    """GitHub Git provider details."""
    git_provider_type: GitProviderType = Field(
        default=GitProviderType.GITHUB, alias="gitProviderType"
    )
    owner_name: str = Field(..., alias="ownerName")
    repository_name: str = Field(..., alias="repositoryName")
    branch_name: str = Field(..., alias="branchName")
    directory_name: str = Field(..., alias="directoryName")

    class Config:
        populate_by_name = True


class GitCredentials(BaseModel):
    """Git credentials configuration."""
    source: GitCredentialsSource = Field(...)

    class Config:
        populate_by_name = True


class GitConnection(BaseModel):
    """Git connection configuration."""
    git_provider_details: Union[AzureDevOpsDetails, GitHubDetails] = Field(..., alias="gitProviderDetails")

    class Config:
        populate_by_name = True


class ConnectToGitRequest(BaseModel):
    """Connect workspace to Git request."""
    git_provider_details: Union[AzureDevOpsDetails, GitHubDetails] = Field(..., alias="gitProviderDetails")

    class Config:
        populate_by_name = True


# =============================================================================
# ROLE ASSIGNMENTS
# =============================================================================

class AddWorkspaceRoleAssignmentRequest(BaseModel):
    """Add workspace role assignment request."""
    principal: Principal = Field(...)
    role: WorkspaceRole = Field(...)

    class Config:
        populate_by_name = True


class AddConnectionRoleAssignmentRequest(BaseModel):
    """Add connection role assignment request."""
    principal: Principal = Field(...)
    role: ConnectionRole = Field(...)

    class Config:
        populate_by_name = True


class AddGatewayRoleAssignmentRequest(BaseModel):
    """Add gateway role assignment request."""
    principal: Principal = Field(...)
    role: GatewayRole = Field(...)

    class Config:
        populate_by_name = True


# =============================================================================
# FOLDERS
# =============================================================================

class Folder(BaseModel):
    """A folder in a workspace."""
    id: Optional[str] = Field(None, description="The folder ID")
    display_name: Optional[str] = Field(None, alias="displayName")
    parent_folder_id: Optional[str] = Field(None, alias="parentFolderId")
    workspace_id: Optional[str] = Field(None, alias="workspaceId")

    class Config:
        populate_by_name = True


class CreateFolderRequest(BaseModel):
    """Create folder request."""
    display_name: str = Field(..., alias="displayName")
    parent_folder_id: Optional[str] = Field(None, alias="parentFolderId")

    class Config:
        populate_by_name = True


class Folders(BaseModel):
    """A list of folders."""
    value: List[Folder] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


# =============================================================================
# DOMAINS
# =============================================================================

class Domain(BaseModel):
    """A domain object."""
    id: Optional[str] = Field(None, description="The domain ID")
    display_name: Optional[str] = Field(None, alias="displayName")
    description: Optional[str] = Field(None)
    parent_domain_id: Optional[str] = Field(None, alias="parentDomainId")

    class Config:
        populate_by_name = True


class Domains(BaseModel):
    """A list of domains."""
    value: List[Domain] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class AssignWorkspaceToDomainRequest(BaseModel):
    """Assign workspace to domain request."""
    domain_id: str = Field(..., alias="domainId")

    class Config:
        populate_by_name = True


# =============================================================================
# TAGS
# =============================================================================

class Tag(BaseModel):
    """A tag object."""
    id: Optional[str] = Field(None, description="The tag ID")
    display_name: Optional[str] = Field(None, alias="displayName")

    class Config:
        populate_by_name = True


class Tags(BaseModel):
    """A list of tags."""
    value: List[Tag] = Field(default_factory=list)
    continuation_token: Optional[str] = Field(None, alias="continuationToken")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri")

    class Config:
        populate_by_name = True


class ApplyTagsRequest(BaseModel):
    """Apply tags to an item request."""
    tags: List[str] = Field(..., description="Array of tag IDs")

    class Config:
        populate_by_name = True


# =============================================================================
# LONG RUNNING OPERATIONS
# =============================================================================

class OperationState(str, Enum):
    """State of a long-running operation."""
    NOT_STARTED = "NotStarted"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


class LongRunningOperation(BaseModel):
    """A long-running operation."""
    id: Optional[str] = Field(None, description="The operation ID")
    status: Optional[OperationState] = Field(None)
    created_time_utc: Optional[datetime] = Field(None, alias="createdTimeUtc")
    last_updated_time_utc: Optional[datetime] = Field(None, alias="lastUpdatedTimeUtc")
    percent_complete: Optional[int] = Field(None, alias="percentComplete")
    error: Optional[dict] = Field(None)

    class Config:
        populate_by_name = True


# Update forward references
Principal.model_rebuild()
PrincipalServicePrincipalProfileDetails.model_rebuild()
