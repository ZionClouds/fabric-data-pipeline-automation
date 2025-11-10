"""
Database service for managing conversations, jobs, and logs
"""
from sqlalchemy import create_engine, desc, and_
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime
import traceback

from models.database_models import (
    Base, Conversation, ConversationMessage, Job, Log,
    ConversationStatus, JobStatus, PipelineStageStatus, LogLevel
)


class DatabaseService:
    """Service for database operations"""

    def __init__(self, database_url: str):
        """
        Initialize database service

        Args:
            database_url: Database connection URL (e.g., sqlite:///./fabric_pipeline.db)
        """
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # ==================== Conversation Operations ====================

    def create_conversation(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        workspace_id: Optional[str] = None,
        lakehouse_id: Optional[str] = None,
        workspace_name: Optional[str] = None,
        lakehouse_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation"""
        with self.get_session() as session:
            conversation = Conversation(
                user_id=user_id,
                user_email=user_email,
                workspace_id=workspace_id,
                lakehouse_id=lakehouse_id,
                workspace_name=workspace_name,
                lakehouse_name=lakehouse_name,
                status=ConversationStatus.ACTIVE.value,
                metadata=metadata
            )
            session.add(conversation)
            session.flush()
            conversation_dict = conversation.to_dict()
            return conversation_dict

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        with self.get_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            return conversation.to_dict() if conversation else None

    def get_conversations_by_user(
        self,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversations by user"""
        with self.get_session() as session:
            query = session.query(Conversation)

            if user_id:
                query = query.filter(Conversation.user_id == user_id)
            if user_email:
                query = query.filter(Conversation.user_email == user_email)
            if status:
                query = query.filter(Conversation.status == status)

            conversations = query.order_by(desc(Conversation.updated_at)).limit(limit).all()
            return [conv.to_dict() for conv in conversations]

    def update_conversation(
        self,
        conversation_id: str,
        status: Optional[str] = None,
        workspace_id: Optional[str] = None,
        lakehouse_id: Optional[str] = None,
        workspace_name: Optional[str] = None,
        lakehouse_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update conversation"""
        with self.get_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()

            if not conversation:
                return None

            if status is not None:
                conversation.status = status
            if workspace_id is not None:
                conversation.workspace_id = workspace_id
            if lakehouse_id is not None:
                conversation.lakehouse_id = lakehouse_id
            if workspace_name is not None:
                conversation.workspace_name = workspace_name
            if lakehouse_name is not None:
                conversation.lakehouse_name = lakehouse_name
            if metadata is not None:
                conversation.metadata = metadata

            conversation.updated_at = datetime.utcnow()
            session.flush()
            return conversation.to_dict()

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all related data"""
        with self.get_session() as session:
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()

            if not conversation:
                return False

            session.delete(conversation)
            return True

    # ==================== Message Operations ====================

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a message to conversation"""
        with self.get_session() as session:
            message = ConversationMessage(
                conversation_id=conversation_id,
                role=role,
                content=content,
                metadata=metadata
            )
            session.add(message)
            session.flush()
            message_dict = message.to_dict()

            # Update conversation timestamp
            conversation = session.query(Conversation).filter(
                Conversation.conversation_id == conversation_id
            ).first()
            if conversation:
                conversation.updated_at = datetime.utcnow()

            return message_dict

    def get_conversation_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        with self.get_session() as session:
            query = session.query(ConversationMessage).filter(
                ConversationMessage.conversation_id == conversation_id
            ).order_by(ConversationMessage.timestamp)

            if limit:
                query = query.limit(limit)

            messages = query.all()
            return [msg.to_dict() for msg in messages]

    def get_conversation_with_messages(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation with all messages"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        messages = self.get_conversation_messages(conversation_id)
        conversation['messages'] = messages
        return conversation

    # ==================== Job Operations ====================

    def create_job(
        self,
        job_type: str,
        conversation_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        lakehouse_id: Optional[str] = None,
        workspace_name: Optional[str] = None,
        lakehouse_name: Optional[str] = None,
        pipeline_definition: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new job"""
        with self.get_session() as session:
            job = Job(
                conversation_id=conversation_id,
                job_type=job_type,
                status=JobStatus.PENDING.value,
                workspace_id=workspace_id,
                lakehouse_id=lakehouse_id,
                workspace_name=workspace_name,
                lakehouse_name=lakehouse_name,
                pipeline_definition=pipeline_definition,
                metadata=metadata
            )
            session.add(job)
            session.flush()
            return job.to_dict()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        with self.get_session() as session:
            job = session.query(Job).filter(Job.job_id == job_id).first()
            return job.to_dict() if job else None

    def get_jobs_by_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all jobs for a conversation"""
        with self.get_session() as session:
            jobs = session.query(Job).filter(
                Job.conversation_id == conversation_id
            ).order_by(desc(Job.created_at)).all()
            return [job.to_dict() for job in jobs]

    def update_job_status(
        self,
        job_id: str,
        status: Optional[str] = None,
        pipeline_generation_status: Optional[str] = None,
        pipeline_deployment_status: Optional[str] = None,
        pipeline_preview_status: Optional[str] = None,
        pipeline_definition: Optional[Dict[str, Any]] = None,
        pipeline_id: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update job status and details"""
        with self.get_session() as session:
            job = session.query(Job).filter(Job.job_id == job_id).first()

            if not job:
                return None

            if status is not None:
                job.status = status
                if status == JobStatus.IN_PROGRESS.value and not job.started_at:
                    job.started_at = datetime.utcnow()
                elif status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
                    job.completed_at = datetime.utcnow()

            if pipeline_generation_status is not None:
                job.pipeline_generation_status = pipeline_generation_status
            if pipeline_deployment_status is not None:
                job.pipeline_deployment_status = pipeline_deployment_status
            if pipeline_preview_status is not None:
                job.pipeline_preview_status = pipeline_preview_status
            if pipeline_definition is not None:
                job.pipeline_definition = pipeline_definition
            if pipeline_id is not None:
                job.pipeline_id = pipeline_id
            if pipeline_name is not None:
                job.pipeline_name = pipeline_name
            if error_message is not None:
                job.error_message = error_message
            if error_details is not None:
                job.error_details = error_details
            if metadata is not None:
                job.metadata = metadata

            job.updated_at = datetime.utcnow()
            session.flush()
            return job.to_dict()

    def get_recent_jobs(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent jobs"""
        with self.get_session() as session:
            query = session.query(Job)

            if status:
                query = query.filter(Job.status == status)
            if job_type:
                query = query.filter(Job.job_type == job_type)

            jobs = query.order_by(desc(Job.created_at)).limit(limit).all()
            return [job.to_dict() for job in jobs]

    # ==================== Log Operations ====================

    def add_log(
        self,
        level: str,
        service: str,
        message: str,
        conversation_id: Optional[str] = None,
        job_id: Optional[str] = None,
        user_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a log entry"""
        with self.get_session() as session:
            log = Log(
                level=level,
                service=service,
                message=message,
                conversation_id=conversation_id,
                job_id=job_id,
                user_id=user_id,
                stack_trace=stack_trace,
                metadata=metadata
            )
            session.add(log)
            session.flush()
            return log.to_dict()

    def get_logs(
        self,
        conversation_id: Optional[str] = None,
        job_id: Optional[str] = None,
        level: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get logs with filters"""
        with self.get_session() as session:
            query = session.query(Log)

            if conversation_id:
                query = query.filter(Log.conversation_id == conversation_id)
            if job_id:
                query = query.filter(Log.job_id == job_id)
            if level:
                query = query.filter(Log.level == level)
            if service:
                query = query.filter(Log.service == service)

            logs = query.order_by(desc(Log.timestamp)).limit(limit).all()
            return [log.to_dict() for log in logs]

    def log_info(self, service: str, message: str, **kwargs):
        """Helper to log INFO level"""
        self.add_log(LogLevel.INFO.value, service, message, **kwargs)

    def log_warning(self, service: str, message: str, **kwargs):
        """Helper to log WARNING level"""
        self.add_log(LogLevel.WARNING.value, service, message, **kwargs)

    def log_error(self, service: str, message: str, **kwargs):
        """Helper to log ERROR level"""
        if 'stack_trace' not in kwargs:
            kwargs['stack_trace'] = traceback.format_exc()
        self.add_log(LogLevel.ERROR.value, service, message, **kwargs)

    def log_debug(self, service: str, message: str, **kwargs):
        """Helper to log DEBUG level"""
        self.add_log(LogLevel.DEBUG.value, service, message, **kwargs)


# Global database service instance
db_service: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    """Get global database service instance"""
    global db_service
    if db_service is None:
        raise RuntimeError("Database service not initialized. Call init_database() first.")
    return db_service


def init_database(database_url: str) -> DatabaseService:
    """Initialize global database service"""
    global db_service
    db_service = DatabaseService(database_url)
    db_service.init_db()
    return db_service
