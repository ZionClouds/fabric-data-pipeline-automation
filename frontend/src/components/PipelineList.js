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
  Divider
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { usePipeline } from '../contexts/PipelineContext';

const PipelineList = () => {
  const { selectedWorkspace, setSelectedJobForPreview, refreshPipelineList } = usePipeline();
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPipelines = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch jobs from database
      const response = await fetch('http://localhost:8080/api/jobs?job_type=pipeline_generation&limit=50');

      if (!response.ok) {
        throw new Error(`Failed to fetch pipelines: ${response.statusText}`);
      }

      const jobs = await response.json();

      // Filter and transform jobs to pipeline format
      const pipelineData = jobs
        .filter(job => job.pipeline_name && job.pipeline_definition)
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
    } catch (err) {
      console.error('Error fetching pipelines:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

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
    // Set the selected job ID for preview
    setSelectedJobForPreview(jobId);
  };

  const handleViewInFabric = (workspaceId, pipelineId, pipelineName) => {
    // Open the pipeline in Microsoft Fabric
    // Try the correct URL format for Data Pipelines
    const fabricUrl = `https://app.fabric.microsoft.com/groups/${workspaceId}/pipelines/${pipelineId}`;

    console.log('Opening Fabric Pipeline:');
    console.log('  Workspace ID:', workspaceId);
    console.log('  Pipeline ID:', pipelineId);
    console.log('  Pipeline Name:', pipelineName);
    console.log('  URL:', fabricUrl);

    window.open(fabricUrl, '_blank', 'noopener,noreferrer');
  };

  if (loading) {
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
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          My Pipelines
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchPipelines}
        >
          Refresh
        </Button>
      </Box>

      {pipelines.length === 0 ? (
        <Card sx={{ textAlign: 'center', py: 8 }}>
          <CardContent>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No pipelines found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create your first pipeline using the AI Chat or Pipeline Preview page.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {pipelines.map((pipeline) => (
            <Grid item xs={12} md={6} lg={4} key={pipeline.job_id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {getStatusIcon(pipeline.status)}
                    <Typography variant="h6" component="div" sx={{ ml: 1 }}>
                      {pipeline.pipeline_name}
                    </Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Status:
                    </Typography>
                    <Chip
                      label={pipeline.status}
                      color={getStatusColor(pipeline.status)}
                      size="small"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>

                  {pipeline.workspace_name && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Workspace: {pipeline.workspace_name}
                      </Typography>
                    </Box>
                  )}

                  {pipeline.lakehouse_name && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Lakehouse: {pipeline.lakehouse_name}
                      </Typography>
                    </Box>
                  )}

                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Generation:
                      <Chip
                        label={pipeline.pipeline_generation_status}
                        color={getStatusColor(pipeline.pipeline_generation_status)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Deployment:
                      <Chip
                        label={pipeline.pipeline_deployment_status}
                        color={getStatusColor(pipeline.pipeline_deployment_status)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </Box>

                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Created: {formatDate(pipeline.created_at)}
                    </Typography>
                  </Box>

                  {pipeline.completed_at && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Completed: {formatDate(pipeline.completed_at)}
                      </Typography>
                    </Box>
                  )}

                  {pipeline.error_message && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      {pipeline.error_message}
                    </Alert>
                  )}

                  {pipeline.pipeline_id && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="primary">
                        Fabric Pipeline ID: {pipeline.pipeline_id}
                      </Typography>
                    </Box>
                  )}
                </CardContent>

                <CardActions>
                  <Button
                    size="small"
                    disabled={!pipeline.pipeline_id || !pipeline.workspace_id}
                    onClick={() => handleViewInFabric(pipeline.workspace_id, pipeline.pipeline_id, pipeline.pipeline_name)}
                  >
                    View in Fabric
                  </Button>
                  <Button size="small" onClick={() => handleViewDetails(pipeline.job_id)}>
                    View Details
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default PipelineList;
