import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = (import.meta as ImportMeta & { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL || 'http://localhost:8000';
const AUTH_STORAGE_KEY = 'applysense_auth';

interface AuthSession {
  access_token: string;
  refresh_token: string;
  user: Record<string, unknown> | null;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const readSession = (): AuthSession | null => {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const writeSession = (session: AuthSession | null) => {
  if (!session) {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return;
  }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
};

const clearSession = () => {
  localStorage.removeItem(AUTH_STORAGE_KEY);
};

const getAccessToken = () => readSession()?.access_token || null;

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let pendingRequests: Array<(token: string | null) => void> = [];

api.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        const session = readSession();
        if (!session?.refresh_token) {
          clearSession();
          window.location.assign('/login');
          return Promise.reject(error);
        }

        try {
          const refreshResponse = await axios.post(`${API_BASE_URL}/api/auth/refresh/`, {
            refresh: session.refresh_token,
          });
          const nextAccessToken = refreshResponse.data?.access;
          if (!nextAccessToken) {
            throw new Error('Refresh token did not return an access token');
          }
          const nextSession = {
            ...session,
            access_token: nextAccessToken,
          };
          writeSession(nextSession);
          pendingRequests.forEach((resolve) => resolve(nextAccessToken));
          pendingRequests = [];
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${nextAccessToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          clearSession();
          window.location.assign('/login');
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      return new Promise((resolve, reject) => {
        pendingRequests.push((token) => {
          if (!token) {
            reject(error);
            return;
          }
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${token}`;
          resolve(api(originalRequest));
        });
      });
    }

    return Promise.reject(error);
  }
);

export const authStorage = {
  read: readSession,
  write: writeSession,
  clear: clearSession,
  getAccessToken,
};

export const login = async (email: string, password: string) => {
  const { data } = await api.post('/api/auth/login/', { email, password });
  writeSession({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    user: data.user || null,
  });
  return data;
};

export const register = async (payload: Record<string, unknown>) => {
  const { data } = await api.post('/api/auth/register/', payload);
  writeSession({
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    user: data.user || null,
  });
  return data;
};

export const logout = async () => {
  const session = readSession();
  try {
    if (session?.refresh_token) {
      await api.post('/api/auth/logout/', { refresh_token: session.refresh_token });
    }
  } catch {
    // ignore logout errors and still clear local state
  } finally {
    clearSession();
    window.location.assign('/login');
  }
};

export const getCurrentUser = async () => {
  const { data } = await api.get('/api/auth/me/');
  return data;
};

// --- Automation (Auto Apply) API ---

export const getAutoApplyConfig = async () => {
  const { data } = await api.get('/api/automation/auto-apply/config/');
  return data;
};

export const updateAutoApplyConfig = async (config: any) => {
  const { data } = await api.put('/api/automation/auto-apply/config/', config);
  return data;
};

export const enableAutoApply = async () => {
  const { data } = await api.post('/api/automation/auto-apply/enable/');
  return data;
};

export const pauseAutoApply = async () => {
  const { data } = await api.post('/api/automation/auto-apply/pause/');
  return data;
};

export const getAutoApplyRuns = async () => {
  const { data } = await api.get('/api/automation/auto-apply/runs/');
  return data;
};

export const getUserActionRequired = async () => {
  const { data } = await api.get('/api/automation/auto-apply/action-required/');
  return data;
};

export const getAutomationHealth = async () => {
  const { data } = await api.get('/api/health/automation/');
  return data;
};

export default api;
