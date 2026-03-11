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
  Button,
  TextField,
  InputAdornment,
  Checkbox,
  Menu,
  MenuItem,
  ListItemSecondaryAction,
  Collapse,
  Snackbar
} from '@mui/material';
import {
  Chat as ChatIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  AccessTime as AccessTimeIcon,
  CheckCircle as CheckCircleIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  Archive as ArchiveIcon,
  Unarchive as UnarchiveIcon,
  Edit as EditIcon,
  DeleteSweep as DeleteSweepIcon,
  Clear as ClearIcon,
  SelectAll as SelectAllIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
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
  const [archivedConversations, setArchivedConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Dialog states
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState(null);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [conversationToRename, setConversationToRename] = useState(null);
  const [newTitle, setNewTitle] = useState('');
  const [bulkDeleteDialogOpen, setBulkDeleteDialogOpen] = useState(false);
  const [clearAllDialogOpen, setClearAllDialogOpen] = useState(false);

  // UI states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectionMode, setSelectionMode] = useState(false);
  const [showArchived, setShowArchived] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [menuConversation, setMenuConversation] = useState(null);

  useEffect(() => {
    loadConversations();
  }, [user, selectedWorkspace]);

  const loadConversations = async () => {
    if (!user) return;

    setIsLoading(true);
    setError(null);

    try {
      // Build params - filter by workspace if selected
      const baseParams = {
        user_email: user.email,
        limit: 50
      };

      // Add workspace filter if a workspace is selected
      if (selectedWorkspace?.id) {
        baseParams.workspace_id = selectedWorkspace.id;
      }

      // Load active conversations
      const activeResponse = await pipelineApi.getConversations({
        ...baseParams,
        status: 'active'
      });

      // Load completed conversations (previous sessions)
      const completedResponse = await pipelineApi.getConversations({
        ...baseParams,
        status: 'completed'
      });

      // Combine active and completed conversations, sorted by updated_at
      const allConversations = [
        ...(activeResponse.data || []),
        ...(completedResponse.data || [])
      ].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

      setConversations(allConversations);

      // Load archived conversations
      const archivedResponse = await pipelineApi.getConversations({
        ...baseParams,
        status: 'archived'
      });
      setArchivedConversations(archivedResponse.data || []);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError('Failed to load chat sessions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    if (conversationId) {
      try {
        await pipelineApi.updateConversation(conversationId, null, 'completed');
      } catch (err) {
        console.error('Failed to update conversation status:', err);
      }
    }

    clearChat();
    setConversationId(null);
    localStorage.removeItem('conversationId');
    setSelectionMode(false);
    setSelectedIds([]);
  };

  const handleSelectConversation = async (conversation) => {
    if (selectionMode) {
      toggleSelection(conversation.conversation_id);
      return;
    }

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

  // Search functionality
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }

    setIsSearching(true);
    try {
      const response = await pipelineApi.searchConversations(searchQuery, user.email, 20);
      setSearchResults(response.data);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  // Selection functions
  const toggleSelection = (id) => {
    setSelectedIds(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : [...prev, id]
    );
  };

  const selectAll = () => {
    const allIds = conversations.map(c => c.conversation_id);
    setSelectedIds(allIds);
  };

  const clearSelection = () => {
    setSelectedIds([]);
    setSelectionMode(false);
  };

  // Delete functions
  const handleDeleteClick = (e, conversation) => {
    e.stopPropagation();
    setConversationToDelete(conversation);
    setDeleteDialogOpen(true);
    setMenuAnchor(null);
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
      setSuccessMessage('Conversation deleted successfully');
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError('Failed to delete conversation. Please try again.');
      setDeleteDialogOpen(false);
    }
  };

  // Bulk delete
  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;

    try {
      await pipelineApi.bulkDeleteConversations(selectedIds);

      if (selectedIds.includes(conversationId)) {
        handleNewChat();
      }

      loadConversations();
      setBulkDeleteDialogOpen(false);
      clearSelection();
      setSuccessMessage(`Deleted ${selectedIds.length} conversations`);
    } catch (err) {
      console.error('Bulk delete failed:', err);
      setError('Failed to delete conversations. Please try again.');
      setBulkDeleteDialogOpen(false);
    }
  };

  // Clear all
  const handleClearAll = async () => {
    try {
      await pipelineApi.deleteAllUserConversations(user.email);
      handleNewChat();
      loadConversations();
      setClearAllDialogOpen(false);
      setSuccessMessage('All conversations deleted');
    } catch (err) {
      console.error('Clear all failed:', err);
      setError('Failed to delete all conversations. Please try again.');
      setClearAllDialogOpen(false);
    }
  };

  // Archive/Restore
  const handleArchive = async (conversation) => {
    try {
      await pipelineApi.archiveConversation(conversation.conversation_id);
      loadConversations();
      setMenuAnchor(null);
      setSuccessMessage('Conversation archived');
    } catch (err) {
      console.error('Archive failed:', err);
      setError('Failed to archive conversation');
    }
  };

  const handleRestore = async (conversation) => {
    try {
      await pipelineApi.restoreConversation(conversation.conversation_id);
      loadConversations();
      setMenuAnchor(null);
      setSuccessMessage('Conversation restored');
    } catch (err) {
      console.error('Restore failed:', err);
      setError('Failed to restore conversation');
    }
  };

  // Rename
  const handleRenameClick = (conversation) => {
    setConversationToRename(conversation);
    setNewTitle(conversation.title || '');
    setRenameDialogOpen(true);
    setMenuAnchor(null);
  };

  const handleRenameConfirm = async () => {
    if (!conversationToRename || !newTitle.trim()) return;

    try {
      await pipelineApi.updateConversation(conversationToRename.conversation_id, newTitle.trim(), null);
      loadConversations();
      setRenameDialogOpen(false);
      setConversationToRename(null);
      setNewTitle('');
      setSuccessMessage('Conversation renamed');
    } catch (err) {
      console.error('Rename failed:', err);
      setError('Failed to rename conversation');
      setRenameDialogOpen(false);
    }
  };

  // Menu handlers
  const handleMenuOpen = (e, conversation) => {
    e.stopPropagation();
    setMenuAnchor(e.currentTarget);
    setMenuConversation(conversation);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setMenuConversation(null);
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

  const displayConversations = searchResults?.conversations || conversations;

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
          {conversations.length > 0 && (
            <Chip
              label={conversations.length}
              size="small"
              sx={{ bgcolor: 'rgba(255,255,255,0.3)', color: 'white', height: 20 }}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {selectionMode ? (
            <>
              <Tooltip title="Select All">
                <IconButton size="small" onClick={selectAll} sx={{ color: 'white' }}>
                  <SelectAllIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete Selected">
                <IconButton
                  size="small"
                  onClick={() => setBulkDeleteDialogOpen(true)}
                  disabled={selectedIds.length === 0}
                  sx={{ color: 'white' }}
                >
                  <DeleteSweepIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Cancel">
                <IconButton size="small" onClick={clearSelection} sx={{ color: 'white' }}>
                  <ClearIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          ) : (
            <>
              <Tooltip title="Select Multiple">
                <IconButton
                  size="small"
                  onClick={() => setSelectionMode(true)}
                  sx={{ color: 'white', opacity: 0.8 }}
                >
                  <Checkbox sx={{ color: 'white', p: 0 }} size="small" />
                </IconButton>
              </Tooltip>
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
            </>
          )}
        </Box>
      </Box>

      {/* Search Bar */}
      <Box sx={{ p: 1.5, bgcolor: 'grey.50' }}>
        <TextField
          size="small"
          fullWidth
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" color="action" />
              </InputAdornment>
            ),
            endAdornment: searchQuery && (
              <InputAdornment position="end">
                <IconButton size="small" onClick={clearSearch}>
                  <ClearIcon fontSize="small" />
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ bgcolor: 'white', borderRadius: 1 }}
        />
        {searchResults && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            Found {searchResults.count} results for "{searchResults.query}"
          </Typography>
        )}
      </Box>

      <Divider />

      {/* Error/Success Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ m: 1 }}>
          {error}
        </Alert>
      )}

      {/* Sessions List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 1 }}>
        {isLoading || isSearching ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={40} />
          </Box>
        ) : displayConversations.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {searchResults ? 'No conversations found.' : 'No chat sessions yet. Start a new conversation!'}
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {displayConversations.map((conversation) => (
              <ListItem
                key={conversation.conversation_id}
                disablePadding
                secondaryAction={
                  !selectionMode && (
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(e) => handleMenuOpen(e, conversation)}
                      sx={{ opacity: 0.6, '&:hover': { opacity: 1 } }}
                    >
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  )
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
                      '&:hover': { bgcolor: 'primary.light' }
                    }
                  }}
                >
                  {selectionMode && (
                    <Checkbox
                      checked={selectedIds.includes(conversation.conversation_id)}
                      onClick={(e) => e.stopPropagation()}
                      onChange={() => toggleSelection(conversation.conversation_id)}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                  )}
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
                        {conversation.match_type === 'message' && (
                          <Chip
                            label="Match"
                            size="small"
                            color="primary"
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

        {/* Archived Section */}
        {archivedConversations.length > 0 && !searchResults && (
          <>
            <Divider sx={{ my: 1 }} />
            <ListItemButton onClick={() => setShowArchived(!showArchived)}>
              <ListItemIcon sx={{ minWidth: 40 }}>
                <ArchiveIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography variant="body2" color="text.secondary">
                    Archived ({archivedConversations.length})
                  </Typography>
                }
              />
              {showArchived ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </ListItemButton>
            <Collapse in={showArchived}>
              <List sx={{ pl: 2 }}>
                {archivedConversations.map((conversation) => (
                  <ListItem
                    key={conversation.conversation_id}
                    disablePadding
                    secondaryAction={
                      <Tooltip title="Restore">
                        <IconButton
                          size="small"
                          onClick={() => handleRestore(conversation)}
                        >
                          <UnarchiveIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    }
                  >
                    <ListItemButton
                      onClick={() => handleSelectConversation(conversation)}
                      sx={{ borderRadius: 1, opacity: 0.7 }}
                    >
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <ChatIcon color="disabled" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body2" color="text.secondary">
                            {conversation.title || 'Archived Conversation'}
                          </Typography>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </>
        )}
      </Box>

      {/* Footer with Clear All */}
      {conversations.length > 0 && (
        <>
          <Divider />
          <Box sx={{ p: 1, display: 'flex', justifyContent: 'center' }}>
            <Button
              size="small"
              color="error"
              startIcon={<DeleteSweepIcon />}
              onClick={() => setClearAllDialogOpen(true)}
              sx={{ fontSize: '0.75rem' }}
            >
              Clear All Conversations
            </Button>
          </Box>
        </>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleRenameClick(menuConversation)}>
          <ListItemIcon><EditIcon fontSize="small" /></ListItemIcon>
          Rename
        </MenuItem>
        <MenuItem onClick={() => handleArchive(menuConversation)}>
          <ListItemIcon><ArchiveIcon fontSize="small" /></ListItemIcon>
          Archive
        </MenuItem>
        <Divider />
        <MenuItem onClick={(e) => handleDeleteClick(e, menuConversation)} sx={{ color: 'error.main' }}>
          <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon>
          Delete
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Chat Session?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this chat session? This will permanently remove the conversation and all associated pipeline configurations. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Delete Dialog */}
      <Dialog open={bulkDeleteDialogOpen} onClose={() => setBulkDeleteDialogOpen(false)}>
        <DialogTitle>Delete {selectedIds.length} Conversations?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete {selectedIds.length} selected conversations? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleBulkDelete} color="error" variant="contained">
            Delete All Selected
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clear All Dialog */}
      <Dialog open={clearAllDialogOpen} onClose={() => setClearAllDialogOpen(false)}>
        <DialogTitle>Delete All Conversations?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            This will permanently delete ALL your conversations and associated data. This action cannot be undone!
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearAllDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleClearAll} color="error" variant="contained">
            Delete Everything
          </Button>
        </DialogActions>
      </Dialog>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onClose={() => setRenameDialogOpen(false)}>
        <DialogTitle>Rename Conversation</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="New Title"
            fullWidth
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleRenameConfirm()}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenameDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleRenameConfirm} variant="contained" disabled={!newTitle.trim()}>
            Rename
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success Snackbar */}
      <Snackbar
        open={Boolean(successMessage)}
        autoHideDuration={3000}
        onClose={() => setSuccessMessage(null)}
        message={successMessage}
      />
    </Paper>
  );
};

export default ChatSessions;
