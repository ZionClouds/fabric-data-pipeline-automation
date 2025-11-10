import React, { useState, useRef, useEffect } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import { useAuth } from '../contexts/AuthContext';
import { pipelineApi } from '../services/api';
import ReactMarkdown from 'react-markdown';
import {
  Box,
  Typography,
  TextField,
  IconButton,
  Paper,
  Avatar,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  Fade,
  InputAdornment
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
  AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';

// API URL from env config (supports Docker runtime injection)
const API_BASE_URL = window._env_?.REACT_APP_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AIChat = () => {
  const {
    selectedWorkspace,
    selectedLakehouse,
    selectedWarehouse,

    chatMessages,
    addChatMessage,
    setCurrentPipeline,
    clearChat,

    updatePipelineConfig,
    conversationId,
    setConversationId,
    currentJobId,
    setCurrentJobId

  } = usePipeline();
  const { user } = useAuth();
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const prevWorkspaceRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Restore conversation_id and messages from database on mount
  useEffect(() => {
    const loadConversationHistory = async () => {
      const storedConversationId = localStorage.getItem('conversationId');

      if (storedConversationId && !conversationId && chatMessages.length === 0) {
        setConversationId(storedConversationId);
        console.log('Restored conversation ID from localStorage:', storedConversationId);

        try {
          // Fetch conversation with messages from database
          const response = await fetch(`${API_BASE_URL}/api/conversations/${storedConversationId}`);

          if (response.ok) {
            const data = await response.json();
            console.log('Loaded conversation from database:', data);

            // Restore messages to chat
            if (data.messages && data.messages.length > 0) {
              data.messages.forEach(msg => {
                addChatMessage(msg.role, msg.content);
              });
              console.log(`Restored ${data.messages.length} messages from database`);
            }
          } else {
            console.warn('Conversation not found in database, starting fresh');
            localStorage.removeItem('conversationId');
          }
        } catch (error) {
          console.error('Failed to load conversation history:', error);
          // Don't block the user if loading fails
        }
      }
    };

    loadConversationHistory();
  }, []);

  // Clear chat when workspace changes
  useEffect(() => {
    if (selectedWorkspace && prevWorkspaceRef.current && prevWorkspaceRef.current.id !== selectedWorkspace.id) {
      clearChat();
      // Clear conversation ID when switching workspaces
      setConversationId(null);
      localStorage.removeItem('conversationId');
    }
    prevWorkspaceRef.current = selectedWorkspace;
  }, [selectedWorkspace, clearChat, setConversationId]);

  const handleSendMessage = async (messageToSend = null) => {
    const messageContent = messageToSend || inputMessage.trim();

    // Clear input if using the input field
    if (!messageToSend) {
      setInputMessage('');
    }

    // Add user message
    addChatMessage('user', messageContent);

    try {
      setIsLoading(true);

      // Create clean, serializable data structure
      const requestData = {
        workspace_id: selectedWorkspace?.id,
        lakehouse_name: selectedLakehouse?.name || null,
        warehouse_name: selectedWarehouse?.name || null,
        messages: [
          ...chatMessages.map(m => ({
            role: String(m.role),
            content: String(m.content)
          })),
          { role: 'user', content: String(messageContent) }
        ],
        context: {
          workspace: {
            id: selectedWorkspace?.id,
            name: selectedWorkspace?.name || '',
            displayName: selectedWorkspace?.displayName || ''
          },
          lakehouse: {
            id: selectedLakehouse?.id || null,
            name: selectedLakehouse?.name || null
          },
          warehouse: {
            id: selectedWarehouse?.id || null,
            name: selectedWarehouse?.name || null
          },
          user: typeof user === 'string' ? user : (user?.email || '')
        }
      };

      // Call Claude API
      const response = await pipelineApi.chat(requestData);

      // Save conversation_id from response
      if (response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
        console.log('Conversation ID:', response.data.conversation_id);

        // Store in localStorage for persistence across page refreshes
        localStorage.setItem('conversationId', response.data.conversation_id);
      }

      // Save job_id if present
      if (response.data.job_id) {
        setCurrentJobId(response.data.job_id);
        console.log('Job ID:', response.data.job_id);
      }

      // Ensure content is a string
      const content = typeof response.data.content === 'string'
        ? response.data.content
        : JSON.stringify(response.data.content);

      // Add AI response
      addChatMessage('assistant', content);

      // Extract pipeline name from summary if present
      const pipelineNameMatch = content.match(/Pipeline Name:\s*(.+)/i);
      if (pipelineNameMatch && pipelineNameMatch[1]) {
        const extractedPipelineName = pipelineNameMatch[1].trim();
        console.log('Extracted pipeline name from chat:', extractedPipelineName);
        updatePipelineConfig({ pipeline_name: extractedPipelineName });
      }

      // If response contains pipeline preview, update current pipeline
      if (response.data.pipeline_preview) {
        setCurrentPipeline(response.data.pipeline_preview);
      }

    } catch (error) {
      console.error('Chat error:', error);
      addChatMessage('assistant', '❌ Sorry, I encountered an error. Please try again.');
    } finally {
      setIsLoading(false);

      // Auto-focus input field after response
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 100);
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
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: '#fafafa',
        position: 'relative',
        overflow: 'hidden' // Ensure no overflow
      }}
    >
      {/* Messages Area */}
      <Box 
        sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          position: 'relative',
          minHeight: 0, // Important for flex shrinking
          overflow: 'hidden'
        }}
      >
        {chatMessages.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 2, // Reduced padding for more space
              overflow: 'auto'
            }}
          >
            <Box sx={{ maxWidth: 480, textAlign: 'center' }}>
              <Avatar
                sx={{
                  width: 56,
                  height: 56,
                  mx: 'auto',
                  mb: 2,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 6px 24px rgba(102, 126, 234, 0.2)',
                  border: '2px solid rgba(255, 255, 255, 0.9)',
                  animation: 'pulse 2s infinite ease-in-out',
                  '@keyframes pulse': {
                    '0%': {
                      transform: 'scale(1)',
                      boxShadow: '0 6px 24px rgba(102, 126, 234, 0.2)',
                    },
                    '50%': {
                      transform: 'scale(1.05)',
                      boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                    },
                    '100%': {
                      transform: 'scale(1)',
                      boxShadow: '0 6px 24px rgba(102, 126, 234, 0.2)',
                    },
                  },
                }}
              >
                <AutoAwesomeIcon sx={{ fontSize: 28, color: 'white' }} />
              </Avatar>
              
              <Typography 
                variant="h5" 
                gutterBottom 
                fontWeight="600" 
                sx={{ 
                  mb: 1,
                  background: 'linear-gradient(135deg, #1f2937 0%, #4f46e5 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  letterSpacing: '-0.01em',
                }}
              >
                Let's build something amazing
              </Typography>
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ 
                  mb: 2.5,
                  fontSize: '0.9rem',
                  lineHeight: 1.5,
                  maxWidth: 400,
                  mx: 'auto',
                  fontWeight: 400,
                }}
              >
                Tell me about your data pipeline needs and I'll help you design the perfect solution.
              </Typography>
              
              <Typography 
                variant="subtitle2" 
                gutterBottom 
                color="text.primary" 
                sx={{ 
                  mb: 2,
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  color: '#374151',
                }}
              >
                ✨ Quick Start
              </Typography>
              
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, 
                gap: 1.2,
                maxWidth: 520,
                mx: 'auto',
              }}>
                {starterQuestions.map((question, index) => (
                  <Card
                    key={index}
                    onClick={() => {
                      handleSendMessage(question);
                    }}
                    sx={{
                      cursor: 'pointer',
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      borderRadius: 2,
                      border: '1.5px solid rgba(102, 126, 234, 0.12)',
                      bgcolor: 'rgba(255, 255, 255, 0.8)',
                      backdropFilter: 'blur(20px)',
                      position: 'relative',
                      overflow: 'hidden',
                      height: 'auto',
                      minHeight: '52px',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '2px',
                        background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                        transform: 'translateX(-100%)',
                        transition: 'transform 0.3s ease',
                      },
                      '&:hover': {
                        transform: 'translateY(-2px) scale(1.005)',
                        boxShadow: '0 8px 24px rgba(102, 126, 234, 0.12)',
                        borderColor: 'rgba(102, 126, 234, 0.25)',
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        '&::before': {
                          transform: 'translateX(0)',
                        },
                      },
                      '&:active': {
                        transform: 'translateY(-1px) scale(1.002)',
                      },
                    }}
                  >
                    <CardContent sx={{ p: 1.5, py: 1.25, '&:last-child': { pb: 1.25 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Box 
                          sx={{ 
                            width: 28,
                            height: 28,
                            borderRadius: 1.25,
                            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}
                        >
                          <Typography sx={{ fontSize: '12px' }}>
                            {index === 0 && '🗄️'}
                            {index === 1 && '📊'}
                            {index === 2 && '📁'}
                            {index === 3 && '🏗️'}
                          </Typography>
                        </Box>
                        <Box sx={{ flex: 1, textAlign: 'left' }}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontSize: '0.8rem',
                              lineHeight: 1.3,
                              color: 'text.primary',
                              fontWeight: 600,
                              letterSpacing: '-0.005em',
                            }}
                          >
                            {question}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
              
              <Typography 
                variant="caption" 
                color="text.secondary" 
                sx={{ 
                  mt: 2,
                  display: 'block',
                  fontSize: '0.75rem',
                  opacity: 0.7,
                  fontStyle: 'italic',
                }}
              >
                Or type your question below
              </Typography>
            </Box>
          </Box>
        ) : (
          <Box
            sx={{
              flex: 1,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              position: 'relative'
            }}
          >
            {/* Chat Messages Container */}
            <Box
              sx={{
                flex: 1,
                overflowY: 'auto',
                overflowX: 'hidden',
                px: 2,
                py: 1.5,
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
                scrollBehavior: 'smooth',
                background: 'linear-gradient(to bottom, #fafafa 0%, #f5f7fa 100%)',
                '&::-webkit-scrollbar': {
                  width: '6px',
                },
                '&::-webkit-scrollbar-track': {
                  background: 'transparent',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: 'rgba(102, 126, 234, 0.3)',
                  borderRadius: '3px',
                  '&:hover': {
                    background: 'rgba(102, 126, 234, 0.5)',
                  },
                },
              }}
            >
              <Box sx={{ maxWidth: '100%', mx: 'auto', width: '100%' }}>
                {chatMessages.map((message, index) => (
                  <Box
                    key={index}
                    sx={{
                      display: 'flex',
                      mb: 1.8,
                      alignItems: 'flex-start',
                      ...(message.role === 'user' ? {
                        justifyContent: 'flex-end',
                      } : {
                        justifyContent: 'flex-start',
                      })
                    }}
                  >
                    {/* Assistant Avatar - Left side */}
                    {message.role === 'assistant' && (
                      <Avatar
                        sx={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          width: 32,
                          height: 32,
                          mr: 1.5,
                          flexShrink: 0,
                          boxShadow: '0 2px 8px rgba(102, 126, 234, 0.2)',
                          border: '2px solid white',
                          transition: 'transform 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'scale(1.05)'
                          }
                        }}
                      >
                        <SmartToyIcon sx={{ fontSize: 18, color: 'white' }} />
                      </Avatar>
                    )}

                    {/* Message Content */}
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        maxWidth: message.role === 'user' ? '75%' : '85%',
                        minWidth: '160px'
                      }}
                    >
                      {/* Message Bubble */}
                      <Paper
                        elevation={0}
                        sx={{
                          p: 2,
                          backgroundColor: message.role === 'assistant' 
                            ? 'white' 
                            : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          color: message.role === 'assistant' ? 'text.primary' : 'white',
                          borderRadius: message.role === 'assistant' ? '18px 18px 18px 4px' : '18px 18px 4px 18px',
                          position: 'relative',
                          boxShadow: message.role === 'user' 
                            ? '0 4px 12px rgba(102, 126, 234, 0.15)' 
                            : '0 2px 8px rgba(0,0,0,0.06)',
                          background: message.role === 'user' 
                            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                            : 'white',
                          border: message.role === 'assistant' ? '1px solid rgba(0,0,0,0.04)' : 'none',
                          backdropFilter: 'blur(10px)',
                          transition: 'all 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-1px)',
                            boxShadow: message.role === 'user' 
                              ? '0 6px 16px rgba(102, 126, 234, 0.2)' 
                              : '0 4px 12px rgba(0,0,0,0.1)',
                          },
                          '&::before': message.role === 'assistant' ? {
                            content: '""',
                            position: 'absolute',
                            left: '-4px',
                            top: '16px',
                            width: 0,
                            height: 0,
                            borderTop: '4px solid transparent',
                            borderBottom: '4px solid transparent',
                            borderRight: '4px solid white',
                          } : {
                            content: '""',
                            position: 'absolute',
                            right: '-4px',
                            top: '16px',
                            width: 0,
                            height: 0,
                            borderTop: '4px solid transparent',
                            borderBottom: '4px solid transparent',
                            borderLeft: '4px solid #667eea',
                          }
                        }}
                      >
                        <ReactMarkdown
                          components={{
                            p: ({children}) => (
                              <Typography
                                variant="body1"
                                sx={{
                                  mb: 1.2,
                                  fontSize: '0.875rem',
                                  lineHeight: 1.6,
                                  '&:last-child': { mb: 0 },
                                  color: 'inherit',
                                  fontWeight: 400,
                                  letterSpacing: '0.005em'
                                }}
                              >
                                {children}
                              </Typography>
                            ),
                            h1: ({children}) => (
                              <Typography
                                variant="h6"
                                sx={{
                                  mt: 2,
                                  mb: 1.5,
                                  fontSize: '1.1rem',
                                  fontWeight: 700,
                                  color: 'inherit'
                                }}
                              >
                                {children}
                              </Typography>
                            ),
                            h2: ({children}) => (
                              <Typography
                                variant="h6"
                                sx={{
                                  mt: 2,
                                  mb: 1.2,
                                  fontSize: '1rem',
                                  fontWeight: 700,
                                  color: 'inherit'
                                }}
                              >
                                {children}
                              </Typography>
                            ),
                            h3: ({children}) => (
                              <Typography
                                variant="subtitle1"
                                sx={{
                                  mt: 1.5,
                                  mb: 1,
                                  fontSize: '0.95rem',
                                  fontWeight: 600,
                                  color: 'inherit'
                                }}
                              >
                                {children}
                              </Typography>
                            ),
                            strong: ({children}) => (
                              <Typography
                                component="strong"
                                sx={{
                                  fontWeight: 700,
                                  color: 'inherit'
                                }}
                              >
                                {children}
                              </Typography>
                            ),
                            ul: ({children}) => (
                              <Box
                                component="ul"
                                sx={{
                                  pl: 3,
                                  my: 1,
                                  '& ul': {
                                    pl: 2,
                                    mt: 0.5,
                                    mb: 0.5
                                  }
                                }}
                              >
                                {children}
                              </Box>
                            ),
                            ol: ({children}) => (
                              <Box
                                component="ol"
                                sx={{
                                  pl: 3,
                                  my: 1,
                                  '& ol': {
                                    pl: 2,
                                    mt: 0.5,
                                    mb: 0.5
                                  }
                                }}
                              >
                                {children}
                              </Box>
                            ),
                            li: ({children}) => (
                              <Typography
                                component="li"
                                sx={{
                                  fontSize: '0.875rem',
                                  lineHeight: 1.6,
                                  mb: 0.5,
                                  color: 'inherit',
                                  pl: 0.5
                                }}
                              >
                                {children}
                              </Typography>
                            ),
                            code: ({children}) => (
                              <Box
                                component="code"
                                sx={{
                                  bgcolor: message.role === 'user'
                                    ? 'rgba(255,255,255,0.25)'
                                    : 'rgba(102, 126, 234, 0.08)',
                                  px: 0.8,
                                  py: 0.3,
                                  borderRadius: 0.8,
                                  fontSize: '0.8em',
                                  fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                                  color: 'inherit',
                                  fontWeight: 500
                                }}
                              >
                                {children}
                              </Box>
                            )
                          }}
                        >
                          {typeof message.content === 'string'
                            ? message.content
                            : (typeof message.content === 'object'
                                ? JSON.stringify(message.content)
                                : String(message.content))}
                        </ReactMarkdown>
                      </Paper>
                      
                      {/* Timestamp */}
                      <Typography
                        variant="caption"
                        sx={{
                          mt: 0.3,
                          opacity: 0.5,
                          fontSize: '0.7rem',
                          textAlign: message.role === 'user' ? 'right' : 'left',
                          px: 0.5
                        }}
                      >
                        {new Date(message.timestamp || new Date()).toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </Typography>
                    </Box>

                    {/* User Avatar - Right side */}
                    {message.role === 'user' && (
                      <Avatar
                        sx={{
                          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                          width: 32,
                          height: 32,
                          ml: 1.5,
                          flexShrink: 0,
                          boxShadow: '0 2px 8px rgba(245, 87, 108, 0.2)',
                          border: '2px solid white',
                          transition: 'transform 0.2s ease-in-out',
                          '&:hover': {
                            transform: 'scale(1.05)'
                          }
                        }}
                      >
                        <PersonIcon sx={{ fontSize: 18, color: 'white' }} />
                      </Avatar>
                    )}
                  </Box>
                ))}
                
                {/* Loading State */}
                {isLoading && (
                  <Fade in={isLoading}>
                    <Box sx={{ display: 'flex', mb: 1.5, alignItems: 'flex-start' }}>
                      <Avatar
                        sx={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          width: 32,
                          height: 32,
                          mr: 1.5,
                          flexShrink: 0,
                          boxShadow: '0 2px 8px rgba(102, 126, 234, 0.2)',
                          border: '2px solid white'
                        }}
                      >
                        <SmartToyIcon sx={{ fontSize: 18, color: 'white' }} />
                      </Avatar>
                      <Paper
                        elevation={1}
                        sx={{
                          p: 1.2,
                          borderRadius: 2,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1.2,
                          bgcolor: 'white',
                          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                          position: 'relative',
                          '&::before': {
                            content: '""',
                            position: 'absolute',
                            left: '-4px',
                            top: '10px',
                            width: 0,
                            height: 0,
                            borderTop: '4px solid transparent',
                            borderBottom: '4px solid transparent',
                            borderRight: '4px solid white',
                          }
                        }}
                      >
                        <CircularProgress size={14} />
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                          AI is thinking...
                        </Typography>
                      </Paper>
                    </Box>
                  </Fade>
                )}
                
                {/* Scroll anchor */}
                <div ref={messagesEndRef} />
              </Box>
            </Box>
          </Box>
        )}
      </Box>

      {/* Input Area */}
      <Paper 
        elevation={0} 
        sx={{ 
          px: 2.5,
          py: 1.5,
          borderTop: '1px solid #e8f4fd',
          flexShrink: 0,
          bgcolor: 'white',
          mx: 0,
          mb: 0,
          borderRadius: 0,
          boxShadow: '0 -6px 25px rgba(102, 126, 234, 0.08), 0 -2px 10px rgba(102, 126, 234, 0.04)'
        }}
      >
        <Box sx={{ maxWidth: '80%', mx: 'auto' }}>
          <TextField
            fullWidth
            multiline
            maxRows={3}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about data sources, transformations, or pipeline architecture..."
            disabled={isLoading}
            size="small"
            inputRef={inputRef}
            autoFocus
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    color="primary"
                    size="small"
                    sx={{
                      bgcolor: 'primary.main',
                      color: 'white',
                      width: 30,
                      height: 30,
                      '&:hover': {
                        bgcolor: 'primary.dark'
                      },
                      '&.Mui-disabled': {
                        bgcolor: 'action.disabled'
                      }
                    }}
                  >
                    {isLoading ? (
                      <CircularProgress size={18} color="inherit" />
                    ) : (
                      <SendIcon sx={{ fontSize: 18 }} />
                    )}
                  </IconButton>
                </InputAdornment>
              )
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                bgcolor: 'rgba(248, 250, 252, 0.8)',
                backdropFilter: 'blur(10px)',
                border: '2px solid rgba(102, 126, 234, 0.1)',
                '& fieldset': {
                  border: 'none'
                },
                '&:hover': {
                  borderColor: 'rgba(102, 126, 234, 0.2)',
                  bgcolor: 'rgba(248, 250, 252, 0.9)'
                },
                '&.Mui-focused': {
                  borderColor: 'rgba(102, 126, 234, 0.4)',
                  bgcolor: 'white',
                  boxShadow: '0 0 0 4px rgba(102, 126, 234, 0.1)'
                }
              }
            }}
          />
          
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mt: 0.75
            }}
          >
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              Press Enter to send, Shift+Enter for new line
            </Typography>
            {inputMessage.length > 100 && (
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                {inputMessage.length}/2000
              </Typography>
            )}
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default AIChat;
