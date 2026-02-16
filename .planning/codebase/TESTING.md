# Testing Patterns

**Analysis Date:** 2026-02-16

## Test Framework

**Runner:**
- No automated test runner configured (pytest, unittest, or React Testing Library not configured)
- Manual test scripts in `backend/test/` directory run directly with Python

**Assertion Library:**
- Python: Standard assertions using `assert` statements and exception catching
- JavaScript: Not detected (no test infrastructure in frontend)

**Run Commands:**
```bash
# Backend tests are manual scripts that execute directly
python backend/test/test_medallion_complete.py
python backend/test/test_bing_grounding.py
python backend/test/test_automated_pipeline_generation.py

# Frontend
npm test                # React Scripts test mode (configured but not implemented)
npm start              # Development server with hot reload
npm build              # Production build
```

## Test File Organization

**Location:**
- Dedicated separate directory: `backend/test/` (not co-located with source)
- Test files are manual integration/E2E scripts, not unit tests
- No test files in frontend directory

**Naming:**
- Convention: `test_{feature}.py`
  - `test_medallion_complete.py` - Tests medallion architecture endpoint
  - `test_bing_grounding.py` - Tests Bing Grounding integration
  - `test_automated_pipeline_generation.py` - Tests pipeline generation
  - `test_medallion_scenario.py` - Tests medallion scenarios
  - `test_sharepoint_medallion.py` - Tests SharePoint medallion
  - `test_proactive_agent.py` - Tests proactive agent suggestions
  - `test_ai_storage_decision.py` - Tests AI storage decisions

**Structure:**
```
backend/test/
├── test_medallion_complete.py      # Integration test
├── test_bing_grounding.py          # Service test
├── test_automated_pipeline_generation.py
├── test_medallion_scenario.py
├── test_sharepoint_medallion.py
├── test_proactive_agent.py
└── test_ai_storage_decision.py
```

## Test Structure

**Suite Organization:**
Manual test scripts with async functions and print-based output

```python
# From test_medallion_complete.py
import asyncio
import logging
import json
from services.azure_ai_agent_service import AzureAIAgentService
from services.medallion_architect import medallion_service
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_medallion():
    """Test complete medallion architecture support"""

    print("\n" + "="*80)
    print("🏗️  COMPLETE MEDALLION ARCHITECTURE TEST")
    print("="*80 + "\n")

    # Initialize agent
    agent_service = AzureAIAgentService(
        project_endpoint=config.AZURE_AI_PROJECT_ENDPOINT,
        api_key=config.AZURE_OPENAI_API_KEY,
        bing_connection_id=config.BING_GROUNDING_CONNECTION_ID,
        model_deployment="gpt-4o-mini-bing"
    )

    # Test METHOD 1: Natural Chat
    print("┌" + "─"*78 + "┐")
    print("│ METHOD 1: Natural Chat Conversation                                       │")
    print("└" + "─"*78 + "┘\n")

    chat_response = await agent_service.chat(
        messages=[{
            "role": "user",
            "content": chat_query
        }]
    )
```

**Patterns:**
- Setup: Direct service instantiation with config parameters
- Execution: Async function with real service calls (no mocking)
- Verification: Print statements with formatted output (emoji decoration for readability)
- Teardown: Not explicitly handled (no cleanup code)

## Mocking

**Framework:**
- No mocking framework detected (no unittest.mock, pytest-mock, or jest setup)
- All test scripts use real service instances and make actual API calls

**Patterns:**
- Integration tests call actual services: `AzureAIAgentService`, `medallion_service`
- Configuration loaded from `config` module (environment variables)
- No test doubles or stubs

**What to Mock (if framework were used):**
- External API calls (Azure AI Agents, Fabric API)
- Database operations (use in-memory SQLite for tests)
- File system operations

**What NOT to Mock:**
- Business logic and service methods (should be tested end-to-end)
- Data transformations
- Response parsing

## Fixtures and Factories

**Test Data:**
- Hardcoded test payloads in test files

From `test_automated_pipeline_generation.py`:
```python
test_payload_medallion = {
    "workspace_id": "c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb",
    "pipeline_name": "test_medallion_pipeline",
    "architecture": "medallion",
    "source_connection": {
        "connection_name": "test_sharepoint_connection",
        "connection_type": "sharepoint",
        "auth_type": "ServicePrincipal",
        "properties": {
            "site_url": "https://test.sharepoint.com/sites/testsite",
            "list_name": "TestList",
            "client_id": "test-client-id",
            "client_secret": "test-secret",
            "tenant_id": "test-tenant-id"
        }
    },
    "bronze_connection": {...},
    "silver_connection": {...},
    "gold_lakehouse_id": "test-lakehouse-id",
    "gold_table_name": "gold_data",
    "layers": [
        {
            "layer_name": "bronze",
            "storage_type": "blob",
            "transformations": [],
            "component_type": "copy_activity"
        },
        ...
    ],
    "schedule": "manual",
    "created_by": "test@example.com"
}
```

**Location:**
- Test data defined at top of test files, not in separate fixtures directory
- Models use Pydantic classes for validation (e.g., `AutomatedPipelineGenerateRequest`)

## Coverage

**Requirements:**
- No coverage requirements enforced (no `.coverage`, `coverage.ini`, or `pytest.ini` files)
- No coverage reporting tool configured

**View Coverage:**
- Not applicable (no coverage framework in place)

## Test Types

**Unit Tests:**
- Not found in codebase
- Business logic tested through integration tests

**Integration Tests:**
- Primary test type: Manual integration tests calling real services
- Examples: `test_medallion_complete.py`, `test_bing_grounding.py`
- Approach: Async functions with real API calls and service instantiation
- Test scenarios: Multi-step workflows (e.g., agent conversation → medallion planning → pipeline templates)

**E2E Tests:**
- Framework: None (no Cypress, Selenium, or Playwright)
- Manual E2E testing through UI interactions
- Frontend: No automated E2E tests detected

## Common Patterns

**Async Testing:**
```python
# From test_medallion_complete.py and test_bing_grounding.py
import asyncio

async def test_function_name():
    """Test async operations"""

    # Create service
    agent_service = AzureAIAgentService(...)

    # Call async methods
    response = await agent_service.chat(
        messages=[{"role": "user", "content": query}]
    )

    # Print results
    print(f"Response: {response.get('content', '')}")

# Run with asyncio
if __name__ == "__main__":
    asyncio.run(test_function_name())
```

**Error Testing:**
```python
# From test_bing_grounding.py
try:
    agent_service = AzureAIAgentService(
        project_endpoint=config.AZURE_AI_PROJECT_ENDPOINT,
        api_key=config.AZURE_OPENAI_API_KEY,
        bing_connection_id=config.BING_GROUNDING_CONNECTION_ID,
        model_deployment="gpt-4o-mini-bing"
    )
    print("✅ Agent service initialized successfully!\n")

except Exception as e:
    print(f"❌ Failed to initialize agent service: {str(e)}")
    return
```

## Test Configuration

**Test Runner Config:**
- Not found: No `pytest.ini`, `setup.cfg`, or `tox.ini`
- Backend tests run standalone: `python backend/test/{test_file}.py`
- Frontend: Create React App default test runner (not configured)

**Database for Tests:**
- In-memory SQLite or temporary files (inferred from `get_session()` context manager pattern)
- No test database configuration detected

**Environment Setup:**
- Tests load configuration from `config` module (imports environment variables)
- Database connection: `DATABASE_URL` from environment
- API endpoints: Hardcoded or from `settings` module

## Test Execution

**Running Tests Manually:**
```bash
# Backend integration tests
cd backend
python test/test_medallion_complete.py
python test/test_bing_grounding.py
python test/test_automated_pipeline_generation.py

# Frontend (no tests implemented)
cd frontend
npm test  # Launches Jest/React Scripts test mode (no tests found)
```

**Expected Output:**
- Formatted console output with emoji indicators
- Status messages (✅ success, ❌ failure)
- Test results printed to stdout
- No structured test reports

## Gaps and Concerns

**Missing:**
- Unit tests for business logic
- Automated test runner (pytest, Jest)
- Test isolation and cleanup
- Test data factories
- Mocking framework
- Frontend component tests
- CI/CD test integration (no GitHub Actions test step)
- Code coverage measurement
- Performance/load tests
- Database schema migration tests

**Current State:**
- Manual integration tests only (developer runs scripts manually)
- No regression prevention mechanism
- Tests are exploratory and documentation-focused rather than validation-focused
- High maintenance burden: Tests call real external services (Azure AI, Fabric API)

---

*Testing analysis: 2026-02-16*
