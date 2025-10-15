# OneLake Shortcuts Implementation Guide

**Status**: ✅ **Production Ready**
**Date**: 2025-10-15
**Version**: 1.0

---

## 🎯 Overview

This guide explains how to use OneLake shortcuts with Data Pipelines in Microsoft Fabric to copy data from external sources (Azure Blob Storage, S3, ADLS) to Lakehouse tables.

### Architecture

```
Azure Blob Storage (External Source)
    ↓ [Fabric Connection with Account Key]
OneLake Shortcut (Virtual Access in Lakehouse Files)
    ↓ [Copy Activity in Data Pipeline]
Lakehouse Table (Target)
```

### Benefits

- ✅ **No data duplication** - Shortcut provides virtual access
- ✅ **No "invalid reference" errors** - Copy Activity works within Lakehouse
- ✅ **No Azure Key Vault needed** - Connection handles authentication
- ✅ **Reusable shortcuts** - Use across multiple pipelines
- ✅ **Access entire containers or subfolders** - Flexible configuration

---

## 🚀 Quick Start

### Prerequisites

1. Microsoft Fabric workspace
2. Lakehouse created in workspace
3. Azure Blob Storage account with data
4. Storage account connection string or account key

### Run the Production Script

```bash
cd backend
python3 deploy_shortcut_pipeline_production.py
```

**What it does:**
1. Creates Connection to Azure Blob Storage
2. Creates OneLake Shortcut in Lakehouse Files
3. Creates Data Pipeline with Copy Activity

---

## 📋 Step-by-Step Guide

### Step 1: Configure Settings

Edit `deploy_shortcut_pipeline_production.py`:

```python
# Fabric Workspace and Lakehouse
WORKSPACE_ID = "your-workspace-id"
LAKEHOUSE_ID = "your-lakehouse-id"

# Azure Blob Storage
CONNECTION_NAME = "AzureBlob_Production"
STORAGE_ACCOUNT_NAME = "yourstorageaccount"
STORAGE_ACCOUNT_KEY = "your-account-key"
BLOB_CONTAINER = "your-container-name"

# Shortcut
SHORTCUT_NAME = "azure_blob_data"
SHORTCUT_SUBPATH = ""  # Empty = entire container

# Pipeline
PIPELINE_NAME = "Pipeline_AzureBlob_To_Lakehouse"
TARGET_TABLE_NAME = "your_target_table"
```

### Step 2: Run Deployment

```bash
python3 deploy_shortcut_pipeline_production.py
```

**Expected Output:**
```
✅ Connection created successfully!
✅ Shortcut created successfully!
✅ Pipeline created successfully!
```

### Step 3: Verify in Fabric UI

1. **Check Shortcut:**
   - Open Lakehouse → Files
   - You should see folder: `azure_blob_data`
   - Click on it → see data from Azure Blob Storage

2. **Run Pipeline:**
   - Go to Pipelines
   - Find: `Pipeline_AzureBlob_To_Lakehouse`
   - Click **Run**

3. **Verify Data:**
   - Go to Lakehouse → Tables
   - Check `your_target_table`
   - Data should be copied from blob storage

---

## 🔧 Configuration Options

### Connection Authentication Methods

#### Option 1: Account Key (Recommended for Production)
```python
connection_config={
    "account_name": "storageaccount",
    "account_key": "your-account-key",
    "auth_type": "Key"
}
```

#### Option 2: Service Principal
```python
connection_config={
    "account_name": "storageaccount",
    "auth_type": "ServicePrincipal"
    # Uses credentials from config.py
}
```

**Note**: Service Principal requires Azure RBAC "Storage Blob Data Reader" role on storage account.

### Shortcut Path Options

#### Access Entire Container
```python
SHORTCUT_SUBPATH = ""  # or "/"
```
Result: `Files/shortcut_name/` contains all container data

#### Access Specific Subfolder
```python
SHORTCUT_SUBPATH = "subfolder_name"
```
Result: `Files/shortcut_name/` contains only subfolder data

### Copy Activity Options

#### Copy All CSV Files (Default)
```python
"wildcardFileName": "*.csv"
```

#### Copy Specific Files
```python
"wildcardFileName": "sales_*.csv"
```

#### Copy All File Types
```python
"wildcardFileName": "*"
```

---

## 📂 Project Structure

```
backend/
├── services/
│   └── fabric_api_service.py
│       ├── create_connection()           # Creates Fabric connection
│       ├── create_onelake_shortcut()     # Creates shortcut
│       └── create_pipeline()             # Creates pipeline
│
├── deploy_shortcut_pipeline_production.py  # ✅ USE THIS (Production)
├── deploy_shortcut_pipeline.py             # Testing version (with timestamps)
│
├── docs/
│   ├── ONELAKE_SHORTCUT_GUIDE.md          # This file
│   └── ONELAKE_SHORTCUT_SUMMARY.md        # Implementation summary
│
└── config.py                               # Configuration and credentials
```

---

## 🔑 Key Implementation Details

### 1. Connection Creation

**Endpoint:**
```
POST https://api.fabric.microsoft.com/v1/connections
```

**Key Points:**
- Global endpoint (not workspace-specific)
- Field name: `servicePrincipalSecret` (not `servicePrincipalKey`)
- Account Key authentication works without Azure RBAC

### 2. OneLake Shortcut Creation

**Endpoint:**
```
POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/items/{lakehouseId}/shortcuts
```

**Payload Structure:**
```json
{
  "path": "Files",
  "name": "shortcut_name",
  "target": {
    "adlsGen2": {
      "connectionId": "connection-guid",
      "location": "https://storageaccount.dfs.core.windows.net/container",
      "subpath": "/"
    }
  }
}
```

**Important:**
- `path`: Parent folder ("Files" or "Tables")
- `name`: Shortcut name (separate from path)
- Result: Creates `Files/shortcut_name` (NOT `Files/Files/shortcut_name`)

### 3. Copy Activity Configuration

**Source:**
- Type: `LakehouseReadSettings`
- Folder Path: Shortcut name (e.g., "azure_blob_data")
- Wildcard: `*.csv` or other pattern

**Sink:**
- Type: `LakehouseTableSink`
- Table Action: `Append` or `Overwrite`
- Table Name: Target table name

---

## ❓ Troubleshooting

### Connection Creation Fails (404)

**Error**: `EntityNotFound: The requested resource could not be found`

**Solution**:
- Endpoint should be `/v1/connections` (not `/workspaces/{id}/connections`)
- Already fixed in code

### Connection Creation Fails (400 - Missing Field)

**Error**: `The ServicePrincipalSecret field is required`

**Solution**:
- Use `servicePrincipalSecret` not `servicePrincipalKey`
- Already fixed in code

### Shortcut Creation Fails (403 - Unauthorized)

**Error**: `Access to target location denied`

**Causes:**
1. **Service Principal**: Needs Azure RBAC "Storage Blob Data Reader"
2. **Account Key**: Wrong key or key expired

**Solutions:**
1. Use Account Key authentication (recommended)
2. Grant Azure RBAC role to service principal:
   ```bash
   az role assignment create \
     --role "Storage Blob Data Reader" \
     --assignee <service-principal-id> \
     --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>
   ```

### Shortcut Shows Duplicate Folders

**Problem**: Seeing `Files/shortcut/shortcut/data`

**Cause**: Path parameter included folder name

**Solution**:
- Set `path = "Files"` and `name = "shortcut_name"` separately
- Already fixed in code

### Pipeline Fails to Read Shortcut

**Error**: Cannot find data in shortcut folder

**Causes:**
1. Shortcut created but path is wrong
2. Source data doesn't match wildcard pattern
3. File format mismatch

**Solutions:**
1. Verify shortcut path: `Files/{SHORTCUT_NAME}`
2. Check wildcard pattern matches files
3. Update format settings in Copy Activity

---

## 🌟 Advanced Usage

### Multiple Shortcuts from Different Sources

```python
# Shortcut 1: Azure Blob
await fabric_service.create_onelake_shortcut(
    shortcut_name="azure_blob_data",
    connection_id=blob_connection_id,
    shortcut_config={
        "target_type": "AzureBlob",
        "storage_account": "account1",
        "container": "data"
    }
)

# Shortcut 2: Amazon S3
await fabric_service.create_onelake_shortcut(
    shortcut_name="s3_data",
    connection_id=s3_connection_id,
    shortcut_config={
        "target_type": "S3",
        "bucket": "my-bucket",
        "region": "us-east-1"
    }
)
```

### Subfolder-Specific Shortcuts

```python
# Shortcut to specific subfolder
shortcut_config={
    "target_type": "AzureBlob",
    "storage_account": "storageaccount",
    "container": "data",
    "folder_path": "sales/2024"  # Only this subfolder
}
```

### Pipeline with Multiple Activities

Add transformation activities after Copy:

```python
pipeline_definition = {
    "properties": {
        "activities": [
            copy_activity,       # Copy from shortcut
            notebook_activity,   # Transform data
            another_copy_activity  # Write to gold layer
        ]
    }
}
```

---

## 📊 Comparison: CopyJob vs OneLake Shortcut

| Feature | CopyJob API | OneLake Shortcut + Pipeline |
|---------|-------------|----------------------------|
| Data Movement | ✅ Direct copy | ✅ Via shortcut |
| External Sources | ✅ Direct | ✅ Via shortcut |
| Lakehouse Integration | ❌ Separate | ✅ Native |
| Reusability | ❌ One-time | ✅ Reusable |
| Visibility in UI | ❌ Limited | ✅ Clear structure |
| Permission Model | Complex | ✅ Simple |
| Best For | Batch ETL jobs | Data lake integration |

**Recommendation**: Use OneLake Shortcuts for most scenarios.

---

## 🔐 Security Best Practices

### 1. Store Credentials Securely

**Don't:**
```python
STORAGE_ACCOUNT_KEY = "hardcoded-key"  # ❌ Never commit to Git
```

**Do:**
```python
import os
STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_KEY")  # ✅ From environment
```

### 2. Use Service Principal in Production

For automated deployments:
```python
connection_config={
    "auth_type": "ServicePrincipal",
    "tenant_id": os.getenv("AZURE_TENANT_ID"),
    "client_id": os.getenv("AZURE_CLIENT_ID"),
    "client_secret": os.getenv("AZURE_CLIENT_SECRET")
}
```

### 3. Apply Least Privilege

Grant only necessary permissions:
- Azure: **Storage Blob Data Reader** (not Contributor)
- Fabric: **Workspace Viewer** + item-specific permissions

---

## 📚 Additional Resources

### Microsoft Documentation
- [OneLake Shortcuts Overview](https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts)
- [OneLake Shortcuts REST API](https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-shortcuts/create-shortcut)
- [Fabric Connections API](https://learn.microsoft.com/en-us/rest/api/fabric/core/connections/create-connection)

### Internal Documentation
- `ONELAKE_SHORTCUT_SUMMARY.md` - Implementation summary
- `IMPLEMENTATION_SUMMARY.md` - Activity hierarchy decisions
- `README.md` - Project overview

---

## 🎓 Key Learnings

### Connection API
✅ Endpoint: `/v1/connections` (global, not workspace-specific)
✅ Auth Field: `servicePrincipalSecret` (not `servicePrincipalKey`)
✅ Account Key works without Azure RBAC

### Shortcut API
✅ Path Format: `path="Files"` + `name="shortcut_name"` separately
✅ Target Format: Nested object with `adlsGen2` or `amazonS3` key
✅ Location: Use `.dfs.core.windows.net` endpoint (not `.blob`)
✅ Subpath: Use `/` for entire container

### Copy Activity
✅ Source Type: `LakehouseReadSettings` (not external connection)
✅ Folder Path: Points to shortcut name
✅ Dataset Settings: Inline Lakehouse linked service

---

## ✅ Production Checklist

Before deploying to production:

- [ ] Update all IDs in config (workspace, lakehouse)
- [ ] Set connection string from environment variable
- [ ] Choose meaningful names (not timestamps)
- [ ] Test shortcut appears in Lakehouse UI
- [ ] Run pipeline manually and verify data
- [ ] Check table has expected row count
- [ ] Set up pipeline schedule if needed
- [ ] Document source data location
- [ ] Add monitoring/alerting
- [ ] Review and approve in Fabric UI

---

## 🆘 Support

**Issues?**
1. Check troubleshooting section above
2. Review error messages in logs
3. Verify configuration values
4. Test in Fabric UI manually first

**Success?**
- Connection created ✅
- Shortcut visible in Files ✅
- Pipeline runs successfully ✅
- Data appears in table ✅

---

**Version**: 1.0
**Status**: Production Ready ✅
**Last Updated**: 2025-10-15
**Author**: Claude Code
