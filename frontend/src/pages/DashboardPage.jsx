import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import api from '../lib/api';
import {
  UserRound,
  ShieldCheck,
  FileText,
  CheckCircle2,
  Loader2,
} from 'lucide-react';

import { WelcomeHeader, StatCard } from '../components/dashboard';

const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get('/analytics/dashboard');
        setStats(response.data);
      } catch (error) {
        console.error('Failed to load dashboard stats', error);
        setError('Dashboard data could not be loaded. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="w-7 h-7 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Greeting */}
      <WelcomeHeader />

      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      {!error && stats && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard
              title="Profile Completion"
              value={`${stats.profile_completion}%`}
              icon={UserRound}
              accentColor="primary"
              subtitle="Core profile fields completed"
              delay={1}
            />
            <StatCard
              title="Eligible Schemes"
              value={stats.eligible_schemes}
              icon={ShieldCheck}
              accentColor="emerald"
              subtitle="From your latest eligibility check"
              delay={2}
            />
            <StatCard
              title="Uploaded Documents"
              value={stats.uploaded_documents}
              icon={FileText}
              accentColor="sky"
              subtitle="Documents in your account"
              delay={3}
            />
            <StatCard
              title="Checklist Progress"
              value={`${stats.checklist_progress.percentage}%`}
              icon={CheckCircle2}
              accentColor="amber"
              subtitle={`${stats.checklist_progress.completed} of ${stats.checklist_progress.total} tasks completed`}
              delay={4}
            />
          </div>
          <div className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6">
            <div className="flex items-center justify-between gap-4 mb-3">
              <h2 className="text-sm font-semibold text-foreground">Application checklist progress</h2>
              <span className="text-sm text-muted-foreground">
                {stats.checklist_progress.completed}/{stats.checklist_progress.total}
              </span>
            </div>
            <div
              className="h-2 rounded-full bg-secondary overflow-hidden"
              role="progressbar"
              aria-label="Application checklist progress"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={stats.checklist_progress.percentage}
            >
              <div
                className="h-full rounded-full bg-primary transition-[width] duration-500"
                style={{ width: `${stats.checklist_progress.percentage}%` }}
              />
            </div>
          </div>
        </>
      )}
    </motion.div>
  );
};

export default DashboardPage;
