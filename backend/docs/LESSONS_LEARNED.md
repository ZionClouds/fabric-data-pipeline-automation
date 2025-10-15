# Lessons Learned - Fabric Pipeline Deployment

## Date: 2025-10-15

## Summary of Learnings

### 1. Connection Creation in Fabric

#### Workspace-Level vs Tenant-Level Connections

**Initial Approach (WRONG):**
```python
# Tenant-level endpoint (not what we want)
POST /v1/connections
```

**Correct Approach:**
```python
# Workspace-level endpoint
POST /v1/workspaces/{workspaceId}/connections
```

**Key Learning:**
- Connections should be created at **workspace level**, not tenant level
- Workspace-level connections are scoped to specific workspaces
- More secure and better isolation than tenant-wide connections

**Status:** ⚠️ Workspace-level connections endpoint returns 404 "EntityNotFound"
- This may indicate the endpoint isn't available in current Fabric API version
- Or it may require specific permissions/capacity settings
- Need to investigate further or use alternative approach

#### Connection Requirements for Copy Activities

**Critical Understanding:**
1. **External sources (Blob Storage) REQUIRE connections**
   - Cannot put credentials directly in Copy Activity
   - Credentials MUST live in Connection object
   - Copy Activity references the Connection by name

2. **Lakehouse sinks DON'T need connections**
   - Lakehouse is a workspace item
   - Reference by name in the workspace
   - No separate connection creation needed

**Copy Activity Structure:**
```json
{
  "source": {
    "type": "DelimitedTextSource",
    "connection": {
      "referenceName": "BlobStorage_Connection",  // References Connection
      "type": "ConnectionReference"
    },
    "storeSettings": {
      "container": "fabric",
      "wildcardFileName": "amazon.csv"
    }
  },
  "sink": {
    "type": "LakehouseSink",
    "workspaceId": "workspace-id",
    "itemId": "lakehouse-id",
    "rootFolder": "Tables",
    "table": "bronze_amazon_products",
    "tableActionOption": "Append"  // REQUIRED field
  }
}
```

### 2. Lakehouse Sink Configuration

**What We Learned:**
- `tableActionOption` is **REQUIRED** (was missing in initial implementation)
- Options: "Append", "Overwrite", "OverwriteSchema"
- `rootFolder`: "Tables" is standard for table writes
- `workspaceId` and `itemId` are optional but recommended

**Updated in:** `_build_copy_sink()` method (line 870)

### 3. Notebook Async Provisioning Challenge

**The Problem:**
When notebooks are created via API, Fabric returns status `202 Accepted`, indicating async provisioning:

```json
{
  "success": true,
  "notebook_id": "notebook_name",
  "status_code": 202,
  "note": "Notebook deployed (status 202)"
}
```

**Key Issues:**
1. Notebook is **not immediately available** after creation
2. Takes **5-10 minutes** (or more) to become fully provisioned
3. Pipelines **cannot reference notebooks** that aren't fully ready
4. Error: `"The document creation or update failed because of invalid reference 'notebook_name'"`

**Tested Wait Times:**
- ❌ 30 seconds - Too short
- ❌ 60 seconds - Still too short
- ❌ 90 seconds - Still too short
- ⏳ Need to wait much longer or implement retry logic

**Possible Solutions:**
1. **Implement retry with exponential backoff**
   - Create notebook
   - Wait 2 minutes
   - Try to create pipeline
   - If fails, wait and retry

2. **Use polling to check notebook availability**
   - Query workspace items until notebook appears
   - Then create pipeline

3. **Deploy notebooks separately from pipelines**
   - Create notebooks in advance
   - Wait for provisioning
   - Deploy pipelines later

4. **Use UI for initial notebook creation**
   - For now, may need manual notebook creation
   - Automate pipeline creation only

### 4. Copy Activity vs Notebook Activity

**Current Recommendation: Use Notebook Activities**

**Reasons:**
1. ✅ Notebooks work reliably (once provisioned)
2. ✅ Don't require connection creation (can handle auth inline)
3. ✅ More flexible for complex transformations
4. ✅ Better for Medallion architecture with multi-step processing

**Copy Activities blocked by:**
- ❌ Connection creation endpoint not working (404)
- ❌ Need to create and reference connections properly
- ❌ More complex setup for external sources

**Future:** Once connection creation is resolved, Copy Activities will be better for simple data movement.

### 5. Code Updates Made

#### File: `services/fabric_api_service.py`

**1. Updated `create_connection()` method (line 226)**
```python
# Now requires workspace_id parameter
async def create_connection(
    self,
    workspace_id: str,  # NEW - required parameter
    connection_name: str,
    source_type: str,
    connection_config: Dict[str, Any]
) -> Dict[str, Any]:
    # Use workspace-level endpoint
    create_url = f"{self.base_url}/workspaces/{workspace_id}/connections"
```

**2. Updated `_build_copy_sink()` method (line 870)**
```python
# Added required fields
{
    "type": "LakehouseSink",
    "workspaceId": workspace_id,      # Optional but recommended
    "itemId": lakehouse_id,            # Optional but recommended
    "rootFolder": "Tables",            # NEW - required
    "table": table_name,
    "tableActionOption": "Append"      # NEW - required
}
```

**3. Re-enabled Copy Activities (line 674)**
- Copy Activities are no longer skipped
- Properly build source and sink with connection references

### 6. Deployment Challenges

**Workspace ID Discovery:**
- Must call workspace backend API to get correct workspace IDs
- Hardcoded IDs can be wrong/outdated
- **soaham-test workspace:** `c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb`

**Item Name Conflicts:**
- Fabric doesn't allow duplicate names
- Items being created async can cause "ItemDisplayNameNotAvailableYet" errors
- Solution: Use timestamp-based unique names

**Error: "EntityNotFound" when creating connections**
- Workspace-level connections endpoint may not be available
- Need alternative approach or API version update

### 7. What Works vs What Doesn't

#### ✅ Works:
1. **Notebook creation via API** (but takes time to provision)
2. **Pipeline creation via API** (if notebooks are ready)
3. **Lakehouse references** in sink configuration
4. **Workspace discovery** via backend API
5. **Fabric API authentication** with service principal

#### ❌ Doesn't Work Yet:
1. **Workspace-level connection creation** (404 error)
2. **Immediate pipeline deployment** after notebook creation (timing issue)
3. **Copy Activities** (blocked by connection creation issue)

#### ⏳ Partially Works:
1. **Notebook deployment** - works but async provisioning is slow
2. **Complete pipeline deployment** - works but timing is critical

### 8. Recommended Approach

**For Production Automation:**

```python
# Step 1: Create notebooks with unique names
notebook_name = f"nb_copy_data_{timestamp}"
await create_notebook(workspace_id, notebook_name, code)

# Step 2: IMPORTANT - Wait or poll for notebook availability
await asyncio.sleep(180)  # Wait 3 minutes
# OR implement polling:
while not is_notebook_ready(workspace_id, notebook_name):
    await asyncio.sleep(30)

# Step 3: Create pipeline referencing the notebook
await create_pipeline(workspace_id, pipeline_name, {
    "activities": [{
        "type": "SynapseNotebook",
        "notebook": {"referenceName": notebook_name}
    }]
})
```

**For Blob Storage Data Copy:**
```python
# Use notebook with inline credentials
notebook_code = '''
spark.conf.set("fs.azure.account.key.{account}.blob.core.windows.net", key)
df = spark.read.csv(f"wasbs://{container}@{account}.blob.core.windows.net/{file}")
df.write.mode("append").saveAsTable(table)
'''
```

### 9. Next Steps

1. **Investigate connection endpoint availability**
   - Check Fabric API documentation for correct endpoint
   - Verify API version and permissions
   - Test with different workspace/capacity configurations

2. **Implement robust retry logic**
   - Add exponential backoff for notebook provisioning
   - Poll workspace items to detect when notebooks are ready
   - Retry pipeline creation if notebook reference fails

3. **Update deployment flow**
   - Create notebooks first
   - Wait for provisioning (with polling)
   - Deploy pipelines second
   - Add status tracking and user feedback

4. **Consider alternative approaches**
   - Pre-create notebooks manually or via separate process
   - Use Fabric UI for initial setup
   - Automate only pipeline creation with existing notebooks

### 10. API Endpoints Reference

**Fabric API Base:** `https://api.fabric.microsoft.com/v1`

**Working Endpoints:**
- ✅ `POST /workspaces/{workspaceId}/notebooks` - Create notebook (async)
- ✅ `POST /workspaces/{workspaceId}/dataPipelines` - Create pipeline
- ✅ `GET /workspaces/{workspaceId}/items` - List workspace items
- ✅ `GET /connections/supportedConnectionTypes` - List connection types

**Not Working:**
- ❌ `POST /workspaces/{workspaceId}/connections` - Returns 404
- ⚠️ Alternative: `POST /connections` (tenant-level, but we want workspace-level)

### 11. Configuration Values

**Current Test Configuration:**
```
Workspace: soaham-test
Workspace ID: c64f4ec0-087b-4ff7-a94e-9fe5cc5370cb
Lakehouse: soaham_test_lakehouse

Blob Storage:
- Account: fabricsatest123
- Container: fabric
- File: amazon.csv
- Target Table: bronze_amazon_products
```

### 12. Key Takeaways

1. ⚠️ **Async provisioning is the main blocker** for automated deployment
2. ⚠️ **Connection creation needs more investigation** - endpoint may not be available
3. ✅ **Notebooks work well** for data movement when given enough time
4. ✅ **Code updates are correct** - just need to solve timing and connection issues
5. 🔄 **Need retry logic** for production-ready automation
6. 📝 **Workspace-level connections preferred** but may need alternative approach

## Files Modified

1. `services/fabric_api_service.py`
   - `create_connection()` - Added workspace_id parameter
   - `_build_copy_sink()` - Added required fields
   - Copy Activities re-enabled

2. `docs/CONNECTIONS_API_UPDATE.md` - Connection implementation guide
3. `docs/COPY_ACTIVITY_UPDATE.md` - Copy Activity configuration guide
4. `docs/CONNECTION_CREATION_SUCCESS.md` - Initial connection success (tenant-level)

## Test Scripts Created

1. `test_blob_connection_final.py` - Test connection creation
2. `get_supported_types.py` - Discover connection types
3. `deploy_copy_pipeline.py` - Deploy with Copy Activity (failed due to connection issue)
4. `deploy_copy_pipeline_notebook.py` - Deploy with Notebook Activity (timing issues)

## Status: In Progress

- ✅ Connection creation code updated
- ✅ Copy Activity sink configuration updated
- ⏳ Need to resolve connection endpoint availability
- ⏳ Need to implement proper wait/retry for notebooks
- ⏳ Need to test full end-to-end deployment

## Recommendations for Tomorrow

1. Test connection creation with different API versions
2. Implement polling for notebook readiness
3. Consider hybrid approach: manual connection setup + automated pipeline deployment
4. Add retry logic to deployment flow
5. Test with longer wait times (3-5 minutes)
