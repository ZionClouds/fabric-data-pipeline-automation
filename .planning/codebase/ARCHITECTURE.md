# Architecture

**Analysis Date:** 2026-02-16

## Pattern Overview

**Overall:** Multi-Agent AI System with FastAPI Backend and React Frontend

**Key Characteristics:**
- OpenAI Agents SDK orchestration layer managing specialized agent collaboration
- FastAPI REST API providing stateless request handling with JWT authentication
- Client-server architecture with SQLite/database persistence for conversations and jobs
- Multi-agent workflow stages: Discovery → Source Analysis → Architecture Design → Transformation → Deployment
- Fabric SDK client wrapper layer abstracting Microsoft Fabric REST API interactions

## Layers

**Frontend (React):**
- Purpose: Provide interactive UI for pipeline design, conversation history, and deployment management
- Location: `frontend/src/`
- Contains: React components, Material-UI theming, authentication context, API client service
- Depends on: Backend FastAPI service for chat, workspace management, and pipeline deployment
- Used by: End users interacting with the pipeline builder

**API Gateway & Request Handling (FastAPI):**
- Purpose: Process HTTP requests, validate JWT tokens, route to appropriate services, manage conversations
- Location: `backend/main.py`, `backend/conversation_endpoints.py`
- Contains: Route handlers (@app.post, @app.get decorators), request validation, CORS middleware
- Depends on: Azure AD JWT validation, database service, AI agent service, fabric API service
- Used by: Frontend application making REST calls

**Multi-Agent Orchestration (Agents SDK):**
- Purpose: Coordinate specialized AI agents to guide users through pipeline design workflow
- Location: `backend/services/agents_sdk/`
- Contains: Agent definitions, context management, tool implementations, guardrails, runner
- Depends on: OpenAI API, Azure OpenAI deployment (gpt-4o-mini or gpt-4o), Fabric API service
- Used by: API endpoints that need intelligent pipeline design assistance

**Business Logic Services:**
- Purpose: Implement domain-specific operations like Fabric API interactions, medallion architecture, proactive suggestions
- Location: `backend/services/`
- Contains: `fabric_api_service.py`, `azure_ai_agent_service.py`, `medallion_architect.py`, `proactive_suggestions.py`
- Depends on: HTTP clients (httpx), Azure SDK, Fabric workspace credentials
- Used by: Agent tools, API endpoints

**Database Persistence:**
- Purpose: Store conversations, messages, jobs, logs, and execution history
- Location: `backend/services/database_service.py`, `backend/models/database_models.py`
- Contains: SQLAlchemy ORM models, session management, CRUD operations
- Depends on: SQLAlchemy, SQLite database file
- Used by: API endpoints, logging system

**Data Models:**
- Purpose: Define request/response contracts and internal data structures
- Location: `backend/models/pipeline_models.py`, `backend/models/database_models.py`
- Contains: Pydantic BaseModel request/response schemas, database ORM models, enums
- Depends on: Pydantic, SQLAlchemy
- Used by: All API endpoints, services, database operations

**Fabric SDK Clients:**
- Purpose: Encapsulate Microsoft Fabric REST API calls with typed client interfaces
- Location: `backend/fabric_sdk/clients/`
- Contains: `datapipeline_client.py`, `notebook_client.py`, `lakehouse_client.py`, workspace/connection clients
- Depends on: httpx, Azure authentication tokens
- Used by: Fabric API service, agent tools for actual pipeline deployment

## Data Flow

**Chat/Conversation Flow:**

1. Frontend sends ChatRequest to `/api/ai/chat` with user message
2. JWT token validated via Azure AD JWKS endpoint
3. Conversation created/retrieved from database
4. Message saved to database
5. Message routed to agent runner based on pipeline context stage
6. Agent runner evaluates message and selects appropriate agent
7. Selected agent executes tools (update_source_info, analyze_source_requirements, etc.)
8. Tools update pipeline context stored in PipelineContext manager
9. Agent response generated and returned to API endpoint
10. Response cleaned (PIPELINE_CONFIG extracted if present)
11. Response saved to conversation in database
12. ChatResponse returned to frontend with message and metadata

**Pipeline Generation Flow:**

1. Frontend sends PipelineGenerateRequest to `/api/pipelines/generate`
2. Request validated and user authenticated
3. Agent runner executes with pipeline context from conversation
4. Multi-agent workflow executes through stages:
   - Discovery agent gathers requirements
   - Source analyst analyzes source system details
   - Fabric architect designs architecture
   - Transform expert specifies transformations
   - Deploy agent prepares for deployment
5. Agents use tools to build pipeline definition step by step
6. Final pipeline definition returned and stored in database
7. PipelineGenerateResponse sent to frontend with pipeline preview
8. Frontend displays notebook/pipeline preview to user

**Pipeline Deployment Flow:**

1. Frontend sends deployment request to `/api/pipelines/deploy`
2. API retrieves pipeline definition from database
3. Fabric SDK clients instantiate with workspace credentials
4. Pipeline deployed to Fabric workspace through REST API
5. Deployment status tracked in database Job record
6. Frontend polls `/api/jobs/{job_id}` for deployment status
7. Completion/failure logged to database Log table

**State Management:**

- PipelineContext (in-memory): Maintains current pipeline design state during conversation
- Database: Persists conversations, messages, jobs, logs for historical access
- Frontend Context: AuthContext (JWT token, user info), PipelineContext (selected workspace/lakehouse)

## Key Abstractions

**PipelineContext:**
- Purpose: Encapsulates all information gathered during pipeline design conversation
- Examples: `backend/services/agents_sdk/context.py`
- Pattern: Dataclass-based state manager with stage progression (INITIAL → DISCOVERY → SOURCE_ANALYSIS → ARCHITECTURE → TRANSFORMATION → DEPLOYMENT → COMPLETE)
- Contains: SourceInfo, BusinessContext, TransformationNeeds, DestinationConfig, OperationalConfig, ArchitectureDesign

**Agent:**
- Purpose: Specialized AI worker focused on one stage of pipeline design
- Examples: `discovery_agent`, `source_analyst_agent`, `fabric_architect_agent` in `backend/services/agents_sdk/agents.py`
- Pattern: OpenAI Agents SDK Agent[PipelineContext] with instructions, tools, and handoff logic
- Agents hand off to each other: Discovery → Source Analyst → Fabric Architect → Transform Expert → Deploy Agent

**Tools:**
- Purpose: Functions agents can call to update state, analyze requirements, or generate outputs
- Examples: `update_source_info()`, `design_architecture()`, `generate_pipeline()`, `deploy_to_fabric()`
- Pattern: Functions decorated for agent use, accepting PipelineContext and returning structured results
- Location: `backend/services/agents_sdk/tools.py`

**Fabric Service Clients:**
- Purpose: Type-safe wrappers around Fabric REST APIs
- Examples: `DataPipelineClient`, `NotebookClient`, `LakehouseClient`
- Pattern: Base client with authentication, individual clients for each resource type
- Location: `backend/fabric_sdk/clients/`

**Conversation & Job Models:**
- Purpose: Represent persistent entities in database
- Pattern: SQLAlchemy ORM models with relationships (Conversation has many Messages, has many Jobs)
- Location: `backend/models/database_models.py`

## Entry Points

**Frontend Application:**
- Location: `frontend/src/index.js`
- Triggers: Browser loads React app
- Responsibilities: Mount App component, initialize Material-UI theme, set up AuthProvider and PipelineProvider

**FastAPI Application:**
- Location: `backend/main.py`
- Triggers: Uvicorn server startup (Python process starts)
- Responsibilities: Create FastAPI instance, configure CORS, include routers, initialize database, initialize agent SDK

**Startup Event Handler:**
- Location: `backend/main.py` @app.on_event("startup")
- Triggers: When FastAPI app starts
- Responsibilities: Initialize SQLite database, create tables, initialize OpenAI Agents SDK runner with fabric_service

**Chat Endpoint:**
- Location: `backend/main.py` POST `/api/ai/chat`
- Triggers: Frontend sends user message
- Responsibilities: Validate JWT, get/create conversation, save message, execute agent runner, return response

**Workspace & Pipeline Endpoints:**
- Location: `backend/main.py` and `backend/conversation_endpoints.py`
- Triggers: Frontend requests workspaces, lakehouses, conversations, jobs
- Responsibilities: Query database or Fabric API, return filtered/formatted responses

## Error Handling

**Strategy:** Try-catch blocks with logging at each layer, specific HTTPException for API responses

**Patterns:**

- **Database Operations:** try-except with rollback in context manager (`database_service.py`)
- **JWT Validation:** HTTPException(401) if token invalid or missing
- **Fabric API Calls:** HTTPException with error details from underlying HTTP response
- **Agent Execution:** Guardrails validation before/after agent runs; exceptions logged but not always exposed to user
- **Logging:** DatabaseService.log_info/log_warning/log_error writes to Log table for audit trail

Example from `main.py` line 66-83:
```python
try:
    # Extract pipeline config
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
```

## Cross-Cutting Concerns

**Logging:**
- Framework: Python logging module + custom database logging
- Approach: All major operations logged to console via logger, important events also written to Log table via db_service.log_info/warning/error
- Locations: `main.py` line 43-45, `database_service.py` log_info/log_warning/log_error methods

**Validation:**
- Input: Pydantic models validate request bodies automatically (ChatRequest, PipelineGenerateRequest, etc.)
- Agent Output: Guardrails in `backend/services/agents_sdk/guardrails.py` sanitize agent outputs before returning
- Database: Foreign key constraints and NOT NULL columns enforce data integrity

**Authentication:**
- Strategy: JWT token validation via Azure AD JWKS endpoint
- Implementation: HTTPBearer security scheme in FastAPI, validate_token dependency in protected endpoints
- Token Storage: Frontend stores token in localStorage, sends in Authorization header on all requests

**Authorization:**
- Approach: Workspace isolation - conversations/jobs scoped to authenticated user and workspace_id
- Pattern: API checks user_id from token matches conversation owner before returning data

---

*Architecture analysis: 2026-02-16*
