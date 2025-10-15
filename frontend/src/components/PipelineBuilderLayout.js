import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usePipeline } from '../contexts/PipelineContext';
import { pipelineApi } from '../services/api';
import WorkspaceSelector from './WorkspaceSelector';
import AIChat from './AIChat';
import PipelinePreview from './PipelinePreview';
import PipelineList from './PipelineList';
import '../styles/PipelineBuilder.css';

const PipelineBuilderLayout = () => {
  const { user, logout } = useAuth();
  const { selectedWorkspace } = usePipeline();
  const [activeTab, setActiveTab] = useState('chat');
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoadingWorkspaces, setIsLoadingWorkspaces] = useState(true);

  useEffect(() => {
    loadWorkspaces();
  }, [user]);

  const loadWorkspaces = async () => {
    try {
      setIsLoadingWorkspaces(true);
      const response = await pipelineApi.getWorkspaces();
      console.log('Workspaces loaded:', response.data);
      setWorkspaces(response.data || []);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    } finally {
      setIsLoadingWorkspaces(false);
    }
  };

  return (
    <div className="pipeline-builder">
      {/* Header */}
      <header className="builder-header">
        <div className="header-left">
          <h1>🚀 Pipeline Builder</h1>
          <span className="header-subtitle">AI-Powered Data Pipelines</span>
        </div>
        <div className="header-right">
          <span className="user-info">
            👤 {user?.name || user?.email}
          </span>
          <button onClick={logout} className="btn-secondary">
            Logout
          </button>
        </div>
      </header>

      {/* Workspace Selector */}
      <div className="workspace-section">
        <WorkspaceSelector
          workspaces={workspaces}
          isLoading={isLoadingWorkspaces}
        />
      </div>

      {/* Main Content */}
      {selectedWorkspace ? (
        <div className="builder-content">
          {/* Navigation Tabs */}
          <nav className="builder-tabs">
            <button
              className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              💬 AI Chat
            </button>
            <button
              className={`tab ${activeTab === 'preview' ? 'active' : ''}`}
              onClick={() => setActiveTab('preview')}
            >
              📊 Pipeline Preview
            </button>
            <button
              className={`tab ${activeTab === 'pipelines' ? 'active' : ''}`}
              onClick={() => setActiveTab('pipelines')}
            >
              📁 My Pipelines
            </button>
          </nav>

          {/* Tab Content */}
          <div className="tab-content">
            {activeTab === 'chat' && <AIChat />}
            {activeTab === 'preview' && <PipelinePreview />}
            {activeTab === 'pipelines' && <PipelineList />}
          </div>
        </div>
      ) : (
        <div className="no-workspace">
          <h2>Welcome to Pipeline Builder!</h2>
          <p>Select a workspace above to start building data pipelines with AI.</p>
        </div>
      )}
    </div>
  );
};

export default PipelineBuilderLayout;
