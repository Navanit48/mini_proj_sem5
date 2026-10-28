import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import api from '../lib/api';

const AuthContext = createContext();

// Demo mode: enabled when Supabase credentials are placeholders
const DEMO_MODE = import.meta.env.VITE_SUPABASE_URL?.includes('placeholder') ||
                  import.meta.env.VITE_SUPABASE_URL?.includes('your-project-ref') ||
                  !import.meta.env.VITE_SUPABASE_URL;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If demo mode, check for a persisted demo session
    if (DEMO_MODE) {
      localStorage.removeItem('aidflow_demo_session');
      setLoading(false);
      return;
    }

    const applySession = async (activeSession) => {
      setSession(activeSession);
      if (!activeSession) {
        setUser(null);
        delete window.__AIDFLOW_TOKEN__;
        setLoading(false);
        return;
      }

      window.__AIDFLOW_TOKEN__ = activeSession.access_token;
      try {
        const { data } = await api.get('/auth/me');
        setUser({ ...activeSession.user, profile: data.profile, role: data.role });
      } catch {
        setUser(null);
        setTimeout(() => supabase.auth.signOut(), 0);
      } finally {
        setLoading(false);
      }
    };

    supabase.auth.getSession().then(({ data: { session } }) => applySession(session));

    // Listen for changes on auth state
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      applySession(session);
    });

    // Listen for Axios 401s
    const handleUnauthorized = async () => {
      // Attempt to refresh or logout
      const { data, error } = await supabase.auth.refreshSession();
      if (error || !data.session) {
        await supabase.auth.signOut({ scope: 'local' });
      }
    };
    
    window.addEventListener('aidflow:unauthorized', handleUnauthorized);

    return () => {
      subscription.unsubscribe();
      window.removeEventListener('aidflow:unauthorized', handleUnauthorized);
    };
  }, []);

  const login = async (email, password) => {
    if (DEMO_MODE) {
      throw new Error('Supabase is not configured');
    }

    const { data } = await api.post('/auth/login', {
      email,
      password,
    });
    const { data: sessionData, error } = await supabase.auth.setSession({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    });
    if (error) throw error;
    window.__AIDFLOW_TOKEN__ = sessionData.session.access_token;
    const { data: profileData } = await api.get('/auth/me');
    setSession(sessionData.session);
    setUser({ ...sessionData.user, profile: profileData.profile, role: profileData.role });
    return sessionData;
  };

  const register = async (email, password, fullName) => {
    if (DEMO_MODE) {
      throw new Error('Supabase is not configured');
    }

    const { data } = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName
    });
    if (!data.access_token || !data.refresh_token) {
      return { needsEmailConfirmation: true };
    }
    const { data: sessionData, error } = await supabase.auth.setSession({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
    });
    if (error) throw error;
    window.__AIDFLOW_TOKEN__ = sessionData.session.access_token;
    const { data: profileData } = await api.get('/auth/me');
    setSession(sessionData.session);
    setUser({ ...sessionData.user, profile: profileData.profile, role: profileData.role });
    return sessionData;
  };

  const logout = async () => {
    if (DEMO_MODE) {
      return;
    }

    try {
      await api.post('/auth/logout');
    } finally {
      await supabase.auth.signOut({ scope: 'local' });
    }
  };

  const value = {
    user,
    session,
    loading,
    login,
    register,
    logout,
    isDemoMode: DEMO_MODE,
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
