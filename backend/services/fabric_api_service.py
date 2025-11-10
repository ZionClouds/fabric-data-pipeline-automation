"""
Microsoft Fabric API Service for deploying pipelines and notebooks
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
import json
import settings

logger = logging.getLogger(__name__)

class FabricAPIService:
    """
    Service for interacting with Microsoft Fabric REST API
    """

    def __init__(self):
        self.base_url = "https://api.fabric.microsoft.com/v1"
        self.client_id = settings.FABRIC_CLIENT_ID
        self.client_secret = settings.FABRIC_CLIENT_SECRET
        self.tenant_id = settings.FABRIC_TENANT_ID
        self.access_token = None

    async def get_access_token(self) -> str:
        """
        Get OAuth2 access token for Fabric API
        Note: Token is fetched fresh each time to avoid expiration issues
        """
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://api.fabric.microsoft.com/.default",
            "grant_type": "client_credentials"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["access_token"]
            logger.info("Successfully obtained fresh Fabric API access token")
            return access_token

    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all Microsoft Fabric workspaces accessible to the service principal

        Returns:
            List of workspace dictionaries with id, displayName, description, type, capacityId
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Microsoft Fabric API endpoint to list workspaces
            list_url = f"{self.base_url}/workspaces"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(list_url, headers=headers)
                response.raise_for_status()

                data = response.json()
                workspaces = data.get("value", [])

                logger.info(f"Successfully fetched {len(workspaces)} workspaces from Fabric API")

                return workspaces

        except Exception as e:
            logger.error(f"Error fetching workspaces from Fabric API: {str(e)}")
            raise

    async def get_workspace_lakehouses(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all lakehouses in a workspace

        Args:
            workspace_id: Fabric workspace ID

        Returns:
            List of lakehouse dictionaries with id, displayName, type
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Get all items in workspace filtered by Lakehouse type
            list_url = f"{self.base_url}/workspaces/{workspace_id}/items?type=Lakehouse"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(list_url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    lakehouses = data.get("value", [])
                    logger.info(f"Found {len(lakehouses)} lakehouse(s) in workspace {workspace_id}")
                    return lakehouses
                else:
                    logger.error(f"Error fetching lakehouses: {response.status_code} - {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching lakehouses from workspace: {str(e)}")
            return []

    async def get_workspace_warehouses(self, workspace_id: str) -> List[Dict[str, Any]]:
        """
        Get all warehouses in a workspace

        Args:
            workspace_id: Fabric workspace ID

        Returns:
            List of warehouse dictionaries with id, displayName, type
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Get all items in workspace filtered by Warehouse type
            list_url = f"{self.base_url}/workspaces/{workspace_id}/items?type=Warehouse"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(list_url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    warehouses = data.get("value", [])
                    logger.info(f"Found {len(warehouses)} warehouse(s) in workspace {workspace_id}")
                    return warehouses
                else:
                    logger.error(f"Error fetching warehouses: {response.status_code} - {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching warehouses from workspace: {str(e)}")
            return []

    async def get_lakehouse_shortcuts(self, workspace_id: str, lakehouse_id: str) -> Dict[str, Any]:
        """
        Get all shortcuts in a lakehouse

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID

        Returns:
            Dict with success status and list of shortcuts
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Get shortcuts from lakehouse
            shortcuts_url = f"{self.base_url}/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(shortcuts_url, headers=headers)

                if response.status_code == 200:
                    shortcuts_data = response.json()
                    shortcuts = shortcuts_data.get("value", [])

                    logger.info(f"Found {len(shortcuts)} shortcut(s) in lakehouse")

                    return {
                        "success": True,
                        "shortcuts": shortcuts,
                        "count": len(shortcuts)
                    }
                else:
                    logger.warning(f"Could not fetch shortcuts: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "shortcuts": [],
                        "error": f"Failed to fetch shortcuts: {response.status_code}"
                    }

        except Exception as e:
            logger.error(f"Error fetching lakehouse shortcuts: {str(e)}")
            return {
                "success": False,
                "shortcuts": [],
                "error": str(e)
            }

    async def get_lakehouse_sql_endpoint(self, workspace_id: str, lakehouse_id: str) -> Dict[str, Any]:
        """
        Get Lakehouse SQL endpoint connection string

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID

        Returns:
            Dict with SQL endpoint details
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Get lakehouse details
            details_url = f"{self.base_url}/workspaces/{workspace_id}/lakehouses/{lakehouse_id}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(details_url, headers=headers)

                if response.status_code == 200:
                    lakehouse_data = response.json()
                    lakehouse_name = lakehouse_data.get("displayName", "")

                    # Construct SQL endpoint connection string
                    # Format: Server={workspace-id}.datawarehouse.fabric.microsoft.com;Initial Catalog={lakehouse-name}
                    sql_endpoint = f"{workspace_id}.datawarehouse.fabric.microsoft.com"

                    connection_string = (
                        f"Server={sql_endpoint};"
                        f"Initial Catalog={lakehouse_name};"
                        f"Authentication=Active Directory Service Principal;"
                        f"User ID={self.client_id};"
                        f"Password={self.client_secret};"
                        f"Encrypt=True;"
                    )

                    logger.info(f"Generated SQL endpoint for lakehouse: {lakehouse_name}")

                    return {
                        "success": True,
                        "lakehouse_name": lakehouse_name,
                        "lakehouse_id": lakehouse_id,
                        "sql_endpoint": sql_endpoint,
                        "connection_string": connection_string
                    }
                else:
                    logger.error(f"Error fetching lakehouse details: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Failed to get lakehouse details: {response.text}"
                    }

        except Exception as e:
            logger.error(f"Error getting lakehouse SQL endpoint: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_lakehouse_table(
        self,
        workspace_id: str,
        lakehouse_id: str,
        table_name: str,
        schema: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Create a table in Lakehouse by loading initial data structure

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID
            table_name: Name of table to create
            schema: List of column definitions [{"name": "col1", "type": "string"}, ...]

        Returns:
            Dict with success status and details
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Create table by loading from an empty/initial file structure
            # Note: In Fabric, tables are typically created via Spark/SQL
            # This method prepares for table creation

            logger.info(f"Table '{table_name}' structure prepared with schema: {schema}")

            # Return info for Script activity to create table via SQL
            return {
                "success": True,
                "table_name": table_name,
                "schema": schema,
                "create_sql": self._generate_create_table_sql(table_name, schema),
                "message": "Use Script activity with SQL endpoint to create table"
            }

        except Exception as e:
            logger.error(f"Error preparing table creation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_create_table_sql(self, table_name: str, schema: List[Dict[str, str]]) -> str:
        """
        Generate CREATE TABLE SQL statement

        Args:
            table_name: Table name
            schema: Column definitions

        Returns:
            SQL CREATE TABLE statement
        """
        columns = []
        for col in schema:
            col_name = col.get("name")
            col_type = col.get("type", "STRING")
            columns.append(f"    {col_name} {col_type}")

        columns_sql = ",\n".join(columns)

        sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
{columns_sql}
);"""

        return sql

    def _generate_script_activity(
        self,
        activity_name: str,
        sql_query: str,
        database: str = None,
        connection_id: str = None,
        sql_connection_string: str = None,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate Script activity with SQL endpoint connection

        Args:
            activity_name: Name of the Script activity
            sql_query: SQL query to execute (can be Expression type)
            database: Database name (optional)
            connection_id: Connection ID for externalReferences (modern approach)
            sql_connection_string: SQL endpoint connection string (legacy approach)
            depends_on: List of activity names this depends on

        Returns:
            Script activity JSON definition
        """
        # Handle both string queries and Expression objects
        if isinstance(sql_query, str):
            sql_text = sql_query
        elif isinstance(sql_query, dict) and "value" in sql_query:
            sql_text = sql_query  # Already in Expression format
        else:
            sql_text = sql_query

        activity = {
            "name": activity_name,
            "type": "Script",
            "dependsOn": self._format_depends_on(depends_on) if depends_on else [],
            "policy": {
                "timeout": "0.12:00:00",
                "retry": 0,
                "retryIntervalInSeconds": 30,
                "secureOutput": False,
                "secureInput": False
            },
            "typeProperties": {
                "scripts": [
                    {
                        "type": "Query",
                        "text": sql_text if isinstance(sql_text, dict) else {
                            "value": sql_text,
                            "type": "Expression"
                        }
                    }
                ],
                "scriptBlockExecutionTimeout": "02:00:00"
            }
        }

        # Add database if provided
        if database:
            activity["typeProperties"]["database"] = database

        # Use externalReferences if connection_id provided (modern approach)
        if connection_id:
            activity["externalReferences"] = {
                "connection": connection_id
            }
        # Fall back to linkedService if connection string provided (legacy)
        elif sql_connection_string:
            activity["typeProperties"]["linkedService"] = {
                "referenceName": "SQLEndpointConnection",
                "type": "LinkedServiceReference",
                "parameters": {
                    "connectionString": sql_connection_string
                }
            }

        return activity

    def _generate_get_metadata_activity(
        self,
        activity_name: str,
        workspace_id: str = None,
        lakehouse_id: str = None,
        folder_path: str = None,
        dataset_name: str = None,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate Get Metadata activity with inline Lakehouse connection

        Args:
            activity_name: Name of the activity
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse artifact ID
            folder_path: Path relative to Files/ (e.g., "bronze")
            dataset_name: Name of the dataset to reference (legacy support)
            depends_on: List of activity names this depends on

        Returns:
            Get Metadata activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "GetMetadata",
            "dependsOn": self._format_depends_on(depends_on) if depends_on else [],
            "policy": {
                "timeout": "0.12:00:00",
                "retry": 0,
                "retryIntervalInSeconds": 30,
                "secureOutput": False,
                "secureInput": False
            },
            "typeProperties": {
                "fieldList": ["childItems"]
            }
        }

        # Use inline Lakehouse datasetSettings (modern approach)
        if workspace_id and lakehouse_id:
            activity["typeProperties"]["datasetSettings"] = {
                "type": "LakehouseFolder",
                "linkedService": {
                    "name": "LakehouseRef",
                    "properties": {
                        "type": "Lakehouse",
                        "typeProperties": {
                            "workspaceId": workspace_id,
                            "artifactId": lakehouse_id,
                            "rootFolder": "Files"
                        }
                    }
                },
                "typeProperties": {
                    "folderPath": folder_path or ""
                }
            }
        # Fall back to dataset reference (legacy approach)
        elif dataset_name:
            activity["typeProperties"]["dataset"] = {
                "referenceName": dataset_name,
                "type": "DatasetReference"
            }
            activity["typeProperties"]["storeSettings"] = {
                "type": "AzureBlobStorageReadSettings",
                "recursive": True,
                "enablePartitionDiscovery": False
            }

        return activity

    def _generate_set_variable_activity(
        self,
        activity_name: str,
        variable_name: str,
        value: Any,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate Set Variable activity

        Args:
            activity_name: Name of the activity
            variable_name: Variable to set
            value: Value to set (can be expression)
            depends_on: List of activity names this depends on

        Returns:
            Set Variable activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "SetVariable",
            "dependsOn": depends_on or [],
            "policy": {
                "secureOutput": False,
                "secureInput": False
            },
            "typeProperties": {
                "variableName": variable_name,
                "value": value
            }
        }
        return activity

    def _generate_filter_activity(
        self,
        activity_name: str,
        items_expression: str,
        condition_expression: str,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate Filter activity

        Args:
            activity_name: Name of the activity
            items_expression: Expression for items to filter (e.g., "@activity('GetMetadata').output.childItems")
            condition_expression: Filter condition expression
            depends_on: List of activity names this depends on

        Returns:
            Filter activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "Filter",
            "dependsOn": depends_on or [],
            "typeProperties": {
                "items": {
                    "value": items_expression,
                    "type": "Expression"
                },
                "condition": {
                    "value": condition_expression,
                    "type": "Expression"
                }
            }
        }
        return activity

    def _generate_foreach_activity(
        self,
        activity_name: str,
        items_expression: str,
        activities: List[Dict[str, Any]],
        is_sequential: bool = False,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate ForEach activity

        Args:
            activity_name: Name of the activity
            items_expression: Expression for items to iterate (e.g., "@activity('Filter').output.value")
            activities: List of nested activities inside ForEach
            is_sequential: Execute sequentially (True) or in parallel (False)
            depends_on: List of activity names this depends on

        Returns:
            ForEach activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "ForEach",
            "dependsOn": depends_on or [],
            "typeProperties": {
                "items": {
                    "value": items_expression,
                    "type": "Expression"
                },
                "isSequential": is_sequential,
                "activities": activities
            }
        }
        return activity

    def _generate_trident_notebook_activity(
        self,
        activity_name: str,
        notebook_id: str,
        workspace_id: str,
        parameters: Dict[str, Any] = None,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate TridentNotebook activity (Fabric Notebook execution)

        Args:
            activity_name: Name of the activity
            notebook_id: ID of the notebook to execute
            workspace_id: Workspace ID where notebook exists
            parameters: Parameters to pass to notebook
            depends_on: List of activity names this depends on

        Returns:
            TridentNotebook activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "TridentNotebook",
            "dependsOn": self._format_depends_on(depends_on) if depends_on else [],
            "policy": {
                "timeout": "0.12:00:00",
                "retry": 0,
                "retryIntervalInSeconds": 30,
                "secureOutput": False,
                "secureInput": False
            },
            "typeProperties": {
                "notebookId": notebook_id,
                "workspaceId": workspace_id
            }
        }

        # Add parameters if provided
        if parameters:
            activity["typeProperties"]["parameters"] = parameters

        return activity

    def _generate_if_condition_activity(
        self,
        activity_name: str,
        condition_expression: str,
        if_true_activities: List[Dict[str, Any]],
        if_false_activities: List[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate IfCondition activity

        Args:
            activity_name: Name of the activity
            condition_expression: Expression to evaluate (e.g., "@bool(...)")
            if_true_activities: Activities to execute when condition is true
            if_false_activities: Activities to execute when condition is false
            depends_on: List of activity names this depends on

        Returns:
            IfCondition activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "IfCondition",
            "dependsOn": self._format_depends_on(depends_on) if depends_on else [],
            "typeProperties": {
                "expression": {
                    "value": condition_expression,
                    "type": "Expression"
                },
                "ifTrueActivities": if_true_activities
            }
        }

        # Add false activities if provided
        if if_false_activities:
            activity["typeProperties"]["ifFalseActivities"] = if_false_activities

        return activity

    def _generate_office365_email_activity(
        self,
        activity_name: str,
        to_email: str,
        subject: str,
        body: str,
        connection_id: str,
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate Office365Email activity

        Args:
            activity_name: Name of the activity
            to_email: Recipient email address
            subject: Email subject
            body: Email body (can include expressions)
            connection_id: Office365 connection ID
            depends_on: List of activity names this depends on

        Returns:
            Office365Email activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "Office365Email",
            "dependsOn": self._format_depends_on(depends_on) if depends_on else [],
            "policy": {
                "timeout": "0.12:00:00",
                "retry": 0,
                "retryIntervalInSeconds": 30,
                "secureOutput": False,
                "secureInput": False
            },
            "typeProperties": {
                "to": to_email,
                "subject": subject,
                "body": body
            },
            "externalReferences": {
                "connection": connection_id
            }
        }
        return activity

    def _generate_refresh_dataflow_activity(
        self,
        activity_name: str,
        dataflow_id: str,
        workspace_id: str,
        notify_option: str = "NoNotification",
        depends_on: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate RefreshDataflow activity (Dataflow Gen2)

        Args:
            activity_name: Name of the activity
            dataflow_id: ID of the dataflow to refresh
            workspace_id: Workspace ID where dataflow exists
            notify_option: Notification option ("NoNotification", "OnCompletion", "OnFailure")
            depends_on: List of activity names this depends on

        Returns:
            RefreshDataflow activity JSON definition
        """
        activity = {
            "name": activity_name,
            "type": "RefreshDataflow",
            "dependsOn": self._format_depends_on(depends_on) if depends_on else [],
            "policy": {
                "timeout": "0.12:00:00",
                "retry": 0,
                "retryIntervalInSeconds": 30,
                "secureOutput": False,
                "secureInput": False
            },
            "typeProperties": {
                "dataflowId": dataflow_id,
                "workspaceId": workspace_id,
                "notifyOption": notify_option,
                "dataflowType": "DataflowFabric"
            }
        }
        return activity

    async def generate_file_processing_pipeline(
        self,
        workspace_id: str,
        lakehouse_id: str,
        pipeline_name: str,
        source_container: str,
        bronze_shortcut_name: str = "azure_blob_bronze"
    ) -> Dict[str, Any]:
        """
        Generate complete file processing pipeline with incremental loading

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse ID
            pipeline_name: Name of the pipeline
            source_container: Source container name (e.g., "bronze")
            bronze_shortcut_name: Name of the OneLake shortcut to bronze container

        Returns:
            Complete pipeline JSON definition
        """
        try:
            # Get SQL endpoint for the lakehouse
            sql_endpoint_result = await self.get_lakehouse_sql_endpoint(workspace_id, lakehouse_id)

            if not sql_endpoint_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to get SQL endpoint"
                }

            connection_string = sql_endpoint_result["connection_string"]
            lakehouse_name = sql_endpoint_result["lakehouse_name"]

            # SQL query to get processed files
            get_processed_files_sql = """
            SELECT filename
            FROM fileprocessed
            WHERE file_status = 'Done'
            """

            # Pipeline variables
            variables = {
                "ProcessedFiles": {
                    "type": "Array",
                    "defaultValue": []
                },
                "NewFiles": {
                    "type": "Array",
                    "defaultValue": []
                }
            }

            # Activity 1: Get Metadata - retrieve all files from bronze container
            get_metadata_activity = self._generate_get_metadata_activity(
                activity_name="GetMetadata",
                dataset_name=f"{bronze_shortcut_name}_dataset"
            )

            # Activity 2: Script - get processed file names from fileprocessed table
            script_activity = self._generate_script_activity(
                activity_name="GetProcessedFileNames",
                sql_query=get_processed_files_sql,
                sql_connection_string=connection_string,
                depends_on=[{"activity": "GetMetadata", "dependencyConditions": ["Succeeded"]}]
            )

            # Activity 3: Set Variable - initialize empty array for new files
            set_variable_activity = self._generate_set_variable_activity(
                activity_name="SetEmptyFileArray",
                variable_name="NewFiles",
                value={"value": "[]", "type": "Expression"},
                depends_on=[{"activity": "GetProcessedFileNames", "dependencyConditions": ["Succeeded"]}]
            )

            # Activity 4: ForEach 1 - loop through all files and build new files array
            # Inside ForEach: Set variable to append new files
            foreach1_nested_activity = self._generate_set_variable_activity(
                activity_name="AppendNewFile",
                variable_name="NewFiles",
                value={
                    "value": "@if(contains(variables('ProcessedFiles'), item().name), variables('NewFiles'), union(variables('NewFiles'), createArray(item())))",
                    "type": "Expression"
                }
            )

            foreach1_activity = self._generate_foreach_activity(
                activity_name="ForEach1",
                items_expression="@activity('GetMetadata').output.childItems",
                activities=[foreach1_nested_activity],
                is_sequential=False,
                depends_on=[{"activity": "SetEmptyFileArray", "dependencyConditions": ["Succeeded"]}]
            )

            # Activity 5: Filter - filter only new files
            filter_activity = self._generate_filter_activity(
                activity_name="FilterNewFiles",
                items_expression="@activity('GetMetadata').output.childItems",
                condition_expression="@not(contains(activity('GetProcessedFileNames').output.resultSets[0].rows, item().name))",
                depends_on=[{"activity": "ForEach1", "dependencyConditions": ["Succeeded"]}]
            )

            # Activity 6: ForEach 2 - process each new file
            # Nested activities: Copy activity, Condition activity, etc.
            copy_activity = {
                "name": "CopyFileToLakehouse",
                "type": "Copy",
                "dependsOn": [],
                "policy": {
                    "timeout": "0.12:00:00",
                    "retry": 0,
                    "retryIntervalInSeconds": 30
                },
                "typeProperties": {
                    "source": {
                        "type": "BinarySource",
                        "storeSettings": {
                            "type": "AzureBlobStorageReadSettings",
                            "recursive": True
                        }
                    },
                    "sink": {
                        "type": "BinarySink",
                        "storeSettings": {
                            "type": "LakehouseWriteSettings"
                        }
                    },
                    "enableStaging": False
                }
            }

            # Condition activity to check copy success
            condition_activity = {
                "name": "CheckCopyStatus",
                "type": "IfCondition",
                "dependsOn": [{"activity": "CopyFileToLakehouse", "dependencyConditions": ["Succeeded"]}],
                "typeProperties": {
                    "expression": {
                        "value": "@equals(activity('CopyFileToLakehouse').Status, 'Succeeded')",
                        "type": "Expression"
                    },
                    "ifTrueActivities": [
                        self._generate_script_activity(
                            activity_name="MarkFileAsProcessed",
                            sql_query=f"INSERT INTO fileprocessed (filename, file_status) VALUES ('@{{item().name}}', 'Done')",
                            sql_connection_string=connection_string
                        )
                    ],
                    "ifFalseActivities": [
                        self._generate_script_activity(
                            activity_name="MarkFileAsFailed",
                            sql_query=f"INSERT INTO fileprocessed (filename, file_status) VALUES ('@{{item().name}}', 'Failed')",
                            sql_connection_string=connection_string
                        )
                    ]
                }
            }

            foreach2_activity = self._generate_foreach_activity(
                activity_name="ForEach2",
                items_expression="@activity('FilterNewFiles').output.value",
                activities=[copy_activity, condition_activity],
                is_sequential=True,
                depends_on=[{"activity": "FilterNewFiles", "dependencyConditions": ["Succeeded"]}]
            )

            # Build complete pipeline JSON
            pipeline_json = {
                "properties": {
                    "activities": [
                        get_metadata_activity,
                        script_activity,
                        set_variable_activity,
                        foreach1_activity,
                        filter_activity,
                        foreach2_activity
                    ],
                    "variables": variables,
                    "annotations": [],
                    "lastPublishTime": None
                }
            }

            logger.info(f"Generated file processing pipeline: {pipeline_name}")

            return {
                "success": True,
                "pipeline_name": pipeline_name,
                "pipeline_json": pipeline_json,
                "lakehouse_name": lakehouse_name,
                "sql_endpoint": sql_endpoint_result["sql_endpoint"],
                "activities_count": len(pipeline_json["properties"]["activities"])
            }

        except Exception as e:
            logger.error(f"Error generating file processing pipeline: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_pipeline(
        self,
        workspace_id: str,
        pipeline_name: str,
        pipeline_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a data pipeline in Microsoft Fabric workspace

        Args:
            workspace_id: Fabric workspace ID
            pipeline_name: Name of the pipeline
            pipeline_definition: Pipeline JSON definition

        Returns:
            Dict with pipeline_id and deployment info
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Use correct Fabric API endpoint for data pipelines
            create_url = f"{self.base_url}/workspaces/{workspace_id}/dataPipelines"

            # Create pipeline with definition
            import base64
            pipeline_content = json.dumps(pipeline_definition)
            pipeline_base64 = base64.b64encode(pipeline_content.encode('utf-8')).decode('utf-8')

            payload = {
                "displayName": pipeline_name,
                "description": "AI-generated data pipeline for Medallion architecture",
                "definition": {
                    "parts": [
                        {
                            "path": "pipeline-content.json",
                            "payload": pipeline_base64,
                            "payloadType": "InlineBase64"
                        }
                    ]
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(create_url, json=payload, headers=headers)

                if response.status_code == 201 or response.status_code == 200:
                    result = response.json()
                    logger.info(f"Pipeline created successfully: {result.get('id')}")

                    return {
                        "success": True,
                        "pipeline_id": result.get("id"),
                        "pipeline_name": pipeline_name,
                        "workspace_id": workspace_id,
                        "note": "Pipeline deployed successfully with activities"
                    }
                else:
                    logger.error(f"Fabric API error: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to create pipeline in Fabric: {response.text}")

        except httpx.HTTPStatusError as e:
            logger.error(f"Fabric API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to create pipeline in Fabric: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating pipeline: {str(e)}")
            raise

    def prepare_notebook_cells_with_parameters(
        self,
        python_code: str,
        parameter_name: str = "fileName",
        parameter_default: str = "default_file.csv"
    ) -> List[Dict[str, Any]]:
        """
        Prepare notebook cells with a parameters cell and main code cell

        Args:
            python_code: Complete Python code from .py file
            parameter_name: Name of the parameter (e.g., "fileName")
            parameter_default: Default value for the parameter

        Returns:
            List of cell definitions for notebook
        """
        # Cell 1: Parameters cell (tagged)
        parameters_cell = {
            "cell_type": "code",
            "source": f"# Parameters\n{parameter_name} = \"{parameter_default}\"",
            "metadata": {
                "tags": ["parameters"]
            },
            "outputs": [],
            "execution_count": None
        }

        # Cell 2: Main code cell
        # Remove the problematic line "fileName = fileName" if it exists
        cleaned_code = python_code.replace(f"{parameter_name} = {parameter_name}\n", "")
        # Also remove any commented default assignment like: # fileName="claims_data.csv"
        import re
        cleaned_code = re.sub(rf'#\s*{parameter_name}\s*=\s*["\'].*?["\']', '', cleaned_code)

        main_code_cell = {
            "cell_type": "code",
            "source": cleaned_code,
            "metadata": {},
            "outputs": [],
            "execution_count": None
        }

        return [parameters_cell, main_code_cell]

    async def create_notebook(
        self,
        workspace_id: str,
        notebook_name: str,
        notebook_code: str = None,
        cells: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a notebook in Microsoft Fabric workspace

        Args:
            workspace_id: Fabric workspace ID
            notebook_name: Name of the notebook
            notebook_code: PySpark code for the notebook (single cell - legacy)
            cells: List of cell definitions for multi-cell notebooks
                   Each cell: {"source": "code", "cell_type": "code", "metadata": {...}}

        Returns:
            Dict with notebook_id and deployment info
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Use correct Fabric API endpoint for notebooks
            create_url = f"{self.base_url}/workspaces/{workspace_id}/notebooks"

            # Create notebook content in ipynb format
            import base64

            # If cells provided, use them; otherwise create single code cell
            if cells:
                notebook_cells = cells
            elif notebook_code:
                notebook_cells = [
                    {
                        "cell_type": "code",
                        "source": notebook_code,
                        "metadata": {},
                        "outputs": [],
                        "execution_count": None
                    }
                ]
            else:
                raise ValueError("Either notebook_code or cells must be provided")

            notebook_content = {
                "nbformat": 4,
                "nbformat_minor": 2,
                "cells": notebook_cells,
                "metadata": {
                    "kernelspec": {
                        "name": "synapse_pyspark",
                        "display_name": "Synapse PySpark"
                    },
                    "language_info": {
                        "name": "python"
                    }
                }
            }

            notebook_json = json.dumps(notebook_content)
            notebook_base64 = base64.b64encode(notebook_json.encode('utf-8')).decode('utf-8')

            payload = {
                "displayName": notebook_name,
                "description": f"Notebook for data processing: {notebook_name}",
                "definition": {
                    "format": "ipynb",
                    "parts": [
                        {
                            "path": "notebook-content.ipynb",
                            "payload": notebook_base64,
                            "payloadType": "InlineBase64"
                        }
                    ]
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(create_url, json=payload, headers=headers)

                if response.status_code in [200, 201, 202]:
                    # 202 Accepted means the operation is async and will complete later
                    try:
                        result = response.json() if response.text and response.text != 'null' else {}
                    except:
                        result = {}

                    notebook_id = result.get('id') or result.get('notebookId') or notebook_name
                    logger.info(f"Notebook created/accepted: {notebook_id} (status: {response.status_code})")

                    # If status is 202, wait for notebook to be fully created
                    if response.status_code == 202:
                        logger.info(f"Notebook creation is async (202). Waiting for notebook to be ready...")
                        logger.info(f"Polling for notebook with ID/name: {notebook_id}")

                        # Poll for notebook status (max 60 seconds, check every 2 seconds)
                        import asyncio
                        max_attempts = 30  # 30 attempts * 2 seconds = 60 seconds total
                        for attempt in range(max_attempts):
                            await asyncio.sleep(2)  # Wait 2 seconds between checks

                            # Try to get notebook by listing all notebooks and finding by name
                            list_url = f"{self.base_url}/workspaces/{workspace_id}/notebooks"
                            list_response = await client.get(list_url, headers=headers)

                            if list_response.status_code == 200:
                                notebooks_list = list_response.json().get("value", [])
                                # Check if our notebook exists in the list
                                notebook_found = any(
                                    nb.get("displayName") == notebook_name or nb.get("id") == notebook_id
                                    for nb in notebooks_list
                                )

                                if notebook_found:
                                    logger.info(f"Notebook '{notebook_name}' is now ready (attempt {attempt + 1}/{max_attempts})")
                                    break
                                else:
                                    logger.debug(f"Notebook not found yet. Total notebooks in workspace: {len(notebooks_list)}")

                            if attempt == max_attempts - 1:
                                logger.warning(f"Notebook '{notebook_name}' creation timeout after {max_attempts * 2} seconds")
                                # Don't fail - continue anyway as notebook might still be creating
                                logger.warning(f"Continuing with pipeline creation anyway...")

                        # Wait additional time to ensure it's fully ready for pipeline reference
                        await asyncio.sleep(5)

                    return {
                        "success": True,
                        "notebook_id": notebook_id,
                        "notebook_name": notebook_name,
                        "note": f"Notebook deployed (status {response.status_code})",
                        "status_code": response.status_code
                    }
                else:
                    logger.error(f"Notebook creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": response.text,
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Error creating notebook: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_connection(
        self,
        workspace_id: str,
        connection_name: str,
        source_type: str,
        connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a Connection using Fabric Connections API (workspace-level)

        Args:
            workspace_id: Fabric workspace ID where connection will be created
            connection_name: Display name for the connection
            source_type: Type of data source (blob, adls, sql, etc.)
            connection_config: Connection configuration including credentials

        Returns:
            Dict with connection creation result
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Use global Connections API endpoint (not workspace-level)
            # Note: Connections API is at /v1/connections, not /v1/workspaces/{id}/connections
            create_url = f"{self.base_url}/connections"

            # Build connection payload based on source type
            payload = self._build_connection_payload(
                connection_name,
                source_type,
                connection_config
            )

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(create_url, json=payload, headers=headers)

                if response.status_code in [200, 201]:
                    result = response.json()
                    connection_id = result.get("id")
                    logger.info(f"Connection '{connection_name}' created successfully: {connection_id}")

                    return {
                        "success": True,
                        "connection_id": connection_id,
                        "connection_name": connection_name,
                        "source_type": source_type
                    }
                else:
                    logger.error(f"Connection creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Failed to create connection: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Error creating connection: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    # ============================================================================
    # COMMENTED OUT - WORKING COPYJOB CODE (2025-10-15)
    # ============================================================================
    # This code works successfully for copying from external sources to Lakehouse
    # Kept for reference and potential future use
    # ============================================================================

    # async def create_copy_job(
    #     self,
    #     workspace_id: str,
    #     copy_job_name: str,
    #     connection_id: str,
    #     source_config: Dict[str, Any],
    #     sink_config: Dict[str, Any]
    # ) -> Dict[str, Any]:
    #     """
    #     Create a CopyJob using Fabric CopyJob API for simple copy operations
    #
    #     CopyJob is the recommended approach for copying data from external sources
    #     (like Azure Blob Storage) to Lakehouse, as it supports direct connection ID references.
    #
    #     Args:
    #         workspace_id: Fabric workspace ID
    #         copy_job_name: Display name for the copy job
    #         connection_id: GUID of the connection created via Connections API
    #         source_config: Source configuration dict with keys:
    #             - container: Container name (for blob storage)
    #             - wildcardFileName: File pattern (e.g., "*.csv")
    #             - recursive: Boolean for recursive search
    #             - format: Format config dict (type, firstRowAsHeader, etc.)
    #         sink_config: Sink configuration dict with keys:
    #             - workspaceId: Lakehouse workspace ID
    #             - lakehouseId: Lakehouse item ID
    #             - tableName: Target table name
    #             - tableAction: "Append" or "Overwrite"
    #
    #     Returns:
    #         Dict with copy job creation result
    #     """
    #     try:
    #         token = await self.get_access_token()
    #
    #         headers = {
    #             "Authorization": f"Bearer {token}",
    #             "Content-Type": "application/json"
    #         }
    #
    #         # Build CopyJob definition
    #         copy_job_definition = {
    #             "properties": {
    #                 "jobMode": "Batch",
    #                 "sources": [
    #                     {
    #                         "name": "Source",
    #                         "connectionId": connection_id,
    #                         "dataSourceType": source_config.get("dataSourceType", "AzureBlobStorage"),
    #                         "container": source_config.get("container", "data"),
    #                         "wildcardFileName": source_config.get("wildcardFileName", "*.csv"),
    #                         "recursive": source_config.get("recursive", True),
    #                         "format": source_config.get("format", {
    #                             "type": "DelimitedText",
    #                             "firstRowAsHeader": True,
    #                             "columnDelimiter": ","
    #                         })
    #                     }
    #                 ],
    #                 "sinks": [
    #                     {
    #                         "name": "Sink",
    #                         "dataSourceType": "Lakehouse",
    #                         "workspaceId": sink_config.get("workspaceId"),
    #                         "lakehouseId": sink_config.get("lakehouseId"),
    #                         "tableName": sink_config.get("tableName", "output_table"),
    #                         "tableAction": sink_config.get("tableAction", "Append")
    #                     }
    #                 ],
    #                 "mappings": [
    #                     {
    #                         "source": "Source",
    #                         "sink": "Sink"
    #                     }
    #                 ]
    #             }
    #         }
    #
    #         # Base64 encode the definition
    #         import base64
    #         definition_json = json.dumps(copy_job_definition)
    #         definition_base64 = base64.b64encode(definition_json.encode()).decode()
    #
    #         # Create CopyJob via API
    #         create_url = f"{self.base_url}/workspaces/{workspace_id}/copyJobs"
    #
    #         payload = {
    #             "displayName": copy_job_name,
    #             "definition": {
    #                 "parts": [
    #                     {
    #                         "path": "copyjob-content.json",
    #                         "payload": definition_base64,
    #                         "payloadType": "InlineBase64"
    #                     }
    #                 ]
    #             }
    #         }
    #
    #         async with httpx.AsyncClient(timeout=60.0) as client:
    #             response = await client.post(create_url, json=payload, headers=headers)
    #
    #             if response.status_code in [200, 201]:
    #                 result = response.json()
    #                 copy_job_id = result.get("id")
    #                 logger.info(f"CopyJob '{copy_job_name}' created successfully: {copy_job_id}")
    #
    #                 return {
    #                     "success": True,
    #                     "copy_job_id": copy_job_id,
    #                     "copy_job_name": copy_job_name,
    #                     "workspace_id": workspace_id,
    #                     "connection_id": connection_id,
    #                     "note": "CopyJob created - use this for external source → Lakehouse copy operations"
    #                 }
    #             else:
    #                 logger.error(f"CopyJob creation failed: {response.status_code} - {response.text}")
    #                 return {
    #                     "success": False,
    #                     "error": f"Failed to create CopyJob: {response.text}",
    #                     "status_code": response.status_code
    #                 }
    #
    #     except Exception as e:
    #         logger.error(f"Error creating CopyJob: {str(e)}")
    #         return {
    #             "success": False,
    #             "error": str(e)
    #         }

    # ============================================================================
    # END OF COMMENTED CODE
    # ============================================================================

    async def create_onelake_shortcut(
        self,
        workspace_id: str,
        lakehouse_id: str,
        shortcut_name: str,
        target_location: str,
        connection_id: str,
        shortcut_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an OneLake shortcut to external storage (Azure Blob, ADLS Gen2, S3, etc.)

        This allows you to access external data directly in Lakehouse Files folder without copying.
        The shortcut can then be used as a source in Copy Activity pipelines.

        Args:
            workspace_id: Fabric workspace ID
            lakehouse_id: Lakehouse item ID where shortcut will be created
            shortcut_name: Name of the shortcut folder
            target_location: Where to create shortcut - "Files" or "Tables"
            connection_id: GUID of the connection to external storage
            shortcut_config: Configuration dict with keys:
                - target_type: "AzureBlob", "AdlsGen2", "S3", etc.
                - container: Container/bucket name (for blob/S3)
                - folder_path: Optional path within container (default: root)
                - For ADLS: filesystem, path
                - For S3: bucket, prefix

        Returns:
            Dict with shortcut creation result

        Example:
            result = await fabric_service.create_onelake_shortcut(
                workspace_id="c64f4ec0-...",
                lakehouse_id="5bb4039e-...",
                shortcut_name="amazon_data",
                target_location="Files",
                connection_id="372a9195-...",
                shortcut_config={
                    "target_type": "AzureBlob",
                    "container": "fabric",
                    "folder_path": "amazon"
                }
            )
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Build shortcut path - where in lakehouse to create it
            # path = parent folder (e.g., "Files" or "Files/subfolder")
            # name = shortcut name
            # Result: path/name (e.g., "Files/my_shortcut")
            shortcut_path = target_location  # Just "Files" or "Tables"

            # Build target configuration based on target type
            # According to Fabric API docs, the target must be a nested object with specific keys
            target_type = shortcut_config.get("target_type", "AzureBlob")

            if target_type in ["AzureBlob", "AzureBlobStorage"]:
                # Azure Blob Storage shortcut
                # Use blob.core.windows.net endpoint for regular blob storage
                storage_account = shortcut_config.get("storage_account", "storage")
                container = shortcut_config.get("container", "data")
                folder_path = shortcut_config.get("folder_path", "")

                # Format: location includes container, subpath has folder with leading slash
                # If folder_path is empty, subpath should be "/" or empty to get entire container
                if folder_path:
                    subpath = f"/{folder_path}" if not folder_path.startswith("/") else folder_path
                else:
                    subpath = "/"  # Root of container = all data

                target = {
                    "adlsGen2": {
                        "connectionId": connection_id,
                        "location": f"https://{storage_account}.blob.core.windows.net/{container}",
                        "subpath": subpath
                    }
                }
            elif target_type in ["AdlsGen2", "AzureBlobFS"]:
                # ADLS Gen2 shortcut - this is the correct format for Azure Storage
                storage_account = shortcut_config.get("storage_account", "storage")
                container = shortcut_config.get("container") or shortcut_config.get("filesystem", "data")
                subpath = shortcut_config.get("folder_path") or shortcut_config.get("path", "")

                target = {
                    "adlsGen2": {
                        "connectionId": connection_id,
                        "location": f"https://{storage_account}.dfs.core.windows.net/{container}",
                        "subpath": subpath
                    }
                }
            elif target_type == "S3":
                # Amazon S3 shortcut
                bucket = shortcut_config.get("bucket") or shortcut_config.get("container", "data")
                region = shortcut_config.get("region", "us-west-2")
                subpath = shortcut_config.get("prefix") or shortcut_config.get("folder_path", "")

                target = {
                    "amazonS3": {
                        "connectionId": connection_id,
                        "location": f"https://{bucket}.s3.{region}.amazonaws.com",
                        "subpath": subpath
                    }
                }
            else:
                raise ValueError(f"Unsupported shortcut target type: {target_type}")

            # Build shortcut payload
            payload = {
                "path": shortcut_path,
                "name": shortcut_name,
                "target": target
            }

            # Create shortcut via OneLake Shortcuts API
            create_url = f"{self.base_url}/workspaces/{workspace_id}/items/{lakehouse_id}/shortcuts"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(create_url, json=payload, headers=headers)

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"OneLake shortcut '{shortcut_name}' created successfully in {target_location}")

                    return {
                        "success": True,
                        "shortcut_name": shortcut_name,
                        "shortcut_path": shortcut_path,
                        "workspace_id": workspace_id,
                        "lakehouse_id": lakehouse_id,
                        "connection_id": connection_id,
                        "target_type": target_type,
                        "note": f"Shortcut created at {target_location}/{shortcut_name} - can now be used in Copy Activity"
                    }
                else:
                    logger.error(f"Shortcut creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Failed to create shortcut: {response.text}",
                        "status_code": response.status_code
                    }

        except Exception as e:
            logger.error(f"Error creating OneLake shortcut: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def create_linked_service(
        self,
        workspace_id: str,
        linked_service_name: str,
        source_type: str,
        connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a Linked Service in Microsoft Fabric workspace (DEPRECATED - use create_connection instead)

        Args:
            workspace_id: Fabric workspace ID
            linked_service_name: Name for the linked service
            source_type: Type of data source (blob, adls, sql, etc.)
            connection_config: Connection configuration including credentials

        Returns:
            Dict with linked service creation result
        """
        try:
            token = await self.get_access_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Build linked service definition based on source type
            linked_service_def = self._build_linked_service_definition(
                linked_service_name,
                source_type,
                connection_config
            )

            # Use Fabric API endpoint for creating items
            create_url = f"{self.base_url}/workspaces/{workspace_id}/items"

            # Encode linked service definition
            import base64
            ls_content = json.dumps(linked_service_def)
            ls_base64 = base64.b64encode(ls_content.encode('utf-8')).decode('utf-8')

            payload = {
                "displayName": linked_service_name,
                "type": "DataPipeline",  # Linked services are part of data pipeline items
                "definition": {
                    "parts": [
                        {
                            "path": "linkedService.json",
                            "payload": ls_base64,
                            "payloadType": "InlineBase64"
                        }
                    ]
                }
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(create_url, json=payload, headers=headers)

                if response.status_code in [200, 201, 202]:
                    result = response.json()
                    logger.info(f"Linked Service '{linked_service_name}' created successfully")

                    return {
                        "success": True,
                        "linked_service_id": result.get("id"),
                        "linked_service_name": linked_service_name,
                        "source_type": source_type
                    }
                else:
                    logger.error(f"Linked Service creation failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Failed to create linked service: {response.text}"
                    }

        except Exception as e:
            logger.error(f"Error creating linked service: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_connection_payload(
        self,
        connection_name: str,
        source_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build Fabric Connection payload using the new Connections API format

        Args:
            connection_name: Display name for the connection
            source_type: Type of data source
            config: Connection configuration

        Returns:
            Connection payload dict for Fabric Connections API
        """

        # Azure Blob Storage
        if source_type in ["blob", "azureblob", "blobstorage"]:
            auth_type = config.get("auth_type", "ServicePrincipal")
            account_name = config.get("account_name")

            payload = {
                "connectivityType": "ShareableCloud",
                "displayName": connection_name,
                "connectionDetails": {
                    "type": "AzureBlobs",
                    "creationMethod": "AzureBlobs",
                    "parameters": [
                        {
                            "dataType": "Text",
                            "name": "account",
                            "value": account_name
                        },
                        {
                            "dataType": "Text",
                            "name": "domain",
                            "value": "blob.core.windows.net"
                        }
                    ]
                },
                "privacyLevel": "Organizational",
                "credentialDetails": {
                    "singleSignOnType": "None",
                    "connectionEncryption": "NotEncrypted",
                    "skipTestConnection": False
                }
            }

            if auth_type == "ServicePrincipal":
                # Use Service Principal (recommended for automation)
                tenant_id = config.get("tenant_id", self.tenant_id)
                client_id = config.get("client_id", self.client_id)
                client_secret = config.get("client_secret", self.client_secret)

                payload["credentialDetails"]["credentials"] = {
                    "credentialType": "ServicePrincipal",
                    "servicePrincipalClientId": client_id,
                    "servicePrincipalSecret": client_secret,  # Correct field name
                    "tenantId": tenant_id
                }
            elif auth_type == "AccountKey" or auth_type == "Key":
                account_key = config.get("account_key")
                payload["credentialDetails"]["credentials"] = {
                    "credentialType": "Key",
                    "key": account_key
                }
            elif auth_type == "SasToken":
                sas_token = config.get("sas_token")
                payload["credentialDetails"]["credentials"] = {
                    "credentialType": "SharedAccessSignature",
                    "token": sas_token
                }
            elif auth_type == "WorkspaceIdentity":
                payload["credentialDetails"]["credentials"] = {
                    "credentialType": "WorkspaceIdentity"
                }

            return payload

        # Azure Data Lake Storage Gen2
        elif source_type in ["adls", "adlsgen2", "datalake"]:
            auth_type = config.get("auth_type", "AccountKey")
            account_name = config.get("account_name")

            payload = {
                "connectivityType": "ShareableCloud",
                "displayName": connection_name,
                "connectionDetails": {
                    "type": "AzureBlobFS",
                    "creationMethod": "AzureBlobFS",
                    "parameters": [
                        {
                            "dataType": "Text",
                            "name": "url",
                            "value": f"https://{account_name}.dfs.core.windows.net"
                        }
                    ]
                },
                "privacyLevel": "Organizational",
                "credentialDetails": {
                    "singleSignOnType": "None",
                    "connectionEncryption": "NotEncrypted",
                    "skipTestConnection": False
                }
            }

            if auth_type == "AccountKey" or auth_type == "Key":
                account_key = config.get("account_key")
                payload["credentialDetails"]["credentials"] = {
                    "credentialType": "Key",
                    "key": account_key
                }
            elif auth_type in ["ManagedIdentity", "WorkspaceIdentity"]:
                payload["credentialDetails"]["credentials"] = {
                    "credentialType": "WorkspaceIdentity"
                }

            return payload

        # Azure SQL Database
        elif source_type in ["azuresql", "sqldb"]:
            server = config.get("server")
            database = config.get("database")
            username = config.get("username")
            password = config.get("password")

            return {
                "connectivityType": "ShareableCloud",
                "displayName": connection_name,
                "connectionDetails": {
                    "type": "SQL",
                    "creationMethod": "SQL",
                    "parameters": [
                        {
                            "dataType": "Text",
                            "name": "server",
                            "value": server
                        },
                        {
                            "dataType": "Text",
                            "name": "database",
                            "value": database
                        }
                    ]
                },
                "privacyLevel": "Organizational",
                "credentialDetails": {
                    "singleSignOnType": "None",
                    "connectionEncryption": "NotEncrypted",
                    "skipTestConnection": False,
                    "credentials": {
                        "credentialType": "Basic",
                        "username": username,
                        "password": password
                    }
                }
            }

        else:
            raise ValueError(f"Unsupported source type for Connections API: {source_type}")

    def _build_linked_service_definition(
        self,
        name: str,
        source_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build Fabric Linked Service definition based on source type (DEPRECATED)

        Args:
            name: Linked service name
            source_type: Type of data source
            config: Connection configuration

        Returns:
            Linked service definition dict
        """

        # Azure Blob Storage
        if source_type in ["blob", "azureblob", "blobstorage"]:
            auth_type = config.get("auth_type", "AccountKey")

            if auth_type == "AccountKey":
                return {
                    "name": name,
                    "properties": {
                        "type": "AzureBlobStorage",
                        "typeProperties": {
                            "connectionString": f"DefaultEndpointsProtocol=https;AccountName={config['account_name']};AccountKey={config['account_key']};EndpointSuffix=core.windows.net"
                        },
                        "annotations": []
                    }
                }
            elif auth_type == "SasToken":
                return {
                    "name": name,
                    "properties": {
                        "type": "AzureBlobStorage",
                        "typeProperties": {
                            "sasUri": config['sas_uri']
                        },
                        "annotations": []
                    }
                }
            elif auth_type == "ManagedIdentity":
                return {
                    "name": name,
                    "properties": {
                        "type": "AzureBlobStorage",
                        "typeProperties": {
                            "serviceEndpoint": f"https://{config['account_name']}.blob.core.windows.net",
                            "authenticationType": "ManagedIdentity"
                        },
                        "annotations": []
                    }
                }

        # Azure Data Lake Storage Gen2
        elif source_type in ["adls", "adlsgen2", "datalake"]:
            auth_type = config.get("auth_type", "AccountKey")

            if auth_type == "AccountKey":
                return {
                    "name": name,
                    "properties": {
                        "type": "AzureBlobFS",
                        "typeProperties": {
                            "url": f"https://{config['account_name']}.dfs.core.windows.net",
                            "accountKey": config['account_key']
                        },
                        "annotations": []
                    }
                }
            elif auth_type == "ManagedIdentity":
                return {
                    "name": name,
                    "properties": {
                        "type": "AzureBlobFS",
                        "typeProperties": {
                            "url": f"https://{config['account_name']}.dfs.core.windows.net",
                            "authenticationType": "ManagedIdentity"
                        },
                        "annotations": []
                    }
                }

        # Azure SQL Database
        elif source_type in ["azuresql", "sqldb"]:
            return {
                "name": name,
                "properties": {
                    "type": "AzureSqlDatabase",
                    "typeProperties": {
                        "connectionString": f"Server=tcp:{config['server']},1433;Database={config['database']};User ID={config['username']};Password={config['password']};Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
                    },
                    "annotations": []
                }
            }

        # SQL Server
        elif source_type in ["sqlserver", "sql"]:
            return {
                "name": name,
                "properties": {
                    "type": "SqlServer",
                    "typeProperties": {
                        "connectionString": f"Server={config['server']};Database={config['database']};User Id={config['username']};Password={config['password']};Encrypt=True;TrustServerCertificate=True;"
                    },
                    "annotations": []
                }
            }

        # REST API
        elif source_type in ["rest", "api"]:
            return {
                "name": name,
                "properties": {
                    "type": "RestService",
                    "typeProperties": {
                        "url": config['base_url'],
                        "authenticationType": config.get('auth_type', 'Anonymous'),
                        "authHeaders": config.get('headers', {})
                    },
                    "annotations": []
                }
            }

        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    def _transform_activities_to_fabric_format(
        self,
        activities: List[Dict[str, Any]],
        workspace_id: str = None,
        lakehouse_id: str = None
    ) -> Dict[str, Any]:
        """
        Transform Claude-generated activities to Fabric pipeline format

        Args:
            activities: List of activities from Claude
            workspace_id: Workspace ID to inject into sources/sinks
            lakehouse_id: Lakehouse ID to inject into LakehouseFiles sources

        Returns:
            Dict with 'activities' and 'datasets' arrays
        """
        fabric_activities = []
        datasets = []
        dataset_counter = 1

        for activity in activities:
            activity_type = activity.get('type', 'Copy')
            activity_name = activity.get('name', 'Activity1')
            config = activity.get('config', {})
            depends_on = activity.get('depends_on', [])

            if activity_type == 'Copy':
                # Build Copy Activity with proper connection reference
                source_config = config.get('source', {})
                sink_config = config.get('sink', {})

                # Inject workspace_id and lakehouse_id into LakehouseFiles sources
                if source_config.get('type') == 'LakehouseFiles':
                    if workspace_id and 'workspace_id' not in source_config:
                        source_config['workspace_id'] = workspace_id
                    if lakehouse_id and 'lakehouse_id' not in source_config:
                        source_config['lakehouse_id'] = lakehouse_id

                # Inject workspace_id and lakehouse_id into sinks
                if sink_config.get('type') in ['LakehouseTable', 'Lakehouse']:
                    if workspace_id and 'workspace_id' not in sink_config:
                        sink_config['workspace_id'] = workspace_id
                    if lakehouse_id and 'lakehouse_id' not in sink_config:
                        sink_config['lakehouse_id'] = lakehouse_id

                fabric_activity = {
                    "name": activity_name,
                    "type": "Copy",
                    "dependsOn": self._format_depends_on(depends_on),
                    "policy": {
                        "timeout": "0.12:00:00",
                        "retry": 2,
                        "retryIntervalInSeconds": 30
                    },
                    "typeProperties": {
                        "source": self._build_copy_source(source_config),
                        "sink": self._build_copy_sink(sink_config),
                        "enableStaging": False
                    }
                }
                fabric_activities.append(fabric_activity)
                logger.info(f"Added Copy activity '{activity_name}' with connection reference")

            elif activity_type == 'Notebook':
                # Build Notebook Activity
                fabric_activity = {
                    "name": activity_name,
                    "type": "SynapseNotebook",
                    "dependsOn": self._format_depends_on(depends_on),
                    "policy": {
                        "timeout": "0.12:00:00",
                        "retry": 0
                    },
                    "typeProperties": {
                        "notebook": {
                            "referenceName": config.get('notebook', 'notebook1'),
                            "type": "NotebookReference"
                        },
                        "parameters": config.get('parameters', {})
                    }
                }
                fabric_activities.append(fabric_activity)

            elif activity_type == 'Lookup':
                # Build Lookup Activity
                fabric_activity = {
                    "name": activity_name,
                    "type": "Lookup",
                    "dependsOn": self._format_depends_on(depends_on),
                    "policy": {
                        "timeout": "0.12:00:00",
                        "retry": 2
                    },
                    "typeProperties": {
                        "source": self._build_source(config.get('source', {})),
                        "firstRowOnly": config.get('firstRowOnly', False)
                    }
                }
                fabric_activities.append(fabric_activity)

            elif activity_type == 'SetVariable':
                # Build SetVariable Activity
                fabric_activity = {
                    "name": activity_name,
                    "type": "SetVariable",
                    "dependsOn": self._format_depends_on(depends_on),
                    "typeProperties": {
                        "variableName": config.get('variableName', 'var1'),
                        "value": config.get('value', '')
                    }
                }
                fabric_activities.append(fabric_activity)

            elif activity_type == 'ForEach':
                # Build ForEach Activity
                nested = self._transform_activities_to_fabric_format(
                    config.get('activities', []),
                    workspace_id,
                    lakehouse_id
                )
                fabric_activity = {
                    "name": activity_name,
                    "type": "ForEach",
                    "dependsOn": self._format_depends_on(depends_on),
                    "typeProperties": {
                        "items": config.get('items', {}),
                        "isSequential": config.get('sequential', False),
                        "batchCount": config.get('batchCount', 20),
                        "activities": nested['activities']
                    }
                }
                # Add nested datasets to main datasets list
                datasets.extend(nested.get('datasets', []))
                fabric_activities.append(fabric_activity)

        return {
            "activities": fabric_activities,
            "datasets": datasets
        }

    def _generate_copy_script(self, source_config: Dict[str, Any], sink_config: Dict[str, Any], activity_name: str) -> str:
        """Generate PySpark script for copy operation"""
        source_type = source_config.get('type', 'Lakehouse Table')
        sink_table = sink_config.get('table') or sink_config.get('tableName', 'output_table')

        # For blob storage source
        if 'Blob' in source_type or 'DelimitedText' in source_type:
            container = source_config.get('container', 'data')
            file_name = source_config.get('fileName') or source_config.get('file_path', '*.csv')
            storage_account = source_config.get('storage_account', 'storage')
            account_key = source_config.get('account_key', '')

            script = f"""
# PySpark script generated for {activity_name}
from pyspark.sql import SparkSession

# Read CSV from blob storage
storage_account_name = "{storage_account}"
storage_account_key = "{account_key}"
container_name = "{container}"
file_path = "{file_name}"

spark.conf.set(f"fs.azure.account.key.{{storage_account_name}}.blob.core.windows.net", storage_account_key)

blob_path = f"wasbs://{{container_name}}@{{storage_account_name}}.blob.core.windows.net/{{file_path}}"

# Read CSV
df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load(blob_path)

# Write to lakehouse table
df.write.mode("overwrite").format("delta").saveAsTable("{sink_table}")

print(f"Successfully loaded {{df.count()}} rows into {sink_table}")
"""
        else:
            # For lakehouse to lakehouse
            source_table = source_config.get('table') or source_config.get('tableName', 'source_table')
            query = source_config.get('query', f'SELECT * FROM {source_table}')

            script = f"""
# PySpark script generated for {activity_name}
from pyspark.sql import SparkSession

# Read from source table
df = spark.sql(\"\"\"{query}\"\"\")

# Write to target table
df.write.mode("overwrite").format("delta").saveAsTable("{sink_table}")

print(f"Successfully processed {{df.count()}} rows into {sink_table}")
"""

        return script

    def _build_copy_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build proper Fabric Copy Activity source with connection reference"""
        source_type = source_config.get('type', 'LakehouseTable')

        if source_type == 'LakehouseFiles':
            # Lakehouse Files source (for shortcuts)
            # This is used when data is accessed via OneLake shortcuts
            path = source_config.get('path', 'Files/bronze')
            file_pattern = source_config.get('filePattern') or source_config.get('fileName', '*.csv')

            # Get workspace and lakehouse IDs
            workspace_id = source_config.get('workspaceId') or source_config.get('workspace_id')
            item_id = source_config.get('itemId') or source_config.get('item_id') or source_config.get('lakehouse_id')

            source = {
                "type": "DelimitedTextSource",
                "storeSettings": {
                    "type": "LakehouseReadSettings",
                    "recursive": True,
                    "wildcardFileName": file_pattern,
                    "wildcardFolderPath": path,
                    "enablePartitionDiscovery": False
                },
                "formatSettings": {
                    "type": "DelimitedTextReadSettings"
                }
            }

            # Add workspace and item IDs if provided
            if workspace_id:
                source["storeSettings"]["workspaceId"] = workspace_id
            if item_id:
                source["storeSettings"]["itemId"] = item_id

            return source
        elif 'Blob' in source_type or 'DelimitedText' in source_type:
            # Azure Blob Storage source - use the actual connection name
            container = source_config.get('container', 'fabric')
            file_path = source_config.get('fileName') or source_config.get('file_path', 'data.csv')

            # Get the connection name - this should match what was actually created
            # Try different possible field names
            connection_name = (source_config.get('linkedService') or
                              source_config.get('linkedServiceName') or
                              source_config.get('linked_service_name') or
                              source_config.get('connection_name') or
                              'blobstorage_connection')  # Default fallback

            # Normalize the connection name to match what was created
            connection_name = connection_name.lower().replace(' ', '_')

            return {
                "type": "DelimitedTextSource",
                "connection": {
                    "referenceName": connection_name,  # Use normalized name
                    "type": "ConnectionReference"
                },
                "storeSettings": {
                    "type": "AzureBlobStorageReadSettings",
                    "recursive": True,
                    "wildcardFileName": file_path,
                    "wildcardFolderPath": container  # Use container as folder path
                },
                "formatSettings": {
                    "type": "DelimitedTextReadSettings"
                }
            }
        elif source_type == 'LakehouseTable':
            # Lakehouse table source
            source = {
                "type": "LakehouseTableSource"
            }
            # Add query if present
            if 'query' in source_config:
                source['query'] = source_config['query']
            if 'table' in source_config or 'tableName' in source_config:
                source['table'] = source_config.get('table') or source_config.get('tableName')
            return source
        else:
            # Default to lakehouse
            return {
                "type": "LakehouseTableSource"
            }

    def _build_copy_sink(self, sink_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build proper Fabric Copy Activity sink with lakehouse reference"""
        sink_type = sink_config.get('type', 'LakehouseTable')

        # Get required sink parameters
        table_name = sink_config.get('table') or sink_config.get('tableName', 'output_table')
        workspace_id = sink_config.get('workspaceId') or sink_config.get('workspace_id')
        item_id = sink_config.get('itemId') or sink_config.get('item_id') or sink_config.get('lakehouse_id')
        table_action = sink_config.get('tableActionOption', 'Append')  # Default to Append

        if 'Lakehouse' in sink_type or sink_type == 'LakehouseTable':
            # Lakehouse sink with all required fields
            sink_payload = {
                "type": "LakehouseSink",
                "rootFolder": "Tables",
                "table": table_name,
                "tableActionOption": table_action
            }

            # Add workspaceId if provided
            if workspace_id:
                sink_payload["workspaceId"] = workspace_id

            # Add itemId if provided
            if item_id:
                sink_payload["itemId"] = item_id

            return sink_payload
        else:
            # Default lakehouse sink
            return {
                "type": "LakehouseSink",
                "rootFolder": "Tables",
                "table": table_name,
                "tableActionOption": table_action
            }

    def _format_depends_on(self, depends_on: List[str]) -> List[Dict[str, Any]]:
        """Format depends_on array to Fabric format"""
        if not depends_on:
            return []

        return [
            {
                "activity": activity_name,
                "dependencyConditions": ["Succeeded"]
            }
            for activity_name in depends_on
        ]

    def _build_source(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build source configuration for Fabric activities with inline dataset"""
        source_type = source_config.get('type', 'LakehouseTable')

        if source_type == 'DelimitedText' or 'Blob' in source_type:
            # Build inline dataset for blob storage with connection reference
            container = source_config.get('container', 'data')
            file_name = source_config.get('fileName') or source_config.get('file_path', '*.csv')

            # Get the connection name - this should match what was actually created
            # Try different possible field names
            connection_name = (source_config.get('linkedService') or
                              source_config.get('linkedServiceName') or
                              source_config.get('linked_service_name') or
                              source_config.get('connection_name') or
                              'blobstorage_connection')  # Default fallback

            # Normalize the connection name to match what was created
            connection_name = connection_name.lower().replace(' ', '_')

            return {
                "type": "DelimitedTextSource",
                "connection": {
                    "referenceName": connection_name,  # Use normalized name
                    "type": "ConnectionReference"
                },
                "storeSettings": {
                    "type": "AzureBlobStorageReadSettings",
                    "recursive": True,
                    "wildcardFileName": file_name,
                    "wildcardFolderPath": container  # Use container as folder path
                },
                "formatSettings": {
                    "type": "DelimitedTextReadSettings",
                    "skipLineCount": 0
                }
            }
        elif source_type == 'LakehouseTable':
            source = {
                "type": "LakehouseTableSource"
            }
            # Add query if present
            if 'query' in source_config:
                source['sqlReaderQuery'] = source_config['query']
            if 'tableName' in source_config or 'table' in source_config:
                source['table'] = source_config.get('tableName') or source_config.get('table')
            return source
        else:
            # Default to lakehouse
            return {
                "type": "LakehouseTableSource"
            }

    def _build_sink(self, sink_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build sink configuration for Fabric activities with inline dataset"""
        sink_type = sink_config.get('type', 'LakehouseTable')

        if sink_type == 'LakehouseTable' or 'Lakehouse' in sink_type:
            sink = {
                "type": "LakehouseTableSink",
                "tableActionOption": "OverwriteSchema"
            }

            # Add table name if present
            table_name = sink_config.get('table') or sink_config.get('tableName', 'default_table')
            sink['table'] = table_name

            return sink
        else:
            # Default lakehouse sink
            return {
                "type": "LakehouseTableSink",
                "tableActionOption": "OverwriteSchema",
                "table": "default_table"
            }

    async def deploy_complete_pipeline(
        self,
        workspace_id: str,
        pipeline_name: str,
        activities: List[Dict[str, Any]],
        notebooks: List[Dict[str, Any]],
        linked_services: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deploy complete pipeline with all notebooks and linked services to Fabric workspace

        Args:
            workspace_id: Fabric workspace ID
            pipeline_name: Name of the pipeline
            activities: List of pipeline activities
            notebooks: List of notebooks with code
            linked_services: Optional list of linked services to create

        Returns:
            Dict with deployment results
        """
        try:
            logger.info(f"Starting deployment of pipeline '{pipeline_name}' to workspace {workspace_id}")

            # Get lakehouse ID for the workspace (needed for LakehouseFiles source)
            lakehouses = await self.get_workspace_lakehouses(workspace_id)
            lakehouse_id = None
            if lakehouses:
                lakehouse_id = lakehouses[0].get("id")
                logger.info(f"Using lakehouse: {lakehouses[0].get('displayName')} ({lakehouse_id})")

            # Deploy linked services first (if provided)
            deployed_linked_services = []
            if linked_services:
                for ls in linked_services:
                    logger.info(f"Creating linked service: {ls['name']}")
                    result = await self.create_linked_service(
                        workspace_id=workspace_id,
                        linked_service_name=ls['name'],
                        source_type=ls['source_type'],
                        connection_config=ls['config']
                    )
                    deployed_linked_services.append(result)

            # Deploy notebooks
            deployed_notebooks = []
            for notebook in notebooks:
                logger.info(f"Deploying notebook: {notebook['notebook_name']}")
                result = await self.create_notebook(
                    workspace_id=workspace_id,
                    notebook_name=notebook['notebook_name'],
                    notebook_code=notebook['code']
                )
                deployed_notebooks.append(result)

            # Log activities for debugging
            logger.info(f"Activities to deploy: {len(activities)}")
            logger.info(f"Original activities: {json.dumps(activities, indent=2)[:500]}")

            # Ensure activities is not empty
            if not activities or len(activities) == 0:
                raise Exception("Cannot deploy pipeline: No activities defined. Pipeline must have at least one activity.")

            # Transform activities to Fabric format
            # Pass workspace_id and lakehouse_id to inject into LakehouseFiles sources
            transformed = self._transform_activities_to_fabric_format(activities, workspace_id, lakehouse_id)
            fabric_activities = transformed['activities']
            datasets = transformed.get('datasets', [])

            logger.info(f"Transformed to Fabric format: {len(fabric_activities)} activities, {len(datasets)} datasets")

            # Log FULL transformed activities for debugging
            logger.info("="*80)
            logger.info("FULL TRANSFORMED ACTIVITIES (for debugging connection references):")
            logger.info(json.dumps(fabric_activities, indent=2))
            logger.info("="*80)

            # Create Fabric pipeline definition with datasets
            fabric_pipeline_def = {
                "name": pipeline_name,
                "properties": {
                    "activities": fabric_activities,
                    "annotations": [],
                    "folder": {
                        "name": "AI Generated Pipelines"
                    }
                }
            }

            # Add datasets if present
            if datasets:
                fabric_pipeline_def["properties"]["datasets"] = datasets
                logger.info(f"Added {len(datasets)} datasets to pipeline")

            # Extract all connection references from activities for validation message
            connection_refs = set()
            for activity in fabric_activities:
                if "typeProperties" in activity:
                    if "source" in activity["typeProperties"]:
                        if "connection" in activity["typeProperties"]["source"]:
                            conn_ref = activity["typeProperties"]["source"]["connection"].get("referenceName")
                            if conn_ref:
                                connection_refs.add(conn_ref)

            if connection_refs:
                logger.info(f"Pipeline references these connections: {', '.join(connection_refs)}")
                logger.warning(f"IMPORTANT: Ensure these connections exist in workspace {workspace_id} before deploying!")

            # Deploy pipeline
            logger.info(f"Deploying pipeline: {pipeline_name}")
            pipeline_result = await self.create_pipeline(
                workspace_id=workspace_id,
                pipeline_name=pipeline_name,
                pipeline_definition=fabric_pipeline_def
            )

            successful_notebooks = [n for n in deployed_notebooks if n.get("success")]
            failed_notebooks = [n for n in deployed_notebooks if not n.get("success")]
            successful_linked_services = [ls for ls in deployed_linked_services if ls.get("success")]
            failed_linked_services = [ls for ls in deployed_linked_services if not ls.get("success")]

            return {
                "success": pipeline_result.get("success"),
                "pipeline_id": pipeline_result.get("pipeline_id"),
                "pipeline_name": pipeline_name,
                "workspace_id": workspace_id,
                "linked_services_deployed": len(successful_linked_services),
                "linked_services_failed": len(failed_linked_services),
                "notebooks_deployed": len(successful_notebooks),
                "notebooks_failed": len(failed_notebooks),
                "deployed_linked_services": [ls.get("linked_service_name") for ls in successful_linked_services],
                "deployed_notebooks": [n.get("notebook_name") for n in successful_notebooks],
                "failed_linked_services": [ls.get("linked_service_name") for ls in failed_linked_services] if failed_linked_services else None,
                "failed_notebooks": [n.get("notebook_name") for n in failed_notebooks] if failed_notebooks else None
            }

        except Exception as e:
            logger.error(f"Complete pipeline deployment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def deploy_pipeline_from_json(
        self,
        workspace_id: str,
        pipeline_json: Dict[str, Any],
        external_refs: Dict[str, str] = None,
        replace_dataflow: bool = True
    ) -> Dict[str, Any]:
        """
        Deploy a pipeline from existing pipeline JSON definition (e.g., exported from Fabric UI)

        Args:
            workspace_id: Fabric workspace ID
            pipeline_json: Complete pipeline JSON (with name, objectId, properties)
            external_refs: Optional dict to override external reference IDs
                {
                    "notebook_id": "new-notebook-id",
                    "dataflow_id": "new-dataflow-id",
                    "workspace_id": "new-workspace-id",
                    "lakehouse_id": "new-lakehouse-id",
                    "email_connection_id": "new-email-connection-id",
                    "sql_connection_id": "new-sql-connection-id"
                }
            replace_dataflow: If True, replace RefreshDataflow with Copy Data activity

        Returns:
            Dict with deployment result
        """
        try:
            pipeline_name = pipeline_json.get("name", "Imported_Pipeline")
            logger.info(f"Deploying pipeline '{pipeline_name}' from JSON to workspace {workspace_id}")

            # Clone the pipeline JSON to avoid modifying the original
            import copy
            pipeline_def = copy.deepcopy(pipeline_json)

            # Replace RefreshDataflow with Copy Data activity if requested
            if replace_dataflow:
                logger.info("Replacing RefreshDataflow activities with Copy Data activities...")
                pipeline_def = self.replace_dataflow_with_copy_activity(pipeline_def)

            # If external_refs provided, update IDs in the pipeline
            if external_refs:
                logger.info(f"Updating external references: {list(external_refs.keys())}")
                pipeline_def = self._update_external_references(pipeline_def, external_refs)

            # Extract just the properties section for deployment
            # Fabric API expects the pipeline definition in a specific format
            if "properties" in pipeline_def:
                fabric_pipeline_def = {
                    "name": pipeline_name,
                    "properties": pipeline_def["properties"]
                }
            else:
                fabric_pipeline_def = pipeline_def

            # Remove objectId and lastPublishTime if present (these are read-only)
            if "objectId" in fabric_pipeline_def:
                del fabric_pipeline_def["objectId"]
            if "properties" in fabric_pipeline_def and "lastPublishTime" in fabric_pipeline_def["properties"]:
                fabric_pipeline_def["properties"]["lastPublishTime"] = None
            if "properties" in fabric_pipeline_def and "lastModifiedByObjectId" in fabric_pipeline_def["properties"]:
                del fabric_pipeline_def["properties"]["lastModifiedByObjectId"]

            logger.info(f"Pipeline definition prepared with {len(fabric_pipeline_def.get('properties', {}).get('activities', []))} activities")

            # Deploy the pipeline
            result = await self.create_pipeline(
                workspace_id=workspace_id,
                pipeline_name=pipeline_name,
                pipeline_definition=fabric_pipeline_def
            )

            return result

        except Exception as e:
            logger.error(f"Failed to deploy pipeline from JSON: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def replace_dataflow_with_copy_activity(
        self,
        pipeline_def: Dict[str, Any],
        source_path: str = "Files/claimpriorauth",
        target_table: str = "curated_claims"
    ) -> Dict[str, Any]:
        """
        Replace RefreshDataflow activity with Copy Data activity

        Args:
            pipeline_def: Pipeline definition dict
            source_path: Lakehouse Files path to read from
            target_table: Lakehouse table to write to

        Returns:
            Updated pipeline definition with Copy activity instead of RefreshDataflow
        """
        import copy
        updated_def = copy.deepcopy(pipeline_def)

        # Find and replace RefreshDataflow activities
        if "properties" in updated_def and "activities" in updated_def["properties"]:
            for i, activity in enumerate(updated_def["properties"]["activities"]):
                if activity.get("type") == "RefreshDataflow":
                    # Get dependencies from original dataflow activity
                    depends_on = activity.get("dependsOn", [])
                    activity_name = activity.get("name", "curated Data")

                    # Create Copy Data activity to replace it
                    copy_activity = {
                        "name": activity_name,
                        "type": "Copy",
                        "dependsOn": depends_on,
                        "policy": {
                            "timeout": "0.12:00:00",
                            "retry": 0,
                            "retryIntervalInSeconds": 30,
                            "secureOutput": False,
                            "secureInput": False
                        },
                        "typeProperties": {
                            "source": {
                                "type": "ParquetSource",
                                "storeSettings": {
                                    "type": "LakehouseReadSettings",
                                    "recursive": True,
                                    "wildcardFolderPath": source_path,
                                    "wildcardFileName": "*.parquet",
                                    "enablePartitionDiscovery": False
                                },
                                "formatSettings": {
                                    "type": "ParquetReadSettings"
                                }
                            },
                            "sink": {
                                "type": "LakehouseSink",
                                "rootFolder": "Tables",
                                "table": target_table,
                                "tableActionOption": "Append"
                            },
                            "enableStaging": False
                        }
                    }

                    # Replace the activity
                    updated_def["properties"]["activities"][i] = copy_activity
                    logger.info(f"Replaced RefreshDataflow activity '{activity_name}' with Copy Data activity")

                # Also recursively check nested activities (inside ForEach, IfCondition, etc.)
                if "typeProperties" in activity and "activities" in activity["typeProperties"]:
                    nested_def = {"properties": {"activities": activity["typeProperties"]["activities"]}}
                    nested_updated = self.replace_dataflow_with_copy_activity(
                        nested_def, source_path, target_table
                    )
                    activity["typeProperties"]["activities"] = nested_updated["properties"]["activities"]

        return updated_def

    def _update_external_references(
        self,
        pipeline_def: Dict[str, Any],
        external_refs: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Update external reference IDs in pipeline definition

        Args:
            pipeline_def: Pipeline definition dict
            external_refs: Dict of reference IDs to update

        Returns:
            Updated pipeline definition
        """
        import json
        import re

        # Convert to JSON string for regex replacement
        pipeline_str = json.dumps(pipeline_def)

        # Update workspace IDs
        if "workspace_id" in external_refs:
            pipeline_str = re.sub(
                r'"workspaceId"\s*:\s*"[^"]*"',
                f'"workspaceId": "{external_refs["workspace_id"]}"',
                pipeline_str
            )

        # Update notebook ID
        if "notebook_id" in external_refs:
            pipeline_str = re.sub(
                r'"notebookId"\s*:\s*"[^"]*"',
                f'"notebookId": "{external_refs["notebook_id"]}"',
                pipeline_str
            )

        # Update dataflow ID
        if "dataflow_id" in external_refs:
            pipeline_str = re.sub(
                r'"dataflowId"\s*:\s*"[^"]*"',
                f'"dataflowId": "{external_refs["dataflow_id"]}"',
                pipeline_str
            )

        # Update lakehouse ID (artifactId in lakehouse connection)
        if "lakehouse_id" in external_refs:
            pipeline_str = re.sub(
                r'"artifactId"\s*:\s*"[^"]*"',
                f'"artifactId": "{external_refs["lakehouse_id"]}"',
                pipeline_str
            )

        # Update connection IDs in externalReferences
        if "email_connection_id" in external_refs:
            # Find Office365Email activities and replace their connection ID
            pipeline_str = re.sub(
                r'("type"\s*:\s*"Office365Email"[\s\S]{0,500}?"externalReferences"\s*:\s*\{\s*"connection"\s*:\s*)"[^"]*"',
                f'\\1"{external_refs["email_connection_id"]}"',
                pipeline_str
            )

        if "sql_connection_id" in external_refs:
            # Find Script activities and replace their connection ID
            pipeline_str = re.sub(
                r'("type"\s*:\s*"Script"[\s\S]{0,500}?"externalReferences"\s*:\s*\{\s*"connection"\s*:\s*)"[^"]*"',
                f'\\1"{external_refs["sql_connection_id"]}"',
                pipeline_str
            )

        # Convert back to dict
        return json.loads(pipeline_str)
