import React, { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Filter, ChevronDown, ExternalLink, Calendar,
  Building2, MapPin, Loader2, ShieldCheck, ArrowRight,
  X, Bookmark, Clock, Sparkles
} from 'lucide-react';
import api from '../lib/api';
import { cn } from '../lib/utils';

const CATEGORIES = [
  'All', 'Housing', 'Agriculture', 'Healthcare', 'Education',
  'Employment', 'Food Security', 'Women & Child', 'Entrepreneurship',
  'Energy', 'Social Security',
];

const categoryColors = {
  Housing: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
  Agriculture: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  Healthcare: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20' },
  Education: { bg: 'bg-violet-500/10', text: 'text-violet-400', border: 'border-violet-500/20' },
  Employment: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
  'Food Security': { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20' },
  'Women & Child': { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20' },
  Entrepreneurship: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20' },
  Energy: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
  'Social Security': { bg: 'bg-teal-500/10', text: 'text-teal-400', border: 'border-teal-500/20' },
};

// Fallback demo data
const DEMO_SCHEMES = [
  { id: '1', name: 'Pradhan Mantri Awas Yojana (PMAY)', slug: 'pmay', description: 'Housing for All mission providing affordable housing to urban and rural poor families across India.', ministry: 'Ministry of Housing and Urban Affairs', category: 'Housing', target_states: ['All India'], benefits_summary: 'Interest subsidy of 6.5% on home loans up to ₹6 lakh for 20 years.', eligibility_summary: 'Annual household income below ₹3 lakh (EWS) or ₹6 lakh (LIG).', application_url: 'https://pmaymis.gov.in', deadline: '2027-03-31', is_active: true, created_at: new Date().toISOString() },
  { id: '2', name: 'PM Kisan Samman Nidhi', slug: 'pm-kisan', description: 'Direct income support of ₹6,000 per year to all landholding farmer families.', ministry: 'Ministry of Agriculture', category: 'Agriculture', target_states: ['All India'], benefits_summary: '₹6,000/year in 3 installments of ₹2,000.', eligibility_summary: 'Small and marginal farmers with cultivable land holding.', application_url: 'https://pmkisan.gov.in', deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '3', name: 'Ayushman Bharat - PMJAY', slug: 'ayushman-bharat', description: 'Health insurance of ₹5 lakh per family per year for secondary and tertiary care hospitalization.', ministry: 'Ministry of Health and Family Welfare', category: 'Healthcare', target_states: ['All India'], benefits_summary: '₹5 lakh health coverage. 1,393 medical packages covered.', eligibility_summary: 'BPL families. Rural and urban poor.', application_url: 'https://pmjay.gov.in', deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '4', name: 'Post-Matric Scholarship for SC Students', slug: 'post-matric-sc', description: 'Scholarship for SC students pursuing post-matriculation education.', ministry: 'Ministry of Social Justice', category: 'Education', target_states: ['All India'], benefits_summary: 'Full tuition fee + ₹500–₹1,200 maintenance allowance.', eligibility_summary: 'SC category. Family income below ₹2.5 lakh.', application_url: 'https://scholarships.gov.in', deadline: '2027-01-31', is_active: true, created_at: new Date().toISOString() },
  { id: '5', name: 'MGNREGA', slug: 'mgnrega', description: '100 days guaranteed wage employment for rural households.', ministry: 'Ministry of Rural Development', category: 'Employment', target_states: ['All India'], benefits_summary: '100 days guaranteed wages. Unemployment allowance.', eligibility_summary: 'Rural adult willing to do unskilled manual work.', application_url: 'https://nrega.nic.in', deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '6', name: 'Stand-Up India', slug: 'stand-up-india', description: 'Bank loans ₹10L–₹1Cr for SC/ST and women entrepreneurs.', ministry: 'Ministry of Finance', category: 'Entrepreneurship', target_states: ['All India'], benefits_summary: 'Loans ₹10L to ₹1Cr. Repayment up to 7 years.', eligibility_summary: 'SC/ST or Women entrepreneur. Age 18+.', application_url: 'https://www.standupmitra.in', deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '7', name: 'National Food Security Act (NFSA)', slug: 'nfsa', description: 'Subsidized food grains through PDS.', ministry: 'Ministry of Consumer Affairs', category: 'Food Security', target_states: ['All India'], benefits_summary: 'Rice ₹3/kg, wheat ₹2/kg. 5kg per person/month.', eligibility_summary: 'BPL families. Income below ₹1 lakh.', application_url: 'https://nfsa.gov.in', deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '8', name: 'Sukanya Samriddhi Yojana', slug: 'sukanya', description: 'Girl child savings scheme with high interest rates.', ministry: 'Ministry of Finance', category: 'Women & Child', target_states: ['All India'], benefits_summary: '8.2% interest. Tax free under 80C.', eligibility_summary: 'Girl child below 10 years. Max 2 accounts/family.', application_url: null, deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '9', name: 'Ujjwala Yojana 2.0', slug: 'ujjwala', description: 'Free LPG connections for BPL women.', ministry: 'Ministry of Petroleum', category: 'Energy', target_states: ['All India'], benefits_summary: 'Free LPG connection, cylinder, regulator, and stove.', eligibility_summary: 'BPL women. Age 18+. No existing LPG connection.', application_url: null, deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '10', name: 'Atal Pension Yojana', slug: 'apy', description: 'Pension scheme for unorganized sector workers.', ministry: 'Ministry of Finance', category: 'Social Security', target_states: ['All India'], benefits_summary: '₹1,000–₹5,000/month pension. 50% govt co-contribution.', eligibility_summary: 'Age 18–40. Bank account with Aadhaar.', application_url: null, deadline: null, is_active: true, created_at: new Date().toISOString() },
  { id: '11', name: 'PM Fasal Bima Yojana', slug: 'pmfby', description: 'Comprehensive crop insurance for farmers.', ministry: 'Ministry of Agriculture', category: 'Agriculture', target_states: ['All India'], benefits_summary: '2% premium for Kharif. Full insured amount on crop loss.', eligibility_summary: 'All farmers including sharecroppers.', application_url: 'https://pmfby.gov.in', deadline: '2027-06-30', is_active: true, created_at: new Date().toISOString() },
  { id: '12', name: 'Digital India Internship', slug: 'digital-india', description: 'Internship for engineering students in govt digital projects.', ministry: 'Ministry of Electronics and IT', category: 'Education', target_states: ['All India'], benefits_summary: '₹10,000/month stipend. Certificate.', eligibility_summary: 'B.Tech/M.Tech/MCA. CGPA > 7.0.', application_url: null, deadline: '2027-02-28', is_active: true, created_at: new Date().toISOString() },
];

const SchemeCard = ({ scheme, index }) => {
  const [expanded, setExpanded] = useState(false);
  const colors = categoryColors[scheme.category] || categoryColors.Housing;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.04, ease: [0.25, 0.46, 0.45, 0.94] }}
      layout
      className="bg-card border border-border/50 rounded-2xl overflow-hidden hover:border-border/80 hover:shadow-lg hover:shadow-black/10 transition-all duration-300 group"
    >
      <div className="p-5 sm:p-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className={cn('px-2.5 py-1 rounded-lg text-[11px] font-semibold border', colors.bg, colors.text, colors.border)}>
            {scheme.category}
          </div>
          {scheme.deadline && (
            <div className="flex items-center gap-1.5 text-[11px] text-amber-400/80 bg-amber-500/8 px-2 py-1 rounded-lg">
              <Calendar className="w-3 h-3" />
              {new Date(scheme.deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
            </div>
          )}
        </div>

        {/* Title */}
        <h3 className="text-[15px] font-semibold text-foreground leading-snug mb-2 group-hover:text-primary transition-colors duration-200">
          {scheme.name}
        </h3>

        {/* Ministry */}
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-3">
          <Building2 className="w-3.5 h-3.5 shrink-0" />
          <span className="truncate">{scheme.ministry}</span>
        </div>

        {/* Description */}
        <p className="text-sm text-muted-foreground/80 leading-relaxed mb-4 line-clamp-2">
          {scheme.description}
        </p>

        {/* Benefits Preview */}
        <div className="bg-emerald-500/6 border border-emerald-500/10 rounded-xl px-3.5 py-2.5 mb-4">
          <p className="text-xs font-medium text-emerald-400 mb-0.5">Benefits</p>
          <p className="text-xs text-emerald-400/70 line-clamp-2">{scheme.benefits_summary}</p>
        </div>

        {/* Expanded section */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden"
            >
              <div className="bg-secondary/30 border border-border/30 rounded-xl px-3.5 py-2.5 mb-4">
                <p className="text-xs font-medium text-primary mb-0.5">Eligibility</p>
                <p className="text-xs text-muted-foreground">{scheme.eligibility_summary}</p>
              </div>

              {scheme.target_states?.length > 0 && (
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-4">
                  <MapPin className="w-3.5 h-3.5 shrink-0" />
                  <span>{Array.isArray(scheme.target_states) ? scheme.target_states.join(', ') : scheme.target_states}</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Actions */}
        <div className="flex items-center justify-between pt-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            {expanded ? 'Show less' : 'View details'}
            <ChevronDown className={cn('w-3.5 h-3.5 transition-transform duration-200', expanded && 'rotate-180')} />
          </button>

          {scheme.application_url && (
            <a
              href={scheme.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors px-3 py-1.5 rounded-lg bg-primary/8 hover:bg-primary/12"
            >
              Apply
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
};

const SchemesPage = () => {
  const [schemes, setSchemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    const fetchSchemes = async () => {
      try {
        const params = {};
        if (selectedCategory !== 'All') params.category = selectedCategory;
        const response = await api.get('/schemes', { params });
        setSchemes(response.data.schemes || response.data);
      } catch (error) {
        console.error('Failed to load schemes, using demo data', error);
        setSchemes(DEMO_SCHEMES);
      } finally {
        setLoading(false);
      }
    };
    fetchSchemes();
  }, [selectedCategory]);

  const filteredSchemes = useMemo(() => {
    if (!searchQuery.trim()) return schemes;
    const q = searchQuery.toLowerCase();
    return schemes.filter(s =>
      s.name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q) ||
      s.ministry.toLowerCase().includes(q) ||
      s.category.toLowerCase().includes(q)
    );
  }, [schemes, searchQuery]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-foreground tracking-tight">
          Discover Schemes
        </h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Browse {filteredSchemes.length} government welfare schemes. Find what you're eligible for.
        </p>
      </div>

      {/* Search + Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search schemes by name, ministry, or keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all"
            id="schemes-search"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Category Chips */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => { setSelectedCategory(cat); setLoading(true); }}
            className={cn(
              'px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all duration-200 border',
              selectedCategory === cat
                ? 'bg-primary/12 text-primary border-primary/20'
                : 'bg-secondary/40 text-muted-foreground border-border/30 hover:bg-secondary/70 hover:text-foreground'
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Schemes Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-7 h-7 animate-spin text-primary" />
        </div>
      ) : filteredSchemes.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 text-center">
          <Search className="w-10 h-10 text-muted-foreground/30 mb-3" />
          <p className="text-muted-foreground font-medium">No schemes found</p>
          <p className="text-sm text-muted-foreground/60 mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredSchemes.map((scheme, index) => (
            <SchemeCard key={scheme.id} scheme={scheme} index={index} />
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default SchemesPage;
