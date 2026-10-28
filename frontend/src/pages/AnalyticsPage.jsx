import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import api from '../lib/api';

const statusColors = {
  eligible: 'hsl(160, 84%, 39%)',
  partial: 'hsl(38, 92%, 60%)',
  notEligible: 'hsl(0, 62%, 55%)',
};

const documentStatus = [
  { key: 'completed', label: 'Completed', color: 'hsl(160, 84%, 39%)' },
  { key: 'processing', label: 'Processing', color: 'hsl(205, 80%, 58%)' },
  { key: 'uploaded', label: 'Uploaded', color: 'hsl(38, 92%, 60%)' },
  { key: 'failed', label: 'Failed', color: 'hsl(0, 62%, 55%)' },
];

const chartTooltipStyle = {
  backgroundColor: 'hsl(228, 14%, 10%)',
  border: '1px solid hsl(228, 12%, 22%)',
  borderRadius: '12px',
  color: 'hsl(220, 20%, 92%)',
};

const ChartPanel = ({ title, description, children, className = '' }) => (
  <section className={`bg-card border border-border/50 rounded-2xl p-5 sm:p-6 ${className}`}>
    <div className="mb-5">
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
      <p className="text-sm text-muted-foreground mt-1">{description}</p>
    </div>
    {children}
  </section>
);

const EmptyChart = ({ message }) => (
  <div className="h-full flex items-center justify-center text-sm text-muted-foreground text-center px-4">
    {message}
  </div>
);

const AnalyticsPage = () => {
  const [analytics, setAnalytics] = useState({ eligibility: [], documents: [], checklists: [] });
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    let active = true;
    const sources = [
      ['eligibility', () => api.get('/eligibility/history')],
      ['documents', () => api.get('/documents')],
      ['checklists', () => api.get('/checklists')],
    ];

    Promise.all(sources.map(async ([key, request]) => {
      try {
        const { data } = await request();
        return { key, data };
      } catch {
        return { key, error: true };
      }
    })).then((results) => {
      if (!active) return;
      const nextAnalytics = { eligibility: [], documents: [], checklists: [] };
      const nextErrors = {};

      results.forEach(({ key, data, error }) => {
        if (error) {
          nextErrors[key] = true;
          return;
        }
        if (key === 'eligibility') nextAnalytics.eligibility = data.checks || [];
        if (key === 'documents') nextAnalytics.documents = data.documents || [];
        if (key === 'checklists') nextAnalytics.checklists = data.checklists || [];
      });

      setAnalytics(nextAnalytics);
      setErrors(nextErrors);
      setLoading(false);
    });

    return () => { active = false; };
  }, []);

  const eligibilityTrend = [...analytics.eligibility]
    .sort((a, b) => new Date(a.checked_at) - new Date(b.checked_at))
    .map((check, index) => {
      const counts = { eligible: 0, partial: 0, notEligible: 0 };
      (check.results || []).forEach(({ match_percentage: percentage }) => {
        if (percentage >= 70) counts.eligible += 1;
        else if (percentage >= 40) counts.partial += 1;
        else counts.notEligible += 1;
      });
      return {
        date: check.checked_at
          ? new Date(check.checked_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
          : `Check ${index + 1}`,
        ...counts,
      };
    });

  const documentBreakdown = documentStatus.map((status) => ({
    name: status.label,
    value: analytics.documents.filter((document) => document.status === status.key).length,
    color: status.color,
  })).filter((status) => status.value > 0);

  const checklistProgress = analytics.checklists.map((checklist) => {
    const items = checklist.items || [];
    const completed = items.filter((item) => item.is_completed).length;
    return {
      scheme: checklist.scheme_name || 'Scheme',
      completed,
      remaining: Math.max(items.length - completed, 0),
    };
  }).filter((checklist) => checklist.completed + checklist.remaining > 0);

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
        <p className="text-sm text-muted-foreground mt-1.5">
          Trends from your saved eligibility checks, documents, and application checklists.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <ChartPanel
          title="Eligibility check history"
          description="Schemes by match status for each saved check."
          className="xl:col-span-2"
        >
          {errors.eligibility ? (
            <div className="h-[280px]"><EmptyChart message="Eligibility history could not be loaded." /></div>
          ) : eligibilityTrend.length === 0 ? (
            <div className="h-[280px]"><EmptyChart message="Run an eligibility check to see your history here." /></div>
          ) : (
            <div className="h-[280px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={eligibilityTrend} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(228, 12%, 20%)" vertical={false} />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: 'hsl(220, 10%, 58%)', fontSize: 12 }} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: 'hsl(220, 10%, 58%)', fontSize: 12 }} />
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Legend />
                  <Line type="monotone" dataKey="eligible" name="Eligible" stroke={statusColors.eligible} strokeWidth={2.5} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="partial" name="Partially eligible" stroke={statusColors.partial} strokeWidth={2.5} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="notEligible" name="Not eligible" stroke={statusColors.notEligible} strokeWidth={2.5} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </ChartPanel>

        <ChartPanel title="Document status" description="Current status of your uploaded documents.">
          {errors.documents ? (
            <div className="h-[260px]"><EmptyChart message="Your documents could not be loaded." /></div>
          ) : documentBreakdown.length === 0 ? (
            <div className="h-[260px]"><EmptyChart message="Uploaded documents will appear here." /></div>
          ) : (
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={documentBreakdown} dataKey="value" nameKey="name" innerRadius={58} outerRadius={92} paddingAngle={3}>
                    {documentBreakdown.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                  </Pie>
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </ChartPanel>

        <ChartPanel title="Checklist progress by scheme" description="Completed and remaining tasks in your saved checklists.">
          {errors.checklists ? (
            <div className="h-[260px]"><EmptyChart message="Your checklists could not be loaded." /></div>
          ) : checklistProgress.length === 0 ? (
            <div className="h-[260px]"><EmptyChart message="Create a checklist to track task progress here." /></div>
          ) : (
            <div className="h-[260px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={checklistProgress} layout="vertical" margin={{ top: 0, right: 12, left: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(228, 12%, 20%)" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: 'hsl(220, 10%, 58%)', fontSize: 12 }} />
                  <YAxis type="category" dataKey="scheme" width={118} axisLine={false} tickLine={false} tick={{ fill: 'hsl(220, 10%, 58%)', fontSize: 11 }} />
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Legend />
                  <Bar dataKey="completed" name="Completed" stackId="tasks" fill={statusColors.eligible} radius={[0, 0, 0, 0]} />
                  <Bar dataKey="remaining" name="Remaining" stackId="tasks" fill="hsl(228, 12%, 28%)" radius={[0, 5, 5, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </ChartPanel>
      </div>
    </motion.div>
  );
};

export default AnalyticsPage;
