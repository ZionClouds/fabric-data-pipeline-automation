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
        borderRadius: 2,
        bgcolor: 'rgba(255, 255, 255, 0.1)',
      }}>
        <CircularProgress 
          size={16} 
          sx={{ color: 'rgba(255, 255, 255, 0.7)' }} 
        />
        <Typography 
          variant="body2" 
          sx={{ 
            color: 'rgba(255, 255, 255, 0.8)',
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
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '11px',
          fontWeight: 500,
          mb: 1,
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
            color: 'white',
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
              borderColor: 'rgba(255, 255, 255, 0.2)',
              borderWidth: '1px',
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(255, 255, 255, 0.4)',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: 'rgba(255, 255, 255, 0.6)',
              borderWidth: '1px',
            },
            '& .MuiSelect-icon': {
              color: 'rgba(255, 255, 255, 0.7)',
              fontSize: '18px',
            },
            bgcolor: 'rgba(255, 255, 255, 0.08)',
            borderRadius: 1.25,
            transition: 'all 0.2s ease',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.12)',
            },
          }}
          MenuProps={{
            PaperProps: {
              sx: {
                bgcolor: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(20px)',
                borderRadius: 1.5,
                mt: 0.25,
                maxHeight: '240px',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                '& .MuiMenuItem-root': {
                  py: 0.75,
                  px: 1.5,
                  fontSize: '13px',
                  fontWeight: 500,
                  minHeight: '36px',
                  transition: 'all 0.15s ease',
                  '&:hover': {
                    bgcolor: 'rgba(102, 126, 234, 0.08)',
                  },
                  '&.Mui-selected': {
                    bgcolor: 'rgba(102, 126, 234, 0.12)',
                    color: '#4f46e5',
                    '&:hover': {
                      bgcolor: 'rgba(102, 126, 234, 0.16)',
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
                <BusinessIcon sx={{ fontSize: '16px', color: '#667eea' }} />
                <Typography sx={{ flex: 1, fontSize: '13px' }}>{workspace.name}</Typography>
                {selectedWorkspace?.id === workspace.id && (
                  <CheckIcon sx={{ fontSize: '16px', color: '#10b981' }} />
                )}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Show success chip when workspace is selected */}
      {selectedWorkspace && (
        <Chip
          icon={<CheckIcon sx={{ fontSize: '12px' }} />}
          label={selectedWorkspace.name}
          size="small"
          sx={{
            mt: 1,
            bgcolor: 'rgba(16, 185, 129, 0.15)',
            color: 'rgba(255, 255, 255, 0.9)',
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

      {/* Show alert when no workspace is selected */}
      {!selectedWorkspace && workspaces.length > 0 && (
        <Alert
          severity="info"
          icon={<InfoIcon sx={{ fontSize: '14px' }} />}
          sx={{
            mt: 1,
            py: 0.5,
            px: 1,
            bgcolor: 'rgba(255, 193, 7, 0.15)',
            color: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid rgba(255, 193, 7, 0.4)',
            borderRadius: 1,
            fontSize: '11px',
            alignItems: 'center',
            '& .MuiAlert-icon': {
              color: '#ffc107',
              mr: 0.75,
              py: 0,
            },
            '& .MuiAlert-message': {
              py: 0,
              fontSize: '11px',
              fontWeight: 500,
            },
            animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            '@keyframes pulse': {
              '0%, 100%': {
                opacity: 1,
              },
              '50%': {
                opacity: 0.7,
              },
            },
          }}
        >
          Select to start building
        </Alert>
      )}
    </Box>
  );
};

export default WorkspaceSelector;
