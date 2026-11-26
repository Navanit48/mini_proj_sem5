import { AlertTriangle, CheckCircle2, Clock3, ShieldAlert, XCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

export const VERIFICATION_BADGES = {
  verified: {
    label: 'Verified',
    icon: CheckCircle2,
    className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  },
  preliminary_match: {
    label: 'Verified',
    icon: CheckCircle2,
    className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  },
  mismatch: {
    label: 'Mismatch',
    icon: XCircle,
    className: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
  },
  needs_review: {
    label: 'Needs review',
    icon: ShieldAlert,
    className: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  },
  unreadable: {
    label: 'Needs review',
    icon: ShieldAlert,
    className: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
  },
  processing: {
    label: 'Processing',
    icon: Clock3,
    className: 'border-sky-500/30 bg-sky-500/10 text-sky-300',
  },
};

export function resolveVerificationBadge(document) {
  const isProcessing =
    document.status === 'processing' ||
    document.status === 'uploaded' ||
    (document.status === 'pending' && (!document.verification_status || document.verification_status === 'pending'));

  if (isProcessing) {
    return VERIFICATION_BADGES.processing;
  }
  const status = document.verification_status || document.verification?.verification_status;
  if (status && VERIFICATION_BADGES[status]) {
    return VERIFICATION_BADGES[status];
  }
  if (document.status === 'failed') {
    return VERIFICATION_BADGES.needs_review;
  }
  return VERIFICATION_BADGES.processing;
}

const formatFieldValue = (field, value) => {
  if (value === null || value === undefined || value === '') return '—';
  if (field === 'annual_income' && !Number.isNaN(Number(value))) {
    return `₹${Number(value).toLocaleString('en-IN')}`;
  }
  return String(value);
};

const DocumentVerificationPanel = ({ document }) => {
  const isProcessing =
    document.status === 'processing' ||
    document.status === 'uploaded' ||
    (document.status === 'pending' && (!document.verification_status || document.verification_status === 'pending'));

  const result = document.verification;
  const extractedFields = document.extracted_fields && Object.keys(document.extracted_fields).length > 0
    ? document.extracted_fields
    : (result?.extracted_fields || {});

  const mismatches = document.mismatch_details?.length
    ? document.mismatch_details
    : (result?.mismatches || []);

  const warnings = result?.warnings || [];

  const rawConfidence = document.ocr_confidence !== null && document.ocr_confidence !== undefined
    ? Number(document.ocr_confidence)
    : (result?.confidence_score !== undefined ? Number(result.confidence_score) / 100 : null);
  const confidencePct = rawConfidence !== null && !Number.isNaN(rawConfidence)
    ? Math.round((rawConfidence > 1 ? rawConfidence / 100 : rawConfidence) * 100)
    : null;

  if (isProcessing) {
    return (
      <div className="mt-4 flex items-center gap-2 rounded-xl border border-sky-500/20 bg-sky-500/8 px-3 py-2.5 text-xs text-sky-300">
        <Clock3 className="h-4 w-4 shrink-0 animate-pulse" />
        <span>Running OCR preprocessing, Groq extraction, and profile verification...</span>
      </div>
    );
  }

  const badge = resolveVerificationBadge(document);
  const StatusIcon = badge.icon;
  const entries = Object.entries(extractedFields);

  return (
    <section
      className="mt-4 rounded-xl border border-border/50 bg-secondary/20 p-3.5"
      aria-label="Document verification details"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h5 className="text-xs font-semibold text-foreground">Verification Result</h5>
        <span className={cn(
          'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium',
          badge.className,
        )}>
          <StatusIcon className="h-3.5 w-3.5" />
          {badge.label}
        </span>
      </div>

      {result?.validation_summary && (
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{result.validation_summary}</p>
      )}

      <div className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
        <span>
          Type: <strong className="text-foreground capitalize">{(document.doc_type || document.document_category || 'unknown').replaceAll('_', ' ')}</strong>
        </span>
        {confidencePct !== null && (
          <span>
            OCR confidence: <strong className="text-foreground">{confidencePct}%</strong>
          </span>
        )}
      </div>

      {entries.length > 0 && (
        <dl className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {entries.map(([field, value]) => (
            <div key={field} className="rounded-lg border border-border/40 bg-background/40 px-2.5 py-2">
              <dt className="text-[11px] capitalize text-muted-foreground">{field.replaceAll('_', ' ')}</dt>
              <dd className="mt-0.5 break-words text-xs font-medium text-foreground">{formatFieldValue(field, value)}</dd>
            </div>
          ))}
        </dl>
      )}

      {mismatches.length > 0 && (
        <div className="mt-3 rounded-lg border border-rose-500/25 bg-rose-500/8 p-2.5 space-y-1.5">
          <h6 className="text-xs font-semibold text-rose-300">Mismatch Reason{mismatches.length > 1 ? 's' : ''}</h6>
          {mismatches.map((mismatch, index) => (
            <p key={`${mismatch.field || 'issue'}-${index}`} className="text-xs text-rose-200/90">
              {mismatch.reason || mismatch.message}
              {mismatch.document_value !== undefined && mismatch.profile_value !== undefined && (
                <span className="block text-[11px] text-muted-foreground mt-0.5">
                  Document: <strong className="text-foreground">{String(mismatch.document_value)}</strong> · Profile: <strong className="text-foreground">{String(mismatch.profile_value)}</strong>
                </span>
              )}
            </p>
          ))}
        </div>
      )}

      {warnings.length > 0 && (
        <ul className="mt-3 space-y-1">
          {warnings.map((warning, index) => (
            <li key={index} className="flex gap-1.5 text-xs text-amber-200/85">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{warning}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};

export default DocumentVerificationPanel;
