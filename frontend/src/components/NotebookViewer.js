import React from 'react';

const NotebookViewer = ({ notebook, onClose }) => {
  if (!notebook) return null;

  return (
    <div className="notebook-modal" onClick={onClose}>
      <div className="notebook-content" onClick={(e) => e.stopPropagation()}>
        <h3>{notebook.name}</h3>
        <pre><code>{notebook.code}</code></pre>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
};

export default NotebookViewer;
