# Microsoft Fabric Pipeline Builder - Deployment Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Azure Resources & Credentials](#azure-resources--credentials)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [How It Works](#how-it-works)
7. [Troubleshooting](#troubleshooting)

---

## System Overview

The **Microsoft Fabric Pipeline Builder** is an AI-powered application that allows users to design and deploy data pipelines to Microsoft Fabric workspaces using natural language. The system consists of three main components:

1. **Frontend (React)**: User interface for chatting with AI and managing pipelines
2. **Backend (FastAPI)**: API server that orchestrates Claude AI and Fabric API
3. **Workspace Backend**: Manages workspace access and user permissions

### Key Features
- 💬 Natural language pipeline design with Claude AI (Anthropic)
- 🏗️ Automatic generation of Medallion architecture (Bronze/Silver/Gold layers)
- 📓 Auto-generates PySpark notebooks with data transformation code
- 🚀 One-click deployment to Microsoft Fabric workspaces
- 🔐 Azure AD authentication for secure access

---

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  React Frontend │────────▶│  FastAPI Backend│────────▶│  Claude AI API  │
│  (Port 3002)    │         │  (Port 8001)    │         │  (Anthropic)    │
│                 │         │                 │         │                 │
└─────────────────┘         └────────┬────────┘         └─────────────────┘
                                     │
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │              │  │              │  │              │
            │ Fabric API   │  │ Workspace    │  │  Azure AD    │
            │ (Microsoft)  │  │ Backend API  │  │  Auth        │
            │              │  │              │  │              │
            └──────────────┘  └──────────────┘  └──────────────┘
```

### Data Flow

1. **User Authentication**: User logs in via Azure AD (MSAL.js)
2. **Workspace Selection**: Frontend fetches approved workspaces from Workspace Backend
3. **AI Chat**: User describes pipeline requirements in natural language
4. **Pipeline Generation**: Claude AI generates complete pipeline definition with activities and notebooks
5. **Deployment**: Backend deploys pipeline and notebooks to selected Fabric workspace via Fabric REST API

---

## Azure Resources & Credentials

### 1. Azure Active Directory (App Registration)

**App Name**: Pipeline Builder Application

**Application (client) ID**: `0944e22d-d0f1-40c1-a9fc-f422c05949f3`

**Directory (tenant) ID**: `e28d23e3-803d-418d-a720-c0bed39f77b6`

**Client Secret**: `[STORED IN .env FILE]`

**Redirect URIs** (SPA Platform):
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:3002`

**API Permissions**:
- Microsoft Graph: `User.Read`
- Microsoft Fabric: `https://api.fabric.microsoft.com/.default`

**Authentication Configuration**:
- Enable ID tokens
- Enable access tokens
- Allow public client flows: Yes

**Service Principal Object ID**: `[Used for Fabric API access]`

---

### 2. Resource Groups

**Primary Resource Group**: (Add your resource group name)

**Region**: East US (or your preferred region)

**Resources in Group**:
- Container Apps (for backend deployment)
- Container Registry
- Log Analytics Workspace
- Storage Accounts (for lakehouse data)

---

### 3. Microsoft Fabric Resources

**Workspace ID**: `5b55aa8e-95fd-4534-9461-9935197de15e`

**Workspace Name**: `jay-test`

**Fabric Capacity**: (Your Fabric capacity name)

**API Endpoint**: `https://api.fabric.microsoft.com/v1`

**Required Permissions**:
- The service principal must have **Contributor** role on the workspace
- Workspace must be on a supported Fabric capacity (F2 or higher)

---

### 4. Workspace Management Backend

**Backend URL**: `https://fabric-pipeline-backend.delightfulplant-1c861d44.eastus.azurecontainerapps.io`

**Endpoints**:
- `GET /api/workspaces` - List all workspaces
- `GET /api/workspaces/approved?user_email={email}` - Get user's approved workspaces

**Database**: Azure SQL Database (for storing workspace access permissions)

**Connection Details**:
- Server: (Your SQL server name)
- Database: (Your database name)
- Authentication: Azure AD or SQL Authentication

---

### 5. Anthropic (Claude AI)

**Service**: Claude AI (Anthropic)

**Model**: `claude-3-5-sonnet-20241022`

**API Key**: `[STORED IN .env FILE]`

**Max Tokens**: `16000`

**Use Case**:
- Natural language understanding
- Pipeline design recommendations
- PySpark code generation
- Activity configuration generation

---

## Backend Deployment

### Prerequisites

1. Python 3.10+
2. pip3
3. Azure CLI (for container deployment)

### Environment Configuration

Create `.env` file in `pipeline-builder-backend/` directory:

```bash
# Anthropic Claude AI
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=16000

# Microsoft Fabric API
FABRIC_CLIENT_ID=0944e22d-d0f1-40c1-a9fc-f422c05949f3
FABRIC_CLIENT_SECRET=your-client-secret-here
FABRIC_TENANT_ID=e28d23e3-803d-418d-a720-c0bed39f77b6

# Workspace Backend
WORKSPACE_BACKEND_URL=https://fabric-pipeline-backend.delightfulplant-1c861d44.eastus.azurecontainerapps.io

# CORS (add all frontend URLs)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:3002

# Development Mode (set to "false" in production)
DISABLE_AUTH=true
```

### Local Development

```bash
# Navigate to backend directory
cd pipeline-builder-backend

# Install dependencies
pip3 install -r requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: `http://localhost:8001`

API Documentation: `http://localhost:8001/docs`

### Production Deployment (Azure Container Apps)

```bash
# Build Docker image
docker build -t pipeline-builder-backend .

# Tag for Azure Container Registry
docker tag pipeline-builder-backend <your-acr>.azurecr.io/pipeline-builder-backend:latest

# Push to ACR
az acr login --name <your-acr>
docker push <your-acr>.azurecr.io/pipeline-builder-backend:latest

# Deploy to Container Apps
az containerapp update \
  --name pipeline-builder-backend \
  --resource-group <your-resource-group> \
  --image <your-acr>.azurecr.io/pipeline-builder-backend:latest \
  --set-env-vars \
    ANTHROPIC_API_KEY=<key> \
    FABRIC_CLIENT_ID=<id> \
    FABRIC_CLIENT_SECRET=<secret> \
    FABRIC_TENANT_ID=<tenant> \
    WORKSPACE_BACKEND_URL=<url> \
    DISABLE_AUTH=false
```

---

## Frontend Deployment

### Prerequisites

1. Node.js 16+
2. npm

### Environment Configuration

Create `.env` file in `pipeline-builder-frontend/` directory:

```bash
# Backend API URL
REACT_APP_API_URL=http://localhost:8001

# Azure AD Configuration (for MSAL authentication)
REACT_APP_CLIENT_ID=0944e22d-d0f1-40c1-a9fc-f422c05949f3
REACT_APP_TENANT_ID=e28d23e3-803d-418d-a720-c0bed39f77b6
REACT_APP_REDIRECT_URI=http://localhost:3002
```

### Local Development

```bash
# Navigate to frontend directory
cd pipeline-builder-frontend

# Install dependencies
npm install

# Start development server on port 3002
PORT=3002 npm start
```

Frontend will be available at: `http://localhost:3002`

### Production Deployment (Azure Static Web Apps or Container Apps)

```bash
# Build production bundle
npm run build

# Deploy to Azure Static Web Apps
az staticwebapp create \
  --name pipeline-builder-frontend \
  --resource-group <your-resource-group> \
  --source ./build \
  --location eastus \
  --branch main \
  --app-location "/build" \
  --output-location "build"

# Or deploy as Container App
docker build -t pipeline-builder-frontend .
docker push <your-acr>.azurecr.io/pipeline-builder-frontend:latest

az containerapp create \
  --name pipeline-builder-frontend \
  --resource-group <your-resource-group> \
  --image <your-acr>.azurecr.io/pipeline-builder-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --environment <your-container-env>
```

---

## How It Works

### Step-by-Step Workflow

#### 1. User Authentication Flow

```
User clicks "Sign In"
  → MSAL.js initiates OAuth2 flow
  → Redirect to login.microsoftonline.com
  → User enters Microsoft credentials
  → Azure AD validates credentials
  → Redirect back to app with ID token
  → Frontend stores token in localStorage
  → Token sent in Authorization header for all API calls
```

**Authentication in Development Mode**:
- Set `DISABLE_AUTH=true` in backend `.env`
- Backend bypasses token validation
- Uses mock user: `dev@example.com`

**Authentication in Production**:
- Set `DISABLE_AUTH=false`
- Backend validates JWT tokens against Azure AD
- Uses PyJWKClient to fetch signing keys from Microsoft
- Validates token signature, expiry, and claims

#### 2. Workspace Loading

```
Frontend loads
  → Calls GET /api/workspaces with Authorization header
  → Backend validates token
  → Backend calls Workspace Backend API
  → Workspace Backend queries SQL database
  → Returns list of workspaces user has access to
  → Frontend displays workspace dropdown
  → User selects workspace
```

**Workspace Data Structure**:
```json
{
  "id": "5b55aa8e-95fd-4534-9461-9935197de15e",
  "name": "jay-test",
  "capacity_id": "...",
  "status": "Active"
}
```

#### 3. AI Chat for Pipeline Design

```
User types message: "I need to load CSV files from Blob Storage"
  → Frontend sends POST /api/ai/chat
  → Backend receives message + workspace context
  → Backend calls Claude AI API with system prompt
  → Claude analyzes requirement
  → Claude responds with suggestions/questions
  → Frontend displays AI response
  → User refines requirements through chat
```

**System Prompt Summary**:
- Act as Microsoft Fabric pipeline architect
- Design complete solutions immediately (be proactive)
- Make reasonable assumptions about missing details
- Follow Medallion architecture (Bronze/Silver/Gold)
- Generate PySpark code for transformations
- Keep code concise (max 50 lines per notebook)

#### 4. Pipeline Generation

```
User clicks "Generate Pipeline"
  → Frontend sends POST /api/pipelines/generate with:
    - pipeline_name
    - workspace_id
    - source_type (e.g., AzureBlob, AzureSQL)
    - tables list
    - source_config (connection details)
    - transformations list
    - use_medallion: true

  → Backend builds detailed prompt for Claude
  → Claude generates complete pipeline JSON:
    {
      "activities": [
        {
          "name": "bronze_load_customers",
          "type": "Copy",
          "config": {...},
          "depends_on": []
        },
        {
          "name": "silver_transform_customers",
          "type": "Notebook",
          "config": {...},
          "depends_on": ["bronze_load_customers"]
        }
      ],
      "notebooks": [
        {
          "notebook_name": "silver_customer_processing",
          "layer": "silver",
          "code": "# PySpark code here...",
          "description": "Clean and deduplicate customer data"
        }
      ],
      "reasoning": "Explanation of design decisions"
    }

  → Backend parses JSON response
  → Backend generates pipeline_id (timestamp)
  → Backend stores in memory: generated_pipelines[pipeline_id]
  → Backend returns pipeline preview to frontend
  → Frontend displays activities and notebooks
```

**Pipeline Activity Types**:
- **Copy Activity**: For bulk data ingestion (SQL → Lakehouse)
- **Notebook Activity**: For data transformations (PySpark)
- **ForEach Activity**: For iterating over multiple tables
- **Lookup Activity**: For fetching metadata/watermarks
- **Script Activity**: For simple SQL transformations

**Generated Notebook Structure**:
```python
# Silver Layer: Customer Data Cleaning
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

# Read from Bronze
df = spark.read.format("delta").load("Tables/bronze_customers")

# Apply transformations
df_clean = df.dropDuplicates(["customer_id"]) \
    .filter(col("customer_id").isNotNull()) \
    .withColumn("phone", regexp_replace("phone", "[^0-9]", ""))

# Write to Silver
df_clean.write.format("delta").mode("overwrite").save("Tables/silver_customers")

print(f"Processed {df_clean.count()} records")
```

#### 5. Pipeline Deployment to Fabric

```
User clicks "Deploy to Fabric Workspace"
  → Frontend sends POST /api/pipelines/{pipeline_id}/deploy
  → Backend retrieves pipeline from memory
  → Backend gets OAuth2 token from Azure AD

  → For each notebook:
      → Convert PySpark code to Jupyter notebook format (.ipynb)
      → Base64 encode the notebook content
      → POST /v1/workspaces/{id}/notebooks
      → Fabric API creates notebook (202 Accepted)

  → For the pipeline:
      → Base64 encode pipeline definition (activities JSON)
      → POST /v1/workspaces/{id}/dataPipelines
      → Fabric API creates pipeline (201 Created)

  → Backend returns deployment results:
    {
      "success": true,
      "pipeline_id": 1760389008,
      "fabric_pipeline_id": "abc-123-def",
      "notebooks_deployed": 4,
      "deployed_notebooks": [
        "silver_customer_processing",
        "gold_customer_analytics"
      ]
    }

  → Frontend shows success message
  → User can view pipeline in Fabric workspace
```

**Fabric API Endpoints Used**:

1. **Create Notebook**:
   ```
   POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/notebooks

   Body:
   {
     "displayName": "silver_customer_processing",
     "description": "Notebook for customer data transformation",
     "definition": {
       "format": "ipynb",
       "parts": [
         {
           "path": "notebook-content.ipynb",
           "payload": "<base64-encoded-notebook>",
           "payloadType": "InlineBase64"
         }
       ]
     }
   }

   Response: 202 Accepted (async operation)
   ```

2. **Create Data Pipeline**:
   ```
   POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/dataPipelines

   Body:
   {
     "displayName": "CustomerDataPipeline",
     "description": "AI-generated data pipeline for Medallion architecture",
     "definition": {
       "parts": [
         {
           "path": "pipeline-content.json",
           "payload": "<base64-encoded-pipeline>",
           "payloadType": "InlineBase64"
         }
       ]
     }
   }

   Response: 201 Created
   ```

**Jupyter Notebook Format**:
```json
{
  "nbformat": 4,
  "nbformat_minor": 2,
  "cells": [
    {
      "cell_type": "code",
      "source": "# PySpark code here",
      "metadata": {},
      "outputs": [],
      "execution_count": null
    }
  ],
  "metadata": {
    "kernelspec": {
      "name": "synapse_pyspark",
      "display_name": "Synapse PySpark"
    },
    "language_info": {
      "name": "python"
    }
  }
}
```

---

## Current Status & Known Issues

### ✅ Working Features

1. **Authentication**: Azure AD MSAL authentication working (with dev mode bypass)
2. **Workspace Loading**: Successfully fetching workspaces from backend
3. **AI Chat**: Claude AI responding to user queries
4. **Pipeline Generation**: Generating complete pipeline definitions with activities and notebooks
5. **OAuth2 Token Acquisition**: Successfully obtaining Fabric API access tokens
6. **API Endpoints**: Using correct Fabric REST API endpoints

### ⚠️ Current Issue: Pipeline Validation Error

**Error Message**:
```
ActivityName bronze_azure_sql_customers contains an invalid Source DatasetSettings <null>
```

**Status**: Notebooks are created (202 Accepted), but pipeline deployment fails with validation error

**Cause**: The Copy Activity configuration generated by Claude AI is missing required dataset configuration fields that Fabric expects.

**Next Steps**:
1. Update Claude AI system prompt with detailed Copy Activity schema
2. Provide example Copy Activity configurations for different source types
3. Ensure all required fields are included (source, sink, datasetSettings)
4. Test with simplified pipeline (Notebook activities only) first

### 📋 Notebook Creation Status

**Response**: `202 Accepted` (Async operation in progress)

The Fabric API returns `202 Accepted` for notebook creation, which means:
- The request was accepted
- The notebook creation is happening asynchronously
- The actual creation may take a few seconds
- You need to poll or check the workspace to confirm creation

**Current Behavior**: The code treats `202` as an error because it expects `200/201` response. This needs to be fixed.

**Fix Required**:
```python
# Current code (incorrect):
if response.status_code == 201 or response.status_code == 200:
    # Success
else:
    # Error

# Should be:
if response.status_code in [200, 201, 202]:
    # Success (202 = accepted for async processing)
else:
    # Error
```

---

## Troubleshooting

### Issue 1: "Redirect URI mismatch" during login

**Symptom**: Azure AD error: "AADSTS50011: The redirect URI does not match"

**Solution**:
```bash
# Add the redirect URI to Azure AD app registration
az ad app update --id 0944e22d-d0f1-40c1-a9fc-f422c05949f3 \
  --web-redirect-uris http://localhost:3002
```

### Issue 2: CORS errors on API calls

**Symptom**: Browser console shows "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solution**:
1. Add frontend URL to `ALLOWED_ORIGINS` in backend `.env`
2. Restart backend server
3. Make sure `HTTPBearer(auto_error=False)` is set to handle OPTIONS requests

### Issue 3: SSL Certificate verification failed

**Symptom**: `[SSL: CERTIFICATE_VERIFY_FAILED]` when calling Microsoft APIs

**Solution**:
```bash
# Install/upgrade certifi
pip3 install --upgrade certifi

# Code should use certifi's certificates
import ssl
import certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())
```

### Issue 4: Token validation fails continuously

**Symptom**: Backend logs show repeated 401 errors, frontend keeps refreshing

**Solution**: Enable development mode in backend
```bash
# In backend/.env
DISABLE_AUTH=true
```

### Issue 5: Workspace dropdown is empty

**Symptom**: No workspaces appear in dropdown after login

**Possible Causes**:
1. User has no approved workspaces in database
2. Workspace Backend API is down
3. Field name mismatch in frontend code

**Solution**:
1. Check Workspace Backend is running: `curl https://fabric-pipeline-backend.delightfulplant-1c861d44.eastus.azurecontainerapps.io/api/workspaces`
2. In development mode, backend should return all workspaces
3. Verify frontend uses `workspace.name` (not `workspace.workspace_name`)

### Issue 6: Pipeline deployment fails with validation error

**Symptom**: `ActivityName contains an invalid Source DatasetSettings <null>`

**Current Status**: Known issue - Copy Activity configuration is missing required fields

**Temporary Workaround**:
1. Deploy pipeline structure only (without Copy activities)
2. Manually configure Copy activities in Fabric UI
3. Or generate pipelines with Notebook activities only

**Permanent Fix**: Update Claude AI prompt with complete Copy Activity schema

### Issue 7: Notebooks show as "failed" but actually created

**Symptom**: Backend logs show "Notebook creation failed: 202"

**Cause**: Code expects `200/201` but Fabric returns `202 Accepted` for async operations

**Solution**: Update `create_notebook` method to accept `202` status code

---

## Security Best Practices

### 1. Environment Variables

**Never commit `.env` files to Git!**

Add to `.gitignore`:
```
.env
*.env
.env.local
.env.production
```

### 2. Azure AD Permissions

- Use least privilege principle
- Separate dev and prod app registrations
- Rotate client secrets regularly (every 90 days)
- Use managed identities in production (no secrets needed)

### 3. Fabric API Access

- Service principal should only have Contributor role on specific workspaces
- Do not use personal accounts for service-to-service auth
- Monitor API usage and set up alerts for unusual activity

### 4. CORS Configuration

- In production, only allow specific frontend domain
- Do not use wildcard `*` for ALLOWED_ORIGINS
- Use HTTPS in production

### 5. Development Mode

- **Always set `DISABLE_AUTH=false` in production**
- Development mode bypasses all authentication
- Only use locally for testing

---

## Production Checklist

Before deploying to production:

- [ ] Set `DISABLE_AUTH=false` in backend
- [ ] Update `ALLOWED_ORIGINS` to production frontend URL only
- [ ] Use HTTPS for all services
- [ ] Rotate Azure AD client secret
- [ ] Set up monitoring and logging (Application Insights)
- [ ] Configure auto-scaling for Container Apps
- [ ] Set up backup for workspace access database
- [ ] Test authentication with real users
- [ ] Set up rate limiting on API endpoints
- [ ] Configure firewall rules for SQL database
- [ ] Enable diagnostic logs for Fabric API calls
- [ ] Set up alerts for deployment failures
- [ ] Document runbook for common issues
- [ ] Create separate app registration for production
- [ ] Request production Fabric capacity (F2+)

---

## Support & Resources

### Documentation Links

- [Microsoft Fabric REST API](https://learn.microsoft.com/en-us/rest/api/fabric/)
- [Claude AI API (Anthropic)](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [MSAL.js Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-js)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

### Contact Information

- **Pipeline Builder Team**: (Add your team email)
- **Azure Support**: (Add support ticket system)
- **Fabric Admin**: (Add Fabric workspace admin contact)

---

## Appendix

### A. Complete Backend API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Health check and API info | No |
| GET | `/health` | Health status | No |
| GET | `/api/workspaces` | List workspaces for user | Yes |
| POST | `/api/ai/chat` | Chat with Claude AI | Yes |
| POST | `/api/pipelines/generate` | Generate pipeline from requirements | Yes |
| POST | `/api/pipelines/{id}/deploy` | Deploy pipeline to Fabric | Yes |
| GET | `/api/pipelines` | List pipelines in workspace | Yes |
| POST | `/api/sources/validate` | Validate data source connection | Yes |

### B. Environment Variables Reference

#### Backend Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude AI API key | `sk-ant-api03-xxx` |
| `CLAUDE_MODEL` | Claude model version | `claude-3-5-sonnet-20241022` |
| `CLAUDE_MAX_TOKENS` | Max tokens per request | `16000` |
| `FABRIC_CLIENT_ID` | Azure AD app client ID | `0944e22d-d0f1-40c1-a9fc-f422c05949f3` |
| `FABRIC_CLIENT_SECRET` | Azure AD app secret | `your-secret-here` |
| `FABRIC_TENANT_ID` | Azure AD tenant ID | `e28d23e3-803d-418d-a720-c0bed39f77b6` |
| `WORKSPACE_BACKEND_URL` | Workspace API URL | `https://fabricbackend...` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3002` |
| `DISABLE_AUTH` | Dev mode auth bypass | `true` or `false` |

#### Frontend Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8001` |
| `REACT_APP_CLIENT_ID` | Azure AD client ID | `0944e22d-...` |
| `REACT_APP_TENANT_ID` | Azure AD tenant ID | `e28d23e3-...` |
| `REACT_APP_REDIRECT_URI` | OAuth redirect URI | `http://localhost:3002` |

### C. Fabric Pipeline Activity Schema Examples

#### Copy Activity (SQL to Lakehouse)

```json
{
  "name": "CopyFromAzureSQL",
  "type": "Copy",
  "typeProperties": {
    "source": {
      "type": "AzureSqlSource",
      "sqlReaderQuery": "SELECT * FROM customers"
    },
    "sink": {
      "type": "LakehouseTableSink",
      "tableActionOption": "Overwrite"
    },
    "enableStaging": false
  },
  "inputs": [
    {
      "referenceName": "AzureSqlTable",
      "type": "DatasetReference"
    }
  ],
  "outputs": [
    {
      "referenceName": "LakehouseTable",
      "type": "DatasetReference"
    }
  ]
}
```

#### Notebook Activity

```json
{
  "name": "TransformData",
  "type": "SynapseNotebook",
  "typeProperties": {
    "notebook": {
      "referenceName": "silver_customer_processing",
      "type": "NotebookReference"
    },
    "parameters": {
      "input_table": "bronze_customers",
      "output_table": "silver_customers"
    }
  },
  "dependsOn": [
    {
      "activity": "CopyFromAzureSQL",
      "dependencyConditions": ["Succeeded"]
    }
  ]
}
```

---

**Last Updated**: 2025-10-14

**Version**: 1.0

**Authors**: Pipeline Builder Team
`