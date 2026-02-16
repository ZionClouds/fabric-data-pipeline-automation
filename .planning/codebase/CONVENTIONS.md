# Coding Conventions

**Analysis Date:** 2026-02-16

## Naming Patterns

**Files:**
- Python modules: `lowercase_with_underscores.py` (e.g., `database_service.py`, `pipeline_models.py`)
- React/JavaScript components: `PascalCase.js` (e.g., `AIChat.js`, `PipelineBuilderLayout.js`)
- Services: `{domain}_service.py` (e.g., `azure_ai_agent_service.py`, `fabric_api_service.py`)
- Test files: `test_{feature}.py` (e.g., `test_medallion_complete.py`, `test_bing_grounding.py`)

**Functions:**
- Python: `lowercase_with_underscores()` for all functions and methods
  - Example: `create_conversation()`, `get_conversations_by_user()`, `_handle_response()`
  - Private methods use leading underscore: `_get_or_create_agent()`, `_get_headers()`
- JavaScript/React: `camelCase()` for functions and methods
  - Example: `handleResponse()`, `scrollToBottom()`, `validateToken()`

**Variables:**
- Python: `lowercase_with_underscores` for all variables
  - Example: `workspace_id`, `pipeline_config`, `lakehouse_name`
  - Database fields: `conversation_id`, `user_email`, `created_at`
- JavaScript/React: `camelCase` for all variables and object keys
  - Example: `selectedWorkspace`, `chatMessages`, `inputMessage`, `isLoading`

**Types and Classes:**
- Python: `PascalCase` for all classes (Pydantic models, SQLAlchemy models, Enums)
  - Models: `ChatMessage`, `PipelineGenerateRequest`, `PipelineConfigResponse`
  - Enums: `SourceType`, `PipelineStatus`, `ExecutionStatus`, `MedallionLayer`
- Python Enums: Values use `UPPERCASE_WITH_UNDERSCORES`
  - Example: `SourceType.AZURE_SQL`, `PipelineStatus.DRAFT`, `MedallionLayer.BRONZE`

**Constants:**
- Python: `UPPERCASE_WITH_UNDERSCORES` for environment variables and global constants
  - Example: `DATABASE_URL`, `ALLOWED_ORIGINS`, `AZURE_OPENAI_API_KEY`

**Database:**
- Column names: `snake_case` (e.g., `conversation_id`, `user_email`, `created_at`, `workspace_id`)
- Table names (SQLAlchemy): `PascalCase` classes mapping to snake_case in conversions
  - Example: `Conversation` class (table: `conversation`), `ConversationMessage` class

## Code Style

**Formatting:**
- No explicit linter/formatter configuration detected (no `.eslintrc`, `.prettierrc`, or `pyproject.toml` found)
- Python code uses consistent 4-space indentation
- JavaScript/React code uses consistent 2-space indentation
- Line length: No enforced limit detected, but files stay under 3000 lines

**Linting:**
- No automated linting configuration in place
- Code follows PEP 8 conventions for Python (inferred from style)
- React/ES6 conventions followed for JavaScript

## Import Organization

**Python:**
1. Standard library imports (`logging`, `json`, `asyncio`, `os`)
2. Third-party imports (`fastapi`, `pydantic`, `sqlalchemy`, `httpx`, `azure-*`)
3. Local module imports (relative: `from models.database_models import`, `from services.database_service import`)
4. Constants and config imports (`import settings`)

Example from `main.py`:
```python
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import httpx
import jwt

import settings
from services.azure_ai_agent_service import AzureAIAgentService
from models.pipeline_models import ChatMessage, ChatRequest
```

**JavaScript/React:**
1. React and external library imports
2. Material-UI component imports (grouped with sub-imports)
3. Icon imports
4. Local service and component imports
5. Style imports (last)

Example from `AIChat.js`:
```javascript
import React, { useState, useRef, useEffect } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import { useAuth } from '../contexts/AuthContext';
import { pipelineApi } from '../services/api';
import ReactMarkdown from 'react-markdown';
import { Box, Typography, TextField, ... } from '@mui/material';
import { Send as SendIcon, SmartToy as SmartToyIcon, ... } from '@mui/icons-material';
```

**Path Aliases:**
- Python: Relative imports from project root (e.g., `from models.pipeline_models import`)
- JavaScript: Relative path imports with `../` traversal (e.g., `from '../contexts/AuthContext'`)

## Error Handling

**Python Patterns:**
- Generic `Exception` raised with descriptive messages
  - Example: `raise Exception(f"HTTP {response.status_code}: {response.text}")`
  - Example: `raise Exception("No messages provided")`
  - Example: `raise Exception(f"Azure AI Agent service error: {str(e)}")`
- Specific exception handling for known errors:
  - `HTTPStatusError`, `RequestError` from httpx
  - `json.JSONDecodeError` for JSON parsing
  - Context manager pattern for database sessions (auto-rollback on exception)
- Try-except blocks wrap critical operations with logging on error
  - Example from `database_service.py`: `try: ... except Exception as e: session.rollback(); raise e`

**JavaScript/React Patterns:**
- Promise rejection handling in interceptors
  - Example: `(error) => { return Promise.reject(error); }`
- Conditional error checking (401 Unauthorized logging without auto-logout)
  - Example from `api.js`: Check `error.response?.status === 401` and log appropriately
- No try-catch blocks visible in React components; async operations handled via `.catch()`

**HTTP/API Error Handling:**
- HTTP errors logged with full context (status code, URL, response text)
- Success codes defined explicitly: `success_codes = [200, 201, 202]`
- Fallback for empty/null responses: Return empty dict `{}`

## Logging

**Framework:** `logging` module (Python standard library)

**Patterns:**
- Loggers created per module: `logger = logging.getLogger(__name__)`
- Logging levels: `INFO` (startup, general), `ERROR` (failures), `DEBUG` (request details)
- Setup at module start:
  ```python
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)
  ```
- Log format includes timestamps, module name, level, and message (from tests):
  ```
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  ```
- Informational messages during startup: `logger.info("[OK] Database initialized successfully")`
- Error context logged with traceback: `logger.error(f"Error message: {e}")`

**JavaScript/React:**
- `console.log()` for general logging
- `console.warn()` for warnings (e.g., API 401 errors)
- No structured logging framework detected

## Comments

**When to Comment:**
- Docstrings required for all classes and public methods
- Inline comments for complex logic or non-obvious implementation details
- Comment sections with headers for major logical blocks (e.g., `# ==================== Conversation Operations ====================`)

**JSDoc/TSDoc:**
- Python uses docstring triple-quotes for functions and classes
  - Example:
    ```python
    def create_conversation(
        self,
        title: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation"""
    ```
  - More detailed docstrings in `FabricBaseClient`:
    ```python
    async def get_access_token(self) -> str:
        """
        Get OAuth2 access token for Fabric API.
        Token is fetched fresh each time to avoid expiration issues.

        Returns:
            Access token string
        """
    ```
- Method docstrings include Args and Returns sections for complex methods
- Module-level docstrings describe purpose and key details

## Function Design

**Size:**
- Small, focused functions are preferred
- Service classes have methods under 50 lines (exceptions: `main.py` chat handling reaches 100+ lines due to complexity)
- Private helper methods start with underscore: `_handle_response()`, `_get_headers()`

**Parameters:**
- Positional parameters for required arguments
- Optional parameters use `Optional[Type] = None` or `= default_value`
- Type hints required for all parameters (example: `user_id: Optional[str] = None`)
- Dataclass/model objects for complex parameter passing (e.g., `ChatRequest`, `PipelineGenerateRequest`)

**Return Values:**
- Explicit return types in function signatures (e.g., `-> Optional[Dict[str, Any]]`)
- Return Pydantic models for structured data (e.g., `-> ChatResponse`)
- Return dictionaries for flexibility in service layers
- Return None for optional results

## Module Design

**Exports:**
- Python modules export classes and functions at module level (no explicit `__all__`)
- Services export main class + module-level singleton getter (e.g., `get_db_service()`)
- Models file `__init__.py` imports and re-exports key classes for easier importing

**Barrel Files:**
- `backend/models/__init__.py` imports and exports all model classes
  - Example: `from models.pipeline_models import ChatMessage, ChatRequest, ...`
  - Example: `from models.database_models import Conversation, Job, ...`
- `backend/fabric_sdk/clients/__init__.py` imports all client classes for unified imports
- `backend/services/agents_sdk/__init__.py` imports all agent SDK components for public API

**Organization Pattern:**
- Services directory groups domain-specific functionality: `azure_ai_agent_service.py`, `fabric_api_service.py`, `database_service.py`
- Models directory separates API models (`pipeline_models.py`) from database models (`database_models.py`)
- Fabric SDK organized with `clients/` (API clients) and `models/` (service definitions) subdirectories

## API and Endpoint Patterns

**FastAPI Endpoints:**
- Route decorators use kebab-case for URL paths
  - Example: `/api/pipelines/generate-automated`, `/api/sources/validate`, `/api/auth/validate-token`
- Request bodies use Pydantic models (inherited from `BaseModel`)
- Response types explicitly defined using Pydantic models
- Error responses use `HTTPException(status_code=..., detail=...)`

**Frontend API:**
- Axios instance creation with base URL and headers
- API method pattern: `methodName: (params) => api.get/post/put/delete(...)`
  - Example: `validateToken: (token) => api.post('/api/auth/validate-token', { token })`
  - Example: `getWorkspaces: () => api.get('/api/workspaces')`

---

*Convention analysis: 2026-02-16*
