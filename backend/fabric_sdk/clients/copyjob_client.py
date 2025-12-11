"""
CopyJob Client for Microsoft Fabric SDK

Provides async operations for copy job management.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional

from fabric_sdk.clients.base_client import FabricBaseClient
from fabric_sdk.models.copyjob import (
    CreateCopyJobRequest,
    CopyJob,
    CopyJobs,
    UpdateCopyJobRequest,
    CopyJobDefinitionContent,
)

logger = logging.getLogger(__name__)


class CopyJobClient(FabricBaseClient):
    """
    Client for CopyJob operations in Microsoft Fabric.

    Supports creating, managing, and running copy jobs.
    """

    async def list_copy_jobs(
        self,
        workspace_id: str,
        continuation_token: Optional[str] = None
    ) -> CopyJobs:
        """List all copy jobs in a workspace."""
        endpoint = f"/workspaces/{workspace_id}/copyJobs"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, CopyJobs)

    async def get_copy_job(
        self,
        workspace_id: str,
        copy_job_id: str
    ) -> CopyJob:
        """Get a specific copy job."""
        endpoint = f"/workspaces/{workspace_id}/copyJobs/{copy_job_id}"
        response = await self.get(endpoint)
        return self._parse_response(response, CopyJob)

    async def create_copy_job(
        self,
        workspace_id: str,
        display_name: str,
        description: Optional[str] = None,
        definition: Optional[CopyJobDefinitionContent] = None
    ) -> Dict[str, Any]:
        """
        Create a new copy job.

        Args:
            workspace_id: Fabric workspace ID
            display_name: Copy job display name
            description: Optional description
            definition: Copy job definition content

        Returns:
            Dict with copy_job_id and creation info
        """
        endpoint = f"/workspaces/{workspace_id}/copyJobs"

        payload = {
            "displayName": display_name,
        }

        if description:
            payload["description"] = description

        if definition:
            content = definition.model_dump(by_alias=True)
            payload["definition"] = self.encode_definition(content, "copyjob-content.json")

        response = await self.post(endpoint, json_data=payload)
        result = self._handle_response(response, [200, 201, 202])

        logger.info(f"CopyJob created: {result.get('id', display_name)}")

        return {
            "success": True,
            "copy_job_id": result.get("id"),
            "copy_job_name": display_name,
            "workspace_id": workspace_id
        }

    async def update_copy_job(
        self,
        workspace_id: str,
        copy_job_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a copy job's metadata."""
        endpoint = f"/workspaces/{workspace_id}/copyJobs/{copy_job_id}"

        payload = {}
        if display_name:
            payload["displayName"] = display_name
        if description is not None:
            payload["description"] = description

        response = await self.patch(endpoint, json_data=payload)
        self._handle_response(response)

        return {"success": True, "copy_job_id": copy_job_id}

    async def delete_copy_job(
        self,
        workspace_id: str,
        copy_job_id: str
    ) -> Dict[str, Any]:
        """Delete a copy job."""
        endpoint = f"/workspaces/{workspace_id}/copyJobs/{copy_job_id}"
        response = await self.delete(endpoint)

        if response.status_code == 200:
            return {"success": True, "copy_job_id": copy_job_id}
        else:
            raise Exception(f"Failed to delete copy job: {response.text}")

    async def run_copy_job(
        self,
        workspace_id: str,
        copy_job_id: str
    ) -> Dict[str, Any]:
        """Run a copy job on demand."""
        endpoint = f"/workspaces/{workspace_id}/items/{copy_job_id}/jobs/instances"
        params = {"jobType": "CopyJob"}

        response = await self._request("POST", endpoint, params=params)
        result = self._handle_response(response, [200, 202])

        return {
            "success": True,
            "copy_job_id": copy_job_id,
            "job_instance_id": result.get("id")
        }
