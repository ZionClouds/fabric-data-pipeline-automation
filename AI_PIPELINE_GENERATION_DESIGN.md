# AI-Powered Data Pipeline Generation - Design Document

## Overview

This document captures the complete design discussion for building an AI-powered data pipeline generation system using Microsoft Fabric SDK and OpenAI.

The system allows users to describe their business requirements in natural language, and the AI will:
1. Understand the use case
2. Identify required activities
3. Gather necessary information
4. Check/create resources
5. Generate pipeline JSON
6. Deploy to Microsoft Fabric

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Implementation Status](#implementation-status)
3. [Multi-LLM Call Structure](#multi-llm-call-structure)
4. [User Interface Flow](#user-interface-flow)
5. [Question Flow](#question-flow)
6. [Source Type Handling](#source-type-handling)
7. [Transformation Handling](#transformation-handling)
8. [PII/PHI Detection & Masking](#piiphi-detection--masking)
9. [Resource Management](#resource-management)
10. [Pipeline Activities](#pipeline-activities)
11. [Generated Notebook Code](#generated-notebook-code)
12. [Configuration Schema](#configuration-schema)
13. [API Endpoints](#api-endpoints)
14. [Test Results](#test-results)
15. [File Structure](#file-structure)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    HIGH-LEVEL ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Frontend  │     │   Backend   │     │  Microsoft  │       │
│  │   (React)   │────▶│   (Python)  │────▶│   Fabric    │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│        │                   │                                     │
│        │                   │                                     │
│        ▼                   ▼                                     │
│  ┌─────────────┐     ┌─────────────┐                            │
│  │  Workspace  │     │ Azure OpenAI│                            │
│  │  Selection  │     │  (GPT-5)    │                            │
│  └─────────────┘     └─────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Flow Summary

```
User selects Workspace (Frontend)
         │
         ▼
AI Chat becomes available
         │
         ▼
User describes business requirement
         │
         ▼
┌─────────────────────────────────────┐
│  LLM Call 1: Understand Use Case    │
│  → Identify activities needed       │
│  → Detect source type (SQL/Blob)    │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM Call 2: Gather Requirements    │
│  → Ask questions based on source    │
│  → Ask about PII/PHI                │
│  → Ask about transformations        │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM Call 3: Resource Resolution    │
│  → Check existing / create new      │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM Call 4: Generate Pipeline JSON │
│  → Use activity builders            │
│  → Generate Notebook if PII enabled │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM Call 5: Validate & Deploy      │
│  → Deploy via Fabric SDK            │
└─────────────────────────────────────┘
```

---

## Implementation Status

### ✅ Completed Components

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Data Models | `models.py` | 247 | ✅ Complete |
| AI Chat Service | `chat_service.py` | 950+ | ✅ Complete |
| Notebook Generator | `notebook_generator.py` | 660+ | ✅ Complete |
| Pipeline Generator | `pipeline_generator.py` | 545+ | ✅ Complete |
| Resource Manager | `resource_manager.py` | 750+ | ✅ Complete |
| Deployment Service | `deployment_service.py` | 405+ | ✅ Complete |
| API Router | `router.py` | 415+ | ✅ Complete |
| **Total** | **8 files** | **4,000+ lines** | ✅ |

### Key Features Implemented

1. **Azure OpenAI Integration** - Uses `gpt-5-chat` deployment
2. **Multi-Source Support** - Azure SQL Database and Blob Storage
3. **Dynamic PII Detection** - Presidio-based, no hardcoded columns
4. **AI-Decided Sample Size** - Based on data volume
5. **4 Masking Types** - Redact, Partial, Fake, Hash
6. **Complete Pipeline Generation** - GetMetadata, ForEach, Copy, Notebook activities
7. **Schedule Generation** - Daily, Weekly, Monthly triggers

---

## Multi-LLM Call Structure

### LLM Call 1: Use Case Analyzer

**Purpose:** Understand user intent and identify required pipeline activities

**Input:**
```
User: "I have my data in the azure sql database and I want to transfer the data into the OneLake"
```

**Output:**
```json
{
    "use_case_type": "database_to_lakehouse",
    "description": "Transfer data from Azure SQL Database to OneLake",
    "activities": [
        {"type": "GetMetadata", "reason": "Retrieve schema or table list from Azure SQL Database", "order": 1},
        {"type": "ForEach", "reason": "Iterate through tables or datasets to be copied", "order": 2},
        {"type": "Copy", "reason": "Copy data from Azure SQL Database to OneLake", "order": 3}
    ],
    "needs_pii_detection": false,
    "needs_transformation": false,
    "needs_scheduling": true
}
```

### LLM Call 2: Requirements Gatherer

**Purpose:** Based on identified source type, determine what information to collect

**Activity Requirements Matrix:**

| Source Type | Required Information |
|-------------|---------------------|
| Azure SQL Database | Server name, Database name, Table name(s) |
| Blob Storage | Storage account, Container, Folder path, File format |
| SharePoint | Site URL, Document library, Folder path |

### LLM Call 3: Resource Resolver

**Purpose:** Check existing Fabric resources or create new ones

```python
# Query existing resources using SDK
existing_connections = await connection_client.list_connections()
existing_environments = await environment_client.list_environments()
default_lakehouse = await lakehouse_client.get_default()
```

### LLM Call 4: JSON Generator

**Purpose:** Generate pipeline JSON using activity builders from SDK

### LLM Call 5: Validator & Deployer

**Purpose:** Validate generated JSON and deploy to Fabric

---

## User Interface Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND: User selects Workspace first                         │
│  ┌─────────────────────────────────────────┐                    │
│  │  Select Workspace: [ jay-dev          ▼ ]│                    │
│  └─────────────────────────────────────────┘                    │
│                       │                                          │
│                       ▼                                          │
│  ┌─────────────────────────────────────────┐                    │
│  │  AI Chat becomes available               │                    │
│  │  "How can I help you build a pipeline?" │                    │
│  └─────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### What We Already Know (No Need to Ask)

| Info | Source |
|------|--------|
| Workspace ID | Selected in UI |
| Workspace Name | Selected in UI |
| Default Lakehouse | Query from workspace |

---

## Question Flow

### Azure SQL Database Source Flow

```
[Workspace: jay-dev - Already Selected]

User: "I have my data in the azure sql database and I want to transfer the data into the OneLake"

AI: "I understand you want to create a data pipeline:

**Use Case:** Transfer data from Azure SQL Database to OneLake

**Activities I'll use:**
   1. GetMetadata - Retrieve schema and table information
   2. ForEach - Iterate through tables or datasets
   3. Copy - Copy data to OneLake

**📦 SOURCE (Azure SQL Database)**
Please provide:
1. Server name? (e.g., myserver.database.windows.net)
2. Database name?
3. Table name(s) to transfer?"

User: "The server name is myserver.database.windows.net, database is salesdb, and I want to load the customers table"

AI: "Got the source details!

**🔒 SENSITIVE DATA**
Does this data contain PII/PHI (Personal/Health Information)?
- **Yes** - Data contains sensitive information
- **No** - No sensitive data"

User: "Yes"

AI: "How would you like to mask sensitive data?
   • **Redact**  → john@email.com → <EMAIL_ADDRESS>
   • **Partial** → john@email.com → j***@***.com
   • **Fake**    → john@email.com → user_8x7k@masked.com
   • **Hash**    → john@email.com → a1b2c3d4..."

User: "Partial"

AI: "PII detection enabled with **partial** masking.

**🔄 TRANSFORMATIONS**
Do you need any other transformations?
- Filter rows
- Select specific columns
- None"

User: "None"

AI: "**📍 DESTINATION**
Where should the data be stored?
- Table name?"

User: "customers_masked"

AI: "**⏰ SCHEDULE**
When should this pipeline run?
- Frequency and time?"

User: "Daily at 2 AM"

AI: "Here's your pipeline summary:

📦 Source: myserver.database.windows.net/salesdb/customers
🔒 PII Masking: Partial (auto-detect at runtime)
📍 Destination: customers_masked (Tables)
⏰ Schedule: Daily at 2:00 AM UTC

Pipeline: 'ExtractDataFromAzurePipeline'
├── GetMetadata
├── ForEach
│   └── Copy (SQL → Lakehouse Files)
├── Notebook (PII masking with Presidio)
└── Schedule: Daily 2:00 AM UTC

[Deploy Now] [Preview JSON] [Edit]"
```

### Blob Storage Source Flow

```
User: "I need to load sales data from blob storage daily"

AI: "**📦 SOURCE (Blob Storage)**
Please provide:
1. Storage account name?
2. Container name?
3. Folder path? (e.g., sales/2024/)
4. File format? (CSV / Parquet / JSON)"
```

---

## Source Type Handling

### Source Detection Logic

The AI automatically detects source type from user message:

| Keywords Detected | Source Type | Questions Asked |
|-------------------|-------------|-----------------|
| "sql", "database", "azure sql" | Azure SQL Database | Server, Database, Table |
| "blob", "storage", "container" | Azure Blob Storage | Account, Container, Path, Format |
| "sharepoint" | SharePoint | Site URL, Library, Folder |

### Source Configuration Mapping

```python
# Azure SQL Source → Model Mapping
source_config = SourceConfig(
    storage_account="myserver.database.windows.net",  # Server name
    container="salesdb",                               # Database name
    folder_path="customers",                           # Table name
    file_format=FileFormat.PARQUET                     # Output format
)
```

---

## Transformation Handling

### Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSFORMATION DECISION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Simple Transformations          Complex Transformations         │
│  ──────────────────────          ──────────────────────         │
│  • Filter rows                   • PII/PHI Detection (Presidio) │
│  • Select columns                • Custom Python logic           │
│  • Rename columns                • Complex joins                 │
│  • Basic aggregations            • ML transformations            │
│  • Type conversions              • External API calls            │
│           │                                │                     │
│           ▼                                ▼                     │
│      ┌─────────┐                    ┌───────────┐               │
│      │ DATAFLOW │                    │ NOTEBOOK  │               │
│      └─────────┘                    └───────────┘               │
│                                           │                      │
│                                           ▼                      │
│                                    ┌─────────────┐              │
│                                    │ ENVIRONMENT │              │
│                                    │ (Presidio)  │              │
│                                    └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## PII/PHI Detection & Masking

### Simplified Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      SIMPLIFIED PII/PHI FLOW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  AI Chat: "Does your data contain PII/PHI?"                      │
│                                                                  │
│  User: "No"  ──────────────────► No masking, proceed             │
│                                                                  │
│  User: "Yes" ──────────────────► AI asks masking type            │
│         │                                                        │
│         ▼                                                        │
│  AI Chat: "How would you like to mask?"                          │
│         │   1. Redact                                            │
│         │   2. Partial                                           │
│         │   3. Fake                                              │
│         │   4. Hash                                              │
│         │                                                        │
│         ▼                                                        │
│  User: "Partial"                                                 │
│         │                                                        │
│         ▼                                                        │
│  AT RUNTIME:                                                     │
│  ┌─────────────────────────────────────────┐                    │
│  │ 1. AI decides sample size               │                    │
│  │ 2. Presidio scans & detects columns     │                    │
│  │ 3. Apply "Partial" mask to ALL detected │                    │
│  │    columns automatically                │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Masking Types

| Type | Example | Use Case |
|------|---------|----------|
| **Redact** | `john@email.com` → `<EMAIL_ADDRESS>` | When you need to know data type but not value |
| **Partial** | `john@email.com` → `j***@***.com` | When partial visibility is needed |
| **Fake** | `john@email.com` → `user_8x7k@masked.com` | When realistic-looking data is needed |
| **Hash** | `john@email.com` → `a1b2c3d4e5f6...` | When data needs to be joinable but hidden |

### AI-Decided Sample Size

```python
def get_sample_size(total_rows: int) -> int:
    """AI logic to decide sample size based on data volume"""
    if total_rows < 100:
        return total_rows  # Scan all
    elif total_rows < 1000:
        return 10
    elif total_rows < 10000:
        return 50
    elif total_rows < 100000:
        return 100
    else:
        return 200
```

### Presidio - Auto-Detected Entities

No hardcoding needed - Presidio automatically detects:

| Category | Entities |
|----------|----------|
| **PII** | EMAIL_ADDRESS, PHONE_NUMBER, PERSON, LOCATION, ADDRESS |
| **Financial** | CREDIT_CARD, IBAN_CODE, US_BANK_NUMBER |
| **Government IDs** | US_SSN, US_PASSPORT, US_DRIVER_LICENSE |
| **Medical (PHI)** | MEDICAL_LICENSE, NPI |
| **Other** | IP_ADDRESS, URL, DATE_TIME |

### Environment Setup for Presidio

```
┌─────────────────────────────────────────────────────────────────┐
│                 ENVIRONMENT CREATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  When PII/PHI detection is needed:                               │
│                                                                  │
│  1. Create Environment (if not exists)                           │
│     └── Name: "PresidioEnvironment"                             │
│                                                                  │
│  2. Install Libraries                                            │
│     └── presidio-analyzer (2.2.0)                               │
│     └── presidio-anonymizer (2.2.0)                             │
│     └── spacy (3.7.0)                                           │
│                                                                  │
│  3. Attach Environment to Notebook                               │
│     └── notebook.environment_id = env_id                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Resource Management

### Lakehouse Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAKEHOUSE DECISION                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Every Workspace has a DEFAULT Lakehouse                         │
│                                                                  │
│  User mentions lakehouse?                                        │
│      │                                                           │
│      ├── NO ──────────────────► Use Default Lakehouse            │
│      │                                                           │
│      └── YES                                                     │
│          │                                                       │
│          ├── "use default" ──────────► Use Default Lakehouse     │
│          │                                                       │
│          ├── "use [name]" ───────────► Check if exists           │
│          │                                 ├── YES → Use it      │
│          │                                 └── NO  → Error/Ask   │
│          │                                                       │
│          └── "create new [name]" ────► Create new lakehouse      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Connection Handling

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONNECTION HANDLING                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  After user provides source details:                             │
│                                                                  │
│  Check: Does connection exist for this source?                   │
│      │                                                           │
│      ├── YES → Use existing connection_id silently               │
│      │                                                           │
│      └── NO  → Create new connection via SDK                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Activities

### Available Activities (from SDK)

| Category | Activities |
|----------|------------|
| **Data Movement** | CopyActivity, InvokeCopyJobActivity |
| **Control Flow** | ForEachActivity, IfConditionActivity, SwitchActivity, UntilActivity, WaitActivity, FailActivity |
| **Variables** | SetVariableActivity, AppendVariableActivity, FilterActivity |
| **Data Operations** | GetMetadataActivity, LookupActivity, ScriptActivity |
| **Fabric Specific** | NotebookActivity (TridentNotebook), RefreshDataflowActivity |
| **External** | WebActivity, ExecutePipelineActivity, Office365EmailActivity |

### Generated Pipeline Structure (with PII)

```json
{
  "name": "AzureSQL_to_OneLake_Pipeline",
  "properties": {
    "activities": [
      {
        "name": "GetFileList",
        "type": "GetMetadata",
        "dependsOn": [],
        "typeProperties": {
          "dataset": { "referenceName": "SourceDataset" },
          "fieldList": ["childItems"]
        }
      },
      {
        "name": "ForEachFile",
        "type": "ForEach",
        "dependsOn": [{"activity": "GetFileList", "dependencyConditions": ["Succeeded"]}],
        "typeProperties": {
          "items": "@activity('GetFileList').output.childItems",
          "activities": [
            {
              "name": "CopyData",
              "type": "Copy",
              "typeProperties": {
                "source": {"type": "BinarySource"},
                "sink": {"type": "LakehouseTableSink"}
              }
            }
          ]
        }
      },
      {
        "name": "ProcessData",
        "type": "TridentNotebook",
        "dependsOn": [{"activity": "ForEachFile", "dependencyConditions": ["Succeeded"]}],
        "typeProperties": {
          "notebookId": "@pipeline().parameters.notebookId",
          "workspaceId": "@pipeline().parameters.workspaceId",
          "parameters": {
            "source_path": {"value": "Files/raw/data/", "type": "string"},
            "output_table": {"value": "customers_masked", "type": "string"}
          }
        }
      }
    ],
    "parameters": {
      "workspaceId": {"type": "string"},
      "lakehouseId": {"type": "string"},
      "notebookId": {"type": "string"}
    },
    "annotations": ["auto-generated", "ai-pipeline-service", "pii-detection"]
  }
}
```

---

## Generated Notebook Code

### Notebook Cells (9 cells for PII-enabled pipeline)

| Cell | Purpose |
|------|---------|
| 1 | Setup and Imports (Presidio, PySpark) |
| 2 | Configuration (source path, masking type, output table) |
| 3 | Read Data from source |
| 4 | AI-Decided Sample Size function |
| 5 | Detect Sensitive Columns using Presidio |
| 6 | Masking Functions (redact, partial, fake, hash) |
| 7 | Apply Masking to detected columns |
| 8 | Write to Lakehouse Table |
| 9 | Execution Summary |

### Sample Code - PII Detection Cell

```python
# Cell 5: Detect Sensitive Columns Using Presidio
def detect_sensitive_columns(df, sample_size):
    """Scan sample rows and detect which columns contain PII/PHI"""
    sensitive_columns = []
    sample_df = df.limit(sample_size).toPandas()

    for column in sample_df.columns:
        for value in sample_df[column].dropna().astype(str):
            if not value.strip():
                continue

            results = analyzer.analyze(text=value, language='en')

            if results:
                sensitive_columns.append({
                    "column": column,
                    "entity_type": results[0].entity_type,
                    "confidence": results[0].score
                })
                break  # Found PII in this column, move to next

    return sensitive_columns

# Execute detection
sensitive_columns_info = detect_sensitive_columns(df, sample_size)
sensitive_column_names = [c["column"] for c in sensitive_columns_info]
print(f"Sensitive columns detected: {sensitive_columns_info}")
```

---

## Configuration Schema

### Complete Pipeline Config (Generated from AI Chat)

```python
from services.ai_pipeline import PipelineConfig, SourceConfig, PIIConfig, DestinationConfig, ScheduleConfig

config = PipelineConfig(
    # Workspace context
    workspace_id="jay-dev-workspace-id",
    workspace_name="jay-dev",

    # Pipeline metadata
    pipeline_name="AzureSQL_to_OneLake_Pipeline",
    pipeline_description="Transfer data from Azure SQL Database to OneLake with PII masking",

    # Source configuration
    source=SourceConfig(
        storage_account="myserver.database.windows.net",
        container="salesdb",
        folder_path="customers",
        file_format=FileFormat.PARQUET
    ),

    # PII configuration
    pii=PIIConfig(
        enabled=True,
        masking_type=MaskingType.PARTIAL
    ),

    # Destination
    destination=DestinationConfig(
        target=DestinationType.TABLES,
        table_name="customers_masked",
        write_mode="overwrite"
    ),

    # Schedule
    schedule=ScheduleConfig(
        enabled=True,
        frequency="daily",
        time="02:00",
        timezone="UTC"
    )
)
```

---

## API Endpoints

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai-pipeline/chat` | Process chat message |
| POST | `/ai-pipeline/chat/reset` | Reset chat session |
| GET | `/ai-pipeline/chat/context/{session_id}` | Get session context |

### Deployment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai-pipeline/deploy` | Deploy pipeline with config |
| POST | `/ai-pipeline/deploy/from-session/{session_id}` | Deploy from chat session |

### Preview Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai-pipeline/preview/pipeline` | Preview pipeline JSON |
| POST | `/ai-pipeline/preview/notebook` | Preview notebook code |
| POST | `/ai-pipeline/preview/schedule` | Preview schedule config |
| GET | `/ai-pipeline/preview/session/{session_id}` | Preview all from session |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai-pipeline/validate` | Validate configuration |
| GET | `/ai-pipeline/masking-types` | Get masking type options |
| GET | `/ai-pipeline/file-formats` | Get supported file formats |
| GET | `/ai-pipeline/schedule-frequencies` | Get schedule frequencies |
| GET | `/ai-pipeline/health` | Health check |

---

## Test Results

### Test Suite Summary (All Passed ✅)

**Use Case:** Azure SQL Database → OneLake Transfer
**Workspace:** jay-dev

#### TEST 1: Initial Chat Response ✅

The AI correctly:
- Identified use case as "Azure SQL to OneLake data transfer"
- Proposed activities: GetMetadata → ForEach → Copy
- Asked SQL-specific questions (server, database, table)

```
[AI RESPONSE]:
State: gathering_source
Message: I understand you want to create a data pipeline:

**Use Case:** Extract data from Azure SQL Database and load it into OneLake (Lakehouse)

**Activities I'll use:**
   1. GetMetadata - Retrieve schema and table information
   2. ForEach - Iterate through tables or datasets
   3. Copy - Copy data to OneLake

**📦 SOURCE (Azure SQL Database)**
Please provide:
1. Server name? (e.g., myserver.database.windows.net)
2. Database name?
3. Table name(s) to transfer?
```

#### TEST 2: Chat Flow Extraction ✅

Successfully extracted from user message:
- Server: `myserver.database.windows.net`
- Database: `salesdb`
- Table: `customers`

#### TEST 3: Notebook Generator ✅

Generated notebook with **9 cells**:
- Setup and Imports
- Configuration
- Read Data (Parquet format)
- AI-Decided Sample Size
- Presidio PII Detection
- Masking Functions
- Apply Masking
- Write to Lakehouse Table
- Execution Summary

#### TEST 4: Pipeline Generator ✅

Generated valid Fabric pipeline JSON with:
- 3 activities: GetMetadata → ForEach → Notebook
- PII detection annotation
- Daily schedule at 2 AM UTC

#### TEST 5: Preview Endpoints ✅

All preview endpoints working:
- Pipeline: Valid with 3 activities
- Notebook: 9 cells with PII detection
- Schedule: Daily trigger

#### TEST 6: API Response Format ✅

API endpoint response includes:
- `session_id`
- `message`
- `state`
- `config`
- `options`
- `is_complete`

---

## File Structure

```
backend/services/ai_pipeline/
├── __init__.py          # Package exports and documentation
├── models.py            # Pydantic models (247 lines)
│   ├── FileFormat, MaskingType, DestinationType (enums)
│   ├── SourceConfig, PIIConfig, TransformationConfig
│   ├── DestinationConfig, ScheduleConfig
│   ├── PipelineConfig (complete configuration)
│   ├── ConversationContext, ConversationMessage
│   ├── ChatRequest, ChatResponse
│   └── DeployRequest, DeployResponse
│
├── chat_service.py      # AI Chat Service (950+ lines)
│   ├── Azure OpenAI integration
│   ├── Multi-turn conversation handling
│   ├── State machine (INITIAL → GATHERING_SOURCE → GATHERING_PII → ...)
│   ├── Use case analysis (LLM)
│   ├── Source info extraction (LLM + fallback)
│   └── SQL vs Blob source handling
│
├── notebook_generator.py # Notebook Generator (660+ lines)
│   ├── Cell generators for each step
│   ├── Presidio integration code
│   ├── AI sample size logic
│   ├── 4 masking function implementations
│   └── Jupyter notebook structure builder
│
├── pipeline_generator.py # Pipeline Generator (545+ lines)
│   ├── Activity creators (GetMetadata, ForEach, Copy, Notebook)
│   ├── Pipeline structure builder
│   ├── Schedule/trigger generation
│   └── Pipeline validation
│
├── resource_manager.py   # Resource Manager (750+ lines)
│   ├── Connection management (check/create)
│   ├── Environment management (Presidio setup)
│   ├── Lakehouse management (default resolution)
│   ├── Notebook creation
│   ├── Pipeline deployment
│   └── Schedule creation
│
├── deployment_service.py # Deployment Service (405+ lines)
│   ├── Full deployment orchestration
│   ├── Resource setup coordination
│   ├── Notebook generation and upload
│   ├── Pipeline validation and deployment
│   └── Preview methods
│
└── router.py            # FastAPI Router (415+ lines)
    ├── Chat endpoints (/chat, /chat/reset, /chat/context)
    ├── Deploy endpoints (/deploy, /deploy/from-session)
    ├── Preview endpoints (/preview/pipeline, /preview/notebook)
    ├── Validation endpoint (/validate)
    └── Utility endpoints (/masking-types, /file-formats, /health)
```

---

## Decision Summary

| Decision | Who Decides | When |
|----------|-------------|------|
| Workspace | User | UI selection (before chat) |
| Lakehouse | System | Auto-use default (unless user asks for new) |
| Source Type | AI | Detected from user message |
| Has PII/PHI? | User | AI chat question |
| Masking type | User | AI chat question (4 options) |
| Sample size | AI | At runtime (based on data volume) |
| Which columns have PII | Presidio | At runtime (auto-detect) |
| Connection | System | Check existing, create if needed |
| Activities to use | AI | Based on use case analysis |

---

## SDK Components Used

### Models (Converted from Go SDK)
- 43 Python model files
- 10,889 lines of code
- All 41 Fabric services covered

### Clients
- `FabricBaseClient` - OAuth2 authentication
- `DataPipelineClient` - Pipeline CRUD operations
- `LakehouseClient` - Lakehouse operations
- `NotebookClient` - Notebook operations
- `ConnectionClient` - Connection management
- `WorkspaceClient` - Workspace operations
- `EnvironmentClient` - Environment management

### Activity Builders
- `CopyActivity`
- `ForEachActivity`
- `GetMetadataActivity`
- `NotebookActivity`
- `IfConditionActivity`
- `SetVariableActivity`
- `PipelineBuilder`

---

## Usage Example

```python
from services.ai_pipeline import AIChatService, DeploymentService

# Create chat session
chat = AIChatService(
    session_id="session-001",
    workspace_id="jay-dev-workspace-id",
    workspace_name="jay-dev"
)

# Process messages
response = await chat.process_message(
    "I have my data in the azure sql database and I want to transfer the data into the OneLake"
)

# Continue conversation...
response = await chat.process_message(
    "Server is myserver.database.windows.net, database is salesdb, table is customers"
)

# When complete, deploy
deployment = DeploymentService(access_token="...")
result = await deployment.deploy(chat.context.config)
print(result.fabric_url)  # Link to view in Fabric portal
```

---

*Document Version: 2.0*
*Last Updated: December 2024*
*Implementation Status: Complete*
