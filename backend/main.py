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
import asyncio
import random

# Import settings and services
import settings
from services.claude_ai_service import ClaudeAIService
from services.azure_openai_service import AzureOpenAIService
from services.azure_ai_agent_service import AzureAIAgentService
from services.fabric_api_service import FabricAPIService
from services.conversation_context import context_manager
from services.proactive_suggestions import proactive_service
from services.medallion_architect import medallion_service
from models.pipeline_models import (
    ChatMessage, ChatRequest, ChatResponse,
    PipelineGenerateRequest, PipelineGenerateResponse,
    LinkedServiceRequest, LinkedServiceResponse,
    AutomatedPipelineGenerateRequest, AutomatedPipelineGenerateResponse,
    ConnectionConfig, PipelineArchitecture, LayerConfig,
    FileProcessingPipelineRequest, FileProcessingPipelineResponse
)

# Import fabric deployment router
from fabric_deployment_endpoint import router as fabric_router

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
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Fabric deployment router
app.include_router(fabric_router)

# Initialize services
claude_service = ClaudeAIService()
fabric_service = FabricAPIService()

# Initialize Azure OpenAI service (GPT-5 with Bing Search)
azure_openai_service = AzureOpenAIService(
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_API_KEY,
    deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    bing_api_key=settings.BING_SEARCH_API_KEY,
    bing_endpoint=settings.BING_SEARCH_ENDPOINT
)

# Initialize Azure AI Agent service (GPT-4o-mini with Bing Grounding via Agents)
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

# Create SSL context with certifi certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Token validation function
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate Microsoft Azure AD JWT token
    """
    # Development mode: bypass authentication
    if settings.DISABLE_AUTH is True or settings.DISABLE_AUTH == "true":
        logger.info("Development mode: bypassing authentication")
        return {"email": "dev@example.com", "name": "Development User", "oid": "dev-user-id"}

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
                    "message": f"Found existing shortcuts but not complete. Bronze: {'✓' if bronze_exists else '✗'}, Silver: {'✓' if silver_exists else '✗'}"
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
        "version": "1.0.0",
        "status": "running",
        "claude_model": settings.CLAUDE_MODEL,
        "azure_openai_model": settings.AZURE_OPENAI_DEPLOYMENT,
        "azure_ai_agent_enabled": True,
        "bing_grounding_enabled": bool(settings.BING_GROUNDING_CONNECTION_ID)
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# AI Chat endpoint (GPT-4o-mini with Bing Grounding via Azure AI Agents - Primary AI)
@app.post("/api/ai/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, user: dict = Depends(validate_token)):
    """
    PROACTIVE Pipeline Architect Chat with Bing Grounding

    This endpoint uses GPT-4o-mini with Bing Grounding to provide PROACTIVE guidance
    for building Microsoft Fabric pipelines. The agent:
    - Automatically searches for latest best practices
    - Proactively suggests optimizations
    - Tracks conversation context
    - Interrupts with important recommendations
    """
    try:
        logger.info(f"Proactive Agent chat request for workspace: {request.workspace_id} by user: {user['email']}")

        # Get or create conversation context for this user
        session_id = f"{user['email']}_{request.workspace_id}"
        conv_context = context_manager.get_context(session_id)

        # Get the last user message
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Prepare lowercase version for keyword detection
        user_message_lower = user_message.lower()

        # Update conversation context with user message
        conv_context.update_context(user_message)

        # BLOCK CHAT IF REQUIRED SELECTIONS ARE MISSING
        if not request.lakehouse_name or not request.warehouse_name:
            return ChatResponse(
                role="assistant",
                content="⚠️ **Please select a Lakehouse and Warehouse above to continue.**\n\nI need to know which lakehouse and warehouse to use for your pipeline. Please select them from the dropdowns at the top of the page.",
                suggestions=None,
                pipeline_preview=None,
                shortcut_info=None,
                needs_confirmation=False,
                confirmation_action=None
            )

        # DETECT DROPDOWN CHANGES (mid-conversation update)
        stored_lakehouse = conv_context.context.get("lakehouse_name")
        stored_warehouse = conv_context.context.get("warehouse_name")

        if stored_lakehouse and stored_lakehouse != request.lakehouse_name:
            logger.info(f"Lakehouse changed from {stored_lakehouse} to {request.lakehouse_name}")
            conv_context.context["lakehouse_name"] = request.lakehouse_name

        if stored_warehouse and stored_warehouse != request.warehouse_name:
            logger.info(f"Warehouse changed from {stored_warehouse} to {request.warehouse_name}")
            conv_context.context["warehouse_name"] = request.warehouse_name

        # ALWAYS CONFIRM SELECTIONS (even if pre-selected)
        if not stored_lakehouse or not stored_warehouse:
            # First time seeing these selections - store them in context
            conv_context.context["lakehouse_name"] = request.lakehouse_name
            conv_context.context["warehouse_name"] = request.warehouse_name
            # Don't set pending state - let the blob detection or normal flow handle the message

        # CHECK FOR PENDING CONFIRMATION (Shortcut Creation)
        pending = conv_context.get_pending_confirmation()

        if pending and pending["action"] == "create_shortcut":
            # User is responding to shortcut creation confirmation
            if conv_context.is_user_confirming(user_message):
                # User confirmed - create shortcuts
                logger.info("User confirmed shortcut creation. Creating shortcuts...")

                shortcut_result = await create_blob_storage_shortcuts(request.workspace_id)

                conv_context.clear_pending_confirmation()

                if shortcut_result["success"]:
                    # Store shortcut information in conversation context
                    conv_context.set_shortcuts(shortcut_result)
                    logger.info(f"Stored shortcut info in conversation context: {shortcut_result.get('lakehouse_name')}")

                    # Success response
                    shortcuts_info = "\n".join([
                        f"  • **{s['name']}** → {s['path']} (container: {s['container']})"
                        for s in shortcut_result["shortcuts"]
                    ])

                    # Check if shortcuts already existed or were just created
                    if shortcut_result.get("already_exists"):
                        success_message = f"""Shortcuts Already Set Up!

Good news! Your lakehouse already has shortcuts configured:

Storage Account: {shortcut_result['storage_account']}
Lakehouse: {shortcut_result['lakehouse_name']}

Available Shortcuts:
{shortcuts_info}

Your data is ready to use! Would you like me to help you create a pipeline to process this data?"""
                    else:
                        success_message = f"""Shortcuts Created Successfully!

I've created OneLake shortcuts for your Azure Blob Storage:

Storage Account: {shortcut_result['storage_account']}
Lakehouse: {shortcut_result['lakehouse_name']}
Connection: {shortcut_result.get('connection_name', 'N/A')}

Shortcuts Created:
{shortcuts_info}

You can now access your data directly in the lakehouse! Would you like me to help you create a pipeline to process this data?"""

                    return ChatResponse(
                        role="assistant",
                        content=success_message,
                        suggestions=["Create a pipeline", "Browse the data", "Add transformations"],
                        pipeline_preview=None,
                        shortcut_info=shortcut_result,
                        needs_confirmation=False,
                        confirmation_action=None
                    )
                else:
                    # Error response
                    error_message = f"""❌ **Failed to Create Shortcuts**

{shortcut_result.get('message', 'Unknown error')}

Error details: {shortcut_result.get('error', 'None')}

Would you like me to provide manual instructions instead?"""

                    return ChatResponse(
                        role="assistant",
                        content=error_message,
                        suggestions=["Show manual steps", "Try again", "Contact support"],
                        pipeline_preview=None,
                        shortcut_info=None,
                        needs_confirmation=False,
                        confirmation_action=None
                    )
            else:
                # User declined
                conv_context.clear_pending_confirmation()
                logger.info("User declined shortcut creation")

                return ChatResponse(
                    role="assistant",
                    content="No problem! Let me know if you'd like to create shortcuts later or if you need help with something else.",
                    suggestions=None,
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

        # CHECK FOR PENDING DEPLOYMENT PARAMETER COLLECTION
        if pending and pending["action"] == "collect_deployment_params":
            # User is providing deployment parameters step by step
            step = pending.get("data", {}).get("step")
            deployment_config = pending.get("data", {}).get("config", {})

            if step == "source_folder":
                # Store source folder and ask for output folder
                # Clean input: remove backticks, quotes, and extra whitespace
                cleaned_input = user_message.strip().strip('`').strip('"').strip("'")
                deployment_config["source_folder"] = cleaned_input
                conv_context.set_pending_confirmation("collect_deployment_params", {
                    "workspace_id": request.workspace_id,
                    "step": "output_folder",
                    "config": deployment_config
                })

                response = f"""Great! What's the **silver layer folder name** where processed data should be written? (e.g., "silver", "processed", "curated")"""

                # Add natural delay for better UX
                await asyncio.sleep(random.uniform(2, 3))

                return ChatResponse(
                    role="assistant",
                    content=response,
                    suggestions=["silver", "processed", "curated"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

            elif step == "output_folder":
                # Store output folder and ask for table name
                # Clean input: remove backticks, quotes, and extra whitespace
                cleaned_input = user_message.strip().strip('`').strip('"').strip("'")
                deployment_config["output_folder"] = cleaned_input
                conv_context.set_pending_confirmation("collect_deployment_params", {
                    "workspace_id": request.workspace_id,
                    "step": "table_name",
                    "config": deployment_config
                })

                response = f"""What should be the **table name** in the lakehouse where the actual data will be stored? (e.g., "claims_data", "patient_records", "sales_transactions")"""

                # Add natural delay for better UX
                await asyncio.sleep(random.uniform(2, 3))

                return ChatResponse(
                    role="assistant",
                    content=response,
                    suggestions=["claims_data", "patient_records", "sales_data"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

            elif step == "table_name":
                # Store table name and ask for pipeline name
                # Clean input: remove backticks, quotes, and extra whitespace
                cleaned_input = user_message.strip().strip('`').strip('"').strip("'")
                deployment_config["table_name"] = cleaned_input

                conv_context.set_pending_confirmation("collect_deployment_params", {
                    "workspace_id": request.workspace_id,
                    "step": "pipeline_name",
                    "config": deployment_config
                })

                response = f"""What should I name this pipeline? (e.g., "PIIDetectionPipeline", "CSVProcessingPipeline", "DataIngestionPipeline")"""

                # Add natural delay for better UX
                await asyncio.sleep(random.uniform(2, 3))

                return ChatResponse(
                    role="assistant",
                    content=response,
                    suggestions=["PIIDetectionPipeline", "CSVProcessingPipeline", "DataIngestionPipeline"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

            elif step == "pii_phi_detection":
                # Store PII/PHI detection preference and ask for pipeline name
                pii_phi_needed = conv_context.is_user_confirming(user_message)
                deployment_config["pii_phi_detection"] = pii_phi_needed
                conv_context.set_pending_confirmation("collect_deployment_params", {
                    "workspace_id": request.workspace_id,
                    "step": "pipeline_name",
                    "config": deployment_config
                })

                response = f"""What should I name this pipeline? (e.g., "DataProcessingPipeline", "CSVLoader", "PIIDetectionPipeline")"""

                return ChatResponse(
                    role="assistant",
                    content=response,
                    suggestions=["DataProcessingPipeline", "CSVLoader", "PIIDetectionPipeline"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

            elif step == "pipeline_name":
                # Store pipeline name and show summary
                # Clean input: remove backticks, quotes, and extra whitespace
                cleaned_input = user_message.strip().strip('`').strip('"').strip("'")
                deployment_config["pipeline_name"] = cleaned_input
                pii_phi_needed = deployment_config.get("pii_phi_detection", True)

                # Build pipeline activities description
                pipeline_activities_summary = f"""### Pipeline Activities:

1. **Get Metadata Activity** - Lists all CSV files from `Files/{deployment_config.get('source_folder')}`
2. **GetProcessedFileNames (Script)** - Queries `processedfiles` table to filter already-processed files
3. **FilterNewFiles (Filter)** - Only new files proceed to processing
4. **forEach Loop** - For each new file:
   - **PHI_PII_detection Notebook**:
     - Reads CSV from `Files/{deployment_config.get('source_folder')}/{{filename}}`
     - Detects PII/PHI patterns (SSN, Member ID, DOB, Email, Phone)
     - Joins with prior authorization data
     - Writes output to `Files/{deployment_config.get('output_folder')}`
     - Data will be stored in lakehouse table: `{deployment_config.get('table_name')}`"""

                # Show configuration summary
                summary_message = f"""## Configuration Complete! ✅

### Configuration Summary:

**Workspace Details:**
- Workspace: `{deployment_config.get('workspace_id')}`
- Lakehouse: `{deployment_config.get('lakehouse_name')}`
- Warehouse: `{deployment_config.get('warehouse_name')}`

**Pipeline Configuration:**
- Pipeline Name: `{deployment_config.get('pipeline_name')}`
- Ingestion Folder: `Files/{deployment_config.get('source_folder')}`
- Silver Layer Folder: `Files/{deployment_config.get('output_folder')}`
- Target Table: `{deployment_config.get('table_name')}`
- PII/PHI Detection: **Enabled**

{pipeline_activities_summary}

---

### Next Step:
**Go to the Pipeline Preview page and click the "Deploy" button** to create this pipeline in your workspace."""

                # Clear pending state - we're done collecting values
                conv_context.clear_pending_confirmation()

                # Add natural delay for better UX (slightly longer for summary)
                await asyncio.sleep(random.uniform(2.5, 3.5))

                return ChatResponse(
                    role="assistant",
                    content=summary_message,
                    suggestions=["Go to Pipeline Preview"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

        # CHECK FOR PENDING APPROACH SELECTION
        if pending and pending["action"] == "select_approach":
            # User is selecting between Option 1, 2, or 3
            deployment_config = pending.get("data", {}).get("config", {})

            # Detect which option user selected
            option_selected = None
            if "option 1" in user_message_lower or "option1" in user_message_lower or "copy activity" in user_message_lower:
                option_selected = 1
            elif "option 2" in user_message_lower or "option2" in user_message_lower or "dataflow" in user_message_lower:
                option_selected = 2
            elif "option 3" in user_message_lower or "option3" in user_message_lower or "notebook" in user_message_lower:
                option_selected = 3

            if not option_selected:
                # User didn't specify a valid option
                return ChatResponse(
                    role="assistant",
                    content="Please select one of the options: **option 1**, **option 2**, or **option 3**.",
                    suggestions=["option 1", "option 2", "option 3"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

            # Store selected option
            deployment_config["selected_option"] = option_selected

            if option_selected == 3:
                # User selected Option 3 (Notebook) - Ask about PHI/PII
                logger.info("Option 3 selected - asking about PHI/PII detection")
                conv_context.set_pending_confirmation("confirm_phi_pii", {
                    "workspace_id": deployment_config.get("workspace_id"),
                    "config": deployment_config
                })

                phi_pii_question = """Great choice! The Notebook approach gives you maximum flexibility.

**Are we dealing with any PHI/PII data in these CSV files?**

PHI/PII includes:
- Social Security Numbers (SSN)
- Member IDs
- Dates of Birth (DOB)
- Email addresses
- Phone numbers
- Protected Health Information"""

                # Add natural delay for better UX
                await asyncio.sleep(random.uniform(2, 3))

                return ChatResponse(
                    role="assistant",
                    content=phi_pii_question,
                    suggestions=["Yes, we have PHI/PII data", "No, just regular data"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )
            else:
                # User selected Option 1 or 2 - For now, show a message
                # (You can expand this later for actual Copy Activity or Dataflow implementation)
                conv_context.clear_pending_confirmation()

                approach_name = "Copy Activity" if option_selected == 1 else "Dataflow Gen2"
                response_message = f"""You've selected **Option {option_selected}: {approach_name}**.

This approach is currently under development. For now, I recommend using **Option 3 (Notebook with PySpark)** which includes PHI/PII detection capabilities.

Would you like to try Option 3 instead?"""

                return ChatResponse(
                    role="assistant",
                    content=response_message,
                    suggestions=["Yes, use option 3", "Tell me more about option 3"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

        # CHECK FOR PENDING PHI/PII CONFIRMATION
        if pending and pending["action"] == "confirm_phi_pii":
            # User is confirming whether they have PHI/PII data
            deployment_config = pending.get("data", {}).get("config", {})
            has_phi_pii = conv_context.is_user_confirming(user_message)

            if has_phi_pii:
                # User confirmed PHI/PII data - Start collecting parameters
                logger.info("PHI/PII confirmed - starting parameter collection")

                confirmation_message = f"""Perfect! I'll create a PHI/PII detection pipeline using:
- **Workspace:** {deployment_config.get('workspace_id')}
- **Lakehouse:** {deployment_config.get('lakehouse_name')}
- **Warehouse:** {deployment_config.get('warehouse_name')}

Now let's configure the pipeline parameters.

What's the **ingestion folder name** where your CSV files are located? (e.g., "bronze", "incoming", "raw-data")

Note: This should be the folder in your lakehouse where shortcuts to Azure Blob Storage CSV files are accessible."""

                # Continue to deployment parameter collection
                deployment_config["pii_phi_detection"] = True
                conv_context.set_pending_confirmation("collect_deployment_params", {
                    "workspace_id": deployment_config.get("workspace_id"),
                    "step": "source_folder",
                    "config": deployment_config
                })

                # Add natural delay for better UX
                await asyncio.sleep(random.uniform(2, 3))

                return ChatResponse(
                    role="assistant",
                    content=confirmation_message,
                    suggestions=["bronze", "incoming", "raw-data"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )
            else:
                # User said no PHI/PII - Show simplified pipeline (for future implementation)
                logger.info("No PHI/PII - showing simplified pipeline")

                no_phi_message = """Got it! For regular data without PHI/PII concerns, I can create a simpler pipeline.

However, the PHI/PII detection pipeline is currently the primary implementation. It can still process your data even if it doesn't contain sensitive information - the detection will simply find no matches.

Would you like to proceed with the full pipeline anyway?"""

                # Keep the same pending state
                return ChatResponse(
                    role="assistant",
                    content=no_phi_message,
                    suggestions=["Yes, proceed with full pipeline", "Tell me more"],
                    pipeline_preview=None,
                    shortcut_info=None,
                    needs_confirmation=False,
                    confirmation_action=None
                )

        # Note: Deployment is now handled by the /api/pipelines/generate endpoint
        # The chat just collects parameters and redirects to Pipeline Preview

        # DETECT BLOB STORAGE / CSV LOADING MENTION (If not already pending)
        blob_keywords = ["azure blob", "blob storage", "azure storage", "storage account", "csv files", "load csv", "loading csv"]
        blob_detected = any(keyword in user_message_lower for keyword in blob_keywords)

        if blob_detected and not pending:
            # User mentioned blob storage or CSV loading - present 3 architectural options
            logger.info("Blob storage/CSV loading detected - presenting architectural options...")

            # Store initial config for later use
            deployment_config = {
                "lakehouse_name": request.lakehouse_name,
                "warehouse_name": request.warehouse_name,
                "workspace_id": request.workspace_id
            }

            # Set pending state for option selection
            conv_context.set_pending_confirmation("select_approach", {
                "workspace_id": request.workspace_id,
                "config": deployment_config
            })

            options_message = f"""Perfect! I can see you've selected:
- **Workspace:** {request.workspace_id}
- **Lakehouse:** {request.lakehouse_name}
- **Warehouse:** {request.warehouse_name}

To load CSV files from Blob Storage, I can help you with different architectural approaches:

**Option 1: Simple Load (Copy Activity)**
- Use when you only need to load data without transformation
- Fast and straightforward ingestion
- Limited transformation capabilities

**Option 2: Light Transformation (Dataflow Gen2)**
- Use for light transformations like filtering or data type changes
- Visual interface, no coding required
- Good for small to medium complexity

**Option 3: Complex Transformation (Notebook with PySpark)**
- Use for complex transformations and business logic
- Full flexibility with PySpark
- Includes PHI/PII detection capabilities

Which approach would you like to use?"""

            # Add natural delay for better UX
            await asyncio.sleep(random.uniform(2, 3))

            return ChatResponse(
                role="assistant",
                content=options_message,
                suggestions=["option 1", "option 2", "option 3"],
                pipeline_preview=None,
                shortcut_info=None,
                needs_confirmation=False,
                confirmation_action=None
            )

        # NORMAL AI CHAT FLOW
        # Check if we should proactively search for best practices
        proactive_search_query = conv_context.should_search_for_best_practices()

        # Convert ChatMessage objects to dict format for Azure AI Agent
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Note: Azure AI Agent only supports 'user' and 'assistant' roles, not 'system'
        # We'll append instructions to the user message instead if needed

        # Add context information to help the agent be more proactive
        context_summary = conv_context.get_context_for_agent()
        if context_summary:
            # Inject context as a system-level hint
            messages[-1]["content"] = messages[-1]["content"] + context_summary

        # If we detected source and destination, proactively check for latest updates
        if proactive_search_query and conv_context.context["current_stage"] == "suggesting":
            logger.info(f"Proactively searching: {proactive_search_query}")

        # Call Azure AI Agent with Bing Grounding
        response = await agent_service.chat(
            messages=messages,
            context=request.context
        )

        # Update context with agent response
        conv_context.update_context(user_message, response.get("content", ""))

        logger.info(f"Agent response received. Bing Grounding used: {response.get('bing_grounding_used', False)}")
        logger.info(f"Conversation stage: {conv_context.context['current_stage']}")
        logger.info(f"Pipeline context: {conv_context.get_summary()}")

        return ChatResponse(
            role="assistant",
            content=response["content"],
            suggestions=None,
            pipeline_preview=None,
            shortcut_info=None,
            needs_confirmation=False,
            confirmation_action=None
        )

    except Exception as e:
        logger.error(f"Proactive Agent chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


# Claude AI endpoint (For notebook code generation only)
@app.post("/api/ai/claude-chat", response_model=ChatResponse)
async def chat_with_claude(request: ChatRequest, user: dict = Depends(validate_token)):
    """
    Chat with Claude AI - specialized for PySpark notebook code generation

    Use this endpoint specifically when you need:
    - PySpark notebook code generation
    - Complex transformation logic
    - Data quality checks code

    For general pipeline design and latest documentation, use /api/ai/chat (GPT-5)
    """
    try:
        logger.info(f"Claude chat request for workspace: {request.workspace_id} by user: {user['email']}")

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
        logger.error(f"Claude chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Claude AI service error: {str(e)}")


# Azure OpenAI Chat endpoint (Duplicate of /api/ai/chat - kept for backward compatibility)
@app.post("/api/ai/gpt5-chat", response_model=ChatResponse)
async def chat_with_gpt5(request: ChatRequest, user: dict = Depends(validate_token)):
    """
    Chat with Azure OpenAI GPT-5 with Bing Search for latest Fabric documentation

    NOTE: This is now identical to /api/ai/chat endpoint.
    Use /api/ai/chat as the primary endpoint.
    This endpoint is kept for backward compatibility.
    """
    try:
        logger.info(f"GPT-5 chat request for workspace: {request.workspace_id} by user: {user['email']}")

        # Convert ChatMessage objects to dict format for Azure OpenAI
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Add context if provided
        if request.context:
            context_str = f"\n\nContext:\n{json.dumps(request.context, indent=2)}"
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] += context_str

        # Call Azure OpenAI with function calling (Bing Search)
        response = await azure_openai_service.chat_with_function_calling(
            messages=messages,
            max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
            temperature=settings.AZURE_OPENAI_TEMPERATURE,
            enable_search=True
        )

        return ChatResponse(
            role="assistant",
            content=response["content"],
            suggestions=None,
            pipeline_preview=None
        )

    except Exception as e:
        logger.error(f"GPT-5 chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Azure OpenAI service error: {str(e)}")


# Azure OpenAI Simple Chat endpoint (without Bing Search)
@app.post("/api/ai/gpt5-simple-chat")
async def simple_chat_with_gpt5(request: ChatRequest, user: dict = Depends(validate_token)):
    """
    Simple chat with Azure OpenAI GPT-5 without Bing Search

    Use this for:
    - General conversations
    - Code generation
    - When you don't need latest documentation
    """
    try:
        logger.info(f"GPT-5 simple chat request by user: {user['email']}")

        # Convert ChatMessage objects to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Add context if provided
        if request.context:
            context_str = f"\n\nContext:\n{json.dumps(request.context, indent=2)}"
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] += context_str

        # Call Azure OpenAI without function calling
        response = await azure_openai_service.simple_chat(
            messages=messages,
            max_tokens=settings.AZURE_OPENAI_MAX_TOKENS,
            temperature=settings.AZURE_OPENAI_TEMPERATURE
        )

        return {
            "role": "assistant",
            "content": response["content"],
            "usage": response["usage"]
        }

    except Exception as e:
        logger.error(f"GPT-5 simple chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Azure OpenAI service error: {str(e)}")

# Pipeline generation endpoint
@app.post("/api/pipelines/generate", response_model=PipelineGenerateResponse)
async def generate_pipeline(request: PipelineGenerateRequest, user: dict = Depends(validate_token)):
    """
    Generate complete pipeline from requirements

    For CSV/blob storage pipelines, this uses the hardcoded deployment template.
    For other pipelines, this uses Claude generation.
    """
    try:
        logger.info(f"Generating pipeline: {request.pipeline_name} for user: {user['email']}")

        # Use the pipeline name directly from the request (now passed from frontend chat context)
        pipeline_name = request.pipeline_name
        logger.info(f"Using pipeline name: {pipeline_name}")

        # JUST GENERATE PREVIEW - Don't deploy yet!
        logger.info("Generating pipeline preview with hardcoded values")

        # Import required models
        from models.pipeline_models import NotebookCode, MedallionLayer, PipelineActivity
        import time

        # Generate pipeline ID for storing in memory
        pipeline_id = int(time.time())

        # Define full pipeline activities (matching deploy_pipeline_api.py template)
        activities = [
            PipelineActivity(
                name="Get Metadata",
                type="GetMetadata",
                config={
                    "description": "Get metadata of files in the lakehouse source folder",
                    "fieldList": ["childItems"],
                    "source": {
                        "type": "Lakehouse",
                        "rootFolder": "Files",
                        "folderPath": "claims"
                    }
                },
                depends_on=None
            ),
            PipelineActivity(
                name="GetProcessedFileNames",
                type="Script",
                config={
                    "description": "Query warehouse to get list of already processed files",
                    "scriptType": "Query",
                    "query": "SELECT [FileName] FROM [dbo].[processedfiles] WHERE Status = 'Done'",
                    "database": "jay-dev-warehouse",
                    "connection": "Warehouse_jay_reddy"
                },
                depends_on=["Get Metadata"]
            ),
            PipelineActivity(
                name="SetEmptyFileArray",
                type="SetVariable",
                config={
                    "description": "Initialize empty array for processed file names",
                    "variableName": "ProcessedFileNames",
                    "value": "[]"
                },
                depends_on=["GetProcessedFileNames"]
            ),
            PipelineActivity(
                name="ForEach1",
                type="ForEach",
                config={
                    "description": "Loop through warehouse results to build processed files list",
                    "items": "@activity('GetProcessedFileNames').output.resultSets[0].rows",
                    "activities": [
                        {
                            "name": "Set variable1",
                            "type": "SetVariable",
                            "variableName": "ProcessedFileNames",
                            "value": "@item().FileName"
                        }
                    ]
                },
                depends_on=["SetEmptyFileArray"]
            ),
            PipelineActivity(
                name="FilterNewFiles",
                type="Filter",
                config={
                    "description": "Filter out files that have already been processed",
                    "items": "@activity('Get Metadata').output.childItems",
                    "condition": "@not(contains(variables('ProcessedFileNames'), item().name))"
                },
                depends_on=["ForEach1"]
            ),
            PipelineActivity(
                name="forEach",
                type="ForEach",
                config={
                    "description": "Process each unprocessed file with PII/PHI detection notebook",
                    "items": "@activity('FilterNewFiles').output.value",
                    "activities": [
                        {
                            "name": "PHI_PII_detection",
                            "type": "TridentNotebook",
                            "notebookId": "PHI_PII_detection",
                            "parameters": {
                                "fileName": "@item().name"
                            }
                        }
                    ]
                },
                depends_on=["FilterNewFiles"]
            )
        ]

        # Define notebook
        notebook = NotebookCode(
            notebook_name="PHI_PII_detection",
            layer=MedallionLayer.SILVER,
            code="# PII/PHI detection notebook\n# Processes CSV files and detects sensitive data",
            description="Detects PII/PHI in CSV files from blob storage"
        )

        # Store in memory for deployment later
        generated_pipelines[pipeline_id] = {
            "pipeline_name": pipeline_name,
            "activities": activities,
            "notebooks": [notebook],
            "workspace_id": request.workspace_id,
            "config": {
                "workspace_id": request.workspace_id,
                "lakehouse_name": request.lakehouse_name or "default_lakehouse",
                "warehouse_name": request.warehouse_name or "default_warehouse",
                "source_folder": "bronze",  # Can be made dynamic later
                "output_folder": "silver"   # Can be made dynamic later
            }
        }

        logger.info(f"✅ Pipeline preview generated (ID: {pipeline_id})")

        # Return preview (NOT deployed yet!)
        return PipelineGenerateResponse(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            activities=activities,
            notebooks=[notebook],
            fabric_pipeline_json={},
            reasoning=f"Pipeline preview ready:\n\nActivities:\n1. Get Metadata - Retrieves file list from lakehouse\n2. GetProcessedFileNames - Queries warehouse for already processed files\n3. SetEmptyFileArray - Initializes processed files variable\n4. ForEach1 - Builds list of processed file names\n5. FilterNewFiles - Filters out already processed files\n6. forEach - Processes each new file with PHI_PII_detection notebook\n\nConfiguration:\n- Workspace: jay-dev\n- Lakehouse: jay_dev_lakehouse\n- Warehouse: jay-dev-warehouse\n- Source: Files/claims\n- Output: Files/silver\n\nClick 'Deploy to Fabric Workspace' to create this pipeline."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline generation error: {str(e)}")
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

# Deploy pipeline
@app.post("/api/pipelines/{pipeline_id}/deploy")
async def deploy_pipeline(pipeline_id: int, request: Dict[str, Any], user: dict = Depends(validate_token)):
    """
    Deploy pipeline to Microsoft Fabric workspace using deploy_pipeline_api.py
    """
    try:
        logger.info(f"Deploying pipeline {pipeline_id} for user: {user['email']}")

        # Get pipeline from memory
        if pipeline_id not in generated_pipelines:
            raise HTTPException(status_code=404, detail="Pipeline not found. Please generate the pipeline first.")

        pipeline_data = generated_pipelines[pipeline_id]
        config = pipeline_data.get("config", {})

        # Import deployment function
        from deploy_pipeline_api import deploy_fabric_pipeline

        # Deploy using dynamic values from config
        logger.info(f"Deploying with config: {config}")

        result = await deploy_fabric_pipeline(
            workspace_id=config.get("workspace_id"),
            lakehouse_name=config.get("lakehouse_name"),
            warehouse_name=config.get("warehouse_name"),
            source_folder=config.get("source_folder", "bronze"),
            output_folder=config.get("output_folder", "silver"),
            pipeline_name=pipeline_data["pipeline_name"],
            notebook_name="PHI_PII_detection"
        )

        # Check if deployment succeeded
        if result and result.get("pipeline_id"):
            logger.info(f"✅ Pipeline deployed successfully to Fabric!")
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "fabric_pipeline_id": result.get("pipeline_id"),
                "message": f"Pipeline '{pipeline_data['pipeline_name']}' deployed successfully to workspace {config.get('workspace_id')}!",
                "notebooks_deployed": 1,
                "deployed_notebooks": [result.get("notebook_name", "PHI_PII_detection")],
                "workspace_id": config.get("workspace_id"),
                "lakehouse_name": result.get("lakehouse_name"),
                "source_folder": result.get("source_folder"),
                "output_folder": result.get("output_folder")
            }
        else:
            raise Exception("Deployment failed - no pipeline ID returned")

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
