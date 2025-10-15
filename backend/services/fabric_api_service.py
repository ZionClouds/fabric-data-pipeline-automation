"""
Microsoft Fabric API Service for deploying pipelines and notebooks
"""
import httpx
import logging
from typing import Dict, Any, List
import json
import config

logger = logging.getLogger(__name__)

class FabricAPIService:
    """
    Service for interacting with Microsoft Fabric REST API
    """

    def __init__(self):
        self.base_url = "https://api.fabric.microsoft.com/v1"
        self.client_id = config.FABRIC_CLIENT_ID
        self.client_secret = config.FABRIC_CLIENT_SECRET
        self.tenant_id = config.FABRIC_TENANT_ID
        self.access_token = None

    async def get_access_token(self) -> str:
        """
        Get OAuth2 access token for Fabric API
        """
        if self.access_token:
            return self.access_token

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
            self.access_token = token_data["access_token"]
            logger.info("Successfully obtained Fabric API access token")
            return self.access_token

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

    async def create_notebook(
        self,
        workspace_id: str,
        notebook_name: str,
        notebook_code: str
    ) -> Dict[str, Any]:
        """
        Create a notebook in Microsoft Fabric workspace

        Args:
            workspace_id: Fabric workspace ID
            notebook_name: Name of the notebook
            notebook_code: PySpark code for the notebook

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
            notebook_content = {
                "nbformat": 4,
                "nbformat_minor": 2,
                "cells": [
                    {
                        "cell_type": "code",
                        "source": notebook_code,
                        "metadata": {},
                        "outputs": [],
                        "execution_count": None
                    }
                ],
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

            # Use workspace-level Connections API endpoint
            create_url = f"{self.base_url}/workspaces/{workspace_id}/connections"

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
            auth_type = config.get("auth_type", "AccountKey")
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

            if auth_type == "AccountKey" or auth_type == "Key":
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
            elif auth_type == "ManagedIdentity":
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
            elif auth_type == "ManagedIdentity":
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

    def _transform_activities_to_fabric_format(self, activities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform Claude-generated activities to Fabric pipeline format

        Args:
            activities: List of activities from Claude

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
                nested = self._transform_activities_to_fabric_format(config.get('activities', []))
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

        if 'Blob' in source_type or 'DelimitedText' in source_type:
            # Azure Blob Storage source - reference linked service from config
            # Get file path, container, and linked service name from config
            container = source_config.get('container', 'fabric')
            file_path = source_config.get('fileName') or source_config.get('file_path', 'data.csv')
            linked_service = source_config.get('linkedService') or source_config.get('linkedServiceName') or source_config.get('linked_service_name', 'BlobStorage_Connection')

            return {
                "type": "DelimitedTextSource",
                "connection": {
                    "referenceName": linked_service,
                    "type": "ConnectionReference"
                },
                "storeSettings": {
                    "type": "AzureBlobStorageReadSettings",
                    "recursive": False,
                    "wildcardFileName": file_path,
                    "container": container
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
            # Build inline dataset for blob storage
            container = source_config.get('container', 'data')
            file_name = source_config.get('fileName') or source_config.get('file_path', '*.csv')
            linked_service = source_config.get('linkedService') or source_config.get('linkedServiceName', '')

            return {
                "type": "DelimitedTextSource",
                "storeSettings": {
                    "type": "AzureBlobStorageReadSettings",
                    "recursive": False,
                    "wildcardFileName": file_name,
                    "wildcardFolderPath": ""
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
            transformed = self._transform_activities_to_fabric_format(activities)
            fabric_activities = transformed['activities']
            datasets = transformed.get('datasets', [])

            logger.info(f"Transformed to Fabric format: {len(fabric_activities)} activities, {len(datasets)} datasets")
            logger.info(f"Activities: {json.dumps(fabric_activities, indent=2)[:500]}")

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
