"""
AI Pipeline Generation Service

This package provides AI-powered data pipeline generation for Microsoft Fabric.

Components:
- AIChatService: Handles multi-turn conversations with OpenAI for gathering requirements
- NotebookGenerator: Generates PySpark notebooks with PII detection using Presidio
- PipelineGenerator: Generates Fabric pipeline JSON definitions
- ResourceManager: Manages Fabric resources (connections, environments, lakehouses)
- DeploymentService: Orchestrates the complete deployment workflow
"""

from services.ai_pipeline.chat_service import AIChatService
from services.ai_pipeline.notebook_generator import NotebookGenerator
from services.ai_pipeline.pipeline_generator import PipelineGenerator
from services.ai_pipeline.resource_manager import ResourceManager
from services.ai_pipeline.deployment_service import DeploymentService
from services.ai_pipeline.router import router as ai_pipeline_router

# Export models for external use
from services.ai_pipeline.models import (
    # Enums
    FileFormat,
    MaskingType,
    DestinationType,
    TransformationType,
    ConversationState,
    # Configuration models
    SourceConfig,
    PIIConfig,
    TransformationConfig,
    TransformationStep,
    DestinationConfig,
    ScheduleConfig,
    PipelineConfig,
    # Conversation models
    ConversationMessage,
    ConversationContext,
    # Analysis models
    IdentifiedActivity,
    UseCaseAnalysis,
    # API models
    ChatRequest,
    ChatResponse,
    DeployRequest,
    DeployResponse,
)

__all__ = [
    # Services
    "AIChatService",
    "NotebookGenerator",
    "PipelineGenerator",
    "ResourceManager",
    "DeploymentService",
    # Router
    "ai_pipeline_router",
    # Enums
    "FileFormat",
    "MaskingType",
    "DestinationType",
    "TransformationType",
    "ConversationState",
    # Configuration models
    "SourceConfig",
    "PIIConfig",
    "TransformationConfig",
    "TransformationStep",
    "DestinationConfig",
    "ScheduleConfig",
    "PipelineConfig",
    # Conversation models
    "ConversationMessage",
    "ConversationContext",
    # Analysis models
    "IdentifiedActivity",
    "UseCaseAnalysis",
    # API models
    "ChatRequest",
    "ChatResponse",
    "DeployRequest",
    "DeployResponse",
]
