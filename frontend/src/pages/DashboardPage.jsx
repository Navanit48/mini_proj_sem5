import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import api from '../lib/api';
import {
  UserRound,
  ShieldCheck,
  FileText,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  ArrowRight,
  FileCheck2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { WelcomeHeader, StatCard, AIInsightCard } from '../components/dashboard';
import ApplicationCard from '../components/applications/ApplicationCard';
import ApplicationTimeline from '../components/applications/ApplicationTimeline';

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
          <AIInsightCard insights={stats.ai_insights || []} />

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-foreground">Document verification</h2>
                  <p className="mt-1 text-xs text-muted-foreground">Preliminary automated checks only</p>
                </div>
                <Link to="/documents" className="text-xs font-medium text-primary hover:underline">View documents <ArrowRight className="inline h-3.5 w-3.5" /></Link>
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                {[
                  { label: 'Preliminary matches', value: stats.verification_summary?.preliminary_match || 0, tone: 'text-emerald-300' },
                  { label: 'Needs review', value: stats.verification_summary?.needs_review || 0, tone: 'text-amber-300' },
                  { label: 'Processing', value: stats.verification_summary?.processing || 0, tone: 'text-primary' },
                  { label: 'Unreadable', value: stats.verification_summary?.unreadable || 0, tone: 'text-rose-300' },
                ].map(item => (
                  <div key={item.label} className="rounded-xl border border-border/50 bg-secondary/20 p-3">
                    <p className={`text-xl font-semibold ${item.tone}`}>{item.value}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{item.label}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-2 rounded-xl border border-border/50 bg-secondary/20 px-3 py-2.5 text-xs text-muted-foreground">
                <AlertTriangle className="h-4 w-4 shrink-0 text-amber-300" />
                {stats.pending_documents || 0} document(s) need processing or a manual review.
              </div>
            </section>

            <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-foreground">Latest application activity</h2>
                  <p className="mt-1 text-xs text-muted-foreground">AidFlow package timeline</p>
                </div>
                <Link to="/applications" className="text-xs font-medium text-primary hover:underline">All applications <ArrowRight className="inline h-3.5 w-3.5" /></Link>
              </div>
              {stats.recent_applications?.[0] ? (
                <div className="mt-5">
                  <div className="mb-4 flex items-center gap-2 text-sm font-medium text-foreground"><FileCheck2 className="h-4 w-4 text-primary" />{stats.recent_applications[0].scheme_name}</div>
                  <ApplicationTimeline
                    events={stats.recent_applications[0].timeline || []}
                    externalStages={stats.recent_applications[0].external_stages || []}
                  />
                </div>
              ) : (
                <div className="mt-5 rounded-xl border border-dashed border-border p-6 text-center">
                  <p className="text-sm text-muted-foreground">No saved applications yet.</p>
                  <Link to="/schemes" className="mt-2 inline-block text-sm font-medium text-primary hover:underline">Explore schemes</Link>
                </div>
              )}
            </section>
          </div>

          <section className="space-y-4">
            <div className="flex items-end justify-between gap-3">
              <div>
                <h2 className="font-semibold text-foreground">Recent applications</h2>
                <p className="mt-1 text-xs text-muted-foreground">Your latest AidFlow packages and their progress</p>
              </div>
              <Link to="/applications" className="text-xs font-medium text-primary hover:underline">View all <ArrowRight className="inline h-3.5 w-3.5" /></Link>
            </div>
            {stats.recent_applications?.length ? (
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {stats.recent_applications.map(application => <ApplicationCard key={application.id} application={application} />)}
              </div>
            ) : (
              <p className="rounded-xl border border-border/50 bg-card p-4 text-sm text-muted-foreground">Application progress will appear here after you prepare a scheme package.</p>
            )}
          </section>
        </>
      )}
    </motion.div>
  );
};

export default DashboardPage;
