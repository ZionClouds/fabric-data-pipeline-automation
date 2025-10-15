# Quick Reference Guide: Activity Selection

**Last Updated**: 2025-10-15

---

## Which Activity Should I Use?

### ✅ Copying from External Source to Lakehouse (Simple Copy)

**Use**: **CopyJob API** (PRIMARY)

**Run**:
```bash
cd backend
python deploy_copy_pipeline_updated.py
```

**Code**:
```python
from services.fabric_api_service import FabricAPIService

fabric_service = FabricAPIService()

result = await fabric_service.create_copy_job(
    workspace_id="YOUR_WORKSPACE_ID",
    copy_job_name="Blob_To_Lakehouse",
    connection_id="YOUR_CONNECTION_ID",
    source_config={
        "container": "your-container",
        "wildcardFileName": "*.csv",
        "recursive": True
    },
    sink_config={
        "workspaceId": "YOUR_WORKSPACE_ID",
        "lakehouseId": "YOUR_LAKEHOUSE_ID",
        "tableName": "target_table",
        "tableAction": "Append"
    }
)
```

**Supported Sources**:
- Azure Blob Storage
- Azure Data Lake Storage Gen2
- Azure SQL Database
- SQL Server
- Any source with Fabric Connection

---

### ✅ Complex Transformations (Joins, Aggregations)

**Use**: **Data Flow Activity** (PRIORITY #2)

**Status**: 🚧 **Not Yet Implemented**

**Fallback**: Use Notebook Activity
```bash
cd backend
python deploy_copy_pipeline_notebook.py
```

---

### ✅ Lakehouse Files to Lakehouse Table

**Use**: **Data Pipeline Copy Activity**

**Code**: See `knowledge/DATA_PIPELINE_STRUCTURE_REFERENCE.md`

**Note**: Only works for Lakehouse-to-Lakehouse, NOT external sources

---

### ✅ Very Complex Logic / Custom Code

**Use**: **Notebook Activity** (BACKUP)

**Run**:
```bash
cd backend
python deploy_copy_pipeline_notebook.py
```

**Use Cases**:
- Custom business logic
- Machine learning preprocessing
- Complex validation rules
- API integrations

---

## Decision Tree

```
What are you trying to do?
│
├─ Copy from Azure Blob/SQL/External → Lakehouse (simple)
│  └─ Use CopyJob API ✅ (deploy_copy_pipeline_updated.py)
│
├─ Complex transformations (joins, aggregations, pivots)
│  └─ Use Data Flow ⚠️ (Not yet implemented)
│     └─ Fallback: Notebook (deploy_copy_pipeline_notebook.py)
│
├─ Lakehouse Files → Lakehouse Table
│  └─ Use Data Pipeline Copy Activity ✅
│
└─ Very complex custom logic
   └─ Use Notebook Activity ✅ (deploy_copy_pipeline_notebook.py)
```

---

## Files to Use

| Task | File | Status |
|------|------|--------|
| External → Lakehouse (simple) | `deploy_copy_pipeline_updated.py` | ✅ Use This |
| Complex transformations | Data Flow (TBD) | 🚧 Not Yet |
| Very complex logic | `deploy_copy_pipeline_notebook.py` | ✅ Backup |
| Lakehouse → Lakehouse | `deploy_copy_pipeline.py` | ✅ Limited |

---

## Files to AVOID

| File | Why Avoid | Alternative |
|------|-----------|-------------|
| `deploy_copy_pipeline.py` (for external sources) | Copy Activity doesn't work with external connections | Use `deploy_copy_pipeline_updated.py` |

---

## Key Limitations

### ❌ Data Pipeline Copy Activity Limitations
- Cannot reference Fabric Connection objects by GUID
- Requires Azure Key Vault for external sources
- Only works for Lakehouse-to-Lakehouse

### ✅ CopyJob API Advantages
- Direct connection ID reference
- Works with external sources
- No Azure Key Vault required
- Simple structure

---

## Common Errors

### Error: "invalid reference '372a9195-...'"
**Cause**: Trying to use Connection GUID in Data Pipeline
**Fix**: Use CopyJob API instead

### Error: "'SecretName' cannot be null"
**Cause**: Trying to embed credentials in Data Pipeline
**Fix**: Use CopyJob API or Azure Key Vault

---

## Documentation Index

- **Activity Hierarchy**: `backend/docs/ACTIVITY_HIERARCHY_AND_USAGE.md`
- **Implementation Summary**: `backend/docs/IMPLEMENTATION_SUMMARY.md`
- **Pipeline Structure**: `knowledge/DATA_PIPELINE_STRUCTURE_REFERENCE.md`
- **Testing Results**: `knowledge/DATA_PIPELINE_CREATION_RESULTS.md`
- **Deployment Guide**: `backend/docs/DEPLOYMENT_GUIDE.md`

---

## Quick Commands

```bash
# Deploy CopyJob (Primary for external sources)
cd backend && python deploy_copy_pipeline_updated.py

# Deploy Notebook (Backup for complex logic)
cd backend && python deploy_copy_pipeline_notebook.py

# List all documentation
find backend/docs -name "*.md" -type f

# Check implementation status
cat backend/docs/IMPLEMENTATION_SUMMARY.md
```

---

## Support

For detailed information:
1. Read `backend/docs/ACTIVITY_HIERARCHY_AND_USAGE.md`
2. Check `backend/docs/IMPLEMENTATION_SUMMARY.md`
3. Review code in `backend/services/fabric_api_service.py`

---

**Author**: Claude Code
**Date**: 2025-10-15
**Version**: 1.0
