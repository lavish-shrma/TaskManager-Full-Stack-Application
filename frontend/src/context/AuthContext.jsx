import React, { createContext, useState, useEffect } from 'react';
import { authAPI } from '../api/endpoints';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkUser = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await authAPI.me();
          setUser(response.data);
        } catch (error) {
          localStorage.removeItem('access_token');
        }
      }
      setLoading(false);
    };

    checkUser();
  }, []);

  const login = async (email, password) => {
    const response = await authAPI.login({ email, password });
    localStorage.setItem('access_token', response.data.access_token);
    const userResponse = await authAPI.me();
    setUser(userResponse.data);
  };

  const signup = async (name, email, password) => {
    await authAPI.signup({ name, email, password });
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
