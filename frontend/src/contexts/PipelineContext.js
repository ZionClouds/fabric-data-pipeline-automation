import React, { createContext, useState, useContext } from 'react';

const PipelineContext = createContext();

export const PipelineProvider = ({ children }) => {
  const [selectedWorkspace, setSelectedWorkspace] = useState(null);
  const [currentPipeline, setCurrentPipeline] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [pipelineConfig, setPipelineConfig] = useState({
    source_type: null,
    tables: [],
    transformations: [],
    use_medallion: true,
    schedule: 'manual'
  });

  const addChatMessage = (role, content) => {
    setChatMessages(prev => [...prev, { role, content, timestamp: new Date() }]);
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
      schedule: 'manual'
    });
  };

  return (
    <PipelineContext.Provider
      value={{
        selectedWorkspace,
        setSelectedWorkspace,
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
