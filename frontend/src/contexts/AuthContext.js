import React, { createContext, useState, useContext, useEffect } from 'react';
import { PublicClientApplication } from '@azure/msal-browser';

const AuthContext = createContext();

// MSAL Configuration
const msalConfig = {
  auth: {
    clientId: '0944e22d-d0f1-40c1-a9fc-f422c05949f3',
    authority: 'https://login.microsoftonline.com/e28d23e3-803d-418d-a720-c0bed39f77b6',
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};

const loginRequest = {
  scopes: ['User.Read'],
};

const msalInstance = new PublicClientApplication(msalConfig);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        await msalInstance.initialize();

        // Handle redirect response
        const response = await msalInstance.handleRedirectPromise();

        if (response) {
          // Successful login
          handleLoginSuccess(response);
        } else {
          // Check if user is already logged in
          const accounts = msalInstance.getAllAccounts();
          if (accounts.length > 0) {
            const account = accounts[0];
            msalInstance.setActiveAccount(account);

            // Try to acquire token silently
            try {
              const tokenResponse = await msalInstance.acquireTokenSilent({
                ...loginRequest,
                account: account,
              });
              handleLoginSuccess(tokenResponse);
            } catch (error) {
              console.error('Silent token acquisition failed:', error);
              setIsAuthenticated(false);
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const handleLoginSuccess = (response) => {
    const account = response.account;
    const token = response.accessToken;

    // Store token and user info
    localStorage.setItem('msal_token', token);
    localStorage.setItem('user_email', account.username);

    setUser({
      email: account.username,
      name: account.name || account.username.split('@')[0],
    });
    setIsAuthenticated(true);
  };

  const login = async () => {
    try {
      setIsLoading(true);
      await msalInstance.loginRedirect(loginRequest);
    } catch (error) {
      console.error('Login error:', error);
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => {
    try {
      localStorage.removeItem('msal_token');
      localStorage.removeItem('user_email');

      await msalInstance.logoutRedirect({
        postLogoutRedirectUri: window.location.origin,
      });

      setUser(null);
      setIsAuthenticated(false);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export default AuthContext;
