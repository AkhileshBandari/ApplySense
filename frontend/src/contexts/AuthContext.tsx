import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { authStorage, getCurrentUser, login as loginRequest, logout as logoutRequest, register as registerRequest } from '../services/api';

interface AuthUser {
  id?: number;
  email?: string;
  username?: string;
  role?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: Record<string, unknown>) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initialize = async () => {
      const session = authStorage.read();
      if (!session?.access_token) {
        setLoading(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser || null);
      } catch (err) {
        console.error('Auth check failed:', err);
        authStorage.clear();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await loginRequest(email, password);
    setUser(data.user || null);
  };

  const register = async (payload: Record<string, unknown>) => {
    const data = await registerRequest(payload);
    setUser(data.user || null);
  };

  const logout = async () => {
    await logoutRequest();
    setUser(null);
  };

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isAuthenticated: Boolean(user),
    loading,
    login,
    register,
    logout,
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
