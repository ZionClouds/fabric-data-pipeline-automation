# Microsoft Fabric Data Pipeline Automation - Backend

Automated deployment and management of Microsoft Fabric data pipelines using Python and REST APIs.

**Current Approach**: OneLake Shortcuts + Copy Activity ✅

---

## 🚀 Quick Start

### Deploy Complete Solution (Connection + Shortcut + Pipeline)
```bash
cd backend
python3 deploy_shortcut_pipeline_production.py
```

### Deploy Pipeline Only (Use existing shortcut)
```bash
cd backend
python3 deploy_pipeline_only.py
```

---

## 📋 Current Approach: OneLake Shortcuts + Copy Activity

**Status**: ✅ **Production Ready**

### Architecture

```
Azure Blob Storage (External Source)
    ↓ [Fabric Connection - Account Key]
OneLake Shortcut (Virtual Access in Lakehouse Files)
    ↓ [Copy Activity in Data Pipeline]
Lakehouse Table (Target)
```

### ✅ Benefits

- **No data duplication** - Shortcut provides virtual access
- **No "invalid reference" errors** - Copy Activity works within Lakehouse
- **No Azure Key Vault needed** - Connection handles authentication
- **Reusable shortcuts** - Use across multiple pipelines
- **Error handling** - Skip incompatible CSV rows automatically
- **Clean structure** - Single folder (no nesting)

### 📄 Main Scripts

1. **`deploy_shortcut_pipeline_production.py`** - Complete deployment (Connection + Shortcut + Pipeline)
2. **`deploy_pipeline_only.py`** - Quick pipeline deployment (uses existing shortcut)

### 📖 Documentation

- **`docs/ONELAKE_SHORTCUT_GUIDE.md`** - Complete user guide
- **`docs/DEPLOYMENT_SUCCESS_SUMMARY.md`** - Implementation summary
- **`docs/ONELAKE_SHORTCUT_SUMMARY.md`** - Technical details
- **`docs/CLEANUP_SUMMARY.md`** - Backend cleanup details

---

## 📁 Project Structure

```
backend/
├── services/
│   └── fabric_api_service.py                 # Main API service
│       ├── create_connection()               # ✅ Create Fabric connections
│       ├── create_onelake_shortcut()         # ✅ Create OneLake shortcuts
│       ├── create_pipeline()                 # ✅ Create data pipelines
│       └── create_notebook()                 # ✅ Create notebooks
│
├── deploy_shortcut_pipeline_production.py    # ✅ MAIN SCRIPT (Production)
├── deploy_pipeline_only.py                   # ✅ Quick pipeline deployment
├── main.py                                   # Backend API server
├── config.py                                 # Configuration
│
├── docs/
│   ├── ONELAKE_SHORTCUT_GUIDE.md            # Complete usage guide
│   ├── DEPLOYMENT_SUCCESS_SUMMARY.md        # Success summary
│   ├── ONELAKE_SHORTCUT_SUMMARY.md          # Technical details
│   ├── QUICK_REFERENCE.md                   # Quick reference
│   └── ACTIVITY_HIERARCHY_AND_USAGE.md      # Activity decisions
│
└── README.md                                 # This file
```

---

## 🎯 Which Script Should I Use?

### New Deployment (First Time)
**✅ Use**: `deploy_shortcut_pipeline_production.py`

Creates:
1. Connection to Azure Blob Storage
2. OneLake Shortcut in Lakehouse Files
3. Data Pipeline with Copy Activity

```bash
python3 deploy_shortcut_pipeline_production.py
```

**Before running**: Edit configuration in the file:
- Workspace ID, Lakehouse ID
- Storage account name and key
- Shortcut name, Pipeline name

---

### Pipeline Only (Shortcut Already Exists)
**✅ Use**: `deploy_pipeline_only.py`

Creates only the pipeline, uses existing shortcut and connection.

```bash
python3 deploy_pipeline_only.py
```

**When to use**:
- Shortcut already created
- Need different pipeline configuration
- Testing different Copy Activity settings

---

## 🔧 API Service Methods

### `create_copy_job()` - PRIMARY METHOD
```python
from services.fabric_api_service import FabricAPIService

fabric_service = FabricAPIService()

result = await fabric_service.create_copy_job(
    workspace_id="c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb",
    copy_job_name="Blob_To_Lakehouse",
    connection_id="372a9195-6f23-48bf-b664-3725fa6ac3f6",
    source_config={
        "container": "fabric",
        "wildcardFileName": "*.csv",
        "recursive": True
    },
    sink_config={
        "workspaceId": "c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb",
        "lakehouseId": "5bb4039e-fe83-4a78-a314-145ce103cc64",
        "tableName": "bronze_amazon_products",
        "tableAction": "Append"
    }
)
```

**Location**: `services/fabric_api_service.py:292-420`

---

## ⚠️ Known Limitations

### Data Pipeline Copy Activity Cannot Use External Connections

**Error**: `"invalid reference '372a9195-6f23-48bf-b664-3725fa6ac3f6'"`

**Reason**: Microsoft Fabric has TWO incompatible connection models:

| Model | Used By | Supports External Sources |
|-------|---------|--------------------------|
| **Connections API** | CopyJob | ✅ Yes (via connectionId) |
| **LinkedServices** | Data Pipeline | ❌ Requires Azure Key Vault |

**Solution**: Use CopyJob API for external sources

**Details**: See `docs/ACTIVITY_HIERARCHY_AND_USAGE.md`

---

## 📚 Documentation

### Quick Reference
📄 `docs/QUICK_REFERENCE.md` - Fast decision guide

### Comprehensive Guides
📄 `docs/ACTIVITY_HIERARCHY_AND_USAGE.md` - Complete activity guide
📄 `docs/IMPLEMENTATION_SUMMARY.md` - Implementation details
📄 `docs/DEPLOYMENT_GUIDE.md` - Step-by-step deployment

### Knowledge Base
📄 `../knowledge/DATA_PIPELINE_STRUCTURE_REFERENCE.md` - Pipeline structure
📄 `../knowledge/DATA_PIPELINE_CREATION_RESULTS.md` - Testing results

---

## 🧪 Testing Results

### ✅ Successful Deployments

**CopyJob**: Azure Blob Storage → Lakehouse
- ID: `2d3f2b4d-e519-4d74-8932-ad4b4d3b738e`
- Name: `AmazonData_BlobToLakehouse`
- Status: ✅ Working

**Data Pipeline**: Lakehouse Files → Lakehouse Table
- ID: `93557a42-669e-4215-a01b-cd5eb4e0573a`
- Name: `DataPipeline_BlobToLakehouse_Amazon`
- Status: ✅ Working

**Connection**: Azure Blob Storage
- ID: `372a9195-6f23-48bf-b664-3725fa6ac3f6`
- Name: `BlobStorage_fabricsatest123`
- Status: ✅ Working with CopyJob

---

### ❌ Failed Attempts

**Data Pipeline Copy Activity**: Azure Blob Storage → Lakehouse
- Error: `"invalid reference 'blobstorage_fabricsatest123'"`
- Reason: Cannot reference Fabric Connections
- Solution: Use CopyJob API instead

---

## 📝 Configuration

### Environment Setup
1. Copy `.env.example` to `.env`
2. Configure your Fabric credentials:
   ```
   FABRIC_TENANT_ID=your-tenant-id
   FABRIC_CLIENT_ID=your-client-id
   FABRIC_CLIENT_SECRET=your-client-secret
   FABRIC_WORKSPACE_ID=your-workspace-id
   ```

### Workspace Configuration
Edit the deployment scripts with your workspace details:
- `WORKSPACE_ID`: Your Fabric workspace GUID
- `LAKEHOUSE_ID`: Your Lakehouse item GUID
- Connection credentials (for Blob Storage, SQL, etc.)

---

## 🚦 Next Steps

### Immediate (Priority 1) ✅ **COMPLETED**
- [x] Implement CopyJob API support
- [x] Update deployment scripts
- [x] Document activity hierarchy

### Short Term (Priority 2)
- [ ] **Implement Data Flow activity support** ← **NEXT PRIORITY**
- [ ] Add activity selection logic
- [ ] Create tests for each activity type

### Long Term (Priority 3)
- [ ] Azure Key Vault integration
- [ ] UI for activity type selection
- [ ] Monitoring and logging

---

## 🐛 Common Errors & Solutions

### Error: "invalid reference '372a9195-...'"
**Cause**: Trying to use Connection GUID in Data Pipeline
**Fix**: Use CopyJob API instead (`deploy_copy_pipeline_updated.py`)

### Error: "'SecretName' cannot be null"
**Cause**: Trying to embed credentials in Data Pipeline
**Fix**: Use CopyJob API or setup Azure Key Vault

### Error: "ItemDisplayNameNotAvailableYet"
**Cause**: Name conflict with recently deleted item
**Fix**: Use a different name or wait a few minutes

---

## 🤝 Contributing

When adding new features:
1. Follow the activity priority hierarchy
2. Add comprehensive docstrings
3. Update documentation in `docs/`
4. Add examples to deployment scripts

---

## 📞 Support

For questions or issues:
1. Check `docs/QUICK_REFERENCE.md`
2. Review `docs/ACTIVITY_HIERARCHY_AND_USAGE.md`
3. Examine code in `services/fabric_api_service.py`

---

**Last Updated**: 2025-10-15
**Version**: 1.0
**Status**: ✅ Production Ready (CopyJob API)
