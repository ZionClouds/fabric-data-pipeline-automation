"""
Workspace Client for Microsoft Fabric SDK

Provides async operations for workspace management.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List

from fabric_sdk.clients.base_client import FabricBaseClient
from fabric_sdk.models.core import (
    CreateWorkspaceRequest,
    Workspace,
    Workspaces,
    UpdateWorkspaceRequest,
    Item,
    Items,
    ItemType,
)

logger = logging.getLogger(__name__)


class WorkspaceClient(FabricBaseClient):
    """
    Client for Workspace operations in Microsoft Fabric.

    Supports creating, managing workspaces and listing items.
    """

    async def list_workspaces(
        self,
        continuation_token: Optional[str] = None
    ) -> Workspaces:
        """
        List all workspaces accessible to the service principal.

        Args:
            continuation_token: Token for pagination

        Returns:
            Workspaces object with list of workspaces
        """
        endpoint = "/workspaces"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, Workspaces)

    async def get_workspace(self, workspace_id: str) -> Workspace:
        """
        Get a specific workspace.

        Args:
            workspace_id: Fabric workspace ID

        Returns:
            Workspace object
        """
        endpoint = f"/workspaces/{workspace_id}"
        response = await self.get(endpoint)
        return self._parse_response(response, Workspace)

    async def create_workspace(
        self,
        display_name: str,
        description: Optional[str] = None,
        capacity_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new workspace.

        Args:
            display_name: Workspace display name
            description: Optional description
            capacity_id: Optional capacity ID to assign

        Returns:
            Dict with workspace_id and creation info
        """
        endpoint = "/workspaces"

        payload = {
            "displayName": display_name,
        }

        if description:
            payload["description"] = description
        if capacity_id:
            payload["capacityId"] = capacity_id

        response = await self.post(endpoint, json_data=payload)
        result = self._handle_response(response, [200, 201, 202])

        logger.info(f"Workspace created: {result.get('id', display_name)}")

        return {
            "success": True,
            "workspace_id": result.get("id"),
            "workspace_name": display_name
        }

    async def update_workspace(
        self,
        workspace_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a workspace's metadata.

        Args:
            workspace_id: Fabric workspace ID
            display_name: New display name
            description: New description

        Returns:
            Dict with update status
        """
        endpoint = f"/workspaces/{workspace_id}"

        payload = {}
        if display_name:
            payload["displayName"] = display_name
        if description is not None:
            payload["description"] = description

        response = await self.patch(endpoint, json_data=payload)
        self._handle_response(response)

        return {"success": True, "workspace_id": workspace_id}

    async def delete_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """
        Delete a workspace.

        Args:
            workspace_id: Fabric workspace ID

        Returns:
            Dict with deletion status
        """
        endpoint = f"/workspaces/{workspace_id}"
        response = await self.delete(endpoint)

        if response.status_code == 200:
            return {"success": True, "workspace_id": workspace_id}
        else:
            raise Exception(f"Failed to delete workspace: {response.text}")

    # =========================================================================
    # ITEM LISTING
    # =========================================================================

    async def list_items(
        self,
        workspace_id: str,
        item_type: Optional[ItemType] = None,
        continuation_token: Optional[str] = None
    ) -> Items:
        """
        List all items in a workspace.

        Args:
            workspace_id: Fabric workspace ID
            item_type: Optional filter by item type
            continuation_token: Token for pagination

        Returns:
            Items object with list of items
        """
        endpoint = f"/workspaces/{workspace_id}/items"
        params = {}
        if item_type:
            params["type"] = item_type.value
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, Items)

    async def list_lakehouses(self, workspace_id: str) -> List[Item]:
        """List all lakehouses in a workspace."""
        items = await self.list_items(workspace_id, ItemType.LAKEHOUSE)
        return items.value

    async def list_warehouses(self, workspace_id: str) -> List[Item]:
        """List all warehouses in a workspace."""
        items = await self.list_items(workspace_id, ItemType.WAREHOUSE)
        return items.value

    async def list_notebooks(self, workspace_id: str) -> List[Item]:
        """List all notebooks in a workspace."""
        items = await self.list_items(workspace_id, ItemType.NOTEBOOK)
        return items.value

    async def list_data_pipelines(self, workspace_id: str) -> List[Item]:
        """List all data pipelines in a workspace."""
        items = await self.list_items(workspace_id, ItemType.DATA_PIPELINE)
        return items.value

    async def list_semantic_models(self, workspace_id: str) -> List[Item]:
        """List all semantic models in a workspace."""
        items = await self.list_items(workspace_id, ItemType.SEMANTIC_MODEL)
        return items.value

    async def list_reports(self, workspace_id: str) -> List[Item]:
        """List all reports in a workspace."""
        items = await self.list_items(workspace_id, ItemType.REPORT)
        return items.value

    # =========================================================================
    # CAPACITY ASSIGNMENT
    # =========================================================================

    async def assign_to_capacity(
        self,
        workspace_id: str,
        capacity_id: str
    ) -> Dict[str, Any]:
        """
        Assign a workspace to a capacity.

        Args:
            workspace_id: Fabric workspace ID
            capacity_id: Capacity ID to assign

        Returns:
            Dict with assignment status
        """
        endpoint = f"/workspaces/{workspace_id}/assignToCapacity"

        payload = {"capacityId": capacity_id}

        response = await self.post(endpoint, json_data=payload)
        self._handle_response(response, [200, 202])

        return {
            "success": True,
            "workspace_id": workspace_id,
            "capacity_id": capacity_id
        }

    async def unassign_from_capacity(self, workspace_id: str) -> Dict[str, Any]:
        """
        Unassign a workspace from its capacity.

        Args:
            workspace_id: Fabric workspace ID

        Returns:
            Dict with unassignment status
        """
        endpoint = f"/workspaces/{workspace_id}/unassignFromCapacity"

        response = await self.post(endpoint)
        self._handle_response(response, [200, 202])

        return {"success": True, "workspace_id": workspace_id}
