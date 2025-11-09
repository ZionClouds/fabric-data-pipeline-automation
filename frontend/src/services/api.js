import axios from 'axios';

// Runtime env config from window._env_ (injected by Docker at startup)
// Fallback to process.env for local development, then hardcoded defaults
const API_BASE_URL = window._env_?.REACT_APP_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8080';
const WORKSPACE_API_URL = window._env_?.REACT_APP_WORKSPACE_API_URL || process.env.REACT_APP_WORKSPACE_API_URL || 'https://fabric-pipeline-backend.delightfulplant-1c861d44.eastus.azurecontainerapps.io';

// Create axios instance for pipeline builder backend
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create axios instance for workspace backend
const workspaceApi = axios.create({
  baseURL: WORKSPACE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('msal_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

workspaceApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('msal_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
const handleResponse = (error) => {
  if (error.response?.status === 401) {
    console.log('401 Unauthorized error:', error.config?.url);
    
    // Don't automatically log out users on API failures
    // Let components handle 401 errors appropriately
    console.warn('API endpoint returned 401:', error.config?.url);
    console.warn('This might be due to backend configuration, unavailability, or token issues.');
    console.warn('User will remain logged in. If this is a persistent auth issue, user should manually logout and login again.');
  }
  return Promise.reject(error);
};

api.interceptors.response.use((response) => response, handleResponse);
workspaceApi.interceptors.response.use((response) => response, handleResponse);

// Pipeline Builder API endpoints
export const pipelineApi = {
  // Authentication
  validateToken: (token) => api.post('/api/auth/validate-token', { token }),

  // Workspaces (now goes through pipeline builder backend)
  getWorkspaces: () => api.get('/api/workspaces'),
  getWorkspaceLakehouse: (workspaceId) => api.get(`/api/workspaces/${workspaceId}/lakehouse`),

  // Source Connections
  validateConnection: (data) => api.post('/api/sources/validate', data),
  getSourceSchema: (sourceId) => api.get(`/api/sources/${sourceId}/schema`),
  getSourcePreview: (sourceId, table) => api.get(`/api/sources/${sourceId}/preview?table=${table}`),
  saveConnection: (data) => api.post('/api/sources/save', data),

  // AI Chat
  chat: (data) => api.post('/api/ai/chat', data),
  getConversationHistory: (pipelineId) => api.get(`/api/ai/conversations/${pipelineId}`),

  // Pipeline Design
  generatePipeline: (data) => api.post('/api/pipelines/generate', data),
  getPipeline: (pipelineId) => api.get(`/api/pipelines/${pipelineId}`),
  updatePipeline: (pipelineId, data) => api.put(`/api/pipelines/${pipelineId}`, data),
  deletePipeline: (pipelineId) => api.delete(`/api/pipelines/${pipelineId}`),
  listPipelines: (workspaceId) => api.get(`/api/pipelines?workspace_id=${workspaceId}`),

  // Pipeline Deployment
  deployPipeline: (pipelineId, workspaceId) => api.post(`/api/pipelines/${pipelineId}/deploy`, { workspace_id: workspaceId }),
  getDeploymentStatus: (pipelineId) => api.get(`/api/pipelines/${pipelineId}/status`),
  runPipeline: (pipelineId) => api.post(`/api/pipelines/${pipelineId}/run`),
  getPipelineExecutions: (pipelineId) => api.get(`/api/pipelines/${pipelineId}/executions`),

  // Notebooks
  generateNotebook: (data) => api.post('/api/notebooks/generate', data),
  deployNotebook: (data) => api.post('/api/notebooks/deploy', data),
};

export default api;
