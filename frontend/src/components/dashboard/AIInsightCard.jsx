import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  FileCheck,
  Lightbulb,
  Sparkles,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const insightIcons = {
  eligible: { icon: CheckCircle2, color: 'text-primary', bg: 'bg-secondary/70' },
  priority: { icon: Sparkles, color: 'text-primary', bg: 'bg-secondary/70' },
  profile: { icon: AlertTriangle, color: 'text-primary', bg: 'bg-secondary/70' },
  documents: { icon: FileCheck, color: 'text-primary', bg: 'bg-secondary/70' },
  checklist: { icon: FileCheck, color: 'text-primary', bg: 'bg-secondary/70' },
  suggestion: { icon: Lightbulb, color: 'text-primary', bg: 'bg-secondary/70' },
};

const AIInsightCard = ({ insights = [] }) => {
  if (insights.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="bg-card border border-border/60 rounded-2xl p-5 sm:p-6"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2 rounded-lg bg-secondary/70 border border-border/60">
          <Sparkles className="w-4 h-4 text-primary" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">AI Insights</h3>
          <p className="text-xs text-muted-foreground">Personalized recommendations for you</p>
        </div>
      </div>

      <div className="space-y-2.5">
        {insights.map((insight, index) => {
          const style = insightIcons[insight.type] || insightIcons.suggestion;
          const Icon = style.icon;
          return (
            <motion.div
              key={insight.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.55 + index * 0.06 }}
              className="flex items-start gap-3 p-3.5 rounded-xl bg-secondary/20 border border-border/50 hover:border-border/80 hover:bg-secondary/35 transition-colors duration-200 group"
            >
              <div className={cn('p-2 rounded-lg shrink-0 mt-0.5', style.bg)}>
                <Icon className={cn('w-4 h-4', style.color)} />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground leading-tight mb-1">
                  {insight.title}
                </p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {insight.description}
                </p>
              </div>

              <Link to={insight.action_path} className="shrink-0 flex items-center gap-1 text-xs font-medium text-primary mt-1">
                {insight.action_label}
                <ArrowRight className="w-3 h-3" />
              </Link>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default AIInsightCard;
