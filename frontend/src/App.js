import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Typography } from '@mui/material';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PipelineProvider } from './contexts/PipelineContext';
import PipelineBuilderLayout from './components/PipelineBuilderLayout';
import Login from './components/Login';
import './styles/App.css';

// Create Material UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2563eb',
      light: '#3b82f6',
      dark: '#1d4ed8',
    },
    secondary: {
      main: '#7c3aed',
      light: '#8b5cf6',
      dark: '#6d28d9',
    },
    background: {
      default: '#f8fafc',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", "Roboto", sans-serif',
    h1: {
      fontWeight: 700,
    },
    h2: {
      fontWeight: 700,
    },
    h3: {
      fontWeight: 600,
    },
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 12,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        },
      },
    },
  },
});

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <Box 
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2
        }}
      >
        <Box 
          sx={{
            textAlign: 'center',
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            p: 5,
            borderRadius: 3,
            boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
            border: '1px solid rgba(255,255,255,0.3)',
            maxWidth: 400,
            width: '100%'
          }}
        >
          <Box
            sx={{
              width: 80,
              height: 80,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 3,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 3,
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
              '@keyframes pulse': {
                '0%, 100%': {
                  opacity: 1,
                },
                '50%': {
                  opacity: 0.5,
                },
              },
            }}
          >
            <Typography sx={{ fontSize: '2.5rem' }}>🚀</Typography>
          </Box>
          <Typography 
            variant="h5" 
            sx={{ 
              color: 'text.primary',
              fontWeight: 600,
              mb: 1
            }}
          >
            Loading Pipeline Builder...
          </Typography>
          <Typography 
            variant="body1" 
            sx={{ 
              color: 'text.secondary',
              fontWeight: 400
            }}
          >
            Preparing your workspace
          </Typography>
        </Box>
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return <PipelineBuilderLayout />;
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <PipelineProvider>
          <AppContent />
        </PipelineProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
