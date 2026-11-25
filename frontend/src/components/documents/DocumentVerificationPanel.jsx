import { AlertTriangle, CheckCircle2, Clock3, ShieldAlert } from 'lucide-react';
import { cn } from '../../lib/utils';

const verificationLabels = {
  preliminary_match: 'Preliminary match',
  needs_review: 'Needs your review',
  unreadable: 'Could not read document',
};

const formatValue = (field, value) => field === 'annual_income'
  ? `₹${Number(value).toLocaleString('en-IN')}`
  : String(value);

const DocumentVerificationPanel = ({ document }) => {
  const result = document.verification;
  if (!result) {
    const processing = ['uploaded', 'processing'].includes(document.status);
    return (
      <div className="mt-4 flex items-center gap-2 rounded-xl border border-border/50 bg-secondary/25 px-3 py-2.5 text-xs text-muted-foreground">
        {processing ? <Clock3 className="h-4 w-4 text-primary" /> : <AlertTriangle className="h-4 w-4 text-amber-400" />}
        <span>{processing ? 'AI Preliminary Verification is processing.' : 'No preliminary verification result is available.'}</span>
      </div>
    );
  }

  const isMatch = result.verification_status === 'preliminary_match';
  const StatusIcon = isMatch ? CheckCircle2 : ShieldAlert;
  const extracted = Object.entries(result.extracted_fields || {});

  return (
    <section className="mt-4 rounded-xl border border-border/50 bg-secondary/20 p-3.5" aria-label="AI Preliminary Verification result">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h5 className="text-xs font-semibold text-foreground">AI Preliminary Verification</h5>
        <span className={cn(
          'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium',
          isMatch ? 'border-emerald-500/20 bg-emerald-500/8 text-emerald-300' : 'border-amber-500/20 bg-amber-500/8 text-amber-300',
        )}>
          <StatusIcon className="h-3.5 w-3.5" />
          {verificationLabels[result.verification_status] || 'Needs your review'}
        </span>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{result.validation_summary}</p>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
        <span>Detected type: <strong className="text-foreground">{(result.detected_document_type || 'unknown').replaceAll('_', ' ')}</strong></span>
        <span>Confidence: <strong className="text-foreground">{Math.round(result.confidence_score || 0)}%</strong></span>
      </div>

      {extracted.length > 0 && (
        <dl className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {extracted.map(([field, value]) => (
            <div key={field} className="rounded-lg border border-border/40 bg-background/40 px-2.5 py-2">
              <dt className="text-[11px] capitalize text-muted-foreground">{field.replaceAll('_', ' ')}</dt>
              <dd className="mt-0.5 break-words text-xs font-medium text-foreground">{formatValue(field, value)}</dd>
            </div>
          ))}
        </dl>
      )}

      {result.mismatches?.length > 0 && (
        <div className="mt-3 space-y-1.5">
          <h6 className="text-xs font-semibold text-amber-300">Possible mismatches</h6>
          {result.mismatches.map((mismatch, index) => (
            <p key={`${mismatch.field}-${index}`} className="text-xs text-muted-foreground">
              {mismatch.message} Document: <strong className="text-foreground">{mismatch.document_value}</strong>; profile: <strong className="text-foreground">{mismatch.profile_value}</strong>.
            </p>
          ))}
        </div>
      )}

      {result.warnings?.length > 0 && (
        <ul className="mt-3 space-y-1">
          {result.warnings.map((warning, index) => (
            <li key={index} className="flex gap-1.5 text-xs text-amber-200/80">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{warning}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 border-t border-border/40 pt-2 text-[11px] text-muted-foreground">
        This automated check is preliminary and is not government or legal verification.
      </p>
    </section>
  );
};

export default DocumentVerificationPanel;
