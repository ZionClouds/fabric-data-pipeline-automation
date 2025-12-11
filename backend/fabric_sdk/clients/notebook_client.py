"""
Notebook Client for Microsoft Fabric SDK

Provides async operations for notebook management.
"""

from __future__ import annotations
import logging
import json
from typing import Dict, Any, Optional, List

from fabric_sdk.clients.base_client import FabricBaseClient
from fabric_sdk.models.notebook import (
    CreateNotebookRequest,
    Notebook,
    Notebooks,
    UpdateNotebookRequest,
    NotebookContent,
    NotebookCell,
    CellType,
    create_code_cell,
    create_parameters_cell,
    create_notebook,
)

logger = logging.getLogger(__name__)


class NotebookClient(FabricBaseClient):
    """
    Client for Notebook operations in Microsoft Fabric.

    Supports creating, managing, and running notebooks.
    """

    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================

    async def list_notebooks(
        self,
        workspace_id: str,
        continuation_token: Optional[str] = None
    ) -> Notebooks:
        """
        List all notebooks in a workspace.

        Args:
            workspace_id: Fabric workspace ID
            continuation_token: Token for pagination

        Returns:
            Notebooks object with list of notebooks
        """
        endpoint = f"/workspaces/{workspace_id}/notebooks"
        params = {}
        if continuation_token:
            params["continuationToken"] = continuation_token

        response = await self.get(endpoint, params=params)
        return self._parse_response(response, Notebooks)

    async def get_notebook(
        self,
        workspace_id: str,
        notebook_id: str
    ) -> Notebook:
        """
        Get a specific notebook.

        Args:
            workspace_id: Fabric workspace ID
            notebook_id: Notebook ID

        Returns:
            Notebook object
        """
        endpoint = f"/workspaces/{workspace_id}/notebooks/{notebook_id}"
        response = await self.get(endpoint)
        return self._parse_response(response, Notebook)

    async def create_notebook(
        self,
        workspace_id: str,
        display_name: str,
        description: Optional[str] = None,
        notebook_content: Optional[NotebookContent] = None,
        code: Optional[str] = None,
        cells: Optional[List[NotebookCell]] = None
    ) -> Dict[str, Any]:
        """
        Create a new notebook.

        Args:
            workspace_id: Fabric workspace ID
            display_name: Notebook display name
            description: Optional description
            notebook_content: Complete NotebookContent object
            code: Simple code string (creates single code cell)
            cells: List of NotebookCell objects

        Returns:
            Dict with notebook_id and creation info
        """
        endpoint = f"/workspaces/{workspace_id}/notebooks"

        # Build notebook content
        if notebook_content:
            content = notebook_content.model_dump(by_alias=True)
        elif cells:
            content = create_notebook(cells).model_dump(by_alias=True)
        elif code:
            content = create_notebook([create_code_cell(code)]).model_dump(by_alias=True)
        else:
            # Create empty notebook
            content = create_notebook([]).model_dump(by_alias=True)

        payload = {
            "displayName": display_name,
            "definition": {
                "format": "ipynb",
                "parts": [
                    {
                        "path": "notebook-content.ipynb",
                        "payload": self._encode_content(content),
                        "payloadType": "InlineBase64"
                    }
                ]
            }
        }

        if description:
            payload["description"] = description

        response = await self.post(endpoint, json_data=payload)
        result = self._handle_response(response, [200, 201, 202])

        notebook_id = result.get('id') or result.get('notebookId') or display_name
        logger.info(f"Notebook created: {notebook_id}")

        # Handle async creation (202)
        if response.status_code == 202:
            await self._wait_for_notebook(workspace_id, display_name, notebook_id)

        return {
            "success": True,
            "notebook_id": notebook_id,
            "notebook_name": display_name,
            "workspace_id": workspace_id
        }

    async def _wait_for_notebook(
        self,
        workspace_id: str,
        display_name: str,
        notebook_id: str,
        max_attempts: int = 30,
        delay_seconds: float = 2.0
    ):
        """Wait for async notebook creation to complete."""
        import asyncio

        logger.info(f"Waiting for notebook '{display_name}' to be ready...")

        for attempt in range(max_attempts):
            await asyncio.sleep(delay_seconds)

            try:
                notebooks = await self.list_notebooks(workspace_id)
                for nb in notebooks.value:
                    if nb.display_name == display_name or nb.id == notebook_id:
                        logger.info(f"Notebook '{display_name}' is ready (attempt {attempt + 1})")
                        return
            except Exception as e:
                logger.debug(f"Still waiting for notebook: {e}")

        logger.warning(f"Notebook creation timeout after {max_attempts * delay_seconds}s")

    async def update_notebook(
        self,
        workspace_id: str,
        notebook_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a notebook's metadata.

        Args:
            workspace_id: Fabric workspace ID
            notebook_id: Notebook ID
            display_name: New display name
            description: New description

        Returns:
            Dict with update status
        """
        endpoint = f"/workspaces/{workspace_id}/notebooks/{notebook_id}"

        payload = {}
        if display_name:
            payload["displayName"] = display_name
        if description is not None:
            payload["description"] = description

        response = await self.patch(endpoint, json_data=payload)
        self._handle_response(response)

        logger.info(f"Notebook updated: {notebook_id}")

        return {
            "success": True,
            "notebook_id": notebook_id
        }

    async def delete_notebook(
        self,
        workspace_id: str,
        notebook_id: str
    ) -> Dict[str, Any]:
        """
        Delete a notebook.

        Args:
            workspace_id: Fabric workspace ID
            notebook_id: Notebook ID

        Returns:
            Dict with deletion status
        """
        endpoint = f"/workspaces/{workspace_id}/notebooks/{notebook_id}"
        response = await self.delete(endpoint)

        if response.status_code == 200:
            logger.info(f"Notebook deleted: {notebook_id}")
            return {"success": True, "notebook_id": notebook_id}
        else:
            raise Exception(f"Failed to delete notebook: {response.text}")

    # =========================================================================
    # DEFINITION OPERATIONS
    # =========================================================================

    async def get_notebook_definition(
        self,
        workspace_id: str,
        notebook_id: str
    ) -> Dict[str, Any]:
        """
        Get the definition (content) of a notebook.

        Args:
            workspace_id: Fabric workspace ID
            notebook_id: Notebook ID

        Returns:
            Decoded notebook content
        """
        endpoint = f"/workspaces/{workspace_id}/notebooks/{notebook_id}/getDefinition"
        response = await self.post(endpoint)
        result = self._handle_response(response, [200, 202])

        if "definition" in result:
            return self.decode_definition(result["definition"])
        return result

    async def update_notebook_definition(
        self,
        workspace_id: str,
        notebook_id: str,
        notebook_content: NotebookContent
    ) -> Dict[str, Any]:
        """
        Update the definition (content) of a notebook.

        Args:
            workspace_id: Fabric workspace ID
            notebook_id: Notebook ID
            notebook_content: New notebook content

        Returns:
            Dict with update status
        """
        endpoint = f"/workspaces/{workspace_id}/notebooks/{notebook_id}/updateDefinition"

        content = notebook_content.model_dump(by_alias=True)

        payload = {
            "definition": {
                "format": "ipynb",
                "parts": [
                    {
                        "path": "notebook-content.ipynb",
                        "payload": self._encode_content(content),
                        "payloadType": "InlineBase64"
                    }
                ]
            }
        }

        response = await self.post(endpoint, json_data=payload)
        self._handle_response(response, [200, 202])

        logger.info(f"Notebook definition updated: {notebook_id}")

        return {
            "success": True,
            "notebook_id": notebook_id
        }

    # =========================================================================
    # RUN OPERATIONS
    # =========================================================================

    async def run_notebook(
        self,
        workspace_id: str,
        notebook_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a notebook on demand.

        Args:
            workspace_id: Fabric workspace ID
            notebook_id: Notebook ID
            parameters: Parameters to pass to the notebook

        Returns:
            Dict with job run status
        """
        endpoint = f"/workspaces/{workspace_id}/items/{notebook_id}/jobs/instances"
        params = {"jobType": "RunNotebook"}

        payload = {}
        if parameters:
            payload["executionData"] = {"parameters": parameters}

        response = await self._request("POST", endpoint, json_data=payload if payload else None, params=params)
        result = self._handle_response(response, [200, 202])

        logger.info(f"Notebook run started: {notebook_id}")

        return {
            "success": True,
            "notebook_id": notebook_id,
            "job_instance_id": result.get("id")
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _encode_content(self, content: Dict[str, Any]) -> str:
        """Encode content to base64."""
        import base64
        content_json = json.dumps(content)
        return base64.b64encode(content_json.encode('utf-8')).decode('utf-8')

    async def create_pyspark_notebook(
        self,
        workspace_id: str,
        display_name: str,
        code_cells: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a PySpark notebook with code cells and optional parameters.

        Args:
            workspace_id: Fabric workspace ID
            display_name: Notebook display name
            code_cells: List of code strings for cells
            parameters: Optional parameters (creates tagged parameters cell)
            description: Optional description

        Returns:
            Dict with notebook creation result
        """
        cells = []

        # Add parameters cell if provided
        if parameters:
            cells.append(create_parameters_cell(parameters))

        # Add code cells
        for code in code_cells:
            cells.append(create_code_cell(code))

        return await self.create_notebook(
            workspace_id=workspace_id,
            display_name=display_name,
            description=description,
            cells=cells
        )
