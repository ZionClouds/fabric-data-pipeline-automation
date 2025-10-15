import React, { useState } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import { useAuth } from '../contexts/AuthContext';
import { pipelineApi } from '../services/api';
import NotebookViewer from './NotebookViewer';

const PipelinePreview = () => {
  const { selectedWorkspace, chatMessages } = usePipeline();
  const { user } = useAuth();
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [generatedPipeline, setGeneratedPipeline] = useState(null);
  const [selectedNotebook, setSelectedNotebook] = useState(null);
  const [error, setError] = useState(null);
  const [deploySuccess, setDeploySuccess] = useState(null);

  const handleGeneratePipeline = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      setDeploySuccess(null);

      // Extract context from chat messages
      const chatContext = chatMessages.map(msg => `${msg.role}: ${msg.content}`).join('\n\n');

      const response = await pipelineApi.generatePipeline({
        workspace_id: selectedWorkspace.id,
        pipeline_name: 'Pipeline_' + Date.now(),
        source_type: 'blob_storage',  // Default to blob storage for now
        source_config: {
          chat_context: chatContext  // Send entire conversation
        },
        tables: ['data'],  // Generic table name
        transformations: [
          {
            transformation_type: 'filtering',
            description: 'Extract from chat conversation',
            source_table: 'bronze_data',
            target_table: 'silver_data',
            layer: 'silver'
          }
        ],
        use_medallion: true,
        schedule: 'manual',
        created_by: user.email
      });

      setGeneratedPipeline(response.data);
    } catch (err) {
      setError('Failed to generate pipeline: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeployPipeline = async () => {
    if (!generatedPipeline) return;

    try {
      setIsDeploying(true);
      setError(null);
      setDeploySuccess(null);

      const response = await pipelineApi.deployPipeline(
        generatedPipeline.pipeline_id,
        selectedWorkspace.id
      );

      setDeploySuccess(`Pipeline deployed successfully! Fabric Pipeline ID: ${response.data.fabric_pipeline_id}`);
    } catch (err) {
      setError('Failed to deploy pipeline: ' + err.message);
    } finally {
      setIsDeploying(false);
    }
  };

  if (!selectedWorkspace) {
    return (
      <div className="pipeline-preview empty">
        <p>Select a workspace to preview pipelines</p>
      </div>
    );
  }

  if (chatMessages.length === 0 && !generatedPipeline) {
    return (
      <div className="pipeline-preview empty">
        <h3>No pipeline to preview</h3>
        <p>Start a conversation in the AI Chat tab to design your pipeline</p>
      </div>
    );
  }

  return (
    <div className="pipeline-preview-container">
      <div className="preview-header">
        <h2>Pipeline Preview</h2>
        <button onClick={handleGeneratePipeline} disabled={isGenerating} className="btn-primary">
          {isGenerating ? 'Generating...' : 'Generate Pipeline'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {deploySuccess && <div className="alert alert-success">{deploySuccess}</div>}

      {generatedPipeline ? (
        <div className="pipeline-details">
          <div className="detail-section">
            <h3>Pipeline: {generatedPipeline.pipeline_name}</h3>

            <div className="deploy-section">
              <button
                onClick={handleDeployPipeline}
                disabled={isDeploying}
                className="btn-success"
                style={{marginBottom: '20px'}}
              >
                {isDeploying ? 'Deploying...' : '🚀 Deploy to Fabric Workspace'}
              </button>
            </div>

            <p className="reasoning"><strong>Architectural Decisions:</strong> {generatedPipeline.reasoning}</p>

            <div className="activities-section">
              <h4>Pipeline Activities ({generatedPipeline.activities?.length || 0})</h4>
              {generatedPipeline.activities && generatedPipeline.activities.length > 0 ? (
                <div className="activities-list">
                  {generatedPipeline.activities.map((activity, index) => (
                    <div key={index} className="activity-card">
                      <h5>{activity.name}</h5>
                      <p><strong>Type:</strong> {activity.type}</p>
                      {activity.depends_on && activity.depends_on.length > 0 && (
                        <p><strong>Depends On:</strong> {activity.depends_on.join(', ')}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p>No activities defined</p>
              )}
            </div>

            <div className="notebooks-section">
              <h4>Notebooks ({generatedPipeline.notebooks?.length || 0})</h4>
              {generatedPipeline.notebooks && generatedPipeline.notebooks.length > 0 ? (
                <div className="notebooks-list">
                  {generatedPipeline.notebooks.map((notebook, index) => (
                    <div key={index} className="notebook-card">
                      <h5>{notebook.notebook_name}</h5>
                      <p><strong>Layer:</strong> {notebook.layer}</p>
                      <p>{notebook.description}</p>
                      <button
                        onClick={() => setSelectedNotebook(notebook)}
                        className="btn-secondary"
                      >
                        View Code
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No notebooks defined</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="preview-placeholder">
          <p>Click "Generate Pipeline" to create your pipeline</p>
        </div>
      )}

      {selectedNotebook && (
        <NotebookViewer notebook={selectedNotebook} onClose={() => setSelectedNotebook(null)} />
      )}
    </div>
  );
};

export default PipelinePreview;
