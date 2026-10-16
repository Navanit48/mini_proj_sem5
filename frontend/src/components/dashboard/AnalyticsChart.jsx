import React from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';

const eligibilityData = [
  { month: 'May', eligible: 3, applied: 1 },
  { month: 'Jun', eligible: 5, applied: 2 },
  { month: 'Jul', eligible: 7, applied: 4 },
  { month: 'Aug', eligible: 8, applied: 5 },
  { month: 'Sep', eligible: 12, applied: 7 },
  { month: 'Oct', eligible: 14, applied: 9 },
];

const documentStatusData = [
  { name: 'Verified', value: 8, color: 'hsl(245, 58%, 64%)' },
  { name: 'Pending', value: 3, color: 'hsl(38, 92%, 60%)' },
  { name: 'Rejected', value: 1, color: 'hsl(0, 62%, 55%)' },
  { name: 'Expired', value: 2, color: 'hsl(220, 10%, 42%)' },
];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card border border-border/60 rounded-xl px-4 py-3 shadow-xl">
        <p className="text-xs font-medium text-muted-foreground mb-1.5">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-sm font-semibold" style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const AnalyticsChart = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-3">
        <div>
          <h3 className="text-base font-semibold text-foreground">Eligibility Trends</h3>
          <p className="text-sm text-muted-foreground mt-0.5">Schemes matched vs. applications filed</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-primary" />
            Eligible
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            Applied
          </span>
        </div>
      </div>

      <div className="h-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={eligibilityData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="eligibleGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(245, 58%, 64%)" stopOpacity={0.25} />
                <stop offset="95%" stopColor="hsl(245, 58%, 64%)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="appliedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(160, 84%, 39%)" stopOpacity={0.2} />
                <stop offset="95%" stopColor="hsl(160, 84%, 39%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(228, 12%, 16%)" vertical={false} />
            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(220, 10%, 52%)', fontSize: 12 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(220, 10%, 52%)', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="eligible"
              name="Eligible"
              stroke="hsl(245, 58%, 64%)"
              strokeWidth={2}
              fill="url(#eligibleGrad)"
            />
            <Area
              type="monotone"
              dataKey="applied"
              name="Applied"
              stroke="hsl(160, 84%, 39%)"
              strokeWidth={2}
              fill="url(#appliedGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
};

const DocumentStatusChart = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6"
    >
      <div className="mb-6">
        <h3 className="text-base font-semibold text-foreground">Document Status</h3>
        <p className="text-sm text-muted-foreground mt-0.5">Overview of uploaded documents</p>
      </div>

      <div className="h-[180px] mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={documentStatusData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(228, 12%, 16%)" vertical={false} />
            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(220, 10%, 52%)', fontSize: 12 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: 'hsl(220, 10%, 52%)', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" name="Documents" radius={[6, 6, 0, 0]}>
              {documentStatusData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {documentStatusData.map((item) => (
          <div key={item.name} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
            {item.name} ({item.value})
          </div>
        ))}
      </div>
    </motion.div>
  );
};

export { AnalyticsChart, DocumentStatusChart };
