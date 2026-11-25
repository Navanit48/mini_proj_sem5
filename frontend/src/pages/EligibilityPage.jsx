import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck, User, MapPin, Briefcase, IndianRupee,
  Loader2, CheckCircle2, XCircle, AlertCircle,
  Sparkles, RefreshCw, History,
  ChevronDown
} from 'lucide-react';
import api from '../lib/api';
import { cn } from '../lib/utils';
import { useAuth } from '../context/AuthContext';
import AIRecommendationPanel from '../components/eligibility/AIRecommendationPanel';

const getEligibilityStatus = (percentage) => {
  if (percentage >= 70) return 'Eligible';
  if (percentage >= 40) return 'Partially Eligible';
  return 'Not Eligible';
};

const STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Delhi', 'Jammu & Kashmir',
];

const OCCUPATIONS = [
  'farmer', 'labourer', 'daily-wage', 'self-employed', 'salaried',
  'student', 'unemployed', 'homemaker', 'retired', 'other',
];

const FormField = ({ label, children, required }) => (
  <label className="block space-y-1.5 text-sm font-medium text-foreground">
    <span>{label} {required && <span className="text-rose-400">*</span>}</span>
    {children}
  </label>
);

const inputClasses = "w-full px-3.5 py-2.5 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all";
const selectClasses = "w-full px-3.5 py-2.5 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all appearance-none cursor-pointer";

const ResultCard = ({ result, index, onCompleteProfile }) => {
  const [expanded, setExpanded] = useState(false);
  const pct = result.match_percentage;
  const status = getEligibilityStatus(pct);
  const isGoodMatch = pct >= 70;
  const isPartialMatch = pct >= 40 && pct < 70;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={cn(
        'bg-card border border-border/60 rounded-2xl overflow-hidden transition-colors duration-200',
        'hover:border-border/90'
      )}
    >
      <div className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-foreground leading-snug">{result.scheme_name}</h4>
          </div>
          <div className={cn(
            'shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold',
            isGoodMatch ? 'bg-emerald-500/12 text-emerald-400' :
            isPartialMatch ? 'bg-amber-500/12 text-amber-400' :
            'bg-rose-500/12 text-rose-400'
          )}>
            {isGoodMatch ? <CheckCircle2 className="w-3.5 h-3.5" /> :
             isPartialMatch ? <AlertCircle className="w-3.5 h-3.5" /> :
             <XCircle className="w-3.5 h-3.5" />}
            <span>{status}</span>
            <span className="opacity-70">{pct}%</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full h-1.5 bg-secondary/60 rounded-full mb-3 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.8, delay: 0.2 + index * 0.05, ease: [0.22, 1, 0.36, 1] }}
            className={cn(
              'h-full rounded-full',
              isGoodMatch ? 'bg-emerald-500' : isPartialMatch ? 'bg-amber-500' : 'bg-rose-500'
            )}
          />
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        >
          {expanded ? 'Hide details' : 'View rule breakdown'}
          <ChevronDown className={cn('w-3.5 h-3.5 transition-transform', expanded && 'rotate-180')} />
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="mt-3 space-y-2">
                {result.matched_rules?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-emerald-400 mb-1.5">✓ Matched</p>
                    {result.matched_rules.map((rule, i) => (
                      <p key={i} className="text-xs text-emerald-400/70 pl-3 py-0.5">• {rule}</p>
                    ))}
                  </div>
                )}
                {result.failed_rules?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-rose-400 mb-1.5">✗ Not matched</p>
                    {result.failed_rules.map((rule, i) => (
                      <p key={i} className="text-xs text-rose-400/70 pl-3 py-0.5">• {rule}</p>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <AIRecommendationPanel
          recommendation={result.ai_recommendation}
          onCompleteProfile={onCompleteProfile}
        />
      </div>
    </motion.div>
  );
};

const EligibilityPage = () => {
  const { user } = useAuth();
  const [step, setStep] = useState('form'); // form | loading | results
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const [profile, setProfile] = useState({
    full_name: '',
    date_of_birth: '',
    gender: '',
    state: '',
    district: '',
    occupation: '',
    category: '',
    annual_income: '',
    land_holding_acres: '',
    is_bpl: false,
    is_disabled: false,
  });

  useEffect(() => {
    const savedProfile = user?.profile;
    if (savedProfile) {
      setProfile(current => ({
        ...current,
        full_name: savedProfile.full_name || current.full_name,
        date_of_birth: savedProfile.date_of_birth || current.date_of_birth,
        gender: savedProfile.gender || current.gender,
        state: savedProfile.state || current.state,
        district: savedProfile.district || current.district,
        occupation: savedProfile.occupation || current.occupation,
        category: savedProfile.category || current.category,
        annual_income: savedProfile.annual_income ?? current.annual_income,
        land_holding_acres: savedProfile.land_holding_acres ?? current.land_holding_acres,
        is_bpl: savedProfile.is_bpl ?? current.is_bpl,
        is_disabled: savedProfile.is_disabled ?? current.is_disabled,
      }));
    }
  }, [user]);

  useEffect(() => {
    let active = true;
    api.get('/eligibility/history')
      .then(({ data }) => {
        if (active) setHistory(data.checks || []);
      })
      .catch(() => {
        if (active) setHistoryError('Could not load eligibility history.');
      })
      .finally(() => {
        if (active) setHistoryLoading(false);
      });
    return () => { active = false; };
  }, []);

  const updateField = (field, value) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setStep('loading');

    try {
      const payload = {
        ...profile,
        annual_income: profile.annual_income ? parseFloat(profile.annual_income) : null,
        land_holding_acres: profile.land_holding_acres ? parseFloat(profile.land_holding_acres) : null,
      };

      const response = await api.post('/eligibility/check', payload);
      setResults(response.data);
      setHistory(current => [response.data, ...current].slice(0, 20));
      setStep('results');
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Could not check eligibility. Please try again.');
      setStep('form');
    }
  };

  const resetForm = () => {
    setStep('form');
    setResults(null);
    setErrorMessage('');
  };

  const matchedCount = results?.results?.filter(r => r.match_percentage >= 70).length || 0;
  const partialCount = results?.results?.filter(r => r.match_percentage >= 40 && r.match_percentage < 70).length || 0;
  const totalCount = results?.results?.length || 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl sm:text-[28px] font-bold text-foreground tracking-tight">
            {step === 'results' ? 'Eligibility Results' : 'Check Eligibility'}
          </h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            {step === 'results'
              ? `${matchedCount} eligible · ${partialCount} partially eligible out of ${totalCount} schemes`
              : 'Fill in your profile to find schemes you qualify for'}
          </p>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <button
            type="button"
            onClick={() => setShowHistory(value => !value)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-muted-foreground bg-secondary/50 hover:bg-secondary transition-all"
          >
            <History className="w-4 h-4" />
            History
          </button>
          {step === 'results' && (
            <button
              type="button"
              onClick={resetForm}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-primary bg-primary/8 hover:bg-primary/14 transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              Check Again
            </button>
          )}
        </div>
      </div>

      {showHistory && (
        <div className="bg-card border border-border/50 rounded-2xl p-5 space-y-3">
          <h2 className="font-semibold text-foreground">Recent eligibility checks</h2>
          {historyLoading ? (
            <p className="text-sm text-muted-foreground">Loading history…</p>
          ) : historyError ? (
            <p className="text-sm text-rose-400">{historyError}</p>
          ) : history.length === 0 ? (
            <p className="text-sm text-muted-foreground">Your saved checks will appear here.</p>
          ) : (
            <div className="divide-y divide-border/40">
              {history.map(check => (
                <button
                  type="button"
                  key={check.check_id}
                  onClick={() => {
                    setResults(check);
                    setStep('results');
                    setShowHistory(false);
                  }}
                  className="w-full flex items-center justify-between gap-4 py-3 text-left hover:text-primary transition-colors"
                >
                  <span className="text-sm text-foreground">
                    {check.matched_count || 0} eligible scheme{check.matched_count === 1 ? '' : 's'}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {check.checked_at ? new Date(check.checked_at).toLocaleString() : ''}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {errorMessage && (
        <div role="alert" className="rounded-xl border border-rose-500/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-400">
          {errorMessage}
        </div>
      )}

      {/* Loading Animation */}
      <AnimatePresence mode="wait">
        {step === 'loading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex flex-col items-center justify-center py-24"
          >
            <div className="relative">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/10 flex items-center justify-center mb-6">
                <Sparkles className="w-8 h-8 text-primary animate-pulse" />
              </div>
              <motion.div
                className="absolute -inset-2 rounded-3xl border border-primary/20"
                animate={{ scale: [1, 1.1, 1], opacity: [0.5, 0.2, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Analyzing your profile...</h3>
            <p className="text-sm text-muted-foreground">Matching against all active government schemes</p>
          </motion.div>
        )}

        {/* Form */}
        {step === 'form' && (
          <motion.form
            key="form"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            onSubmit={handleSubmit}
            className="space-y-6"
          >
            {/* Personal Information */}
            <div className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="p-2 rounded-xl bg-primary/10">
                  <User className="w-4 h-4 text-primary" />
                </div>
                <h3 className="text-base font-semibold text-foreground">Personal Information</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <FormField label="Full Name">
                  <input type="text" value={profile.full_name} onChange={e => updateField('full_name', e.target.value)} className={inputClasses} placeholder="Enter your name" />
                </FormField>
                <FormField label="Date of Birth">
                  <input type="date" value={profile.date_of_birth} onChange={e => updateField('date_of_birth', e.target.value)} className={inputClasses} />
                </FormField>
                <FormField label="Gender" required>
                  <div className="relative">
                    <select value={profile.gender} onChange={e => updateField('gender', e.target.value)} className={selectClasses} required>
                      <option value="">Select gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                    <ChevronDown className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </FormField>
              </div>
            </div>

            {/* Location */}
            <div className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="p-2 rounded-xl bg-emerald-500/10">
                  <MapPin className="w-4 h-4 text-emerald-400" />
                </div>
                <h3 className="text-base font-semibold text-foreground">Location</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FormField label="State" required>
                  <div className="relative">
                    <select value={profile.state} onChange={e => updateField('state', e.target.value)} className={selectClasses} required>
                      <option value="">Select state</option>
                      {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <ChevronDown className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </FormField>
                <FormField label="District">
                  <input type="text" value={profile.district} onChange={e => updateField('district', e.target.value)} className={inputClasses} placeholder="Enter district" />
                </FormField>
              </div>
            </div>

            {/* Employment & Income */}
            <div className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6">
              <div className="flex items-center gap-2.5 mb-5">
                <div className="p-2 rounded-xl bg-amber-500/10">
                  <Briefcase className="w-4 h-4 text-amber-400" />
                </div>
                <h3 className="text-base font-semibold text-foreground">Employment & Income</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <FormField label="Occupation" required>
                  <div className="relative">
                    <select value={profile.occupation} onChange={e => updateField('occupation', e.target.value)} className={selectClasses} required>
                      <option value="">Select occupation</option>
                      {OCCUPATIONS.map(o => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1).replace(/-/g, ' ')}</option>)}
                    </select>
                    <ChevronDown className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </FormField>
                <FormField label="Category" required>
                  <div className="relative">
                    <select value={profile.category} onChange={e => updateField('category', e.target.value)} className={selectClasses} required>
                      <option value="">Select category</option>
                      <option value="general">General</option>
                      <option value="obc">OBC</option>
                      <option value="sc">SC</option>
                      <option value="st">ST</option>
                      <option value="ews">EWS</option>
                    </select>
                    <ChevronDown className="w-4 h-4 text-muted-foreground absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                </FormField>
                <FormField label="Annual Income (₹)" required>
                  <input
                    type="number"
                    value={profile.annual_income}
                    onChange={e => updateField('annual_income', e.target.value)}
                    className={inputClasses}
                    placeholder="e.g. 250000"
                    min="0"
                    required
                  />
                </FormField>
                <FormField label="Land Holding (acres)">
                  <input
                    type="number"
                    step="0.01"
                    value={profile.land_holding_acres}
                    onChange={e => updateField('land_holding_acres', e.target.value)}
                    className={inputClasses}
                    placeholder="e.g. 2.5"
                    min="0"
                  />
                </FormField>
              </div>

              {/* Checkboxes */}
              <div className="flex flex-wrap gap-6 mt-5 pt-4 border-t border-border/30">
                <label className="flex items-center gap-2.5 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={profile.is_bpl}
                    onChange={e => updateField('is_bpl', e.target.checked)}
                    className="w-4 h-4 rounded border-border bg-secondary text-primary focus:ring-primary/25"
                  />
                  <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">Below Poverty Line (BPL)</span>
                </label>
                <label className="flex items-center gap-2.5 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={profile.is_disabled}
                    onChange={e => updateField('is_disabled', e.target.checked)}
                    className="w-4 h-4 rounded border-border bg-secondary text-primary focus:ring-primary/25"
                  />
                  <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">Person with Disability</span>
                </label>
              </div>
            </div>

            {/* Submit */}
            <div className="flex justify-end">
              <button
                type="submit"
                className="inline-flex items-center gap-2 px-8 py-3 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 hover:shadow-primary/30"
              >
                <ShieldCheck className="w-4 h-4" />
                Check My Eligibility
              </button>
            </div>
          </motion.form>
        )}

        {/* Results */}
        {step === 'results' && results && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="space-y-6"
          >
            <section className="overflow-hidden rounded-2xl border border-border/60 bg-card p-5 sm:p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-border/60 bg-secondary/70">
                    <Sparkles className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-foreground">Your AI Summary</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Based on your profile and {results.ai_summary?.evaluated_count ?? totalCount} evaluated scheme rules.
                    </p>
                  </div>
                </div>
                <div className="min-w-36 rounded-xl border border-border/60 bg-secondary/25 px-4 py-2.5">
                  <p className="text-xs text-muted-foreground">Overall Profile Strength</p>
                  <p className="mt-0.5 text-2xl font-bold text-primary">
                    {results.ai_summary?.profile_strength ?? 0}%
                  </p>
                </div>
              </div>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl border border-border/50 bg-secondary/20 p-4">
                  <h3 className="text-sm font-semibold text-foreground">You qualify for</h3>
                  {results.ai_summary?.eligible_schemes?.length ? (
                    <ul className="mt-2 space-y-1 text-sm text-foreground/85">
                      {results.ai_summary.eligible_schemes.map((name) => <li key={name}>• {name}</li>)}
                    </ul>
                  ) : (
                    <p className="mt-2 text-sm text-muted-foreground">No evaluated scheme currently meets the eligible threshold.</p>
                  )}
                </div>
                <div className="rounded-xl border border-border/50 bg-secondary/20 p-4">
                  <h3 className="text-sm font-semibold text-foreground">You narrowly miss</h3>
                  {results.ai_summary?.near_misses?.length ? (
                    <ul className="mt-2 space-y-1 text-sm text-foreground/85">
                      {results.ai_summary.near_misses.map((name) => <li key={name}>• {name}</li>)}
                    </ul>
                  ) : (
                    <p className="mt-2 text-sm text-muted-foreground">No scheme is currently in the near-miss range.</p>
                  )}
                </div>
              </div>
            </section>

            {/* Result Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.results.map((result, index) => (
                <ResultCard
                  key={result.scheme_id}
                  result={result}
                  index={index}
                  onCompleteProfile={resetForm}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default EligibilityPage;
