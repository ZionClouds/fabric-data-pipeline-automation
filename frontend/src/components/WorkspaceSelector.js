import React from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import {
  Box,
  Typography,
  FormControl,
  Select,
  MenuItem,
  CircularProgress,
  Chip,
  Alert
} from '@mui/material';
import { Business as BusinessIcon, CheckCircle as CheckIcon, Info as InfoIcon } from '@mui/icons-material';

const WorkspaceSelector = ({ workspaces, isLoading }) => {
  const { selectedWorkspace, setSelectedWorkspace } = usePipeline();

  const handleSelect = (event) => {
    const workspace = workspaces.find(w => w.id === event.target.value);
    setSelectedWorkspace(workspace);
  };

  if (isLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 1.5,
        p: 2,
      }}>
        <CircularProgress 
          size={16} 
          sx={{ color: '#0066cc' }} 
        />
        <Typography 
          variant="body2" 
          sx={{ 
            color: '#6b7280',
            fontSize: '13px'
          }}
        >
          Loading workspaces...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Typography
        variant="caption"
        sx={{
          color: '#0066cc',
          fontSize: '11px',
          fontWeight: 600,
          mb: 1.5,
          display: 'block',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        Workspace
      </Typography>
      
      <FormControl fullWidth size="small">
        <Select
          value={selectedWorkspace?.id || ''}
          onChange={handleSelect}
          displayEmpty
          sx={{
            color: '#1f2937',
            fontSize: '13px',
            minHeight: '36px',
            '& .MuiSelect-select': {
              py: 0.75,
              px: 1.25,
              display: 'flex',
              alignItems: 'center',
              gap: 0.75,
              minHeight: 'unset',
            },
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(0, 102, 204, 0.3)',
              borderWidth: '1px',
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(0, 102, 204, 0.5)',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: '#0066cc',
              borderWidth: '1px',
            },
            '& .MuiSelect-icon': {
              color: '#6b7280',
              fontSize: '18px',
            },
            bgcolor: '#f8fafc',
            borderRadius: 1.25,
            transition: 'all 0.2s ease',
            '&:hover': {
              bgcolor: '#f1f5f9',
            },
          }}
          MenuProps={{
            PaperProps: {
              sx: {
                bgcolor: 'white',
                borderRadius: 1.5,
                mt: 0.25,
                maxHeight: '240px',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
                border: '1px solid #e2e8f0',
                '& .MuiMenuItem-root': {
                  py: 0.75,
                  px: 1.5,
                  fontSize: '13px',
                  fontWeight: 500,
                  minHeight: '36px',
                  color: '#1f2937',
                  transition: 'all 0.15s ease',
                  '&:hover': {
                    bgcolor: 'rgba(0, 102, 204, 0.08)',
                  },
                  '&.Mui-selected': {
                    bgcolor: 'rgba(0, 102, 204, 0.12)',
                    color: '#0066cc',
                    '&:hover': {
                      bgcolor: 'rgba(0, 102, 204, 0.16)',
                    },
                  },
                },
              },
            },
          }}
        >
          <MenuItem value="" disabled>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, opacity: 0.6 }}>
              <BusinessIcon sx={{ fontSize: '16px' }} />
              <Typography sx={{ fontSize: '13px' }}>Choose workspace</Typography>
            </Box>
          </MenuItem>
          {workspaces.map(workspace => (
            <MenuItem key={workspace.id} value={workspace.id}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                <BusinessIcon sx={{ fontSize: '16px', color: '#0066cc' }} />
                <Typography sx={{ flex: 1, fontSize: '13px' }}>{workspace.name}</Typography>
                {selectedWorkspace?.id === workspace.id && (
                  <CheckIcon sx={{ fontSize: '16px', color: '#10b981' }} />
                )}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {selectedWorkspace && (
        <Chip
          icon={<CheckIcon sx={{ fontSize: '12px' }} />}
          label={selectedWorkspace.name}
          size="small"
          sx={{
            mt: 1,
            bgcolor: 'rgba(16, 185, 129, 0.1)',
            color: '#065f46',
            fontSize: '10px',
            fontWeight: 500,
            height: 20,
            borderRadius: 0.75,
            border: '1px solid rgba(16, 185, 129, 0.3)',
            '& .MuiChip-icon': {
              color: '#10b981',
            },
            '& .MuiChip-label': {
              px: 0.75,
            },
          }}
        />
      )}


    </Box>
  );
};

export default WorkspaceSelector;
