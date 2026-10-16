import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import api from '../lib/api';

const AuthContext = createContext();

// Demo mode: enabled when Supabase credentials are placeholders
const DEMO_MODE = import.meta.env.VITE_SUPABASE_URL?.includes('placeholder') ||
                  import.meta.env.VITE_SUPABASE_URL?.includes('your-project-ref') ||
                  !import.meta.env.VITE_SUPABASE_URL;

const DEMO_USER = {
  id: 'demo-user-001',
  email: 'navanit@aidflow.dev',
  user_metadata: {
    full_name: 'Navanit Sharma',
  },
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If demo mode, check for a persisted demo session
    if (DEMO_MODE) {
      const demoSession = localStorage.getItem('aidflow_demo_session');
      if (demoSession) {
        setUser(DEMO_USER);
        setSession({ user: DEMO_USER, access_token: 'demo-token' });
      }
      setLoading(false);
      return;
    }

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
    // Demo mode: accept any credentials
    if (DEMO_MODE) {
      const demoUser = {
        ...DEMO_USER,
        email: email || DEMO_USER.email,
        user_metadata: {
          full_name: email?.split('@')[0]
            ? email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1)
            : DEMO_USER.user_metadata.full_name,
        },
      };
      setUser(demoUser);
      setSession({ user: demoUser, access_token: 'demo-token' });
      localStorage.setItem('aidflow_demo_session', 'true');
      return { user: demoUser };
    }

    // Real Supabase auth
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    if (error) throw error;
    return data;
  };

  const register = async (email, password, fullName) => {
    // Demo mode: treat register same as login
    if (DEMO_MODE) {
      const demoUser = {
        ...DEMO_USER,
        email,
        user_metadata: { full_name: fullName || 'Demo User' },
      };
      setUser(demoUser);
      setSession({ user: demoUser, access_token: 'demo-token' });
      localStorage.setItem('aidflow_demo_session', 'true');
      return { user: demoUser };
    }

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
    if (DEMO_MODE) {
      setUser(null);
      setSession(null);
      localStorage.removeItem('aidflow_demo_session');
      return;
    }

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
