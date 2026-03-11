# AI Chat Integration Guide - Fabric Pipeline Deployment

## Overview

This guide explains how to integrate Fabric pipeline deployment with your AI chat interface. Users can describe what they want, and the AI will guide them through deploying a pipeline.

---

## User Flow

```
1. User opens AI Chat
   └─> Selects workspace: "jay-dev"

2. User says: "I want to create a pipeline to process blob storage data"

3. AI asks: "What lakehouse should I use?"
   └─> User: "jay_dev_lakehouse"

4. AI asks: "What's the source folder name?"
   └─> User: "raw-data" or "bronze"

5. AI asks: "What's the output folder name?"
   └─> User: "processed-data" or "silver"

6. AI asks: "What should I name the pipeline?"
   └─> User: "CustomerDataPipeline"

7. AI shows summary:
   ┌──────────────────────────────────────┐
   │ Pipeline Configuration:              │
   ├──────────────────────────────────────┤
   │ Workspace:  jay-dev                  │
   │ Lakehouse:  jay_dev_lakehouse        │
   │ Source:     Files/raw-data           │
   │ Output:     Files/processed-data     │
   │ Pipeline:   CustomerDataPipeline     │
   │                                      │
   │ [Generate Pipeline] [Cancel]         │
   └──────────────────────────────────────┘

8. User clicks "Generate Pipeline"

9. Backend deploys pipeline

10. AI shows result:
    ✅ Pipeline deployed successfully!
    - Pipeline ID: abc-123-def
    - Notebook ID: xyz-456-ghi
    - Ready to run in Fabric UI
```

---

## Integration Steps

### Step 1: Add Router to FastAPI App

In your `main.py`, add:

```python
from fabric_deployment_endpoint import router as fabric_router

# Add the router
app.include_router(fabric_router)
```

### Step 2: Frontend Integration

The frontend needs to:

1. **Collect Information** via AI chat conversation
2. **Display Summary** with "Generate Pipeline" button
3. **Call API** when user clicks button
4. **Show Results**

Example frontend code:

```typescript
// When user clicks "Generate Pipeline" button
async function deployPipeline(config: PipelineConfig) {
  try {
    const response = await fetch('/api/fabric/deploy-pipeline', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workspace_name: config.workspace,
        lakehouse_name: config.lakehouse,
        source_folder: config.sourceFolder,
        output_folder: config.outputFolder,
        pipeline_name: config.pipelineName
      })
    });

    const result = await response.json();

    if (result.status === 'success') {
      // Show success message
      showSuccess(`Pipeline "${result.pipeline_name}" deployed!`);
    } else {
      // Show error
      showError(result.message);
    }
  } catch (error) {
    showError('Deployment failed');
  }
}
```

---

## API Endpoints

### 1. Deploy Pipeline

**Endpoint:** `POST /api/fabric/deploy-pipeline`

**Request Body:**
```json
{
  "workspace_name": "jay-dev",
  "lakehouse_name": "jay_dev_lakehouse",
  "source_folder": "bronze",
  "output_folder": "silver",
  "pipeline_name": "MyPipeline",
  "warehouse_name": "jay-dev-warehouse",
  "notebook_name": "PHI_PII_detection"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Pipeline 'MyPipeline' deployed successfully!",
  "workspace_id": "561d497c-4709-4a69-924d-e59ad8fa6ee1",
  "workspace_name": "jay-dev",
  "lakehouse_id": "71b91fa4-7883-44e1-aa6f-f2d6c8d564ef",
  "lakehouse_name": "jay_dev_lakehouse",
  "notebook_id": "abc-123-def",
  "notebook_name": "PHI_PII_detection",
  "pipeline_id": "xyz-456-ghi",
  "pipeline_name": "MyPipeline",
  "source_folder": "Files/bronze",
  "output_folder": "Files/silver"
}
```

### 2. Validate Workspace

**Endpoint:** `GET /api/fabric/validate-workspace/{workspace_name}`

**Example:** `GET /api/fabric/validate-workspace/jay-dev`

**Response:**
```json
{
  "status": "success",
  "exists": true,
  "workspace_id": "561d497c-4709-4a69-924d-e59ad8fa6ee1",
  "workspace_name": "jay-dev"
}
```

### 3. List Lakehouses

**Endpoint:** `GET /api/fabric/list-lakehouses/{workspace_name}`

**Example:** `GET /api/fabric/list-lakehouses/jay-dev`

**Response:**
```json
{
  "status": "success",
  "workspace_name": "jay-dev",
  "lakehouses": [
    {
      "id": "71b91fa4-7883-44e1-aa6f-f2d6c8d564ef",
      "name": "jay_dev_lakehouse",
      "description": "Main lakehouse"
    }
  ]
}
```

---

## AI Chat Conversation Examples

### Example 1: User mentions "blob storage"

**User:** "I want to process data from blob storage"

**AI Response:**
```
I can help you create a pipeline to process data from your lakehouse
(which uses blob storage under the hood).

Let me gather some information:

1. What lakehouse should I use?
   - jay_dev_lakehouse
   - [Other available lakehouses...]
```

### Example 2: User provides folder names

**User:** "Source is in 'incoming' folder, output should go to 'processed'"

**AI Response:**
```
Perfect! I'll use:
- Source folder: Files/incoming
- Output folder: Files/processed

What would you like to name this pipeline?
```

### Example 3: User wants to customize

**User:** "Can I use a different warehouse?"

**AI Response:**
```
Yes! The default warehouse is 'jay-dev-warehouse', but you can specify
a different one. Which warehouse would you like to use?
```

---

## AI Prompting Strategy

### System Prompt for AI

```
You are a Microsoft Fabric pipeline deployment assistant. When users mention:
- "blob storage", "data lake", "lakehouse", "storage"
- "process files", "ETL pipeline", "data pipeline"

Your job is to:
1. Confirm they want to deploy a Fabric pipeline
2. Collect these required parameters:
   - Lakehouse name (suggest available options)
   - Source folder name (just the folder name, not full path)
   - Output folder name (just the folder name, not full path)
   - Pipeline name (suggest based on purpose)

3. Show a summary and ask for confirmation
4. When they confirm, display a "Generate Pipeline" button

Remember:
- Folder paths are always: Files/{folder_name}
- Warehouse is usually: jay-dev-warehouse
- Notebook logic is fixed (PII/PHI detection)
- Don't make up component IDs - only show after deployment
```

### Conversation Flow Template

```typescript
const conversationFlow = {
  step1: {
    trigger: ["blob storage", "data lake", "pipeline"],
    response: "I can help deploy a Fabric pipeline. What lakehouse should I use?",
    collectParam: "lakehouse_name"
  },
  step2: {
    response: "What's the source folder name? (e.g., 'bronze', 'raw-data')",
    collectParam: "source_folder"
  },
  step3: {
    response: "What's the output folder name? (e.g., 'silver', 'processed')",
    collectParam: "output_folder"
  },
  step4: {
    response: "What should I name this pipeline?",
    collectParam: "pipeline_name"
  },
  step5: {
    response: "Here's the summary:\n[Show config]\nReady to deploy?",
    action: "showGenerateButton"
  }
};
```

---

## Error Handling

### Common Errors and Responses

| Error | AI Response |
|-------|-------------|
| Workspace not found | "I couldn't find workspace '{name}'. Please check the name and try again." |
| Lakehouse not found | "Lakehouse '{name}' doesn't exist. Would you like to create it first?" |
| Warehouse not found | "Warehouse '{name}' not found. Using default: 'jay-dev-warehouse'" |
| Invalid folder name | "Folder names should not contain special characters or spaces." |
| Deployment fails | "Deployment failed: {error}. Would you like to try again?" |

---

## Testing

### Test the API

```bash
# Test deployment
curl -X POST http://localhost:8080/api/fabric/deploy-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_name": "jay-dev",
    "lakehouse_name": "jay_dev_lakehouse",
    "source_folder": "test-source",
    "output_folder": "test-output",
    "pipeline_name": "TestPipeline"
  }'

# Validate workspace
curl http://localhost:8080/api/fabric/validate-workspace/jay-dev

# List lakehouses
curl http://localhost:8080/api/fabric/list-lakehouses/jay-dev
```

---

## Deployment Checklist

Before deploying:

- [ ] User selected workspace in chat UI
- [ ] Lakehouse name collected
- [ ] Source folder name collected (no "Files/" prefix)
- [ ] Output folder name collected (no "Files/" prefix)
- [ ] Pipeline name collected
- [ ] User confirmed configuration
- [ ] "Generate Pipeline" button shown

After deployment:

- [ ] Show success message with pipeline ID
- [ ] Provide link to Fabric UI
- [ ] Explain next steps (place files in source folder)

---

## Next Steps After Deployment

The AI should tell the user:

```
✅ Pipeline deployed successfully!

Next steps:
1. Open Fabric UI: https://app.fabric.microsoft.com
2. Go to workspace: {workspace_name}
3. Find your pipeline: {pipeline_name}
4. Place files in: {lakehouse_name} → Files/{source_folder}
5. Run the pipeline
6. Results will appear in: Files/{output_folder}

Need help running the pipeline?
```

---

## Advanced: Context-Aware Suggestions

The AI can be smarter by:

1. **Analyzing folder names** - suggest "silver" if source is "bronze"
2. **Detecting data types** - suggest appropriate pipeline names
3. **Remembering user preferences** - reuse warehouse/lakehouse choices
4. **Checking existing pipelines** - warn about name conflicts

---

## Security Considerations

1. **Validate workspace access** - ensure user has permissions
2. **Sanitize folder names** - prevent path traversal
3. **Rate limiting** - prevent abuse of deployment API
4. **Audit logging** - track who deployed what

---

## Support

If users encounter issues:

1. Check Fabric workspace permissions
2. Verify lakehouse/warehouse exist
3. Check deployment logs
4. Contact support with deployment ID

---

## Summary

**User Flow:**
1. Chat → Collect params → Show summary → Click button → Deploy

**Backend Flow:**
1. Validate input → Authenticate → Find resources → Deploy components → Return status

**What's Customizable:**
- Workspace (selected in UI)
- Lakehouse name
- Source folder
- Output folder
- Pipeline name

**What's Fixed (for now):**
- Warehouse (jay-dev-warehouse)
- Notebook logic (PII/PHI detection)
- Pipeline structure (Get Metadata → Filter → ForEach → Notebook)

---

Ready to integrate! 🚀
