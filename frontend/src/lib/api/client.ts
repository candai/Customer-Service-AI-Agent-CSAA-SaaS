// src/lib/api/client.ts
import axios from 'axios';
import { config } from '@/lib/config';

export const apiClient = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Track if we're currently refreshing to avoid multiple refresh attempts
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
};

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        localStorage.clear();
        window.location.href = '/login';
        return Promise.reject(error);
      }
      
      if (!isRefreshing) {
        isRefreshing = true;
        
        try {
          const response = await axios.post(`${config.apiUrl}/auth/refresh`, {
            refresh: refreshToken,
          });
          const { access, refresh } = response.data;
          
          localStorage.setItem('access_token', access);
          if (refresh) {
            localStorage.setItem('refresh_token', refresh);
          }
          
          // Update token expiry
          const expiresAt = Date.now() + (2 * 60 * 60 * 1000);
          localStorage.setItem('token_expires_at', expiresAt.toString());
          
          isRefreshing = false;
          onTokenRefreshed(access);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient.request(originalRequest);
        } catch (refreshError) {
          isRefreshing = false;
          localStorage.clear();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
      
      // Wait for token refresh to complete
      return new Promise((resolve) => {
        subscribeTokenRefresh((token: string) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          resolve(apiClient.request(originalRequest));
        });
      });
    }
    
    return Promise.reject(error);
  }
);