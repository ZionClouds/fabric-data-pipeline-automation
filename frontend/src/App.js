import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Typography } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PipelineProvider } from './contexts/PipelineContext';
import PipelineBuilderLayout from './components/PipelineBuilderLayout';
import Login from './components/Login';
import './styles/App.css';

// Microsoft Fabric-aligned MUI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#0078D4',
      light: '#2B88D8',
      dark: '#005A9E',
    },
    secondary: {
      main: '#8764B8',
      light: '#9C7FCE',
      dark: '#6B4F96',
    },
    background: {
      default: '#F3F2F1',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#323130',
      secondary: '#605E5C',
    },
    divider: '#EDEBE9',
    error: { main: '#D13438' },
    success: { main: '#107C10' },
    warning: { main: '#FFB900' },
  },
  typography: {
    fontFamily: '"Segoe UI", "Inter", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 6,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: '0 2px 4px rgba(0,0,0,0.08), 0 0 2px rgba(0,0,0,0.06)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
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
          background: '#1B1B1F',
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box sx={{ textAlign: 'center' }}>
            <motion.div
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
            >
              <Box
                sx={{
                  width: 64,
                  height: 64,
                  background: '#0078D4',
                  borderRadius: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 3,
                  boxShadow: '0 8px 32px rgba(0,120,212,0.3)',
                }}
              >
                <Typography sx={{ fontSize: '1.8rem' }}>⚡</Typography>
              </Box>
            </motion.div>
            <Typography variant="h6" sx={{ color: '#E8E6E3', fontWeight: 600, mb: 0.5 }}>
              Pipeline Builder
            </Typography>
            <Typography variant="body2" sx={{ color: '#A19F9D' }}>
              Preparing your workspace...
            </Typography>
          </Box>
        </motion.div>
      </Box>
    );
  }

  return (
    <AnimatePresence mode="wait">
      {!isAuthenticated ? (
        <motion.div
          key="login"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          transition={{ duration: 0.3 }}
        >
          <Login />
        </motion.div>
      ) : (
        <motion.div
          key="app"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          style={{ height: '100vh' }}
        >
          <PipelineBuilderLayout />
        </motion.div>
      )}
    </AnimatePresence>
  );
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
