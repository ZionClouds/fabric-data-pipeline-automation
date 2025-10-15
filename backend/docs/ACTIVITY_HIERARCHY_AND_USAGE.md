# Fabric Pipeline Activity Hierarchy and Usage Guide

## Overview

This document defines the recommended hierarchy for using different activity types in Microsoft Fabric pipelines, based on real-world testing and API limitations discovered during implementation.

**Last Updated**: 2025-10-15
**Testing Workspace**: soaham-test (c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb)

---

## Activity Priority Hierarchy

### 1. **CopyJob API** (Primary for External Sources)
**Use When**: Copying data from external sources to Lakehouse

**Supported Sources**:
- Azure Blob Storage ✅
- Azure Data Lake Storage Gen2 ✅
- Azure SQL Database ✅
- SQL Server ✅
- Other external sources with Fabric Connections

**Advantages**:
- ✅ Direct connection ID reference (no complex setup)
- ✅ Works with Fabric Connections API
- ✅ Simple, flat structure (sources[], sinks[], mappings[])
- ✅ Optimized for data movement
- ✅ Proven working in production

**Example**:
```python
await fabric_service.create_copy_job(
    workspace_id=WORKSPACE_ID,
    copy_job_name="Blob_To_Lakehouse",
    connection_id="372a9195-6f23-48bf-b664-3725fa6ac3f6",
    source_config={
        "container": "fabric",
        "wildcardFileName": "*.csv",
        "recursive": True
    },
    sink_config={
        "workspaceId": WORKSPACE_ID,
        "lakehouseId": LAKEHOUSE_ID,
        "tableName": "target_table",
        "tableAction": "Append"
    }
)
```

**Files**:
- Implementation: `services/fabric_api_service.py:create_copy_job()`
- Deployment Script: `backend/deploy_copy_pipeline_updated.py`

---

### 2. **Data Flow Activity** (For Complex Transformations)
**Use When**: Complex transformations, joins, aggregations needed

**Supported Operations**:
- Multiple source joins
- Aggregations, pivots, unpivots
- Derived columns, conditional splits
- Data type conversions
- Data quality rules

**Advantages**:
- ✅ Visual transformation designer in Fabric UI
- ✅ No code required for transformations
- ✅ Optimized for ETL operations
- ✅ Built-in data profiling

**Status**: 🚧 **Not Yet Implemented**

**Planned Implementation**:
```python
# TODO: Add to fabric_api_service.py
async def create_data_flow(
    self,
    workspace_id: str,
    data_flow_name: str,
    source_config: Dict[str, Any],
    transformations: List[Dict[str, Any]],
    sink_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a Data Flow for complex transformations"""
    pass
```

**Priority**: HIGH - Implement after CopyJob is stable

---

### 3. **Data Pipeline Copy Activity** (For Lakehouse-to-Lakehouse)
**Use When**: Copying between Lakehouse tables (internal)

**Supported Sources/Sinks**:
- Lakehouse Files → Lakehouse Table ✅
- Lakehouse Table → Lakehouse Table ✅
- External sources → Lakehouse ❌ (Use CopyJob instead)

**Advantages**:
- ✅ Part of orchestrated workflows
- ✅ Can have dependencies on other activities
- ✅ Works with embedded linkedService for Lakehouse

**Limitations**:
- ❌ **Does NOT support external source connections**
- ❌ Cannot reference Fabric Connection objects by GUID
- ❌ Requires Azure Key Vault for external sources
- ❌ Complex nested structure (datasetSettings)

**Example** (Lakehouse-to-Lakehouse only):
```python
pipeline_definition = {
    "properties": {
        "activities": [{
            "name": "Copy_Files_To_Table",
            "type": "Copy",
            "typeProperties": {
                "source": {
                    "type": "DelimitedTextSource",
                    "datasetSettings": {
                        "linkedService": {
                            "name": "lakehouse",
                            "properties": {
                                "type": "Lakehouse",
                                "typeProperties": {
                                    "workspaceId": WORKSPACE_ID,
                                    "artifactId": LAKEHOUSE_ID,
                                    "rootFolder": "Files"
                                }
                            }
                        }
                    }
                },
                "sink": {
                    "type": "LakehouseTableSink",
                    "tableActionOption": "Append"
                }
            }
        }]
    }
}
```

**Files**:
- Implementation: `services/fabric_api_service.py:create_pipeline()`
- Example: `knowledge/DATA_PIPELINE_STRUCTURE_REFERENCE.md`

---

### 4. **Notebook Activity** (Backup for Complex Logic)
**Use When**: Very complex transformations, custom logic, ML preprocessing

**Use Cases**:
- Custom business logic not supported by Copy or Data Flow
- Machine learning preprocessing
- Complex data validation rules
- API calls, custom integrations
- Fallback when Copy Activity doesn't work

**Advantages**:
- ✅ Full PySpark capabilities
- ✅ Access to all Spark libraries
- ✅ Can handle credentials directly
- ✅ Complete flexibility

**Disadvantages**:
- ❌ Requires Spark runtime (slower startup)
- ❌ Code maintenance overhead
- ❌ Credentials embedded in code (can parameterize)
- ❌ Less optimized than native activities

**Example**:
```python
notebook_code = """
# Configure blob storage access
spark.conf.set(
    f"fs.azure.account.key.{account_name}.blob.core.windows.net",
    account_key
)

# Read CSV from blob
blob_path = f"wasbs://{container}@{account_name}.blob.core.windows.net/{file}"
df = spark.read.format("csv").option("header", "true").load(blob_path)

# Write to lakehouse
df.write.mode("append").format("delta").saveAsTable("target_table")
"""

await fabric_service.create_notebook(
    workspace_id=WORKSPACE_ID,
    notebook_name="Copy_Blob_To_Lakehouse",
    notebook_code=notebook_code
)
```

**Files**:
- Implementation: `services/fabric_api_service.py:create_notebook()`
- Deployment Script: `backend/deploy_copy_pipeline_notebook.py`

---

## Decision Tree

```
Need to copy data from external source to Lakehouse?
│
├─ YES
│  │
│  ├─ Is it a simple copy (no complex transformations)?
│  │  │
│  │  ├─ YES → Use CopyJob API ✅ (Primary Choice)
│  │  │
│  │  └─ NO → Need transformations?
│  │     │
│  │     ├─ Standard ETL (joins, aggregations) → Use Data Flow ✅
│  │     │
│  │     └─ Very complex/custom logic → Use Notebook Activity ⚠️
│  │
│  └─ Is it Lakehouse Files → Lakehouse Table?
│     │
│     └─ YES → Use Data Pipeline Copy Activity ✅
│
└─ NO (Orchestration workflow with multiple steps)
   │
   └─ Use Data Pipeline with multiple activities
      (Notebook → Data Flow → Copy → etc.)
```

---

## Implementation Status

| Activity Type | Status | API Support | Use Case | Files |
|--------------|--------|-------------|----------|-------|
| **CopyJob** | ✅ Implemented | Full | External → Lakehouse | `deploy_copy_pipeline_updated.py` |
| **Data Flow** | 🚧 Planned | Not Yet | Complex transformations | TBD |
| **Pipeline Copy** | ✅ Partial | Lakehouse only | Lakehouse → Lakehouse | `deploy_copy_pipeline.py` (deprecated) |
| **Notebook** | ✅ Implemented | Full | Complex logic | `deploy_copy_pipeline_notebook.py` |

---

## Known Limitations

### Data Pipeline Copy Activity Cannot Use External Connections

**Error**: `"invalid reference '372a9195-6f23-48bf-b664-3725fa6ac3f6'"`

**Reason**: Data Pipelines use a different connection model than the Fabric Connections API

**Workaround**: Use CopyJob API instead

**Details**: See `knowledge/DATA_PIPELINE_CREATION_RESULTS.md`

### Fabric Has Two Incompatible Connection Models

| Model | Used By | Supports External Sources |
|-------|---------|--------------------------|
| **Connections API** | CopyJob, Items | ✅ Yes (via connectionId) |
| **LinkedServices** | Data Pipeline | ❌ Requires Azure Key Vault |

**Recommendation**: Use CopyJob for external sources, Data Pipeline for internal Lakehouse operations

---

## Code Examples by Scenario

### Scenario 1: Azure Blob Storage → Lakehouse (Simple Copy)
**✅ Use**: CopyJob API

```bash
python backend/deploy_copy_pipeline_updated.py
```

### Scenario 2: Complex ETL with Joins and Aggregations
**✅ Use**: Data Flow (when implemented)

```python
# TODO: Implement Data Flow support
# For now, use Notebook as fallback
python backend/deploy_copy_pipeline_notebook.py
```

### Scenario 3: Lakehouse Files → Lakehouse Table
**✅ Use**: Data Pipeline Copy Activity

```python
# Use existing Data Pipeline deployment
# See: knowledge/DATA_PIPELINE_STRUCTURE_REFERENCE.md
```

### Scenario 4: Multi-Step Workflow
**✅ Use**: Data Pipeline with multiple activities

```python
pipeline_definition = {
    "properties": {
        "activities": [
            {
                "name": "Extract_Data",
                "type": "TridentNotebook",  # Notebook for extraction
                "dependsOn": []
            },
            {
                "name": "Transform_Data",
                "type": "Copy",  # Copy for simple transform
                "dependsOn": [{"activity": "Extract_Data"}]
            },
            {
                "name": "Load_Data",
                "type": "TridentNotebook",  # Notebook for loading
                "dependsOn": [{"activity": "Transform_Data"}]
            }
        ]
    }
}
```

---

## Testing Results

### Successful Deployments

✅ **CopyJob**: Azure Blob Storage → Lakehouse
- ID: `2d3f2b4d-e519-4d74-8932-ad4b4d3b738e`
- Name: `AmazonData_BlobToLakehouse`
- Status: Working

✅ **Data Pipeline**: Lakehouse Files → Lakehouse Table
- ID: `93557a42-669e-4215-a01b-cd5eb4e0573a`
- Name: `DataPipeline_BlobToLakehouse_Amazon`
- Status: Working

✅ **Connection**: Azure Blob Storage
- ID: `372a9195-6f23-48bf-b664-3725fa6ac3f6`
- Name: `BlobStorage_fabricsatest123`
- Status: Working with CopyJob

### Failed Attempts

❌ **Data Pipeline Copy Activity**: Azure Blob Storage → Lakehouse
- Error: `"invalid reference 'blobstorage_fabricsatest123'"`
- Reason: Cannot reference Fabric Connections in Data Pipeline
- Solution: Use CopyJob instead

---

## Recommendations for Your Application

### Primary Implementation (Current)
1. **Use CopyJob API** for all external source → Lakehouse copies
2. **Use Notebook Activity** as fallback for complex scenarios
3. **Document limitations** in user-facing documentation

### Future Enhancements
1. **Implement Data Flow support** for complex transformations
2. **Add activity type selection** in UI based on source type and complexity
3. **Automatic fallback** from Copy → Data Flow → Notebook based on requirements

### Code Organization
```
backend/
├── services/
│   └── fabric_api_service.py
│       ├── create_copy_job()        ← Primary for external sources
│       ├── create_data_flow()       ← TODO: For transformations
│       ├── create_pipeline()        ← For Lakehouse-to-Lakehouse
│       └── create_notebook()        ← Fallback for complex logic
│
├── deploy_copy_pipeline_updated.py  ← Use this (CopyJob)
├── deploy_copy_pipeline.py          ← Deprecated (broken Copy Activity)
└── deploy_copy_pipeline_notebook.py ← Fallback (Notebook)
```

---

## Next Steps

### Immediate (Priority 1)
- [x] Implement CopyJob API support
- [x] Update deployment scripts
- [x] Document activity hierarchy

### Short Term (Priority 2)
- [ ] Implement Data Flow activity support
- [ ] Add activity selection logic in main pipeline deployment
- [ ] Create tests for each activity type

### Long Term (Priority 3)
- [ ] Explore Azure Key Vault integration for Data Pipeline external sources
- [ ] Build UI for activity type selection
- [ ] Add monitoring and logging for each activity type

---

## References

- **CopyJob Definition**: `knowledge/Copy job definition - Microsoft Fabric REST APIs _ Microsoft Learn.pdf`
- **Data Pipeline Structure**: `knowledge/DATA_PIPELINE_STRUCTURE_REFERENCE.md`
- **Testing Results**: `knowledge/DATA_PIPELINE_CREATION_RESULTS.md`
- **Working Example**: Pipeline from `uicomidlakeprod01fabws` workspace

---

**Author**: Claude Code
**Date**: 2025-10-15
**Version**: 1.0
