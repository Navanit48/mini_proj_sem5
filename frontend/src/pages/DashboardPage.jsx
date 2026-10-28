import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import {
  ShieldCheck,
  FileText,
  Clock,
  Loader2,
} from 'lucide-react';

import {
  WelcomeHeader,
  StatCard,
  AnalyticsChart,
  DocumentStatusChart,
  RemindersSection,
  AIInsightCard,
} from '../components/dashboard';

const DashboardPage = () => {
  const { user } = useAuth();
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

      {/* Summary Cards */}
      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Matched Schemes"
          value={stats?.matched_schemes ?? 0}
          icon={ShieldCheck}
          accentColor="primary"
          delay={1}
        />
        <StatCard
          title="Pending Tasks"
          value={stats?.pending_tasks ?? 0}
          icon={FileText}
          accentColor="amber"
          delay={2}
        />
        <StatCard
          title="Uploaded Documents"
          value={stats?.uploaded_documents ?? 0}
          icon={Clock}
          accentColor="sky"
          delay={3}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3">
          <AnalyticsChart />
        </div>
        <div className="lg:col-span-2">
          <DocumentStatusChart />
        </div>
      </div>

      {/* Bottom Row: Reminders + AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RemindersSection />
        <AIInsightCard />
      </div>
    </motion.div>
  );
};

export default DashboardPage;
