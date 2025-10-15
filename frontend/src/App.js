import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { PipelineProvider } from './contexts/PipelineContext';
import PipelineBuilderLayout from './components/PipelineBuilderLayout';
import Login from './components/Login';
import './styles/App.css';

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading Pipeline Builder...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return <PipelineBuilderLayout />;
}

function App() {
  return (
    <AuthProvider>
      <PipelineProvider>
        <AppContent />
      </PipelineProvider>
    </AuthProvider>
  );
}

export default App;
