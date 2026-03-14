import React, { useState, useEffect } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import { useAuth } from '../contexts/AuthContext';
import { pipelineApi } from '../services/api';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  IconButton,
  Divider,
  Tooltip,
  CircularProgress,
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
  Collapse,
  Snackbar,
  Chip,
  Alert
} from '@mui/material';
import {
  Chat as ChatIcon,
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

// Dark sidebar color tokens
const colors = {
  bg: '#1B1B1F',
  surfaceHover: 'rgba(255,255,255,0.05)',
  surfaceActive: 'rgba(0,120,212,0.15)',
  border: 'rgba(255,255,255,0.08)',
  textPrimary: '#E8E6E3',
  textSecondary: '#A19F9D',
  textMuted: '#8A8886',
  accent: '#0078D4',
  inputBg: '#2D2D30',
  inputBorder: '#3E3E42',
};

const ChatSessions = () => {
  const {
    conversationId,
    setConversationId,
    setChatMessages,
    addChatMessage,
    clearChat,
    selectedWorkspace,
    refreshConversations
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
  }, [user, selectedWorkspace, refreshConversations]);

  const loadConversations = async () => {
    if (!user) return;
    setIsLoading(true);
    setError(null);
    try {
      const baseParams = { user_email: user.email, limit: 50 };
      if (selectedWorkspace?.id) baseParams.workspace_id = selectedWorkspace.id;

      const activeResponse = await pipelineApi.getConversations({ ...baseParams, status: 'active' });
      const completedResponse = await pipelineApi.getConversations({ ...baseParams, status: 'completed' });
      const allConversations = [
        ...(activeResponse.data || []),
        ...(completedResponse.data || [])
      ].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
      setConversations(allConversations);

      const archivedResponse = await pipelineApi.getConversations({ ...baseParams, status: 'archived' });
      setArchivedConversations(archivedResponse.data || []);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError('Failed to load chats');
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
        data.messages.forEach(msg => addChatMessage(msg.role, msg.content));
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
      setError('Failed to load conversation');
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    setIsSearching(true);
    try {
      const response = await pipelineApi.searchConversations(searchQuery, user.email, 20);
      setSearchResults(response.data);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => { setSearchQuery(''); setSearchResults(null); };
  const toggleSelection = (id) => setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  const selectAll = () => setSelectedIds(conversations.map(c => c.conversation_id));
  const clearSelection = () => { setSelectedIds([]); setSelectionMode(false); };

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
      if (conversationToDelete.conversation_id === conversationId) handleNewChat();
      loadConversations();
      setDeleteDialogOpen(false);
      setConversationToDelete(null);
      setSuccessMessage('Deleted');
    } catch (err) {
      setError('Failed to delete');
      setDeleteDialogOpen(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    try {
      await pipelineApi.bulkDeleteConversations(selectedIds);
      if (selectedIds.includes(conversationId)) handleNewChat();
      loadConversations();
      setBulkDeleteDialogOpen(false);
      clearSelection();
      setSuccessMessage(`Deleted ${selectedIds.length} chats`);
    } catch (err) {
      setError('Failed to delete');
      setBulkDeleteDialogOpen(false);
    }
  };

  const handleClearAll = async () => {
    try {
      await pipelineApi.deleteAllUserConversations(user.email);
      handleNewChat();
      loadConversations();
      setClearAllDialogOpen(false);
      setSuccessMessage('All chats deleted');
    } catch (err) {
      setError('Failed to delete all');
      setClearAllDialogOpen(false);
    }
  };

  const handleArchive = async (conversation) => {
    try {
      await pipelineApi.archiveConversation(conversation.conversation_id);
      loadConversations();
      setMenuAnchor(null);
      setSuccessMessage('Archived');
    } catch (err) { setError('Failed to archive'); }
  };

  const handleRestore = async (conversation) => {
    try {
      await pipelineApi.restoreConversation(conversation.conversation_id);
      loadConversations();
      setMenuAnchor(null);
      setSuccessMessage('Restored');
    } catch (err) { setError('Failed to restore'); }
  };

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
      setSuccessMessage('Renamed');
    } catch (err) {
      setError('Failed to rename');
      setRenameDialogOpen(false);
    }
  };

  const handleMenuOpen = (e, conversation) => { e.stopPropagation(); setMenuAnchor(e.currentTarget); setMenuConversation(conversation); };
  const handleMenuClose = () => { setMenuAnchor(null); setMenuConversation(null); };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMin = Math.floor(diffMs / 60000);
    const diffHr = Math.floor(diffMs / 3600000);
    const diffDay = Math.floor(diffMs / 86400000);
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    if (diffDay === 1) return 'Yesterday';
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const displayConversations = searchResults?.conversations || conversations;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Search Bar */}
      <Box sx={{ px: 2, py: 1 }}>
        <TextField
          size="small"
          fullWidth
          placeholder="Search chats..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon sx={{ fontSize: 16, color: colors.textMuted }} />
              </InputAdornment>
            ),
            endAdornment: searchQuery && (
              <InputAdornment position="end">
                <IconButton size="small" onClick={clearSearch} sx={{ color: colors.textMuted }}>
                  <ClearIcon sx={{ fontSize: 14 }} />
                </IconButton>
              </InputAdornment>
            ),
            sx: {
              bgcolor: colors.inputBg,
              borderRadius: '6px',
              color: colors.textPrimary,
              fontSize: '12px',
              '& fieldset': { borderColor: colors.inputBorder },
              '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.2) !important' },
              '&.Mui-focused fieldset': { borderColor: `${colors.accent} !important` },
              '& input::placeholder': { color: colors.textMuted, opacity: 1 },
            },
          }}
        />
        {searchResults && (
          <Typography sx={{ mt: 0.5, fontSize: '11px', color: colors.textMuted }}>
            {searchResults.count} results
          </Typography>
        )}
      </Box>

      {/* Selection Mode Bar */}
      {selectionMode && (
        <Box sx={{ px: 2, py: 0.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Tooltip title="Select All">
            <IconButton size="small" onClick={selectAll} sx={{ color: colors.textSecondary }}>
              <SelectAllIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete Selected">
            <IconButton
              size="small"
              onClick={() => setBulkDeleteDialogOpen(true)}
              disabled={selectedIds.length === 0}
              sx={{ color: '#D13438' }}
            >
              <DeleteSweepIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Cancel">
            <IconButton size="small" onClick={clearSelection} sx={{ color: colors.textSecondary }}>
              <ClearIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
          <Typography sx={{ ml: 'auto', fontSize: '11px', color: colors.textMuted }}>
            {selectedIds.length} selected
          </Typography>
        </Box>
      )}

      {/* Sessions List */}
      <Box sx={{ flex: 1, overflow: 'auto', px: 1, py: 0.5,
        '&::-webkit-scrollbar': { width: '4px' },
        '&::-webkit-scrollbar-track': { background: 'transparent' },
        '&::-webkit-scrollbar-thumb': { background: 'rgba(255,255,255,0.15)', borderRadius: '2px' },
      }}>
        {isLoading || isSearching ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={24} sx={{ color: colors.accent }} />
          </Box>
        ) : displayConversations.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography sx={{ fontSize: '12px', color: colors.textMuted }}>
              {searchResults ? 'No results found' : 'No chats yet'}
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {displayConversations.map((conversation, index) => (
              <motion.div
                key={conversation.conversation_id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03, duration: 0.2 }}
              >
                <ListItem disablePadding sx={{ mb: 0.25 }}>
                  <ListItemButton
                    selected={conversation.conversation_id === conversationId}
                    onClick={() => handleSelectConversation(conversation)}
                    sx={{
                      borderRadius: '6px',
                      py: 1,
                      px: 1.5,
                      color: colors.textPrimary,
                      '&:hover': { bgcolor: colors.surfaceHover },
                      '&.Mui-selected': {
                        bgcolor: colors.surfaceActive,
                        borderLeft: `2px solid ${colors.accent}`,
                        '&:hover': { bgcolor: colors.surfaceActive },
                      },
                    }}
                  >
                    {selectionMode && (
                      <Checkbox
                        checked={selectedIds.includes(conversation.conversation_id)}
                        onClick={(e) => e.stopPropagation()}
                        onChange={() => toggleSelection(conversation.conversation_id)}
                        size="small"
                        sx={{ mr: 0.5, p: 0.25, color: colors.textMuted, '&.Mui-checked': { color: colors.accent } }}
                      />
                    )}
                    <ListItemText
                      primary={
                        <Typography
                          sx={{
                            fontSize: '13px',
                            fontWeight: conversation.conversation_id === conversationId ? 600 : 400,
                            color: colors.textPrimary,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            lineHeight: 1.3,
                          }}
                        >
                          {conversation.title || 'New Conversation'}
                        </Typography>
                      }
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.25 }}>
                          <Typography sx={{ fontSize: '11px', color: colors.textMuted }}>
                            {formatDate(conversation.updated_at)}
                          </Typography>
                          {conversation.message_count > 0 && (
                            <Typography sx={{ fontSize: '11px', color: colors.textMuted }}>
                              · {conversation.message_count} msg
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    {!selectionMode && (
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, conversation)}
                        sx={{
                          color: colors.textMuted,
                          opacity: 0,
                          '.MuiListItemButton-root:hover &': { opacity: 1 },
                          ml: 0.5,
                          p: 0.25,
                        }}
                      >
                        <MoreVertIcon sx={{ fontSize: 16 }} />
                      </IconButton>
                    )}
                  </ListItemButton>
                </ListItem>
              </motion.div>
            ))}
          </List>
        )}

        {/* Archived Section */}
        {archivedConversations.length > 0 && !searchResults && (
          <>
            <Divider sx={{ my: 1, borderColor: colors.border }} />
            <ListItemButton
              onClick={() => setShowArchived(!showArchived)}
              sx={{ borderRadius: '6px', py: 0.75, color: colors.textMuted }}
            >
              <ListItemIcon sx={{ minWidth: 28 }}>
                <ArchiveIcon sx={{ fontSize: 14, color: colors.textMuted }} />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography sx={{ fontSize: '12px', color: colors.textMuted }}>
                    Archived ({archivedConversations.length})
                  </Typography>
                }
              />
              {showArchived ? <ExpandLessIcon sx={{ fontSize: 16 }} /> : <ExpandMoreIcon sx={{ fontSize: 16 }} />}
            </ListItemButton>
            <Collapse in={showArchived}>
              <List sx={{ pl: 1 }}>
                {archivedConversations.map((conversation) => (
                  <ListItem key={conversation.conversation_id} disablePadding>
                    <ListItemButton
                      onClick={() => handleSelectConversation(conversation)}
                      sx={{
                        borderRadius: '6px',
                        py: 0.75,
                        px: 1.5,
                        opacity: 0.6,
                        '&:hover': { bgcolor: colors.surfaceHover, opacity: 0.8 },
                      }}
                    >
                      <ListItemText
                        primary={
                          <Typography sx={{ fontSize: '12px', color: colors.textSecondary }}>
                            {conversation.title || 'Archived'}
                          </Typography>
                        }
                      />
                      <Tooltip title="Restore">
                        <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleRestore(conversation); }} sx={{ color: colors.textMuted, p: 0.25 }}>
                          <UnarchiveIcon sx={{ fontSize: 14 }} />
                        </IconButton>
                      </Tooltip>
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </Collapse>
          </>
        )}
      </Box>

      {/* Footer Actions */}
      {conversations.length > 3 && !selectionMode && (
        <Box sx={{ px: 2, py: 1, borderTop: `1px solid ${colors.border}`, display: 'flex', gap: 0.5 }}>
          <Button
            size="small"
            onClick={() => setSelectionMode(true)}
            sx={{ color: colors.textMuted, fontSize: '11px', textTransform: 'none', minWidth: 0, px: 1 }}
          >
            Select
          </Button>
          <Button
            size="small"
            onClick={() => setClearAllDialogOpen(true)}
            sx={{ color: '#D13438', fontSize: '11px', textTransform: 'none', minWidth: 0, px: 1, ml: 'auto' }}
          >
            Clear all
          </Button>
        </Box>
      )}

      {/* Context Menu */}
      <Menu anchorEl={menuAnchor} open={Boolean(menuAnchor)} onClose={handleMenuClose}
        PaperProps={{ sx: { bgcolor: '#2D2D30', color: colors.textPrimary, minWidth: 150, boxShadow: '0 4px 16px rgba(0,0,0,0.4)' } }}
      >
        <MenuItem onClick={() => handleRenameClick(menuConversation)} sx={{ fontSize: '13px', '&:hover': { bgcolor: colors.surfaceHover } }}>
          <ListItemIcon><EditIcon sx={{ fontSize: 16, color: colors.textSecondary }} /></ListItemIcon>
          Rename
        </MenuItem>
        <MenuItem onClick={() => handleArchive(menuConversation)} sx={{ fontSize: '13px', '&:hover': { bgcolor: colors.surfaceHover } }}>
          <ListItemIcon><ArchiveIcon sx={{ fontSize: 16, color: colors.textSecondary }} /></ListItemIcon>
          Archive
        </MenuItem>
        <Divider sx={{ borderColor: colors.border }} />
        <MenuItem onClick={(e) => handleDeleteClick(e, menuConversation)} sx={{ fontSize: '13px', color: '#D13438', '&:hover': { bgcolor: 'rgba(209,52,56,0.1)' } }}>
          <ListItemIcon><DeleteIcon sx={{ fontSize: 16, color: '#D13438' }} /></ListItemIcon>
          Delete
        </MenuItem>
      </Menu>

      {/* Dialogs (keep light theme for modals) */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Chat?</DialogTitle>
        <DialogContent>
          <DialogContentText>This will permanently remove this conversation and all associated data.</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">Delete</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={bulkDeleteDialogOpen} onClose={() => setBulkDeleteDialogOpen(false)}>
        <DialogTitle>Delete {selectedIds.length} Chats?</DialogTitle>
        <DialogContent>
          <DialogContentText>This action cannot be undone.</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBulkDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleBulkDelete} color="error" variant="contained">Delete All</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={clearAllDialogOpen} onClose={() => setClearAllDialogOpen(false)}>
        <DialogTitle>Delete All Conversations?</DialogTitle>
        <DialogContent>
          <DialogContentText>This will permanently delete ALL your conversations.</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearAllDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleClearAll} color="error" variant="contained">Delete Everything</Button>
        </DialogActions>
      </Dialog>

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
          <Button onClick={handleRenameConfirm} variant="contained" disabled={!newTitle.trim()}>Rename</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={Boolean(successMessage)}
        autoHideDuration={2000}
        onClose={() => setSuccessMessage(null)}
        message={successMessage}
      />
      <Snackbar
        open={Boolean(error)}
        autoHideDuration={3000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)} sx={{ fontSize: '12px' }}>{error}</Alert>
      </Snackbar>
    </Box>
  );
};

export default ChatSessions;
