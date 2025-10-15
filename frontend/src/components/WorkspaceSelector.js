import React from 'react';
import { usePipeline } from '../contexts/PipelineContext';

const WorkspaceSelector = ({ workspaces, isLoading }) => {
  const { selectedWorkspace, setSelectedWorkspace } = usePipeline();

  const handleSelect = (workspace) => {
    setSelectedWorkspace(workspace);
  };

  if (isLoading) {
    return <div className="workspace-selector loading">Loading workspaces...</div>;
  }

  return (
    <div className="workspace-selector">
      <label>Select Workspace:</label>
      <select
        value={selectedWorkspace?.id || ''}
        onChange={(e) => {
          const ws = workspaces.find(w => w.id === e.target.value);
          handleSelect(ws);
        }}
        className="workspace-dropdown"
      >
        <option value="">-- Choose a workspace --</option>
        {workspaces.map(workspace => (
          <option key={workspace.id} value={workspace.id}>
            {workspace.name}
          </option>
        ))}
      </select>
      {selectedWorkspace && (
        <div className="workspace-info">
          ✓ Connected to: <strong>{selectedWorkspace.name}</strong>
        </div>
      )}
    </div>
  );
};

export default WorkspaceSelector;
