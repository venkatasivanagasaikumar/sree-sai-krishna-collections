import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (credentials: any) => Promise<any>;
  register: (data: any) => Promise<any>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('ssk_access_token'));
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      if (localStorage.getItem('ssk_access_token')) {
        const profile = await api.getProfile();
        setUser(profile);
      }
    } catch (err) {
      console.warn('Session expired or invalid, logging out:', err);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const login = async (credentials: any) => {
    const res = await api.login(credentials);
    localStorage.setItem('ssk_access_token', res.access_token);
    localStorage.setItem('ssk_refresh_token', res.refresh_token);
    setToken(res.access_token);
    setUser(res.user);
    return res;
  };

  const register = async (data: any) => {
    const res = await api.register(data);
    localStorage.setItem('ssk_access_token', res.access_token);
    localStorage.setItem('ssk_refresh_token', res.refresh_token);
    setToken(res.access_token);
    setUser(res.user);
    return res;
  };

  const logout = () => {
    localStorage.removeItem('ssk_access_token');
    localStorage.removeItem('ssk_refresh_token');
    setToken(null);
    setUser(null);
  };

  const refreshProfile = async () => {
    await fetchProfile();
  };

  const isAdmin = !!(user && ['Super Admin', 'Admin', 'Order Manager', 'Inventory Manager', 'Customer Support'].includes(user.role));

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        isAdmin,
        login,
        register,
        logout,
        refreshProfile
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
