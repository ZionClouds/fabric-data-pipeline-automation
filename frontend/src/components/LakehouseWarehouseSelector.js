import React, { useState, useEffect } from 'react';
import { usePipeline } from '../contexts/PipelineContext';
import axios from 'axios';
import {
  Box,
  Typography,
  FormControl,
  Select,
  MenuItem,
  CircularProgress,
  Chip
} from '@mui/material';
import { Storage as StorageIcon, Warehouse as WarehouseIcon, CheckCircle as CheckIcon } from '@mui/icons-material';

// API URL from env config (supports Docker runtime injection)
const API_BASE_URL = window._env_?.REACT_APP_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8000';

const LakehouseWarehouseSelector = () => {
  const {
    selectedWorkspace,
    selectedLakehouse,
    setSelectedLakehouse,
    selectedWarehouse,
    setSelectedWarehouse
  } = usePipeline();

  const [lakehouses, setLakehouses] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch lakehouses and warehouses when workspace changes
  useEffect(() => {
    if (selectedWorkspace?.id) {
      fetchLakehousesAndWarehouses();
    } else {
      // Reset when no workspace selected
      setLakehouses([]);
      setWarehouses([]);
      setSelectedLakehouse(null);
      setSelectedWarehouse(null);
    }
  }, [selectedWorkspace]);

  const fetchLakehousesAndWarehouses = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('authToken');
      const config = {
        headers: { Authorization: `Bearer ${token}` }
      };

      // Fetch lakehouses
      const lakehousesRes = await axios.get(
        `${API_BASE_URL}/api/workspaces/${selectedWorkspace.id}/lakehouses`,
        config
      );
      setLakehouses(lakehousesRes.data || []);

      // Fetch warehouses
      const warehousesRes = await axios.get(
        `${API_BASE_URL}/api/workspaces/${selectedWorkspace.id}/warehouses`,
        config
      );
      setWarehouses(warehousesRes.data || []);

      // Auto-select if only one option available
      if (lakehousesRes.data?.length === 1) {
        setSelectedLakehouse(lakehousesRes.data[0]);
      }
      if (warehousesRes.data?.length === 1) {
        setSelectedWarehouse(warehousesRes.data[0]);
      }
    } catch (error) {
      console.error('Error fetching lakehouses/warehouses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLakehouseSelect = (event) => {
    const lakehouse = lakehouses.find(lh => lh.id === event.target.value);
    setSelectedLakehouse(lakehouse);
  };

  const handleWarehouseSelect = (event) => {
    const warehouse = warehouses.find(wh => wh.id === event.target.value);
    setSelectedWarehouse(warehouse);
  };

  if (!selectedWorkspace) {
    return null;
  }

  if (loading) {
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
          Loading lakehouses and warehouses...
        </Typography>
      </Box>
    );
  }

  const selectStyles = {
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
  };

  const menuProps = {
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
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, width: '100%' }}>
      {/* Lakehouse Selector */}
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
          Lakehouse
        </Typography>

        <FormControl fullWidth size="small">
          <Select
            value={selectedLakehouse?.id || ''}
            onChange={handleLakehouseSelect}
            displayEmpty
            sx={selectStyles}
            MenuProps={menuProps}
          >
            <MenuItem value="" disabled>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, opacity: 0.6 }}>
                <StorageIcon sx={{ fontSize: '16px' }} />
                <Typography sx={{ fontSize: '13px' }}>Choose lakehouse</Typography>
              </Box>
            </MenuItem>
            {lakehouses.map(lakehouse => (
              <MenuItem key={lakehouse.id} value={lakehouse.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  <StorageIcon sx={{ fontSize: '16px', color: '#667eea' }} />
                  <Typography sx={{ flex: 1, fontSize: '13px' }}>{lakehouse.name}</Typography>
                  {selectedLakehouse?.id === lakehouse.id && (
                    <CheckIcon sx={{ fontSize: '16px', color: '#10b981' }} />
                  )}
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {selectedLakehouse && (
          <Chip
            icon={<CheckIcon sx={{ fontSize: '12px' }} />}
            label={selectedLakehouse.name}
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
      </Box>

      {/* Warehouse Selector */}
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
          Warehouse
        </Typography>

        <FormControl fullWidth size="small">
          <Select
            value={selectedWarehouse?.id || ''}
            onChange={handleWarehouseSelect}
            displayEmpty
            sx={selectStyles}
            MenuProps={menuProps}
          >
            <MenuItem value="" disabled>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, opacity: 0.6 }}>
                <WarehouseIcon sx={{ fontSize: '16px' }} />
                <Typography sx={{ fontSize: '13px' }}>Choose warehouse</Typography>
              </Box>
            </MenuItem>
            {warehouses.map(warehouse => (
              <MenuItem key={warehouse.id} value={warehouse.id}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  <WarehouseIcon sx={{ fontSize: '16px', color: '#667eea' }} />
                  <Typography sx={{ flex: 1, fontSize: '13px' }}>{warehouse.name}</Typography>
                  {selectedWarehouse?.id === warehouse.id && (
                    <CheckIcon sx={{ fontSize: '16px', color: '#10b981' }} />
                  )}
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {selectedWarehouse && (
          <Chip
            icon={<CheckIcon sx={{ fontSize: '12px' }} />}
            label={selectedWarehouse.name}
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
      </Box>
    </Box>
  );
};

export default LakehouseWarehouseSelector;
