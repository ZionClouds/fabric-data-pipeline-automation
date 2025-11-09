# Pipeline Deployment Fix - 400 Bad Request Error

## The Problem

The `deploy_pipeline_api.py` was failing with a **400 Bad Request** error when trying to deploy the pipeline definition to Microsoft Fabric API.

---

## Root Cause

The issue was in the `update_item_definition()` function. The API file was sending the pipeline JSON incorrectly:

### ❌ WRONG (Original deploy_pipeline_api.py):

```python
payload = {"definition": json.loads(definition)}
```

This was trying to parse the pipeline JSON string and send it directly as a JSON object.

### ✅ CORRECT (From deploy_pipeline.py):

```python
# Base64 encode the definition
payload_bytes = definition.encode("utf-8")
encoded_payload = base64.b64encode(payload_bytes).decode("ascii")

# Wrap in proper structure
update_payload = {
    "definition": {
        "parts": [
            {
                "path": "pipeline-content.json",
                "payload": encoded_payload,
                "payloadType": "InlineBase64"
            }
        ]
    }
}
```

---

## The Fix

Updated the `update_item_definition()` function in `deploy_pipeline_api.py` (lines 1028-1074):

### Changes Made:

1. **Base64 encode the definition string**
   ```python
   payload_bytes = definition.encode("utf-8")
   encoded_payload = base64.b64encode(payload_bytes).decode("ascii")
   ```

2. **Detect content type** (notebook vs pipeline)
   ```python
   if definition.startswith("# Fabric notebook source"):
       content_path = "notebook-content.py"
   else:
       content_path = "pipeline-content.json"
   ```

3. **Wrap in proper "parts" structure**
   ```python
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
   ```

4. **Add better error logging**
   ```python
   if response.status_code not in [200, 202]:
       print(f"   ❌ Update failed with status {response.status_code}")
       print(f"   Response: {response.text}")
   ```

---

## Why This Works

Microsoft Fabric API expects:

- ✅ **Base64-encoded content** in the payload
- ✅ **Proper file path** designation (`pipeline-content.json` for pipelines, `notebook-content.py` for notebooks)
- ✅ **PayloadType specification** as `"InlineBase64"`

This is the same format used for notebooks and all other Fabric items.

---

## What's Fixed

The `modify_pipeline_definition()` function was already working correctly (lines 885-978):

- ✅ Removes Email/Dataflow activities
- ✅ Updates all IDs (workspace, lakehouse, notebook)
- ✅ Rebuilds Get Metadata activity with correct structure
- ✅ Updates Script activity with warehouse connection
- ✅ Configures ForEach loop properly

The issue was **NOT** in the pipeline structure - it was in how we were **sending** the pipeline to the API.

---

## Testing

The deployment should now work successfully with:

- ✅ **Get Metadata** activity (reads from bronze/ folder)
- ✅ **GetProcessedFileNames** activity (queries warehouse via connection)
- ✅ **FilterNewFiles** activity (filters out already-processed files)
- ✅ **ForEach** loop with PHI_PII_detection notebook
- ✅ **Proper warehouse connection** reference

---

## Next Steps

1. **Test the deployment** by clicking "Deploy to Fabric Workspace" in the UI
2. **Verify** the pipeline appears in Fabric workspace at https://app.fabric.microsoft.com
3. **Check** that all activities are properly configured:
   - Get Metadata → GetProcessedFileNames → SetEmptyFileArray → ForEach1 → FilterNewFiles → forEach
4. **Run the pipeline** to process files from the bronze folder
5. **Verify** results appear in the silver folder

---

## Files Modified

- `/Users/jayavardhanareddy/Desktop/fabric-data-pipeline-automation/backend/deploy_pipeline_api.py`
  - Function: `update_item_definition()` (lines 1028-1074)
  - Fixed payload structure to use base64 encoding and "parts" wrapper

---

## Summary

**The 400 Bad Request error was caused by sending the pipeline definition as a plain JSON object instead of base64-encoded content wrapped in the proper "parts" structure.**

By matching the working implementation from `deploy_pipeline.py`, the deployment should now succeed!
