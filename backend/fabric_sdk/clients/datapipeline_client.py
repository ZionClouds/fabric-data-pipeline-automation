"""
Data Pipeline Client for Microsoft Fabric SDK

Provides async operations for data pipeline management.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List

from fabric_sdk.clients.base_client import FabricBaseClient
from fabric_sdk.models.datapipeline import (
    CreateDataPipelineRequest,
    DataPipeline,
    DataPipelines,
    UpdateDataPipelineRequest,
    PipelineDefinitionContent,
)
from fabric_sdk.models.core import Definition

logger = logging.getLogger(__name__)


class DataPipelineClient(FabricBaseClient):
    """
    Client for Data Pipeline operations in Microsoft Fabric.

    Supports creating, updating, deleting, and running data pipelines.
    """

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    async def list_data_pipelines(
        self,
        workspace_id: str,
        continuation_token: Optional[str] = None
    ) -> DataPipelines:
        """
        List all data pipelines in a workspace.

        Args:
            workspace_id: Fabric workspace ID
            continuation_token: Token for pagination

        Returns:
            DataPipelines object with list of pipelines
        """
        endpoint = f"/workspaces/{workspace_id}/dataPipelines"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, DataPipelines)

    async def get_data_pipeline(
        self,
        workspace_id: str,
        data_pipeline_id: str
    ) -> DataPipeline:
        """
        Get a specific data pipeline.

        Args:
            workspace_id: Fabric workspace ID
            data_pipeline_id: Data pipeline ID

        Returns:
            DataPipeline object
        """
        endpoint = f"/workspaces/{workspace_id}/dataPipelines/{data_pipeline_id}"
        response = await self.get(endpoint)
        return self._parse_response(response, DataPipeline)

    async def create_data_pipeline(
        self,
        workspace_id: str,
        display_name: str,
        description: Optional[str] = None,
        definition: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new data pipeline.

        Args:
            workspace_id: Fabric workspace ID
            display_name: Pipeline display name
            description: Optional description
            definition: Optional pipeline definition content

        Returns:
            Dict with pipeline_id and creation info
        """
        endpoint = f"/workspaces/{workspace_id}/dataPipelines"

        payload = {
            "displayName": display_name,
        }

        if description:
            payload["description"] = description

        if definition:
            payload["definition"] = self.encode_definition(
                definition,
                "pipeline-content.json"
            )

        response = await self.post(endpoint, json_data=payload)
        result = self._handle_response(response, [200, 201, 202])

        logger.info(f"Pipeline created: {result.get('id', display_name)}")

        return {
            "success": True,
            "pipeline_id": result.get("id"),
            "pipeline_name": display_name,
            "workspace_id": workspace_id
        }

    async def update_data_pipeline(
        self,
        workspace_id: str,
        data_pipeline_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a data pipeline's metadata.

        Args:
            workspace_id: Fabric workspace ID
            data_pipeline_id: Data pipeline ID
            display_name: New display name
            description: New description

        Returns:
            Dict with update status
        """
        endpoint = f"/workspaces/{workspace_id}/dataPipelines/{data_pipeline_id}"

        payload = {}
        if display_name:
            payload["displayName"] = display_name
        if description is not None:
            payload["description"] = description

        response = await self.patch(endpoint, json_data=payload)
        self._handle_response(response)

        logger.info(f"Pipeline updated: {data_pipeline_id}")

        return {
            "success": True,
            "pipeline_id": data_pipeline_id
        }

    async def delete_data_pipeline(
        self,
        workspace_id: str,
        data_pipeline_id: str
    ) -> Dict[str, Any]:
        """
        Delete a data pipeline.

        Args:
            workspace_id: Fabric workspace ID
            data_pipeline_id: Data pipeline ID

        Returns:
            Dict with deletion status
        """
        endpoint = f"/workspaces/{workspace_id}/dataPipelines/{data_pipeline_id}"
        response = await self.delete(endpoint)

        if response.status_code == 200:
            logger.info(f"Pipeline deleted: {data_pipeline_id}")
            return {"success": True, "pipeline_id": data_pipeline_id}
        else:
            raise Exception(f"Failed to delete pipeline: {response.text}")

    # =========================================================================
    # DEFINITION OPERATIONS
    # =========================================================================

    async def get_data_pipeline_definition(
        self,
        workspace_id: str,
        data_pipeline_id: str
    ) -> Dict[str, Any]:
        """
        Get the definition of a data pipeline.

        Args:
            workspace_id: Fabric workspace ID
            data_pipeline_id: Data pipeline ID

        Returns:
            Decoded pipeline definition content
        """
        endpoint = f"/workspaces/{workspace_id}/dataPipelines/{data_pipeline_id}/getDefinition"
        response = await self.post(endpoint)
        result = self._handle_response(response, [200, 202])

        if "definition" in result:
            return self.decode_definition(result["definition"])
        return result

    async def update_data_pipeline_definition(
        self,
        workspace_id: str,
        data_pipeline_id: str,
        definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the definition of a data pipeline.

        Args:
            workspace_id: Fabric workspace ID
            data_pipeline_id: Data pipeline ID
            definition: New pipeline definition content

        Returns:
            Dict with update status
        """
        endpoint = f"/workspaces/{workspace_id}/dataPipelines/{data_pipeline_id}/updateDefinition"

        payload = {
            "definition": self.encode_definition(definition, "pipeline-content.json")
        }

        response = await self.post(endpoint, json_data=payload)
        self._handle_response(response, [200, 202])

        logger.info(f"Pipeline definition updated: {data_pipeline_id}")

        return {
            "success": True,
            "pipeline_id": data_pipeline_id
        }

    # =========================================================================
    # RUN OPERATIONS
    # =========================================================================

    async def run_on_demand_item_job(
        self,
        workspace_id: str,
        data_pipeline_id: str,
        job_type: str = "Pipeline",
        execution_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a data pipeline on demand.

        Args:
            workspace_id: Fabric workspace ID
            data_pipeline_id: Data pipeline ID
            job_type: Job type (default: "Pipeline")
            execution_data: Optional execution parameters

        Returns:
            Dict with job run status
        """
        endpoint = f"/workspaces/{workspace_id}/items/{data_pipeline_id}/jobs/instances"

        params = {"jobType": job_type}

        payload = {}
        if execution_data:
            payload["executionData"] = execution_data

        response = await self.post(endpoint, json_data=payload if payload else None)
        # Add params to the request
        response = await self._request(
            "POST",
            endpoint,
            json_data=payload if payload else None,
            params=params
        )
        result = self._handle_response(response, [200, 202])

        logger.info(f"Pipeline job started: {data_pipeline_id}")

        return {
            "success": True,
            "pipeline_id": data_pipeline_id,
            "job_instance_id": result.get("id")
        }

    async def get_item_job_instance(
        self,
        workspace_id: str,
        item_id: str,
        job_instance_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of a job instance.

        Args:
            workspace_id: Fabric workspace ID
            item_id: Item (pipeline) ID
            job_instance_id: Job instance ID

        Returns:
            Job instance status
        """
        endpoint = f"/workspaces/{workspace_id}/items/{item_id}/jobs/instances/{job_instance_id}"
        response = await self.get(endpoint)
        return self._handle_response(response)

    async def cancel_item_job_instance(
        self,
        workspace_id: str,
        item_id: str,
        job_instance_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a running job instance.

        Args:
            workspace_id: Fabric workspace ID
            item_id: Item (pipeline) ID
            job_instance_id: Job instance ID

        Returns:
            Cancellation status
        """
        endpoint = f"/workspaces/{workspace_id}/items/{item_id}/jobs/instances/{job_instance_id}/cancel"
        response = await self.post(endpoint)
        self._handle_response(response, [200, 202])

        return {
            "success": True,
            "job_instance_id": job_instance_id,
            "status": "Cancelled"
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def create_pipeline_with_activities(
        self,
        workspace_id: str,
        pipeline_name: str,
        activities: List[Dict[str, Any]],
        variables: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pipeline with specified activities.

        Args:
            workspace_id: Fabric workspace ID
            pipeline_name: Pipeline display name
            activities: List of activity definitions
            variables: Pipeline variables
            parameters: Pipeline parameters
            description: Pipeline description

        Returns:
            Dict with pipeline creation result
        """
        pipeline_definition = {
            "properties": {
                "activities": activities,
                "annotations": []
            }
        }

        if variables:
            pipeline_definition["properties"]["variables"] = variables

        if parameters:
            pipeline_definition["properties"]["parameters"] = parameters

        return await self.create_data_pipeline(
            workspace_id=workspace_id,
            display_name=pipeline_name,
            description=description,
            definition=pipeline_definition
        )
