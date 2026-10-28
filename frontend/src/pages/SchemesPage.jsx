import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, ChevronDown, ExternalLink, Calendar,
  Building2, MapPin, Loader2, ShieldCheck, X
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
          <div className="flex items-center gap-1.5 text-[11px] text-amber-400/80 bg-amber-500/8 px-2 py-1 rounded-lg">
            {scheme.deadline ? (
              <>
              <Calendar className="w-3 h-3" />
              {new Date(scheme.deadline).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
              </>
            ) : 'No deadline'}
          </div>
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

        <div className="bg-secondary/30 border border-border/30 rounded-xl px-3.5 py-2.5 mb-4">
          <p className="text-xs font-medium text-primary mb-0.5">Eligibility</p>
          <p className="text-xs text-muted-foreground line-clamp-2">{scheme.eligibility_summary}</p>
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

          <a
              href={scheme.application_url || undefined}
              aria-disabled={!scheme.application_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(event) => !scheme.application_url && event.preventDefault()}
              className={cn(
                'inline-flex items-center gap-1.5 text-xs font-medium transition-colors px-3 py-1.5 rounded-lg',
                scheme.application_url
                  ? 'text-primary hover:text-primary/80 bg-primary/8 hover:bg-primary/12'
                  : 'text-muted-foreground bg-secondary/50 cursor-not-allowed'
              )}
            >
              Apply
              {scheme.application_url && <ExternalLink className="w-3 h-3" />}
          </a>
        </div>
      </div>
    </motion.div>
  );
};

const SchemesPage = () => {
  const [schemes, setSchemes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    let active = true;
    const fetchSchemes = async () => {
      setLoading(true);
      setError('');
      try {
        const params = { per_page: 50 };
        if (selectedCategory !== 'All') params.category = selectedCategory;
        if (searchQuery.trim()) params.search = searchQuery.trim();
        const response = await api.get('/schemes', { params });
        if (active) {
          setSchemes(response.data.schemes || []);
          setTotal(response.data.total || 0);
        }
      } catch {
        if (active) {
          setSchemes([]);
          setTotal(0);
          setError('Schemes could not be loaded. Please try again.');
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    const timer = setTimeout(fetchSchemes, searchQuery ? 250 : 0);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [selectedCategory, searchQuery]);

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
          Browse {total} government welfare schemes. Find what you're eligible for.
        </p>
      </div>

      {/* Search + Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search schemes by name..."
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
            onClick={() => setSelectedCategory(cat)}
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
      ) : error ? (
        <p role="alert" className="text-sm text-red-400">{error}</p>
      ) : schemes.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 text-center">
          <Search className="w-10 h-10 text-muted-foreground/30 mb-3" />
          <p className="text-muted-foreground font-medium">No schemes found</p>
          <p className="text-sm text-muted-foreground/60 mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {schemes.map((scheme, index) => (
            <SchemeCard key={scheme.id} scheme={scheme} index={index} />
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default SchemesPage;
