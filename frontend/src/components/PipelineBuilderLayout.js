import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usePipeline } from '../contexts/PipelineContext';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  Typography,
  IconButton,
  Avatar,
  Tooltip,
  Snackbar,
  Alert,
  Backdrop,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Logout as LogoutIcon,
  Close as CloseIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import PermanentHeader from './PermanentHeader';
import AIChat from './AIChat';
import PipelinePreview from './PipelinePreview';
import PipelineList from './PipelineList';
import ChatSessions from './ChatSessions';
import logo from '../assets/images/zionai.png';

const SIDEBAR_WIDTH = 280;

const PipelineBuilderLayout = () => {
  const { user, logout } = useAuth();
  const {
    selectedWorkspace,
    selectedJobForPreview,
    activeTab,
    handleTabClick,
    clearChat,
    setConversationId,
  } = usePipeline();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showWorkspaceAlert, setShowWorkspaceAlert] = useState(false);
  const [showPreviewPanel, setShowPreviewPanel] = useState(false);

  // Auto-open preview panel when a job is selected
  useEffect(() => {
    if (selectedJobForPreview) {
      setShowPreviewPanel(true);
    }
  }, [selectedJobForPreview]);

  const handleTabClickWithValidation = (tab) => {
    if (!selectedWorkspace) {
      setShowWorkspaceAlert(true);
      return;
    }
    handleTabClick(tab);
  };

  const handleNewChat = () => {
    clearChat();
    setConversationId(null);
    localStorage.removeItem('conversationId');
    handleTabClick('chat');
  };

  const handleCloseAlert = (event, reason) => {
    if (reason === 'clickaway') return;
    setShowWorkspaceAlert(false);
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#F3F2F1' }}>
      {/* ========== Dark Sidebar ========== */}
      <motion.div
        animate={{ width: sidebarCollapsed ? 0 : SIDEBAR_WIDTH }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        style={{
          overflow: 'hidden',
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
          background: '#1B1B1F',
          height: '100vh',
        }}
      >
        <Box
          sx={{
            width: SIDEBAR_WIDTH,
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Sidebar Header */}
          <Box
            sx={{
              p: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Box
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: '8px',
                  background: '#0078D4',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 2px 8px rgba(0,120,212,0.3)',
                }}
              >
                <img
                  src={logo}
                  alt="Logo"
                  style={{ width: 18, height: 18, filter: 'brightness(0) invert(1)' }}
                />
              </Box>
              <Typography
                sx={{
                  color: '#E8E6E3',
                  fontSize: '14px',
                  fontWeight: 600,
                  letterSpacing: '-0.01em',
                }}
              >
                Pipeline Builder
              </Typography>
            </Box>
            <Tooltip title="Collapse sidebar">
              <IconButton
                onClick={() => setSidebarCollapsed(true)}
                size="small"
                sx={{
                  color: '#A19F9D',
                  '&:hover': { color: '#E8E6E3', bgcolor: 'rgba(255,255,255,0.06)' },
                }}
              >
                <ChevronLeftIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>

          {/* New Chat Button */}
          <Box sx={{ p: '12px 16px 8px' }}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={handleNewChat}
              sx={{
                color: '#E8E6E3',
                borderColor: 'rgba(255,255,255,0.15)',
                borderRadius: '8px',
                py: 1,
                fontSize: '13px',
                fontWeight: 500,
                justifyContent: 'flex-start',
                '&:hover': {
                  borderColor: 'rgba(255,255,255,0.3)',
                  bgcolor: 'rgba(255,255,255,0.06)',
                },
              }}
            >
              New Chat
            </Button>
          </Box>

          {/* Chat Sessions List */}
          <Box sx={{ flex: 1, overflow: 'hidden', minHeight: 0 }}>
            <ChatSessions />
          </Box>

          {/* Sidebar Footer — User Profile */}
          <Box
            sx={{
              p: '12px 16px',
              borderTop: '1px solid rgba(255,255,255,0.08)',
              display: 'flex',
              alignItems: 'center',
              gap: 1.5,
            }}
          >
            <Avatar
              sx={{
                width: 28,
                height: 28,
                bgcolor: '#0078D4',
                fontSize: '12px',
                fontWeight: 600,
              }}
            >
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </Avatar>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography
                sx={{
                  color: '#E8E6E3',
                  fontSize: '13px',
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  lineHeight: 1.3,
                }}
              >
                {user?.name || 'User'}
              </Typography>
              <Tooltip title={user?.email || ''} placement="top">
                <Typography
                  sx={{
                    color: '#A19F9D',
                    fontSize: '11px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    lineHeight: 1.3,
                    cursor: 'help',
                  }}
                >
                  {user?.email || ''}
                </Typography>
              </Tooltip>
            </Box>
            <Tooltip title="Logout">
              <IconButton
                onClick={logout}
                size="small"
                sx={{
                  color: '#A19F9D',
                  '&:hover': { color: '#E8E6E3', bgcolor: 'rgba(255,255,255,0.06)' },
                }}
              >
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </motion.div>

      {/* ========== Main Content ========== */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Header with expand button when sidebar collapsed */}
        <Box sx={{ display: 'flex', alignItems: 'stretch' }}>
          {sidebarCollapsed && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                px: 1,
                bgcolor: 'rgba(255,255,255,0.95)',
                borderBottom: '1px solid #EDEBE9',
              }}
            >
              <Tooltip title="Expand sidebar">
                <IconButton
                  onClick={() => setSidebarCollapsed(false)}
                  size="small"
                  sx={{ color: '#605E5C' }}
                >
                  <MenuIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}
          <Box sx={{ flex: 1 }}>
            <PermanentHeader
              activeTab={activeTab}
              onTabChange={handleTabClickWithValidation}
              onPreviewOpen={() => setShowPreviewPanel(true)}
            />
          </Box>
        </Box>

        {/* Content Area with Transitions */}
        {selectedWorkspace ? (
          <Box sx={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2, ease: 'easeInOut' }}
                style={{ height: '100%' }}
              >
                {activeTab === 'chat' && <AIChat />}
                {activeTab === 'pipelines' && <PipelineList />}
                {activeTab === 'preview' && <PipelinePreview />}
              </motion.div>
            </AnimatePresence>

            {/* Pipeline Preview Slide-Over Panel */}
            <AnimatePresence>
              {showPreviewPanel && activeTab !== 'preview' && (
                <>
                  <Backdrop
                    open
                    onClick={() => setShowPreviewPanel(false)}
                    sx={{ position: 'absolute', zIndex: 1100, bgcolor: 'rgba(0,0,0,0.3)' }}
                  />
                  <motion.div
                    initial={{ x: '100%' }}
                    animate={{ x: 0 }}
                    exit={{ x: '100%' }}
                    transition={{ type: 'spring', damping: 28, stiffness: 220 }}
                    style={{
                      position: 'absolute',
                      right: 0,
                      top: 0,
                      bottom: 0,
                      width: '55%',
                      minWidth: 500,
                      maxWidth: 800,
                      zIndex: 1200,
                      background: '#FFFFFF',
                      boxShadow: '-4px 0 24px rgba(0,0,0,0.12)',
                      display: 'flex',
                      flexDirection: 'column',
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        p: '12px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        borderBottom: '1px solid #EDEBE9',
                        bgcolor: '#FAFAF9',
                      }}
                    >
                      <Typography sx={{ fontWeight: 600, fontSize: '14px', color: '#323130' }}>
                        Pipeline Preview
                      </Typography>
                      <IconButton
                        onClick={() => setShowPreviewPanel(false)}
                        size="small"
                        sx={{ color: '#605E5C' }}
                      >
                        <CloseIcon fontSize="small" />
                      </IconButton>
                    </Box>
                    <Box sx={{ flex: 1, overflow: 'auto' }}>
                      <PipelinePreview />
                    </Box>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </Box>
        ) : (
          /* Welcome Screen — No Workspace Selected */
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#FAFAF9',
            }}
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Box sx={{ textAlign: 'center', maxWidth: 420, p: 4 }}>
                <Box
                  sx={{
                    width: 56,
                    height: 56,
                    borderRadius: '14px',
                    background: '#0078D4',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 3,
                    boxShadow: '0 4px 16px rgba(0,120,212,0.25)',
                  }}
                >
                  <img
                    src={logo}
                    alt="Logo"
                    style={{ width: 28, height: 28, filter: 'brightness(0) invert(1)' }}
                  />
                </Box>
                <Typography
                  variant="h5"
                  sx={{ fontWeight: 700, color: '#323130', mb: 1.5, letterSpacing: '-0.02em' }}
                >
                  Welcome to Pipeline Builder
                </Typography>
                <Typography
                  variant="body2"
                  sx={{ color: '#605E5C', mb: 4, lineHeight: 1.6, fontSize: '14px' }}
                >
                  Select a workspace from the header to start building intelligent data pipelines with AI.
                </Typography>
                {[
                  { icon: '💬', label: 'Chat with AI to design pipelines' },
                  { icon: '📊', label: 'Preview and validate before deploy' },
                  { icon: '📁', label: 'Manage all your pipeline projects' },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + i * 0.1 }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.5,
                        p: 1.5,
                        mb: 1,
                        bgcolor: '#FFFFFF',
                        borderRadius: '8px',
                        border: '1px solid #EDEBE9',
                        transition: 'all 0.2s',
                        '&:hover': {
                          borderColor: '#0078D4',
                          boxShadow: '0 2px 8px rgba(0,120,212,0.1)',
                        },
                      }}
                    >
                      <Box sx={{ fontSize: '16px', width: 28, textAlign: 'center' }}>{item.icon}</Box>
                      <Typography sx={{ fontSize: '13px', fontWeight: 500, color: '#323130' }}>
                        {item.label}
                      </Typography>
                    </Box>
                  </motion.div>
                ))}
              </Box>
            </motion.div>
          </Box>
        )}
      </Box>

      {/* Workspace Selection Alert */}
      <Snackbar
        open={showWorkspaceAlert}
        autoHideDuration={1500}
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        sx={{ mt: 8 }}
      >
        <Alert
          onClose={handleCloseAlert}
          severity="warning"
          variant="filled"
          sx={{ fontSize: '13px', fontWeight: 600 }}
        >
          Please select a workspace first
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default PipelineBuilderLayout;
