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
    workspace_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get conversations for a user, optionally filtered by workspace
    """
    try:
        db_service = get_db_service()
        conversations = db_service.get_conversations_by_user(
            user_id=user_id,
            user_email=user_email,
            workspace_id=workspace_id,
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


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete"""
    conversation_ids: List[str]


@router.post("/conversations/bulk-delete")
async def bulk_delete_conversations(request: BulkDeleteRequest):
    """
    Delete multiple conversations at once
    """
    try:
        db_service = get_db_service()
        deleted_count = 0
        failed_ids = []

        for conv_id in request.conversation_ids:
            try:
                success = db_service.delete_conversation(conv_id)
                if success:
                    deleted_count += 1
                else:
                    failed_ids.append(conv_id)
            except Exception:
                failed_ids.append(conv_id)

        db_service.log_info(
            service="conversation_endpoints",
            message=f"Bulk delete: {deleted_count} deleted, {len(failed_ids)} failed",
            metadata={"deleted_count": deleted_count, "failed_ids": failed_ids}
        )

        return {
            "success": True,
            "message": f"Deleted {deleted_count} conversations",
            "deleted_count": deleted_count,
            "failed_ids": failed_ids
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk delete: {str(e)}")


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(conversation_id: str):
    """
    Archive a conversation (soft delete - can be restored)
    """
    try:
        db_service = get_db_service()
        conversation = db_service.update_conversation(conversation_id, status="archived")

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db_service.log_info(
            service="conversation_endpoints",
            message=f"Conversation archived: {conversation_id}",
            conversation_id=conversation_id
        )

        return {"success": True, "message": "Conversation archived successfully", "conversation": conversation}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error archiving conversation: {str(e)}")


@router.post("/conversations/{conversation_id}/restore")
async def restore_conversation(conversation_id: str):
    """
    Restore an archived conversation
    """
    try:
        db_service = get_db_service()
        conversation = db_service.update_conversation(conversation_id, status="active")

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        db_service.log_info(
            service="conversation_endpoints",
            message=f"Conversation restored: {conversation_id}",
            conversation_id=conversation_id
        )

        return {"success": True, "message": "Conversation restored successfully", "conversation": conversation}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restoring conversation: {str(e)}")


@router.get("/conversations/search")
async def search_conversations(
    q: str = Query(..., min_length=1, description="Search query"),
    user_email: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search conversations by title or message content
    """
    try:
        db_service = get_db_service()

        # Get all conversations for user
        conversations = db_service.get_conversations_by_user(
            user_email=user_email,
            limit=500  # Get more to search through
        )

        # Filter by search query (case-insensitive)
        search_lower = q.lower()
        results = []

        for conv in conversations:
            # Search in title
            if conv.get('title') and search_lower in conv['title'].lower():
                conv['match_type'] = 'title'
                results.append(conv)
                continue

            # Search in messages
            messages = db_service.get_conversation_messages(conv['conversation_id'])
            for msg in messages:
                if msg.get('content') and search_lower in msg['content'].lower():
                    conv['match_type'] = 'message'
                    conv['match_preview'] = msg['content'][:200] + '...' if len(msg['content']) > 200 else msg['content']
                    results.append(conv)
                    break

            if len(results) >= limit:
                break

        return {
            "query": q,
            "count": len(results),
            "conversations": results[:limit]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching conversations: {str(e)}")


@router.delete("/conversations/user/{user_email}")
async def delete_all_user_conversations(
    user_email: str,
    confirm: bool = Query(False, description="Must be true to confirm deletion")
):
    """
    Delete all conversations for a specific user (requires confirmation)
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to delete all conversations"
        )

    try:
        db_service = get_db_service()

        # Get all user conversations
        conversations = db_service.get_conversations_by_user(
            user_email=user_email,
            limit=1000
        )

        deleted_count = 0
        for conv in conversations:
            try:
                db_service.delete_conversation(conv['conversation_id'])
                deleted_count += 1
            except Exception:
                pass  # Continue with others if one fails

        db_service.log_info(
            service="conversation_endpoints",
            message=f"Deleted all conversations for user: {user_email}",
            metadata={"deleted_count": deleted_count, "user_email": user_email}
        )

        return {
            "success": True,
            "message": f"Deleted {deleted_count} conversations for user {user_email}",
            "deleted_count": deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user conversations: {str(e)}")


class MigrateUserRequest(BaseModel):
    from_email: str
    to_email: str


@router.post("/conversations/migrate-user")
async def migrate_user_conversations(request: MigrateUserRequest):
    """
    Migrate conversations from one user email to another.
    Useful for development when conversations were created under dev@example.com
    """
    try:
        db_service = get_db_service()

        # Get all conversations for the source email
        conversations = db_service.get_conversations_by_user(
            user_email=request.from_email,
            limit=1000
        )

        if not conversations:
            return {
                "success": True,
                "message": f"No conversations found for {request.from_email}",
                "migrated_count": 0
            }

        # Update each conversation's user_email
        migrated_count = 0
        for conv in conversations:
            try:
                with db_service.get_session() as session:
                    from models.database_models import Conversation
                    conversation = session.query(Conversation).filter(
                        Conversation.conversation_id == conv['conversation_id']
                    ).first()
                    if conversation:
                        conversation.user_email = request.to_email
                        session.commit()
                        migrated_count += 1
            except Exception as e:
                print(f"Failed to migrate conversation {conv['conversation_id']}: {e}")

        db_service.log_info(
            service="conversation_endpoints",
            message=f"Migrated conversations from {request.from_email} to {request.to_email}",
            metadata={"migrated_count": migrated_count}
        )

        return {
            "success": True,
            "message": f"Migrated {migrated_count} conversations from {request.from_email} to {request.to_email}",
            "migrated_count": migrated_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error migrating conversations: {str(e)}")


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
