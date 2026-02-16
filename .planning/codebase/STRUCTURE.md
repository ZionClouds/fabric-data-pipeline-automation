# Codebase Structure

**Analysis Date:** 2026-02-16

## Directory Layout

```
fabric-data-pipeline-automation/
├── backend/                          # Python FastAPI backend application
│   ├── main.py                       # FastAPI app initialization, routes, startup logic
│   ├── conversation_endpoints.py     # Conversation and job management routes
│   ├── settings.py                   # Configuration from environment variables
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                    # Docker image for backend
│   ├── services/                     # Business logic and integrations
│   │   ├── agents_sdk/               # Multi-agent system for pipeline design (primary AI logic)
│   │   │   ├── __init__.py           # Public exports and runner initialization
│   │   │   ├── runner.py             # PipelineAgentRunner orchestrates agents
│   │   │   ├── agents.py             # Agent definitions and handoff logic
│   │   │   ├── context.py            # PipelineContext state management
│   │   │   ├── tools.py              # Tool functions agents execute
│   │   │   └── guardrails.py         # Input validation and output sanitization
│   │   ├── azure_ai_agent_service.py # Azure OpenAI integration with Bing grounding
│   │   ├── fabric_api_service.py     # High-level Fabric API operations
│   │   ├── database_service.py       # SQLAlchemy database CRUD operations
│   │   ├── medallion_architect.py    # Medallion architecture design guidance
│   │   ├── proactive_suggestions.py  # Proactive recommendation service
│   │   ├── conversation_context.py   # Historical conversation context management
│   │   ├── multi_agent/              # Alternative multi-agent implementation
│   │   └── __pycache__/              # Compiled Python bytecode
│   ├── models/                       # Data models and schemas
│   │   ├── pipeline_models.py        # Pydantic request/response models for API
│   │   ├── database_models.py        # SQLAlchemy ORM models for persistence
│   │   └── __pycache__/
│   ├── fabric_sdk/                   # Microsoft Fabric SDK wrappers
│   │   ├── __init__.py               # SDK initialization
│   │   ├── clients/                  # Typed REST clients for Fabric resources
│   │   │   ├── base_client.py        # Base HTTP client with auth
│   │   │   ├── datapipeline_client.py # Pipeline deployment and management
│   │   │   ├── notebook_client.py    # Notebook CRUD operations
│   │   │   ├── lakehouse_client.py   # Lakehouse metadata and tables
│   │   │   ├── workspace_client.py   # Workspace enumeration
│   │   │   ├── connection_client.py  # Connection/linked service management
│   │   │   ├── copyjob_client.py     # Copy job operations
│   │   │   └── shortcut_client.py    # Shortcuts in lakehouse
│   │   ├── activities/               # Pipeline activity definitions
│   │   └── models/                   # Fabric resource models (auto-generated)
│   ├── templates/                    # Jinja2 templates for pipeline/notebook generation
│   │   ├── pipeline_templates/
│   │   └── notebook_templates/
│   ├── database/                     # Database initialization
│   │   └── schema.sql                # SQL schema definitions (legacy, managed by ORM)
│   ├── test/                         # Test files
│   │   ├── test_medallion_complete.py
│   │   ├── test_automated_pipeline_generation.py
│   │   ├── test_ai_storage_decision.py
│   │   └── [other test files]
│   ├── docs/                         # Documentation files
│   └── __pycache__/
├── frontend/                         # React frontend application
│   ├── src/
│   │   ├── index.js                  # React app entry point
│   │   ├── App.js                    # Root component with theme provider
│   │   ├── components/               # React components
│   │   │   ├── PipelineBuilderLayout.js  # Main layout container
│   │   │   ├── AIChat.js             # Chat interface and message handling
│   │   │   ├── ChatSessions.js       # Conversation history sidebar
│   │   │   ├── PipelinePreview.js    # Pipeline JSON/notebook visualization
│   │   │   ├── PipelineList.js       # Historical pipelines listing
│   │   │   ├── WorkspaceSelector.js  # Workspace/lakehouse selection
│   │   │   ├── LakehouseWarehouseSelector.js # Resource selector
│   │   │   ├── PermanentHeader.js    # App header/toolbar
│   │   │   ├── NotebookViewer.js     # Notebook preview renderer
│   │   │   └── Login.js              # Microsoft Entra ID login
│   │   ├── contexts/                 # React context providers
│   │   │   ├── AuthContext.js        # Authentication state (token, user info)
│   │   │   └── PipelineContext.js    # Pipeline state (workspace, lakehouse)
│   │   ├── services/                 # API client and utilities
│   │   │   └── api.js                # Axios-based HTTP client with interceptors
│   │   ├── styles/                   # CSS and styling
│   │   │   ├── App.css
│   │   │   └── [component-specific styles]
│   │   └── assets/
│   │       └── images/               # Static images
│   ├── public/                       # Static HTML and config
│   │   └── index.html
│   ├── build/                        # Production build output (auto-generated)
│   ├── package.json                  # Node dependencies
│   └── node_modules/
├── .github/
│   └── workflows/                    # CI/CD pipeline definitions
│       └── azure-deploy.yml          # Azure Container Apps deployment
├── .planning/
│   └── codebase/                     # GSD codebase analysis documents
├── skills/                           # Reference implementations and patterns
│   ├── multi-agent-patterns/
│   ├── context-degradation/
│   ├── context-compression/
│   └── memory-systems/
├── docker-compose.yml                # Local dev environment (backend + database)
├── README.md                         # Project overview
├── PROJECT_OVERVIEW.md               # Architecture and design decisions
├── AI_PIPELINE_GENERATION_DESIGN.md  # Design document for AI pipeline generation
└── [other config files]
```

## Directory Purposes

**backend/:**
- Purpose: FastAPI REST API, business logic, database, AI agent system
- Contains: Python source code, tests, documentation
- Entry point: `main.py` (Uvicorn starts this)

**backend/services/:**
- Purpose: Encapsulate external integrations and domain logic
- Contains: Service classes for Fabric API, database, AI agents, medallion architecture
- Key files: `agents_sdk/` (primary AI orchestration), `fabric_api_service.py`, `database_service.py`

**backend/services/agents_sdk/:**
- Purpose: Multi-agent orchestration system for pipeline design workflow
- Contains: Agent definitions, context management, tools, guardrails, runner
- Pattern: Agents are stage-based (Discovery → Source Analysis → Architecture → Transform → Deploy)

**backend/models/:**
- Purpose: Define data contracts and database schema
- Contains: Pydantic models (API requests/responses), SQLAlchemy ORM models (database tables)
- Key files: `pipeline_models.py` (API schemas), `database_models.py` (database persistence)

**backend/fabric_sdk/:**
- Purpose: Type-safe wrappers around Microsoft Fabric REST APIs
- Contains: HTTP clients for each Fabric resource type
- Pattern: Base client for auth/requests, individual clients for DataPipeline, Notebook, Lakehouse, etc.

**frontend/src/components/:**
- Purpose: React UI components
- Key components: AIChat (main chat interface), PipelinePreview (pipeline visualization), ChatSessions (history)
- Pattern: Functional components with hooks, Material-UI for styling

**frontend/src/contexts/:**
- Purpose: Global state management via React Context API
- Contains: AuthContext (JWT token, user), PipelineContext (workspace/lakehouse selection)
- Pattern: useAuth() and usePipeline() custom hooks for component access

**frontend/src/services/:**
- Purpose: HTTP client for backend communication
- Contains: `api.js` with axios instances and API wrapper functions
- Pattern: Interceptors for auth token injection and error handling

## Key File Locations

**Entry Points:**
- `backend/main.py`: FastAPI app creation, route handlers, startup initialization
- `frontend/src/index.js`: React app mount point
- `frontend/src/App.js`: Root component with theme and auth setup

**Configuration:**
- `backend/settings.py`: Environment-based configuration (API keys, URLs, database)
- `backend/requirements.txt`: Python dependencies
- `frontend/package.json`: Node.js dependencies
- `.env.example`: Example environment variables template

**Core Logic:**
- `backend/services/agents_sdk/runner.py`: PipelineAgentRunner orchestrates agent workflow
- `backend/services/agents_sdk/agents.py`: Individual agent definitions (Discovery, SourceAnalyst, etc.)
- `backend/services/agents_sdk/tools.py`: Tool functions agents call (update_source_info, generate_pipeline, etc.)
- `backend/services/fabric_api_service.py`: High-level Fabric API operations
- `frontend/src/components/AIChat.js`: Chat UI and message handling (59KB, largest component)

**Database:**
- `backend/services/database_service.py`: SQLAlchemy session management and CRUD operations
- `backend/models/database_models.py`: ORM models (Conversation, ConversationMessage, Job, Log)
- `backend/database/schema.sql`: Legacy schema reference (ORM is source of truth)

**Testing:**
- `backend/test/test_medallion_complete.py`: Full pipeline generation test
- `backend/test/test_automated_pipeline_generation.py`: Automation test
- `backend/test/test_proactive_agent.py`: Proactive suggestions test

## Naming Conventions

**Files:**
- `*_service.py`: Service classes that encapsulate business logic (fabric_api_service.py, database_service.py)
- `*_models.py`: Pydantic or SQLAlchemy model definitions (pipeline_models.py, database_models.py)
- `*_client.py`: HTTP client wrappers for external APIs (datapipeline_client.py, notebook_client.py)
- `*.js`: React components and utilities (PipelineBuilderLayout.js, api.js)
- Test files: `test_*.py` in backend/test/

**Directories:**
- `services/`: Business logic service classes
- `models/`: Data models and schemas
- `components/`: React UI components
- `contexts/`: React context providers
- `fabric_sdk/`: Fabric-specific SDK clients

**Functions:**
- Async endpoints: `async def endpoint_name(...)` with FastAPI decorators
- Service methods: camelCase (e.g., create_conversation, get_workspace_lakehouses)
- Tool functions: snake_case (e.g., update_source_info, design_architecture)

**Classes:**
- Service classes: PascalCase ending in "Service" (DatabaseService, FabricAPIService, AzureAIAgentService)
- React components: PascalCase (AIChat, ChatSessions, PipelinePreview)
- ORM models: PascalCase (Conversation, ConversationMessage, Job, Log)
- Pydantic models: PascalCase ending in "Request/Response" (ChatRequest, ChatResponse, PipelineGenerateRequest)

## Where to Add New Code

**New Feature (e.g., adding new pipeline activity type):**
- Primary code: `backend/fabric_sdk/activities/` (new activity model), `backend/services/agents_sdk/tools.py` (new tool function)
- Tests: `backend/test/test_new_feature.py`
- Models: Update `backend/models/pipeline_models.py` if new request/response type needed

**New Component/Module:**
- Frontend component: Create `.js` file in `frontend/src/components/`, import in parent component
- Backend service: Create `backend/services/new_service.py` with service class, expose via imports in `__init__.py`
- Database model: Add SQLAlchemy class to `backend/models/database_models.py`, service to `database_service.py`

**Utilities/Helpers:**
- Shared helpers: `backend/services/` (for Python utilities), `frontend/src/services/api.js` (for API functions)
- Constants: `backend/settings.py` (backend), environment variables

**Agent Changes:**
- New agent: Add to `backend/services/agents_sdk/agents.py`, register in AGENTS dict, add tools needed
- New tool: Add function to `backend/services/agents_sdk/tools.py`, register in agent's tools list
- Tool testing: Add test to `backend/test/` with mock PipelineContext

## Special Directories

**backend/services/multi_agent/:**
- Purpose: Alternative multi-agent implementation (experimental/reference)
- Generated: No, manually maintained
- Committed: Yes, but not actively used (agents_sdk is primary)

**backend/fabric_sdk/models/:**
- Purpose: Auto-generated or manually-created Fabric resource model classes
- Generated: Partially (from Fabric API specs)
- Committed: Yes

**backend/templates/:**
- Purpose: Jinja2 templates for generating pipeline JSON and notebook Python code
- Generated: No, manually maintained
- Committed: Yes

**frontend/build/:**
- Purpose: Production build output (React compiled to static assets)
- Generated: Yes, by `npm run build`
- Committed: No, excluded in .gitignore

**frontend/node_modules/:**
- Purpose: Node.js package dependencies
- Generated: Yes, by `npm install`
- Committed: No, excluded in .gitignore

**backend/__pycache__/:**
- Purpose: Python compiled bytecode cache
- Generated: Yes, automatically
- Committed: No, excluded in .gitignore

**.planning/codebase/:**
- Purpose: GSD codebase analysis documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Generated: Yes, by `/gsd:map-codebase` command
- Committed: Yes, for reference

**skills/**
- Purpose: Reference implementations and design patterns
- Contains: Examples of multi-agent patterns, context management, memory systems
- Generated: No, manually maintained
- Committed: Yes

---

*Structure analysis: 2026-02-16*
