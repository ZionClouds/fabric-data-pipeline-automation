"""
FastAPI Endpoint for Fabric Pipeline Deployment
This integrates with your AI chat backend to deploy pipelines
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

# Import the deployment function
from deploy_pipeline_api import deploy_fabric_pipeline

# Create router
router = APIRouter(prefix="/api/fabric", tags=["fabric-deployment"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PipelineDeploymentRequest(BaseModel):
    """Request model for pipeline deployment"""
    workspace_name: str
    lakehouse_name: str
    source_folder: str  # e.g., "bronze"
    output_folder: str  # e.g., "silver"
    pipeline_name: str
    warehouse_name: Optional[str] = "jay-dev-warehouse"
    notebook_name: Optional[str] = "PHI_PII_detection"

    class Config:
        json_schema_extra = {
            "example": {
                "workspace_name": "jay-dev",
                "lakehouse_name": "jay_dev_lakehouse",
                "source_folder": "bronze",
                "output_folder": "silver",
                "pipeline_name": "Customer_Pipeline",
                "warehouse_name": "jay-dev-warehouse",
                "notebook_name": "PHI_PII_detection"
            }
        }


class PipelineDeploymentResponse(BaseModel):
    """Response model for pipeline deployment"""
    status: str
    message: str
    workspace_id: Optional[str] = None
    workspace_name: Optional[str] = None
    lakehouse_id: Optional[str] = None
    lakehouse_name: Optional[str] = None
    notebook_id: Optional[str] = None
    notebook_name: Optional[str] = None
    pipeline_id: Optional[str] = None
    pipeline_name: Optional[str] = None
    source_folder: Optional[str] = None
    output_folder: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/deploy-pipeline", response_model=PipelineDeploymentResponse)
async def deploy_pipeline_endpoint(request: PipelineDeploymentRequest):
    """
    Deploy a Fabric pipeline based on user input from AI chat.

    This endpoint is called when the user clicks "Generate Pipeline" button
    after providing all required information through the AI chat.

    Args:
        request: PipelineDeploymentRequest with all deployment parameters

    Returns:
        PipelineDeploymentResponse with deployment status and component IDs
    """
    try:
        # Validate input
        if not request.workspace_name:
            raise HTTPException(status_code=400, detail="Workspace name is required")
        if not request.lakehouse_name:
            raise HTTPException(status_code=400, detail="Lakehouse name is required")
        if not request.source_folder:
            raise HTTPException(status_code=400, detail="Source folder is required")
        if not request.output_folder:
            raise HTTPException(status_code=400, detail="Output folder is required")
        if not request.pipeline_name:
            raise HTTPException(status_code=400, detail="Pipeline name is required")

        # Call deployment function
        result = await deploy_fabric_pipeline(
            workspace_name=request.workspace_name,
            lakehouse_name=request.lakehouse_name,
            source_folder=request.source_folder,
            output_folder=request.output_folder,
            pipeline_name=request.pipeline_name,
            warehouse_name=request.warehouse_name,
            notebook_name=request.notebook_name
        )

        # Return response
        return PipelineDeploymentResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-workspace/{workspace_name}")
async def validate_workspace(workspace_name: str):
    """
    Validate if a workspace exists.
    This can be called by AI chat before starting the deployment flow.
    """
    try:
        from deploy_pipeline_api import get_access_token, find_workspace

        token = await get_access_token()
        workspace = await find_workspace(token, workspace_name)

        if workspace:
            return {
                "status": "success",
                "exists": True,
                "workspace_id": workspace.get("id"),
                "workspace_name": workspace.get("displayName")
            }
        else:
            return {
                "status": "success",
                "exists": False,
                "message": f"Workspace '{workspace_name}' not found"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-lakehouses/{workspace_name}")
async def list_lakehouses(workspace_name: str):
    """
    List all lakehouses in a workspace.
    This helps AI chat provide suggestions to the user.
    """
    try:
        from deploy_pipeline_api import get_access_token, find_workspace
        import httpx

        token = await get_access_token()
        workspace = await find_workspace(token, workspace_name)

        if not workspace:
            raise HTTPException(status_code=404, detail=f"Workspace '{workspace_name}' not found")

        workspace_id = workspace.get("id")

        # Get lakehouses
        url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"type": "Lakehouse"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            lakehouses = response.json().get("value", [])

            return {
                "status": "success",
                "workspace_name": workspace_name,
                "lakehouses": [
                    {
                        "id": lh.get("id"),
                        "name": lh.get("displayName"),
                        "description": lh.get("description")
                    }
                    for lh in lakehouses
                ]
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTEGRATION WITH MAIN APP
# ============================================================================
"""
To integrate this with your main FastAPI app (main.py), add this to main.py:

```python
from fabric_deployment_endpoint import router as fabric_router

# Add the router
app.include_router(fabric_router)
```

Then the endpoints will be available at:
- POST /api/fabric/deploy-pipeline
- GET /api/fabric/validate-workspace/{workspace_name}
- GET /api/fabric/list-lakehouses/{workspace_name}
"""
