'use client'

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthResponse, LoginCredentials, AuthContextType } from '@/types/auth';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing auth on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');
    const tokenExpiry = localStorage.getItem('token_expiry');

    if (storedToken && storedUser && tokenExpiry) {
      const now = Date.now();
      const expiry = parseInt(tokenExpiry);

      if (now < expiry) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } else {
        // Token expired, clear storage
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('token_expiry');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const data: AuthResponse = await response.json();
      
      // Calculate expiry time (current time + expires_in seconds * 1000 for milliseconds)
      const expiryTime = Date.now() + (data.expires_in * 1000);

      // Store in localStorage
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      localStorage.setItem('token_expiry', expiryTime.toString());

      // Update state
      setToken(data.token);
      setUser(data.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    localStorage.removeItem('token_expiry');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user && !!token,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
