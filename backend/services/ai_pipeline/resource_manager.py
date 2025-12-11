"""
Resource Manager for AI Pipeline Service

Manages Fabric resources: connections, environments, lakehouses, and notebooks.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List

# Import Fabric SDK services
try:
    from fabric_sdk.services.connections_service import ConnectionsService
    from fabric_sdk.services.environment_service import EnvironmentService
    from fabric_sdk.services.lakehouse_service import LakehouseService
    from fabric_sdk.services.notebook_service import NotebookService
    from fabric_sdk.services.item_service import ItemService
    FABRIC_SDK_AVAILABLE = True
except ImportError:
    FABRIC_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Manages Fabric resources for pipeline deployment.

    Handles:
    - Checking and creating connections
    - Managing environments (for Presidio)
    - Getting default or creating lakehouses
    - Creating notebooks
    """

    def __init__(self, access_token: str):
        """
        Initialize the resource manager.

        Args:
            access_token: Bearer token for Fabric API authentication
        """
        self.access_token = access_token
        self._init_services()

    def _init_services(self):
        """Initialize Fabric SDK services."""
        if FABRIC_SDK_AVAILABLE:
            self.connections_service = ConnectionsService(self.access_token)
            self.environment_service = EnvironmentService(self.access_token)
            self.lakehouse_service = LakehouseService(self.access_token)
            self.notebook_service = NotebookService(self.access_token)
            self.item_service = ItemService(self.access_token)
        else:
            logger.warning("Fabric SDK not available, using mock services")
            self.connections_service = None
            self.environment_service = None
            self.lakehouse_service = None
            self.notebook_service = None
            self.item_service = None

    # =========================================================================
    # CONNECTION MANAGEMENT
    # =========================================================================

    async def get_or_create_blob_connection(
        self,
        workspace_id: str,
        storage_account: str,
        container: str,
        connection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing connection or create a new one for Azure Blob Storage.

        Args:
            workspace_id: Workspace ID
            storage_account: Azure storage account name
            container: Container name
            connection_name: Optional connection name

        Returns:
            Connection details with ID
        """
        # Generate connection name if not provided
        if not connection_name:
            connection_name = f"conn_{storage_account}_{container}"

        # Check for existing connection
        existing = await self._find_existing_connection(
            workspace_id,
            storage_account,
            container
        )

        if existing:
            logger.info(f"Found existing connection: {existing.get('id')}")
            return existing

        # Create new connection
        logger.info(f"Creating new connection: {connection_name}")
        return await self._create_blob_connection(
            workspace_id,
            storage_account,
            container,
            connection_name
        )

    async def _find_existing_connection(
        self,
        workspace_id: str,
        storage_account: str,
        container: str
    ) -> Optional[Dict[str, Any]]:
        """Find existing connection for the given storage account and container."""
        try:
            if not self.connections_service:
                return None

            # List all connections in workspace
            connections = await self.connections_service.list_connections(workspace_id)

            for conn in connections.get("value", []):
                # Check if connection matches storage account
                conn_props = conn.get("properties", {})
                if (conn_props.get("storageAccountName") == storage_account or
                    storage_account in conn.get("name", "")):
                    return conn

            return None

        except Exception as e:
            logger.error(f"Error finding connection: {e}")
            return None

    async def _create_blob_connection(
        self,
        workspace_id: str,
        storage_account: str,
        container: str,
        connection_name: str
    ) -> Dict[str, Any]:
        """Create a new Azure Blob Storage connection."""
        try:
            if not self.connections_service:
                # Return mock connection for testing
                return {
                    "id": f"mock-connection-{storage_account}",
                    "name": connection_name,
                    "type": "AzureBlobStorage",
                    "properties": {
                        "storageAccountName": storage_account,
                        "container": container
                    }
                }

            connection_config = {
                "name": connection_name,
                "type": "AzureBlobStorage",
                "typeProperties": {
                    "serviceUri": f"https://{storage_account}.blob.core.windows.net",
                    "containerName": container
                },
                "annotations": [
                    "auto-generated",
                    "ai-pipeline-service"
                ]
            }

            result = await self.connections_service.create_connection(
                workspace_id,
                connection_config
            )

            return result

        except Exception as e:
            logger.error(f"Error creating connection: {e}")
            raise

    # =========================================================================
    # ENVIRONMENT MANAGEMENT (for Presidio)
    # =========================================================================

    async def get_or_create_presidio_environment(
        self,
        workspace_id: str,
        environment_name: str = "PresidioEnvironment"
    ) -> Dict[str, Any]:
        """
        Get existing or create new environment with Presidio libraries.

        Args:
            workspace_id: Workspace ID
            environment_name: Name for the environment

        Returns:
            Environment details with ID
        """
        # Check for existing environment
        existing = await self._find_presidio_environment(workspace_id)

        if existing:
            logger.info(f"Found existing Presidio environment: {existing.get('id')}")
            return existing

        # Create new environment
        logger.info(f"Creating new Presidio environment: {environment_name}")
        return await self._create_presidio_environment(workspace_id, environment_name)

    async def _find_presidio_environment(
        self,
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find existing environment with Presidio libraries."""
        try:
            if not self.environment_service:
                return None

            # List all environments in workspace
            environments = await self.environment_service.list_environments(workspace_id)

            for env in environments.get("value", []):
                # Check if environment has Presidio in name or tags
                env_name = env.get("displayName", "").lower()
                if "presidio" in env_name or "pii" in env_name:
                    return env

            return None

        except Exception as e:
            logger.error(f"Error finding environment: {e}")
            return None

    async def _create_presidio_environment(
        self,
        workspace_id: str,
        environment_name: str
    ) -> Dict[str, Any]:
        """Create a new environment with Presidio libraries."""
        try:
            if not self.environment_service:
                # Return mock environment for testing
                return {
                    "id": f"mock-environment-presidio",
                    "displayName": environment_name,
                    "type": "Environment",
                    "libraries": ["presidio-analyzer", "presidio-anonymizer"]
                }

            # Create environment
            environment_config = {
                "displayName": environment_name,
                "description": "Environment with Presidio libraries for PII detection and masking"
            }

            result = await self.environment_service.create_environment(
                workspace_id,
                environment_config
            )

            environment_id = result.get("id")

            # Add Presidio libraries to environment
            await self._add_presidio_libraries(workspace_id, environment_id)

            return result

        except Exception as e:
            logger.error(f"Error creating environment: {e}")
            raise

    async def _add_presidio_libraries(
        self,
        workspace_id: str,
        environment_id: str
    ) -> None:
        """Add Presidio libraries to environment."""
        try:
            if not self.environment_service:
                return

            libraries = [
                {"name": "presidio-analyzer", "version": "2.2.0"},
                {"name": "presidio-anonymizer", "version": "2.2.0"},
                {"name": "spacy", "version": "3.7.0"}
            ]

            for lib in libraries:
                await self.environment_service.add_library(
                    workspace_id,
                    environment_id,
                    lib
                )

            logger.info(f"Added Presidio libraries to environment {environment_id}")

        except Exception as e:
            logger.error(f"Error adding libraries: {e}")
            raise

    # =========================================================================
    # LAKEHOUSE MANAGEMENT
    # =========================================================================

    async def get_default_lakehouse(
        self,
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the default lakehouse for a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            Default lakehouse details or None
        """
        try:
            if not self.lakehouse_service:
                # Return mock lakehouse for testing
                return {
                    "id": f"mock-lakehouse-default",
                    "displayName": "DefaultLakehouse",
                    "type": "Lakehouse"
                }

            # List all lakehouses in workspace
            lakehouses = await self.lakehouse_service.list_lakehouses(workspace_id)

            lakehouse_list = lakehouses.get("value", [])

            if not lakehouse_list:
                # No lakehouse exists, create default
                return await self.create_lakehouse(workspace_id, "DefaultLakehouse")

            # Return the first lakehouse as default
            return lakehouse_list[0]

        except Exception as e:
            logger.error(f"Error getting default lakehouse: {e}")
            return None

    async def create_lakehouse(
        self,
        workspace_id: str,
        lakehouse_name: str
    ) -> Dict[str, Any]:
        """
        Create a new lakehouse.

        Args:
            workspace_id: Workspace ID
            lakehouse_name: Name for the lakehouse

        Returns:
            Created lakehouse details
        """
        try:
            if not self.lakehouse_service:
                # Return mock lakehouse for testing
                return {
                    "id": f"mock-lakehouse-{lakehouse_name.lower()}",
                    "displayName": lakehouse_name,
                    "type": "Lakehouse"
                }

            lakehouse_config = {
                "displayName": lakehouse_name,
                "description": "Auto-generated lakehouse for data pipeline"
            }

            result = await self.lakehouse_service.create_lakehouse(
                workspace_id,
                lakehouse_config
            )

            logger.info(f"Created lakehouse: {result.get('id')}")
            return result

        except Exception as e:
            logger.error(f"Error creating lakehouse: {e}")
            raise

    # =========================================================================
    # NOTEBOOK MANAGEMENT
    # =========================================================================

    async def create_notebook(
        self,
        workspace_id: str,
        notebook_name: str,
        notebook_content: str,
        environment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a notebook in the workspace.

        Args:
            workspace_id: Workspace ID
            notebook_name: Name for the notebook
            notebook_content: Notebook content (ipynb JSON string)
            environment_id: Optional environment ID to attach

        Returns:
            Created notebook details with ID
        """
        try:
            if not self.notebook_service:
                # Return mock notebook for testing
                return {
                    "id": f"mock-notebook-{notebook_name.lower().replace(' ', '-')}",
                    "displayName": notebook_name,
                    "type": "Notebook"
                }

            notebook_config = {
                "displayName": notebook_name,
                "description": "Auto-generated notebook for data processing",
                "definition": {
                    "format": "ipynb",
                    "parts": [
                        {
                            "path": "notebook-content.ipynb",
                            "payload": notebook_content,
                            "payloadType": "InlineBase64"
                        }
                    ]
                }
            }

            # Add environment reference if provided
            if environment_id:
                notebook_config["environmentId"] = environment_id

            result = await self.notebook_service.create_notebook(
                workspace_id,
                notebook_config
            )

            logger.info(f"Created notebook: {result.get('id')}")
            return result

        except Exception as e:
            logger.error(f"Error creating notebook: {e}")
            raise

    async def update_notebook(
        self,
        workspace_id: str,
        notebook_id: str,
        notebook_content: str
    ) -> Dict[str, Any]:
        """
        Update an existing notebook.

        Args:
            workspace_id: Workspace ID
            notebook_id: Notebook ID to update
            notebook_content: New notebook content

        Returns:
            Updated notebook details
        """
        try:
            if not self.notebook_service:
                return {"id": notebook_id, "status": "updated"}

            update_config = {
                "definition": {
                    "format": "ipynb",
                    "parts": [
                        {
                            "path": "notebook-content.ipynb",
                            "payload": notebook_content,
                            "payloadType": "InlineBase64"
                        }
                    ]
                }
            }

            result = await self.notebook_service.update_notebook(
                workspace_id,
                notebook_id,
                update_config
            )

            return result

        except Exception as e:
            logger.error(f"Error updating notebook: {e}")
            raise

    # =========================================================================
    # PIPELINE MANAGEMENT
    # =========================================================================

    async def create_pipeline(
        self,
        workspace_id: str,
        pipeline_name: str,
        pipeline_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a pipeline in the workspace.

        Args:
            workspace_id: Workspace ID
            pipeline_name: Name for the pipeline
            pipeline_definition: Pipeline JSON definition

        Returns:
            Created pipeline details with ID
        """
        try:
            if not self.item_service:
                # Return mock pipeline for testing
                return {
                    "id": f"mock-pipeline-{pipeline_name.lower().replace(' ', '-')}",
                    "displayName": pipeline_name,
                    "type": "DataPipeline"
                }

            import json
            import base64

            # Encode pipeline definition
            pipeline_json = json.dumps(pipeline_definition)
            pipeline_base64 = base64.b64encode(pipeline_json.encode()).decode()

            pipeline_config = {
                "displayName": pipeline_name,
                "type": "DataPipeline",
                "description": "Auto-generated data pipeline",
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

            result = await self.item_service.create_item(
                workspace_id,
                pipeline_config
            )

            logger.info(f"Created pipeline: {result.get('id')}")
            return result

        except Exception as e:
            logger.error(f"Error creating pipeline: {e}")
            raise

    # =========================================================================
    # TRIGGER/SCHEDULE MANAGEMENT
    # =========================================================================

    async def create_schedule(
        self,
        workspace_id: str,
        pipeline_id: str,
        schedule_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a schedule/trigger for a pipeline.

        Args:
            workspace_id: Workspace ID
            pipeline_id: Pipeline ID to schedule
            schedule_config: Schedule configuration

        Returns:
            Created schedule details
        """
        try:
            if not self.item_service:
                # Return mock schedule for testing
                return {
                    "id": f"mock-schedule-{pipeline_id}",
                    "pipelineId": pipeline_id,
                    "status": "enabled"
                }

            # Note: Fabric API for triggers may vary
            # This is a placeholder for the actual implementation
            trigger_config = {
                "displayName": schedule_config.get("name", f"Trigger_{pipeline_id}"),
                "type": "ScheduleTrigger",
                "properties": schedule_config.get("properties", {})
            }

            # The actual API call would depend on Fabric's trigger API
            # This may need adjustment based on actual Fabric API
            result = await self.item_service.create_item(
                workspace_id,
                trigger_config
            )

            return result

        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            raise

    # =========================================================================
    # VALIDATION HELPERS
    # =========================================================================

    async def validate_workspace_access(
        self,
        workspace_id: str
    ) -> bool:
        """
        Validate that we have access to the workspace.

        Args:
            workspace_id: Workspace ID to validate

        Returns:
            True if accessible, False otherwise
        """
        try:
            if not self.item_service:
                return True  # Assume valid in mock mode

            # Try to list items in workspace to verify access
            await self.item_service.list_items(workspace_id)
            return True

        except Exception as e:
            logger.error(f"Workspace access validation failed: {e}")
            return False

    async def validate_connection(
        self,
        workspace_id: str,
        connection_id: str
    ) -> bool:
        """
        Validate that a connection exists and is accessible.

        Args:
            workspace_id: Workspace ID
            connection_id: Connection ID to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            if not self.connections_service:
                return True  # Assume valid in mock mode

            connection = await self.connections_service.get_connection(
                workspace_id,
                connection_id
            )
            return connection is not None

        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_fabric_portal_url(
        self,
        workspace_id: str,
        item_type: str,
        item_id: str
    ) -> str:
        """
        Generate URL to view item in Fabric portal.

        Args:
            workspace_id: Workspace ID
            item_type: Type of item (pipeline, notebook, etc.)
            item_id: Item ID

        Returns:
            Fabric portal URL
        """
        base_url = "https://app.fabric.microsoft.com"

        type_paths = {
            "pipeline": "datapipeline",
            "notebook": "synapse-notebook",
            "lakehouse": "lakehouse",
            "environment": "environment"
        }

        item_path = type_paths.get(item_type.lower(), item_type.lower())

        return f"{base_url}/groups/{workspace_id}/{item_path}/{item_id}"

    async def get_workspace_resources(
        self,
        workspace_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all relevant resources in a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            Dictionary of resource types and their items
        """
        resources = {
            "lakehouses": [],
            "connections": [],
            "environments": [],
            "notebooks": [],
            "pipelines": []
        }

        try:
            if self.lakehouse_service:
                lakehouses = await self.lakehouse_service.list_lakehouses(workspace_id)
                resources["lakehouses"] = lakehouses.get("value", [])

            if self.connections_service:
                connections = await self.connections_service.list_connections(workspace_id)
                resources["connections"] = connections.get("value", [])

            if self.environment_service:
                environments = await self.environment_service.list_environments(workspace_id)
                resources["environments"] = environments.get("value", [])

            if self.notebook_service:
                notebooks = await self.notebook_service.list_notebooks(workspace_id)
                resources["notebooks"] = notebooks.get("value", [])

            if self.item_service:
                items = await self.item_service.list_items(workspace_id, type="DataPipeline")
                resources["pipelines"] = items.get("value", [])

        except Exception as e:
            logger.error(f"Error getting workspace resources: {e}")

        return resources
