import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import api from '../lib/api';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check active sessions and sets the user
    const initializeAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        setSession(session);
        setUser(session.user);
        // Inject token for Axios
        window.__AIDFLOW_TOKEN__ = session.access_token;
      }
      setLoading(false);
    };

    initializeAuth();

    // Listen for changes on auth state
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      
      if (session?.access_token) {
        window.__AIDFLOW_TOKEN__ = session.access_token;
      } else {
        delete window.__AIDFLOW_TOKEN__;
      }
      
      setLoading(false);
    });

    // Listen for Axios 401s
    const handleUnauthorized = async () => {
      // Attempt to refresh or logout
      const { data, error } = await supabase.auth.refreshSession();
      if (error || !data.session) {
        await logout();
      }
    };
    
    window.addEventListener('aidflow:unauthorized', handleUnauthorized);

    return () => {
      subscription.unsubscribe();
      window.removeEventListener('aidflow:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    // We can call Supabase directly for login, which is safer/simpler than bouncing through our API for auth state sync
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    if (error) throw error;
    return data;
  };

  const register = async (email, password, fullName) => {
    // Proxy through our backend to ensure user profile is created Atomically
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName
    });
    
    // Also sign in via client to set local session
    if (response.data) {
        await supabase.auth.signInWithPassword({email, password});
    }
    
    return response.data;
  };

  const logout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    setUser(null);
    setSession(null);
    delete window.__AIDFLOW_TOKEN__;
  };

  const value = {
    user,
    session,
    loading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
