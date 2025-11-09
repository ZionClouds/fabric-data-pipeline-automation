import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  Typography,
  Button,
} from '@mui/material';
import { Microsoft } from '@mui/icons-material';
import logo from '../assets/images/zionai.png';

const Login = () => {
  const { login } = useAuth();

  const handleLogin = () => {
    login();
  };

  return (
    <Box 
      className="login-container"
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
        p: 2
      }}
    >
      <Box 
        className="login-card"
        sx={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          p: 3.5,
          borderRadius: 2.5,
          boxShadow: '0 15px 45px rgba(0,0,0,0.15)',
          textAlign: 'center',
          maxWidth: 380,
          width: '100%',
          border: '1px solid rgba(255,255,255,0.3)'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1.5 }}>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
              boxShadow: '0 8px 24px rgba(0, 123, 255, 0.25)',
              mr: 2,
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: '0 12px 32px rgba(0, 123, 255, 0.35)'
              }
            }}
          >
            <img 
              src={logo} 
              alt="Pipeline Builder Logo" 
              style={{ 
                width: '28px', 
                height: '28px',
                filter: 'brightness(0) invert(1)',
                transition: 'all 0.3s ease'
              }} 
            />
          </Box>
          <Typography 
            variant="h4" 
            component="h1"
            sx={{
              fontSize: '2rem',
              fontWeight: 700,
              background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              color: 'transparent',
              WebkitTextFillColor: 'transparent'
            }}
          >
            Pipeline Builder
          </Typography>
        </Box>
        
        <Typography 
          className="subtitle"
          variant="subtitle1"
          sx={{
            color: 'text.secondary',
            mb: 3,
            fontWeight: 400,
            fontSize: '0.95rem'
          }}
        >
          AI-Powered Data Pipelines for Microsoft Fabric
        </Typography>

        <Box 
          className="login-info"
          sx={{
            bgcolor: 'rgba(255, 255, 255, 0.7)',
            p: 2.5,
            borderRadius: 1.5,
            mb: 3,
            border: '1px solid rgba(103, 126, 234, 0.2)',
            textAlign: 'left'
          }}
        >
          <Typography 
            variant="body2" 
            sx={{ 
              mb: 1.5, 
              color: 'text.primary',
              lineHeight: 1.5,
              fontSize: '0.9rem',
              fontWeight: 400
            }}
          >
            ✨ Build intelligent data pipelines with AI-powered recommendations.
          </Typography>
          <Typography 
            variant="body2" 
            sx={{ 
              color: 'text.primary',
              lineHeight: 1.5,
              fontSize: '0.9rem',
              fontWeight: 400
            }}
          >
            🔐 Sign in with your Microsoft account to get started.
          </Typography>
        </Box>

        <Button
          onClick={handleLogin}
          className="btn-primary"
          variant="contained"
          size="medium"
          fullWidth
          startIcon={<Microsoft />}
          sx={{
            background: 'linear-gradient(135deg, hsl(210 100% 45%), hsl(175 70% 50%))',
            py: 1.5,
            borderRadius: 1.5,
            fontSize: '1rem',
            fontWeight: 600,
            textTransform: 'none',
            boxShadow: '0 6px 20px rgba(0, 123, 255, 0.3)',
            '&:hover': {
              background: 'linear-gradient(135deg, hsl(210 100% 40%), hsl(175 70% 45%))',
              boxShadow: '0 8px 28px rgba(0, 123, 255, 0.4)',
              transform: 'translateY(-1px)'
            },
            transition: 'all 0.3s ease'
          }}
        >
          Sign in with Microsoft
        </Button>
      </Box>
    </Box>
  );
};

export default Login;
