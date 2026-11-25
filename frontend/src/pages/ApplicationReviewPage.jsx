import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, Check, FileText, Loader2, ShieldCheck } from 'lucide-react';
import api from '../lib/api';

const profileFields = [
  { key: 'full_name', label: 'Full name', type: 'text' },
  { key: 'date_of_birth', label: 'Date of birth', type: 'date' },
  { key: 'gender', label: 'Gender', type: 'select', options: [['', 'Select'], ['female', 'Female'], ['male', 'Male'], ['other', 'Other']] },
  { key: 'state', label: 'State', type: 'text' },
  { key: 'district', label: 'District', type: 'text' },
  { key: 'occupation', label: 'Occupation', type: 'text' },
  { key: 'category', label: 'Social category', type: 'select', options: [['', 'Select'], ['general', 'General'], ['obc', 'OBC'], ['sc', 'SC'], ['st', 'ST'], ['ews', 'EWS']] },
  { key: 'annual_income', label: 'Annual income (₹)', type: 'number' },
  { key: 'land_holding_acres', label: 'Land holding (acres)', type: 'number' },
];

const ApplicationReviewPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const schemeId = searchParams.get('scheme_id');
  const [preview, setPreview] = useState(null);
  const [profile, setProfile] = useState({});
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    if (!schemeId) {
      setError('Choose a scheme before preparing an application.');
      setLoading(false);
      return () => { active = false; };
    }
    api.post('/applications/preview', { scheme_id: schemeId })
      .then(({ data }) => {
        if (!active) return;
        setPreview(data);
        setProfile(data.profile || {});
        setSelectedDocuments((data.documents || []).map(document => document.id));
      })
      .catch((requestError) => {
        if (active) setError(requestError.response?.data?.detail || 'Application details could not be loaded.');
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [schemeId]);

  const updateProfile = (field, value) => setProfile(current => ({ ...current, [field]: value }));
  const toggleDocument = (id) => setSelectedDocuments(current => (
    current.includes(id) ? current.filter(item => item !== id) : [...current, id]
  ));

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    const overrides = {};
    for (const field of profileFields) {
      const value = profile[field.key];
      if (value === undefined) continue;
      if (value === null || value === '') {
        overrides[field.key] = null;
        continue;
      }
      overrides[field.key] = field.type === 'number' ? Number(value) : value;
    }
    overrides.is_bpl = Boolean(profile.is_bpl);
    overrides.is_disabled = Boolean(profile.is_disabled);
    try {
      const { data } = await api.post('/applications', {
        scheme_id: schemeId,
        profile_overrides: overrides,
        document_ids: selectedDocuments,
        eligibility_check_id: preview?.eligibility?.check_id || null,
      });
      navigate(`/applications/${data.id}`);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Application package could not be saved. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="flex h-64 items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-primary" /></div>;
  if (error && !preview) return <div role="alert" className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-300">{error}</div>;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <button type="button" onClick={() => navigate('/schemes')} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to schemes
      </button>
      <header>
        <p className="text-xs font-semibold uppercase tracking-wide text-primary">AidFlow application package</p>
        <h1 className="mt-1 text-2xl font-bold text-foreground">Review your application</h1>
        <p className="mt-2 text-sm text-muted-foreground">Check the information and documents before saving this package to AidFlow.</p>
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-300">{error}</div>}
      <div className="flex gap-3 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-amber-100/80">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-300" />
        <p>{preview?.notice} AidFlow does not send this package to a government portal.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
          <div className="mb-5 flex items-start gap-3">
            <div className="rounded-xl bg-secondary p-2.5 text-primary"><FileText className="h-5 w-5" /></div>
            <div className="min-w-0">
              <h2 className="font-semibold text-foreground">{preview.scheme.name}</h2>
              <p className="mt-1 text-xs text-muted-foreground">{preview.scheme.ministry} · {preview.scheme.category}</p>
            </div>
          </div>
          {preview.eligibility?.status ? (
            <div className="rounded-xl border border-border/50 bg-secondary/25 p-3 text-sm">
              <div className="flex items-center gap-2 font-medium text-foreground"><ShieldCheck className="h-4 w-4 text-primary" />Saved eligibility result: {preview.eligibility.status} ({preview.eligibility.match_percentage}%)</div>
              <p className="mt-1 text-xs text-muted-foreground">{preview.eligibility.notice}</p>
            </div>
          ) : (
            <p className="rounded-xl border border-border/50 bg-secondary/25 p-3 text-xs text-muted-foreground">No saved eligibility result is available for this scheme. This package does not make an eligibility decision.</p>
          )}
        </section>

        <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
          <div className="mb-4">
            <h2 className="font-semibold text-foreground">Profile information</h2>
            <p className="mt-1 text-xs text-muted-foreground">Pre-filled from your saved profile. Edits here apply to this package only.</p>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {profileFields.map((field) => (
              <label key={field.key} className="space-y-1.5 text-xs font-medium text-muted-foreground">
                <span>{field.label}</span>
                {field.type === 'select' ? (
                  <select value={profile[field.key] || ''} onChange={event => updateProfile(field.key, event.target.value)} className="w-full rounded-xl border border-border bg-secondary/40 px-3 py-2.5 text-sm text-foreground">
                    {field.options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                ) : (
                  <input type={field.type} step={field.type === 'number' ? 'any' : undefined} value={profile[field.key] ?? ''} onChange={event => updateProfile(field.key, event.target.value)} className="w-full rounded-xl border border-border bg-secondary/40 px-3 py-2.5 text-sm text-foreground" />
                )}
              </label>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-4">
            {[["is_bpl", "BPL household"], ["is_disabled", "Person with disability"]].map(([key, label]) => (
              <label key={key} className="flex items-center gap-2 text-sm text-foreground">
                <input type="checkbox" checked={Boolean(profile[key])} onChange={event => updateProfile(key, event.target.checked)} className="h-4 w-4 accent-[hsl(var(--primary))]" />{label}
              </label>
            ))}
          </div>
          {preview.missing_profile_fields?.length > 0 && (
            <p className="mt-4 text-xs text-amber-300">Some saved profile fields are empty: {preview.missing_profile_fields.map(field => field.replaceAll('_', ' ')).join(', ')}.</p>
          )}
          <p className="mt-3 text-xs text-muted-foreground">Changing these values updates this application snapshot only. Run eligibility again if you want a result based on the edits.</p>
        </section>

        <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
          <div className="mb-4">
            <h2 className="font-semibold text-foreground">Attach documents</h2>
            <p className="mt-1 text-xs text-muted-foreground">Choose files to include. Their preliminary checks remain guidance only.</p>
          </div>
          {preview.documents.length ? (
            <div className="space-y-2">
              {preview.documents.map(document => (
                <label key={document.id} className="flex cursor-pointer items-start gap-3 rounded-xl border border-border/50 bg-secondary/20 p-3">
                  <input type="checkbox" checked={selectedDocuments.includes(document.id)} onChange={() => toggleDocument(document.id)} className="mt-1 h-4 w-4 accent-[hsl(var(--primary))]" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-foreground">{document.file_name}</span>
                    <span className="mt-0.5 block text-xs text-muted-foreground">{(document.document_category || 'general').replaceAll('_', ' ')} · {document.status}</span>
                    {document.verification && <span className="mt-1 block text-xs text-muted-foreground">AI Preliminary Verification: {document.verification.verification_status.replaceAll('_', ' ')}</span>}
                  </span>
                  {document.verification?.verification_status === 'preliminary_match' && <Check className="mt-0.5 h-4 w-4 text-emerald-400" />}
                </label>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">No documents uploaded yet. You can save this package and attach documents later through the Documents page.</div>
          )}
        </section>

        <button type="submit" disabled={submitting} className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60">
          {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
          Submit package to AidFlow
        </button>
      </form>
    </div>
  );
};

export default ApplicationReviewPage;
