# Microsoft Fabric PII/PHI Detection Pipeline - Complete Deployment Guide

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Components Deployed](#components-deployed)
- [Configuration](#configuration)
- [Deployment Process](#deployment-process)
- [API Reference](#api-reference)
- [Connection Management](#connection-management)
- [Notebook Format](#notebook-format)
- [Pipeline Structure](#pipeline-structure)
- [Troubleshooting](#troubleshooting)
- [Usage Guide](#usage-guide)

---

## Overview

This solution deploys an automated **PII/PHI detection pipeline** in Microsoft Fabric that:

1. **Monitors** a Lakehouse folder for new claim files
2. **Filters** already-processed files by querying a Warehouse table
3. **Processes** only new files through a Notebook
4. **Detects** PII/PHI data in claims using Presidio
5. **Matches** claims against prior authorization data
6. **Logs** results to a Warehouse table for auditing

### Key Features
- ✅ Automated file filtering (no duplicate processing)
- ✅ PII/PHI detection with Microsoft Presidio
- ✅ Claims-to-prior-auth matching
- ✅ Warehouse-based logging and tracking
- ✅ Lakehouse for data storage
- ✅ Fully automated via Data Pipeline

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Microsoft Fabric Workspace                   │
│                          (jay-dev)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │   Lakehouse      │         │   Warehouse      │             │
│  │ jay_dev_lakehouse│         │ jay-dev-warehouse│             │
│  ├──────────────────┤         ├──────────────────┤             │
│  │ Files/           │         │ processedfiles   │             │
│  │  ├─ claims/      │◄───────►│  - filename      │             │
│  │  └─ priorauths/  │         │  - status        │             │
│  │ Tables/          │         │  - timestamp     │             │
│  │  └─ results      │         └──────────────────┘             │
│  └──────────────────┘                  ▲                        │
│         ▲                               │                        │
│         │                               │                        │
│  ┌──────┴───────────────────────────────┴──────┐               │
│  │         Data Pipeline                        │               │
│  │        PII_PHI_Pipeline                      │               │
│  ├──────────────────────────────────────────────┤               │
│  │ 1. GetProcessedFileNames (Script)            │               │
│  │    └─ Query Warehouse for processed files    │               │
│  │ 2. Get Metadata (GetMetadata)                │               │
│  │    └─ List all files in claims/ folder       │               │
│  │ 3. Filter (Filter)                           │               │
│  │    └─ Remove already-processed files         │               │
│  │ 4. ForEach (ForEach)                         │               │
│  │    └─ Process each new file:                 │               │
│  │       └─ Run PHI_PII_detection Notebook      │               │
│  └──────────────────────────────────────────────┘               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────┐               │
│  │         Notebook                              │               │
│  │      PHI_PII_detection                        │               │
│  ├──────────────────────────────────────────────┤               │
│  │ 1. Read claim file from Lakehouse             │               │
│  │ 2. Read prior auth file from Lakehouse        │               │
│  │ 3. Detect PII/PHI with Presidio               │               │
│  │ 4. Match claims to prior auths                │               │
│  │ 5. Write results to Lakehouse Tables          │               │
│  │ 6. Log to Warehouse processedfiles table      │               │
│  └──────────────────────────────────────────────┘               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. Azure AD Service Principal

You need a Service Principal with permissions to access Microsoft Fabric:

```bash
# Required Azure AD credentials
TENANT_ID="your-tenant-id"
CLIENT_ID="your-client-id"
CLIENT_SECRET="your-client-secret"
```

**Permissions Required:**
- Fabric Admin or Workspace Admin role
- API Permissions: `https://api.fabric.microsoft.com/.default`

### 2. Python Environment

```bash
# Required Python packages
pip install httpx msal asyncio
```

### 3. Fabric Resources

You must have these created in your Fabric workspace:

| Resource Type | Name | Purpose |
|--------------|------|---------|
| Workspace | `jay-dev` | Container for all resources |
| Lakehouse | `jay_dev_lakehouse` | Store files and result tables |
| Warehouse | `jay-dev-warehouse` | Track processed files |

### 4. Warehouse Table

The `processedfiles` table must exist in the warehouse:

```sql
CREATE TABLE processedfiles (
    filename NVARCHAR(500) PRIMARY KEY,
    status NVARCHAR(50),
    processed_timestamp DATETIME,
    pii_phi_detected BIT,
    total_claims INT,
    matched_claims INT
);
```

---

## Components Deployed

### 1. Notebook: `PHI_PII_detection`

**Purpose:** Process claim files and detect PII/PHI

**Features:**
- Reads CSV claim files from Lakehouse
- Detects PII/PHI using Microsoft Presidio
- Matches claims to prior authorization data
- Writes results to Lakehouse tables
- Logs processing status to Warehouse

**Parameters:**
- `fileName` (string): Name of the claim file to process

**Output:**
- Results written to Lakehouse table `results`
- Status logged to Warehouse table `processedfiles`

### 2. Pipeline: `PII_PHI_Pipeline`

**Purpose:** Orchestrate automated file processing

**Activities:**

#### Activity 1: GetProcessedFileNames (Script)
- **Type:** Script
- **Purpose:** Query warehouse for already-processed files
- **Connection:** Warehouse_jay_reddy (SQL connection)
- **Query:**
```sql
SELECT filename FROM processedfiles WHERE status = 'SUCCESS'
```
- **Output Variable:** `processedFileNames` (array of filenames)

#### Activity 2: Get Metadata (GetMetadata)
- **Type:** GetMetadata
- **Purpose:** List all files in the claims folder
- **Dataset:** Binary with LakehouseLocation
- **Location:** `Files/claims/`
- **Field List:** `['childItems']`
- **Output:** Array of file objects

#### Activity 3: Filter (Filter)
- **Type:** Filter
- **Purpose:** Remove already-processed files
- **Input:** Files from Get Metadata
- **Condition:**
```javascript
@not(contains(activity('GetProcessedFileNames').output.resultSetCount.value, item().name))
```

#### Activity 4: ForEach (ForEach)
- **Type:** ForEach
- **Purpose:** Process each new file
- **Items:** Output from Filter activity
- **Sequential:** true
- **Child Activity:**
  - **Type:** Notebook
  - **Notebook:** PHI_PII_detection
  - **Parameters:** `{"fileName": "@item().name"}`

### 3. Connection: `Warehouse_jay_reddy`

**Type:** SQL Connection (Managed Connection)

**Details:**
- **Connectivity Type:** ShareableCloud
- **Server:** `4mry3yr5qcgudjzayc7nhh3xwy-prer2vqji5uuvesn4wnnr6to4e.datawarehouse.fabric.microsoft.com`
- **Database:** `jay-dev-warehouse`
- **Authentication:** Service Principal
- **Privacy Level:** Organizational

---

## Configuration

### Environment Variables

The deployment script `deploy_pipeline.py` uses these configurations:

```python
# ============================================================================
# FABRIC WORKSPACE AND RESOURCE NAMES
# ============================================================================
WORKSPACE_NAME = "jay-dev"
LAKEHOUSE_NAME = "jay_dev_lakehouse"
WAREHOUSE_NAME = "jay-dev-warehouse"
NOTEBOOK_NAME = "PHI_PII_detection"
PIPELINE_NAME = "PII_PHI_Pipeline"
CONNECTION_NAME = "Warehouse_jay_reddy"

# ============================================================================
# AZURE AD AUTHENTICATION
# ============================================================================
TENANT_ID = "e28d23e3-803d-418d-a720-c0bed39f77b6"
CLIENT_ID = "0944e22d-d0f1-40c1-a9fc-f422c05949f3"
CLIENT_SECRET = "oRF8Q~g03M~RuIJ3Tf.eKTS-W8kVvFQXCbIr-ac7"

# ============================================================================
# FABRIC API ENDPOINTS
# ============================================================================
FABRIC_BASE_URL = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
```

### File Paths in Lakehouse

```
jay_dev_lakehouse/
├── Files/
│   ├── claims/              # Place claim CSV files here
│   │   ├── claims_data.csv
│   │   └── claims_jan2024.csv
│   └── priorauths/          # Place prior auth file here
│       └── prior_authorization_data.csv
└── Tables/
    └── results/             # Pipeline writes results here
```

---

## Deployment Process

### Step 1: Authentication

The deployment uses **MSAL (Microsoft Authentication Library)** for OAuth2 authentication:

```python
async def get_access_token() -> str:
    """Get Azure AD access token"""
    import msal

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET
    )

    result = app.acquire_token_for_client(scopes=[FABRIC_SCOPE])

    if "access_token" not in result:
        raise RuntimeError(f"Authentication failed: {result}")

    return result["access_token"]
```

**API Call:**
```http
POST https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}
&scope=https://api.fabric.microsoft.com/.default
&grant_type=client_credentials
```

### Step 2: Find Workspace

```python
async def find_workspace(token: str, workspace_name: str) -> Optional[dict]:
    """Find workspace by name"""
    url = f"{FABRIC_BASE_URL}/workspaces"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

        workspaces = response.json().get("value", [])
        for ws in workspaces:
            if ws.get("displayName") == workspace_name:
                return ws
    return None
```

**API Call:**
```http
GET https://api.fabric.microsoft.com/v1/workspaces
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "value": [
    {
      "id": "561d497c-4709-4a69-924d-e59ad8fa6ee1",
      "displayName": "jay-dev",
      "type": "Workspace"
    }
  ]
}
```

### Step 3: Find Lakehouse and Warehouse

```python
async def find_item_by_name(
    token: str,
    workspace_id: str,
    item_type: str,
    item_name: str
) -> Optional[dict]:
    """Find an item by type and name"""
    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"type": item_type}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()

        items = response.json().get("value", [])
        for item in items:
            if item.get("displayName") == item_name:
                return item
    return None
```

**API Call:**
```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items?type=Lakehouse
Authorization: Bearer {access_token}
```

### Step 4: Create Warehouse SQL Connection

This is a critical step that enables the Script activity to query the warehouse.

```python
async def create_or_get_warehouse_connection(
    token: str,
    connection_name: str,
    sql_endpoint: str,
    database_name: str
) -> Dict[str, Any]:
    """Create or get existing SQL connection to warehouse"""

    list_url = f"{FABRIC_BASE_URL}/connections"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check if connection already exists
        list_response = await client.get(list_url, headers=headers)
        connections = list_response.json().get("value", [])

        for conn in connections:
            if conn.get("displayName") == connection_name:
                return conn

        # Create new connection
        payload = {
            "connectivityType": "ShareableCloud",
            "displayName": connection_name,
            "connectionDetails": {
                "type": "SQL",  # IMPORTANT: Must be uppercase "SQL"
                "creationMethod": "Sql",
                "parameters": [
                    {
                        "dataType": "Text",
                        "name": "server",
                        "value": sql_endpoint
                    },
                    {
                        "dataType": "Text",
                        "name": "database",
                        "value": database_name
                    }
                ]
            },
            "privacyLevel": "Organizational",
            "credentialDetails": {
                "singleSignOnType": "None",
                "connectionEncryption": "NotEncrypted",
                "skipTestConnection": False,
                "credentials": {
                    "credentialType": "ServicePrincipal",
                    "servicePrincipalClientId": CLIENT_ID,
                    "servicePrincipalSecret": CLIENT_SECRET,
                    "tenantId": TENANT_ID
                }
            }
        }

        create_response = await client.post(
            list_url,
            headers=headers,
            data=json.dumps(payload)
        )
        create_response.raise_for_status()

        connection = create_response.json()
        return connection
```

**API Call:**
```http
POST https://api.fabric.microsoft.com/v1/connections
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "connectivityType": "ShareableCloud",
  "displayName": "Warehouse_jay_reddy",
  "connectionDetails": {
    "type": "SQL",
    "creationMethod": "Sql",
    "parameters": [
      {
        "dataType": "Text",
        "name": "server",
        "value": "4mry3yr5qcgudjzayc7nhh3xwy-prer2vqji5uuvesn4wnnr6to4e.datawarehouse.fabric.microsoft.com"
      },
      {
        "dataType": "Text",
        "name": "database",
        "value": "jay-dev-warehouse"
      }
    ]
  },
  "privacyLevel": "Organizational",
  "credentialDetails": {
    "singleSignOnType": "None",
    "connectionEncryption": "NotEncrypted",
    "skipTestConnection": false,
    "credentials": {
      "credentialType": "ServicePrincipal",
      "servicePrincipalClientId": "0944e22d-d0f1-40c1-a9fc-f422c05949f3",
      "servicePrincipalSecret": "oRF8Q~g03M~RuIJ3Tf.eKTS-W8kVvFQXCbIr-ac7",
      "tenantId": "e28d23e3-803d-418d-a720-c0bed39f77b6"
    }
  }
}
```

**Important Notes:**
- ⚠️ `type` must be `"SQL"` (uppercase), not `"Sql"`
- ⚠️ `creationMethod` is `"Sql"` (camel case)
- ⚠️ `skipTestConnection` must be `false` (not `true`)
- ⚠️ Credential field is `servicePrincipalSecret` (not `servicePrincipalKey`)

### Step 5: Create Notebook

```python
async def create_fabric_item(
    token: str,
    workspace_id: str,
    item_type: str,
    item_name: str,
    lakehouse_id: str = None
) -> dict:
    """Create a Fabric item (Notebook or DataPipeline)"""

    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "type": item_type,
        "displayName": item_name
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        item = response.json()
        return item
```

**API Call:**
```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "type": "Notebook",
  "displayName": "PHI_PII_detection"
}
```

### Step 6: Upload Notebook Definition

This is where the **Fabric Python format** is critical.

```python
def get_notebook_ipynb_content(python_source: str, lakehouse_id: str) -> str:
    """
    Converts raw Python script into Fabric Python notebook format.
    This format includes the required prologue and lakehouse metadata.
    """

    # Create Fabric Python notebook format with proper prologue
    fabric_py_content = f"""# Fabric notebook source

# METADATA ********************

# META {{
# META   "dependencies": {{
# META     "lakehouse": {{
# META       "default_lakehouse": "{lakehouse_id}",
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }}
# META   }}
# META }}

# CELL ********************

{python_source}
"""

    return fabric_py_content


async def update_item_definition(
    token: str,
    workspace_id: str,
    item_id: str,
    payload_str: str
):
    """Upload a definition (Notebook, Pipeline) to a Fabric item"""

    payload_bytes = payload_str.encode("utf-8")
    encoded_payload = base64.b64encode(payload_bytes).decode("ascii")

    # Determine the correct path based on content type
    if payload_str.startswith("# Fabric notebook source"):
        content_path = "notebook-content.py"
    else:
        content_path = "pipeline-content.json"

    update_payload = {
        "definition": {
            "parts": [
                {
                    "path": content_path,
                    "payload": encoded_payload,
                    "payloadType": "InlineBase64"
                }
            ]
        }
    }

    url = f"{FABRIC_BASE_URL}/workspaces/{workspace_id}/items/{item_id}/updateDefinition"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, data=json.dumps(update_payload))
        response.raise_for_status()

        # Poll operation if async
        operation_id = response.headers.get("x-ms-operation-id")
        if operation_id and response.status_code == 202:
            await poll_operation_status(token, operation_id)
```

**API Call:**
```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{notebook_id}/updateDefinition
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "definition": {
    "parts": [
      {
        "path": "notebook-content.py",
        "payload": "IyBGYWJyaWMgbm90ZWJvb2sgc291cmNlCgojIE1FVEFEQVRBIC...",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

**Response:**
```http
HTTP/1.1 202 Accepted
Location: https://api.fabric.microsoft.com/v1/operations/{operation_id}
x-ms-operation-id: f375dca0-7506-4786-82d1-236a56a2b0fa
Retry-After: 20
```

### Step 7: Poll Operation Status

Since updateDefinition is asynchronous, we must poll for completion:

```python
async def poll_operation_status(token: str, operation_id: str, max_attempts: int = 30):
    """Poll operation status until completion"""
    url = f"{FABRIC_BASE_URL}/operations/{operation_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(max_attempts):
            await asyncio.sleep(2)

            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                operation_data = response.json()
                status = operation_data.get("status")

                if status == "Succeeded":
                    return operation_data
                elif status == "Failed":
                    error = operation_data.get("error", {})
                    raise RuntimeError(f"Operation failed: {error}")
                elif status in ["Running", "NotStarted"]:
                    continue

        raise RuntimeError(f"Operation polling timeout")
```

**API Call:**
```http
GET https://api.fabric.microsoft.com/v1/operations/{operation_id}
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": "f375dca0-7506-4786-82d1-236a56a2b0fa",
  "status": "Succeeded",
  "createdDateTime": "2025-11-08T16:38:23Z",
  "lastUpdatedDateTime": "2025-11-08T16:38:27Z"
}
```

### Step 8: Deploy Pipeline

The pipeline JSON is modified to inject the correct IDs and connection:

```python
def modify_pipeline_definition(
    template_str: str,
    new_workspace_id: str,
    new_lakehouse_id: str,
    new_notebook_id: str,
    warehouse_connection_id: str
) -> str:
    """Modify pipeline template with actual resource IDs"""

    pipeline_obj = json.loads(template_str)

    # Update Notebook activity
    for activity in pipeline_obj.get("properties", {}).get("activities", []):
        if activity.get("name") == "RunNotebook":
            # Update notebook reference
            activity["typeProperties"]["notebookId"] = new_notebook_id
            activity["typeProperties"]["workspaceId"] = new_workspace_id

    # Update Script activity with connection
    for activity in pipeline_obj.get("properties", {}).get("activities", []):
        if activity.get("name") == "GetProcessedFileNames":
            # Add external reference to connection
            activity["externalReferences"] = {
                "connection": warehouse_connection_id
            }

    # Update GetMetadata activity with inline lakehouse connection
    for activity in pipeline_obj.get("properties", {}).get("activities", []):
        if activity.get("name") == "Get Metadata":
            activity["typeProperties"]["datasetSettings"] = {
                "type": "Binary",
                "linkedService": {
                    "name": "LakehouseRef",
                    "properties": {
                        "type": "Lakehouse",
                        "typeProperties": {
                            "workspaceId": new_workspace_id,
                            "artifactId": new_lakehouse_id,
                            "rootFolder": "Files"
                        }
                    }
                },
                "typeProperties": {
                    "location": {
                        "type": "LakehouseLocation",
                        "folderPath": "claims/"
                    }
                }
            }

    return json.dumps(pipeline_obj)
```

---

## API Reference

### Authentication

#### Get Access Token
```http
POST https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
&client_secret={CLIENT_SECRET}
&scope=https://api.fabric.microsoft.com/.default
&grant_type=client_credentials
```

### Workspaces

#### List Workspaces
```http
GET https://api.fabric.microsoft.com/v1/workspaces
Authorization: Bearer {access_token}
```

### Items

#### List Items in Workspace
```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items?type={item_type}
Authorization: Bearer {access_token}
```

**Item Types:** `Lakehouse`, `Warehouse`, `Notebook`, `DataPipeline`, `SemanticModel`

#### Create Item
```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "type": "Notebook",
  "displayName": "MyNotebook"
}
```

#### Update Item Definition
```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{item_id}/updateDefinition
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "definition": {
    "parts": [
      {
        "path": "notebook-content.py",
        "payload": "{base64_encoded_content}",
        "payloadType": "InlineBase64"
      }
    ]
  }
}
```

#### Get Item Definition
```http
POST https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/items/{item_id}/getDefinition
Authorization: Bearer {access_token}
```

### Connections

#### List Connections
```http
GET https://api.fabric.microsoft.com/v1/connections
Authorization: Bearer {access_token}
```

#### Create Connection
```http
POST https://api.fabric.microsoft.com/v1/connections
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "connectivityType": "ShareableCloud",
  "displayName": "MyConnection",
  "connectionDetails": {
    "type": "SQL",
    "creationMethod": "Sql",
    "parameters": [...]
  },
  "privacyLevel": "Organizational",
  "credentialDetails": {...}
}
```

### Operations

#### Get Operation Status
```http
GET https://api.fabric.microsoft.com/v1/operations/{operation_id}
Authorization: Bearer {access_token}
```

### Warehouse

#### Get Warehouse Properties
```http
GET https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/warehouses/{warehouse_id}
Authorization: Bearer {access_token}
```

**Response includes SQL endpoint:**
```json
{
  "id": "1dfba14d-4bad-4314-af53-d6cc483e52ef",
  "displayName": "jay-dev-warehouse",
  "properties": {
    "connectionString": "server.datawarehouse.fabric.microsoft.com"
  }
}
```

---

## Connection Management

### SQL Connection Structure

The warehouse SQL connection enables Script activities to query the warehouse:

```json
{
  "id": "0b30e036-b711-4f4b-9594-d0db785790c8",
  "displayName": "Warehouse_jay_reddy",
  "connectivityType": "ShareableCloud",
  "connectionDetails": {
    "type": "SQL",
    "creationMethod": "Sql",
    "parameters": [
      {
        "name": "server",
        "value": "4mry3yr5qcgudjzayc7nhh3xwy-prer2vqji5uuvesn4wnnr6to4e.datawarehouse.fabric.microsoft.com",
        "dataType": "Text"
      },
      {
        "name": "database",
        "value": "jay-dev-warehouse",
        "dataType": "Text"
      }
    ]
  },
  "privacyLevel": "Organizational",
  "credentialDetails": {
    "singleSignOnType": "None",
    "connectionEncryption": "NotEncrypted",
    "credentials": {
      "credentialType": "ServicePrincipal"
    }
  }
}
```

### Using Connection in Pipeline

To use a connection in a Script activity, reference it via `externalReferences`:

```json
{
  "name": "GetProcessedFileNames",
  "type": "Script",
  "typeProperties": {
    "scriptType": "Query",
    "scripts": [
      {
        "type": "Query",
        "text": "SELECT filename FROM processedfiles WHERE status = 'SUCCESS'"
      }
    ],
    "scriptBlockExecutionTimeout": "02:00:00"
  },
  "externalReferences": {
    "connection": "0b30e036-b711-4f4b-9594-d0db785790c8"
  }
}
```

**Important:**
- The connection ID is required in `externalReferences`
- You cannot use a connection name or string - must be the GUID
- Connection must be created before pipeline deployment

---

## Notebook Format

### Fabric Python Notebook Format

Microsoft Fabric requires notebooks to be in a specific Python format with metadata:

```python
# Fabric notebook source

# METADATA ********************

# META {
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "{lakehouse_id}",
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }
# META   }
# META }

# CELL ********************

# Your actual Python code goes here
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("MyNotebook").getOrCreate()

# ... rest of your code ...
```

**Key Requirements:**
1. Must start with `# Fabric notebook source`
2. Metadata section with `# METADATA ********************`
3. Lakehouse dependency in META block (JSON in comments)
4. Cell marker `# CELL ********************`
5. Actual code after the cell marker

### Uploading Notebook

When uploading, the path must be `notebook-content.py`:

```python
# Encode content
payload_bytes = fabric_py_content.encode("utf-8")
encoded_payload = base64.b64encode(payload_bytes).decode("ascii")

# Upload with correct path
update_payload = {
    "definition": {
        "parts": [
            {
                "path": "notebook-content.py",  # Must be .py for Fabric format
                "payload": encoded_payload,
                "payloadType": "InlineBase64"
            }
        ]
    }
}
```

**Common Mistakes:**
- ❌ Using `notebook-content.json` or `notebook-content.ipynb`
- ❌ Uploading ipynb JSON format (causes "PyToIPynbFailure" error)
- ❌ Missing the `# Fabric notebook source` prologue
- ❌ Not encoding in base64

---

## Pipeline Structure

### Complete Pipeline JSON

The pipeline definition uses this structure:

```json
{
  "properties": {
    "activities": [
      {
        "name": "GetProcessedFileNames",
        "type": "Script",
        "typeProperties": {
          "scriptType": "Query",
          "scripts": [
            {
              "type": "Query",
              "text": "SELECT filename FROM processedfiles WHERE status = 'SUCCESS'"
            }
          ],
          "scriptBlockExecutionTimeout": "02:00:00"
        },
        "externalReferences": {
          "connection": "{warehouse_connection_id}"
        }
      },
      {
        "name": "Get Metadata",
        "type": "GetMetadata",
        "dependsOn": [
          {
            "activity": "GetProcessedFileNames",
            "dependencyConditions": ["Succeeded"]
          }
        ],
        "typeProperties": {
          "datasetSettings": {
            "type": "Binary",
            "linkedService": {
              "name": "LakehouseRef",
              "properties": {
                "type": "Lakehouse",
                "typeProperties": {
                  "workspaceId": "{workspace_id}",
                  "artifactId": "{lakehouse_id}",
                  "rootFolder": "Files"
                }
              }
            },
            "typeProperties": {
              "location": {
                "type": "LakehouseLocation",
                "folderPath": "claims/"
              }
            }
          },
          "fieldList": ["childItems"]
        }
      },
      {
        "name": "Filter",
        "type": "Filter",
        "dependsOn": [
          {
            "activity": "Get Metadata",
            "dependencyConditions": ["Succeeded"]
          }
        ],
        "typeProperties": {
          "items": {
            "value": "@activity('Get Metadata').output.childItems",
            "type": "Expression"
          },
          "condition": {
            "value": "@not(contains(activity('GetProcessedFileNames').output.resultSet, item().name))",
            "type": "Expression"
          }
        }
      },
      {
        "name": "ForEach",
        "type": "ForEach",
        "dependsOn": [
          {
            "activity": "Filter",
            "dependencyConditions": ["Succeeded"]
          }
        ],
        "typeProperties": {
          "items": {
            "value": "@activity('Filter').output.value",
            "type": "Expression"
          },
          "isSequential": true,
          "activities": [
            {
              "name": "RunNotebook",
              "type": "Notebook",
              "typeProperties": {
                "notebookId": "{notebook_id}",
                "workspaceId": "{workspace_id}",
                "parameters": {
                  "fileName": {
                    "value": "@item().name",
                    "type": "Expression"
                  }
                }
              }
            }
          ]
        }
      }
    ]
  }
}
```

### GetMetadata Activity - Correct Dataset Structure

**This is critical!** The GetMetadata activity must use `Binary` type with `LakehouseLocation`:

```json
{
  "name": "Get Metadata",
  "type": "GetMetadata",
  "typeProperties": {
    "datasetSettings": {
      "type": "Binary",
      "linkedService": {
        "name": "LakehouseRef",
        "properties": {
          "type": "Lakehouse",
          "typeProperties": {
            "workspaceId": "{workspace_id}",
            "artifactId": "{lakehouse_id}",
            "rootFolder": "Files"
          }
        }
      },
      "typeProperties": {
        "location": {
          "type": "LakehouseLocation",
          "folderPath": "claims/"
        }
      }
    },
    "fieldList": ["childItems"]
  }
}
```

**Common Mistakes:**
- ❌ Using `LakehouseFile`, `LakehouseFiles`, or `LakehouseFolder` types
- ❌ Missing `linkedService` inline definition
- ❌ Using dataset reference instead of inline dataset
- ✅ Must be `Binary` with `LakehouseLocation`

---

## Troubleshooting

### Authentication Issues

**Error:** `AADSTS90002: Tenant 'xxx' not found`
- **Cause:** Invalid tenant ID
- **Fix:** Verify tenant ID in Azure Portal → Azure Active Directory → Overview

**Error:** `AADSTS7000215: Invalid client secret`
- **Cause:** Wrong or expired client secret
- **Fix:** Regenerate client secret in App Registration → Certificates & secrets

### Connection Issues

**Error:** `Kind: Sql is not supported`
- **Cause:** Connection type is lowercase "Sql" instead of "SQL"
- **Fix:** Use `"type": "SQL"` (uppercase)

**Error:** `ServicePrincipalSecret field is required`
- **Cause:** Wrong credential field name
- **Fix:** Use `servicePrincipalSecret` not `servicePrincipalKey`

**Error:** `SkipTestConnection is not supported`
- **Cause:** `skipTestConnection: true` not allowed for this connection type
- **Fix:** Set `"skipTestConnection": false`

### Notebook Issues

**Error:** `PyToIPynbFailure - prologue is invalid`
- **Cause:** Notebook not in Fabric Python format
- **Fix:** Use the Fabric Python format with `# Fabric notebook source` prologue

**Error:** `The file suffix type .ipynb is not supported`
- **Cause:** Using wrong file path
- **Fix:** Use `"path": "notebook-content.py"` not `.ipynb` or `.json`

**Issue:** Notebook has no code in cells
- **Cause:** Using ipynb JSON format instead of Fabric Python format
- **Fix:** Convert to Fabric Python format and re-upload

### Pipeline Issues

**Error:** `Connection cannot be null`
- **Cause:** Script activity missing `externalReferences`
- **Fix:** Add connection ID to `externalReferences.connection`

**Error:** `GetMetadata activity failed`
- **Cause:** Wrong dataset type
- **Fix:** Use Binary with LakehouseLocation (not LakehouseFile/Files/Folder)

### API Issues

**Error:** `202 Accepted` but no content
- **Cause:** Async operation not polled
- **Fix:** Poll the operation endpoint until status is "Succeeded"

**Error:** `Operation timeout`
- **Cause:** Operation taking longer than expected
- **Fix:** Increase polling timeout or retry

---

## Usage Guide

### 1. Initial Setup

```bash
# Clone or download the deployment script
cd /path/to/fabric-data-pipeline-automation/backend

# Install dependencies
pip install httpx msal

# Update credentials in deploy_pipeline.py
# - TENANT_ID
# - CLIENT_ID
# - CLIENT_SECRET
# - WORKSPACE_NAME
# - LAKEHOUSE_NAME
# - WAREHOUSE_NAME
```

### 2. Deploy Solution

```bash
# Run deployment
python3 deploy_pipeline.py
```

**Expected Output:**
```
================================================================================
  STANDALONE PII/PHI SOLUTION DEPLOYMENT (Hybrid)
================================================================================

1. Authenticating...
   ✓ Access token obtained

2. Finding workspace 'jay-dev'...
   ✓ Found workspace: 561d497c-4709-4a69-924d-e59ad8fa6ee1

3. Finding Lakehouse 'jay_dev_lakehouse'...
   ✓ Found Lakehouse: 71b91fa4-7883-44e1-aa6f-f2d6c8d564ef

4. Finding Warehouse 'jay-dev-warehouse'...
   ✓ Found Warehouse: 1dfba14d-4bad-4314-af53-d6cc483e52ef

4.5. Creating Warehouse SQL Connection...
   ✓ Warehouse connection ready: 0b30e036-b711-4f4b-9594-d0db785790c8

5. Deploying Notebook 'PHI_PII_detection'...
   ✓ Notebook 'PHI_PII_detection' deployed.

6. Deploying Pipeline 'PII_PHI_Pipeline'...
   ✓ Pipeline 'PII_PHI_Pipeline' deployed.

================================================================================
  ✅ SOLUTION DEPLOYMENT SUCCESSFUL
================================================================================
```

### 3. Upload Data Files

```bash
# Upload prior authorization file
# Go to Fabric UI → jay-dev → jay_dev_lakehouse
# Upload to: Files/priorauths/prior_authorization_data.csv

# Upload claim files
# Upload to: Files/claims/claims_data.csv
```

### 4. Run Pipeline

1. Open Fabric UI: https://app.fabric.microsoft.com
2. Navigate to: **jay-dev workspace**
3. Open: **PII_PHI_Pipeline**
4. Click: **Run**
5. Monitor execution in the pipeline run view

### 5. Check Results

**View Processed Files:**
```sql
-- Run in Warehouse SQL Analytics Endpoint
SELECT * FROM processedfiles ORDER BY processed_timestamp DESC;
```

**View Results:**
```python
# In a Fabric Notebook
df = spark.read.table("jay_dev_lakehouse.results")
display(df)
```

### 6. Redeploy

If you need to redeploy:

```bash
# Delete existing items in Fabric UI (optional)
# - Delete PII_PHI_Pipeline
# - Delete PHI_PII_detection notebook

# Run deployment again
python3 deploy_pipeline.py
```

---

## Data Flow Summary

1. **User uploads claim files** → `jay_dev_lakehouse/Files/claims/`
2. **Pipeline triggers** (manual or scheduled)
3. **Script activity queries warehouse** → Gets list of already-processed files
4. **GetMetadata activity** → Lists all files in claims folder
5. **Filter activity** → Removes already-processed files from list
6. **ForEach activity** → Loops through new files
7. **Notebook runs** for each file:
   - Reads claim CSV
   - Reads prior auth CSV
   - Detects PII/PHI with Presidio
   - Matches claims to prior auths
   - Writes results to Lakehouse table
   - Logs status to Warehouse table
8. **Results available** in Lakehouse tables and Warehouse logs

---

## Security Considerations

1. **Service Principal Permissions**
   - Grant minimum required permissions
   - Use separate service principals for different environments
   - Rotate secrets regularly

2. **Connection Security**
   - Service Principal authentication (not username/password)
   - Connection encryption settings
   - Privacy level: Organizational

3. **Data Protection**
   - PII/PHI data handled in secure Lakehouse
   - Results logged for audit trail
   - Access controlled via Fabric workspace permissions

4. **Secret Management**
   - Never commit secrets to git
   - Use Azure Key Vault for production
   - Environment variables for credentials

---

## Performance Optimization

1. **Pipeline Execution**
   - Set `isSequential: true` for ForEach to control concurrency
   - Adjust timeout values based on file size
   - Use triggers for scheduled execution

2. **Notebook Optimization**
   - Partition large datasets
   - Use appropriate Spark configurations
   - Cache frequently accessed data

3. **Warehouse Queries**
   - Index on `filename` column in processedfiles table
   - Regular maintenance and statistics updates

---

## Monitoring and Logging

### Pipeline Monitoring

**View Pipeline Runs:**
1. Open Fabric UI → jay-dev workspace
2. Click on PII_PHI_Pipeline
3. Go to "Run history" tab
4. View status, duration, and errors

### Notebook Monitoring

**View Notebook Runs:**
1. Open PHI_PII_detection notebook
2. Check execution history
3. Review output and errors

### Warehouse Logging

**Query Processing Logs:**
```sql
-- All processed files
SELECT * FROM processedfiles ORDER BY processed_timestamp DESC;

-- Failed files
SELECT * FROM processedfiles WHERE status = 'FAILED';

-- Files with PII/PHI
SELECT * FROM processedfiles WHERE pii_phi_detected = 1;

-- Processing statistics
SELECT
    status,
    COUNT(*) as file_count,
    AVG(total_claims) as avg_claims,
    AVG(matched_claims) as avg_matched
FROM processedfiles
GROUP BY status;
```

---

## Appendix

### A. File Structure

```
fabric-data-pipeline-automation/
└── backend/
    ├── deploy_pipeline.py              # Main deployment script
    ├── fix_notebook_with_polling.py    # Fix notebook content
    ├── check_notebook_with_polling.py  # Verify notebook content
    ├── DEPLOYMENT_GUIDE.md             # This file
    └── debug_pipeline.json             # Generated pipeline JSON
```

### B. API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/workspaces` | GET | List workspaces |
| `/workspaces/{id}/items` | GET | List items in workspace |
| `/workspaces/{id}/items` | POST | Create new item |
| `/workspaces/{id}/items/{id}/updateDefinition` | POST | Upload item definition |
| `/workspaces/{id}/items/{id}/getDefinition` | POST | Get item definition |
| `/workspaces/{id}/warehouses/{id}` | GET | Get warehouse properties |
| `/connections` | GET | List connections |
| `/connections` | POST | Create connection |
| `/operations/{id}` | GET | Get operation status |

### C. Resource IDs

Current deployment IDs (example):

| Resource | ID |
|----------|-----|
| Workspace | `561d497c-4709-4a69-924d-e59ad8fa6ee1` |
| Lakehouse | `71b91fa4-7883-44e1-aa6f-f2d6c8d564ef` |
| Warehouse | `1dfba14d-4bad-4314-af53-d6cc483e52ef` |
| Connection | `0b30e036-b711-4f4b-9594-d0db785790c8` |
| Notebook | `15a011de-fa33-40db-b69d-7d938b26660c` |
| Pipeline | `e330194a-fe1e-43ee-801f-3a4b75ed1afb` |

### D. Common Fabric Expressions

**Filter Condition:**
```javascript
@not(contains(activity('GetProcessedFileNames').output.resultSet, item().name))
```

**ForEach Items:**
```javascript
@activity('Filter').output.value
```

**Notebook Parameter:**
```javascript
@item().name
```

### E. SQL Endpoint Format

```
{unique-id}.datawarehouse.fabric.microsoft.com
```

Example:
```
4mry3yr5qcgudjzayc7nhh3xwy-prer2vqji5uuvesn4wnnr6to4e.datawarehouse.fabric.microsoft.com
```

---

## Support and Contributing

For issues or questions:
1. Check this documentation
2. Review debug_pipeline.json for pipeline structure
3. Check Fabric UI for detailed error messages
4. Verify all prerequisites are met

---

**Document Version:** 1.0
**Last Updated:** 2025-11-08
**Author:** Automated Deployment System
**Fabric API Version:** v1
