"""
Lakehouse Client for Microsoft Fabric SDK

Provides async operations for lakehouse management.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List

from fabric_sdk.clients.base_client import FabricBaseClient
from fabric_sdk.models.lakehouse import (
    CreateLakehouseRequest,
    Lakehouse,
    Lakehouses,
    UpdateLakehouseRequest,
    Tables,
    LoadTableRequest,
    RunOnDemandTableMaintenanceRequest,
)

logger = logging.getLogger(__name__)


class LakehouseClient(FabricBaseClient):
    """
    Client for Lakehouse operations in Microsoft Fabric.

    Supports creating, managing, and querying lakehouses and tables.
    """

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    async def list_lakehouses(
        self,
        workspace_id: str,
        continuation_token: Optional[str] = None
    ) -> Lakehouses:
        """
        List all lakehouses in a workspace.

        Args:
            workspace_id: Fabric workspace ID
            continuation_token: Token for pagination

        Returns:
            Lakehouses object with list of lakehouses
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, Lakehouses)

    async def get_lakehouse(
        self,
        workspace_id: str,
        lakehouse_id: str
    ) -> Lakehouse:
        """
        Get a specific lakehouse.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID

        Returns:
            Lakehouse object
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}"
        response = await self.get(endpoint)
        return self._parse_response(response, Lakehouse)

    async def create_lakehouse(
        self,
        workspace_id: str,
        display_name: str,
        description: Optional[str] = None,
        enable_schemas: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new lakehouse.

        Args:
            workspace_id: Fabric workspace ID
            display_name: Lakehouse display name
            description: Optional description
            enable_schemas: Create schema-enabled lakehouse

        Returns:
            Dict with lakehouse_id and creation info
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses"

        payload = {
            "displayName": display_name,
        }

        if description:
            payload["description"] = description

        if enable_schemas:
            payload["creationPayload"] = {"enableSchemas": True}

        response = await self.post(endpoint, json_data=payload)
        result = self._handle_response(response, [200, 201, 202])

        logger.info(f"Lakehouse created: {result.get('id', display_name)}")

        return {
            "success": True,
            "lakehouse_id": result.get("id"),
            "lakehouse_name": display_name,
            "workspace_id": workspace_id
        }

    async def update_lakehouse(
        self,
        workspace_id: str,
        lakehouse_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a lakehouse's metadata.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID
            display_name: New display name
            description: New description

        Returns:
            Dict with update status
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}"

        payload = {}
        if display_name:
            payload["displayName"] = display_name
        if description is not None:
            payload["description"] = description

        response = await self.patch(endpoint, json_data=payload)
        self._handle_response(response)

        logger.info(f"Lakehouse updated: {lakehouse_id}")

        return {
            "success": True,
            "lakehouse_id": lakehouse_id
        }

    async def delete_lakehouse(
        self,
        workspace_id: str,
        lakehouse_id: str
    ) -> Dict[str, Any]:
        """
        Delete a lakehouse.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID

        Returns:
            Dict with deletion status
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}"
        response = await self.delete(endpoint)

        if response.status_code == 200:
            logger.info(f"Lakehouse deleted: {lakehouse_id}")
            return {"success": True, "lakehouse_id": lakehouse_id}
        else:
            raise Exception(f"Failed to delete lakehouse: {response.text}")

    # =========================================================================
    # TABLE OPERATIONS
    # =========================================================================

    async def list_tables(
        self,
        workspace_id: str,
        lakehouse_id: str,
        continuation_token: Optional[str] = None
    ) -> Tables:
        """
        List all tables in a lakehouse.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID
            continuation_token: Token for pagination

        Returns:
            Tables object with list of tables
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}/tables"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, Tables)

    async def load_table(
        self,
        workspace_id: str,
        lakehouse_id: str,
        table_name: str,
        path_type: str,
        relative_path: str,
        mode: str = "Overwrite",
        file_extension: Optional[str] = None,
        recursive: bool = False,
        format_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load data into a lakehouse table.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID
            table_name: Target table name
            path_type: "File" or "Folder"
            relative_path: Path to data file/folder
            mode: "Overwrite" or "Append"
            file_extension: File extension filter
            recursive: Search recursively in folder
            format_options: Format configuration (CSV options, etc.)

        Returns:
            Dict with load operation status
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}/tables/{table_name}/load"

        payload = {
            "pathType": path_type,
            "relativePath": relative_path,
            "mode": mode
        }

        if file_extension:
            payload["fileExtension"] = file_extension
        if recursive:
            payload["recursive"] = recursive
        if format_options:
            payload["formatOptions"] = format_options

        response = await self.post(endpoint, json_data=payload, timeout=300.0)
        self._handle_response(response, [200, 202])

        logger.info(f"Table load initiated: {table_name}")

        return {
            "success": True,
            "lakehouse_id": lakehouse_id,
            "table_name": table_name
        }

    # =========================================================================
    # TABLE MAINTENANCE
    # =========================================================================

    async def run_table_maintenance(
        self,
        workspace_id: str,
        lakehouse_id: str,
        table_name: str,
        schema_name: Optional[str] = None,
        optimize_v_order: bool = True,
        z_order_columns: Optional[List[str]] = None,
        vacuum_retention_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run table maintenance (optimize and vacuum).

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID
            table_name: Table name
            schema_name: Schema name (for schema-enabled lakehouse)
            optimize_v_order: Enable V-Order optimization
            z_order_columns: Columns for Z-Order
            vacuum_retention_period: Retention period (d:hh:mm:ss format)

        Returns:
            Dict with maintenance job status
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}/jobs/instances"
        params = {"jobType": "TableMaintenance"}

        execution_data = {
            "tableName": table_name
        }

        if schema_name:
            execution_data["schemaName"] = schema_name

        optimize_settings = {}
        if optimize_v_order:
            optimize_settings["vOrder"] = True
        if z_order_columns:
            optimize_settings["zOrderBy"] = z_order_columns
        if optimize_settings:
            execution_data["optimizeSettings"] = optimize_settings

        if vacuum_retention_period:
            execution_data["vacuumSettings"] = {
                "retentionPeriod": vacuum_retention_period
            }

        payload = {"executionData": execution_data}

        response = await self._request("POST", endpoint, json_data=payload, params=params)
        result = self._handle_response(response, [200, 202])

        logger.info(f"Table maintenance started: {table_name}")

        return {
            "success": True,
            "lakehouse_id": lakehouse_id,
            "table_name": table_name,
            "job_instance_id": result.get("id")
        }

    # =========================================================================
    # SQL ENDPOINT
    # =========================================================================

    async def get_sql_endpoint(
        self,
        workspace_id: str,
        lakehouse_id: str
    ) -> Dict[str, Any]:
        """
        Get SQL endpoint details for a lakehouse.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID

        Returns:
            Dict with SQL endpoint information
        """
        lakehouse = await self.get_lakehouse(workspace_id, lakehouse_id)

        if lakehouse.properties and lakehouse.properties.sql_endpoint_properties:
            props = lakehouse.properties.sql_endpoint_properties
            return {
                "success": True,
                "lakehouse_id": lakehouse_id,
                "lakehouse_name": lakehouse.display_name,
                "sql_endpoint_id": props.id,
                "connection_string": props.connection_string,
                "provisioning_status": props.provisioning_status.value if props.provisioning_status else None
            }
        else:
            return {
                "success": False,
                "error": "SQL endpoint not available",
                "lakehouse_id": lakehouse_id
            }

    # =========================================================================
    # LIVY SESSIONS
    # =========================================================================

    async def list_livy_sessions(
        self,
        workspace_id: str,
        lakehouse_id: str,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List Livy sessions for a lakehouse.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID
            continuation_token: Token for pagination

        Returns:
            Dict with list of Livy sessions
        """
        endpoint = f"/workspaces/{workspace_id}/lakehouses/{lakehouse_id}/livySessions"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._handle_response(response)
