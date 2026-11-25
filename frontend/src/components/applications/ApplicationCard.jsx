import { ArrowRight, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';

const statusLabels = {
  submitted: 'Submitted',
  under_review: 'Under Review',
  ai_document_verification: 'AI Preliminary Verification',
  ready_for_government_submission: 'Ready for Government Submission',
};

const ApplicationCard = ({ application }) => (
  <article className="rounded-2xl border border-border/60 bg-card p-5">
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <p className="text-xs text-muted-foreground">{application.application_code}</p>
        <h3 className="mt-1 truncate text-base font-semibold text-foreground">{application.scheme_name}</h3>
      </div>
      <span className={cn(
        'shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-medium',
        application.status === 'ready_for_government_submission'
          ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-300'
          : 'border-border bg-secondary/50 text-muted-foreground',
      )}>
        {statusLabels[application.status] || 'In progress'}
      </span>
    </div>

    <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
      <FileText className="h-3.5 w-3.5" />
      {application.documents?.length || 0} attached document(s)
      <span className="ml-auto">{new Date(application.submitted_at).toLocaleDateString('en-IN')}</span>
    </div>

    <div className="mt-3">
      <div className="mb-1.5 flex justify-between text-xs text-muted-foreground">
        <span>AidFlow package progress</span><span>{application.progress}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-secondary" role="progressbar" aria-label="AidFlow application package progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={application.progress}>
        <div className="h-full rounded-full bg-primary transition-[width] duration-500" style={{ width: `${application.progress}%` }} />
      </div>
    </div>

    <Link
      to={`/applications/${application.id}`}
      className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
    >
      Track application <ArrowRight className="h-4 w-4" />
    </Link>
  </article>
);

export default ApplicationCard;
