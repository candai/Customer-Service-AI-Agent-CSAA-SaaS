// src/lib/stores/auth.store.ts
import { create } from 'zustand';
import { User } from '@/types';
import { apiClient } from '@/lib/api/client';
import { wsService } from '@/lib/websocket';
import axios from 'axios';
import { config } from '@/lib/config'

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshTimer: NodeJS.Timeout | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  refreshToken: () => Promise<void>;
  scheduleTokenRefresh: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  refreshTimer: null,

  login: async (email: string, password: string) => {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { access, refresh, user_id, organization_id, role, name } = response.data;
      
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      
      // Store token expiry (2 hours from now based on backend settings)
      const expiresAt = Date.now() + (2 * 60 * 60 * 1000);
      localStorage.setItem('token_expires_at', expiresAt.toString());
      
      const user: User = {
        id: user_id,
        email,
        name: name || email,
        role,
        organization_id,
      };
      
      set({ user, token: access, isAuthenticated: true });
      
      // Schedule token refresh
      get().scheduleTokenRefresh();
      
      try {
        // Connect WebSocket
        wsService.connect(access);
      } catch (wsError) {
        console.error('WebSocket connection failed:', wsError);
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },

  logout: () => {
    // Clear refresh timer
    try {
      const { refreshTimer } = get();
      if (refreshTimer) {
        clearTimeout(refreshTimer);
      }
      
      localStorage.clear();
      wsService.disconnect();
      set({ user: null, token: null, isAuthenticated: false, refreshTimer: null });
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!token || !refreshToken) {
      set({ isLoading: false });
      return;
    }

    try {
      // Check if token needs refresh
      const expiresAt = localStorage.getItem('token_expires_at');
      const needsRefresh = expiresAt && Date.now() >= parseInt(expiresAt) - (5 * 60 * 1000);
      
      if (needsRefresh) {
        await get().refreshToken();
      }
      
      const response = await apiClient.get('/auth/me');
      set({ 
        user: response.data, 
        token, 
        isAuthenticated: true,
        isLoading: false
      });
      
      // Schedule token refresh
      get().scheduleTokenRefresh();
      
      // Connect WebSocket
      wsService.connect(token);
    } catch {
      // Try to refresh token before giving up
      try {
        await get().refreshToken();
        const response = await apiClient.get('/auth/me');
        set({ 
          user: response.data, 
          token: localStorage.getItem('access_token'), 
          isAuthenticated: true,
          isLoading: false 
        });
        wsService.connect(localStorage.getItem('access_token')!);
      } catch {
        localStorage.clear();
        set({ isLoading: false });
      }
    }
  },
  
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token');
    }
    
    try {
      const response = await axios.post(`${config.apiUrl}/auth/refresh`, {
        refresh: refreshToken,
      });
      
      const { access, refresh } = response.data;
      
      // Update tokens
      localStorage.setItem('access_token', access);
      if (refresh) {
        localStorage.setItem('refresh_token', refresh);
      }
      
      // Update expiry time
      const expiresAt = Date.now() + (2 * 60 * 60 * 1000);
      localStorage.setItem('token_expires_at', expiresAt.toString());
      
      set({ token: access });
      
      // Reconnect WebSocket with new token
      wsService.disconnect();
      wsService.connect(access);
      
      // Schedule next refresh
      get().scheduleTokenRefresh();
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    }
  },
  
  scheduleTokenRefresh: () => {
    const { refreshTimer } = get();
    
    // Clear existing timer
    if (refreshTimer) {
      clearTimeout(refreshTimer);
    }
    
    // Schedule refresh 5 minutes before expiry
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return;
    
    const timeUntilRefresh = parseInt(expiresAt) - Date.now() - (5 * 60 * 1000);
    
    if (timeUntilRefresh > 0) {
      const timer = setTimeout(() => {
        get().refreshToken().catch(() => {
          get().logout();
        });
      }, timeUntilRefresh);
      
      set({ refreshTimer: timer });
    } else {
      // Token needs immediate refresh
      get().refreshToken().catch(() => {
        get().logout();
      });
    }
  },
}));

// Handle page visibility changes to refresh token when returning to tab
if (typeof window !== 'undefined') {
  document.addEventListener('visibilitychange', async () => {
    if (!document.hidden && useAuthStore.getState().isAuthenticated) {
      const expiresAt = localStorage.getItem('token_expires_at');
      
      // Check if token expired while tab was inactive
      if (expiresAt && Date.now() >= parseInt(expiresAt)) {
        // Token expired, need to refresh or re-login
        try {
          await useAuthStore.getState().refreshToken();
        } catch {
          // Refresh failed, redirect to login
          useAuthStore.getState().logout();
        }
      } else if (expiresAt && Date.now() >= parseInt(expiresAt) - (5 * 60 * 1000)) {
        // Token expiring soon, refresh it
        await useAuthStore.getState().refreshToken();
      }
    }
  });

  // Sync token changes across tabs
  window.addEventListener('storage', (e) => {
    if (e.key === 'access_token') {
      if (!e.newValue) {
        // Token was cleared in another tab
        const state = useAuthStore.getState();
        if (state.refreshTimer) {
          clearTimeout(state.refreshTimer);
        }
        useAuthStore.setState({ 
          user: null,
          token: null,
          isAuthenticated: false,
          refreshTimer: null
        });
        window.location.href = '/login';
      } else if (e.newValue && e.newValue !== useAuthStore.getState().token) {
        // Token was refreshed in another tab
        useAuthStore.setState({ token: e.newValue });
        // Reconnect WebSocket with new token
        wsService.disconnect();
        wsService.connect(e.newValue);
      }
    }
  });
}

