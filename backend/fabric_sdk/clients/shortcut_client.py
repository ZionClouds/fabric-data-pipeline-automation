"""
Shortcut Client for Microsoft Fabric SDK

Provides async operations for OneLake shortcut management.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List

from fabric_sdk.clients.base_client import FabricBaseClient
from fabric_sdk.models.core import (
    CreateShortcutRequest,
    CreateShortcutWithTransformRequest,
    Shortcut,
    Shortcuts,
    ShortcutTarget,
    AzureBlobStorage,
    AdlsGen2,
    AmazonS3,
    OneLakeTarget,
)

logger = logging.getLogger(__name__)


class ShortcutClient(FabricBaseClient):
    """
    Client for OneLake Shortcut operations in Microsoft Fabric.

    Shortcuts allow accessing external data without copying.
    """

    async def list_shortcuts(
        self,
        workspace_id: str,
        item_id: str,
        parent_path: Optional[str] = None
    ) -> Shortcuts:
        """
        List shortcuts in a lakehouse.

        Args:
            workspace_id: Fabric workspace ID
            item_id: Lakehouse item ID
            parent_path: Optional parent path filter

        Returns:
            Shortcuts object with list of shortcuts
        """
        endpoint = f"/workspaces/{workspace_id}/items/{item_id}/shortcuts"
        params = {}
        if parent_path:
            params["parentPath"] = parent_path

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, Shortcuts)

    async def get_shortcut(
        self,
        workspace_id: str,
        item_id: str,
        shortcut_path: str,
        shortcut_name: str
    ) -> Shortcut:
        """
        Get a specific shortcut.

        Args:
            workspace_id: Fabric workspace ID
            item_id: Lakehouse item ID
            shortcut_path: Path (Files or Tables)
            shortcut_name: Shortcut name

        Returns:
            Shortcut object
        """
        endpoint = f"/workspaces/{workspace_id}/items/{item_id}/shortcuts/{shortcut_path}/{shortcut_name}"
        response = await self.get(endpoint)
        return self._parse_response(response, Shortcut)

    async def create_shortcut(
        self,
        workspace_id: str,
        item_id: str,
        shortcut_name: str,
        shortcut_path: str,
        target: ShortcutTarget
    ) -> Dict[str, Any]:
        """
        Create a new shortcut.

        Args:
            workspace_id: Fabric workspace ID
            item_id: Lakehouse item ID
            shortcut_name: Shortcut name
            shortcut_path: Path (Files or Tables)
            target: Shortcut target configuration

        Returns:
            Dict with shortcut creation result
        """
        endpoint = f"/workspaces/{workspace_id}/items/{item_id}/shortcuts"

        payload = {
            "name": shortcut_name,
            "path": shortcut_path,
            "target": target.model_dump(by_alias=True, exclude_none=True)
        }

        response = await self.post(endpoint, json_data=payload)
        result = self._handle_response(response, [200, 201])

        logger.info(f"Shortcut created: {shortcut_name} at {shortcut_path}")

        return {
            "success": True,
            "shortcut_name": shortcut_name,
            "shortcut_path": shortcut_path,
            "item_id": item_id
        }

    async def create_azure_blob_shortcut(
        self,
        workspace_id: str,
        lakehouse_id: str,
        shortcut_name: str,
        connection_id: str,
        storage_account_name: str,
        container: str,
        subpath: str = "",
        target_location: str = "Files"
    ) -> Dict[str, Any]:
        """
        Create a shortcut to Azure Blob Storage.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse item ID
            shortcut_name: Shortcut name
            connection_id: Connection ID for the storage account
            storage_account_name: Storage account name
            container: Container name
            subpath: Optional subpath within container
            target_location: "Files" or "Tables"

        Returns:
            Dict with shortcut creation result
        """
        location = f"https://{storage_account_name}.blob.core.windows.net"
        full_subpath = f"/{container}/{subpath}".rstrip("/") if subpath else f"/{container}"

        target = ShortcutTarget(
            azure_blob_storage=AzureBlobStorage(
                connection_id=connection_id,
                location=location,
                subpath=full_subpath
            )
        )

        return await self.create_shortcut(
            workspace_id=workspace_id,
            item_id=lakehouse_id,
            shortcut_name=shortcut_name,
            shortcut_path=target_location,
            target=target
        )

    async def create_adls_shortcut(
        self,
        workspace_id: str,
        lakehouse_id: str,
        shortcut_name: str,
        connection_id: str,
        storage_account_name: str,
        container: str,
        subpath: str = "",
        target_location: str = "Files"
    ) -> Dict[str, Any]:
        """
        Create a shortcut to ADLS Gen2.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse item ID
            shortcut_name: Shortcut name
            connection_id: Connection ID for the storage account
            storage_account_name: Storage account name
            container: Container/filesystem name
            subpath: Optional subpath
            target_location: "Files" or "Tables"

        Returns:
            Dict with shortcut creation result
        """
        location = f"https://{storage_account_name}.dfs.core.windows.net"
        full_subpath = f"/{container}/{subpath}".rstrip("/") if subpath else f"/{container}"

        target = ShortcutTarget(
            adls_gen2=AdlsGen2(
                connection_id=connection_id,
                location=location,
                subpath=full_subpath
            )
        )

        return await self.create_shortcut(
            workspace_id=workspace_id,
            item_id=lakehouse_id,
            shortcut_name=shortcut_name,
            shortcut_path=target_location,
            target=target
        )

    async def create_s3_shortcut(
        self,
        workspace_id: str,
        lakehouse_id: str,
        shortcut_name: str,
        connection_id: str,
        bucket_name: str,
        region: str,
        subpath: str = "",
        target_location: str = "Files"
    ) -> Dict[str, Any]:
        """
        Create a shortcut to Amazon S3.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse item ID
            shortcut_name: Shortcut name
            connection_id: Connection ID for S3
            bucket_name: S3 bucket name
            region: AWS region
            subpath: Optional prefix/subpath
            target_location: "Files" or "Tables"

        Returns:
            Dict with shortcut creation result
        """
        location = f"https://{bucket_name}.s3.{region}.amazonaws.com"

        target = ShortcutTarget(
            amazon_s3=AmazonS3(
                connection_id=connection_id,
                location=location,
                subpath=subpath if subpath else None
            )
        )

        return await self.create_shortcut(
            workspace_id=workspace_id,
            item_id=lakehouse_id,
            shortcut_name=shortcut_name,
            shortcut_path=target_location,
            target=target
        )

    async def create_onelake_shortcut(
        self,
        workspace_id: str,
        lakehouse_id: str,
        shortcut_name: str,
        target_workspace_id: str,
        target_item_id: str,
        target_path: str,
        target_location: str = "Files"
    ) -> Dict[str, Any]:
        """
        Create a shortcut to another OneLake location.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse item ID
            shortcut_name: Shortcut name
            target_workspace_id: Target workspace ID
            target_item_id: Target item ID
            target_path: Path within target item
            target_location: "Files" or "Tables"

        Returns:
            Dict with shortcut creation result
        """
        target = ShortcutTarget(
            one_lake=OneLakeTarget(
                workspace_id=target_workspace_id,
                item_id=target_item_id,
                path=target_path
            )
        )

        return await self.create_shortcut(
            workspace_id=workspace_id,
            item_id=lakehouse_id,
            shortcut_name=shortcut_name,
            shortcut_path=target_location,
            target=target
        )

    async def delete_shortcut(
        self,
        workspace_id: str,
        item_id: str,
        shortcut_path: str,
        shortcut_name: str
    ) -> Dict[str, Any]:
        """
        Delete a shortcut.

        Args:
            workspace_id: Fabric workspace ID
            item_id: Lakehouse item ID
            shortcut_path: Path (Files or Tables)
            shortcut_name: Shortcut name

        Returns:
            Dict with deletion status
        """
        endpoint = f"/workspaces/{workspace_id}/items/{item_id}/shortcuts/{shortcut_path}/{shortcut_name}"
        response = await self.delete(endpoint)

        if response.status_code == 200:
            return {"success": True, "shortcut_name": shortcut_name}
        else:
            raise Exception(f"Failed to delete shortcut: {response.text}")
