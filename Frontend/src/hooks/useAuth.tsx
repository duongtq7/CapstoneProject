import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authAPI, usersAPI } from '../lib/api';
import { useNavigate } from 'react-router-dom';

interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const userData = await authAPI.testToken();
          setUser(userData);
        } catch (error) {
          console.error('Token validation failed:', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const response = await authAPI.login(email, password);
      if (response && response.access_token) {
        localStorage.setItem('token', response.access_token);
        const userData = await authAPI.testToken();
        setUser(userData);
        navigate('/');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    setLoading(true);
    try {
      console.log('Starting registration process with:', { email, hasFullName: !!fullName });
      
      const userData = {
        email,
        password,
        full_name: fullName || null,
      };
      
      console.log('Calling usersAPI.register with data:', { email, hasPassword: !!password, hasFullName: !!fullName });
      await usersAPI.register(userData);
      
      console.log('Registration successful, redirecting to login page');
      navigate('/login');
    } catch (error: any) {
      console.error('Registration error in useAuth:', error);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
        console.error('Response data:', error.response.data);
      }
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 