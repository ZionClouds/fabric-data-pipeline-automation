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

  // Load conversations when component mounts or user/workspace changes
  useEffect(() => {
    if (user && selectedWorkspace) {
      loadConversations();
    }
  }, [user, selectedWorkspace]);

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

      if (selectedWorkspace) {
        params.workspace_id = selectedWorkspace.id;
      }

      const response = await pipelineApi.getConversations(params);
      setConversations(response.data || []);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  const handleNewChat = () => {
    clearChat();
    setConversationId(null);
    localStorage.removeItem('conversationId');
    loadConversations(); // Refresh list
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
    if (!conversationId || !renameTitle.trim()) return;

    try {
      await pipelineApi.updateConversation(conversationId, renameTitle.trim());
      await loadConversations(); // Refresh list
      setRenameDialogOpen(false);
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
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#fafafa' }}>
      {/* Conversation Selector Header */}
      <Paper
        elevation={1}
        sx={{
          p: 2,
          borderRadius: 0,
          borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
          bgcolor: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}
      >
        <ChatIcon sx={{ color: 'primary.main', fontSize: 28 }} />

        <FormControl sx={{ flex: 1, minWidth: 200 }}>
          <Select
            value={conversationId || ''}
            displayEmpty
            onChange={(e) => e.target.value && handleSelectConversation(e.target.value)}
            renderValue={() => (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                  {getCurrentConversationTitle()}
                </Typography>
                {conversationId && (
                  <Chip
                    label={`${chatMessages.length} msgs`}
                    size="small"
                    sx={{ height: 20, fontSize: '0.7rem' }}
                  />
                )}
              </Box>
            )}
            sx={{
              '& .MuiOutlinedInput-notchedOutline': { border: 'none' },
              '&:hover .MuiOutlinedInput-notchedOutline': { border: 'none' },
              '&.Mui-focused .MuiOutlinedInput-notchedOutline': { border: 'none' }
            }}
          >
            <MenuItem disabled>
              <Typography variant="caption" color="text.secondary">
                {isLoadingConversations ? 'Loading...' : 'Select a conversation'}
              </Typography>
            </MenuItem>
            <Divider />
            {conversations.map((conv) => (
              <MenuItem key={conv.conversation_id} value={conv.conversation_id}>
                <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                  <Typography variant="body2" sx={{ fontWeight: conv.conversation_id === conversationId ? 600 : 400 }}>
                    {conv.title || 'New Conversation'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(conv.updated_at)}
                    </Typography>
                    {conv.message_count > 0 && (
                      <Chip
                        label={`${conv.message_count} msg`}
                        size="small"
                        sx={{ height: 18, fontSize: '0.65rem' }}
                      />
                    )}
                  </Box>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Tooltip title="New Chat">
          <IconButton onClick={handleNewChat} color="primary">
            <AddIcon />
          </IconButton>
        </Tooltip>

        {conversationId && (
          <Tooltip title="Options">
            <IconButton onClick={handleMenuOpen}>
              <MoreVertIcon />
            </IconButton>
          </Tooltip>
        )}

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleRenameClick}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Rename</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleDeleteClick}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Delete</ListItemText>
          </MenuItem>
        </Menu>
      </Paper>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}
      >
        {chatMessages.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: 2
            }}
          >
            <AutoAwesomeIcon sx={{ fontSize: 64, color: 'primary.main', opacity: 0.3 }} />
            <Typography variant="h6" color="text.secondary">
              Start a new conversation
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ask me anything about building pipelines!
            </Typography>
          </Box>
        ) : (
          chatMessages.map((message, index) => (
            <Fade key={index} in timeout={300}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                <Avatar
                  sx={{
                    bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                    width: 36,
                    height: 36
                  }}
                >
                  {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                </Avatar>
                <Card
                  elevation={1}
                  sx={{
                    flex: 1,
                    bgcolor: message.role === 'user' ? 'primary.light' : 'white'
                  }}
                >
                  <CardContent>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </CardContent>
                </Card>
              </Box>
            </Fade>
          ))
        )}

        {isLoading && (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
            <Avatar sx={{ bgcolor: 'secondary.main', width: 36, height: 36 }}>
              <SmartToyIcon />
            </Avatar>
            <Card elevation={1} sx={{ flex: 1 }}>
              <CardContent sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <CircularProgress size={16} />
                <Typography variant="body2">Thinking...</Typography>
              </CardContent>
            </Card>
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          borderRadius: 0,
          borderTop: '1px solid rgba(0, 0, 0, 0.12)'
        }}
      >
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
          placeholder="Type your message..."
          variant="outlined"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  color="primary"
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() || isLoading}
                >
                  <SendIcon />
                </IconButton>
              </InputAdornment>
            )
          }}
        />
      </Paper>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onClose={() => setRenameDialogOpen(false)}>
        <DialogTitle>Rename Conversation</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <TextField
            autoFocus
            fullWidth
            label="Conversation Title"
            value={renameTitle}
            onChange={(e) => setRenameTitle(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenameDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRenameConfirm} variant="contained" disabled={!renameTitle.trim()}>
            Rename
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Conversation?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete this conversation? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIChat;
