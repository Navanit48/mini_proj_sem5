import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { Loader2, AlertCircle, Sparkles, Info } from 'lucide-react';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login, isDemoMode } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Failed to login');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsSubmitting(true);
    try {
      await login('navanit@aidflow.dev', 'demo');
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Failed to login');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background accents */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/5 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="sm:mx-auto sm:w-full sm:max-w-md relative z-10"
      >
        <div className="flex justify-center mb-6">
          <Link to="/" className="flex items-center gap-2.5 font-bold text-2xl text-foreground">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white shadow-lg shadow-primary/20">
              <Sparkles className="w-5 h-5" />
            </div>
            AidFlow AI
          </Link>
        </div>
        <h2 className="text-center text-2xl font-bold text-foreground tracking-tight">
          Welcome back
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          Or{' '}
          <Link to="/register" className="font-medium text-primary hover:text-primary/80 transition-colors">
            create a new account
          </Link>
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="mt-8 sm:mx-auto sm:w-full sm:max-w-md relative z-10"
      >
        <div className="bg-card py-8 px-4 shadow-xl shadow-black/10 sm:rounded-2xl sm:px-10 border border-border/50">
          
          {/* Demo mode banner */}
          {isDemoMode && (
            <div className="mb-5 bg-primary/8 border border-primary/15 text-primary px-4 py-3 rounded-xl flex items-start gap-3 text-sm">
              <Info className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="text-xs leading-relaxed">
                <strong>Demo Mode</strong> — Supabase not configured. Enter any email and password, or use the demo button below.
              </span>
            </div>
          )}

          {error && (
            <div className="mb-4 bg-red-500/8 border border-red-500/15 text-red-400 px-4 py-3 rounded-xl flex items-start gap-3 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Email address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none block w-full px-3.5 py-2.5 bg-secondary/50 border border-border/50 rounded-xl shadow-sm placeholder-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all text-sm text-foreground"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none block w-full px-3.5 py-2.5 bg-secondary/50 border border-border/50 rounded-xl shadow-sm placeholder-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all text-sm text-foreground"
                placeholder="••••••••"
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 rounded border-border bg-secondary text-primary focus:ring-primary/25"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-muted-foreground">
                  Remember me
                </label>
              </div>
              <a href="#" className="text-sm font-medium text-primary hover:text-primary/80 transition-colors">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center items-center gap-2 py-2.5 px-4 rounded-xl shadow-sm text-sm font-semibold text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-card focus:ring-primary transition-all disabled:opacity-70"
            >
              {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Log in'}
            </button>
          </form>

          {/* Demo login shortcut */}
          {isDemoMode && (
            <div className="mt-4 pt-4 border-t border-border/30">
              <button
                onClick={handleDemoLogin}
                disabled={isSubmitting}
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 rounded-xl text-sm font-medium text-muted-foreground bg-secondary/50 border border-border/40 hover:bg-secondary hover:text-foreground transition-all disabled:opacity-70"
              >
                <Sparkles className="w-4 h-4" />
                Continue as Demo User
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;
