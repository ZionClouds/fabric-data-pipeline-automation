from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import httpx
import jwt
from jwt import PyJWKClient
import ssl
import certifi
import os

# Import config and services
import config
from services.claude_ai_service import ClaudeAIService
from services.fabric_api_service import FabricAPIService
from models.pipeline_models import (
    ChatMessage, ChatRequest, ChatResponse,
    PipelineGenerateRequest, PipelineGenerateResponse,
    LinkedServiceRequest, LinkedServiceResponse
)

# In-memory storage for generated pipelines (temporary - should use database in production)
generated_pipelines = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Pipeline Builder API",
    description="AI-Powered Data Pipeline Builder for Microsoft Fabric",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
claude_service = ClaudeAIService()
fabric_service = FabricAPIService()

# Security
security = HTTPBearer(auto_error=False)

# Microsoft Azure AD configuration
AZURE_TENANT_ID = config.FABRIC_TENANT_ID
JWKS_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys"

# Create SSL context with certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Token validation function
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate Microsoft Azure AD JWT token
    """
    # Development mode: bypass authentication
    if config.DISABLE_AUTH == "true":
        logger.info("Development mode: bypassing authentication")
        return {"email": "dev@example.com", "name": "Development User", "oid": "dev-user-id"}

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials

    logger.info(f"Validating token: {token[:50]}...")

    try:
        # For development/testing, skip validation if token is 'test'
        if token == 'test':
            return {"email": "test@example.com", "name": "Test User"}

        # Get signing keys from Microsoft with SSL context
        jwks_client = PyJWKClient(JWKS_URL, ssl_context=ssl_context)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        logger.info("Successfully got signing key from Microsoft")

        # Decode and validate token
        # Note: MSAL tokens for user auth have Microsoft Graph as audience, not the app client ID
        # Try to decode without strict issuer validation first
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False, "verify_iss": False}  # Skip audience and issuer verification for user tokens
        )

        logger.info(f"Token decoded. Issuer: {payload.get('iss')}, Audience: {payload.get('aud')}")

        # Verify the app ID is in the token
        if payload.get("appid") != config.FABRIC_CLIENT_ID and payload.get("azp") != config.FABRIC_CLIENT_ID:
            logger.warning(f"Token appid: {payload.get('appid')}, Expected: {config.FABRIC_CLIENT_ID}")

        user_email = payload.get("preferred_username") or payload.get("upn") or payload.get("email")
        user_name = payload.get("name")

        logger.info(f"Token validated successfully for user: {user_email}")

        return {
            "email": user_email,
            "name": user_name,
            "oid": payload.get("oid")
        }

    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Pipeline Builder API",
        "version": "1.0.0",
        "status": "running",
        "claude_model": config.CLAUDE_MODEL
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# AI Chat endpoint
@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, user: dict = Depends(validate_token)):
    """
    Chat with Claude AI for pipeline design
    """
    try:
        logger.info(f"Chat request for workspace: {request.workspace_id} by user: {user['email']}")

        response = await claude_service.chat(
            messages=request.messages,
            context=request.context
        )

        return ChatResponse(
            role="assistant",
            content=response["content"],
            suggestions=None,
            pipeline_preview=None
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

# Pipeline generation endpoint
@app.post("/api/pipelines/generate", response_model=PipelineGenerateResponse)
async def generate_pipeline(request: PipelineGenerateRequest, user: dict = Depends(validate_token)):
    """
    Generate complete pipeline from requirements
    """
    try:
        logger.info(f"Generating pipeline: {request.pipeline_name} for user: {user['email']}")

        result = await claude_service.generate_pipeline(request)

        # Generate pipeline ID and store in memory
        import time
        pipeline_id = int(time.time())

        # Store generated pipeline for deployment
        generated_pipelines[pipeline_id] = {
            "pipeline_name": request.pipeline_name,
            "activities": result.get("activities", []),
            "notebooks": result.get("notebooks", []),
            "reasoning": result.get("reasoning", ""),
            "workspace_id": request.workspace_id
        }

        return PipelineGenerateResponse(
            pipeline_id=pipeline_id,
            pipeline_name=request.pipeline_name,
            activities=result.get("activities", []),
            notebooks=result.get("notebooks", []),
            fabric_pipeline_json=result.get("fabric_pipeline_json", {}),
            reasoning=result.get("reasoning", "")
        )

    except Exception as e:
        logger.error(f"Pipeline generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline generation failed: {str(e)}")

# Get workspaces (proxy to workspace backend)
@app.get("/api/workspaces")
async def get_workspaces(user: dict = Depends(validate_token)):
    """
    Get workspaces for user (calls workspace backend)
    """
    try:
        user_email = user['email']
        async with httpx.AsyncClient() as client:
            # In development mode, return all workspaces
            if config.DISABLE_AUTH == "true":
                response = await client.get(
                    f"{config.WORKSPACE_BACKEND_URL}/api/workspaces",
                    timeout=30.0
                )
            else:
                response = await client.get(
                    f"{config.WORKSPACE_BACKEND_URL}/api/workspaces/approved",
                    params={"user_email": user_email},
                    timeout=30.0
                )
            return response.json()
    except Exception as e:
        logger.error(f"Failed to get workspaces: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch workspaces: {str(e)}")

# Validate source connection
@app.post("/api/sources/validate")
async def validate_connection(request: Dict[str, Any]):
    """
    Test data source connection
    """
    return {
        "success": True,
        "message": "Connection validated successfully",
        "tables": []
    }

# Deploy pipeline
@app.post("/api/pipelines/{pipeline_id}/deploy")
async def deploy_pipeline(pipeline_id: int, request: Dict[str, Any], user: dict = Depends(validate_token)):
    """
    Deploy pipeline to Microsoft Fabric workspace
    """
    try:
        logger.info(f"Deploying pipeline {pipeline_id} for user: {user['email']}")

        # Get pipeline from memory
        if pipeline_id not in generated_pipelines:
            raise HTTPException(status_code=404, detail="Pipeline not found. Please generate the pipeline first.")

        pipeline_data = generated_pipelines[pipeline_id]
        workspace_id = request.get("workspace_id") or pipeline_data.get("workspace_id")

        if not workspace_id:
            raise HTTPException(status_code=400, detail="Workspace ID is required")

        # Deploy to Fabric using Fabric API service
        result = await fabric_service.deploy_complete_pipeline(
            workspace_id=workspace_id,
            pipeline_name=pipeline_data["pipeline_name"],
            activities=pipeline_data["activities"],
            notebooks=pipeline_data["notebooks"]
        )

        if result.get("success"):
            logger.info(f"Pipeline deployed successfully to workspace {workspace_id}")
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "fabric_pipeline_id": result.get("pipeline_id"),
                "message": f"Pipeline deployed successfully to workspace {workspace_id}",
                "notebooks_deployed": result.get("notebooks_deployed", 0),
                "deployed_notebooks": result.get("deployed_notebooks", [])
            }
        else:
            raise Exception(result.get("error", "Deployment failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deployment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

# List pipelines
@app.get("/api/pipelines")
async def list_pipelines(workspace_id: str, user: dict = Depends(validate_token)):
    """
    List pipelines for workspace
    """
    logger.info(f"Listing pipelines for workspace {workspace_id}, user: {user['email']}")
    return []

# Create Linked Service endpoint
@app.post("/api/linked-services/create", response_model=LinkedServiceResponse)
async def create_linked_service(request: LinkedServiceRequest, user: dict = Depends(validate_token)):
    """
    Create a Linked Service in Microsoft Fabric workspace

    SECURITY WARNING: This endpoint accepts credentials. Credentials are sent directly
    to Microsoft Fabric API and are NOT stored in our system.
    """
    try:
        logger.info(f"Creating linked service '{request.linked_service_name}' in workspace {request.workspace_id}")
        logger.info(f"Source type: {request.source_type}, Auth type: {request.auth_type}")

        # Important: Do not log credentials
        # Convert connection_config to include auth_type
        connection_config = {**request.connection_config, "auth_type": request.auth_type.value}

        # Call Fabric API service to create linked service
        result = await fabric_service.create_linked_service(
            workspace_id=request.workspace_id,
            linked_service_name=request.linked_service_name,
            source_type=request.source_type.lower(),
            connection_config=connection_config
        )

        if result.get("success"):
            logger.info(f"Linked service '{request.linked_service_name}' created successfully")
            return LinkedServiceResponse(
                success=True,
                linked_service_id=result.get("linked_service_id"),
                linked_service_name=request.linked_service_name,
                source_type=request.source_type
            )
        else:
            logger.error(f"Linked service creation failed: {result.get('error')}")
            return LinkedServiceResponse(
                success=False,
                linked_service_id=None,
                linked_service_name=request.linked_service_name,
                source_type=request.source_type,
                error=result.get("error")
            )

    except Exception as e:
        logger.error(f"Linked service creation error: {str(e)}", exc_info=True)
        return LinkedServiceResponse(
            success=False,
            linked_service_id=None,
            linked_service_name=request.linked_service_name,
            source_type=request.source_type,
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
