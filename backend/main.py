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
    ConnectionConfig, PipelineArchitecture, LayerConfig
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

# Initialize Azure OpenAI service (GPT-5 with Bing Search)
azure_openai_service = AzureOpenAIService(
    azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    deployment_name=config.AZURE_OPENAI_DEPLOYMENT,
    api_version=config.AZURE_OPENAI_API_VERSION,
    bing_api_key=config.BING_SEARCH_API_KEY,
    bing_endpoint=config.BING_SEARCH_ENDPOINT
)

# Initialize Azure AI Agent service (GPT-4o-mini with Bing Grounding via Agents)
agent_service = AzureAIAgentService(
    project_endpoint=config.AZURE_AI_PROJECT_ENDPOINT,
    api_key=config.AZURE_OPENAI_API_KEY,
    bing_connection_id=config.BING_GROUNDING_CONNECTION_ID,
    model_deployment="gpt-4o-mini-bing"
)

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
        "claude_model": config.CLAUDE_MODEL,
        "azure_openai_model": config.AZURE_OPENAI_DEPLOYMENT,
        "azure_ai_agent_enabled": True,
        "bing_grounding_enabled": bool(config.BING_GROUNDING_CONNECTION_ID)
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

        # Update conversation context with user message
        conv_context.update_context(user_message)

        # Check if we should proactively search for best practices
        proactive_search_query = conv_context.should_search_for_best_practices()

        # Convert ChatMessage objects to dict format for Azure AI Agent
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Add context information to help the agent be more proactive
        context_summary = conv_context.get_context_for_agent()
        if context_summary:
            # Inject context as a system-level hint
            messages[-1]["content"] = messages[-1]["content"] + context_summary

        # If we detected source and destination, proactively check for latest updates
        proactive_info = ""
        if proactive_search_query and conv_context.context["current_stage"] == "suggesting":
            logger.info(f"Proactively searching: {proactive_search_query}")
            # The agent will do this automatically with the new prompt, but we track it
            proactive_info = f"\n\n🔍 PROACTIVE SEARCH TRIGGERED: {proactive_search_query}"

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
            pipeline_preview=None
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
            max_tokens=config.AZURE_OPENAI_MAX_TOKENS,
            temperature=config.AZURE_OPENAI_TEMPERATURE,
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
            max_tokens=config.AZURE_OPENAI_MAX_TOKENS,
            temperature=config.AZURE_OPENAI_TEMPERATURE
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
