import React, { createContext, useState, useContext, useEffect } from 'react';
import { PublicClientApplication } from '@azure/msal-browser';

const AuthContext = createContext();

// Dev mode: skip MSAL entirely when REACT_APP_DISABLE_AUTH is set
const DISABLE_AUTH = window._env_?.REACT_APP_DISABLE_AUTH || process.env.REACT_APP_DISABLE_AUTH || 'false';
const DEV_AUTH_ENABLED = DISABLE_AUTH === 'true' || DISABLE_AUTH === true;
const DEV_USER_EMAIL = window._env_?.REACT_APP_DEV_USER_EMAIL || process.env.REACT_APP_DEV_USER_EMAIL || 'dev123@gmail.com';

// MSAL Configuration (only used when auth is enabled)
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

// Only create MSAL instance if auth is enabled
const msalInstance = DEV_AUTH_ENABLED ? null : new PublicClientApplication(msalConfig);

// Module-level promise to prevent React StrictMode double-mount from calling
// handleRedirectPromise twice (which causes the second call to hang).
let msalInitPromise = null;

function getMsalInitResult() {
  if (!msalInstance) return Promise.resolve(null);
  if (!msalInitPromise) {
    msalInitPromise = (async () => {
      await msalInstance.initialize();
      const response = await msalInstance.handleRedirectPromise();
      return response;
    })();
  }
  return msalInitPromise;
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Dev mode: bypass MSAL, set hardcoded user immediately
    if (DEV_AUTH_ENABLED) {
      console.log(`[Auth] Dev mode enabled — using ${DEV_USER_EMAIL}`);
      setUser({
        email: DEV_USER_EMAIL,
        name: DEV_USER_EMAIL.split('@')[0],
      });
      setIsAuthenticated(true);
      localStorage.setItem('msal_token', 'dev-token');
      localStorage.setItem('user_email', DEV_USER_EMAIL);
      setIsLoading(false);
      return;
    }

    const initAuth = async () => {
      try {
        const response = await getMsalInitResult();

        if (response) {
          // Successful login
          handleLoginSuccess(response);
        } else {
          // Check if user is already logged in
          const accounts = msalInstance.getAllAccounts();
          const storedToken = localStorage.getItem('msal_token');
          const storedEmail = localStorage.getItem('user_email');

          if (accounts.length > 0 && storedToken && storedEmail) {
            const account = accounts[0];
            msalInstance.setActiveAccount(account);

            // Try to acquire token silently to validate the stored token
            try {
              const tokenResponse = await msalInstance.acquireTokenSilent({
                ...loginRequest,
                account: account,
              });
              handleLoginSuccess(tokenResponse);
            } catch (error) {
              console.error('Silent token acquisition failed:', error);
              // Token is invalid, clear everything
              localStorage.removeItem('msal_token');
              localStorage.removeItem('user_email');
              msalInstance.setActiveAccount(null);
              setIsAuthenticated(false);
              setUser(null);
            }
          } else {
            // No valid authentication found, ensure clean state
            localStorage.removeItem('msal_token');
            localStorage.removeItem('user_email');
            setIsAuthenticated(false);
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        // On any error, ensure clean state
        localStorage.removeItem('msal_token');
        localStorage.removeItem('user_email');
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    // Handle storage changes (e.g., logout from another tab or external clearing)
    const handleStorageChange = (e) => {
      // Be very conservative about storage-based logout
      // Only logout if this was clearly an intentional token removal
      if ((e.key === 'msal_token' || e.key === 'user_email') && e.newValue === null && e.oldValue) {
        // Double-check that both tokens are actually gone
        const token = localStorage.getItem('msal_token');
        const email = localStorage.getItem('user_email');

        if (!token && !email) {
          setUser(null);
          setIsAuthenticated(false);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    initAuth();

    // Cleanup
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
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
    if (DEV_AUTH_ENABLED) return; // No-op in dev mode
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
    if (DEV_AUTH_ENABLED) {
      // In dev mode, just reset state
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('msal_token');
      localStorage.removeItem('user_email');
      return;
    }

    try {
      // Update state immediately to show login screen
      setUser(null);
      setIsAuthenticated(false);

      // Clear local storage
      localStorage.removeItem('msal_token');
      localStorage.removeItem('user_email');

      // Clear MSAL cache and accounts
      const accounts = msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        // Clear all accounts from MSAL cache
        accounts.forEach(account => {
          msalInstance.removeAccount(account);
        });
        msalInstance.setActiveAccount(null);
      }

      // Clear the entire MSAL cache to ensure complete logout
      await msalInstance.clearCache();

      // Optional: Perform logout from Microsoft
      try {
        await msalInstance.logoutPopup({
          postLogoutRedirectUri: window.location.origin,
          mainWindowRedirectUri: window.location.origin
        });
      } catch (popupError) {
        // If popup is blocked or fails, we still maintain logged out state
        console.warn('Popup logout failed, but local logout completed:', popupError);
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Ensure state is updated even if logout fails
      setUser(null);
      setIsAuthenticated(false);

      // Force clear storage even on error
      localStorage.removeItem('msal_token');
      localStorage.removeItem('user_email');
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
