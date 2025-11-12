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
  InputAdornment,
  Alert,
  Fab,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  Menu,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
  AutoAwesome as AutoAwesomeIcon,
  Visibility as VisibilityIcon,
  RocketLaunch as RocketLaunchIcon,
  AddCircle as AddCircleIcon,
  Delete as DeleteIcon,
  AccessTime as AccessTimeIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
  Chat as ChatIcon
} from '@mui/icons-material';

// API URL from env config (supports Docker runtime injection)
const API_BASE_URL = window._env_?.REACT_APP_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8080';

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
    setCurrentJobId,
    setSelectedJobForPreview,
    handleTabClick,
    isTemporaryChat,
    setIsTemporaryChat,
    setChatMessages
  } = usePipeline();

  const { user } = useAuth();
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const prevWorkspaceRef = useRef(null);
  const inputRef = useRef(null);

  // Conversation management state
  const [conversations, setConversations] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renameTitle, setRenameTitle] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Load conversations when component mounts or user changes
  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user]);

  // Restore conversation_id and messages from database on mount
  useEffect(() => {
    const loadConversationHistory = async () => {
      const storedConversationId = localStorage.getItem('conversationId');

      if (storedConversationId && !conversationId && chatMessages.length === 0) {
        setConversationId(storedConversationId);
        console.log('Restored conversation ID from localStorage:', storedConversationId);

        try {
          const response = await pipelineApi.getConversation(storedConversationId);
          const data = response.data;
          console.log('Loaded conversation from database:', data);

          if (data.messages && data.messages.length > 0) {
            setChatMessages(data.messages.map(msg => ({
              role: msg.role,
              content: msg.content,
              timestamp: new Date(msg.timestamp)
            })));
            console.log(`Restored ${data.messages.length} messages from database`);
          }
        } catch (error) {
          console.error('Failed to load conversation history:', error);
          localStorage.removeItem('conversationId');
        }
      }
    };

    loadConversationHistory();
  }, []);

  // Clear chat when workspace changes
  useEffect(() => {
    if (selectedWorkspace && prevWorkspaceRef.current && prevWorkspaceRef.current.id !== selectedWorkspace.id) {
      handleNewChat();
    }
    prevWorkspaceRef.current = selectedWorkspace;
  }, [selectedWorkspace]);

  const loadConversations = async () => {
    if (!user) return;

    setIsLoadingConversations(true);

    try {
      const params = {
        user_email: user.email,
        status: 'active',
        limit: 50
      };

      const response = await pipelineApi.getConversations(params);
      setConversations(response.data || []);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  const handleNewChat = async () => {
    // Mark current conversation as completed if exists
    if (conversationId) {
      try {
        await pipelineApi.updateConversation(
          conversationId,
          null, // Don't change title
          'completed' // Mark as completed so a new conversation will be created
        );
      } catch (err) {
        console.error('Failed to update conversation status:', err);
      }
    }

    clearChat();
    setConversationId(null);
    localStorage.removeItem('conversationId');
    await loadConversations(); // Refresh list
  };

  const handleSelectConversation = async (convId) => {
    if (convId === conversationId) return;

    try {
      const response = await pipelineApi.getConversation(convId);
      const data = response.data;

      clearChat();
      setConversationId(data.conversation_id);
      localStorage.setItem('conversationId', data.conversation_id);

      if (data.messages && data.messages.length > 0) {
        setChatMessages(data.messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp)
        })));
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleMenuOpen = (event) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleRenameClick = () => {
    const currentConv = conversations.find(c => c.conversation_id === conversationId);
    setRenameTitle(currentConv?.title || '');
    setRenameDialogOpen(true);
    handleMenuClose();
  };

  const handleRenameConfirm = async () => {
    if (!conversationToDelete || !renameTitle.trim()) return;

    try {
      await pipelineApi.updateConversation(conversationToDelete, renameTitle.trim(), null);
      await loadConversations(); // Refresh list
      setRenameDialogOpen(false);
      setConversationToDelete(null);
    } catch (err) {
      console.error('Failed to rename conversation:', err);
    }
  };

  const handleDeleteClick = () => {
    setConversationToDelete(conversationId);
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (!conversationToDelete) return;

    try {
      await pipelineApi.deleteConversation(conversationToDelete);

      if (conversationToDelete === conversationId) {
        handleNewChat();
      } else {
        await loadConversations();
      }

      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setDeleteDialogOpen(false);
    }
  };

  const getCurrentConversationTitle = () => {
    const currentConv = conversations.find(c => c.conversation_id === conversationId);
    return currentConv?.title || 'New Conversation';
  };

  // Handle quick access to pipeline preview
  const handlePreviewShortcut = () => {
    handleTabClick('preview');
  };

  // Check if preview shortcut should be shown
  const shouldShowPreviewShortcut = chatMessages.length > 0 && selectedWorkspace;

  const handleSendMessage = async (messageToSend = null) => {
    const messageContent = messageToSend || inputMessage.trim();

    if (!messageToSend) {
      setInputMessage('');
    }

    addChatMessage('user', messageContent);

    try {
      setIsLoading(true);

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
          lakehouse_name: selectedLakehouse?.name || null,
          warehouse_name: selectedWarehouse?.name || null
        }
      };

      const response = await pipelineApi.chat(requestData);

      addChatMessage('assistant', response.data.content);

      // Update conversation ID if returned
      if (response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
        localStorage.setItem('conversationId', response.data.conversation_id);
        await loadConversations(); // Refresh to show new/updated conversation
      }

      // Handle job ID
      if (response.data.job_id) {
        setCurrentJobId(response.data.job_id);
      }

      // Handle pipeline name
      if (response.data.pipeline_name) {
        updatePipelineConfig({ pipeline_name: response.data.pipeline_name });
        console.log('Pipeline name extracted from chat:', response.data.pipeline_name);
      }

      // Handle suggestions
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        // Suggestions handled below
      }

      // Handle pipeline preview
      if (response.data.pipeline_preview) {
        setCurrentPipeline(response.data.pipeline_preview);
      }

    } catch (error) {
      console.error('Chat error:', error);
      addChatMessage('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now - date;
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays}d ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <Box 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column', 
        bgcolor: '#fafafa',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Conversation Selector Header */}
      <Paper
        elevation={0}
        sx={{
          p: 1.25,
          borderRadius: 0,
          borderBottom: '1px solid #e8f4fd',
          bgcolor: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 1.25,
          boxShadow: '0 2px 10px rgba(102, 126, 234, 0.04)'
        }}
      >
        <Box
          sx={{
            width: 30,
            height: 30,
            borderRadius: 1.25,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 3px 10px rgba(102, 126, 234, 0.2)'
          }}
        >
          <ChatIcon sx={{ color: 'white', fontSize: 17 }} />
        </Box>

        <FormControl sx={{ flex: 1, minWidth: 160 }}>
          <Select
            value={conversationId || ''}
            displayEmpty
            onChange={(e) => e.target.value && handleSelectConversation(e.target.value)}
            size="small"
            renderValue={() => (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: '#1f2937', fontSize: '0.85rem' }}>
                  {getCurrentConversationTitle()}
                </Typography>
                {conversationId && (
                  <Chip
                    label={`${chatMessages.length} msgs`}
                    size="small"
                    sx={{ 
                      height: 17, 
                      fontSize: '0.65rem',
                      bgcolor: 'rgba(102, 126, 234, 0.1)',
                      color: '#667eea',
                      fontWeight: 600,
                      '& .MuiChip-label': {
                        px: 0.75
                      }
                    }}
                  />
                )}
              </Box>
            )}
            MenuProps={{
              PaperProps: {
                sx: {
                  maxHeight: 320,
                  borderRadius: 2,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                  mt: 0.5,
                  width: '260px',
                  '& .MuiList-root': {
                    maxHeight: 320,
                    overflowY: 'auto',
                    overflowX: 'hidden',
                    '&::-webkit-scrollbar': {
                      width: '6px',
                    },
                    '&::-webkit-scrollbar-track': {
                      background: 'rgba(0,0,0,0.05)',
                      borderRadius: '10px',
                    },
                    '&::-webkit-scrollbar-thumb': {
                      background: 'rgba(102, 126, 234, 0.3)',
                      borderRadius: '10px',
                      '&:hover': {
                        background: 'rgba(102, 126, 234, 0.5)',
                      },
                    },
                  }
                }
              }
            }}
            sx={{
              fontSize: '0.85rem',
              '& .MuiSelect-select': {
                py: 0.85
              },
              '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
              '&:hover .MuiOutlinedInput-notchedOutline': { border: 'none' },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': { border: 'none' }
            }}
          >
            <MenuItem disabled>
              <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', fontSize: '0.72rem' }}>
                {isLoadingConversations ? 'Loading conversations...' : 'Select a conversation'}
              </Typography>
            </MenuItem>
            <Divider sx={{ my: 0.5 }} />
            {conversations.length === 0 && !isLoadingConversations ? (
              <MenuItem disabled>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', py: 1.5 }}>
                  <ChatIcon sx={{ fontSize: 30, color: 'text.disabled', mb: 0.75, opacity: 0.3 }} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem', fontWeight: 500 }}>
                    No sessions found
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.68rem', mt: 0.25 }}>
                    Start a new conversation
                  </Typography>
                </Box>
              </MenuItem>
            ) : (
              conversations.map((conv) => (
                <MenuItem 
                  key={conv.conversation_id} 
                  value={conv.conversation_id}
                  sx={{
                    borderRadius: 1,
                    mx: 0.5,
                    my: 0.25,
                    py: 0.65,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    '&:hover': {
                      bgcolor: 'rgba(102, 126, 234, 0.08)'
                    },
                    '&.Mui-selected': {
                      bgcolor: 'rgba(102, 126, 234, 0.12)',
                      '&:hover': {
                        bgcolor: 'rgba(102, 126, 234, 0.15)'
                      }
                    }
                  }}
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontWeight: conv.conversation_id === conversationId ? 600 : 500,
                        color: conv.conversation_id === conversationId ? '#667eea' : 'text.primary',
                        fontSize: '0.82rem',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {conv.title || 'New Conversation'}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mt: 0.25 }}>
                      <AccessTimeIcon sx={{ fontSize: 11, color: 'text.secondary', opacity: 0.6 }} />
                      <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.67rem' }}>
                        {formatDate(conv.updated_at)}
                      </Typography>
                      {conv.message_count > 0 && (
                        <Chip
                          label={`${conv.message_count} msgs`}
                          size="small"
                          sx={{ 
                            height: 15, 
                            fontSize: '0.62rem', 
                            bgcolor: 'rgba(0,0,0,0.04)',
                            '& .MuiChip-label': {
                              px: 0.5
                            }
                          }}
                        />
                      )}
                    </Box>
                  </Box>
                  <IconButton
                    size="small"
                    className="options-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setConversationToDelete(conv.conversation_id);
                      setAnchorEl(e.currentTarget);
                    }}
                    sx={{
                      opacity: 0.6,
                      transition: 'all 0.2s',
                      ml: 0.5,
                      p: 0.3,
                      '&:hover': {
                        opacity: 1,
                        bgcolor: 'rgba(0,0,0,0.08)',
                        transform: 'scale(1.1)'
                      }
                    }}
                  >
                    <MoreVertIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                </MenuItem>
              ))
            )}
          </Select>
        </FormControl>

        <Tooltip title="New Chat" arrow placement="bottom">
          <IconButton 
            onClick={handleNewChat} 
            size="small"
            sx={{
              position: 'relative',
              bgcolor: 'rgba(102, 126, 234, 0.08)',
              border: '1.5px solid transparent',
              borderRadius: 2,
              width: 30,
              height: 30,
              color: '#667eea',
              overflow: 'hidden',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                opacity: 0,
                transition: 'opacity 0.3s ease'
              },
              '&:hover': {
                borderColor: 'rgba(102, 126, 234, 0.4)',
                transform: 'translateY(-1px) scale(1.05)',
                boxShadow: '0 6px 16px rgba(102, 126, 234, 0.25)',
                '&::before': {
                  opacity: 1
                },
                '& .MuiSvgIcon-root': {
                  color: 'white',
                  transform: 'rotate(90deg)'
                }
              },
              '&:active': {
                transform: 'translateY(0) scale(1.02)'
              }
            }}
          >
            <AddIcon 
              sx={{ 
                fontSize: 17,
                position: 'relative',
                zIndex: 1,
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }} 
            />
          </IconButton>
        </Tooltip>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          PaperProps={{
            sx: {
              borderRadius: 2,
              boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
              minWidth: 140
            }
          }}
        >
          <MenuItem 
            onClick={() => {
              const conv = conversations.find(c => c.conversation_id === conversationToDelete);
              setRenameTitle(conv?.title || '');
              setRenameDialogOpen(true);
              handleMenuClose();
            }}
            sx={{
              borderRadius: 1,
              mx: 0.5,
              my: 0.25,
              py: 0.65,
              fontSize: '0.8rem',
              '&:hover': {
                bgcolor: 'rgba(102, 126, 234, 0.08)'
              }
            }}
          >
            <ListItemIcon>
              <EditIcon fontSize="small" sx={{ color: '#667eea', fontSize: 16 }} />
            </ListItemIcon>
            <ListItemText primaryTypographyProps={{ fontSize: '0.8rem' }}>Rename</ListItemText>
          </MenuItem>
          <MenuItem 
            onClick={() => {
              setDeleteDialogOpen(true);
              handleMenuClose();
            }}
            sx={{
              borderRadius: 1,
              mx: 0.5,
              my: 0.25,
              py: 0.65,
              fontSize: '0.8rem',
              '&:hover': {
                bgcolor: 'rgba(244, 67, 54, 0.08)'
              }
            }}
          >
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" sx={{ fontSize: 16 }} />
            </ListItemIcon>
            <ListItemText primaryTypographyProps={{ fontSize: '0.8rem', color: 'error.main' }}>Delete</ListItemText>
          </MenuItem>
        </Menu>
      </Paper>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          minHeight: 0,
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
              overflow: 'auto'
            }}
          >
            <Box sx={{ maxWidth: 520, textAlign: 'center', width: '100%' }}>
              <Avatar
                sx={{
                  width: 64,
                  height: 64,
                  mx: 'auto',
                  mb: 3,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.25)',
                  border: '3px solid rgba(255, 255, 255, 0.9)',
                  animation: 'pulse 2s infinite ease-in-out',
                  '@keyframes pulse': {
                    '0%': {
                      transform: 'scale(1)',
                      boxShadow: '0 8px 24px rgba(102, 126, 234, 0.25)',
                    },
                    '50%': {
                      transform: 'scale(1.05)',
                      boxShadow: '0 12px 32px rgba(102, 126, 234, 0.35)',
                    },
                    '100%': {
                      transform: 'scale(1)',
                      boxShadow: '0 8px 24px rgba(102, 126, 234, 0.25)',
                    },
                  },
                }}
              >
                <AutoAwesomeIcon sx={{ fontSize: 32, color: 'white' }} />
              </Avatar>

              <Typography
                variant="h5"
                gutterBottom
                sx={{
                  mb: 1.5,
                  fontWeight: 700,
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
                  mb: 3,
                  fontSize: '0.95rem',
                  lineHeight: 1.6,
                  maxWidth: 450,
                  mx: 'auto',
                }}
              >
                Tell me about your data pipeline needs and I'll help you design the perfect solution.
              </Typography>

              {!selectedWorkspace && (
                <Alert
                  severity="warning"
                  icon={<AutoAwesomeIcon />}
                  sx={{
                    mb: 3,
                    maxWidth: 500,
                    mx: 'auto',
                    borderRadius: 2,
                    bgcolor: 'rgba(255, 152, 0, 0.08)',
                    border: '1px solid rgba(255, 152, 0, 0.25)',
                    '& .MuiAlert-icon': {
                      color: '#ff9800'
                    }
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Please select a workspace from the sidebar to continue
                  </Typography>
                </Alert>
              )}

              <Typography
                variant="subtitle2"
                sx={{
                  mb: 2,
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  color: '#374151',
                }}
              >
                ✨ Quick Start
              </Typography>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' },
                  gap: 1.5,
                  maxWidth: 520,
                  mx: 'auto',
                }}
              >
                {[
                  { icon: '💾', text: 'I want to ingest data from SQL Server' },
                  { icon: '📊', text: 'Help me build a pipeline for customer analytics' },
                  { icon: '📄', text: 'I need to load CSV files from Blob Storage' },
                  { icon: '🏆', text: 'Create a pipeline with Bronze/Silver/Gold layers' }
                ].map((item, index) => (
                  <Card
                    key={index}
                    onClick={() => selectedWorkspace && handleSendMessage(item.text)}
                    sx={{
                      cursor: selectedWorkspace ? 'pointer' : 'not-allowed',
                      opacity: selectedWorkspace ? 1 : 0.5,
                      transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                      borderRadius: 2,
                      border: '1.5px solid rgba(102, 126, 234, 0.12)',
                      bgcolor: 'rgba(255, 255, 255, 0.8)',
                      backdropFilter: 'blur(20px)',
                      position: 'relative',
                      overflow: 'hidden',
                      minHeight: '64px',
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
                        transform: selectedWorkspace ? 'translateY(-2px) scale(1.02)' : 'none',
                        boxShadow: selectedWorkspace ? '0 8px 24px rgba(102, 126, 234, 0.15)' : 'none',
                        borderColor: 'rgba(102, 126, 234, 0.25)',
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        '&::before': {
                          transform: 'translateX(0)',
                        },
                      },
                    }}
                  >
                    <CardContent sx={{ p: 1.75, '&:last-child': { pb: 1.75 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Box
                          sx={{
                            width: 36,
                            height: 36,
                            borderRadius: 1.5,
                            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}
                        >
                          <Typography sx={{ fontSize: '18px' }}>{item.icon}</Typography>
                        </Box>
                        <Typography
                          variant="body2"
                          sx={{
                            fontSize: '0.85rem',
                            lineHeight: 1.4,
                            fontWeight: 600,
                            letterSpacing: '-0.005em',
                            flex: 1,
                            textAlign: 'left'
                          }}
                        >
                          {item.text}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>

              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  mt: 3,
                  display: 'block',
                  fontSize: '0.75rem',
                  fontStyle: 'italic',
                  opacity: 0.7,
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
          py: 2,
          borderTop: '1px solid #e8f4fd',
          flexShrink: 0,
          bgcolor: 'white',
          borderRadius: 0,
          boxShadow: '0 -6px 25px rgba(102, 126, 234, 0.08), 0 -2px 10px rgba(102, 126, 234, 0.04)'
        }}
      >
        <Box sx={{ maxWidth: '85%', mx: 'auto' }}>
          {!selectedWorkspace && (
            <Alert
              severity="info"
              icon={<AutoAwesomeIcon />}
              sx={{
                mb: 1.5,
                borderRadius: 2,
                bgcolor: 'rgba(102, 126, 234, 0.08)',
                border: '1px solid rgba(102, 126, 234, 0.2)',
                '& .MuiAlert-icon': {
                  color: '#667eea'
                }
              }}
            >
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                  Select a workspace to get started
                </Typography>
                <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                  Choose a workspace from the sidebar to start building your data pipeline
                </Typography>
              </Box>
            </Alert>
          )}

          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (inputMessage.trim()) {
                  handleSendMessage();
                }
              }
            }}
            placeholder={
              !selectedWorkspace
                ? "Select a workspace to start chatting..."
                : "Ask about data sources, transformations, or pipeline architecture..."
            }
            disabled={isLoading || !selectedWorkspace}
            size="small"
            inputRef={inputRef}
            autoFocus
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => handleSendMessage()}
                    disabled={!inputMessage.trim() || isLoading || !selectedWorkspace}
                    color="primary"
                    size="small"
                    sx={{
                      bgcolor: 'primary.main',
                      color: 'white',
                      width: 32,
                      height: 32,
                      '&:hover': {
                        bgcolor: 'primary.dark',
                        transform: 'scale(1.05)'
                      },
                      '&.Mui-disabled': {
                        bgcolor: 'action.disabled'
                      },
                      transition: 'all 0.2s'
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

      {/* Rename Dialog */}
      <Dialog 
        open={renameDialogOpen} 
        onClose={() => setRenameDialogOpen(false)}
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 12px 48px rgba(0,0,0,0.15)',
            minWidth: 450
          }
        }}
      >
        <DialogTitle sx={{ 
          fontWeight: 700,
          fontSize: '1.25rem',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          pb: 1
        }}>
          Rename Conversation
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <TextField
            autoFocus
            fullWidth
            label="Conversation Title"
            value={renameTitle}
            onChange={(e) => setRenameTitle(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && renameTitle.trim()) {
                handleRenameConfirm();
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                '&.Mui-focused fieldset': {
                  borderColor: '#667eea',
                  borderWidth: 2
                }
              },
              '& .MuiInputLabel-root.Mui-focused': {
                color: '#667eea'
              }
            }}
          />
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5, pt: 2 }}>
          <Button 
            onClick={() => setRenameDialogOpen(false)}
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              px: 2.5
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleRenameConfirm} 
            variant="contained" 
            disabled={!renameTitle.trim()}
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              px: 3,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                transform: 'translateY(-1px)',
                boxShadow: '0 6px 20px rgba(102, 126, 234, 0.3)'
              },
              transition: 'all 0.2s'
            }}
          >
            Rename
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog 
        open={deleteDialogOpen} 
        onClose={() => setDeleteDialogOpen(false)}
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 12px 48px rgba(0,0,0,0.15)',
            minWidth: 450
          }
        }}
      >
        <DialogTitle sx={{ 
          fontWeight: 700,
          fontSize: '1.25rem',
          color: 'error.main',
          pb: 1
        }}>
          Delete Conversation?
        </DialogTitle>
        <DialogContent sx={{ mt: 1 }}>
          <Alert 
            severity="warning" 
            icon={<DeleteIcon />}
            sx={{ 
              mb: 2,
              borderRadius: 2,
              bgcolor: 'rgba(244, 67, 54, 0.08)',
              border: '1px solid rgba(244, 67, 54, 0.2)'
            }}
          >
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
              This action cannot be undone
            </Typography>
            <Typography variant="caption" color="text.secondary">
              All messages in this conversation will be permanently deleted.
            </Typography>
          </Alert>
          <Typography>
            Are you sure you want to delete this conversation?
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5, pt: 2 }}>
          <Button 
            onClick={() => setDeleteDialogOpen(false)}
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              px: 2.5
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              px: 3,
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: '0 6px 20px rgba(244, 67, 54, 0.3)'
              },
              transition: 'all 0.2s'
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Pipeline Preview Shortcut FAB */}
      {shouldShowPreviewShortcut && (
        <Tooltip title="View Pipeline Preview" arrow placement="left">
          <Fab
            color="primary"
            size="medium"
            onClick={handlePreviewShortcut}
            sx={{
              position: 'fixed',
              bottom: 120,
              right: 24,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              zIndex: 1000,
              '&:hover': {
                transform: 'translateY(-2px) scale(1.05)',
                boxShadow: '0 12px 40px rgba(102, 126, 234, 0.4)',
                background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
              },
              '&:active': {
                transform: 'translateY(0) scale(1.02)',
              },
              '& .MuiFab-root': {
                minHeight: 48,
              },
            }}
          >
            <VisibilityIcon sx={{ fontSize: 24, color: 'white' }} />
          </Fab>
        </Tooltip>
      )}
    </Box>
  );
};

export default AIChat;
