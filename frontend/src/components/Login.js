import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import '../styles/Login.css';

const Login = () => {
  const { login } = useAuth();

  const handleLogin = () => {
    login();
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>🚀 Pipeline Builder</h1>
        <p className="subtitle">AI-Powered Data Pipelines for Microsoft Fabric</p>

        <div className="login-info">
          <p>Build intelligent data pipelines with AI-powered recommendations.</p>
          <p>Sign in with your Microsoft account to get started.</p>
        </div>

        <button
          onClick={handleLogin}
          className="btn-primary"
        >
          Sign in with Microsoft
        </button>
      </div>
    </div>
  );
};

export default Login;
