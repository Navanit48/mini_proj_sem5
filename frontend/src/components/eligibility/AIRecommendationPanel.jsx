import { Link } from 'react-router-dom';
import {
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  FileCheck2,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const statusStyles = {
  Eligible: {
    icon: CheckCircle2,
    color: 'text-emerald-400',
    badge: 'bg-secondary/40 text-foreground border-border/60',
  },
  'Partially Eligible': {
    icon: AlertCircle,
    color: 'text-amber-400',
    badge: 'bg-secondary/40 text-foreground border-border/60',
  },
  'Not Eligible': {
    icon: XCircle,
    color: 'text-rose-400',
    badge: 'bg-secondary/40 text-foreground border-border/60',
  },
};

const priorityStyles = {
  highest: 'border-primary/35 bg-primary/10 text-primary',
  medium: 'border-border/70 bg-secondary/40 text-foreground/80',
  low: 'border-secondary bg-secondary/60 text-muted-foreground',
};

const AIRecommendationPanel = ({ recommendation, onCompleteProfile }) => {
  if (!recommendation) return null;

  const style = statusStyles[recommendation.status] || statusStyles['Not Eligible'];
  const StatusIcon = style.icon;
  const action = recommendation.next_action;

  return (
    <section className="mt-5 rounded-xl border border-border/60 bg-secondary/20 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-secondary/70">
            <ShieldCheck className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h5 className="font-semibold text-foreground">AI Recommendation</h5>
            <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
              {recommendation.recommendation}
            </p>
          </div>
        </div>
        {recommendation.priority && (
          <span className={cn(
            'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold',
            priorityStyles[recommendation.priority.class] || priorityStyles.low,
          )}>
            <span className="tracking-tight" aria-label={recommendation.priority.stars + ' stars'}>
              {'★'.repeat(recommendation.priority.stars)}
            </span>
            {recommendation.priority.label}
          </span>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold', style.badge)}>
          <StatusIcon className={cn('h-3.5 w-3.5', style.color)} />
          {recommendation.status}
        </span>
        <span className="rounded-full border border-border/60 bg-secondary/30 px-2.5 py-1 text-xs text-muted-foreground">
          AI Confidence Score: <strong className="text-foreground">{recommendation.confidence_score}%</strong>
        </span>
      </div>

      {recommendation.reasons?.length > 0 && (
        <div className="mt-4">
          <h6 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Why this result</h6>
          <ul className="space-y-1.5">
            {recommendation.reasons.map((reason, index) => (
              <li key={index} className="flex gap-2 text-sm text-foreground/85">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {recommendation.improve_eligibility?.length > 0 && (
        <div className="mt-4 rounded-xl border border-border/60 bg-secondary/25 p-3.5">
          <h6 className="mb-2 text-xs font-semibold uppercase tracking-wide text-foreground">Improve Eligibility</h6>
          <ul className="space-y-1.5">
            {recommendation.improve_eligibility.map((tip, index) => (
              <li key={index} className="flex gap-2 text-sm text-foreground/85">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {recommendation.recommended_documents?.length > 0 && (
        <div className="mt-4">
          <h6 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Recommended Documents
            {recommendation.recommended_documents.some((doc) => doc.generic) && (
              <span className="ml-2 normal-case tracking-normal">Generic preparation list</span>
            )}
          </h6>
          <div className="flex flex-wrap gap-2">
            {recommendation.recommended_documents.map((document) => (
              <span
                key={document.category}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs',
                  document.uploaded
                  ? 'border-border/60 bg-secondary/30 text-foreground'
                    : 'border-border/50 bg-secondary/30 text-muted-foreground',
                )}
              >
                <FileCheck2 className="h-3.5 w-3.5" />
                {document.name}
                {document.uploaded ? ' · Uploaded' : ''}
              </span>
            ))}
          </div>
        </div>
      )}

      {recommendation.checklist_progress && (
        <p className="mt-3 text-xs text-muted-foreground">
          Checklist progress: {recommendation.checklist_progress.completed} of {recommendation.checklist_progress.total} tasks complete.
        </p>
      )}

      {action && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Recommended Next Action
          </p>
          {action.kind === 'complete_profile' ? (
            <button
              type="button"
              onClick={onCompleteProfile}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary/90"
            >
              {action.label}
            </button>
          ) : action.external ? (
            <a
              href={action.href}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary/90"
            >
              {action.label}
              <ExternalLink className="h-4 w-4" />
            </a>
          ) : (
            <Link
              to={action.href}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary/90"
            >
              {action.label}
            </Link>
          )}
        </div>
      )}
    </section>
  );
};

export default AIRecommendationPanel;
