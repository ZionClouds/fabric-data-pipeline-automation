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
2. [Multi-LLM Call Structure](#multi-llm-call-structure)
3. [User Interface Flow](#user-interface-flow)
4. [Question Flow](#question-flow)
5. [Transformation Handling](#transformation-handling)
6. [PII/PHI Detection & Masking](#piiphi-detection--masking)
7. [Resource Management](#resource-management)
8. [Pipeline Activities](#pipeline-activities)
9. [Generated Notebook Code](#generated-notebook-code)
10. [Configuration Schema](#configuration-schema)
11. [Next Steps](#next-steps)

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
│  │  Workspace  │     │   OpenAI    │                            │
│  │  Selection  │     │   (LLM)     │                            │
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
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM Call 2: Gather Requirements    │
│  → Ask questions based on activities│
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
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  LLM Call 5: Validate & Deploy      │
│  → Deploy via Fabric SDK            │
└─────────────────────────────────────┘
```

---

## Multi-LLM Call Structure

### LLM Call 1: Use Case Analyzer

**Purpose:** Understand user intent and identify required pipeline activities

**Input:**
```
User: "I need to load sales data from blob storage daily"
```

**Output:**
```json
{
    "use_case": "blob_to_lakehouse_ingestion",
    "activities": [
        {"type": "GetMetadata", "reason": "List files in source"},
        {"type": "ForEach", "reason": "Handle multiple files"},
        {"type": "Copy", "reason": "Move data to lakehouse"}
    ],
    "needs_transformation": false,
    "needs_scheduling": true
}
```

### LLM Call 2: Requirements Gatherer

**Purpose:** Based on identified activities, determine what information to collect

**Activity Requirements Matrix:**

| Activity | Required Information |
|----------|---------------------|
| GetMetadata (Blob) | Storage account, Container, Folder path |
| ForEach | No extra info (uses GetMetadata output) |
| Copy (Blob→Lakehouse) | Connection ID, Workspace ID, Lakehouse ID, Target |
| Notebook | Environment ID (if PII detection needed) |

### LLM Call 3: Resource Resolver

**Purpose:** Check existing Fabric resources or create new ones

```python
# Query existing resources using SDK
existing_connections = await connection_client.list_connections()
existing_workspaces = await workspace_client.list_workspaces()
existing_lakehouses = await workspace_client.list_lakehouses(workspace_id)
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
│  │  Select Workspace: [ Sales-Analytics ▼ ]│                    │
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

### Complete AI Chat Question Flow

```
[Workspace: Sales-Analytics - Already Selected]

User: "I need to load sales data from blob storage daily"

AI: "I'll create this pipeline. A few questions:

📦 SOURCE
1. Storage account name?
2. Container name?
3. Folder path?
4. File format? (CSV / Parquet / JSON)

🔒 SENSITIVE DATA
5. Does this data contain PII/PHI? (Yes / No)

   [If Yes]
   6. How would you like to mask sensitive data?
      • Redact   → john@email.com → <EMAIL_ADDRESS>
      • Partial  → john@email.com → j***@***.com
      • Fake     → john@email.com → user_8x7k@masked.com
      • Hash     → john@email.com → a1b2c3d4...

🔄 TRANSFORMATIONS
7. Any transformations needed? (describe or none)

📍 DESTINATION
8. Load to: Files or Tables?
9. Table name? (if Tables)

⏰ SCHEDULE
10. Time & Timezone?"
```

### Questions Summary

| Category | Questions | Count |
|----------|-----------|-------|
| Source | Storage, Container, Folder, Format | 4 |
| PII/PHI | Has sensitive data?, Masking type | 2 |
| Transformations | What transformations? | 1 |
| Destination | Files/Tables, Table name | 2 |
| Schedule | Time, Timezone | 2 |
| **Total** | | **~11** |

### What AI Figures Out (Not Asked)

| Info | How AI Gets It |
|------|----------------|
| Workspace ID | Already selected in UI |
| Lakehouse ID | Get default lakehouse from workspace |
| Connection ID | Check existing or create new |
| Activities to use | Determined from use case analysis |
| Sample size for PII scan | AI decides based on data volume |
| Which columns have PII | Presidio detects at runtime |

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

### When to Use What

| Transformation Type | Tool | Example |
|---------------------|------|---------|
| Simple filters | Dataflow | `WHERE status = 'active'` |
| Column selection | Dataflow | `SELECT id, name, amount` |
| PII/PHI masking | Notebook + Presidio | Mask emails, phones, SSN |
| Complex Python logic | Notebook | Custom business rules |

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

```
┌─────────────────────────────────────────┐
│ Total Rows      │ Sample Size           │
├─────────────────────────────────────────┤
│ < 100           │ All rows              │
│ 100 - 1,000     │ 10 rows               │
│ 1,000 - 10,000  │ 50 rows               │
│ 10,000 - 100K   │ 100 rows              │
│ > 100K          │ 200 rows              │
└─────────────────────────────────────────┘
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
│     └── Name: "presidio-env" or "{workspace}-pii-env"           │
│                                                                  │
│  2. Install Libraries                                            │
│     └── presidio-analyzer                                        │
│     └── presidio-anonymizer                                      │
│     └── spacy                                                    │
│     └── en_core_web_lg (spacy model)                            │
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
│  After user provides storage account name:                       │
│                                                                  │
│  Check: Does connection exist for this storage?                  │
│      │                                                           │
│      ├── YES → Use existing connection_id silently               │
│      │                                                           │
│      └── NO  → Ask user for credentials                          │
│               │                                                  │
│               ▼                                                  │
│          "No connection found. Please provide:                   │
│           • Account Key, OR                                      │
│           • Service Principal credentials, OR                    │
│           • Use Managed Identity"                                │
│                                                                  │
│          Then create connection via SDK                          │
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
| **Fabric Specific** | NotebookActivity, RefreshDataflowActivity |
| **External** | WebActivity, ExecutePipelineActivity, Office365EmailActivity |

### Example Pipeline Structure

```
User: "I need to load sales data from blob storage daily"
       + Has PII (email, phone)
       + Transform: filter active customers only

Pipeline:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  1. GetMetadata ──► List files in blob                          │
│          │                                                       │
│          ▼                                                       │
│  2. ForEach ──► Iterate each file                               │
│          │                                                       │
│          ▼                                                       │
│  3. Copy ──► Blob to Lakehouse/Files (raw)                      │
│          │                                                       │
│          ▼                                                       │
│  4. Notebook ──► (with presidio-env attached)                   │
│          │       ├── Read raw data                              │
│          │       ├── Scan first N rows (AI decides N)           │
│          │       ├── Detect sensitive columns (Presidio)        │
│          │       ├── Apply user-selected masking                │
│          │       ├── Apply business transformations             │
│          │       └── Write to lakehouse table                   │
│          │                                                       │
│          ▼                                                       │
│  5. Done                                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Generated Notebook Code

### Complete Notebook (Auto-Generated)

```python
# Cell 1: Setup Presidio
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType
import hashlib

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Cell 2: Configuration (Generated from user input)
CONFIG = {
    "source_path": "Files/raw/sales/",
    "output_table": "fact_sales",
    "masking_type": "partial"  # Options: redact, partial, fake, hash
}

# Cell 3: Read Data
df = spark.read.format("delta").load(CONFIG["source_path"])

# Cell 4: AI-Decided Sample Size
def get_sample_size(total_rows):
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

total_rows = df.count()
sample_size = get_sample_size(total_rows)
print(f"Total rows: {total_rows}, Sample size for PII detection: {sample_size}")

# Cell 5: Detect Sensitive Columns Using Presidio
def detect_sensitive_columns(df, sample_size):
    """Scan sample rows and detect which columns contain PII/PHI"""
    sensitive_columns = []
    sample_df = df.limit(sample_size).toPandas()

    for column in sample_df.columns:
        for value in sample_df[column].dropna():
            if value is None or str(value).strip() == "":
                continue

            results = analyzer.analyze(text=str(value), language='en')

            if results:
                sensitive_columns.append({
                    "column": column,
                    "entity_type": results[0].entity_type
                })
                break

    return sensitive_columns

sensitive_columns_info = detect_sensitive_columns(df, sample_size)
sensitive_column_names = [c["column"] for c in sensitive_columns_info]
print(f"Sensitive columns detected: {sensitive_columns_info}")

# Cell 6: Masking Functions Based on User Choice
def create_masking_function(masking_type):
    """Create masking function based on user's choice"""

    def redact_mask(text):
        """Replace with entity labels: john@email.com → <EMAIL_ADDRESS>"""
        if text is None or str(text).strip() == "":
            return text
        results = analyzer.analyze(text=str(text), language='en')
        if results:
            anonymized = anonymizer.anonymize(text=str(text), analyzer_results=results)
            return anonymized.text
        return text

    def partial_mask(text):
        """Partial masking: john@email.com → j***@***.com"""
        if text is None or str(text).strip() == "":
            return text
        results = analyzer.analyze(text=str(text), language='en')
        if results:
            operators = {
                "DEFAULT": OperatorConfig(
                    "mask",
                    {"chars_to_mask": 6, "masking_char": "*", "from_end": False}
                )
            }
            anonymized = anonymizer.anonymize(
                text=str(text),
                analyzer_results=results,
                operators=operators
            )
            return anonymized.text
        return text

    def fake_mask(text):
        """Replace with fake data: john@email.com → user_8x7k@masked.com"""
        if text is None or str(text).strip() == "":
            return text
        results = analyzer.analyze(text=str(text), language='en')
        if results:
            entity_type = results[0].entity_type
            fake_values = {
                "EMAIL_ADDRESS": f"user_{hashlib.md5(str(text).encode()).hexdigest()[:6]}@masked.com",
                "PHONE_NUMBER": "555-000-0000",
                "US_SSN": "000-00-0000",
                "PERSON": "REDACTED_NAME",
                "CREDIT_CARD": "0000-0000-0000-0000"
            }
            return fake_values.get(entity_type, "<MASKED>")
        return text

    def hash_mask(text):
        """One-way hash: john@email.com → a1b2c3d4e5f6..."""
        if text is None or str(text).strip() == "":
            return text
        results = analyzer.analyze(text=str(text), language='en')
        if results:
            return hashlib.sha256(str(text).encode()).hexdigest()[:16]
        return text

    # Return function based on user's choice
    mask_functions = {
        "redact": redact_mask,
        "partial": partial_mask,
        "fake": fake_mask,
        "hash": hash_mask
    }
    return mask_functions.get(masking_type, redact_mask)

# Cell 7: Apply Masking
mask_function = create_masking_function(CONFIG["masking_type"])
mask_udf = udf(mask_function, StringType())

df_masked = df
for column_name in sensitive_column_names:
    print(f"Masking column: {column_name} using {CONFIG['masking_type']} method")
    df_masked = df_masked.withColumn(column_name, mask_udf(col(column_name)))

# Cell 8: Apply Business Transformations (Generated based on user input)
# Example: df_transformed = df_masked.filter(df_masked.status == 'active')
df_transformed = df_masked

# Cell 9: Write to Lakehouse Table
df_transformed.write.format("delta").mode("overwrite").saveAsTable(CONFIG["output_table"])
print(f"Data written to: {CONFIG['output_table']}")
```

---

## Configuration Schema

### Complete Pipeline Config (Generated from AI Chat)

```python
PIPELINE_CONFIG = {
    # Source
    "source": {
        "storage_account": "contososales",
        "container": "raw-data",
        "folder_path": "sales/2024/",
        "file_format": "csv"
    },

    # PII/PHI
    "pii_detection": {
        "enabled": True,           # User said "Yes"
        "masking_type": "partial"  # User chose "Partial"
    },

    # Transformations
    "transformations": [
        {"type": "filter", "condition": "status = 'active'"}
    ],

    # Destination (Lakehouse = default, not asked)
    "destination": {
        "target": "Tables",
        "table_name": "fact_sales"
    },

    # Schedule
    "schedule": {
        "frequency": "daily",
        "time": "02:00",
        "timezone": "UTC"
    }
}
```

---

## Decision Summary

| Decision | Who Decides | When |
|----------|-------------|------|
| Workspace | User | UI selection (before chat) |
| Lakehouse | System | Auto-use default (unless user asks for new) |
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

### Activity Builders
- `CopyActivity`
- `ForEachActivity`
- `GetMetadataActivity`
- `NotebookActivity`
- `IfConditionActivity`
- `SetVariableActivity`
- `PipelineBuilder`

---

## Next Steps

### To Implement

1. **AI Chat Service**
   - OpenAI integration
   - Multi-turn conversation handling
   - Question flow logic

2. **Notebook Generator**
   - Template-based code generation
   - Dynamic configuration injection
   - Presidio environment setup

3. **Pipeline Generator**
   - Use activity builders
   - Generate complete pipeline JSON
   - Handle dependencies between activities

4. **Resource Manager**
   - Connection check/create logic
   - Environment check/create logic
   - Lakehouse default resolution

5. **Deployment Service**
   - Pipeline deployment via SDK
   - Schedule configuration
   - Error handling

### Open Questions

1. **LLM Choice**: OpenAI (GPT-4) or Azure OpenAI?

2. **Environment Strategy**: One shared `presidio-env` per workspace, or check-and-create-if-needed?

3. **Error Handling**: What happens if pipeline generation fails?

4. **Versioning**: Should we version generated pipelines?

---

## Appendix: Example Conversation

```
[Workspace: Sales-Analytics - Selected in UI]

User: "I need to load sales data from blob storage daily"

AI: "I'll help you create a data ingestion pipeline. Let me ask a few questions:

📦 SOURCE
1. Storage account name?"

User: "contososales"

AI: "2. Container name?"

User: "raw-data"

AI: "3. Folder path?"

User: "sales/2024/"

AI: "4. File format? (CSV / Parquet / JSON)"

User: "CSV"

AI: "🔒 SENSITIVE DATA
5. Does this data contain PII/PHI? (Yes / No)"

User: "Yes"

AI: "6. How would you like to mask sensitive data?
   • Redact   → john@email.com → <EMAIL_ADDRESS>
   • Partial  → john@email.com → j***@***.com
   • Fake     → john@email.com → user_8x7k@masked.com
   • Hash     → john@email.com → a1b2c3d4..."

User: "Partial"

AI: "🔄 TRANSFORMATIONS
7. Any transformations needed? (describe or none)"

User: "Filter only active customers"

AI: "📍 DESTINATION
8. Load to: Files or Tables?"

User: "Tables"

AI: "9. Table name?"

User: "fact_sales"

AI: "⏰ SCHEDULE
10. What time should it run daily and timezone?"

User: "2 AM UTC"

AI: "Perfect! Here's your pipeline summary:

📦 Source: contososales/raw-data/sales/2024/*.csv
🔒 PII Masking: Partial (auto-detect columns at runtime)
🔄 Transform: Filter active customers
📍 Destination: fact_sales (Tables)
⏰ Schedule: Daily at 2:00 AM UTC

Pipeline: 'DailySalesIngestion'
├── GetMetadata (list CSV files)
├── ForEach (iterate files)
│   └── Copy (blob → lakehouse files)
├── Notebook (PII masking + transformations)
└── Schedule: Daily 2:00 AM UTC

[Deploy Now] [Preview JSON] [Edit]"

User: "Deploy Now"

AI: "✅ Pipeline 'DailySalesIngestion' deployed successfully!

View in Fabric: [link]
First run scheduled: Tomorrow 2:00 AM UTC"
```

---

*Document Version: 1.0*
*Last Updated: December 2024*
