import { Check, Circle, Clock3 } from 'lucide-react';
import { cn } from '../../lib/utils';

const statusLabels = {
  submitted: 'Submitted to AidFlow',
  under_review: 'Under Review',
  ai_document_verification: 'AI Preliminary Verification',
  ready_for_government_submission: 'Ready for Government Submission',
};

const formatDate = (date) => date
  ? new Date(date).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
  : 'Pending';

const ApplicationTimeline = ({ events = [], externalStages = [] }) => {
  const completed = events.map((event) => ({
    key: event.status,
    title: statusLabels[event.status] || event.status,
    description: event.description,
    occurredAt: event.occurred_at,
    progress: event.progress,
    done: true,
  }));
  const external = externalStages.map((stage) => ({
    key: stage.title,
    title: stage.title,
    description: stage.description,
    occurredAt: stage.occurred_at,
    progress: stage.progress,
    done: false,
  }));
  const stages = [...completed, ...external];

  return (
    <ol className="space-y-0" aria-label="Application status timeline">
      {stages.map((stage, index) => (
        <li key={`${stage.key}-${index}`} className="relative flex gap-3 pb-5 last:pb-0">
          {index < stages.length - 1 && (
            <span className={cn(
              'absolute left-[11px] top-6 h-[calc(100%-14px)] w-px',
              stage.done ? 'bg-primary/50' : 'bg-border',
            )} aria-hidden="true" />
          )}
          <span className={cn(
            'relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border',
            stage.done ? 'border-primary/40 bg-primary/15 text-primary' : 'border-border bg-secondary text-muted-foreground',
          )}>
            {stage.done ? <Check className="h-3.5 w-3.5" /> : index < completed.length + 1 ? <Clock3 className="h-3.5 w-3.5" /> : <Circle className="h-3 w-3" />}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h4 className={cn('text-sm font-semibold', stage.done ? 'text-foreground' : 'text-muted-foreground')}>
                {stage.title}
              </h4>
              <span className="text-xs text-muted-foreground">{formatDate(stage.occurredAt)}</span>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{stage.description}</p>
            <div className="mt-2 flex items-center gap-2 text-[11px] text-muted-foreground">
              <span className="h-1.5 w-20 overflow-hidden rounded-full bg-secondary" role="progressbar" aria-label={`${stage.title} progress`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={stage.progress}>
                <span className={cn('block h-full rounded-full', stage.done ? 'bg-primary' : 'bg-muted-foreground/40')} style={{ width: `${stage.progress}%` }} />
              </span>
              {stage.progress}%
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
};

export default ApplicationTimeline;
