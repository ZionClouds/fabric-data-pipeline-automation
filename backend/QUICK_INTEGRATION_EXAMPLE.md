# Quick Integration Example

## Scenario: User wants to deploy a pipeline via AI chat

---

## Frontend (React/TypeScript Example)

```typescript
// State to track deployment configuration
interface PipelineConfig {
  workspace: string;
  lakehouse: string;
  sourceFolder: string;
  outputFolder: string;
  pipelineName: string;
}

const [config, setConfig] = useState<PipelineConfig>({
  workspace: 'jay-dev', // From user's workspace selection
  lakehouse: '',
  sourceFolder: '',
  outputFolder: '',
  pipelineName: ''
});

const [showDeployButton, setShowDeployButton] = useState(false);

// Function to handle deployment
async function handleDeploy() {
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
      // Add AI message showing success
      addMessage({
        role: 'assistant',
        content: `✅ Pipeline deployed successfully!\n\n` +
                `Pipeline: ${result.pipeline_name}\n` +
                `ID: ${result.pipeline_id}\n\n` +
                `Next steps:\n` +
                `1. Go to Fabric UI\n` +
                `2. Navigate to workspace: ${result.workspace_name}\n` +
                `3. Find pipeline: ${result.pipeline_name}\n` +
                `4. Place files in: ${result.lakehouse_name} → ${result.source_folder}\n` +
                `5. Run the pipeline`
      });
    } else {
      addMessage({
        role: 'assistant',
        content: `❌ Deployment failed: ${result.message}`
      });
    }
  } catch (error) {
    addMessage({
      role: 'assistant',
      content: `❌ Error: ${error.message}`
    });
  }
}

// AI Chat conversation handling
function handleAIResponse(userMessage: string) {
  const lowerMsg = userMessage.toLowerCase();

  // Detect deployment intent
  if (lowerMsg.includes('blob storage') ||
      lowerMsg.includes('pipeline') ||
      lowerMsg.includes('data lake')) {

    // Start deployment flow
    addMessage({
      role: 'assistant',
      content: 'I can help you deploy a Fabric pipeline. What lakehouse should I use?'
    });

    // Set flag to collect lakehouse next
    setCollectingParam('lakehouse');
  }

  // Collect lakehouse
  else if (collectingParam === 'lakehouse') {
    setConfig(prev => ({ ...prev, lakehouse: userMessage }));
    addMessage({
      role: 'assistant',
      content: `Got it! Using lakehouse: ${userMessage}\n\n` +
               `What's the source folder name? (e.g., "bronze", "raw-data")`
    });
    setCollectingParam('sourceFolder');
  }

  // Collect source folder
  else if (collectingParam === 'sourceFolder') {
    setConfig(prev => ({ ...prev, sourceFolder: userMessage }));
    addMessage({
      role: 'assistant',
      content: `Source folder: Files/${userMessage}\n\n` +
               `What's the output folder name? (e.g., "silver", "processed")`
    });
    setCollectingParam('outputFolder');
  }

  // Collect output folder
  else if (collectingParam === 'outputFolder') {
    setConfig(prev => ({ ...prev, outputFolder: userMessage }));
    addMessage({
      role: 'assistant',
      content: `Output folder: Files/${userMessage}\n\n` +
               `What should I name this pipeline?`
    });
    setCollectingParam('pipelineName');
  }

  // Collect pipeline name and show summary
  else if (collectingParam === 'pipelineName') {
    setConfig(prev => ({ ...prev, pipelineName: userMessage }));

    addMessage({
      role: 'assistant',
      content: `Perfect! Here's your pipeline configuration:\n\n` +
               `┌────────────────────────────────┐\n` +
               `│ Workspace:  ${config.workspace.padEnd(18)} │\n` +
               `│ Lakehouse:  ${config.lakehouse.padEnd(18)} │\n` +
               `│ Source:     Files/${config.sourceFolder.padEnd(11)} │\n` +
               `│ Output:     Files/${userMessage.padEnd(11)} │\n` +
               `│ Pipeline:   ${userMessage.padEnd(18)} │\n` +
               `└────────────────────────────────┘\n\n` +
               `Ready to deploy?`
    });

    setShowDeployButton(true);
    setCollectingParam(null);
  }
}
```

---

## Backend Integration (main.py)

```python
from fastapi import FastAPI
from fabric_deployment_endpoint import router as fabric_router

app = FastAPI()

# Include the Fabric deployment router
app.include_router(fabric_router)

# Your existing chat endpoints
@app.post("/api/chat")
async def chat(message: str):
    # Your AI chat logic here
    pass

# Now these endpoints are available:
# - POST /api/fabric/deploy-pipeline
# - GET /api/fabric/validate-workspace/{workspace_name}
# - GET /api/fabric/list-lakehouses/{workspace_name}
```

---

## Complete Conversation Example

```
User: I need to process files from blob storage

AI: I can help you deploy a Fabric pipeline. What lakehouse should I use?

User: jay_dev_lakehouse

AI: Got it! Using lakehouse: jay_dev_lakehouse
    What's the source folder name? (e.g., "bronze", "raw-data")

User: incoming-claims

AI: Source folder: Files/incoming-claims
    What's the output folder name? (e.g., "silver", "processed")

User: processed-claims

AI: Output folder: Files/processed-claims
    What should I name this pipeline?

User: ClaimsProcessingPipeline

AI: Perfect! Here's your pipeline configuration:

    ┌────────────────────────────────┐
    │ Workspace:  jay-dev            │
    │ Lakehouse:  jay_dev_lakehouse  │
    │ Source:     Files/incoming-claims │
    │ Output:     Files/processed-claims │
    │ Pipeline:   ClaimsProcessingPipeline │
    └────────────────────────────────┘

    Ready to deploy?

    [Generate Pipeline] [Cancel]

User: *clicks Generate Pipeline*

AI: ⏳ Deploying pipeline...

    ✅ Pipeline deployed successfully!

    Pipeline: ClaimsProcessingPipeline
    ID: abc-123-def-456

    Next steps:
    1. Go to https://app.fabric.microsoft.com
    2. Navigate to workspace: jay-dev
    3. Find pipeline: ClaimsProcessingPipeline
    4. Place files in: jay_dev_lakehouse → Files/incoming-claims
    5. Run the pipeline

    Results will appear in: Files/processed-claims
```

---

## API Call Example

```bash
# What happens when user clicks "Generate Pipeline"
curl -X POST http://localhost:8000/api/fabric/deploy-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_name": "jay-dev",
    "lakehouse_name": "jay_dev_lakehouse",
    "source_folder": "incoming-claims",
    "output_folder": "processed-claims",
    "pipeline_name": "ClaimsProcessingPipeline"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Pipeline 'ClaimsProcessingPipeline' deployed successfully!",
  "workspace_id": "561d497c-4709-4a69-924d-e59ad8fa6ee1",
  "workspace_name": "jay-dev",
  "lakehouse_id": "71b91fa4-7883-44e1-aa6f-f2d6c8d564ef",
  "lakehouse_name": "jay_dev_lakehouse",
  "notebook_id": "xyz-789",
  "notebook_name": "PHI_PII_detection",
  "pipeline_id": "abc-123",
  "pipeline_name": "ClaimsProcessingPipeline",
  "source_folder": "Files/incoming-claims",
  "output_folder": "Files/processed-claims"
}
```

---

## Button Component Example

```tsx
// DeployPipelineButton.tsx
import React from 'react';

interface DeployButtonProps {
  config: PipelineConfig;
  onDeploy: () => Promise<void>;
  onCancel: () => void;
}

export function DeployPipelineButton({ config, onDeploy, onCancel }: DeployButtonProps) {
  const [deploying, setDeploying] = React.useState(false);

  async function handleDeploy() {
    setDeploying(true);
    try {
      await onDeploy();
    } finally {
      setDeploying(false);
    }
  }

  return (
    <div className="deploy-pipeline-card">
      <h3>Pipeline Configuration</h3>
      <table>
        <tr>
          <td>Workspace:</td>
          <td>{config.workspace}</td>
        </tr>
        <tr>
          <td>Lakehouse:</td>
          <td>{config.lakehouse}</td>
        </tr>
        <tr>
          <td>Source:</td>
          <td>Files/{config.sourceFolder}</td>
        </tr>
        <tr>
          <td>Output:</td>
          <td>Files/{config.outputFolder}</td>
        </tr>
        <tr>
          <td>Pipeline:</td>
          <td>{config.pipelineName}</td>
        </tr>
      </table>

      <div className="button-group">
        <button
          onClick={handleDeploy}
          disabled={deploying}
          className="btn-primary"
        >
          {deploying ? '⏳ Deploying...' : '🚀 Generate Pipeline'}
        </button>
        <button
          onClick={onCancel}
          disabled={deploying}
          className="btn-secondary"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
```

---

## Testing in Development

```bash
# 1. Start your backend
cd backend
python3 -m uvicorn main:app --reload --port 8000

# 2. Test the endpoint
curl -X POST http://localhost:8000/api/fabric/deploy-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_name": "jay-dev",
    "lakehouse_name": "jay_dev_lakehouse",
    "source_folder": "test-in",
    "output_folder": "test-out",
    "pipeline_name": "TestPipeline"
  }'

# 3. Check Fabric UI
# Go to https://app.fabric.microsoft.com
# Navigate to jay-dev workspace
# Look for "TestPipeline"
```

---

## Summary

**Files Created:**
1. `deploy_pipeline_api.py` - Core deployment logic
2. `fabric_deployment_endpoint.py` - FastAPI endpoints
3. `AI_CHAT_INTEGRATION_GUIDE.md` - Full integration guide
4. `QUICK_INTEGRATION_EXAMPLE.md` - This file

**Integration Steps:**
1. Add router to main.py: `app.include_router(fabric_router)`
2. Update frontend to collect parameters via AI chat
3. Show "Generate Pipeline" button with summary
4. Call `/api/fabric/deploy-pipeline` on button click
5. Display deployment results

**What Users Provide:**
- Lakehouse name
- Source folder (e.g., "bronze")
- Output folder (e.g., "silver")
- Pipeline name

**What Gets Deployed:**
- Notebook with PII/PHI detection logic
- Pipeline with Get Metadata → Filter → ForEach → Notebook
- Source: Files/{source_folder}
- Output: Files/{output_folder}

Ready to integrate! 🎉
