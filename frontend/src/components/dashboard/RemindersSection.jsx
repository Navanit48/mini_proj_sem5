import React from 'react';
import { motion } from 'framer-motion';
import { Circle, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

const reminders = [
  {
    id: 1,
    title: 'Upload Income Certificate',
    description: 'Required for PM Awas Yojana application',
    dueDate: 'Oct 20, 2026',
    status: 'urgent',
    completed: false,
  },
  {
    id: 2,
    title: 'Aadhaar verification pending',
    description: 'Complete e-KYC for scheme eligibility',
    dueDate: 'Oct 22, 2026',
    status: 'upcoming',
    completed: false,
  },
  {
    id: 3,
    title: 'Ration Card renewal',
    description: 'Annual renewal due for NFSA benefits',
    dueDate: 'Oct 28, 2026',
    status: 'upcoming',
    completed: false,
  },
  {
    id: 4,
    title: 'Scholarship application submitted',
    description: 'Post-Matric Scholarship — awaiting review',
    dueDate: 'Oct 10, 2026',
    status: 'done',
    completed: true,
  },
  {
    id: 5,
    title: 'Bank passbook uploaded',
    description: 'DBT account verification complete',
    dueDate: 'Oct 8, 2026',
    status: 'done',
    completed: true,
  },
];

const statusConfig = {
  urgent: {
    icon: AlertCircle,
    badgeClass: 'bg-rose-500/10 text-rose-400',
    label: 'Urgent',
  },
  upcoming: {
    icon: Clock,
    badgeClass: 'bg-amber-500/10 text-amber-400',
    label: 'Upcoming',
  },
  done: {
    icon: CheckCircle2,
    badgeClass: 'bg-emerald-500/10 text-emerald-400',
    label: 'Done',
  },
};

const RemindersSection = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.45, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6"
    >
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-base font-semibold text-foreground">Reminders & Deadlines</h3>
          <p className="text-sm text-muted-foreground mt-0.5">{reminders.filter(r => !r.completed).length} pending items</p>
        </div>
        <button className="text-xs font-medium text-primary hover:text-primary/80 transition-colors px-3 py-1.5 rounded-lg hover:bg-primary/8">
          View All
        </button>
      </div>

      <div className="space-y-1">
        {reminders.map((reminder, index) => {
          const config = statusConfig[reminder.status];
          const StatusIcon = config.icon;

          return (
            <motion.div
              key={reminder.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.5 + index * 0.05 }}
              className={cn(
                'flex items-start gap-3 p-3 rounded-xl transition-colors duration-200 group',
                'hover:bg-secondary/40',
                reminder.completed && 'opacity-50'
              )}
            >
              <div className="mt-0.5">
                {reminder.completed ? (
                  <CheckCircle2 className="w-[18px] h-[18px] text-emerald-400" />
                ) : (
                  <Circle className="w-[18px] h-[18px] text-muted-foreground/40 group-hover:text-muted-foreground/60 transition-colors" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className={cn(
                  'text-sm font-medium text-foreground leading-tight',
                  reminder.completed && 'line-through text-muted-foreground'
                )}>
                  {reminder.title}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">
                  {reminder.description}
                </p>
              </div>

              <div className="flex flex-col items-end gap-1.5 shrink-0">
                <span className={cn('text-[10px] font-medium px-2 py-0.5 rounded-md', config.badgeClass)}>
                  {config.label}
                </span>
                <span className="text-[11px] text-muted-foreground">{reminder.dueDate}</span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default RemindersSection;
