import React, { createContext, useState, useContext } from 'react';

const PipelineContext = createContext();

export const PipelineProvider = ({ children }) => {
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  const [selectedLakehouse, setSelectedLakehouse] = useState(null);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [currentPipeline, setCurrentPipeline] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [pipelineConfig, setPipelineConfig] = useState({
    source_type: null,
    tables: [],
    transformations: [],
    use_medallion: true,
    schedule: 'manual',
    pipeline_name: null
  });

  const addChatMessage = (role, content) => {
    // Debug log to see what's being passed
    console.log('addChatMessage called with:', { role, contentType: typeof content, content });

    // Ensure content is always a string
    let stringContent;

    if (typeof content === 'string') {
      stringContent = content;
    } else if (content === null || content === undefined) {
      stringContent = '';
      console.warn('addChatMessage received null/undefined content');
    } else if (typeof content === 'object') {
      // Handle objects - avoid circular references
      console.warn('addChatMessage received object instead of string:', content);
      try {
        // If it's a plain object, try to stringify
        if (content.constructor === Object || Array.isArray(content)) {
          stringContent = JSON.stringify(content, null, 2);
        } else {
          // For other objects (DOM elements, React components, etc.), just convert to string
          console.warn('Content is not a plain object, converting to string');
          stringContent = '[Object]';
        }
      } catch (e) {
        // If JSON.stringify fails (circular reference), just convert to string
        console.error('Failed to stringify content:', e);
        stringContent = '[Unable to display content]';
      }
    } else {
      stringContent = String(content);
    }

    setChatMessages(prev => [...prev, { role, content: stringContent, timestamp: new Date() }]);
  };

  const clearChat = () => {
    setChatMessages([]);
  };

  const updatePipelineConfig = (updates) => {
    setPipelineConfig(prev => ({ ...prev, ...updates }));
  };

  const resetPipeline = () => {
    setCurrentPipeline(null);
    setChatMessages([]);
    setPipelineConfig({
      source_type: null,
      tables: [],
      transformations: [],
      use_medallion: true,
      schedule: 'manual',
      pipeline_name: null
    });
  };

  return (
    <PipelineContext.Provider
      value={{
        selectedWorkspace,
        setSelectedWorkspace,
        selectedLakehouse,
        setSelectedLakehouse,
        selectedWarehouse,
        setSelectedWarehouse,
        currentPipeline,
        setCurrentPipeline,
        chatMessages,
        addChatMessage,
        clearChat,
        pipelineConfig,
        updatePipelineConfig,
        resetPipeline,
      }}
    >
      {children}
    </PipelineContext.Provider>
  );
};

export const usePipeline = () => {
  const context = useContext(PipelineContext);
  if (!context) {
    throw new Error('usePipeline must be used within PipelineProvider');
  }
  return context;
};

export default PipelineContext;
