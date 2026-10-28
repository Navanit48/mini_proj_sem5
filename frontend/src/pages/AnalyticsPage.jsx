import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, FileText, Loader2, ShieldCheck, UserRound } from 'lucide-react';
import api from '../lib/api';
import { StatCard } from '../components/dashboard';

const AnalyticsPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    api.get('/analytics/dashboard')
      .then(({ data }) => {
        if (active) setStats(data);
      })
      .catch(() => {
        if (active) setError('Your activity data could not be loaded. Please try again.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
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
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-foreground tracking-tight">My Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1.5">A summary of your profile and scheme activity.</p>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-rose-400">{error}</p>
      ) : stats && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard title="Profile Completion" value={`${stats.profile_completion}%`} icon={UserRound} accentColor="primary" subtitle="Core profile fields completed" />
            <StatCard title="Eligible Schemes" value={stats.eligible_schemes} icon={ShieldCheck} accentColor="emerald" subtitle="From your latest eligibility check" />
            <StatCard title="Uploaded Documents" value={stats.uploaded_documents} icon={FileText} accentColor="sky" subtitle="Documents in your account" />
            <StatCard title="Checklist Progress" value={`${stats.checklist_progress.percentage}%`} icon={CheckCircle2} accentColor="amber" subtitle={`${stats.checklist_progress.completed} of ${stats.checklist_progress.total} tasks completed`} />
          </div>

          <section className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6">
            <div className="flex items-center justify-between gap-4 mb-3">
              <h2 className="text-sm font-semibold text-foreground">Checklist task completion</h2>
              <span className="text-sm text-muted-foreground">
                {stats.checklist_progress.completed}/{stats.checklist_progress.total}
              </span>
            </div>
            <div
              className="h-2 rounded-full bg-secondary overflow-hidden"
              role="progressbar"
              aria-label="Checklist task completion"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={stats.checklist_progress.percentage}
            >
              <div
                className="h-full rounded-full bg-primary transition-[width] duration-500"
                style={{ width: `${stats.checklist_progress.percentage}%` }}
              />
            </div>
          </section>
        </>
      )}
    </motion.div>
  );
};

export default AnalyticsPage;
