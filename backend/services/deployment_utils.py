"""
Comprehensive Deployment Utilities for Microsoft Fabric
Provides dynamic, reusable deployment functions with extensive logging
"""
import httpx
import logging
import json
import base64
import asyncio
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class FabricDeploymentService:
    """
    Dynamic deployment service for Microsoft Fabric items
    Supports: Notebooks, Pipelines, Warehouses, Connections
    """

    def __init__(self, fabric_service):
        """
        Initialize deployment service

        Args:
            fabric_service: Instance of FabricAPIService for API calls
        """
        logger.info("[DEPLOYMENT SERVICE] Initializing Fabric Deployment Service")
        self.fabric_service = fabric_service
        self.base_url = fabric_service.base_url
        logger.info("[DEPLOYMENT SERVICE] [OK] Deployment service initialized")

    async def find_or_create_item(
        self,
        workspace_id: str,
        item_type: str,
        item_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Find an existing item or create it if it doesn't exist

        Args:
            workspace_id: Fabric workspace ID
            item_type: Type of item (Notebook, DataPipeline, Warehouse, Lakehouse)
            item_name: Display name of the item
            **kwargs: Additional creation parameters

        Returns:
            Dict with item details
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"[FIND/CREATE] Starting find or create for {item_type}: '{item_name}'")
        logger.info(f"[FIND/CREATE] Workspace ID: {workspace_id}")
        logger.info(f"{'='*80}")

        try:
            # Step 1: Try to find existing item
            logger.info(f"[FIND/CREATE] Step 1: Searching for existing {item_type}...")

            token = await self.fabric_service.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}

            list_url = f"{self.base_url}/workspaces/{workspace_id}/items"
            params = {"type": item_type}

            logger.debug(f"[FIND/CREATE] API URL: {list_url}")
            logger.debug(f"[FIND/CREATE] Query params: {params}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(list_url, headers=headers, params=params)

                if response.status_code == 200:
                    items = response.json().get("value", [])
                    logger.info(f"[FIND/CREATE] Found {len(items)} existing {item_type} items")

                    # Search for item by name
                    for item in items:
                        if item.get("displayName") == item_name:
                            item_id = item.get("id")
                            logger.info(f"[FIND/CREATE] [OK] Found existing {item_type}: {item_id}")
                            logger.info(f"[FIND/CREATE] Item details: {json.dumps(item, indent=2)[:300]}")
                            return {
                                "success": True,
                                "item": item,
                                "item_id": item_id,
                                "item_name": item_name,
                                "created": False,
                                "message": f"{item_type} '{item_name}' already exists"
                            }

                    logger.info(f"[FIND/CREATE] Item '{item_name}' not found in {len(items)} items")
                else:
                    logger.warning(f"[FIND/CREATE] List API returned {response.status_code}: {response.text[:200]}")

            # Step 2: Item not found, create it
            logger.info(f"[FIND/CREATE] Step 2: Creating new {item_type}...")

            create_url = f"{self.base_url}/workspaces/{workspace_id}/items"
            create_payload = {
                "displayName": item_name,
                "type": item_type
            }

            # Add any additional creation parameters
            if kwargs:
                logger.debug(f"[FIND/CREATE] Additional parameters: {json.dumps(kwargs, indent=2)}")
                create_payload.update(kwargs)

            logger.info(f"[FIND/CREATE] Creating {item_type} with payload:")
            logger.info(f"  Display Name: {item_name}")
            logger.info(f"  Type: {item_type}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                create_response = await client.post(
                    create_url,
                    headers={**headers, "Content-Type": "application/json"},
                    data=json.dumps(create_payload)
                )

                if create_response.status_code in [200, 201]:
                    item = create_response.json()
                    item_id = item.get("id")

                    logger.info(f"[FIND/CREATE] [OK] {item_type} created successfully!")
                    logger.info(f"[FIND/CREATE] Item ID: {item_id}")
                    logger.info(f"[FIND/CREATE] Item Name: {item_name}")

                    # Wait for item to provision
                    logger.info(f"[FIND/CREATE] Waiting 3 seconds for item to provision...")
                    await asyncio.sleep(3)

                    logger.info(f"{'='*80}\n")

                    return {
                        "success": True,
                        "item": item,
                        "item_id": item_id,
                        "item_name": item_name,
                        "created": True,
                        "message": f"{item_type} '{item_name}' created successfully"
                    }

                elif create_response.status_code == 409:
                    # Conflict - item was created between our check and creation
                    logger.warning(f"[FIND/CREATE] Conflict (409) - item may have been created concurrently")
                    logger.info(f"[FIND/CREATE] Retrying find operation...")

                    # Retry find
                    return await self.find_or_create_item(workspace_id, item_type, item_name, **kwargs)

                else:
                    error_msg = create_response.text
                    logger.error(f"[FIND/CREATE] [ERROR] Failed to create {item_type}")
                    logger.error(f"[FIND/CREATE] Status code: {create_response.status_code}")
                    logger.error(f"[FIND/CREATE] Error response: {error_msg}")

                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"Failed to create {item_type}: {error_msg}"
                    }

        except Exception as e:
            logger.error(f"[FIND/CREATE] [ERROR] Exception occurred: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception during find/create: {str(e)}"
            }

    async def deploy_notebook_with_lakehouse(
        self,
        workspace_id: str,
        notebook_name: str,
        python_code: str,
        lakehouse_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy a notebook with lakehouse attachment and optional parameters

        Args:
            workspace_id: Fabric workspace ID
            notebook_name: Name for the notebook
            python_code: Raw Python code to include in notebook
            lakehouse_id: ID of lakehouse to attach
            parameters: Optional default parameters for the notebook

        Returns:
            Dict with deployment status
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"[NOTEBOOK DEPLOY] Starting notebook deployment")
        logger.info(f"[NOTEBOOK DEPLOY] Notebook name: {notebook_name}")
        logger.info(f"[NOTEBOOK DEPLOY] Workspace ID: {workspace_id}")
        logger.info(f"[NOTEBOOK DEPLOY] Lakehouse ID: {lakehouse_id}")
        logger.info(f"[NOTEBOOK DEPLOY] Code length: {len(python_code)} characters")
        if parameters:
            logger.info(f"[NOTEBOOK DEPLOY] Parameters: {list(parameters.keys())}")
        logger.info(f"{'='*80}")

        try:
            # Step 1: Find or create notebook
            logger.info(f"[NOTEBOOK DEPLOY] Step 1: Finding or creating notebook...")
            result = await self.find_or_create_item(workspace_id, "Notebook", notebook_name)

            if not result["success"]:
                logger.error(f"[NOTEBOOK DEPLOY] [ERROR] Failed to create notebook")
                return result

            notebook_id = result["item_id"]
            logger.info(f"[NOTEBOOK DEPLOY] [OK] Notebook ready: {notebook_id}")

            # Step 2: Build notebook definition with lakehouse attachment
            logger.info(f"[NOTEBOOK DEPLOY] Step 2: Building notebook definition...")

            # Convert Python code to notebook cells
            logger.debug(f"[NOTEBOOK DEPLOY] Converting Python code to notebook cells...")
            source_lines = [line + '\n' for line in python_code.strip().split('\n')]

            # Build cells array
            cells = []

            # Add parameters cell if parameters provided
            if parameters:
                logger.info(f"[NOTEBOOK DEPLOY] Adding parameters cell with {len(parameters)} parameters")
                param_lines = ["# Parameters\n"]
                for key, value in parameters.items():
                    if isinstance(value, str):
                        param_lines.append(f"{key} = \"{value}\"\n")
                    else:
                        param_lines.append(f"{key} = {value}\n")

                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {"tags": ["parameters"]},
                    "outputs": [],
                    "source": param_lines
                })

            # Add main code cell
            logger.info(f"[NOTEBOOK DEPLOY] Adding main code cell with {len(source_lines)} lines")
            cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": source_lines
            })

            # Build notebook JSON with lakehouse attachment
            logger.info(f"[NOTEBOOK DEPLOY] Building notebook JSON with lakehouse attachment...")
            notebook_json = {
                "cells": cells,
                "metadata": {
                    "kernelspec": {
                        "display_name": "Synapse PySpark",
                        "language": "Python",
                        "name": "synapse_pyspark"
                    },
                    "language_info": {
                        "name": "python"
                    },
                    # Attach lakehouse
                    "defaultLakehouse": {
                        "id": lakehouse_id,
                        "defaultLakehouseArtifactId": lakehouse_id
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 2
            }

            logger.info(f"[NOTEBOOK DEPLOY] [OK] Notebook JSON built with lakehouse attachment")
            logger.debug(f"[NOTEBOOK DEPLOY] Notebook structure: {len(cells)} cells, lakehouse attached")

            # Step 3: Upload notebook definition
            logger.info(f"[NOTEBOOK DEPLOY] Step 3: Uploading notebook definition...")

            notebook_json_str = json.dumps(notebook_json)
            logger.debug(f"[NOTEBOOK DEPLOY] Notebook JSON size: {len(notebook_json_str)} characters")

            # Encode to base64
            notebook_bytes = notebook_json_str.encode("utf-8")
            notebook_base64 = base64.b64encode(notebook_bytes).decode("ascii")
            logger.debug(f"[NOTEBOOK DEPLOY] Encoded size: {len(notebook_base64)} characters")

            update_payload = {
                "definition": {
                    "parts": [
                        {
                            "path": "notebook-content.py",
                            "payload": notebook_base64,
                            "payloadType": "InlineBase64"
                        }
                    ]
                }
            }

            token = await self.fabric_service.get_access_token()
            update_url = f"{self.base_url}/workspaces/{workspace_id}/items/{notebook_id}/updateDefinition"

            logger.info(f"[NOTEBOOK DEPLOY] Uploading to Fabric API...")
            logger.debug(f"[NOTEBOOK DEPLOY] Update URL: {update_url}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    update_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    data=json.dumps(update_payload)
                )

                if response.status_code in [200, 202]:
                    logger.info(f"[NOTEBOOK DEPLOY] [OK] Notebook definition uploaded successfully!")
                    logger.info(f"[NOTEBOOK DEPLOY] Notebook ID: {notebook_id}")
                    logger.info(f"[NOTEBOOK DEPLOY] Notebook Name: {notebook_name}")
                    logger.info(f"[NOTEBOOK DEPLOY] Lakehouse attached: {lakehouse_id}")
                    logger.info(f"{'='*80}\n")

                    return {
                        "success": True,
                        "notebook_id": notebook_id,
                        "notebook_name": notebook_name,
                        "lakehouse_id": lakehouse_id,
                        "cells_count": len(cells),
                        "has_parameters": bool(parameters),
                        "message": f"Notebook '{notebook_name}' deployed successfully with lakehouse attachment"
                    }
                else:
                    error_msg = response.text
                    logger.error(f"[NOTEBOOK DEPLOY] [ERROR] Failed to upload notebook definition")
                    logger.error(f"[NOTEBOOK DEPLOY] Status code: {response.status_code}")
                    logger.error(f"[NOTEBOOK DEPLOY] Error response: {error_msg[:500]}")

                    return {
                        "success": False,
                        "notebook_id": notebook_id,
                        "error": error_msg,
                        "message": f"Failed to upload notebook definition: {error_msg}"
                    }

        except Exception as e:
            logger.error(f"[NOTEBOOK DEPLOY] [ERROR] Exception occurred: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception during notebook deployment: {str(e)}"
            }

    async def create_warehouse_connection(
        self,
        connection_name: str,
        warehouse_sql_endpoint: str,
        database_name: str
    ) -> Dict[str, Any]:
        """
        Create or get existing SQL connection to a Fabric Warehouse

        Args:
            connection_name: Name for the connection
            warehouse_sql_endpoint: SQL endpoint of the warehouse
            database_name: Database name to connect to

        Returns:
            Dict with connection details
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"[WAREHOUSE CONNECTION] Creating/finding warehouse connection")
        logger.info(f"[WAREHOUSE CONNECTION] Connection name: {connection_name}")
        logger.info(f"[WAREHOUSE CONNECTION] SQL endpoint: {warehouse_sql_endpoint}")
        logger.info(f"[WAREHOUSE CONNECTION] Database: {database_name}")
        logger.info(f"{'='*80}")

        try:
            token = await self.fabric_service.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Step 1: Check if connection already exists
            logger.info(f"[WAREHOUSE CONNECTION] Step 1: Checking for existing connection...")

            list_url = f"{self.base_url}/connections"
            logger.debug(f"[WAREHOUSE CONNECTION] List URL: {list_url}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                list_response = await client.get(list_url, headers=headers)

                if list_response.status_code == 200:
                    connections = list_response.json().get("value", [])
                    logger.info(f"[WAREHOUSE CONNECTION] Found {len(connections)} existing connections")

                    # Search for connection by name
                    for conn in connections:
                        if conn.get("displayName") == connection_name:
                            conn_id = conn.get("id")
                            logger.info(f"[WAREHOUSE CONNECTION] [OK] Found existing connection: {conn_id}")
                            logger.info(f"{'='*80}\n")
                            return {
                                "success": True,
                                "connection_id": conn_id,
                                "connection_name": connection_name,
                                "created": False,
                                "message": f"Connection '{connection_name}' already exists"
                            }

                    logger.info(f"[WAREHOUSE CONNECTION] Connection not found, creating new one...")
                else:
                    logger.warning(f"[WAREHOUSE CONNECTION] List failed: {list_response.status_code}")

                # Step 2: Create new connection
                logger.info(f"[WAREHOUSE CONNECTION] Step 2: Creating new SQL connection...")

                create_payload = {
                    "connectivityType": "ShareableCloud",
                    "displayName": connection_name,
                    "connectionDetails": {
                        "type": "SQL",
                        "creationMethod": "Sql",
                        "parameters": [
                            {
                                "dataType": "Text",
                                "name": "server",
                                "value": warehouse_sql_endpoint
                            },
                            {
                                "dataType": "Text",
                                "name": "database",
                                "value": database_name
                            }
                        ]
                    },
                    "privacyLevel": "Organizational",
                    "credentialDetails": {
                        "singleSignOnType": "None",
                        "connectionEncryption": "NotEncrypted",
                        "skipTestConnection": False,
                        "credentials": {
                            "credentialType": "ServicePrincipal",
                            "servicePrincipalClientId": self.fabric_service.client_id,
                            "servicePrincipalSecret": self.fabric_service.client_secret,
                            "tenantId": self.fabric_service.tenant_id
                        }
                    }
                }

                logger.info(f"[WAREHOUSE CONNECTION] Creating connection with Service Principal auth...")
                logger.debug(f"[WAREHOUSE CONNECTION] Payload: {json.dumps({k: v for k, v in create_payload.items() if k != 'credentialDetails'}, indent=2)}")

                create_response = await client.post(list_url, headers=headers, data=json.dumps(create_payload))

                if create_response.status_code in [200, 201]:
                    connection = create_response.json()
                    conn_id = connection.get("id")

                    logger.info(f"[WAREHOUSE CONNECTION] [OK] Connection created successfully!")
                    logger.info(f"[WAREHOUSE CONNECTION] Connection ID: {conn_id}")
                    logger.info(f"[WAREHOUSE CONNECTION] Connection Name: {connection_name}")
                    logger.info(f"{'='*80}\n")

                    return {
                        "success": True,
                        "connection_id": conn_id,
                        "connection_name": connection_name,
                        "created": True,
                        "message": f"Connection '{connection_name}' created successfully"
                    }
                else:
                    error_msg = create_response.text
                    logger.error(f"[WAREHOUSE CONNECTION] [ERROR] Failed to create connection")
                    logger.error(f"[WAREHOUSE CONNECTION] Status code: {create_response.status_code}")
                    logger.error(f"[WAREHOUSE CONNECTION] Error response: {error_msg}")

                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"Failed to create connection: {error_msg}"
                    }

        except Exception as e:
            logger.error(f"[WAREHOUSE CONNECTION] [ERROR] Exception occurred: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception during connection creation: {str(e)}"
            }

    async def get_warehouse_sql_endpoint(
        self,
        workspace_id: str,
        warehouse_id: str
    ) -> Optional[str]:
        """
        Get SQL endpoint from warehouse properties

        Args:
            workspace_id: Fabric workspace ID
            warehouse_id: Warehouse item ID

        Returns:
            SQL endpoint string or None if not found
        """
        logger.info(f"[WAREHOUSE ENDPOINT] Getting SQL endpoint for warehouse: {warehouse_id}")

        try:
            token = await self.fabric_service.get_access_token()
            url = f"{self.base_url}/workspaces/{workspace_id}/warehouses/{warehouse_id}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 200:
                    warehouse_props = response.json()
                    sql_endpoint = warehouse_props.get("properties", {}).get("connectionString")

                    if sql_endpoint:
                        logger.info(f"[WAREHOUSE ENDPOINT] [OK] SQL endpoint: {sql_endpoint}")
                        return sql_endpoint
                    else:
                        logger.error(f"[WAREHOUSE ENDPOINT] [ERROR] No SQL endpoint found in response")
                        return None
                else:
                    logger.error(f"[WAREHOUSE ENDPOINT] [ERROR] Failed to get warehouse: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"[WAREHOUSE ENDPOINT] [ERROR] Exception: {str(e)}", exc_info=True)
            return None
