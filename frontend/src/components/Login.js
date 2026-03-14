import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { motion } from 'framer-motion';
import {
  Box,
  Typography,
  Button,
} from '@mui/material';
import { Microsoft } from '@mui/icons-material';
import logo from '../assets/images/zionai.png';

const Login = () => {
  const { login } = useAuth();

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#1B1B1F',
        p: 2,
        position: 'relative',
        overflow: 'hidden',
        // Subtle grid pattern
        '&::before': {
          content: '""',
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0)',
          backgroundSize: '40px 40px',
        },
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
      >
        <Box
          sx={{
            background: '#FFFFFF',
            p: 4,
            borderRadius: '12px',
            boxShadow: '0 16px 48px rgba(0,0,0,0.3)',
            textAlign: 'center',
            maxWidth: 380,
            width: '100%',
            position: 'relative',
            zIndex: 1,
          }}
        >
          {/* Logo */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1.5, gap: 1.5 }}>
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  borderRadius: '12px',
                  background: '#0078D4',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(0,120,212,0.3)',
                }}
              >
                <img
                  src={logo}
                  alt="Logo"
                  style={{ width: 24, height: 24, filter: 'brightness(0) invert(1)' }}
                />
              </Box>
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  color: '#323130',
                  letterSpacing: '-0.02em',
                }}
              >
                Pipeline Builder
              </Typography>
            </Box>
          </motion.div>

          <Typography
            variant="body2"
            sx={{ color: '#605E5C', mb: 3, fontWeight: 400, fontSize: '14px' }}
          >
            AI-Powered Data Pipelines for Microsoft Fabric
          </Typography>

          {/* Features */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.4 }}
          >
            <Box
              sx={{
                bgcolor: '#FAFAF9',
                p: 2,
                borderRadius: '8px',
                mb: 3,
                border: '1px solid #EDEBE9',
                textAlign: 'left',
              }}
            >
              <Typography variant="body2" sx={{ mb: 1, color: '#323130', fontSize: '13px', lineHeight: 1.6 }}>
                Build intelligent data pipelines with AI-powered recommendations.
              </Typography>
              <Typography variant="body2" sx={{ color: '#605E5C', fontSize: '13px', lineHeight: 1.6 }}>
                Sign in with your Microsoft account to get started.
              </Typography>
            </Box>
          </motion.div>

          {/* Sign In Button */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.3 }}
          >
            <Button
              onClick={login}
              variant="contained"
              size="large"
              fullWidth
              startIcon={<Microsoft />}
              sx={{
                background: '#0078D4',
                py: 1.5,
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 600,
                textTransform: 'none',
                boxShadow: '0 2px 8px rgba(0,120,212,0.3)',
                '&:hover': {
                  background: '#005A9E',
                  boxShadow: '0 4px 16px rgba(0,120,212,0.4)',
                },
                transition: 'all 0.2s',
              }}
            >
              Sign in with Microsoft
            </Button>
          </motion.div>
        </Box>
      </motion.div>
    </Box>
  );
};

export default Login;
