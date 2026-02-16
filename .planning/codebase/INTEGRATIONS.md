# External Integrations

**Analysis Date:** 2026-02-16

## APIs & External Services

**AI & Generative Models:**
- Anthropic Claude API - LLM inference for pipeline design
  - SDK: `anthropic` 0.7.8
  - Auth: `ANTHROPIC_API_KEY` environment variable
  - Model: `claude-sonnet-4-20250514`
  - Max tokens: 8000
  - Implementation: `backend/main.py` uses Claude for conversation routing

- Azure OpenAI (GPT-5) - Primary LLM through Azure
  - SDK: `openai` >=1.12.0
  - Auth: `AZURE_OPENAI_API_KEY`
  - Endpoint: `AZURE_OPENAI_ENDPOINT`
  - Deployment: `gpt-5-chat`
  - API version: `2024-12-01-preview`
  - Max tokens: 16384
  - Temperature: 1.0
  - Implementation: `backend/services/agents_sdk/runner.py` uses AzureOpenAI client

**Azure AI Agents with Bing Grounding:**
- Azure AI Projects SDK - Agent orchestration with Bing search grounding
  - SDK: `azure-ai-projects` >=1.0.0
  - Service: Azure AI Foundry Project
  - Auth: Service Principal (ClientSecretCredential)
  - Endpoint: `AZURE_AI_PROJECT_ENDPOINT`
  - Bing connection: `BING_GROUNDING_CONNECTION_ID`
  - Model deployment: `gpt-4o-mini-bing`
  - Implementation: `backend/services/azure_ai_agent_service.py`
  - Uses: For agents that need real-time Bing search in responses

**OpenAI Agents SDK:**
- Multi-agent orchestration framework
  - SDK: `openai-agents` >=0.0.3
  - Implementation: `backend/services/agents_sdk/` module
  - Files: `agents.py`, `runner.py`, `tools.py`, `guardrails.py`, `context.py`
  - Purpose: Specialized agent definitions and agent-to-agent handoff patterns

**Bing Search (Legacy - Deprecated):**
- Bing Web Search API - Fallback for grounding (not preferred)
  - SDK: Direct HTTP calls via `httpx`
  - Auth: `BING_SEARCH_API_KEY`
  - Endpoint: `https://api.bing.microsoft.com/v7.0/search`
  - Note: Azure AI Agents with Bing Grounding is the modern replacement

**Microsoft Fabric API:**
- Workspace, Lakehouse, Pipeline management
  - SDK: Direct HTTP calls via `httpx` (async)
  - Auth: OAuth 2.0 with Service Principal
  - Client credentials: `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET`, `FABRIC_TENANT_ID`
  - Token endpoint: Azure AD
  - Implementation: `backend/services/fabric_api_service.py`
  - Key operations:
    - List workspaces: `/api/v1/workspaces`
    - Get lakehouse shortcuts: `/api/v1/workspaces/{workspaceId}/lakehouses/{lakehouseId}/shortcuts`
    - Get SQL endpoint: `/api/v1/workspaces/{workspaceId}/lakehouses/{lakehouseId}/sqlEndpoints`
    - Create notebooks: `/api/v1/workspaces/{workspaceId}/notebooks`
    - Create pipelines: `/api/v1/workspaces/{workspaceId}/pipelines`
    - Deploy pipelines: Run notebook in background for notebook-based deployment

## Data Storage

**Databases:**
- Microsoft Azure SQL Server (primary relational database)
  - Provider: Azure SQL Database
  - Connection: `mssql+pyodbc://` via SQLAlchemy
  - Client: PyODBC 5.0.1, SQLAlchemy ORM
  - Tables: Conversations, ConversationMessages, Jobs, Logs
  - Models: `backend/models/database_models.py`

**File Storage:**
- Azure Storage Account (ADLS Gen2 - Hierarchical Namespace)
  - Account: `claimsadlsgen2`
  - SDK: `azure-storage-blob` 12.19.0
  - Containers: `bronze`, `silver` (medallion architecture)
  - Auth: Storage account key `STORAGE_ACCOUNT_KEY`
  - Connection string: `STORAGE_CONNECTION_STRING`
  - Protocol: HTTPS
  - Endpoint suffix: `core.windows.net`
  - Purpose: Data lake storage for pipeline input/output

**Caching:**
- None detected - in-memory storage used for session state
  - In-memory dict: `generated_pipelines = {}` in `backend/main.py`
  - Should use database or Redis for production

## Authentication & Identity

**Backend Service Authentication:**
- Azure Service Principal (ClientSecretCredential)
  - For: Fabric API, Azure AI Projects
  - Credentials: `FABRIC_CLIENT_ID`, `FABRIC_TENANT_ID`, `FABRIC_CLIENT_SECRET`
  - Implementation: `backend/services/azure_ai_agent_service.py` uses ClientSecretCredential
  - Scopes: Microsoft Fabric, Azure AI services

**Frontend User Authentication:**
- Azure AD / Microsoft Entra ID via MSAL
  - SDK: `@azure/msal-browser` 2.38.3, `@azure/msal-react` 1.5.8
  - Implementation: `frontend/src/contexts/AuthContext.js`
  - Token storage: `localStorage` with key `msal_token`
  - Auth type: OAuth 2.0 with MSAL
  - Interceptor: Tokens added to all API requests
  - Graceful handling: 401 errors don't auto-logout (must be manual)

**API Token Validation:**
- JWT token validation via `python-jose`
  - Implementation: `backend/main.py` validates bearer tokens
  - Endpoint: POST `/api/auth/validate-token`
  - Fallback: `DISABLE_AUTH=True` in development

**Password Management (if applicable):**
- `passlib[bcrypt]` 1.7.4 for secure hashing
- Not currently used in active auth flow but available for future user password management

## Monitoring & Observability

**Error Tracking:**
- None detected - no external error tracking service configured
- Local logging via Python `logging` module
- Log level: `logging.INFO`

**Logs:**
- Local file/console logging
- Logger: `logging.getLogger(__name__)` in services
- Log output: Standard Python logging to console
- No centralized logging service (ELK, Application Insights, etc.)

**Tracing:**
- OpenAI Agents SDK tracing available
  - Module: `backend/services/agents_sdk/runner.py`
  - Uses: `agents.tracing.TracingProcessor`, `agents.tracing.Span`, `agents.tracing.Trace`
  - For: Internal agent execution tracing (not external service)

## CI/CD & Deployment

**Hosting:**
- Azure Container Apps (target deployment)
  - Frontend URL pattern: `https://fabric-pipeline-backend.[subdomain].azurecontainerapps.io`
  - Backend URL pattern: Similar container apps endpoint

**CI Pipeline:**
- GitHub Actions workflows (defined in `.github/workflows/`)
  - File: `.github/workflows/azure-deploy.yml`
  - Purpose: Automated container build and Azure deployment

**Container Registry:**
- Docker images built locally
- Deployment: Build and push scripts provided
  - Scripts: `1-build-and-push.sh`, `2-deploy-to-azure.sh`, `3-rebuild-frontend.sh`

**Local Development:**
- Docker Compose for local orchestration
  - File: `docker-compose.yml`
  - Services: backend (port 8080), frontend (port 3000)
  - Health checks: HTTP endpoints for both services

## Environment Configuration

**Required Environment Variables:**

*Database:*
- `DATABASE_SERVER` - SQL Server FQDN
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - SQL login
- `DATABASE_PASSWORD` - SQL password

*AI/ML:*
- `ANTHROPIC_API_KEY` - Claude API key
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI service endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT` - GPT model deployment name
- `AZURE_AI_PROJECT_ENDPOINT` - Azure AI Foundry project URL
- `BING_GROUNDING_CONNECTION_ID` - Connection ID for Bing Grounding
- `BING_SEARCH_API_KEY` - Legacy Bing Search key (optional)

*Fabric Integration:*
- `FABRIC_CLIENT_ID` - Azure AD app registration ID
- `FABRIC_TENANT_ID` - Azure AD tenant ID
- `FABRIC_CLIENT_SECRET` - Service principal secret

*Storage:*
- `STORAGE_ACCOUNT_NAME` - Azure Storage account name
- `STORAGE_ACCOUNT_KEY` - Storage account key

*Frontend:*
- `REACT_APP_API_URL` - Backend API URL (default: `http://localhost:8080`)
- `REACT_APP_WORKSPACE_API_URL` - Workspace backend URL

*Development:*
- `DISABLE_AUTH` - Set to `true` for development (skip auth validation)

**Secrets Location:**
- Development: `backend/settings.py` (hardcoded - INSECURE)
- Production: Should load from Azure Key Vault or environment
- Docker Compose: Loads from `.env` file
- `.env` file is in `.gitignore` for security

## Webhooks & Callbacks

**Incoming Webhooks:**
- None detected

**Outgoing Webhooks:**
- None detected
- Fabric API calls are request-response based, not webhook-driven

**Async Background Jobs:**
- Fabric pipeline deployment runs asynchronously
- Job tracking: Stored in database `Job` table
- Status tracking: `pipeline_deployment_status` queried periodically from frontend
- No external job queue service (Celery, RabbitMQ, etc.) - uses background processes

## Integration Patterns

**Request/Response Pattern:**
- All external API calls use `httpx` (async) or `requests` (sync)
- Timeouts: 30-60 seconds configured for Fabric API calls
- Error handling: HTTPStatusError and RequestError caught in service layers

**Authentication Flow:**
1. User authenticates via Azure AD (MSAL in frontend)
2. Token stored in localStorage
3. Token included in all API requests via interceptor
4. Backend validates token with FastAPI HTTPBearer security
5. Backend service principal handles backend-to-backend auth (Fabric, Azure AI)

**Data Flow:**
1. Frontend → Backend API (REST)
2. Backend AI agents (Anthropic Claude, Azure OpenAI)
3. Backend → Fabric API (for pipeline deployment)
4. Backend → Azure Storage (for data pipeline operations)
5. Backend → SQL Database (for conversation/job persistence)

---

*Integration audit: 2026-02-16*
