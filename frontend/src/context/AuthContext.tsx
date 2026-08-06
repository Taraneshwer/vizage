import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  token: str | null;
  isAuthenticated: boolean;
  login: (token: str) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<str | null>(localStorage.getItem('vizage_token'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('vizage_token', token);
    } else {
      localStorage.removeItem('vizage_token');
    }
  }, [token]);

  const login = (newToken: str) => {
    setToken(newToken);
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        isAuthenticated: !!token,
        login,
        logout,
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
