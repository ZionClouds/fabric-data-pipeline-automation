"""
FastAPI Router for AI Pipeline Generation Service

Exposes REST endpoints for:
- Chat interaction for pipeline generation
- Pipeline deployment
- Preview and validation
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header

from services.ai_pipeline.models import (
    ChatRequest,
    ChatResponse,
    DeployRequest,
    DeployResponse,
    PipelineConfig,
)
from services.ai_pipeline.chat_service import AIChatService
from services.ai_pipeline.deployment_service import DeploymentService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/ai-pipeline",
    tags=["AI Pipeline Generation"]
)

# In-memory session storage (in production, use Redis or similar)
_chat_sessions: Dict[str, AIChatService] = {}


def get_access_token(authorization: Optional[str] = Header(None)) -> str:
    """Extract access token from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use 'Bearer <token>'"
        )

    return authorization[7:]  # Remove "Bearer " prefix


def get_chat_service(session_id: str, workspace_id: str, workspace_name: str) -> AIChatService:
    """Get or create chat service for session."""
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = AIChatService(
            session_id=session_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name
        )
    return _chat_sessions[session_id]


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
) -> ChatResponse:
    """
    Process a chat message for pipeline generation.

    This endpoint handles the multi-turn conversation flow:
    1. User describes their use case
    2. AI asks clarifying questions
    3. AI gathers source, PII, transformation, destination, schedule info
    4. Returns pipeline configuration when complete
    """
    try:
        # Get or create chat service
        chat_service = get_chat_service(
            request.session_id,
            request.workspace_id,
            request.workspace_name
        )

        # Process the message
        response = await chat_service.process_message(request.message)

        return response

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/chat/reset")
async def reset_chat(
    session_id: str,
    workspace_id: str,
    workspace_name: str
) -> Dict[str, str]:
    """Reset a chat session to start over."""
    try:
        # Remove existing session
        if session_id in _chat_sessions:
            del _chat_sessions[session_id]

        # Create fresh session
        _chat_sessions[session_id] = AIChatService(
            session_id=session_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name
        )

        return {"status": "success", "message": "Chat session reset"}

    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Session reset failed: {str(e)}"
        )


@router.get("/chat/context/{session_id}")
async def get_chat_context(session_id: str) -> Dict[str, Any]:
    """Get the current context for a chat session."""
    if session_id not in _chat_sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    chat_service = _chat_sessions[session_id]
    context = chat_service.context

    return {
        "session_id": context.session_id,
        "state": context.state.value,
        "workspace_id": context.workspace_id,
        "workspace_name": context.workspace_name,
        "config": context.config.model_dump(),
        "collected_fields": context.collected_fields,
        "message_count": len(context.messages)
    }


# =============================================================================
# DEPLOYMENT ENDPOINTS
# =============================================================================

@router.post("/deploy", response_model=DeployResponse)
async def deploy_pipeline(
    request: DeployRequest,
    access_token: str = Depends(get_access_token)
) -> DeployResponse:
    """
    Deploy a pipeline to Microsoft Fabric.

    Requires:
    - Valid access token in Authorization header
    - Complete pipeline configuration
    """
    try:
        # Create deployment service
        deployment_service = DeploymentService(access_token)

        # Validate configuration
        validation = await deployment_service.validate_config(request.config)
        if not validation["is_valid"]:
            return DeployResponse(
                success=False,
                message=f"Validation failed: {', '.join(validation['errors'])}"
            )

        # Deploy
        response = await deployment_service.deploy(request.config)

        return response

    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deployment failed: {str(e)}"
        )


@router.post("/deploy/from-session/{session_id}", response_model=DeployResponse)
async def deploy_from_session(
    session_id: str,
    access_token: str = Depends(get_access_token)
) -> DeployResponse:
    """
    Deploy the pipeline from a completed chat session.

    This is a convenience endpoint that uses the configuration
    built up during the chat conversation.
    """
    if session_id not in _chat_sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    chat_service = _chat_sessions[session_id]

    if not chat_service.context.state.value == "completed":
        return DeployResponse(
            success=False,
            message="Pipeline configuration is not complete. Please finish the chat conversation first."
        )

    try:
        deployment_service = DeploymentService(access_token)
        response = await deployment_service.deploy(chat_service.context.config)
        return response

    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deployment failed: {str(e)}"
        )


# =============================================================================
# PREVIEW ENDPOINTS
# =============================================================================

@router.post("/preview/pipeline")
async def preview_pipeline(config: PipelineConfig) -> Dict[str, Any]:
    """
    Preview the generated pipeline definition without deploying.

    Returns the pipeline JSON and validation results.
    """
    try:
        deployment_service = DeploymentService("")  # No token needed for preview
        return deployment_service.preview_pipeline(config)

    except Exception as e:
        logger.error(f"Preview error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(e)}"
        )


@router.post("/preview/notebook")
async def preview_notebook(config: PipelineConfig) -> Dict[str, str]:
    """
    Preview the generated notebook code without deploying.

    Returns the PySpark code that would be generated.
    """
    try:
        deployment_service = DeploymentService("")
        notebook_code = deployment_service.preview_notebook(config)
        return {"code": notebook_code}

    except Exception as e:
        logger.error(f"Preview error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(e)}"
        )


@router.post("/preview/schedule")
async def preview_schedule(config: PipelineConfig) -> Dict[str, Any]:
    """
    Preview the generated schedule configuration.

    Returns the trigger/schedule JSON.
    """
    try:
        deployment_service = DeploymentService("")
        return deployment_service.preview_schedule(config)

    except Exception as e:
        logger.error(f"Preview error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(e)}"
        )


@router.get("/preview/session/{session_id}")
async def preview_from_session(session_id: str) -> Dict[str, Any]:
    """
    Preview all generated artifacts from a chat session.
    """
    if session_id not in _chat_sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    chat_service = _chat_sessions[session_id]
    config = chat_service.context.config

    deployment_service = DeploymentService("")

    return {
        "pipeline": deployment_service.preview_pipeline(config),
        "notebook": deployment_service.preview_notebook(config) if config.pii.enabled else None,
        "schedule": deployment_service.preview_schedule(config) if config.schedule.enabled else None
    }


# =============================================================================
# VALIDATION ENDPOINTS
# =============================================================================

@router.post("/validate")
async def validate_config(
    config: PipelineConfig,
    access_token: str = Depends(get_access_token)
) -> Dict[str, Any]:
    """
    Validate pipeline configuration.

    Checks:
    - Required fields are present
    - Workspace is accessible
    - Configuration is internally consistent
    """
    try:
        deployment_service = DeploymentService(access_token)
        return await deployment_service.validate_config(config)

    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/masking-types")
async def get_masking_types() -> Dict[str, Any]:
    """Get available PII masking types with descriptions."""
    return {
        "masking_types": [
            {
                "value": "redact",
                "label": "Redact",
                "description": "Replace with type indicator (e.g., john@email.com → <EMAIL_ADDRESS>)"
            },
            {
                "value": "partial",
                "label": "Partial Mask",
                "description": "Partially mask the value (e.g., john@email.com → j***@***.com)"
            },
            {
                "value": "fake",
                "label": "Fake Data",
                "description": "Replace with realistic fake data (e.g., john@email.com → user_8x7k@masked.com)"
            },
            {
                "value": "hash",
                "label": "Hash",
                "description": "Replace with hash value (e.g., john@email.com → a1b2c3d4e5f6...)"
            }
        ]
    }


@router.get("/file-formats")
async def get_file_formats() -> Dict[str, Any]:
    """Get supported file formats."""
    return {
        "file_formats": [
            {"value": "csv", "label": "CSV", "description": "Comma-separated values"},
            {"value": "parquet", "label": "Parquet", "description": "Apache Parquet columnar format"},
            {"value": "json", "label": "JSON", "description": "JSON files"},
            {"value": "delta", "label": "Delta", "description": "Delta Lake format"},
            {"value": "avro", "label": "Avro", "description": "Apache Avro format"}
        ]
    }


@router.get("/schedule-frequencies")
async def get_schedule_frequencies() -> Dict[str, Any]:
    """Get available schedule frequencies."""
    return {
        "frequencies": [
            {"value": "hourly", "label": "Hourly"},
            {"value": "daily", "label": "Daily"},
            {"value": "weekly", "label": "Weekly"},
            {"value": "monthly", "label": "Monthly"}
        ]
    }


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ai-pipeline-generation"}
