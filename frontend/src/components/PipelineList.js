import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Grid,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Fade,
  Paper,
  FormControl,
  InputLabel,
  Select,
  Stack
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Storage as StorageIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
  Visibility as VisibilityIcon,
  Launch as LaunchIcon,
  FilterList as FilterListIcon,
  Sort as SortIcon
} from '@mui/icons-material';
import { usePipeline } from '../contexts/PipelineContext';

// API URL from env config (supports Docker runtime injection)
const API_BASE_URL = window._env_?.REACT_APP_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8080';

const PipelineList = () => {
  const { selectedWorkspace, setSelectedJobForPreview, refreshPipelineList } = usePipeline();
  const [pipelines, setPipelines] = useState([]);
  const [filteredPipelines, setFilteredPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [renameDialog, setRenameDialog] = useState({ open: false, pipeline: null, newName: '' });
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_desc');

  const fetchPipelines = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch jobs from database
      const response = await fetch(`${API_BASE_URL}/api/jobs?job_type=pipeline_generation&limit=50`);

      if (!response.ok) {
        throw new Error(`Failed to fetch pipelines: ${response.statusText}`);
      }

      const jobs = await response.json();

      // Filter and transform jobs to pipeline format
      const pipelineData = jobs
        .filter(job => job.pipeline_name && job.pipeline_definition && job.status !== 'deleted')
        .map(job => ({
          job_id: job.job_id,
          pipeline_name: job.pipeline_name,
          status: job.status,
          pipeline_generation_status: job.pipeline_generation_status,
          pipeline_deployment_status: job.pipeline_deployment_status,
          pipeline_id: job.pipeline_id,
          workspace_id: job.workspace_id,
          workspace_name: job.workspace_name,
          lakehouse_name: job.lakehouse_name,
          created_at: job.created_at,
          completed_at: job.completed_at,
          error_message: job.error_message
        }));

      setPipelines(pipelineData);
      setFilteredPipelines(pipelineData);
    } catch (err) {
      console.error('Error fetching pipelines:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort pipelines
  useEffect(() => {
    let filtered = [...pipelines];

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(pipeline => pipeline.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name_asc':
          return a.pipeline_name.localeCompare(b.pipeline_name);
        case 'name_desc':
          return b.pipeline_name.localeCompare(a.pipeline_name);
        case 'created_asc':
          return new Date(a.created_at) - new Date(b.created_at);
        case 'created_desc':
          return new Date(b.created_at) - new Date(a.created_at);
        case 'status_asc':
          return a.status.localeCompare(b.status);
        case 'status_desc':
          return b.status.localeCompare(a.status);
        default:
          return new Date(b.created_at) - new Date(a.created_at);
      }
    });

    setFilteredPipelines(filtered);
  }, [pipelines, statusFilter, sortBy]);

  useEffect(() => {
    fetchPipelines();

    // Refresh pipelines when the window gains focus (user comes back from deployment)
    const handleFocus = () => {
      console.log('Window focused - refreshing pipeline list');
      fetchPipelines();
    };

    // Refresh when visibility changes (user switches tabs)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('Page visible - refreshing pipeline list');
        fetchPipelines();
      }
    };

    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup listeners
    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Refresh when refreshPipelineList changes (triggered from other components)
  useEffect(() => {
    if (refreshPipelineList > 0) {
      console.log('Pipeline list refresh triggered from context');
      fetchPipelines();
    }
  }, [refreshPipelineList]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'in_progress':
      case 'pending':
        return <PendingIcon color="warning" />;
      default:
        return <PendingIcon />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'warning';
      case 'pending':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleViewDetails = (jobId) => {
    // Set the selected job ID for preview without triggering loading state
    setSelectedJobForPreview(jobId);
  };

  const handleViewInFabric = (workspaceId, pipelineId, pipelineName) => {
    // Open the pipeline in Microsoft Fabric without triggering loading state
    // Try the correct URL format for Data Pipelines
    const fabricUrl = `https://app.fabric.microsoft.com/groups/${workspaceId}/pipelines/${pipelineId}`;

    console.log('Opening Fabric Pipeline:');
    console.log('  Workspace ID:', workspaceId);
    console.log('  Pipeline ID:', pipelineId);
    console.log('  Pipeline Name:', pipelineName);
    console.log('  URL:', fabricUrl);

    window.open(fabricUrl, '_blank', 'noopener,noreferrer');
  };

  const handleDeletePipeline = async (jobId, pipelineName) => {
    // Confirm deletion
    if (!window.confirm(`Are you sure you want to delete pipeline "${pipelineName}"?\n\nThis will delete the pipeline from both the Fabric workspace and the database.`)) {
      return;
    }

    try {
      setError(null);
      // Show a local loading indicator instead of global loading

      const response = await fetch(`${API_BASE_URL}/api/pipelines/${jobId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete pipeline: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Delete result:', result);

      // Show success message
      alert(`Pipeline "${pipelineName}" deleted successfully!`);

      // Refresh pipeline list
      await fetchPipelines();
    } catch (err) {
      console.error('Error deleting pipeline:', err);
      setError(err.message);
      alert(`Failed to delete pipeline: ${err.message}`);
    }
  };

  const handleRenamePipeline = async (jobId, newName) => {
    try {
      setError(null);
      // Don't set loading to true for rename operations to avoid UI disruption

      const response = await fetch(`${API_BASE_URL}/api/pipelines/${jobId}/rename`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_pipeline_name: newName })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to rename pipeline: ${response.statusText}`);
      }

      // Show success message
      alert(`Pipeline renamed to "${newName}" successfully!`);

      // Refresh pipeline list
      await fetchPipelines();
    } catch (err) {
      console.error('Error renaming pipeline:', err);
      setError(err.message);
      alert(`Failed to rename pipeline: ${err.message}`);
    } finally {
      setRenameDialog({ open: false, pipeline: null, newName: '' });
    }
  };

  const handleOpenRenameDialog = (pipeline) => {
    setRenameDialog({ open: true, pipeline, newName: pipeline.pipeline_name });
    setAnchorEl(null);
  };

  const handleCloseRenameDialog = () => {
    setRenameDialog({ open: false, pipeline: null, newName: '' });
  };

  const handleMenuOpen = (event, pipeline) => {
    setAnchorEl(event.currentTarget);
    setSelectedPipeline(pipeline);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedPipeline(null);
  };

  if (loading && pipelines.length === 0) {
    // Only show loading screen if we have no pipelines yet
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading pipelines...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={fetchPipelines}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ 
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      bgcolor: '#fafafa'
    }}>
      {/* Compact Header with Filters */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: 1.5, 
          borderRadius: '20px', 
          borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
          bgcolor: 'white',
          background: 'linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
          backdropFilter: 'blur(8px)',
          position: 'relative',
          m: 2,
          mt: 0,
          mb: 0,
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '2px',
            background: 'linear-gradient(90deg, rgba(102, 126, 234, 0.3), rgba(76, 175, 80, 0.3), rgba(255, 152, 0, 0.3))',
            borderRadius: '20px 20px 0 0',
          }
        }}
      >
        <Stack 
          direction={{ xs: 'column', sm: 'row' }} 
          spacing={1.5} 
          alignItems={{ xs: 'stretch', sm: 'center' }}
          justifyContent="space-between"
        >
          {/* Filter and Sort Controls */}
          <Stack direction="row" spacing={1.5} alignItems="center" sx={{ minWidth: 0 }}>
            <FormControl size="small" sx={{ 
              minWidth: 110,
              '& .MuiOutlinedInput-root': {
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(8px)',
                transition: 'all 0.3s ease',
                fontSize: '0.85rem',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.95)',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                },
                '&.Mui-focused': {
                  background: 'rgba(255, 255, 255, 1)',
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.2)',
                }
              },
              '& .MuiInputLabel-root': {
                fontSize: '0.85rem'
              }
            }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="not_started">Not Started</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
              </Select>
            </FormControl>
            
            <FormControl size="small" sx={{ 
              minWidth: 130,
              '& .MuiOutlinedInput-root': {
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(8px)',
                transition: 'all 0.3s ease',
                fontSize: '0.85rem',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.95)',
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                },
                '&.Mui-focused': {
                  background: 'rgba(255, 255, 255, 1)',
                  boxShadow: '0 4px 12px rgba(102, 126, 234, 0.2)',
                }
              },
              '& .MuiInputLabel-root': {
                fontSize: '0.85rem'
              }
            }}>
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                label="Sort By"
                onChange={(e) => setSortBy(e.target.value)}
              >
                <MenuItem value="created_desc">Newest First</MenuItem>
                <MenuItem value="created_asc">Oldest First</MenuItem>
                <MenuItem value="name_asc">Name A-Z</MenuItem>
                <MenuItem value="name_desc">Name Z-A</MenuItem>
                <MenuItem value="status_asc">Status A-Z</MenuItem>
                <MenuItem value="status_desc">Status Z-A</MenuItem>
              </Select>
            </FormControl>

            <Typography variant="body2" color="text.secondary" sx={{ ml: 1.5, fontSize: '0.8rem' }}>
              {filteredPipelines.length} pipeline{filteredPipelines.length !== 1 ? 's' : ''}
            </Typography>
          </Stack>

          {/* Action Buttons */}
          <Stack direction="row" spacing={1} alignItems="center">
            {loading && pipelines.length > 0 && (
              <CircularProgress size={16} sx={{ mr: 1 }} />
            )}
            <Button
              variant="outlined"
              size="small"
              startIcon={<RefreshIcon sx={{ fontSize: 16 }} />}
              onClick={fetchPipelines}
              disabled={loading}
              sx={{
                textTransform: 'none',
                borderRadius: '10px',
                px: 1.75,
                py: 0.5,
                fontSize: '0.8rem',
                fontWeight: 600,
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(102, 126, 234, 0.3)',
                color: 'rgba(102, 126, 234, 0.9)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: 'rgba(102, 126, 234, 0.05)',
                  borderColor: 'rgba(102, 126, 234, 0.5)',
                  boxShadow: '0 2px 8px rgba(102, 126, 234, 0.2)',
                  transform: 'translateY(-1px)',
                },
                '&:disabled': {
                  background: 'rgba(255, 255, 255, 0.5)',
                  color: 'rgba(0, 0, 0, 0.4)',
                  borderColor: 'rgba(0, 0, 0, 0.1)',
                }
              }}
            >
              {loading && pipelines.length > 0 ? 'Refreshing...' : 'Refresh'}
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {/* Scrollable Content */}
      <Box sx={{ 
        flex: 1,
        overflow: 'auto',
        p: 3,
        pb: 16, // Increased bottom padding for better visibility of last row
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: 'rgba(0,0,0,0.05)',
          borderRadius: '4px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '4px',
          '&:hover': {
            background: 'rgba(0,0,0,0.5)',
          },
        },
      }}>
        {filteredPipelines.length === 0 ? (
          <Fade in={true} timeout={600}>
            <Card sx={{ 
              textAlign: 'center', 
              py: 8, 
              bgcolor: 'rgba(102, 126, 234, 0.05)',
              border: '1px solid rgba(102, 126, 234, 0.1)',
              borderRadius: '12px',
              mx: 'auto',
              maxWidth: 600
            }}>
              <CardContent>
                <Box sx={{ mb: 3 }}>
                  <StorageIcon sx={{ 
                    fontSize: 64, 
                    color: 'rgba(102, 126, 234, 0.5)', 
                    mb: 2 
                  }} />
                </Box>
                {pipelines.length === 0 ? (
                  <>
                    <Typography variant="h5" color="text.primary" gutterBottom sx={{ fontWeight: 600 }}>
                      No Pipelines Yet
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto', lineHeight: 1.6 }}>
                      Get started by creating your first data pipeline. You can use our AI Chat to build pipelines automatically or create them manually.
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                      <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        onClick={() => window.location.href = '/'}
                        sx={{
                          textTransform: 'none',
                          px: 3,
                          py: 1.5,
                          fontSize: '15px',
                          fontWeight: 600,
                          borderRadius: '8px',
                          boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
                        }}
                      >
                        Create Pipeline with AI Chat
                      </Button>
                      <Button
                        variant="outlined"
                        size="large"
                        onClick={() => window.location.href = '/pipeline-preview'}
                        sx={{
                          textTransform: 'none',
                          px: 3,
                          py: 1.5,
                          fontSize: '15px',
                          fontWeight: 600,
                          borderColor: 'rgba(102, 126, 234, 0.5)',
                          color: '#0078D4',
                          borderRadius: '8px'
                        }}
                      >
                        View Pipeline Preview
                      </Button>
                    </Box>
                  </>
                ) : (
                  <>
                    <Typography variant="h5" color="text.primary" gutterBottom sx={{ fontWeight: 600 }}>
                      No Pipelines Match Your Filter
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 500, mx: 'auto', lineHeight: 1.6 }}>
                      Try adjusting your filter settings to see more pipelines, or create a new pipeline.
                    </Typography>
                    <Button
                      variant="outlined"
                      onClick={() => {
                        setStatusFilter('all');
                        setSortBy('created_desc');
                      }}
                      sx={{
                        textTransform: 'none',
                        px: 3,
                        py: 1,
                        fontSize: '14px',
                        fontWeight: 600,
                        borderRadius: '8px'
                      }}
                    >
                      Clear Filters
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </Fade>
        ) : (
          <Grid container spacing={3} sx={{
            '& .MuiGrid-item': {
              display: 'flex',
              justifyContent: 'center'
            }
          }}>
            {filteredPipelines.map((pipeline, index) => (
              <Grid item xs={12} md={6} lg={4} key={pipeline.job_id} sx={{
                display: 'flex',
                justifyContent: 'center'
              }}>
                <Fade in={true} timeout={300 + index * 100}>
                  <Card sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: '16px',
                    border: '1px solid rgba(0, 0, 0, 0.06)',
                    background: 'linear-gradient(145deg, #ffffff 0%, #fafafa 100%)',
                    boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
                    backdropFilter: 'blur(8px)',
                    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                    height: '320px', // Fixed height for all cards
                    width: '100%', // Fixed width to fill container
                    maxWidth: '400px', // Maximum width constraint
                    minWidth: '300px', // Minimum width constraint
                    position: 'relative',
                    overflow: 'hidden',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '3px',
                      background: 'linear-gradient(90deg, rgba(102, 126, 234, 0.6), rgba(76, 175, 80, 0.6), rgba(255, 152, 0, 0.6))',
                      opacity: 0,
                      transition: 'opacity 0.3s ease',
                    },
                    '&:hover': {
                      transform: 'translateY(-6px) scale(1.02)',
                      boxShadow: '0 12px 32px rgba(0, 0, 0, 0.15)',
                      borderColor: 'rgba(102, 126, 234, 0.4)',
                      background: 'linear-gradient(145deg, #ffffff 0%, #f8f9ff 100%)',
                      '&::before': {
                        opacity: 1,
                      }
                    }
                  }}>
                    <CardContent sx={{ 
                      flexGrow: 1, 
                      p: 2, 
                      pb: 1, 
                      overflow: 'hidden',
                      display: 'flex',
                      flexDirection: 'column',
                      height: '100%',
                      maxHeight: '260px' // Ensure content doesn't exceed card height
                    }}>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', flex: 1, minWidth: 0 }}>
                          {getStatusIcon(pipeline.status)}
                          <Typography variant="h6" component="div" sx={{ 
                            ml: 1, 
                            fontWeight: 600,
                            fontSize: '1rem',
                            color: '#1a1a1a',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            flex: 1,
                            maxWidth: '200px', // Fixed max width to prevent expansion
                            minWidth: '100px'   // Fixed min width to prevent shrinking
                          }}>
                            {pipeline.pipeline_name}
                          </Typography>
                        </Box>
                        <IconButton 
                          size="small" 
                          onClick={(e) => handleMenuOpen(e, pipeline)}
                          sx={{ ml: 1, flexShrink: 0 }}
                        >
                          <MoreVertIcon fontSize="small" />
                        </IconButton>
                      </Box>

                      <Divider sx={{ my: 1 }} />

                      {/* Status Section */}
                      <Box sx={{ mb: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem', fontWeight: 500 }}>
                            Status:
                          </Typography>
                          <Chip
                            label={pipeline.status}
                            color={getStatusColor(pipeline.status)}
                            size="small"
                            sx={{ 
                              fontWeight: 600,
                              textTransform: 'capitalize',
                              fontSize: '0.7rem',
                              height: '20px'
                            }}
                          />
                        </Box>
                      </Box>

                      {/* Workspace and Lakehouse - Compact */}
                      {(pipeline.workspace_name || pipeline.lakehouse_name) && (
                        <Box sx={{ 
                          mb: 1.5, 
                          fontSize: '0.8rem',
                          minHeight: '40px', // Reserve space even if content is short
                          maxHeight: '40px', // Prevent expansion
                          overflow: 'hidden'
                        }}>
                          {pipeline.workspace_name && (
                            <Typography variant="body2" color="text.secondary" sx={{ 
                              fontSize: '0.8rem', 
                              mb: 0.3,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              maxWidth: '250px' // Constrain text width
                            }}>
                              Workspace: {pipeline.workspace_name}
                            </Typography>
                          )}
                          {pipeline.lakehouse_name && (
                            <Typography variant="body2" color="text.secondary" sx={{ 
                              fontSize: '0.8rem',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              maxWidth: '250px' // Constrain text width
                            }}>
                              Lakehouse: {pipeline.lakehouse_name}
                            </Typography>
                          )}
                        </Box>
                      )}

                      {/* Generation and Deployment Status - Compact Row */}
                      <Box sx={{ mb: 1.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                            Generation:
                          </Typography>
                          <Chip
                            label={pipeline.pipeline_generation_status}
                            color={getStatusColor(pipeline.pipeline_generation_status)}
                            size="small"
                            sx={{ 
                              fontWeight: 600, 
                              textTransform: 'capitalize',
                              fontSize: '0.65rem',
                              height: '18px'
                            }}
                          />
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                            Deployment:
                          </Typography>
                          <Chip
                            label={pipeline.pipeline_deployment_status}
                            color={getStatusColor(pipeline.pipeline_deployment_status)}
                            size="small"
                            sx={{ 
                              fontWeight: 600, 
                              textTransform: 'capitalize',
                              fontSize: '0.65rem',
                              height: '18px'
                            }}
                          />
                        </Box>
                      </Box>

                      {/* Created Date - Always show, minimal space */}
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary" sx={{ 
                          fontSize: '0.7rem',
                          display: 'block',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          Created: {formatDate(pipeline.created_at)}
                        </Typography>
                      </Box>

                      {/* Error Message - Compact if present */}
                      <Box sx={{ 
                        mb: 1, 
                        minHeight: '32px', // Reserve space whether error exists or not
                        maxHeight: '32px', // Prevent expansion
                        overflow: 'hidden'
                      }}>
                        {pipeline.error_message && (
                          <Alert severity="error" sx={{ 
                            borderRadius: '6px',
                            fontSize: '0.7rem',
                            minHeight: '28px',
                            maxHeight: '28px',
                            '& .MuiAlert-message': {
                              fontSize: '0.7rem',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }
                          }}>
                            {pipeline.error_message}
                          </Alert>
                        )}
                      </Box>

                      {/* Fabric Pipeline ID - Fixed positioning at bottom of content */}
                      <Box sx={{ 
                        mt: 'auto',
                        pt: 1,
                        minHeight: '24px', // Reserve space whether ID exists or not
                        display: 'flex',
                        alignItems: 'center'
                      }}>
                        {pipeline.pipeline_id ? (
                          <Box sx={{ 
                            p: 0.8, 
                            bgcolor: 'rgba(102, 126, 234, 0.05)', 
                            borderRadius: '6px',
                            width: '100%',
                            overflow: 'hidden'
                          }}>
                            <Typography variant="caption" color="primary" sx={{ 
                              fontWeight: 600,
                              fontSize: '0.65rem',
                              display: 'block',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}>
                              ID: {pipeline.pipeline_id}
                            </Typography>
                          </Box>
                        ) : (
                          <Box sx={{ height: '24px' }} /> // Placeholder to maintain consistent spacing
                        )}
                      </Box>
                    </CardContent>

                    <CardActions sx={{ 
                      p: 1.5, 
                      pt: 0, 
                      mt: 'auto',
                      height: '50px', // Fixed height for all card actions
                      minHeight: '50px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-start'
                    }}>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<LaunchIcon sx={{ fontSize: '14px' }} />}
                        disabled={!pipeline.pipeline_id || !pipeline.workspace_id}
                        onClick={() => handleViewInFabric(pipeline.workspace_id, pipeline.pipeline_id, pipeline.pipeline_name)}
                        sx={{ 
                          textTransform: 'none',
                          borderRadius: '5px',
                          fontSize: '11px',
                          px: 1.5,
                          py: 0.5,
                          minWidth: 'auto'
                        }}
                      >
                        Fabric
                      </Button>
                      <Button 
                        size="small"
                        variant="text"
                        startIcon={<VisibilityIcon sx={{ fontSize: '14px' }} />}
                        onClick={() => handleViewDetails(pipeline.job_id)}
                        sx={{ 
                          textTransform: 'none',
                          borderRadius: '5px',
                          fontSize: '11px',
                          px: 1.5,
                          py: 0.5,
                          minWidth: 'auto'
                        }}
                      >
                        Details
                      </Button>
                    </CardActions>
                  </Card>
                </Fade>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* Menu for Pipeline Actions */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            borderRadius: '8px',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
            minWidth: 180
          }
        }}
      >
        <MenuItem onClick={() => handleOpenRenameDialog(selectedPipeline)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Rename Pipeline</ListItemText>
        </MenuItem>
        <MenuItem 
          onClick={() => {
            handleViewDetails(selectedPipeline?.job_id);
            handleMenuClose();
          }}
        >
          <ListItemIcon>
            <VisibilityIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem 
          onClick={() => {
            handleDeletePipeline(selectedPipeline?.job_id, selectedPipeline?.pipeline_name);
            handleMenuClose();
          }}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete Pipeline</ListItemText>
        </MenuItem>
      </Menu>

      {/* Rename Dialog */}
      <Dialog 
        open={renameDialog.open} 
        onClose={handleCloseRenameDialog}
        PaperProps={{
          sx: {
            borderRadius: '12px',
            minWidth: 400
          }
        }}
      >
        <DialogTitle sx={{ pb: 1, fontWeight: 600 }}>
          Rename Pipeline
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Enter a new name for "{renameDialog.pipeline?.pipeline_name}"
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label="Pipeline Name"
            value={renameDialog.newName}
            onChange={(e) => setRenameDialog(prev => ({ ...prev, newName: e.target.value }))}
            sx={{ mt: 1 }}
            inputProps={{ maxLength: 100 }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button onClick={handleCloseRenameDialog} sx={{ textTransform: 'none' }}>
            Cancel
          </Button>
          <Button
            onClick={() => handleRenamePipeline(renameDialog.pipeline?.job_id, renameDialog.newName)}
            variant="contained"
            disabled={!renameDialog.newName.trim() || renameDialog.newName === renameDialog.pipeline?.pipeline_name}
            sx={{ 
              textTransform: 'none',
              borderRadius: '6px',
              px: 3
            }}
          >
            Rename
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PipelineList;
