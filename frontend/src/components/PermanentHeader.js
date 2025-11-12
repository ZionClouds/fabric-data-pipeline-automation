import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usePipeline } from '../contexts/PipelineContext';
import { pipelineApi } from '../services/api';
import {
  Box,
  Typography,
  Paper,
  Menu,
  Button,
  CircularProgress,
  Alert,
  Chip
} from '@mui/material';
import {
  KeyboardArrowDown as ArrowDownIcon,
  Business as BusinessIcon,
  Storage as StorageIcon,
  Warehouse as WarehouseIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import WorkspaceSelector from './WorkspaceSelector';
import LakehouseWarehouseSelector from './LakehouseWarehouseSelector';

const PermanentHeader = () => {
  const { user } = useAuth();
  const { selectedWorkspace, selectedLakehouse, selectedWarehouse, setSelectedWorkspace } = usePipeline();
  const [workspaces, setWorkspaces] = useState([]);
  const [isLoadingWorkspaces, setIsLoadingWorkspaces] = useState(true);
  const [workspaceMenuAnchor, setWorkspaceMenuAnchor] = useState(null);

  const isWorkspaceMenuOpen = Boolean(workspaceMenuAnchor);

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

  return (
    <Paper
      elevation={0}
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 1100,
        borderRadius: 0,
        borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
        bgcolor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
        },
      }}
    >
      <Box sx={{ p: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Left Section - Single Workspace Dropdown */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {/* Workspace Selector (with integrated lakehouse/warehouse) */}
          <Button
            onClick={handleWorkspaceMenuClick}
            variant="outlined"
            sx={{
              minWidth: '220px',
              height: '36px',
              borderRadius: '6px',
              border: '1px solid rgba(0, 0, 0, 0.12)',
              bgcolor: 'white',
              color: selectedWorkspace ? '#1f2937' : '#6b7280',
              textTransform: 'none',
              justifyContent: 'space-between',
              px: 1.5,
              fontSize: '0.8rem',
              fontWeight: 500,
              '&:hover': {
                bgcolor: '#f9fafb',
                borderColor: 'rgba(0, 123, 255, 0.3)',
              },
            }}
            endIcon={isLoadingWorkspaces ? <CircularProgress size={14} /> : <ArrowDownIcon sx={{ fontSize: 16 }} />}
            disabled={isLoadingWorkspaces}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.8, overflow: 'hidden' }}>
              <BusinessIcon sx={{ fontSize: 14, color: '#6b7280' }} />
              <Typography
                variant="body2"
                sx={{
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  color: 'inherit',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  maxWidth: '160px',
                }}
              >
                {selectedWorkspace ? selectedWorkspace.name : 'Workspace'}
              </Typography>
            </Box>
          </Button>
        </Box>

        {/* Right Section - Selected Workspace Display */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {selectedWorkspace && (
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
          )}
        </Box>
      </Box>

      {/* Show alert when no workspace is selected */}
      {!selectedWorkspace && workspaces.length > 0 && (
        <Box sx={{ px: 3, pb: 0.5 }}>
          <Alert
            severity="warning"
            icon={<InfoIcon sx={{ fontSize: '10px' }} />}
            sx={{
              width: 'fit-content',
              minWidth: '200px',
              maxWidth: '300px',
              py: 0.1,
              px: 0.75,
              bgcolor: '#fff3cd',
              color: '#856404',
              border: '1px solid #ffeaa7',
              borderRadius: '6px',
              fontSize: '11px',
              alignItems: 'center',
              boxShadow: '0 2px 8px rgba(255, 193, 7, 0.2)',
              '& .MuiAlert-icon': {
                color: '#f39c12',
                mr: 0.4,
                py: 0,
                my: 0,
              },
              '& .MuiAlert-message': {
                py: 0,
                my: 0,
                fontSize: '10px',
                fontWeight: 600,
                letterSpacing: '0.25px',
                lineHeight: 1.2,
              },
              '@keyframes pulse': {
                '0%, 100%': {
                  opacity: 1,
                  transform: 'scale(1)',
                },
                '50%': {
                  opacity: 0.8,
                  transform: 'scale(1.02)',
                },
              },
            }}
          >
            Select workspace to start building
          </Alert>
        </Box>
      )}

      {/* Integrated Workspace Menu with Lakehouse/Warehouse */}
      <Menu
        anchorEl={workspaceMenuAnchor}
        open={isWorkspaceMenuOpen}
        onClose={handleCloseMenus}
        sx={{
          zIndex: 1300,
        }}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: '350px',
            maxWidth: '450px',
            maxHeight: '500px',
            borderRadius: '12px',
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.15)',
            border: '1px solid rgba(0, 0, 0, 0.08)',
            overflow: 'visible',
            zIndex: 1300,
            '& .MuiList-root': {
              py: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'left', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'left', vertical: 'bottom' }}
        slotProps={{
          paper: {
            style: {
              maxHeight: '500px',
              overflow: 'auto',
              zIndex: 1300,
            },
          },
        }}
      >
        <Box sx={{ p: 2, maxHeight: '450px', overflow: 'auto' }}>
          {/* Workspace Selection Section */}
          <WorkspaceSelector workspaces={workspaces} isLoading={isLoadingWorkspaces} />
          
          {/* Lakehouse/Warehouse Selection Section - Only show if workspace is selected */}
          {selectedWorkspace && (
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(0, 0, 0, 0.08)' }}>
              <LakehouseWarehouseSelector />
            </Box>
          )}
        </Box>
      </Menu>
    </Paper>
  );
};

export default PermanentHeader;
