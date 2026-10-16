import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

const StatCard = ({ title, value, subtitle, icon: Icon, trend, trendLabel, accentColor = 'primary', delay = 0 }) => {
  const accentMap = {
    primary: {
      iconBg: 'bg-primary/10',
      iconText: 'text-primary',
      trendUp: 'text-emerald-400',
      trendDown: 'text-red-400',
      glow: 'shadow-primary/5',
    },
    emerald: {
      iconBg: 'bg-emerald-500/10',
      iconText: 'text-emerald-400',
      trendUp: 'text-emerald-400',
      trendDown: 'text-red-400',
      glow: 'shadow-emerald-500/5',
    },
    amber: {
      iconBg: 'bg-amber-500/10',
      iconText: 'text-amber-400',
      trendUp: 'text-emerald-400',
      trendDown: 'text-red-400',
      glow: 'shadow-amber-500/5',
    },
    rose: {
      iconBg: 'bg-rose-500/10',
      iconText: 'text-rose-400',
      trendUp: 'text-emerald-400',
      trendDown: 'text-red-400',
      glow: 'shadow-rose-500/5',
    },
    sky: {
      iconBg: 'bg-sky-500/10',
      iconText: 'text-sky-400',
      trendUp: 'text-emerald-400',
      trendDown: 'text-red-400',
      glow: 'shadow-sky-500/5',
    },
  };

  const accent = accentMap[accentColor] || accentMap.primary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: delay * 0.08, ease: [0.25, 0.46, 0.45, 0.94] }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      className={cn(
        'bg-card border border-border/50 rounded-2xl p-5 transition-shadow duration-300',
        'hover:shadow-lg hover:border-border/80',
        accent.glow
      )}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={cn('p-2.5 rounded-xl', accent.iconBg)}>
          <Icon className={cn('w-5 h-5', accent.iconText)} />
        </div>
        {trend !== undefined && (
          <span
            className={cn(
              'text-xs font-medium px-2 py-1 rounded-lg',
              trend >= 0
                ? `${accent.trendUp} bg-emerald-500/10`
                : `${accent.trendDown} bg-red-500/10`
            )}
          >
            {trend >= 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>

      <div>
        <p className="text-sm text-muted-foreground font-medium mb-1">{title}</p>
        <h3 className="text-2xl font-bold text-foreground tracking-tight">{value}</h3>
        {(subtitle || trendLabel) && (
          <p className="text-xs text-muted-foreground mt-1.5">{trendLabel || subtitle}</p>
        )}
      </div>
    </motion.div>
  );
};

export default StatCard;
