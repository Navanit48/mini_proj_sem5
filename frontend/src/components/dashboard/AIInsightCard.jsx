import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, AlertTriangle, FileCheck, Lightbulb } from 'lucide-react';
import { cn } from '../../lib/utils';

const insights = [
  {
    id: 1,
    type: 'missing',
    icon: AlertTriangle,
    iconColor: 'text-amber-400',
    iconBg: 'bg-amber-500/10',
    title: 'Missing: Income Certificate',
    description: 'You need an income certificate to qualify for 3 additional schemes including PM Awas Yojana and NSAP.',
    action: 'Upload Now',
  },
  {
    id: 2,
    type: 'suggestion',
    icon: Lightbulb,
    iconColor: 'text-primary',
    iconBg: 'bg-primary/10',
    title: 'New scheme match found',
    description: 'Based on your profile, you may be eligible for the Ayushman Bharat health insurance scheme. Check your eligibility.',
    action: 'Check Eligibility',
  },
  {
    id: 3,
    type: 'action',
    icon: FileCheck,
    iconColor: 'text-emerald-400',
    iconBg: 'bg-emerald-500/10',
    title: 'Complete your Ration Card application',
    description: 'Your NFSA application is 80% complete. Upload remaining documents to submit.',
    action: 'Continue',
  },
];

const AIInsightCard = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6 relative overflow-hidden"
    >
      {/* Subtle gradient accent */}
      <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-primary/6 to-transparent rounded-full -translate-y-1/2 translate-x-1/4 pointer-events-none" />

      <div className="flex items-center gap-2.5 mb-5 relative">
        <div className="p-2 rounded-xl bg-gradient-to-br from-primary/15 to-purple-500/10 border border-primary/10">
          <Sparkles className="w-4 h-4 text-primary" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-foreground">AI Insights</h3>
          <p className="text-xs text-muted-foreground">Personalized recommendations for you</p>
        </div>
      </div>

      <div className="space-y-3 relative">
        {insights.map((insight, index) => {
          const Icon = insight.icon;
          return (
            <motion.div
              key={insight.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.55 + index * 0.06 }}
              className="flex items-start gap-3 p-3.5 rounded-xl bg-secondary/30 border border-border/30 hover:border-border/60 hover:bg-secondary/50 transition-all duration-200 group cursor-pointer"
            >
              <div className={cn('p-2 rounded-lg shrink-0 mt-0.5', insight.iconBg)}>
                <Icon className={cn('w-4 h-4', insight.iconColor)} />
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground leading-tight mb-1">
                  {insight.title}
                </p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {insight.description}
                </p>
              </div>

              <button className="shrink-0 flex items-center gap-1 text-xs font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-200 mt-1">
                {insight.action}
                <ArrowRight className="w-3 h-3" />
              </button>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default AIInsightCard;
