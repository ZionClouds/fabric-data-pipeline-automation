"""
API endpoints for conversations and jobs
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.database_service import get_db_service
from models.database_models import ConversationStatus, JobStatus

router = APIRouter(prefix="/api", tags=["conversations", "jobs"])


# ==================== Request/Response Models ====================

class ConversationResponse(BaseModel):
    """Response model for conversation"""
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: str
    title: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    workspace_id: Optional[str] = None
    lakehouse_id: Optional[str] = None
    workspace_name: Optional[str] = None
    lakehouse_name: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    message_count: Optional[int] = None


class ConversationWithMessagesResponse(BaseModel):
    """Response model for conversation with messages"""
    model_config = ConfigDict(populate_by_name=True)

    conversation_id: str
    title: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    workspace_id: Optional[str] = None
    lakehouse_id: Optional[str] = None
    workspace_name: Optional[str] = None
    lakehouse_name: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="extra_metadata")
    messages: List[Dict[str, Any]]


class JobResponse(BaseModel):
    """Response model for job"""
    model_config = ConfigDict(populate_by_name=True)

    job_id: str
    conversation_id: Optional[str] = None
    job_type: str
    status: str
    pipeline_generation_status: str
    pipeline_deployment_status: str
    pipeline_preview_status: str
    pipeline_definition: Optional[Dict[str, Any]] = None
    pipeline_id: Optional[str] = None
    pipeline_name: Optional[str] = None
    workspace_id: Optional[str] = None
    lakehouse_id: Optional[str] = None
    workspace_name: Optional[str] = None
    lakehouse_name: Optional[str] = None
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="extra_metadata")


class LogResponse(BaseModel):
    """Response model for log"""
    model_config = ConfigDict(populate_by_name=True)

    log_id: int
    timestamp: str
    level: str
    service: str
    conversation_id: Optional[str] = None
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias="extra_metadata")


# ==================== Conversation Endpoints ====================

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    user_id: Optional[str] = Query(None),
    user_email: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get conversations for a user
    """
    try:
        db_service = get_db_service()
        conversations = db_service.get_conversations_by_user(
            user_id=user_id,
            user_email=user_email,
            status=status,
            limit=limit
        )

        # Add message count for each conversation
        for conv in conversations:
            messages = db_service.get_conversation_messages(conv['conversation_id'])
            conv['message_count'] = len(messages)

        return conversations

    except Exception as e:
        try:
            db_service = get_db_service()
            db_service.log_error(
                service="conversation_endpoints",
                message=f"Error getting conversations: {str(e)}",
                user_id=user_id,
                metadata={"user_email": user_email, "status": status}
            )
        except:
            # If logging fails (e.g., DB unavailable), just print to console
            print(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversations: {str(e)}")


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessagesResponse)
async def get_conversation(conversation_id: str):
    """
    Get a specific conversation with all messages
    """
    try:
        db_service = get_db_service()
        conversation = db_service.get_conversation_with_messages(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        try:
            db_service = get_db_service()
            db_service.log_error(
                service="conversation_endpoints",
                message=f"Error getting conversation {conversation_id}: {str(e)}",
                conversation_id=conversation_id
            )
        except:
            print(f"Error getting conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    title: Optional[str] = Query(None, description="New title for the conversation"),
    status: Optional[str] = Query(None, description="New status for the conversation")
):
    """
    Update conversation title and/or status
    """
    try:
        db_service = get_db_service()
        conversation = db_service.update_conversation(conversation_id, title=title, status=status)

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db_service.log_info(
            service="conversation_endpoints",
            message=f"Conversation updated: {conversation_id}",
            conversation_id=conversation_id
        )

        return {"success": True, "message": "Conversation updated successfully", "conversation": conversation}

    except HTTPException:
        raise
    except Exception as e:
        try:
            db_service = get_db_service()
            db_service.log_error(
                service="conversation_endpoints",
                message=f"Error updating conversation {conversation_id}: {str(e)}",
                conversation_id=conversation_id
            )
        except:
            print(f"Error updating conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating conversation: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all related data
    """
    try:
        db_service = get_db_service()
        success = db_service.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db_service.log_info(
            service="conversation_endpoints",
            message=f"Conversation deleted: {conversation_id}",
            conversation_id=conversation_id
        )

        return {"success": True, "message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        try:
            db_service = get_db_service()
            db_service.log_error(
                service="conversation_endpoints",
                message=f"Error deleting conversation {conversation_id}: {str(e)}",
                conversation_id=conversation_id
            )
        except:
            print(f"Error deleting conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")


# ==================== Job Endpoints ====================

@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    conversation_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get jobs with optional filters
    """
    try:
        db_service = get_db_service()

        if conversation_id:
            jobs = db_service.get_jobs_by_conversation(conversation_id)
        else:
            jobs = db_service.get_recent_jobs(status=status, job_type=job_type, limit=limit)

        return jobs

    except Exception as e:
        try:
            db_service = get_db_service()
            db_service.log_error(
                service="conversation_endpoints",
                message=f"Error getting jobs: {str(e)}",
                conversation_id=conversation_id,
                metadata={"status": status, "job_type": job_type}
            )
        except:
            # If logging fails (e.g., DB unavailable), just print to console
            print(f"Error getting jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """
    Get a specific job
    """
    try:
        db_service = get_db_service()
        job = db_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        try:
            db_service = get_db_service()
            db_service.log_error(
                service="conversation_endpoints",
                message=f"Error getting job {job_id}: {str(e)}",
                job_id=job_id
            )
        except:
            print(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving job: {str(e)}")


# ==================== Log Endpoints ====================

@router.get("/logs", response_model=List[LogResponse])
async def get_logs(
    conversation_id: Optional[str] = Query(None),
    job_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Get logs with optional filters
    """
    try:
        db_service = get_db_service()
        logs = db_service.get_logs(
            conversation_id=conversation_id,
            job_id=job_id,
            level=level,
            service=service,
            limit=limit
        )

        return logs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")
