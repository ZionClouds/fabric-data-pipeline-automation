import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usePipeline } from '../contexts/PipelineContext';
import { pipelineApi } from '../services/api';
import {
  Box,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Chip,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Chat as ChatIcon,
  Assessment as AssessmentIcon,
  Folder as FolderIcon,
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Logout as LogoutIcon
} from '@mui/icons-material';
import WorkspaceSelector from './WorkspaceSelector';
import LakehouseWarehouseSelector from './LakehouseWarehouseSelector';
import AIChat from './AIChat';
import PipelinePreview from './PipelinePreview';
import PipelineList from './PipelineList';
import logo from '../assets/images/zionai.png';

const PipelineBuilderLayout = () => {
  const { user, logout } = useAuth();
  const { selectedWorkspace } = usePipeline();
  const [activeTab, setActiveTab] = useState('chat');
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoadingWorkspaces, setIsLoadingWorkspaces] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    loadWorkspaces();
  }, [user]);

  const loadWorkspaces = async () => {
    try {
      setIsLoadingWorkspaces(true);
      const response = await pipelineApi.getWorkspaces();
      console.log('Workspaces loaded:', response.data);
      setWorkspaces(response.data || []);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      // Set empty workspaces array and let user continue
      setWorkspaces([]);
    } finally {
      setIsLoadingWorkspaces(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#fafafa' }}>
      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: sidebarCollapsed ? 70 : 280,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: sidebarCollapsed ? 70 : 280,
            boxSizing: 'border-box',
            background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
            color: 'white',
            border: 'none',
            boxShadow: '2px 0 10px rgba(0, 0, 0, 0.1)',
            transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          },
        }}
      >
        {/* Sidebar Header */}
        <Box
          sx={{
            p: sidebarCollapsed ? '24px 8px 20px' : '24px 20px 20px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
            display: 'flex',
            justifyContent: sidebarCollapsed ? 'center' : 'space-between',
            alignItems: sidebarCollapsed ? 'center' : 'flex-start',
            minHeight: sidebarCollapsed ? '80px' : '100px',
            position: 'relative',
          }}
        >
          {!sidebarCollapsed && (
            <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'flex-start' }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.2)',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                  mr: 2,
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                }}
              >
                <img 
                  src={logo} 
                  alt="Pipeline Builder Logo" 
                  style={{ 
                    width: '20px', 
                    height: '20px',
                    filter: 'brightness(0) invert(1)',
                  }} 
                />
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <Typography
                  variant="h6"
                  sx={{
                    fontSize: '1.3rem',
                    fontWeight: 700,
                    margin: 0,
                    color: 'white',
                    lineHeight: 1.2,
                    letterSpacing: '-0.02em',
                    textShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                  }}
                >
                  Pipeline Builder
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.8rem',
                    opacity: 0.85,
                    mt: 0.8,
                    display: 'block',
                    color: 'rgba(255, 255, 255, 0.9)',
                    fontWeight: 400,
                    lineHeight: 1.3,
                    letterSpacing: '0.02em',
                  }}
                >
                  AI-Powered Data Pipelines
                </Typography>
              </Box>
            </Box>
          )}
          <IconButton
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            sx={{
              color: 'white',
              bgcolor: 'rgba(255, 255, 255, 0.1)',
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              backdropFilter: 'blur(10px)',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              alignSelf: sidebarCollapsed ? 'center' : 'flex-start',
              mt: sidebarCollapsed ? 0 : 0.5,
              '&:hover': {
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                transform: 'scale(1.05)',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
              },
              '&:active': {
                transform: 'scale(0.95)',
              },
            }}
            size="small"
          >
            {sidebarCollapsed ? <MenuIcon fontSize="small" /> : <ChevronLeftIcon fontSize="small" />}
          </IconButton>
        </Box>

        {/* Workspace Section */}
        {!sidebarCollapsed && (
          <Box
            sx={{
              p: '16px 20px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <WorkspaceSelector
              workspaces={workspaces}
              isLoading={isLoadingWorkspaces}
            />

            {/* Lakehouse and Warehouse Selectors */}
            <Box sx={{ mt: 2 }}>
              <LakehouseWarehouseSelector />
            </Box>
          </Box>
        )}

        {/* Navigation Menu */}
        <List sx={{ flex: 1, pt: 3 }}>
          <ListItem disablePadding>
            <ListItemButton
              onClick={() => setActiveTab('chat')}
              selected={activeTab === 'chat'}
              sx={{
                color: 'rgba(255, 255, 255, 0.8)',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                },
                '&.Mui-selected': {
                  bgcolor: 'rgba(255, 255, 255, 0.15)',
                  color: 'white',
                  borderLeft: '3px solid white',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.15)',
                  },
                },
                transition: 'all 0.2s',
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: sidebarCollapsed ? 0 : 40 }}>
                <ChatIcon />
              </ListItemIcon>
              {!sidebarCollapsed && (
                <ListItemText 
                  primary="AI Chat" 
                  primaryTypographyProps={{
                    fontSize: '14px',
                    fontWeight: 500,
                  }}
                />
              )}
            </ListItemButton>
          </ListItem>

          <ListItem disablePadding>
            <ListItemButton
              onClick={() => setActiveTab('preview')}
              selected={activeTab === 'preview'}
              sx={{
                color: 'rgba(255, 255, 255, 0.8)',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                },
                '&.Mui-selected': {
                  bgcolor: 'rgba(255, 255, 255, 0.15)',
                  color: 'white',
                  borderLeft: '3px solid white',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.15)',
                  },
                },
                transition: 'all 0.2s',
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: sidebarCollapsed ? 0 : 40 }}>
                <AssessmentIcon />
              </ListItemIcon>
              {!sidebarCollapsed && (
                <ListItemText 
                  primary="Pipeline Preview" 
                  primaryTypographyProps={{
                    fontSize: '14px',
                    fontWeight: 500,
                  }}
                />
              )}
            </ListItemButton>
          </ListItem>

          <ListItem disablePadding>
            <ListItemButton
              onClick={() => setActiveTab('pipelines')}
              selected={activeTab === 'pipelines'}
              sx={{
                color: 'rgba(255, 255, 255, 0.8)',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                  color: 'white',
                },
                '&.Mui-selected': {
                  bgcolor: 'rgba(255, 255, 255, 0.15)',
                  color: 'white',
                  borderLeft: '3px solid white',
                  '&:hover': {
                    bgcolor: 'rgba(255, 255, 255, 0.15)',
                  },
                },
                transition: 'all 0.2s',
              }}
            >
              <ListItemIcon sx={{ color: 'inherit', minWidth: sidebarCollapsed ? 0 : 40 }}>
                <FolderIcon />
              </ListItemIcon>
              {!sidebarCollapsed && (
                <ListItemText 
                  primary="My Pipelines" 
                  primaryTypographyProps={{
                    fontSize: '14px',
                    fontWeight: 500,
                  }}
                />
              )}
            </ListItemButton>
          </ListItem>
        </List>

        {/* Sidebar Footer */}
        <Box
          sx={{
            p: '16px 20px 24px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar
              sx={{
                width: 28,
                height: 28,
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                fontSize: '12px',
                flexShrink: 0,
                border: '1px solid rgba(255, 255, 255, 0.3)',
              }}
            >
              👤
            </Avatar>
            {!sidebarCollapsed && (
              <Box sx={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box sx={{ flex: 1, minWidth: 0, mr: 1 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontSize: '13px',
                      fontWeight: 500,
                      color: 'white',
                      mb: 0.25,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      lineHeight: 1.2,
                    }}
                  >
                    {user?.name || 'User'}
                  </Typography>
                  <Tooltip title={user?.email || 'No email'} placement="top">
                    <Typography
                      variant="caption"
                      sx={{
                        fontSize: '11px',
                        color: 'rgba(255, 255, 255, 0.7)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        display: 'block',
                        lineHeight: 1.2,
                        cursor: 'help',
                      }}
                    >
                      {user?.email || 'No email'}
                    </Typography>
                  </Tooltip>
                </Box>
                <Tooltip title="Logout" placement="top">
                  <IconButton
                    onClick={logout}
                    sx={{
                      color: 'rgba(255, 255, 255, 0.7)',
                      width: 32,
                      height: 32,
                      flexShrink: 0,
                      '&:hover': {
                        color: 'white',
                        bgcolor: 'rgba(255, 255, 255, 0.1)',
                      },
                    }}
                    size="small"
                  >
                    <LogoutIcon fontSize="medium" />
                  </IconButton>
                </Tooltip>
              </Box>
            )}
          </Box>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {selectedWorkspace ? (
          <>
            {/* Content Header */}
            <Paper
              elevation={0}
              sx={{
                p: '12px 24px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderRadius: 0,
                borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
                bgcolor: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(20px)',
                position: 'relative',
                overflow: 'hidden',
                minHeight: '60px',
                zIndex: 1000,
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '2px',
                  background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
                  zIndex: 1,
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '16px',
                    boxShadow: '0 2px 8px rgba(0, 123, 255, 0.25)',
                  }}
                >
                  {activeTab === 'chat' && '💬'}
                  {activeTab === 'preview' && '📊'}
                  {activeTab === 'pipelines' && '📁'}
                </Box>
                <Box>
                  <Typography
                    variant="h6"
                    component="h1"
                    sx={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      color: '#1f2937',
                      margin: 0,
                      letterSpacing: '-0.01em',
                      lineHeight: 1.2,
                      background: 'linear-gradient(135deg, #1f2937 0%, #4f46e5 100%)',
                      backgroundClip: 'text',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    {activeTab === 'chat' && 'AI Chat Assistant'}
                    {activeTab === 'preview' && 'Pipeline Preview'}
                    {activeTab === 'pipelines' && 'My Pipelines'}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      fontSize: '0.75rem',
                      color: '#6b7280',
                      fontWeight: 400,
                      mt: 0.25,
                      display: 'block',
                      lineHeight: 1.2,
                    }}
                  >
                    {activeTab === 'chat' && 'Build pipelines with natural language'}
                    {activeTab === 'preview' && 'Review and validate your pipeline'}
                    {activeTab === 'pipelines' && 'Manage your data pipeline projects'}
                  </Typography>
                </Box>
              </Box>
              <Chip
                label={`📍 ${selectedWorkspace.name}`}
                size="small"
                sx={{
                  background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '11px',
                  height: 28,
                  borderRadius: '14px',
                  boxShadow: '0 2px 8px rgba(0, 123, 255, 0.25)',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  '& .MuiChip-label': {
                    px: 1.5,
                  },
                  '&:hover': {
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 12px rgba(0, 123, 255, 0.35)',
                  },
                }}
              />
            </Paper>

            {/* Content Body */}
            <Box
              sx={{
                flex: 1,
                p: activeTab === 'chat' ? 0 : 4, // Remove padding for chat to maximize space
                overflow: 'hidden', // Changed from 'auto' to 'hidden' for chat
                bgcolor: '#fafafa',
              }}
            >
              {activeTab === 'chat' && <AIChat />}
              {activeTab === 'preview' && <PipelinePreview />}
              {activeTab === 'pipelines' && <PipelineList />}
            </Box>
          </>
        ) : (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              background: 'linear-gradient(135deg, hsl(170 25% 98%), hsl(175 30% 95%))',
              position: 'relative',
              '&::before': {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'radial-gradient(circle at 50% 50%, rgba(0, 123, 255, 0.05) 0%, transparent 70%)',
                pointerEvents: 'none',
              }
            }}
          >
            <Paper
              elevation={0}
              sx={{
                textAlign: 'center',
                maxWidth: 520,
                p: 3.5,
                bgcolor: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(20px)',
                borderRadius: 3,
                border: '1px solid rgba(255, 255, 255, 0.6)',
                boxShadow: '0 16px 48px rgba(0, 0, 0, 0.08)',
                position: 'relative',
                zIndex: 1,
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '56px',
                  height: '56px',
                  borderRadius: '14px',
                  background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
                  boxShadow: '0 6px 20px rgba(0, 123, 255, 0.25)',
                  mb: 2.5,
                  mx: 'auto',
                  transition: 'all 0.3s ease',
                  position: 'relative',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    inset: '-2px',
                    borderRadius: '16px',
                    background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
                    opacity: 0.2,
                    filter: 'blur(5px)',
                    transition: 'all 0.3s ease',
                  },
                  '&:hover': {
                    transform: 'translateY(-3px) scale(1.05)',
                    boxShadow: '0 12px 32px rgba(0, 123, 255, 0.35)',
                    '&::before': {
                      opacity: 0.4,
                      filter: 'blur(8px)',
                    }
                  }
                }}
              >
                <img 
                  src={logo} 
                  alt="Pipeline Builder Logo" 
                  style={{ 
                    width: '32px', 
                    height: '32px',
                    filter: 'brightness(0) invert(1)',
                    position: 'relative',
                    zIndex: 1,
                  }} 
                />
              </Box>
              <Typography
                variant="h5"
                component="h2"
                sx={{
                  fontSize: '1.6rem',
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  color: 'transparent',
                  WebkitTextFillColor: 'transparent',
                  mb: 1.5,
                  letterSpacing: '-0.02em',
                }}
              >
                Welcome to Pipeline Builder!
              </Typography>
              <Typography
                variant="body2"
                sx={{
                  fontSize: '0.95rem',
                  color: '#64748b',
                  mb: 3,
                  lineHeight: 1.5,
                  fontWeight: 400,
                  maxWidth: '420px',
                  mx: 'auto',
                }}
              >
                Select a workspace from the sidebar to start building intelligent data pipelines with AI assistance.
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {[
                  { icon: '💬', text: 'Chat with AI to build pipelines', desc: 'Natural language interface' },
                  { icon: '📊', text: 'Preview and validate pipelines', desc: 'Real-time visualization' },
                  { icon: '📁', text: 'Manage pipeline projects', desc: 'Organize your work' },
                ].map((feature, index) => (
                  <Paper
                    key={index}
                    elevation={0}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      p: 2,
                      bgcolor: 'rgba(255, 255, 255, 0.9)',
                      borderRadius: 1.5,
                      border: '1px solid rgba(255, 255, 255, 0.8)',
                      boxShadow: '0 3px 12px rgba(0, 0, 0, 0.04)',
                      transition: 'all 0.3s ease',
                      position: 'relative',
                      overflow: 'hidden',
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        bottom: 0,
                        width: '3px',
                        background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
                        transform: 'translateX(-3px)',
                        transition: 'transform 0.3s ease',
                      },
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: '0 8px 24px rgba(0, 123, 255, 0.12)',
                        bgcolor: 'rgba(255, 255, 255, 0.95)',
                        '&::before': {
                          transform: 'translateX(0)',
                        }
                      },
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '36px',
                        height: '36px',
                        borderRadius: '9px',
                        background: 'linear-gradient(135deg, rgba(0, 123, 255, 0.1), rgba(32, 201, 151, 0.1))',
                        fontSize: '16px',
                        flexShrink: 0,
                      }}
                    >
                      {feature.icon}
                    </Box>
                    <Box sx={{ textAlign: 'left', flex: 1 }}>
                      <Typography 
                        variant="subtitle2" 
                        sx={{ 
                          fontSize: '0.9rem',
                          fontWeight: 600,
                          color: '#1e293b',
                          mb: 0.2,
                          lineHeight: 1.2,
                        }}
                      >
                        {feature.text}
                      </Typography>
                      <Typography 
                        variant="caption" 
                        sx={{ 
                          fontSize: '0.75rem',
                          color: '#64748b',
                          fontWeight: 400,
                          lineHeight: 1.2,
                        }}
                      >
                        {feature.desc}
                      </Typography>
                    </Box>
                  </Paper>
                ))}
              </Box>
            </Paper>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default PipelineBuilderLayout;
