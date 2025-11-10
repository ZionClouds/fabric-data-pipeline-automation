"""
SQLAlchemy models for database tables
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Enum, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()


class ConversationStatus(str, enum.Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStageStatus(str, enum.Enum):
    """Pipeline stage status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class LogLevel(str, enum.Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Conversation(Base):
    """Conversation table to store chat conversations"""
    __tablename__ = "conversations"

    conversation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=True)
    user_email = Column(String(255), nullable=True)
    workspace_id = Column(String(255), nullable=True)
    lakehouse_id = Column(String(255), nullable=True)
    workspace_name = Column(String(255), nullable=True)
    lakehouse_name = Column(String(255), nullable=True)
    status = Column(String(50), default=ConversationStatus.ACTIVE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)

    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="conversation", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "workspace_id": self.workspace_id,
            "lakehouse_id": self.lakehouse_id,
            "workspace_name": self.workspace_name,
            "lakehouse_name": self.lakehouse_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "extra_metadata": self.extra_metadata
        }


class ConversationMessage(Base):
    """Conversation messages table"""
    __tablename__ = "conversation_messages"

    message_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(JSON, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "extra_metadata": self.extra_metadata
        }


class Job(Base):
    """Jobs table to track pipeline generation and deployment jobs"""
    __tablename__ = "jobs"

    job_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.conversation_id", ondelete="CASCADE"), nullable=True)
    job_type = Column(String(100), nullable=False)  # 'pipeline_generation', 'pipeline_deployment', 'pipeline_preview'
    status = Column(String(50), default=JobStatus.PENDING.value)

    # Pipeline stage statuses
    pipeline_generation_status = Column(String(50), default=PipelineStageStatus.NOT_STARTED.value)
    pipeline_deployment_status = Column(String(50), default=PipelineStageStatus.NOT_STARTED.value)
    pipeline_preview_status = Column(String(50), default=PipelineStageStatus.NOT_STARTED.value)

    # Pipeline details
    pipeline_definition = Column(JSON, nullable=True)
    pipeline_id = Column(String(255), nullable=True)  # Fabric pipeline ID after deployment
    pipeline_name = Column(String(255), nullable=True)

    # Workspace details
    workspace_id = Column(String(255), nullable=True)
    lakehouse_id = Column(String(255), nullable=True)
    workspace_name = Column(String(255), nullable=True)
    lakehouse_name = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Additional metadata
    extra_metadata = Column(JSON, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="jobs")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "conversation_id": self.conversation_id,
            "job_type": self.job_type,
            "status": self.status,
            "pipeline_generation_status": self.pipeline_generation_status,
            "pipeline_deployment_status": self.pipeline_deployment_status,
            "pipeline_preview_status": self.pipeline_preview_status,
            "pipeline_definition": self.pipeline_definition,
            "pipeline_id": self.pipeline_id,
            "pipeline_name": self.pipeline_name,
            "workspace_id": self.workspace_id,
            "lakehouse_id": self.lakehouse_id,
            "workspace_name": self.workspace_name,
            "lakehouse_name": self.lakehouse_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "extra_metadata": self.extra_metadata
        }


class Log(Base):
    """Logs table for comprehensive application logging"""
    __tablename__ = "logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20), nullable=False, index=True)
    service = Column(String(100), nullable=False, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    job_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "log_id": self.log_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "service": self.service,
            "conversation_id": self.conversation_id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "message": self.message,
            "stack_trace": self.stack_trace,
            "extra_metadata": self.extra_metadata
        }
