import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, FileCheck2, Loader2, Plus, ShieldAlert } from 'lucide-react';
import api from '../lib/api';
import ApplicationCard from '../components/applications/ApplicationCard';
import ApplicationTimeline from '../components/applications/ApplicationTimeline';

const ApplicationsPage = () => {
  const { applicationId } = useParams();
  const [applications, setApplications] = useState([]);
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const activeRef = useRef(true);
  const applicationsRef = useRef(applications);
  const applicationStatusRef = useRef(application?.status);
  applicationsRef.current = applications;
  applicationStatusRef.current = application?.status;

  useEffect(() => {
    activeRef.current = true;
    setLoading(true);
    setError('');
    if (applicationId) setApplication(null);
    const load = async () => {
      try {
        if (applicationId) {
          const { data } = await api.get(`/applications/${applicationId}`);
          if (activeRef.current) setApplication(data);
        } else {
          const { data } = await api.get('/applications');
          if (activeRef.current) setApplications(data.applications || []);
        }
        if (activeRef.current) setError('');
      } catch (requestError) {
        if (activeRef.current) setError(requestError.response?.data?.detail || 'Applications could not be loaded. Please try again.');
      } finally {
        if (activeRef.current) setLoading(false);
      }
    };
    load();
    const interval = setInterval(() => {
      const isProgressing = applicationId
        ? ['submitted', 'under_review', 'ai_document_verification'].includes(applicationStatusRef.current)
        : applicationsRef.current.some(item => ['submitted', 'under_review', 'ai_document_verification'].includes(item.status));
      if (isProgressing) load();
    }, 5000);
    return () => {
      activeRef.current = false;
      clearInterval(interval);
    };
  }, [applicationId]);

  if (loading) return <div className="flex h-64 items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-primary" /></div>;

  if (applicationId) {
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <Link to="/applications" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> All applications</Link>
        {error && <div role="alert" className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-300">{error}</div>}
        {application && (
          <>
            <header className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary">{application.application_code}</p>
              <h1 className="mt-1 text-2xl font-bold text-foreground">{application.scheme_name}</h1>
              <p className="mt-2 text-sm text-muted-foreground">Saved {new Date(application.submitted_at).toLocaleString('en-IN')}</p>
              <div className="mt-5 flex items-center justify-between text-xs text-muted-foreground"><span>AidFlow package progress</span><strong className="text-foreground">{application.progress}%</strong></div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-secondary" role="progressbar" aria-label="AidFlow application package progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={application.progress}>
                <div className="h-full rounded-full bg-primary transition-[width] duration-500" style={{ width: `${application.progress}%` }} />
              </div>
              <p className="mt-3 text-xs text-muted-foreground">Progress covers AidFlow package preparation. External government review and decisions are not connected.</p>
            </header>

            <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
              <h2 className="mb-5 font-semibold text-foreground">Application timeline</h2>
              <ApplicationTimeline events={application.timeline} externalStages={application.external_stages} />
            </section>

            <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
              <h2 className="mb-4 font-semibold text-foreground">Attached document snapshots</h2>
              {application.documents.length === 0 ? (
                <p className="text-sm text-muted-foreground">No documents were attached to this package.</p>
              ) : (
                <ul className="space-y-3">
                  {application.documents.map(document => (
                    <li key={document.id} className="flex items-start gap-3 rounded-xl border border-border/50 bg-secondary/20 p-3">
                      {document.verification_status === 'preliminary_match'
                        ? <FileCheck2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                        : <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-foreground">{document.file_name}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{(document.document_category || 'general').replaceAll('_', ' ')} · {document.status}</p>
                        <p className="mt-1 text-xs text-muted-foreground">AI Preliminary Verification: {document.verification_status?.replaceAll('_', ' ') || 'not available'}{document.confidence_score != null ? ` · ${Math.round(document.confidence_score)}% confidence` : ''}</p>
                        {Object.entries(document.extracted_fields || {}).length > 0 && (
                          <p className="mt-2 text-xs text-foreground/80">{Object.entries(document.extracted_fields).map(([field, value]) => `${field.replaceAll('_', ' ')}: ${value}`).join(' · ')}</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-4 text-[11px] text-muted-foreground">AI checks are preliminary and are not government verification.</p>
            </section>

            <section className="rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
              <h2 className="mb-4 font-semibold text-foreground">Saved profile snapshot</h2>
              <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {Object.entries(application.profile_snapshot || {}).filter(([, value]) => value !== null && value !== '').map(([field, value]) => (
                  <div key={field} className="rounded-lg bg-secondary/25 px-3 py-2">
                    <dt className="text-[11px] capitalize text-muted-foreground">{field.replaceAll('_', ' ')}</dt>
                    <dd className="mt-0.5 text-sm text-foreground">{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}</dd>
                  </div>
                ))}
              </dl>
            </section>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Applications</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">Review AidFlow packages and track their in-app preparation status.</p>
        </div>
        <Link to="/schemes" className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground"><Plus className="h-4 w-4" /> Prepare application</Link>
      </header>
      {error && <div role="alert" className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 text-sm text-rose-300">{error}</div>}
      {!error && applications.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border p-10 text-center">
          <FileCheck2 className="mx-auto h-9 w-9 text-muted-foreground" />
          <h2 className="mt-3 font-semibold text-foreground">No application packages yet</h2>
          <p className="mt-1 text-sm text-muted-foreground">Choose a scheme to prepare and save your first package.</p>
          <Link to="/schemes" className="mt-4 inline-flex rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">Browse schemes</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {applications.map(item => <ApplicationCard key={item.id} application={item} />)}
        </div>
      )}
    </div>
  );
};

export default ApplicationsPage;
