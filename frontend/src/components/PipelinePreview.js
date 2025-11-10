import React, { useState, useEffect } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import { useAuth } from '../contexts/AuthContext';
import { pipelineApi } from '../services/api';
import NotebookViewer from './NotebookViewer';
import {
  Box,
  Typography,
  Button,
  Paper,
  Card,
  CardContent,
  Avatar,
  Chip,
  Alert,
  CircularProgress,
  Fade,
  Grid,
  IconButton,
  Collapse
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  RocketLaunch as RocketLaunchIcon,
  Storage as StorageIcon,
  AccountTree as AccountTreeIcon,
  MenuBook as MenuBookIcon,
  Visibility as VisibilityIcon,
  Architecture as ArchitectureIcon,
  PlayArrow as PlayArrowIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';

const PipelinePreview = () => {
  const { selectedWorkspace, chatMessages, pipelineConfig, selectedJobForPreview, setSelectedJobForPreview, triggerPipelineListRefresh } = usePipeline();
  const { user } = useAuth();
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isLoadingJob, setIsLoadingJob] = useState(false);
  const [generatedPipeline, setGeneratedPipeline] = useState(null);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [selectedNotebook, setSelectedNotebook] = useState(null);
  const [error, setError] = useState(null);
  const [deploySuccess, setDeploySuccess] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    activities: true,
    notebooks: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Load job data when selectedJobForPreview is set
  useEffect(() => {
    const loadJobData = async () => {
      if (!selectedJobForPreview) return;

      try {
        setIsLoadingJob(true);
        setError(null);
        setDeploySuccess(null);

        // Fetch job details from API
        const response = await fetch(`http://localhost:8080/api/jobs/${selectedJobForPreview}`);

        if (!response.ok) {
          throw new Error(`Failed to fetch job details: ${response.statusText}`);
        }

        const jobData = await response.json();

        // Store the job_id for deployment
        setCurrentJobId(jobData.job_id);

        // Set the generated pipeline from job data
        if (jobData.pipeline_definition) {
          setGeneratedPipeline({
            pipeline_id: jobData.pipeline_id,
            pipeline_name: jobData.pipeline_name,
            activities: jobData.pipeline_definition.activities || [],
            notebooks: jobData.pipeline_definition.notebooks || [],
            reasoning: jobData.pipeline_definition.reasoning || null
          });
        }

        // Clear the selected job after loading (so it doesn't reload on re-render)
        setSelectedJobForPreview(null);
      } catch (err) {
        console.error('Error loading job data:', err);
        setError('Failed to load pipeline details: ' + err.message);
        setSelectedJobForPreview(null);
      } finally {
        setIsLoadingJob(false);
      }
    };

    loadJobData();
  }, [selectedJobForPreview, setSelectedJobForPreview]);

  const handleGeneratePipeline = async () => {
    try {
      setIsGenerating(true);
      setError(null);
      setDeploySuccess(null);

      // Extract context from chat messages
      const chatContext = chatMessages.map(msg => `${msg.role}: ${msg.content}`).join('\n\n');

      // Use pipeline name from chat context, or generate one if not available
      const pipelineName = pipelineConfig.pipeline_name || ('Pipeline_' + Date.now());
      console.log('Using pipeline name for generation:', pipelineName);

      const response = await pipelineApi.generatePipeline({
        workspace_id: selectedWorkspace.id,
        pipeline_name: pipelineName,
        source_type: 'blob_storage',  // Default to blob storage for now
        source_config: {
          chat_context: chatContext  // Send entire conversation
        },
        tables: ['data'],  // Generic table name
        transformations: [
          {
            transformation_type: 'filtering',
            description: 'Extract from chat conversation',
            source_table: 'bronze_data',
            target_table: 'silver_data',
            layer: 'silver'
          }
        ],
        use_medallion: true,
        schedule: 'manual',
        created_by: user.email
      });

      setGeneratedPipeline(response.data);
    } catch (err) {
      setError('Failed to generate pipeline: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeployPipeline = async () => {
    if (!generatedPipeline) return;

    try {
      setIsDeploying(true);
      setError(null);
      setDeploySuccess(null);

      let response;

      // If we have a job_id, use the job-based deployment endpoint
      if (currentJobId) {
        const res = await fetch(`http://localhost:8080/api/jobs/${currentJobId}/deploy`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.detail || 'Deployment failed');
        }

        response = { data: await res.json() };
      } else {
        // Fallback to old pipeline-based deployment for in-memory pipelines
        response = await pipelineApi.deployPipeline(
          generatedPipeline.pipeline_id,
          selectedWorkspace.id
        );
      }

      setDeploySuccess(`Pipeline deployed successfully! Fabric Pipeline ID: ${response.data.fabric_pipeline_id}`);

      // Trigger refresh of pipeline list to show updated deployment status
      if (triggerPipelineListRefresh) {
        triggerPipelineListRefresh();
      }
    } catch (err) {
      setError('Failed to deploy pipeline: ' + err.message);
    } finally {
      setIsDeploying(false);
    }
  };

  if (isLoadingJob) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#fafafa',
          p: 3
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress size={48} sx={{ mb: 2 }} />
          <Typography variant="h6" color="text.primary">
            Loading pipeline details...
          </Typography>
        </Box>
      </Box>
    );
  }

  if (!selectedWorkspace) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#fafafa',
          p: 3
        }}
      >
        <Box sx={{ textAlign: 'center', maxWidth: 400 }}>
          <Avatar
            sx={{
              width: 48,
              height: 48,
              mx: 'auto',
              mb: 1.5,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
            }}
          >
            <StorageIcon sx={{ fontSize: 24, color: 'white' }} />
          </Avatar>
          <Typography variant="h6" gutterBottom color="text.primary" fontWeight="600" sx={{ fontSize: '1.1rem' }}>
            No Workspace Selected
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
            Please select a workspace to preview and manage your data pipelines
          </Typography>
        </Box>
      </Box>
    );
  }

  if (chatMessages.length === 0 && !generatedPipeline) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: '#fafafa',
          p: 3
        }}
      >
        <Box sx={{ textAlign: 'center', maxWidth: 500 }}>
          <Avatar
            sx={{
              width: 56,
              height: 56,
              mx: 'auto',
              mb: 2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              boxShadow: '0 8px 24px rgba(102, 126, 234, 0.3)',
              animation: 'pulse 2s infinite ease-in-out',
              '@keyframes pulse': {
                '0%': {
                  transform: 'scale(1)',
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.3)',
                },
                '50%': {
                  transform: 'scale(1.03)',
                  boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)',
                },
                '100%': {
                  transform: 'scale(1)',
                  boxShadow: '0 8px 24px rgba(102, 126, 234, 0.3)',
                },
              },
            }}
          >
            <ArchitectureIcon sx={{ fontSize: 28, color: 'white' }} />
          </Avatar>
          <Typography 
            variant="h6" 
            gutterBottom 
            sx={{
              fontWeight: 600,
              fontSize: '1.2rem',
              background: 'linear-gradient(135deg, #1f2937 0%, #4f46e5 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Ready to Build Your Pipeline
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, fontSize: '0.85rem' }}>
            Start a conversation in the AI Chat tab to design your data pipeline architecture
          </Typography>
          <Chip 
            label="💬 Go to AI Chat"
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              fontWeight: 600,
              px: 2,
              py: 1,
              '& .MuiChip-label': {
                fontSize: '0.9rem'
              }
            }}
          />
        </Box>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: '#fafafa',
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          px: 2.5,
          py: 1.8,
          borderBottom: '1px solid #e8f4fd',
          bgcolor: 'white',
          flexShrink: 0,
          boxShadow: '0 2px 8px rgba(102, 126, 234, 0.08)'
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar
              sx={{
                width: 32,
                height: 32,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                boxShadow: '0 3px 8px rgba(102, 126, 234, 0.3)',
              }}
            >
              <ArchitectureIcon sx={{ fontSize: 18, color: 'white' }} />
            </Avatar>
            <Box>
              <Typography 
                variant="h6" 
                sx={{ 
                  fontWeight: 600,
                  fontSize: '1.1rem',
                  background: 'linear-gradient(135deg, #1f2937 0%, #4f46e5 100%)',
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                Pipeline Preview
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                Generate and deploy your data pipeline
              </Typography>
            </Box>
          </Box>
          
          <Button
            onClick={handleGeneratePipeline}
            disabled={isGenerating}
            variant="contained"
            startIcon={isGenerating ? <CircularProgress size={16} color="inherit" /> : <AutoAwesomeIcon />}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2.5,
              px: 2.5,
              py: 1,
              boxShadow: '0 3px 12px rgba(102, 126, 234, 0.3)',
              textTransform: 'none',
              fontWeight: 600,
              fontSize: '0.85rem',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                boxShadow: '0 4px 16px rgba(102, 126, 234, 0.4)',
                transform: 'translateY(-1px)',
              },
              '&:disabled': {
                background: 'rgba(102, 126, 234, 0.5)',
                color: 'white',
              },
              transition: 'all 0.2s ease-in-out',
            }}
          >
            {isGenerating ? 'Generating...' : 'Generate Pipeline'}
          </Button>
        </Box>
      </Paper>

      {/* Content Area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          '&::-webkit-scrollbar': {
            width: '4px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'transparent',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'rgba(102, 126, 234, 0.3)',
            borderRadius: '2px',
            '&:hover': {
              background: 'rgba(102, 126, 234, 0.5)',
            },
          },
        }}
      >
        {/* Alerts */}
        {error && (
          <Fade in={true}>
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2, 
                borderRadius: 2,
                '& .MuiAlert-icon': {
                  fontSize: '1.1rem'
                }
              }}
            >
              {error}
            </Alert>
          </Fade>
        )}
        
        {deploySuccess && (
          <Fade in={true}>
            <Alert 
              severity="success" 
              sx={{ 
                mb: 2, 
                borderRadius: 2,
                '& .MuiAlert-icon': {
                  fontSize: '1.1rem'
                }
              }}
            >
              {deploySuccess}
            </Alert>
          </Fade>
        )}

        {generatedPipeline ? (
          <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
            {/* Pipeline Header */}
            <Card
              elevation={0}
              sx={{
                mb: 2,
                borderRadius: 2.5,
                border: '1px solid rgba(102, 126, 234, 0.12)',
                background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%)',
                backdropFilter: 'blur(20px)',
                overflow: 'hidden',
                position: 'relative',
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '3px',
                  background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                },
              }}
            >
              <CardContent sx={{ p: 2.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 600, color: 'text.primary', mb: 0.8, fontSize: '1.1rem' }}>
                      📊 {generatedPipeline.pipeline_name}
                    </Typography>
                    {generatedPipeline.reasoning && (
                      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5, fontSize: '0.85rem' }}>
                        <strong>Architectural Decisions:</strong> {generatedPipeline.reasoning}
                      </Typography>
                    )}
                  </Box>
                  
                  <Button
                    onClick={handleDeployPipeline}
                    disabled={isDeploying}
                    variant="contained"
                    startIcon={isDeploying ? <CircularProgress size={16} color="inherit" /> : <RocketLaunchIcon />}
                    sx={{
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      borderRadius: 2,
                      px: 2,
                      py: 0.8,
                      boxShadow: '0 3px 10px rgba(16, 185, 129, 0.3)',
                      textTransform: 'none',
                      fontWeight: 600,
                      fontSize: '0.8rem',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                        boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
                        transform: 'translateY(-1px)',
                      },
                      '&:disabled': {
                        background: 'rgba(16, 185, 129, 0.5)',
                        color: 'white',
                      },
                      transition: 'all 0.2s ease-in-out',
                    }}
                  >
                    {isDeploying ? 'Deploying...' : 'Deploy to Fabric'}
                  </Button>
                </Box>
              </CardContent>
            </Card>

            <Grid container spacing={2}>
              {/* Activities Section */}
              <Grid item xs={12} md={6}>
                <Card
                  elevation={0}
                  sx={{
                    borderRadius: 2.5,
                    border: '1px solid rgba(102, 126, 234, 0.12)',
                    bgcolor: 'white',
                    height: 'fit-content',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      boxShadow: '0 6px 24px rgba(102, 126, 234, 0.12)',
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  <CardContent sx={{ p: 0 }}>
                    <Box
                      onClick={() => toggleSection('activities')}
                      sx={{
                        p: 2,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        borderBottom: '1px solid rgba(0,0,0,0.06)',
                        '&:hover': {
                          bgcolor: 'rgba(102, 126, 234, 0.02)',
                        },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2 }}>
                        <Avatar
                          sx={{
                            width: 28,
                            height: 28,
                            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                          }}
                        >
                          <AccountTreeIcon sx={{ fontSize: 16, color: 'white' }} />
                        </Avatar>
                        <Box>
                          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
                            Pipeline Activities
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                            {generatedPipeline.activities?.length || 0} activities configured
                          </Typography>
                        </Box>
                      </Box>
                      <IconButton size="small">
                        {expandedSections.activities ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Box>

                    <Collapse in={expandedSections.activities}>
                      <Box sx={{ p: 2 }}>
                        {generatedPipeline.activities && generatedPipeline.activities.length > 0 ? (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                            {generatedPipeline.activities.map((activity, index) => (
                              <Paper
                                key={index}
                                elevation={0}
                                sx={{
                                  p: 1.5,
                                  borderRadius: 1.5,
                                  border: '1px solid rgba(102, 126, 234, 0.1)',
                                  bgcolor: 'rgba(248, 250, 252, 0.5)',
                                  position: 'relative',
                                  '&::before': {
                                    content: '""',
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    bottom: 0,
                                    width: '2px',
                                    background: 'linear-gradient(180deg, #667eea 0%, #764ba2 100%)',
                                    borderRadius: '0 1px 1px 0',
                                  },
                                }}
                              >
                                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5, fontSize: '0.85rem' }}>
                                  {activity.name}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
                                  <strong>Type:</strong> {activity.type}
                                </Typography>
                                {activity.config?.description && (
                                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1, fontSize: '0.75rem', fontStyle: 'italic' }}>
                                    {activity.config.description}
                                  </Typography>
                                )}
                                {activity.depends_on && activity.depends_on.length > 0 && (
                                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                    <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                                      Depends on:
                                    </Typography>
                                    {activity.depends_on.map((dep, depIndex) => (
                                      <Chip
                                        key={depIndex}
                                        label={dep}
                                        size="small"
                                        sx={{
                                          fontSize: '0.7rem',
                                          height: 20,
                                          bgcolor: 'rgba(102, 126, 234, 0.1)',
                                          color: 'text.secondary',
                                        }}
                                      />
                                    ))}
                                  </Box>
                                )}
                              </Paper>
                            ))}
                          </Box>
                        ) : (
                          <Box sx={{ textAlign: 'center', py: 3 }}>
                            <Typography variant="body2" color="text.secondary">
                              No activities defined
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </Collapse>
                  </CardContent>
                </Card>
              </Grid>

              {/* Notebooks Section */}
              <Grid item xs={12} md={6}>
                <Card
                  elevation={0}
                  sx={{
                    borderRadius: 2.5,
                    border: '1px solid rgba(102, 126, 234, 0.12)',
                    bgcolor: 'white',
                    height: 'fit-content',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                      boxShadow: '0 6px 24px rgba(102, 126, 234, 0.12)',
                      transform: 'translateY(-1px)',
                    },
                  }}
                >
                  <CardContent sx={{ p: 0 }}>
                    <Box
                      onClick={() => toggleSection('notebooks')}
                      sx={{
                        p: 2,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        borderBottom: '1px solid rgba(0,0,0,0.06)',
                        '&:hover': {
                          bgcolor: 'rgba(102, 126, 234, 0.02)',
                        },
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.2 }}>
                        <Avatar
                          sx={{
                            width: 28,
                            height: 28,
                            background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                          }}
                        >
                          <MenuBookIcon sx={{ fontSize: 16, color: 'white' }} />
                        </Avatar>
                        <Box>
                          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
                            Notebooks
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                            {generatedPipeline.notebooks?.length || 0} notebooks generated
                          </Typography>
                        </Box>
                      </Box>
                      <IconButton size="small">
                        {expandedSections.notebooks ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Box>

                    <Collapse in={expandedSections.notebooks}>
                      <Box sx={{ p: 2 }}>
                        {generatedPipeline.notebooks && generatedPipeline.notebooks.length > 0 ? (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                            {generatedPipeline.notebooks.map((notebook, index) => (
                              <Paper
                                key={index}
                                elevation={0}
                                sx={{
                                  p: 1.5,
                                  borderRadius: 1.5,
                                  border: '1px solid rgba(139, 92, 246, 0.1)',
                                  bgcolor: 'rgba(248, 250, 252, 0.5)',
                                  position: 'relative',
                                  '&::before': {
                                    content: '""',
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    bottom: 0,
                                    width: '2px',
                                    background: 'linear-gradient(180deg, #8b5cf6 0%, #7c3aed 100%)',
                                    borderRadius: '0 1px 1px 0',
                                  },
                                }}
                              >
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                  <Box sx={{ flex: 1 }}>
                                    <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5, fontSize: '0.85rem' }}>
                                      {notebook.notebook_name}
                                    </Typography>
                                    <Chip
                                      label={notebook.layer}
                                      size="small"
                                      sx={{
                                        fontSize: '0.65rem',
                                        height: 18,
                                        mb: 0.8,
                                        bgcolor: 'rgba(139, 92, 246, 0.1)',
                                        color: 'text.primary',
                                        fontWeight: 600,
                                      }}
                                    />
                                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                                      {notebook.description}
                                    </Typography>
                                  </Box>
                                  <Button
                                    onClick={() => setSelectedNotebook(notebook)}
                                    variant="outlined"
                                    size="small"
                                    startIcon={<VisibilityIcon />}
                                    sx={{
                                      ml: 1.5,
                                      borderRadius: 1.5,
                                      textTransform: 'none',
                                      fontSize: '0.7rem',
                                      py: 0.5,
                                      px: 1.2,
                                      borderColor: 'rgba(139, 92, 246, 0.3)',
                                      color: '#8b5cf6',
                                      '&:hover': {
                                        borderColor: '#8b5cf6',
                                        bgcolor: 'rgba(139, 92, 246, 0.04)',
                                      },
                                    }}
                                  >
                                    View Code
                                  </Button>
                                </Box>
                              </Paper>
                            ))}
                          </Box>
                        ) : (
                          <Box sx={{ textAlign: 'center', py: 2 }}>
                            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                              No notebooks defined
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </Collapse>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        ) : (
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              py: 4
            }}
          >
            <Box sx={{ textAlign: 'center', maxWidth: 350 }}>
              <Avatar
                sx={{
                  width: 56,
                  height: 56,
                  mx: 'auto',
                  mb: 2,
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
                  border: '2px solid rgba(102, 126, 234, 0.2)',
                }}
              >
                <PlayArrowIcon sx={{ fontSize: 28, color: '#667eea' }} />
              </Avatar>
              <Typography variant="h6" gutterBottom color="text.primary" fontWeight="600" sx={{ fontSize: '1.1rem' }}>
                Ready to Generate
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.5, fontSize: '0.85rem' }}>
                Click "Generate Pipeline" to create your pipeline based on the conversation context
              </Typography>
            </Box>
          </Box>
        )}
      </Box>

      {selectedNotebook && (
        <NotebookViewer notebook={selectedNotebook} onClose={() => setSelectedNotebook(null)} />
      )}
    </Box>
  );
};

export default PipelinePreview;
