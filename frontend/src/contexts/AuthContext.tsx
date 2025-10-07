// FRONTEND ONLY: Mock authentication context for demonstration purposes
// Replace with real authentication (e.g., Supabase, Auth0) in production

import React, { createContext, useContext, useState, useEffect } from 'react';

type UserRole = 'user' | 'admin' | null;

interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  login: (email: string, password: string, role?: UserRole) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load mock session from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('mockUser');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string, role: UserRole = 'user') => {
    // FRONTEND ONLY: Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Mock user creation
    const mockUser: AuthUser = {
      id: Math.random().toString(36).substr(2, 9),
      email,
      name: email.split('@')[0],
      role,
    };
    
    setUser(mockUser);
    localStorage.setItem('mockUser', JSON.stringify(mockUser));
  };

  const signup = async (name: string, email: string, password: string) => {
    // FRONTEND ONLY: Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const mockUser: AuthUser = {
      id: Math.random().toString(36).substr(2, 9),
      email,
      name,
      role: 'user',
    };
    
    setUser(mockUser);
    localStorage.setItem('mockUser', JSON.stringify(mockUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('mockUser');
  };

  const value = {
    user,
    isLoading,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
