import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usePipeline } from '../contexts/PipelineContext';
import { pipelineApi } from '../services/api';
import axios from 'axios';
import {
  Box,
  Typography,
  Paper,
  Menu,
  Button,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  KeyboardArrowDown as ArrowDownIcon,
  Business as BusinessIcon,
  Folder as FolderIcon,
  Assessment as AssessmentIcon,
  Chat as ChatIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import WorkspaceSelector from './WorkspaceSelector';
import LakehouseWarehouseSelector from './LakehouseWarehouseSelector';

const API_BASE_URL = window._env_?.REACT_APP_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8080';

const PermanentHeader = ({ activeTab, onTabChange, onPreviewOpen }) => {
  const { user } = useAuth();
  const { selectedWorkspace, selectedLakehouse, selectedWarehouse, setSelectedWorkspace, setSelectedLakehouse, setSelectedWarehouse } = usePipeline();
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoadingWorkspaces, setIsLoadingWorkspaces] = useState(true);
  const [workspaceMenuAnchor, setWorkspaceMenuAnchor] = useState(null);

  const isWorkspaceMenuOpen = Boolean(workspaceMenuAnchor);

  useEffect(() => {
    loadWorkspaces();
  }, [user]);

  // Auto-select lakehouse and warehouse when workspace changes
  // This runs outside the Menu so it triggers immediately on workspace selection
  // Uses retry logic since the first Fabric API call may fail due to token timing
  useEffect(() => {
    if (!selectedWorkspace?.id) return;
    // Only auto-load if not already selected
    if (selectedLakehouse && selectedWarehouse) return;

    let cancelled = false;

    const autoSelectLakehouseWarehouse = async (attempt = 1) => {
      try {
        const token = sessionStorage.getItem('authToken');
        const config = { headers: { Authorization: `Bearer ${token}` } };

        const [lhRes, whRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/api/workspaces/${selectedWorkspace.id}/lakehouses`, config),
          axios.get(`${API_BASE_URL}/api/workspaces/${selectedWorkspace.id}/warehouses`, config),
        ]);

        if (cancelled) return;

        const lakehouses = lhRes.data || [];
        const warehouses = whRes.data || [];

        if (lakehouses.length >= 1 && !selectedLakehouse) {
          setSelectedLakehouse(lakehouses[0]);
        }
        if (warehouses.length >= 1 && !selectedWarehouse) {
          setSelectedWarehouse(warehouses[0]);
        }

        // Retry if we got 0 results (Fabric API token may not be ready yet)
        if ((lakehouses.length === 0 || warehouses.length === 0) && attempt < 3) {
          setTimeout(() => {
            if (!cancelled) autoSelectLakehouseWarehouse(attempt + 1);
          }, 2000 * attempt);
        }
      } catch (err) {
        console.error(`Auto-select lakehouse/warehouse failed (attempt ${attempt}):`, err);
        // Retry on error
        if (attempt < 3 && !cancelled) {
          setTimeout(() => {
            if (!cancelled) autoSelectLakehouseWarehouse(attempt + 1);
          }, 2000 * attempt);
        }
      }
    };

    autoSelectLakehouseWarehouse();
    return () => { cancelled = true; };
  }, [selectedWorkspace?.id]);

  const loadWorkspaces = async () => {
    try {
      setIsLoadingWorkspaces(true);
      const response = await pipelineApi.getWorkspaces();
      setWorkspaces(response.data || []);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      setWorkspaces([]);
    } finally {
      setIsLoadingWorkspaces(false);
    }
  };

  const handleWorkspaceMenuClick = (event) => {
    setWorkspaceMenuAnchor(event.currentTarget);
  };

  const handleCloseMenus = () => {
    setWorkspaceMenuAnchor(null);
  };

  const navItems = [
    { key: 'chat', label: 'AI Chat', icon: <ChatIcon sx={{ fontSize: 16 }} /> },
    { key: 'pipelines', label: 'Pipelines', icon: <FolderIcon sx={{ fontSize: 16 }} /> },
    { key: 'preview', label: 'Preview', icon: <AssessmentIcon sx={{ fontSize: 16 }} /> },
  ];

  return (
    <Paper
      elevation={0}
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 1100,
        borderRadius: 0,
        borderBottom: '1px solid #EDEBE9',
        bgcolor: '#FFFFFF',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: '#0078D4',
        },
      }}
    >
      <Box sx={{ px: 3, py: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Left — Workspace Selector */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            onClick={handleWorkspaceMenuClick}
            variant="outlined"
            sx={{
              minWidth: '200px',
              height: '34px',
              borderRadius: '6px',
              border: '1px solid #EDEBE9',
              bgcolor: '#FAFAF9',
              color: selectedWorkspace ? '#323130' : '#A19F9D',
              textTransform: 'none',
              justifyContent: 'space-between',
              px: 1.5,
              fontSize: '13px',
              fontWeight: 500,
              '&:hover': {
                bgcolor: '#F3F2F1',
                borderColor: '#0078D4',
              },
            }}
            endIcon={isLoadingWorkspaces ? <CircularProgress size={14} /> : <ArrowDownIcon sx={{ fontSize: 16 }} />}
            disabled={isLoadingWorkspaces}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8, overflow: 'hidden' }}>
              <BusinessIcon sx={{ fontSize: 14, color: '#A19F9D' }} />
              <Typography
                sx={{
                  fontSize: '13px',
                  fontWeight: 500,
                  color: 'inherit',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  maxWidth: '140px',
                }}
              >
                {selectedWorkspace ? selectedWorkspace.name : 'Select Workspace'}
              </Typography>
            </Box>
          </Button>

          {selectedWorkspace && (
            <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
          )}

          {/* Navigation Tabs */}
          {selectedWorkspace && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {navItems.map((item) => (
                <Button
                  key={item.key}
                  size="small"
                  startIcon={item.icon}
                  onClick={() => onTabChange?.(item.key)}
                  sx={{
                    fontSize: '12px',
                    fontWeight: activeTab === item.key ? 600 : 400,
                    color: activeTab === item.key ? '#0078D4' : '#605E5C',
                    bgcolor: activeTab === item.key ? 'rgba(0,120,212,0.08)' : 'transparent',
                    borderRadius: '6px',
                    px: 1.5,
                    py: 0.5,
                    minWidth: 0,
                    textTransform: 'none',
                    transition: 'all 0.15s',
                    '&:hover': {
                      bgcolor: activeTab === item.key ? 'rgba(0,120,212,0.12)' : '#F3F2F1',
                    },
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}
        </Box>

        {/* Right — Workspace Badge */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {selectedWorkspace && (
            <Chip
              label={selectedWorkspace.name}
              size="small"
              sx={{
                bgcolor: 'rgba(0,120,212,0.08)',
                color: '#0078D4',
                fontWeight: 600,
                fontSize: '11px',
                height: 26,
                borderRadius: '4px',
                border: '1px solid rgba(0,120,212,0.15)',
                '& .MuiChip-label': { px: 1 },
              }}
            />
          )}
        </Box>
      </Box>

      {/* Workspace not selected hint */}
      {!selectedWorkspace && workspaces.length > 0 && (
        <Box sx={{ px: 3, pb: 0.5 }}>
          <Alert
            severity="info"
            icon={<InfoIcon sx={{ fontSize: 14 }} />}
            sx={{
              width: 'fit-content',
              py: 0,
              px: 1,
              bgcolor: 'rgba(0,120,212,0.06)',
              color: '#0078D4',
              border: '1px solid rgba(0,120,212,0.15)',
              borderRadius: '4px',
              fontSize: '11px',
              '& .MuiAlert-icon': { color: '#0078D4', mr: 0.5, py: 0 },
              '& .MuiAlert-message': { py: 0.25, fontSize: '11px', fontWeight: 500 },
            }}
          >
            Select a workspace to start
          </Alert>
        </Box>
      )}

      {/* Workspace Menu */}
      <Menu
        anchorEl={workspaceMenuAnchor}
        open={isWorkspaceMenuOpen}
        onClose={handleCloseMenus}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: '350px',
            maxWidth: '450px',
            maxHeight: '500px',
            borderRadius: '8px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
            border: '1px solid #EDEBE9',
          },
        }}
        transformOrigin={{ horizontal: 'left', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'left', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, maxHeight: '450px', overflow: 'auto' }}>
          <WorkspaceSelector workspaces={workspaces} isLoading={isLoadingWorkspaces} />
          {selectedWorkspace && (
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #EDEBE9' }}>
              <LakehouseWarehouseSelector />
            </Box>
          )}
        </Box>
      </Menu>
    </Paper>
  );
};

export default PermanentHeader;
