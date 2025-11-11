import React, { useState, useEffect } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import { useAuth } from '../contexts/AuthContext';
import { pipelineApi } from '../services/api';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  IconButton,
  Paper,
  Divider,
  Chip,
  Tooltip,
  CircularProgress,
  Alert,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Button
} from '@mui/material';
import {
  Chat as ChatIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  AccessTime as AccessTimeIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';

const ChatSessions = () => {
  const {
    conversationId,
    setConversationId,
    setChatMessages,
    addChatMessage,
    clearChat,
    selectedWorkspace
  } = usePipeline();
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState(null);

  useEffect(() => {
    loadConversations();
  }, [user]);

  const loadConversations = async () => {
    if (!user) return;

    setIsLoading(true);
    setError(null);

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
      setError('Failed to load chat sessions. Please try again.');
    } finally {
      setIsLoading(false);
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
  };

  const handleSelectConversation = async (conversation) => {
    if (conversation.conversation_id === conversationId) return;

    try {
      const response = await pipelineApi.getConversation(conversation.conversation_id);
      const data = response.data;

      clearChat();
      setConversationId(data.conversation_id);
      localStorage.setItem('conversationId', data.conversation_id);

      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(msg => {
          addChatMessage(msg.role, msg.content);
        });
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
      setError('Failed to load conversation. Please try again.');
    }
  };

  const handleDeleteClick = (e, conversation) => {
    e.stopPropagation();
    setConversationToDelete(conversation);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!conversationToDelete) return;

    try {
      await pipelineApi.deleteConversation(conversationToDelete.conversation_id);

      if (conversationToDelete.conversation_id === conversationId) {
        handleNewChat();
      }

      loadConversations();
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError('Failed to delete conversation. Please try again.');
      setDeleteDialogOpen(false);
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
    <Paper
      elevation={2}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ChatIcon />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Chat Sessions
          </Typography>
        </Box>
        <Tooltip title="New Chat">
          <IconButton
            onClick={handleNewChat}
            size="small"
            sx={{
              color: 'white',
              bgcolor: 'rgba(255,255,255,0.2)',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
            }}
          >
            <AddIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Divider />

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ m: 2 }}>
          {error}
        </Alert>
      )}

      {/* Sessions List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={40} />
          </Box>
        ) : conversations.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              No chat sessions yet. Start a new conversation!
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {conversations.map((conversation) => (
              <ListItem
                key={conversation.conversation_id}
                disablePadding
                secondaryAction={
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={(e) => handleDeleteClick(e, conversation)}
                    sx={{
                      opacity: 0.6,
                      '&:hover': { opacity: 1, color: 'error.main' }
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                }
              >
                <ListItemButton
                  selected={conversation.conversation_id === conversationId}
                  onClick={() => handleSelectConversation(conversation)}
                  sx={{
                    borderRadius: 1,
                    mb: 0.5,
                    '&.Mui-selected': {
                      bgcolor: 'primary.light',
                      '&:hover': {
                        bgcolor: 'primary.light'
                      }
                    }
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>
                    {conversation.conversation_id === conversationId ? (
                      <CheckCircleIcon color="primary" fontSize="small" />
                    ) : (
                      <ChatIcon color="action" fontSize="small" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: conversation.conversation_id === conversationId ? 600 : 400,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {conversation.title || 'New Conversation'}
                      </Typography>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <AccessTimeIcon sx={{ fontSize: 12 }} />
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(conversation.updated_at)}
                        </Typography>
                        {conversation.message_count > 0 && (
                          <Chip
                            label={`${conversation.message_count} msg`}
                            size="small"
                            sx={{ height: 18, fontSize: '0.7rem' }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Chat Session?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this chat session? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ChatSessions;
