import React, { useState, useRef, useEffect } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import { useAuth } from '../contexts/AuthContext';
import { pipelineApi } from '../services/api';
import ReactMarkdown from 'react-markdown';

const AIChat = () => {
  const { selectedWorkspace, chatMessages, addChatMessage, setCurrentPipeline } = usePipeline();
  const { user } = useAuth();
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedWorkspace) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    // Add user message
    addChatMessage('user', userMessage);

    try {
      setIsLoading(true);

      // Call Claude API
      const response = await pipelineApi.chat({
        workspace_id: selectedWorkspace.id,
        messages: [
          ...chatMessages.map(m => ({ role: m.role, content: m.content })),
          { role: 'user', content: userMessage }
        ],
        context: {
          workspace: selectedWorkspace,
          user: user.email
        }
      });

      // Add AI response
      addChatMessage('assistant', response.data.content);

      // If response contains pipeline preview, update current pipeline
      if (response.data.pipeline_preview) {
        setCurrentPipeline(response.data.pipeline_preview);
      }

    } catch (error) {
      console.error('Chat error:', error);
      addChatMessage('assistant', '❌ Sorry, I encountered an error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const starterQuestions = [
    "I want to ingest data from SQL Server",
    "Help me build a pipeline for customer analytics",
    "I need to load CSV files from Blob Storage",
    "Create a pipeline with Bronze/Silver/Gold layers"
  ];

  return (
    <div className="ai-chat-container">
      <div className="chat-header">
        <h2>💬 Chat with AI Pipeline Architect</h2>
        <p>Describe what you want to build, and I'll help you design the pipeline</p>
      </div>

      {chatMessages.length === 0 ? (
        <div className="chat-welcome">
          <h3>Welcome! How can I help you today?</h3>
          <div className="starter-questions">
            <p>Try asking:</p>
            {starterQuestions.map((question, index) => (
              <button
                key={index}
                className="starter-question"
                onClick={() => setInputMessage(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="chat-messages">
          {chatMessages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-icon">
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-icon">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      <div className="chat-input-container">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Describe your pipeline requirements..."
          className="chat-input"
          rows={3}
          disabled={!selectedWorkspace || isLoading}
        />
        <button
          onClick={handleSendMessage}
          disabled={!inputMessage.trim() || !selectedWorkspace || isLoading}
          className="btn-send"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>

      {!selectedWorkspace && (
        <div className="chat-warning">
          ⚠️ Please select a workspace first
        </div>
      )}
    </div>
  );
};

export default AIChat;
