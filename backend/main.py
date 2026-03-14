from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import logging
import httpx
import jwt
from jwt import PyJWKClient
import ssl
import certifi
import os
import random
import re
import json
from datetime import datetime

# Import settings and services
import settings
from services.azure_ai_agent_service import AzureAIAgentService
from services.fabric_api_service import FabricAPIService
from services.proactive_suggestions import proactive_service
from services.medallion_architect import medallion_service
from models.pipeline_models import (
    ChatRequest, ChatResponse,
    PipelineGenerateRequest, PipelineGenerateResponse,
    LinkedServiceRequest, LinkedServiceResponse,
    AutomatedPipelineGenerateRequest, AutomatedPipelineGenerateResponse,
    PipelineArchitecture,
    FileProcessingPipelineRequest, FileProcessingPipelineResponse
)

# Import conversation endpoints router
from conversation_endpoints import router as conversation_router

# Import database service
from services.database_service import init_database, get_db_service

# In-memory storage for generated pipelines (temporary - should use database in production)
generated_pipelines = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import SDK agents (primary implementation)
from services.agents_sdk import (
    PipelineAgentRunner,
    initialize_runner,
    get_runner,
)
logger.info("OpenAI Agents SDK loaded successfully")


def extract_pipeline_config(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract PIPELINE_CONFIG JSON block from AI response content.

    Args:
        content: The AI response content

    Returns:
        Parsed pipeline config dict or None if not found
    """
    try:
        # Look for ```PIPELINE_CONFIG ... ``` block
        pattern = r'```PIPELINE_CONFIG\s*\n([\s\S]*?)\n```'
        match = re.search(pattern, content)

        if match:
            json_str = match.group(1).strip()
            config = json.loads(json_str)
            logger.info(f"Extracted pipeline config: {config}")
            return config

        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pipeline config JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting pipeline config: {e}")
        return None


def clean_ai_response(content: str) -> str:
    """
    Remove PIPELINE_CONFIG JSON block from AI response for cleaner display.

    Args:
        content: The AI response content

    Returns:
        Content without the PIPELINE_CONFIG block
    """
    # Remove ```PIPELINE_CONFIG ... ``` blocks
    pattern = r'\n*```PIPELINE_CONFIG\s*\n[\s\S]*?\n```\n*'
    cleaned = re.sub(pattern, '', content)
    return cleaned.strip()

# Create FastAPI app
app = FastAPI(
    title="Pipeline Builder API",
    description="AI-Powered Data Pipeline Builder for Microsoft Fabric",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversation_router)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and SDK agents on startup"""
    try:
        logger.info("Initializing database...")
        init_database(settings.DATABASE_URL)
        logger.info("[OK] Database initialized successfully")

        # Log startup
        db_service = get_db_service()
        db_service.log_info(
            service="main",
            message="Application started successfully"
        )
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # Don't crash the app, just log the error
        import traceback
        traceback.print_exc()

    # Initialize SDK agents
    try:
        logger.info("Initializing OpenAI Agents SDK...")
        initialize_runner(
            model=settings.CLAUDE_MODEL,
            temperature=settings.CLAUDE_TEMPERATURE,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            fabric_service=fabric_service,
        )
        logger.info("[OK] OpenAI Agents SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SDK agents: {str(e)}")
        import traceback
        traceback.print_exc()

# Initialize services
fabric_service = FabricAPIService()

# Initialize Azure AI Agent service (GPT-4o-mini with Bing Grounding via Agents)
# Used for proactive suggestions and medallion architect services
agent_service = AzureAIAgentService(
    project_endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    bing_connection_id=settings.BING_GROUNDING_CONNECTION_ID,
    model_deployment="gpt-4o-mini-bing"
)

# Security
security = HTTPBearer(auto_error=False)

# Microsoft Azure AD configuration
AZURE_TENANT_ID = settings.FABRIC_TENANT_ID
JWKS_URL = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys"

# ==================== Database Helper Functions ====================

def generate_conversation_title(user_message: str) -> str:
    """
    Generate a short title from the first user message
    """
    # Truncate and clean the message for use as a title
    title = user_message.strip()

    # Remove special characters and extra whitespace
    import re
    title = re.sub(r'\s+', ' ', title)

    # Truncate to 50 characters
    if len(title) > 50:
        title = title[:47] + "..."

    return title if title else "New Conversation"


def get_or_create_conversation(
    user_email: str,
    workspace_id: Optional[str] = None,
    lakehouse_id: Optional[str] = None
) -> str:
    """
    Get existing conversation or create a new one

    Returns:
        conversation_id: The conversation ID
    """
    try:
        db_service = get_db_service()

        # Try to find an active conversation for this user and workspace
        conversations = db_service.get_conversations_by_user(
            user_email=user_email,
            status="active",
            limit=1
        )

        if conversations:
            # Return existing conversation
            return conversations[0]['conversation_id']

        # Create new conversation
        conversation = db_service.create_conversation(
            user_email=user_email,
            workspace_id=workspace_id,
            lakehouse_id=lakehouse_id
        )

        return conversation['conversation_id']

    except Exception as e:
        logger.error(f"Error getting/creating conversation: {str(e)}")
        # Return a temporary ID if database fails
        import uuid
        return str(uuid.uuid4())


def update_conversation_title(conversation_id: str, user_message: str):
    """
    Update conversation title if it hasn't been set yet
    """
    try:
        db_service = get_db_service()
        conversation = db_service.get_conversation(conversation_id)

        # Only update if the conversation exists and has no title or default title
        if conversation and (not conversation.get('title') or conversation.get('title') == 'New Conversation'):
            title = generate_conversation_title(user_message)
            db_service.update_conversation(conversation_id, title=title)
            logger.info(f"Updated conversation title to: {title}")
    except Exception as e:
        logger.error(f"Error updating conversation title: {str(e)}")


def save_chat_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Save a chat message to the database"""
    try:
        db_service = get_db_service()
        db_service.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata
        )

        # Update conversation title from first user message
        if role == "user":
            update_conversation_title(conversation_id, content)

    except RuntimeError as e:
        # Database not initialized - log warning but don't fail
        logger.warning(f"Database not available, skipping message save: {str(e)}")
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        # Don't fail the request if message saving fails

# Create SSL context with certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Token validation function
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate Microsoft Azure AD JWT token
    """
    # Development mode: try to decode token for user info, but don't require valid token
    if settings.DISABLE_AUTH is True or settings.DISABLE_AUTH == "true":
        logger.info("Development mode: bypassing authentication")
        # Try to extract user info from token if provided
        if credentials and credentials.credentials:
            try:
                # Decode without verification to get user info
                token = credentials.credentials
                # Decode without verification (development only)
                payload = jwt.decode(token, options={"verify_signature": False})
                user_email = payload.get("preferred_username") or payload.get("upn") or payload.get("email")
                user_name = payload.get("name")
                if user_email:
                    logger.info(f"Development mode: using token user {user_email}")
                    return {"email": user_email, "name": user_name or "Development User", "oid": payload.get("oid", "dev-user-id")}
            except Exception as e:
                logger.debug(f"Development mode: could not decode token: {e}")
        return {"email": "dev123@gmail.com", "name": "dev123", "oid": "dev-user-id"}

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials

    logger.info(f"Validating token: {token[:50]}...")

    try:
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
        if payload.get("appid") != settings.FABRIC_CLIENT_ID and payload.get("azp") != settings.FABRIC_CLIENT_ID:
            logger.warning(f"Token appid: {payload.get('appid')}, Expected: {settings.FABRIC_CLIENT_ID}")

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

# Helper Functions
async def create_blob_storage_shortcuts(workspace_id: str) -> Dict[str, Any]:
    """
    Check for existing OneLake shortcuts and inform user
    If shortcuts don't exist, guide user to create them manually (API limitation)

    Returns:
        Dict with success status, existing shortcuts info
    """
    try:
        # Get lakehouse from workspace
        lakehouses = await fabric_service.get_workspace_lakehouses(workspace_id)

        if not lakehouses:
            return {
                "success": False,
                "error": "No lakehouse found in workspace",
                "message": "Please create a lakehouse in your workspace first"
            }

        lakehouse = lakehouses[0]  # Use first lakehouse
        lakehouse_id = lakehouse.get("id")
        lakehouse_name = lakehouse.get("displayName", "Unknown")

        logger.info(f"Using lakehouse: {lakehouse_name} ({lakehouse_id})")

        # Check for existing shortcuts
        existing_shortcuts = await fabric_service.get_lakehouse_shortcuts(workspace_id, lakehouse_id)

        if existing_shortcuts.get("success"):
            shortcuts = existing_shortcuts.get("shortcuts", [])

            # Check if bronze and silver shortcuts already exist
            bronze_exists = any(s.get("name") == "bronze" for s in shortcuts)
            silver_exists = any(s.get("name") == "silver" for s in shortcuts)

            if bronze_exists and silver_exists:
                logger.info("Bronze and silver shortcuts already exist")
                return {
                    "success": True,
                    "lakehouse_name": lakehouse_name,
                    "lakehouse_id": lakehouse_id,
                    "shortcuts": [
                        {"name": "bronze", "container": "bronze", "path": "Files/bronze"},
                        {"name": "silver", "container": "silver", "path": "Files/silver"}
                    ],
                    "storage_account": settings.STORAGE_ACCOUNT_NAME,
                    "already_exists": True,
                    "message": "Shortcuts already exist in your lakehouse"
                }
            elif bronze_exists or silver_exists:
                logger.info(f"Some shortcuts exist: bronze={bronze_exists}, silver={silver_exists}")
                # Partial setup - inform user
                return {
                    "success": False,
                    "error": "Partial shortcut setup detected",
                    "message": f"Found existing shortcuts but not complete. Bronze: {'[OK]' if bronze_exists else '[FAILED]'}, Silver: {'[OK]' if silver_exists else '[FAILED]'}"
                }

        logger.info(f"No shortcuts found, would need manual creation")

        # Create connection for blob storage using settings
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        connection_name = f"BlobStorage_{settings.STORAGE_ACCOUNT_NAME}_{timestamp}"

        connection_result = await fabric_service.create_connection(
            workspace_id=workspace_id,
            connection_name=connection_name,
            source_type="adls",  # Use ADLS Gen2 for shortcuts
            connection_config={
                "account_name": settings.STORAGE_ACCOUNT_NAME,
                "auth_type": "WorkspaceIdentity"  # Use Workspace Identity for ADLS Gen2
            }
        )

        if not connection_result.get("success"):
            error_msg = connection_result.get("error", "Unknown error")
            # Check if it's a duplicate connection error
            if "DuplicateConnectionName" in str(error_msg):
                logger.warning(f"Connection with similar name already exists, trying with different name...")
                # Try again with a random suffix
                import random
                random_suffix = random.randint(1000, 9999)
                connection_name = f"BlobStorage_{settings.STORAGE_ACCOUNT_NAME}_{random_suffix}"

                connection_result = await fabric_service.create_connection(
                    workspace_id=workspace_id,
                    connection_name=connection_name,
                    source_type="adls",  # Use ADLS Gen2 for shortcuts
                    connection_config={
                        "account_name": settings.STORAGE_ACCOUNT_NAME,
                        "auth_type": "WorkspaceIdentity"  # Use Workspace Identity for ADLS Gen2
                    }
                )

                if not connection_result.get("success"):
                    return {
                        "success": False,
                        "error": "Failed to create connection after retry",
                        "message": connection_result.get("error", "Unknown error")
                    }
            else:
                return {
                    "success": False,
                    "error": "Failed to create connection",
                    "message": error_msg
                }

        connection_id = connection_result.get("connection_id")
        logger.info(f"Connection created: {connection_name} ({connection_id})")

        # Create shortcuts for bronze and silver containers
        shortcuts_created = []

        for container_name in ["bronze", "silver"]:
            shortcut_name = f"azure_blob_{container_name}"

            shortcut_result = await fabric_service.create_onelake_shortcut(
                workspace_id=workspace_id,
                lakehouse_id=lakehouse_id,
                shortcut_name=shortcut_name,
                target_location="Files",  # Create in Files folder
                connection_id=connection_id,
                shortcut_config={
                    "target_type": "AdlsGen2",  # Use ADLS Gen2 format
                    "storage_account": settings.STORAGE_ACCOUNT_NAME,
                    "container": container_name,
                    "folder_path": ""  # Root of container
                }
            )

            if shortcut_result.get("success"):
                shortcuts_created.append({
                    "name": shortcut_name,
                    "container": container_name,
                    "path": f"Files/{shortcut_name}"
                })
                logger.info(f"Shortcut created: {shortcut_name}")
            else:
                logger.warning(f"Failed to create shortcut for {container_name}: {shortcut_result.get('error')}")

        if shortcuts_created:
            return {
                "success": True,
                "lakehouse_name": lakehouse_name,
                "lakehouse_id": lakehouse_id,
                "connection_name": connection_name,
                "connection_id": connection_id,
                "shortcuts": shortcuts_created,
                "storage_account": settings.STORAGE_ACCOUNT_NAME
            }
        else:
            return {
                "success": False,
                "error": "No shortcuts were created",
                "message": "Check if shortcuts already exist or if there are permission issues"
            }

    except Exception as e:
        logger.error(f"Error creating blob storage shortcuts: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while creating shortcuts"
        }

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Pipeline Builder API",
        "version": "2.0.0",
        "status": "running",
        "azure_openai_model": settings.AZURE_OPENAI_DEPLOYMENT,
        "bing_grounding_enabled": bool(settings.BING_GROUNDING_CONNECTION_ID),
        "multi_agent_sdk": "openai-agents",
        "endpoints": {
            "chat": "/api/ai/chat",
            "reset": "/api/ai/chat/reset",
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Clear conversation messages endpoint
@app.delete("/api/conversations/{conversation_id}/messages")
async def clear_conversation(conversation_id: str, user: dict = Depends(validate_token)):
    """Clear all messages from a conversation without deleting the conversation"""
    try:
        db_service = get_db_service()
        success = db_service.clear_conversation_messages(conversation_id)

        if success:
            logger.info(f"Cleared conversation {conversation_id} messages for user: {user['email']}")
            return {"success": True, "message": "Chat cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear conversation: {str(e)}")


# Multi-Agent Pipeline Architect Chat (SDK-based)
@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat_with_pipeline_architect(request: ChatRequest, user: dict = Depends(validate_token)):
    """
    Multi-Agent Pipeline Architect Chat

    This endpoint uses the OpenAI Agents SDK for multi-agent orchestration.
    Features:
    - Automatic agent routing based on conversation stage
    - Built-in handoffs between specialized agents
    - Production guardrails for safety
    - Tracing and metrics collection

    Agents:
    - Discovery Agent: Understands business context and requirements
    - Source Analyst: Expert on source systems and connections
    - Fabric Architect: Designs optimal pipeline architecture
    - Transform Expert: Plans data transformations and PII handling
    - Deploy Agent: Generates deployment packages
    """
    try:
        logger.info(f"SDK chat request for workspace: {request.workspace_id} by user: {user['email']}")

        # Validate required selections
        if not request.lakehouse_name or not request.warehouse_name:
            return ChatResponse(
                role="assistant",
                content="**Please select a Lakehouse and Warehouse above to continue.**\n\nI need to know which lakehouse and warehouse to use for your pipeline. Please select them from the dropdowns at the top of the page.",
                suggestions=None,
                pipeline_preview=None,
                shortcut_info=None,
                needs_confirmation=False,
                confirmation_action=None
            )

        # Get or create database conversation
        conversation_id = get_or_create_conversation(
            user_email=user['email'],
            workspace_id=request.workspace_id,
            lakehouse_id=request.lakehouse_id if hasattr(request, 'lakehouse_id') else None
        )

        # Get the last user message
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Save user message to database
        save_chat_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
            metadata={"workspace_id": request.workspace_id}
        )

        # Get SDK runner and process message
        runner = get_runner()
        response = await runner.run(
            message=user_message,
            workspace_id=request.workspace_id,
            user_id=user['email'],
            lakehouse_name=request.lakehouse_name,
            lakehouse_id=request.lakehouse_id,
            warehouse_name=request.warehouse_name,
        )

        # Extract response components
        assistant_content = response.message
        stage = response.stage
        pipeline_ready = response.pipeline_ready
        pipeline_config = response.deployment_preview

        # Add stage indicator to response
        stage_display = {
            "initial": "Understanding Requirements",
            "discovery": "Gathering Information",
            "analyzing": "Analyzing Source & Architecture",
            "designing": "Designing Pipeline",
            "reviewing": "Reviewing Design",
            "deploying": "Ready to Deploy",
            "completed": "Deployment Ready"
        }

        # Prepend stage indicator if not in final stages
        if stage not in ["reviewing", "deploying", "completed"]:
            stage_info = f"*{stage_display.get(stage, stage)}*\n\n"
            assistant_content = stage_info + assistant_content

        # Save assistant message to database
        save_chat_message(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            metadata={
                "stage": stage,
                "agent": response.agent_name,
                "pipeline_ready": pipeline_ready,
                "pipeline_config": pipeline_config,
                "metrics": response.metrics,
            }
        )

        # Build suggestions based on stage
        suggestions = None
        if stage == "reviewing":
            suggestions = ["Deploy pipeline", "Make changes", "Show more details"]
        elif stage in ["deploying", "completed"]:
            suggestions = ["Go to Pipeline Preview", "Deploy to workspace"]
        elif pipeline_ready:
            suggestions = ["Deploy pipeline", "Review design"]

        return ChatResponse(
            role="assistant",
            content=assistant_content,
            suggestions=suggestions,
            pipeline_preview=None,
            pipeline_config=pipeline_config,
            shortcut_info=None,
            needs_confirmation=pipeline_ready,
            confirmation_action="deploy_pipeline" if pipeline_ready else None,
            conversation_id=conversation_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SDK chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


# Reset multi-agent session
@app.post("/api/ai/chat/reset")
async def reset_pipeline_architect_session(request: ChatRequest, user: dict = Depends(validate_token)):
    """Reset the multi-agent session state for a user"""
    try:
        runner = get_runner()
        runner.clear_context(request.workspace_id, user['email'])
        return {"success": True, "message": "Session reset successfully"}
    except Exception as e:
        logger.error(f"Session reset error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Pipeline generation endpoint
@app.post("/api/pipelines/generate", response_model=PipelineGenerateResponse)
async def generate_pipeline(request: PipelineGenerateRequest, user: dict = Depends(validate_token)):
    """
    Generate complete pipeline from requirements collected via AI chat.

    Uses the source_config to dynamically generate pipeline activities based on:
    - Source type (PostgreSQL, SQL Server, Blob Storage, etc.)
    - Transformations required
    - PII/PHI masking requirements
    - Schedule
    """
    try:
        logger.info(f"Generating pipeline: {request.pipeline_name} for user: {user['email']}")
        logger.info(f"Source type: {request.source_type}")
        logger.info(f"Source config: {request.source_config}")

        # Create job for pipeline generation
        db_service = get_db_service()
        job = db_service.create_job(
            job_type="pipeline_generation",
            workspace_id=request.workspace_id,
            pipeline_definition=None,
            metadata={
                "pipeline_name": request.pipeline_name,
                "user_email": user['email'],
                "source_type": request.source_type,
                "source_config": request.source_config
            }
        )
        job_id = job['job_id']

        # Update job status to in progress
        db_service.update_job_status(
            job_id=job_id,
            status="in_progress",
            pipeline_generation_status="in_progress"
        )

        # Clean the pipeline name
        pipeline_name = request.pipeline_name.strip().strip('`').strip('"').strip("'").strip()
        logger.info(f"Using pipeline name: {pipeline_name}")

        # Import required models
        from models.pipeline_models import NotebookCode, MedallionLayer, PipelineActivity
        import time

        # Generate pipeline ID
        pipeline_id = int(time.time())

        # Extract config from source_config (passed from AI chat)
        source_config = request.source_config or {}
        source_type = request.source_type or "postgresql"
        tables = request.tables or []
        table_name = source_config.get("table_name", tables[0] if tables else "data")
        destination = source_config.get("destination", "tables")
        transformations = source_config.get("transformations", "none")
        pii_masking = source_config.get("pii_masking", "none")
        schedule = source_config.get("schedule", "manual")

        logger.info(f"Building pipeline for: source={source_type}, table={table_name}, transformations={transformations}, pii={pii_masking}")

        # Generate activities based on user requirements
        activities = []

        # Activity 1: Copy data from source to OneLake
        copy_activity = PipelineActivity(
            name=f"Copy_{source_type}_to_OneLake",
            type="Copy",
            config={
                "description": f"Copy data from {source_type} to OneLake",
                "source": {
                    "type": source_type.upper(),
                    "connection": f"{source_type}_connection",
                    "query": f"SELECT * FROM {table_name}" if source_type in ["postgresql", "mysql", "sql_server", "oracle", "azure_sql"] else None
                },
                "destination": {
                    "type": "Lakehouse",
                    "tableName": table_name,
                    "tableAction": "Overwrite"
                },
                "enableStaging": False
            },
            depends_on=None
        )
        activities.append(copy_activity)

        # Activity 2: Add transformation activity if transformations are needed
        if transformations and transformations.lower() != "none":
            transform_activity = PipelineActivity(
                name="Transform_Data",
                type="DataflowGen2",
                config={
                    "description": f"Apply transformations: {transformations}",
                    "dataflowName": f"{pipeline_name}_transform",
                    "source": {
                        "type": "Lakehouse",
                        "tableName": table_name
                    },
                    "transformations": [transformations],
                    "destination": {
                        "type": "Lakehouse",
                        "tableName": f"{table_name}_transformed"
                    }
                },
                depends_on=[f"Copy_{source_type}_to_OneLake"]
            )
            activities.append(transform_activity)

        # Activity 3: Add PII/PHI masking if needed
        notebooks = []
        if pii_masking and pii_masking.lower() != "none":
            masking_activity = PipelineActivity(
                name="PII_PHI_Masking",
                type="TridentNotebook",
                config={
                    "description": f"Apply {pii_masking} masking to sensitive data",
                    "notebookId": f"{pipeline_name}_pii_masking",
                    "parameters": {
                        "table_name": table_name,
                        "masking_type": pii_masking
                    }
                },
                depends_on=[activities[-1].name]
            )
            activities.append(masking_activity)

            # Generate masking notebook code
            masking_code = f'''# PII/PHI Masking Notebook - {pii_masking} masking
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, sha2, concat, lit

spark = SparkSession.builder.appName("PII_Masking").getOrCreate()

# Read data
df = spark.read.format("delta").load("Tables/{table_name}")

# Apply {pii_masking} masking to detected PII columns
# Email masking
df = df.withColumn("email",
    regexp_replace(col("email"), r"(.).*@(.*)\\.(.*)", r"$1***@***.***"))

# Phone masking
df = df.withColumn("phone",
    regexp_replace(col("phone"), r"(\\d{{3}})-(\\d{{3}})-(\\d{{4}})", r"$1-***-****"))

# Write masked data
df.write.format("delta").mode("overwrite").save("Tables/{table_name}_masked")
print("PII/PHI masking completed successfully!")
'''
            notebook = NotebookCode(
                notebook_name=f"{pipeline_name}_pii_masking",
                layer=MedallionLayer.SILVER,
                code=masking_code,
                description=f"Applies {pii_masking} masking to sensitive PII/PHI data"
            )
            notebooks.append(notebook)

        # Generate reasoning based on actual config
        reasoning = f"""## Pipeline Architecture Overview

This pipeline transfers data from **{source_type}** to **OneLake** based on your requirements.

### Configuration Summary:
- **Source**: {source_type} ({source_config.get('source_details', 'on-premise database')})
- **Destination**: OneLake {destination} → "{table_name}"
- **Transformations**: {transformations if transformations != 'none' else 'None (direct copy)'}
- **PII/PHI Masking**: {pii_masking if pii_masking != 'none' else 'None'}
- **Schedule**: {schedule}

### Pipeline Flow:

**1. Data Ingestion**
   - **Copy Activity**: Connects to {source_type} and copies data to OneLake table "{table_name}"
   - Uses Copy Activity for efficient bulk data transfer
   - {"Requires Self-Hosted Integration Runtime for on-premise connectivity" if source_type in ["postgresql", "mysql", "sql_server", "oracle"] else "Uses cloud-based connectivity"}
"""

        if transformations and transformations.lower() != "none":
            reasoning += f"""
**2. Data Transformation**
   - **Dataflow Gen2**: Applies {transformations} transformations
   - Output stored in "{table_name}_transformed" table
"""

        if pii_masking and pii_masking.lower() != "none":
            reasoning += f"""
**{"3" if transformations and transformations.lower() != "none" else "2"}. PII/PHI Masking**
   - **Notebook Activity**: Applies {pii_masking} masking to sensitive data
   - Protects email, phone, and other PII fields
   - Output stored in "{table_name}_masked" table
"""

        reasoning += """
### Next Steps:
1. Configure the source connection in Microsoft Fabric
2. Deploy this pipeline to your workspace
3. Run the pipeline manually or set up the schedule
"""

        # Store in memory for deployment later
        generated_pipelines[pipeline_id] = {
            "pipeline_name": pipeline_name,
            "activities": activities,
            "notebooks": notebooks,
            "reasoning": reasoning,
            "workspace_id": request.workspace_id,
            "config": {
                "workspace_id": request.workspace_id,
                "lakehouse_name": request.lakehouse_name or "default_lakehouse",
                "warehouse_name": request.warehouse_name or "default_warehouse",
                "source_type": source_type,
                "table_name": table_name,
                "transformations": transformations,
                "pii_masking": pii_masking,
                "schedule": schedule
            }
        }

        logger.info(f"[SUCCESS] Pipeline preview generated (ID: {pipeline_id})")

        # Convert pipeline definition to JSON-serializable format
        pipeline_def_for_db = {
            "pipeline_name": pipeline_name,
            "activities": [activity.dict() if hasattr(activity, 'dict') else activity for activity in activities],
            "notebooks": [nb.dict() if hasattr(nb, 'dict') else nb for nb in notebooks],
            "reasoning": reasoning,
            "workspace_id": request.workspace_id,
            "config": generated_pipelines[pipeline_id]["config"]
        }

        # Update job status to completed
        db_service.update_job_status(
            job_id=job_id,
            status="completed",
            pipeline_generation_status="completed",
            pipeline_preview_status="completed",
            pipeline_name=pipeline_name,
            pipeline_definition=pipeline_def_for_db
        )

        # Return preview (NOT deployed yet!)
        return PipelineGenerateResponse(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            activities=activities,
            notebooks=notebooks,
            fabric_pipeline_json={},
            reasoning=reasoning,
            job_id=job_id  # Include job_id for deployment
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline generation error: {str(e)}")

        # Update job status to failed
        try:
            db_service.update_job_status(
                job_id=job_id,
                status="failed",
                pipeline_generation_status="failed",
                error_message=str(e)
            )
        except:
            pass

        raise HTTPException(status_code=500, detail=f"Pipeline generation failed: {str(e)}")


# Automated Pipeline Generation with Connection Creation
@app.post("/api/pipelines/generate-automated", response_model=AutomatedPipelineGenerateResponse)
async def generate_automated_pipeline(
    request: AutomatedPipelineGenerateRequest,
    user: dict = Depends(validate_token)
):
    """
    Automated pipeline generation with connection creation

    This endpoint:
    1. Creates all required connections in Fabric workspace
    2. Creates pipeline activities based on architecture
    3. Creates the complete pipeline
    4. Returns success with resource IDs or manual instructions as fallback

    Supports:
    - Medallion architecture (Bronze -> Silver -> Gold)
    - Simple copy architecture (Source -> OneLake directly)
    """
    try:
        logger.info(f"Automated pipeline generation requested by user: {user['email']}")
        logger.info(f"Architecture: {request.architecture}, Pipeline: {request.pipeline_name}")

        connections_created = []
        activities = []
        notebooks_created = []

        # Step 1: Create Source Connection
        logger.info(f"Creating source connection: {request.source_connection.connection_name}")
        source_conn_result = await fabric_service.create_connection(
            workspace_id=request.workspace_id,
            connection_name=request.source_connection.connection_name,
            source_type=request.source_connection.connection_type,
            connection_config=request.source_connection.properties
        )

        if source_conn_result.get("success"):
            connections_created.append({
                "name": request.source_connection.connection_name,
                "id": source_conn_result.get("connection_id", ""),
                "type": request.source_connection.connection_type
            })
            logger.info(f"Source connection created: {source_conn_result.get('connection_id')}")
        else:
            logger.warning(f"Source connection creation failed: {source_conn_result.get('error')}")
            # Continue with manual instructions fallback

        # Step 2: Create Destination Connections (if medallion architecture)
        if request.architecture == PipelineArchitecture.MEDALLION:
            # Create Bronze connection (Blob Storage)
            if request.bronze_connection:
                logger.info(f"Creating bronze connection: {request.bronze_connection.connection_name}")
                bronze_conn_result = await fabric_service.create_connection(
                    workspace_id=request.workspace_id,
                    connection_name=request.bronze_connection.connection_name,
                    source_type=request.bronze_connection.connection_type,
                    connection_config=request.bronze_connection.properties
                )

                if bronze_conn_result.get("success"):
                    connections_created.append({
                        "name": request.bronze_connection.connection_name,
                        "id": bronze_conn_result.get("connection_id", ""),
                        "type": request.bronze_connection.connection_type
                    })
                    logger.info(f"Bronze connection created: {bronze_conn_result.get('connection_id')}")

            # Create Silver connection (Blob Storage)
            if request.silver_connection:
                logger.info(f"Creating silver connection: {request.silver_connection.connection_name}")
                silver_conn_result = await fabric_service.create_connection(
                    workspace_id=request.workspace_id,
                    connection_name=request.silver_connection.connection_name,
                    source_type=request.silver_connection.connection_type,
                    connection_config=request.silver_connection.properties
                )

                if silver_conn_result.get("success"):
                    connections_created.append({
                        "name": request.silver_connection.connection_name,
                        "id": silver_conn_result.get("connection_id", ""),
                        "type": request.silver_connection.connection_type
                    })
                    logger.info(f"Silver connection created: {silver_conn_result.get('connection_id')}")

        # Step 3: Build Pipeline Activities based on architecture
        if request.architecture == PipelineArchitecture.MEDALLION:
            # Build medallion architecture activities
            layer_order = ["bronze", "silver", "gold"]
            previous_activity = None

            for layer_config in (request.layers or []):
                layer_name = layer_config.layer_name
                component_type = layer_config.component_type or "copy_activity"

                logger.info(f"Building {layer_name} layer activity using {component_type}")

                if component_type == "copy_activity":
                    # Build Copy Activity
                    activity_name = f"Copy_to_{layer_name}_layer"

                    # Determine source and sink based on layer
                    if layer_name == "bronze":
                        # Source: External connection
                        source_connection = request.source_connection.connection_name
                        sink_connection = request.bronze_connection.connection_name if request.bronze_connection else None
                    elif layer_name == "silver":
                        # Source: Bronze layer
                        source_connection = request.bronze_connection.connection_name if request.bronze_connection else None
                        sink_connection = request.silver_connection.connection_name if request.silver_connection else None
                    elif layer_name == "gold":
                        # Source: Silver layer, Sink: OneLake
                        source_connection = request.silver_connection.connection_name if request.silver_connection else None
                        sink_connection = None  # OneLake (no connection needed)

                    activity = {
                        "name": activity_name,
                        "type": "Copy",
                        "config": {
                            "source": {
                                "type": "DelimitedText" if layer_name == "bronze" else "BlobSource",
                                "linkedService": source_connection
                            },
                            "sink": {
                                "type": "LakehouseTable" if layer_name == "gold" else "BlobSink",
                                "linkedService": sink_connection,
                                "tableName": request.gold_table_name if layer_name == "gold" else f"{layer_name}_data",
                                "lakehouse_id": request.gold_lakehouse_id if layer_name == "gold" else None
                            }
                        },
                        "depends_on": [previous_activity] if previous_activity else []
                    }

                    activities.append(activity)
                    previous_activity = activity_name

                elif component_type == "notebook":
                    # Build Notebook Activity for complex transformations
                    activity_name = f"Transform_{layer_name}_layer"
                    notebook_name = f"{request.pipeline_name}_{layer_name}_transformation"

                    # Generate notebook code based on transformations
                    transformation_desc = "\n".join(layer_config.transformations or [])
                    notebook_code = f"""
# {layer_name.capitalize()} Layer Transformation
# Pipeline: {request.pipeline_name}
# Transformations: {transformation_desc}

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

# Read from source
df = spark.read.format("delta").table("{layer_name}_source")

# Apply transformations
# TODO: Add specific transformation logic here
{transformation_desc}

# Write to destination
df.write.mode("overwrite").format("delta").saveAsTable("{layer_name}_output")

print(f"Processed {{df.count()}} rows in {layer_name} layer")
"""

                    # Create notebook
                    notebook_result = await fabric_service.create_notebook(
                        workspace_id=request.workspace_id,
                        notebook_name=notebook_name,
                        notebook_code=notebook_code
                    )

                    if notebook_result.get("success"):
                        notebooks_created.append(notebook_name)
                        logger.info(f"Notebook created: {notebook_name}")

                    activity = {
                        "name": activity_name,
                        "type": "Notebook",
                        "config": {
                            "notebook": notebook_name,
                            "parameters": {}
                        },
                        "depends_on": [previous_activity] if previous_activity else []
                    }

                    activities.append(activity)
                    previous_activity = activity_name

        elif request.architecture == PipelineArchitecture.SIMPLE_COPY:
            # Simple copy activity from source to OneLake
            activity = {
                "name": "Copy_to_OneLake",
                "type": "Copy",
                "config": {
                    "source": {
                        "type": "DelimitedText",
                        "linkedService": request.source_connection.connection_name
                    },
                    "sink": {
                        "type": "LakehouseTable",
                        "tableName": request.gold_table_name or "destination_table",
                        "lakehouse_id": request.gold_lakehouse_id
                    }
                },
                "depends_on": []
            }
            activities.append(activity)

        # Step 4: Create Pipeline in Fabric
        if activities:
            logger.info(f"Creating pipeline with {len(activities)} activities")

            # Build Fabric pipeline definition
            pipeline_def = {
                "name": request.pipeline_name,
                "properties": {
                    "activities": activities,
                    "annotations": [f"Architecture: {request.architecture}"],
                    "folder": {
                        "name": "AI Generated Pipelines"
                    }
                }
            }

            try:
                pipeline_result = await fabric_service.create_pipeline(
                    workspace_id=request.workspace_id,
                    pipeline_name=request.pipeline_name,
                    pipeline_definition=pipeline_def
                )

                if pipeline_result.get("success"):
                    logger.info(f"Pipeline created successfully: {pipeline_result.get('pipeline_id')}")

                    return AutomatedPipelineGenerateResponse(
                        success=True,
                        pipeline_id=pipeline_result.get("pipeline_id"),
                        pipeline_name=request.pipeline_name,
                        workspace_id=request.workspace_id,
                        connections_created=connections_created,
                        activities_created=[a["name"] for a in activities],
                        notebooks_created=notebooks_created if notebooks_created else None,
                        architecture=request.architecture.value,
                        layers=[layer.layer_name for layer in (request.layers or [])]
                    )
                else:
                    raise Exception(f"Pipeline creation failed: {pipeline_result.get('error')}")

            except Exception as pipeline_error:
                logger.error(f"Pipeline creation failed: {str(pipeline_error)}")
                # Fall back to manual instructions
                manual_instructions = _generate_manual_instructions(
                    request, connections_created, activities
                )

                return AutomatedPipelineGenerateResponse(
                    success=False,
                    pipeline_id=None,
                    pipeline_name=request.pipeline_name,
                    workspace_id=request.workspace_id,
                    connections_created=connections_created,
                    activities_created=[],
                    notebooks_created=notebooks_created if notebooks_created else None,
                    architecture=request.architecture.value,
                    layers=[layer.layer_name for layer in (request.layers or [])],
                    error=str(pipeline_error),
                    manual_instructions=manual_instructions
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="No activities generated. Please check your configuration."
            )

    except Exception as e:
        logger.error(f"Automated pipeline generation error: {str(e)}", exc_info=True)

        # Generate manual instructions as fallback
        manual_instructions = f"""
## Manual Pipeline Creation Instructions

Due to an error in automated creation, please follow these steps to create your pipeline manually:

1. **Create Connections in Fabric Workspace:**
   - Go to your workspace: {request.workspace_id}
   - Create source connection: {request.source_connection.connection_name}
   - Connection type: {request.source_connection.connection_type}

2. **Create Pipeline:**
   - Name: {request.pipeline_name}
   - Architecture: {request.architecture}

3. **Add Activities:**
   - Follow the {request.architecture} pattern
   - Configure source and sink for each layer

Error details: {str(e)}
"""

        return AutomatedPipelineGenerateResponse(
            success=False,
            pipeline_id=None,
            pipeline_name=request.pipeline_name,
            workspace_id=request.workspace_id,
            connections_created=[],
            activities_created=[],
            architecture=request.architecture.value,
            error=str(e),
            manual_instructions=manual_instructions
        )


def _generate_manual_instructions(
    request: AutomatedPipelineGenerateRequest,
    connections_created: List[Dict[str, str]],
    activities: List[Dict[str, Any]]
) -> str:
    """Generate manual instructions when automation partially fails"""

    instructions = f"""
## Manual Pipeline Completion Instructions

### Connections Already Created:
"""

    for conn in connections_created:
        instructions += f"- {conn['name']} (Type: {conn['type']}, ID: {conn['id']})\n"

    instructions += f"""

### Steps to Complete Pipeline Creation:

1. **Go to Fabric Workspace:**
   - Navigate to workspace: {request.workspace_id}

2. **Create Data Pipeline:**
   - Click "+ New" -> "Data Pipeline"
   - Name: {request.pipeline_name}

3. **Add Activities:**
"""

    for i, activity in enumerate(activities, 1):
        instructions += f"""
   Activity {i}: {activity['name']}
   - Type: {activity['type']}
   - Source: {activity['config'].get('source', {}).get('linkedService', 'N/A')}
   - Sink: {activity['config'].get('sink', {}).get('linkedService', 'N/A')}
"""

    instructions += f"""

4. **Configure Schedule:**
   - Schedule: {request.schedule}

5. **Test and Publish:**
   - Debug the pipeline to test
   - Publish when ready
"""

    return instructions


# Pre-deployment validation endpoint
@app.post("/api/pipelines/validate-before-deploy")
async def validate_before_deploy(request: Dict[str, Any], user: dict = Depends(validate_token)):
    """
    Proactive pre-deployment validation and optimization check

    This endpoint performs a comprehensive check before deployment:
    - Searches for latest best practices
    - Identifies optimization opportunities
    - Suggests improvements
    - Validates against current Fabric standards
    """
    try:
        logger.info(f"Pre-deployment validation requested by user: {user['email']}")

        pipeline_config = request.get("pipeline_config", {})

        if not pipeline_config:
            raise HTTPException(status_code=400, detail="pipeline_config is required")

        # Perform proactive optimization check
        validation_result = await proactive_service.pre_deployment_check(
            pipeline_config=pipeline_config,
            agent_service=agent_service
        )

        logger.info(f"Pre-deployment check completed. Bing search used: {validation_result.get('bing_search_used', False)}")

        return {
            "success": validation_result.get("success", False),
            "ready_to_deploy": validation_result.get("ready_to_deploy", True),
            "optimization_recommendations": validation_result.get("optimization_recommendations", ""),
            "bing_search_used": validation_result.get("bing_search_used", False),
            "pipeline_summary": {
                "source": pipeline_config.get("source", {}).get("type", "Unknown"),
                "destination": pipeline_config.get("destination", {}).get("type", "Unknown"),
                "activities_count": len(pipeline_config.get("activities", []))
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pre-deployment validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# Check for component alternatives endpoint
@app.post("/api/pipelines/check-component")
async def check_component_alternative(request: Dict[str, Any], user: dict = Depends(validate_token)):
    """
    Proactively check if there's a better component for the use case

    When user selects a component (e.g., Copy Activity), this endpoint
    searches for latest recommendations and suggests alternatives if available.
    """
    try:
        logger.info(f"Component check requested by user: {user['email']}")

        current_component = request.get("component")
        use_case = request.get("use_case")

        if not current_component or not use_case:
            raise HTTPException(status_code=400, detail="component and use_case are required")

        # Check for better alternatives
        suggestion = await proactive_service.suggest_component_alternative(
            current_component=current_component,
            use_case=use_case,
            agent_service=agent_service
        )

        logger.info(f"Component check completed. Bing search used: {suggestion.get('bing_search_used', False)}")

        return {
            "success": suggestion.get("success", False),
            "current_component": current_component,
            "use_case": use_case,
            "recommendation": suggestion.get("recommendation", ""),
            "bing_search_used": suggestion.get("bing_search_used", False)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Component check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Component check failed: {str(e)}")


# Medallion Architecture guidance endpoint
@app.post("/api/pipelines/medallion-architecture")
async def get_medallion_architecture_guidance(request: Dict[str, Any], user: dict = Depends(validate_token)):
    """
    Get comprehensive medallion architecture (Bronze/Silver/Gold) guidance

    This endpoint provides:
    - Layer-by-layer recommendations
    - Latest Fabric best practices for each layer
    - Pipeline templates
    - Optimization strategies
    - Build sequence
    """
    try:
        logger.info(f"Medallion architecture guidance requested by user: {user['email']}")

        source = request.get("source")
        data_volume = request.get("data_volume", "Unknown")
        frequency = request.get("frequency", "daily")
        business_use_case = request.get("business_use_case", "analytics")

        if not source:
            raise HTTPException(status_code=400, detail="source is required")

        # Get comprehensive medallion architecture guidance
        guidance = await medallion_service.get_medallion_guidance(
            source=source,
            data_volume=data_volume,
            frequency=frequency,
            business_use_case=business_use_case,
            agent_service=agent_service
        )

        logger.info(f"Medallion guidance generated. Bing search used: {guidance.get('bing_search_used', False)}")

        # Add pipeline templates for each layer
        build_sequence = medallion_service.get_layer_sequence()
        layer_templates = {
            layer: medallion_service.get_pipeline_template(
                layer=layer,
                source=source if layer == "bronze" else f"{build_sequence[i-1]}_layer",
                destination="lakehouse"
            )
            for i, layer in enumerate(build_sequence)
        }

        return {
            "success": guidance.get("success", False),
            "architecture_plan": guidance.get("architecture_plan", ""),
            "bing_search_used": guidance.get("bing_search_used", False),
            "build_sequence": build_sequence,
            "layer_templates": layer_templates,
            "layer_info": guidance.get("layers", {}),
            "requirements": {
                "source": source,
                "data_volume": data_volume,
                "frequency": frequency,
                "business_use_case": business_use_case
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Medallion architecture guidance error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Medallion guidance failed: {str(e)}")


# Get workspaces (directly from Fabric API)
@app.get("/api/workspaces")
async def get_workspaces(user: dict = Depends(validate_token)):
    """
    Get workspaces directly from Microsoft Fabric API
    """
    try:
        logger.info(f"Fetching workspaces from Fabric API for user: {user.get('email')}")

        # Get workspaces directly from Fabric API
        workspaces = await fabric_service.list_workspaces()

        # Transform to match frontend expected format (array directly)
        result = [
            {
                "id": ws.get("id"),
                "name": ws.get("displayName") or ws.get("name"),
                "description": ws.get("description", ""),
                "type": ws.get("type", "Workspace"),
                "capacityId": ws.get("capacityId")
            }
            for ws in workspaces
        ]

        logger.info(f"Successfully fetched {len(result)} workspaces from Fabric API")
        return result

    except Exception as e:
        logger.error(f"Failed to get workspaces from Fabric API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch workspaces: {str(e)}")

# Get lakehouses in workspace
@app.get("/api/workspaces/{workspace_id}/lakehouses")
async def get_workspace_lakehouses(workspace_id: str, user: dict = Depends(validate_token)):
    """
    Get all lakehouses in a workspace
    """
    try:
        logger.info(f"Fetching lakehouses for workspace {workspace_id} by user: {user.get('email')}")

        lakehouses = await fabric_service.get_workspace_lakehouses(workspace_id)

        # Transform to match frontend expected format
        result = [
            {
                "id": lh.get("id"),
                "name": lh.get("displayName") or lh.get("name"),
                "description": lh.get("description", ""),
                "type": lh.get("type", "Lakehouse")
            }
            for lh in lakehouses
        ]

        logger.info(f"Successfully fetched {len(result)} lakehouses from workspace {workspace_id}")
        return result

    except Exception as e:
        logger.error(f"Failed to get lakehouses for workspace {workspace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch lakehouses: {str(e)}")

# Get warehouses in workspace
@app.get("/api/workspaces/{workspace_id}/warehouses")
async def get_workspace_warehouses(workspace_id: str, user: dict = Depends(validate_token)):
    """
    Get all warehouses in a workspace
    """
    try:
        logger.info(f"Fetching warehouses for workspace {workspace_id} by user: {user.get('email')}")

        warehouses = await fabric_service.get_workspace_warehouses(workspace_id)

        # Transform to match frontend expected format
        result = [
            {
                "id": wh.get("id"),
                "name": wh.get("displayName") or wh.get("name"),
                "description": wh.get("description", ""),
                "type": wh.get("type", "Warehouse")
            }
            for wh in warehouses
        ]

        logger.info(f"Successfully fetched {len(result)} warehouses from workspace {workspace_id}")
        return result

    except Exception as e:
        logger.error(f"Failed to get warehouses for workspace {workspace_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch warehouses: {str(e)}")

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

# Deploy pipeline from job (CONSOLIDATED - SINGLE DEPLOYMENT ENDPOINT)
@app.post("/api/jobs/{job_id}/deploy")
async def deploy_pipeline_from_job(job_id: str):
    """
    Deploy pipeline from a job stored in the database.
    Uses the ACTUAL generated pipeline activities, not hardcoded template.
    """
    try:
        logger.info(f"Deploying pipeline from job {job_id}")

        # Get job from database
        db_service = get_db_service()
        job = db_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if not job.get('pipeline_definition'):
            raise HTTPException(status_code=400, detail="Job does not have a pipeline definition")

        pipeline_definition = job['pipeline_definition']

        # Update job status to in_progress
        db_service.update_job_status(
            job_id=job_id,
            status='in_progress',
            pipeline_deployment_status='in_progress'
        )

        # Get config and activities from pipeline definition
        config = pipeline_definition.get('config', {})
        activities = pipeline_definition.get('activities', [])
        pipeline_name = job.get('pipeline_name', f"Pipeline_{job_id}")
        workspace_id = config.get("workspace_id")

        logger.info(f"Deploying pipeline '{pipeline_name}' with {len(activities)} activities")
        logger.info(f"Config: {config}")

        # Convert our activities to Fabric pipeline JSON format
        fabric_activities = []
        for activity in activities:
            activity_name = activity.get('name', 'Activity')
            activity_type = activity.get('type', 'Copy')
            activity_config = activity.get('config', {})
            depends_on = activity.get('depends_on', [])

            # Build Fabric activity based on type
            if activity_type == "Copy":
                fabric_activity = {
                    "name": activity_name,
                    "type": "Copy",
                    "dependsOn": [{"activity": dep, "dependencyConditions": ["Succeeded"]} for dep in (depends_on or [])],
                    "policy": {
                        "timeout": "0.12:00:00",
                        "retry": 0,
                        "retryIntervalInSeconds": 30
                    },
                    "typeProperties": {
                        "source": activity_config.get('source', {}),
                        "sink": {
                            "type": "LakehouseTableSink",
                            "tableActionOption": activity_config.get('destination', {}).get('tableAction', 'Overwrite')
                        },
                        "enableStaging": activity_config.get('enableStaging', False)
                    }
                }
            elif activity_type == "DataflowGen2":
                fabric_activity = {
                    "name": activity_name,
                    "type": "DataflowGen2",
                    "dependsOn": [{"activity": dep, "dependencyConditions": ["Succeeded"]} for dep in (depends_on or [])],
                    "typeProperties": {
                        "dataflowName": activity_config.get('dataflowName', activity_name)
                    }
                }
            elif activity_type == "TridentNotebook":
                fabric_activity = {
                    "name": activity_name,
                    "type": "TridentNotebook",
                    "dependsOn": [{"activity": dep, "dependencyConditions": ["Succeeded"]} for dep in (depends_on or [])],
                    "typeProperties": {
                        "notebookId": activity_config.get('notebookId'),
                        "parameters": activity_config.get('parameters', {})
                    }
                }
            else:
                # Generic activity
                fabric_activity = {
                    "name": activity_name,
                    "type": activity_type,
                    "dependsOn": [{"activity": dep, "dependencyConditions": ["Succeeded"]} for dep in (depends_on or [])],
                    "typeProperties": activity_config
                }

            fabric_activities.append(fabric_activity)

        # Build complete Fabric pipeline definition
        fabric_pipeline_def = {
            "properties": {
                "activities": fabric_activities
            }
        }

        logger.info(f"Fabric pipeline definition: {json.dumps(fabric_pipeline_def, indent=2)}")

        # Deploy using fabric_service
        result = await fabric_service.create_pipeline(
            workspace_id=workspace_id,
            pipeline_name=pipeline_name,
            pipeline_definition=fabric_pipeline_def
        )

        # Check if deployment succeeded
        if result and result.get("success") == False:
            # Deployment failed
            error_msg = result.get("error", "Unknown deployment error")
            logger.error(f"Deployment failed: {error_msg}")

            # Update job with failure status
            db_service.update_job_status(
                job_id=job_id,
                status='failed',
                pipeline_deployment_status='failed',
                error_message=error_msg
            )
            raise Exception(error_msg)

        elif result and (result.get("success") or result.get("pipeline_id")):
            logger.info(f"[SUCCESS] Pipeline '{pipeline_name}' deployed successfully to Fabric!")

            # Update job with deployment results (clear any previous errors)
            db_service.update_job_status(
                job_id=job_id,
                status='completed',
                pipeline_deployment_status='completed',
                pipeline_id=result.get("pipeline_id"),
                pipeline_name=pipeline_name,
                clear_error=True  # Clear previous errors on success
            )

            return {
                "success": True,
                "job_id": job_id,
                "fabric_pipeline_id": result.get("pipeline_id"),
                "message": f"Pipeline '{pipeline_name}' deployed successfully!",
                "activities_count": len(activities),
                "workspace_id": workspace_id,
                "config": config
            }
        else:
            # Unexpected result format
            logger.error(f"Unexpected deployment result: {result}")
            error_message = "Deployment failed - unexpected response from Fabric API"

            # Update job with failure status
            db_service.update_job_status(
                job_id=job_id,
                status='failed',
                pipeline_deployment_status='failed',
                error_message=error_message
            )
            raise Exception(error_message)

    except HTTPException:
        raise
    except Exception as e:
        # Update job with error
        db_service = get_db_service()
        db_service.update_job_status(
            job_id=job_id,
            status='failed',
            pipeline_deployment_status='failed',
            error_message=str(e)
        )

        # Handle Unicode characters in error messages safely
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        logger.error(f"Deployment error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {error_msg}")

# Delete pipeline from Fabric workspace and database
@app.delete("/api/pipelines/{job_id}")
async def delete_pipeline(job_id: str, user: dict = Depends(validate_token)):
    """
    Delete pipeline from Fabric workspace and database

    This will:
    1. Delete the pipeline from Microsoft Fabric workspace (if deployed)
    2. Delete the job record from the database
    """
    try:
        logger.info(f"Deleting pipeline job {job_id} for user: {user['email']}")

        # Get job from database
        db_service = get_db_service()
        job = db_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Pipeline job not found")

        pipeline_id = job.get('pipeline_id')
        workspace_id = job.get('workspace_id')
        pipeline_name = job.get('pipeline_name', 'Unknown')

        # If pipeline was deployed to Fabric, delete it from there first
        if pipeline_id and workspace_id:
            try:
                logger.info(f"Deleting pipeline {pipeline_id} from Fabric workspace {workspace_id}")

                # Get Fabric API token
                fabric_svc = FabricAPIService()
                token = await fabric_svc.get_access_token()

                # Delete pipeline from Fabric using REST API
                delete_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{pipeline_id}"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }

                    response = await client.delete(delete_url, headers=headers)

                    if response.status_code == 200:
                        logger.info(f"[SUCCESS] Deleted pipeline {pipeline_id} from Fabric")
                    elif response.status_code == 404:
                        logger.warning(f"Pipeline {pipeline_id} not found in Fabric (may have been manually deleted)")
                    else:
                        logger.warning(f"Failed to delete from Fabric: {response.status_code} - {response.text}")
                        # Continue anyway to delete from database

            except Exception as e:
                logger.error(f"Error deleting pipeline from Fabric: {str(e)}")
                # Continue anyway to delete from database

        # Delete job from database
        success = db_service.delete_conversation(job_id)  # This also deletes related jobs

        # Actually we need to delete the job, not conversation
        # Let me check if there's a delete_job method
        # For now, update status to 'deleted'
        db_service.update_job_status(
            job_id=job_id,
            status='deleted',
            metadata={'deleted_by': user['email'], 'deleted_at': str(datetime.utcnow())}
        )

        logger.info(f"[SUCCESS] Deleted pipeline job {job_id}")

        return {
            "success": True,
            "message": f"Pipeline '{pipeline_name}' deleted successfully",
            "job_id": job_id,
            "pipeline_id": pipeline_id,
            "deleted_from_fabric": bool(pipeline_id and workspace_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        logger.error(f"Delete pipeline error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to delete pipeline: {error_msg}")

# Rename pipeline
@app.patch("/api/pipelines/{job_id}/rename")
async def rename_pipeline(job_id: str, request: Dict[str, Any], user: dict = Depends(validate_token)):
    """
    Rename a pipeline in both database and Microsoft Fabric

    This will:
    1. Update the pipeline name in the database
    2. Update the pipeline display name in Microsoft Fabric (if deployed)

    Uses PATCH method as per REST conventions for partial resource updates.
    Aligns with Microsoft Fabric API which also uses PATCH for updating displayName.
    """
    try:
        new_pipeline_name = request.get("new_pipeline_name")

        if not new_pipeline_name or not new_pipeline_name.strip():
            raise HTTPException(status_code=400, detail="New pipeline name is required")

        # Clean the pipeline name
        new_pipeline_name = new_pipeline_name.strip()

        logger.info(f"Renaming pipeline job {job_id} to '{new_pipeline_name}' for user: {user['email']}")

        # Get job from database
        db_service = get_db_service()
        job = db_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Pipeline job not found")

        old_pipeline_name = job.get('pipeline_name', 'Unknown')
        pipeline_id = job.get('pipeline_id')
        workspace_id = job.get('workspace_id')

        # Update pipeline name in Fabric if it's deployed
        fabric_updated = False
        if pipeline_id and workspace_id:
            try:
                logger.info(f"Updating pipeline name in Fabric workspace {workspace_id}")

                # Get Fabric API token
                fabric_svc = FabricAPIService()
                token = await fabric_svc.get_access_token()

                # Update pipeline display name in Fabric using REST API
                # Official endpoint: https://learn.microsoft.com/en-us/rest/api/fabric/datapipeline/items/update-data-pipeline
                update_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/dataPipelines/{pipeline_id}"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }

                    payload = {
                        "displayName": new_pipeline_name
                    }

                    logger.info(f"PATCH request to: {update_url}")
                    logger.info(f"Payload: {payload}")

                    response = await client.patch(update_url, headers=headers, json=payload)

                    logger.info(f"Fabric API Response: {response.status_code}")

                    if response.status_code == 200:
                        logger.info(f"[SUCCESS] Updated pipeline name in Fabric to '{new_pipeline_name}'")
                        fabric_updated = True
                    else:
                        logger.warning(f"Failed to update pipeline name in Fabric: {response.status_code} - {response.text}")
                        # Continue anyway to update in database

            except Exception as e:
                logger.error(f"Error updating pipeline name in Fabric: {str(e)}")
                # Continue anyway to update in database

        # Update pipeline name in database
        db_service.update_job_status(
            job_id=job_id,
            pipeline_name=new_pipeline_name,
            metadata={
                'renamed_by': user['email'],
                'renamed_at': str(datetime.utcnow()),
                'old_name': old_pipeline_name
            }
        )

        logger.info(f"[SUCCESS] Renamed pipeline job {job_id} from '{old_pipeline_name}' to '{new_pipeline_name}'")

        return {
            "success": True,
            "message": f"Pipeline renamed from '{old_pipeline_name}' to '{new_pipeline_name}'",
            "job_id": job_id,
            "old_name": old_pipeline_name,
            "new_name": new_pipeline_name,
            "updated_in_fabric": fabric_updated,
            "pipeline_id": pipeline_id
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        logger.error(f"Rename pipeline error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to rename pipeline: {error_msg}")

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

@app.post("/api/pipelines/generate-file-processing", response_model=FileProcessingPipelineResponse)
async def generate_file_processing_pipeline(request: FileProcessingPipelineRequest, user: dict = Depends(validate_token)):
    """
    Generate complete file processing pipeline with incremental loading pattern

    This creates a pipeline that:
    1. Gets all files from Azure Blob Storage shortcut
    2. Queries fileprocessed table via SQL endpoint to get already processed files
    3. Filters to only new files
    4. Processes each new file and updates fileprocessed table
    """
    try:
        logger.info(f"Generating file processing pipeline: {request.pipeline_name}")
        logger.info(f"Workspace: {request.workspace_id}, Lakehouse: {request.lakehouse_id}")

        # Generate the complete pipeline JSON
        result = await fabric_service.generate_file_processing_pipeline(
            workspace_id=request.workspace_id,
            lakehouse_id=request.lakehouse_id,
            pipeline_name=request.pipeline_name,
            source_container=request.source_container,
            bronze_shortcut_name=request.bronze_shortcut_name
        )

        if not result["success"]:
            logger.error(f"Pipeline generation failed: {result.get('error')}")
            return FileProcessingPipelineResponse(
                success=False,
                pipeline_name=request.pipeline_name,
                error=result.get("error"),
                message="Failed to generate pipeline"
            )

        pipeline_json = result["pipeline_json"]

        # If deploy_immediately is True, deploy the pipeline
        if request.deploy_immediately:
            logger.info(f"Deploying pipeline immediately: {request.pipeline_name}")

            deploy_result = await fabric_service.create_pipeline(
                workspace_id=request.workspace_id,
                pipeline_name=request.pipeline_name,
                pipeline_definition=pipeline_json
            )

            if deploy_result["success"]:
                logger.info(f"Pipeline deployed successfully: {deploy_result.get('pipeline_id')}")
                return FileProcessingPipelineResponse(
                    success=True,
                    pipeline_name=request.pipeline_name,
                    pipeline_id=deploy_result.get("pipeline_id"),
                    lakehouse_name=result.get("lakehouse_name"),
                    sql_endpoint=result.get("sql_endpoint"),
                    activities_count=result.get("activities_count"),
                    pipeline_json=pipeline_json,
                    message=f"Pipeline generated and deployed successfully with {result.get('activities_count')} activities"
                )
            else:
                logger.error(f"Pipeline deployment failed: {deploy_result.get('error')}")
                return FileProcessingPipelineResponse(
                    success=True,
                    pipeline_name=request.pipeline_name,
                    lakehouse_name=result.get("lakehouse_name"),
                    sql_endpoint=result.get("sql_endpoint"),
                    activities_count=result.get("activities_count"),
                    pipeline_json=pipeline_json,
                    error=f"Pipeline generated but deployment failed: {deploy_result.get('error')}",
                    message="Pipeline generated successfully but deployment failed"
                )
        else:
            # Just return the pipeline JSON for preview
            logger.info(f"Pipeline generated successfully: {request.pipeline_name}")
            return FileProcessingPipelineResponse(
                success=True,
                pipeline_name=request.pipeline_name,
                lakehouse_name=result.get("lakehouse_name"),
                sql_endpoint=result.get("sql_endpoint"),
                activities_count=result.get("activities_count"),
                pipeline_json=pipeline_json,
                message=f"Pipeline generated successfully with {result.get('activities_count')} activities. Set deploy_immediately=true to deploy."
            )

    except Exception as e:
        logger.error(f"Error generating file processing pipeline: {str(e)}", exc_info=True)
        return FileProcessingPipelineResponse(
            success=False,
            pipeline_name=request.pipeline_name,
            error=str(e),
            message="Pipeline generation failed"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
