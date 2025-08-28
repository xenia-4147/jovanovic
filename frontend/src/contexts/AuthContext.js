import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    initializeAuth();
    
    // Listen for auth expiration events from API interceptors
    const handleAuthExpired = () => {
      setUser(null);
      setIsAuthenticated(false);
    };
    
    window.addEventListener('auth-expired', handleAuthExpired);
    
    return () => {
      window.removeEventListener('auth-expired', handleAuthExpired);
    };
  }, []);

  const initializeAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');
      
      if (token && storedUser) {
        try {
          // Try to validate token with backend
          const userData = await authApi.getProfile();
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          // If token validation fails, try to use stored user data
          console.warn('Token validation failed, using stored user data');
          try {
            const parsedUser = JSON.parse(storedUser);
            setUser(parsedUser);
            setIsAuthenticated(true);
          } catch (parseError) {
            console.error('Failed to parse stored user data:', parseError);
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
          }
        }
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      const response = await authApi.register(userData);
      
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      
      setUser(response.user);
      setIsAuthenticated(true);
      
      return { success: true, user: response.user };
    } catch (error) {
      console.error('Registration failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const login = async (credentials) => {
    try {
      const response = await authApi.login(credentials);
      
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      
      setUser(response.user);
      setIsAuthenticated(true);
      
      return { success: true, user: response.user };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  const updateProfile = async (profileData) => {
    try {
      const updatedUser = await authApi.updateProfile(profileData);
      setUser(updatedUser);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return { success: true, user: updatedUser };
    } catch (error) {
      console.error('Profile update failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Profile update failed' 
      };
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    register,
    login,
    logout,
    updateProfile
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;