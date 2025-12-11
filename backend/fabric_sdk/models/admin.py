"""
Admin Models for Microsoft Fabric SDK

Contains models for admin operations including:
- Domains and domain management
- External data shares
- Item access and permissions
- Tenant settings
- User/group management
- Workspaces

Converted from: knowledge/fabric/admin/models.go and constants.go
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from pydantic import BaseModel, Field

from fabric_sdk.models.core import ItemTag, ItemType, Principal, GroupType, PrincipalType


# =============================================================================
# ENUMS
# =============================================================================

class AssignmentMethod(str, Enum):
    """Specifies whether the assigned label was set by an automated process or manually."""
    PRIVILEDGED = "Priviledged"
    STANDARD = "Standard"


class Category(str, Enum):
    """The category of the item type."""
    ITEM = "Item"


class ContributorsScopeType(str, Enum):
    """The contributor scope."""
    ADMINS_ONLY = "AdminsOnly"
    ALL_TENANT = "AllTenant"
    SPECIFIC_USERS_AND_GROUPS = "SpecificUsersAndGroups"


class DelegatedFrom(str, Enum):
    """The Fabric component that the tenant setting was delegated from."""
    CAPACITY = "Capacity"
    DOMAIN = "Domain"
    TENANT = "Tenant"


class DomainRole(str, Enum):
    """Represents the domain members by the principal's request type."""
    ADMIN = "Admin"
    CONTRIBUTOR = "Contributor"


class ExternalDataShareStatus(str, Enum):
    """The status of a given external data share."""
    ACTIVE = "Active"
    INVITATION_EXPIRED = "InvitationExpired"
    PENDING = "Pending"
    REVOKED = "Revoked"


class GitProviderType(str, Enum):
    """A Git provider type."""
    AZURE_DEV_OPS = "AzureDevOps"
    GIT_HUB = "GitHub"


class ItemPermissions(str, Enum):
    """Item permissions."""
    EXECUTE = "Execute"
    EXPLORE = "Explore"
    READ = "Read"
    RESHARE = "Reshare"
    WRITE = "Write"


class ItemState(str, Enum):
    """The item state."""
    ACTIVE = "Active"


class SharingLinkType(str, Enum):
    """Specifies the type of sharing link that is required to be deleted for each Fabric item."""
    ORG_LINK = "OrgLink"


class SharingLinksRemovalStatus(str, Enum):
    """The status of removal of sharing links."""
    NOT_FOUND = "NotFound"
    SUCCEEDED = "Succeeded"


class Status(str, Enum):
    """The status of an information protection label change operation."""
    FAILED = "Failed"
    FAILED_TO_GET_USAGE_RIGHTS = "FailedToGetUsageRights"
    INSUFFICIENT_USAGE_RIGHTS = "InsufficientUsageRights"
    NOT_FOUND = "NotFound"
    SUCCEEDED = "Succeeded"


class TagScopeType(str, Enum):
    """Denotes tag scope."""
    DOMAIN = "Domain"
    TENANT = "Tenant"


class TenantSettingPropertyType(str, Enum):
    """Tenant setting property type."""
    BOOLEAN = "Boolean"
    FREE_TEXT = "FreeText"
    INTEGER = "Integer"
    MAIL_ENABLED_SECURITY_GROUP = "MailEnabledSecurityGroup"
    URL = "Url"


class WorkspaceRole(str, Enum):
    """A Workspace role."""
    ADMIN = "Admin"
    CONTRIBUTOR = "Contributor"
    MEMBER = "Member"
    VIEWER = "Viewer"


class WorkspaceState(str, Enum):
    """The workspace state."""
    ACTIVE = "Active"
    DELETED = "Deleted"


class WorkspaceType(str, Enum):
    """A workspace type."""
    ADMIN_WORKSPACE = "AdminWorkspace"
    PERSONAL = "Personal"
    WORKSPACE = "Workspace"


# =============================================================================
# MODELS
# =============================================================================

class AccessDetails(BaseModel):
    """Access details model for list access entities response."""
    principal: Principal = Field(..., description="The principal")
    item_access_details: Optional[List[ItemAccessDetails]] = Field(None, alias="itemAccessDetails", description="List of item access details")
    additional_permissions: Optional[List[str]] = Field(None, alias="additionalPermissions", description="Additional permissions")


class AccessEntities(BaseModel):
    """A list of access details for a given item."""
    access_entities: List[AccessDetails] = Field(..., alias="accessEntities", description="A list of access entities")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


class BulkDeleteSharingLinksRequest(BaseModel):
    """Request to delete sharing links for multiple items."""
    items: List[ItemIdentifier] = Field(..., description="List of items to delete sharing links for")
    sharing_link_type: SharingLinkType = Field(..., alias="sharingLinkType", description="The type of sharing link to delete")


class BulkDeleteSharingLinksResponse(BaseModel):
    """Response for bulk delete sharing links operation."""
    items: List[SharingLinksRemovalResult] = Field(..., description="List of results for sharing link removal")


class ContributorsScope(BaseModel):
    """The contributor scope of a domain."""
    type: ContributorsScopeType = Field(..., description="The scope type")
    principals: Optional[List[Principal]] = Field(None, description="The list of principals if type is SpecificUsersAndGroups")


class CreateDomainRequest(BaseModel):
    """Create domain request payload."""
    display_name: str = Field(..., alias="displayName", description="The domain display name")
    contributors_scope: Optional[ContributorsScope] = Field(None, alias="contributorsScope", description="The contributor scope")
    description: Optional[str] = Field(None, description="The domain description")
    parent_domain_id: Optional[str] = Field(None, alias="parentDomainId", description="The parent domain ID")


class Domain(BaseModel):
    """A domain object."""
    id: str = Field(..., description="The domain ID")
    display_name: str = Field(..., alias="displayName", description="The domain display name")
    contributors_scope: ContributorsScope = Field(..., alias="contributorsScope", description="The contributor scope")
    description: Optional[str] = Field(None, description="The domain description")
    parent_domain_id: Optional[str] = Field(None, alias="parentDomainId", description="The parent domain ID")


class Domains(BaseModel):
    """A list of domains."""
    value: List[Domain] = Field(..., description="A list of domains")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


class DomainWorkspacesAssignment(BaseModel):
    """Request to assign or unassign workspaces to a domain."""
    workspaces_to_assign: Optional[List[str]] = Field(None, alias="workspacesToAssign", description="List of workspace IDs to assign")
    workspaces_to_unassign: Optional[List[str]] = Field(None, alias="workspacesToUnassign", description="List of workspace IDs to unassign")


class ExternalDataShare(BaseModel):
    """An external data share."""
    id: str = Field(..., description="The external data share ID")
    item_id: str = Field(..., alias="itemId", description="The item ID")
    recipient_email: str = Field(..., alias="recipientEmail", description="The recipient email")
    status: ExternalDataShareStatus = Field(..., description="The status")
    workspace_id: str = Field(..., alias="workspaceId", description="The workspace ID")
    invitation_expiration_date: Optional[datetime] = Field(None, alias="invitationExpirationDate", description="When the invitation expires")
    recipient_tenant_id: Optional[str] = Field(None, alias="recipientTenantId", description="The recipient tenant ID")
    share_kind: Optional[str] = Field(None, alias="shareKind", description="The kind of share")


class ExternalDataShares(BaseModel):
    """A list of external data shares."""
    value: List[ExternalDataShare] = Field(..., description="A list of external data shares")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


class ItemAccessDetails(BaseModel):
    """Item access details."""
    item_id: str = Field(..., alias="itemId", description="The item ID")
    permissions: List[ItemPermissions] = Field(..., description="List of permissions")
    type: ItemType = Field(..., description="The item type")
    additional_permissions: Optional[List[str]] = Field(None, alias="additionalPermissions", description="Additional permissions")


class ItemIdentifier(BaseModel):
    """Item identifier."""
    id: str = Field(..., description="The item ID")
    type: ItemType = Field(..., description="The item type")


class ItemMetadata(BaseModel):
    """Item metadata for admin operations."""
    id: str = Field(..., description="The item ID")
    display_name: str = Field(..., alias="displayName", description="The item display name")
    type: ItemType = Field(..., description="The item type")
    workspace_id: str = Field(..., alias="workspaceId", description="The workspace ID")
    description: Optional[str] = Field(None, description="The item description")
    sensitivity_label: Optional[SensitivityLabel] = Field(None, alias="sensitivityLabel", description="The sensitivity label")
    state: Optional[ItemState] = Field(None, description="The item state")


class Items(BaseModel):
    """A list of items."""
    value: List[ItemMetadata] = Field(..., description="A list of items")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


class ModifyWorkspaceGitConnectionRequest(BaseModel):
    """Request to modify workspace git connection."""
    git_connection_details: Optional[WorkspaceGitConnectionDetails] = Field(None, alias="gitConnectionDetails", description="Git connection details")


class ProvisionIdentity(BaseModel):
    """Identity provisioning information."""
    identity_id: str = Field(..., alias="identityId", description="The identity ID")
    display_name: str = Field(..., alias="displayName", description="The display name")
    type: PrincipalType = Field(..., description="The principal type")
    user_principal_name: Optional[str] = Field(None, alias="userPrincipalName", description="The user principal name for User type")


class RoleAssignment(BaseModel):
    """A role assignment for a domain."""
    id: str = Field(..., description="The role assignment ID")
    principal: Principal = Field(..., description="The principal")
    role: DomainRole = Field(..., description="The domain role")


class RoleAssignments(BaseModel):
    """A list of role assignments."""
    value: List[RoleAssignment] = Field(..., description="A list of role assignments")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


class SensitivityLabel(BaseModel):
    """Sensitivity label information."""
    id: str = Field(..., description="The sensitivity label ID")
    assignment_method: Optional[AssignmentMethod] = Field(None, alias="assignmentMethod", description="The assignment method")


class SetItemLabelRequest(BaseModel):
    """Request to set an item's sensitivity label."""
    label_id: str = Field(..., alias="labelId", description="The label ID to assign")
    assignment_method: Optional[AssignmentMethod] = Field(None, alias="assignmentMethod", description="The assignment method")
    delegated_user: Optional[ProvisionIdentity] = Field(None, alias="delegatedUser", description="The delegated user")


class SetItemLabelsRequest(BaseModel):
    """Request to set labels for multiple items."""
    items: List[ItemLabelRequest] = Field(..., description="List of items with labels to set")


class ItemLabelRequest(BaseModel):
    """Item with label to set."""
    item: ItemIdentifier = Field(..., description="The item identifier")
    label_id: str = Field(..., alias="labelId", description="The label ID")
    assignment_method: Optional[AssignmentMethod] = Field(None, alias="assignmentMethod", description="The assignment method")
    delegated_user: Optional[ProvisionIdentity] = Field(None, alias="delegatedUser", description="The delegated user")


class SetItemLabelsResponse(BaseModel):
    """Response for setting labels on multiple items."""
    items: List[ItemLabelResult] = Field(..., description="List of results for label setting")


class ItemLabelResult(BaseModel):
    """Result of setting a label on an item."""
    item: ItemIdentifier = Field(..., description="The item identifier")
    status: Status = Field(..., description="The status")


class SharingLinksRemovalResult(BaseModel):
    """Result of sharing link removal for an item."""
    item: ItemIdentifier = Field(..., description="The item identifier")
    status: SharingLinksRemovalStatus = Field(..., description="The status")


class Tag(BaseModel):
    """A tag."""
    id: str = Field(..., description="The tag ID")
    name: str = Field(..., description="The tag name")
    scope_type: TagScopeType = Field(..., alias="scopeType", description="The scope type")
    scope_id: Optional[str] = Field(None, alias="scopeId", description="The scope ID")


class Tags(BaseModel):
    """A list of tags."""
    value: List[Tag] = Field(..., description="A list of tags")


class TenantSetting(BaseModel):
    """A tenant setting."""
    setting_name: str = Field(..., alias="settingName", description="The setting name")
    enabled: Optional[bool] = Field(None, description="Whether the setting is enabled")
    tenant_setting_group: Optional[str] = Field(None, alias="tenantSettingGroup", description="The tenant setting group")
    title: Optional[str] = Field(None, description="The setting title")
    can_specify_security_groups: Optional[bool] = Field(None, alias="canSpecifySecurityGroups", description="Whether security groups can be specified")
    delegated_from: Optional[DelegatedFrom] = Field(None, alias="delegatedFrom", description="Where the setting was delegated from")
    enabled_security_groups: Optional[List[Principal]] = Field(None, alias="enabledSecurityGroups", description="Enabled security groups")
    properties: Optional[List[TenantSettingProperty]] = Field(None, description="Setting properties")


class TenantSettingProperty(BaseModel):
    """A tenant setting property."""
    name: str = Field(..., description="The property name")
    type: TenantSettingPropertyType = Field(..., description="The property type")
    value: Optional[str] = Field(None, description="The property value")


class TenantSettings(BaseModel):
    """A list of tenant settings."""
    value: List[TenantSetting] = Field(..., description="A list of tenant settings")


class UpdateDomainRequest(BaseModel):
    """Update domain request payload."""
    contributors_scope: Optional[ContributorsScope] = Field(None, alias="contributorsScope", description="The contributor scope")
    description: Optional[str] = Field(None, description="The domain description")
    display_name: Optional[str] = Field(None, alias="displayName", description="The domain display name")


class User(BaseModel):
    """A user."""
    id: str = Field(..., description="The user ID")
    display_name: Optional[str] = Field(None, alias="displayName", description="The display name")
    email_address: Optional[str] = Field(None, alias="emailAddress", description="The email address")
    graph_id: Optional[str] = Field(None, alias="graphId", description="The graph ID")
    principal_name: Optional[str] = Field(None, alias="principalName", description="The principal name")
    type: Optional[str] = Field(None, description="The user type")
    user_type: Optional[str] = Field(None, alias="userType", description="The user type")


class Users(BaseModel):
    """A list of users."""
    value: List[User] = Field(..., description="A list of users")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


class WorkspaceGitConnectionDetails(BaseModel):
    """Git connection details for a workspace."""
    git_provider_type: GitProviderType = Field(..., alias="gitProviderType", description="The git provider type")
    git_connection_state: Optional[str] = Field(None, alias="gitConnectionState", description="The git connection state")
    organization_name: Optional[str] = Field(None, alias="organizationName", description="The organization name")
    project_name: Optional[str] = Field(None, alias="projectName", description="The project name")
    repository_name: Optional[str] = Field(None, alias="repositoryName", description="The repository name")


class WorkspaceInfo(BaseModel):
    """Workspace information."""
    id: str = Field(..., description="The workspace ID")
    name: str = Field(..., description="The workspace name")
    type: WorkspaceType = Field(..., description="The workspace type")
    capacity_id: Optional[str] = Field(None, alias="capacityId", description="The capacity ID")
    description: Optional[str] = Field(None, description="The workspace description")
    git_connection_details: Optional[WorkspaceGitConnectionDetails] = Field(None, alias="gitConnectionDetails", description="Git connection details")
    state: Optional[WorkspaceState] = Field(None, description="The workspace state")


class Workspaces(BaseModel):
    """A list of workspaces."""
    value: List[WorkspaceInfo] = Field(..., description="A list of workspaces")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


class WorkspaceRoleAssignment(BaseModel):
    """A workspace role assignment."""
    id: str = Field(..., description="The role assignment ID")
    principal: Principal = Field(..., description="The principal")
    role: WorkspaceRole = Field(..., description="The workspace role")


class WorkspaceRoleAssignments(BaseModel):
    """A list of workspace role assignments."""
    value: List[WorkspaceRoleAssignment] = Field(..., description="A list of workspace role assignments")
    continuation_token: Optional[str] = Field(None, alias="continuationToken", description="Token for the next result set batch")
    continuation_uri: Optional[str] = Field(None, alias="continuationUri", description="URI of the next result set batch")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AssignmentMethod",
    "Category",
    "ContributorsScopeType",
    "DelegatedFrom",
    "DomainRole",
    "ExternalDataShareStatus",
    "GitProviderType",
    "ItemPermissions",
    "ItemState",
    "SharingLinkType",
    "SharingLinksRemovalStatus",
    "Status",
    "TagScopeType",
    "TenantSettingPropertyType",
    "WorkspaceRole",
    "WorkspaceState",
    "WorkspaceType",
    # Models
    "AccessDetails",
    "AccessEntities",
    "BulkDeleteSharingLinksRequest",
    "BulkDeleteSharingLinksResponse",
    "ContributorsScope",
    "CreateDomainRequest",
    "Domain",
    "Domains",
    "DomainWorkspacesAssignment",
    "ExternalDataShare",
    "ExternalDataShares",
    "ItemAccessDetails",
    "ItemIdentifier",
    "ItemMetadata",
    "Items",
    "ModifyWorkspaceGitConnectionRequest",
    "ProvisionIdentity",
    "RoleAssignment",
    "RoleAssignments",
    "SensitivityLabel",
    "SetItemLabelRequest",
    "SetItemLabelsRequest",
    "ItemLabelRequest",
    "SetItemLabelsResponse",
    "ItemLabelResult",
    "SharingLinksRemovalResult",
    "Tag",
    "Tags",
    "TenantSetting",
    "TenantSettingProperty",
    "TenantSettings",
    "UpdateDomainRequest",
    "User",
    "Users",
    "WorkspaceGitConnectionDetails",
    "WorkspaceInfo",
    "Workspaces",
    "WorkspaceRoleAssignment",
    "WorkspaceRoleAssignments",
]
