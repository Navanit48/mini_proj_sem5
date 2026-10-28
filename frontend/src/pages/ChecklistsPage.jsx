import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckSquare, Plus, Loader2, CheckCircle2, Circle,
  ChevronDown, ChevronRight, Sparkles, Clock, AlertCircle,
  Trash2, ExternalLink, ListChecks
} from 'lucide-react';
import api from '../lib/api';
import { cn } from '../lib/utils';

// Demo data
const DEMO_CHECKLISTS = [
  {
    id: 'cl1',
    scheme_id: 's1',
    scheme_name: 'Pradhan Mantri Awas Yojana',
    status: 'active',
    created_at: '2026-10-10T10:00:00Z',
    updated_at: '2026-10-22T10:00:00Z',
    items: [
      { id: 'i1', title: 'Collect Income Certificate', description: 'Obtain from Tehsildar office. Must be for current financial year.', is_completed: true, due_date: '2026-10-15', sort_order: 0, completed_at: '2026-10-14T10:00:00Z' },
      { id: 'i2', title: 'Upload Aadhaar Card copy', description: 'Both front and back. Must be linked to mobile number.', is_completed: true, due_date: '2026-10-18', sort_order: 1, completed_at: '2026-10-16T10:00:00Z' },
      { id: 'i3', title: 'Get BPL Certificate', description: 'Issued by Block Development Officer. Valid for 1 year.', is_completed: false, due_date: '2026-10-25', sort_order: 2, completed_at: null },
      { id: 'i4', title: 'Fill online application form', description: 'Visit pmaymis.gov.in and complete the application with all details.', is_completed: false, due_date: '2026-10-28', sort_order: 3, completed_at: null },
      { id: 'i5', title: 'Submit physical documents at CSC', description: 'Visit nearest Common Service Centre with all original documents.', is_completed: false, due_date: '2026-11-01', sort_order: 4, completed_at: null },
    ],
  },
  {
    id: 'cl2',
    scheme_id: 's3',
    scheme_name: 'Ayushman Bharat - PMJAY',
    status: 'active',
    created_at: '2026-10-18T10:00:00Z',
    updated_at: '2026-10-20T10:00:00Z',
    items: [
      { id: 'i6', title: 'Check name in beneficiary list', description: 'Visit mera.pmjay.gov.in and search with Aadhaar/mobile.', is_completed: true, due_date: null, sort_order: 0, completed_at: '2026-10-18T14:00:00Z' },
      { id: 'i7', title: 'Visit empanelled hospital for e-KYC', description: 'Carry Aadhaar and ration card for biometric verification.', is_completed: false, due_date: '2026-10-30', sort_order: 1, completed_at: null },
      { id: 'i8', title: 'Collect Ayushman Card', description: 'Golden card will be issued after verification. Keep safely.', is_completed: false, due_date: '2026-11-05', sort_order: 2, completed_at: null },
    ],
  },
  {
    id: 'cl3',
    scheme_id: 's6',
    scheme_name: 'Post-Matric Scholarship',
    status: 'completed',
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-10-05T10:00:00Z',
    items: [
      { id: 'i9', title: 'Register on National Scholarship Portal', description: 'Create account at scholarships.gov.in', is_completed: true, due_date: '2026-09-10', sort_order: 0, completed_at: '2026-09-08T10:00:00Z' },
      { id: 'i10', title: 'Upload caste certificate and marksheet', description: 'Scan and upload in PDF format under 2MB.', is_completed: true, due_date: '2026-09-15', sort_order: 1, completed_at: '2026-09-14T10:00:00Z' },
      { id: 'i11', title: 'Get institute verification', description: 'Submit printed application to college admin.', is_completed: true, due_date: '2026-09-25', sort_order: 2, completed_at: '2026-09-22T10:00:00Z' },
    ],
  },
];

const ChecklistCard = ({ checklist, onToggleItem }) => {
  const [expanded, setExpanded] = useState(checklist.status === 'active');
  const completedItems = checklist.items.filter(i => i.is_completed).length;
  const totalItems = checklist.items.length;
  const progress = totalItems > 0 ? (completedItems / totalItems) * 100 : 0;
  const isComplete = checklist.status === 'completed';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'bg-card border rounded-2xl overflow-hidden transition-all duration-300',
        isComplete ? 'border-emerald-500/20' : 'border-border/50 hover:border-border/80'
      )}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-5 sm:p-6 flex items-center gap-4 text-left"
      >
        <div className={cn(
          'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
          isComplete ? 'bg-emerald-500/12' : 'bg-primary/10'
        )}>
          {isComplete ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <ListChecks className="w-5 h-5 text-primary" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-foreground truncate">{checklist.scheme_name}</h3>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-xs text-muted-foreground">{completedItems}/{totalItems} tasks</span>
            <span className={cn(
              'text-[11px] font-medium px-2 py-0.5 rounded-md',
              isComplete ? 'bg-emerald-500/10 text-emerald-400' : 'bg-primary/10 text-primary'
            )}>
              {isComplete ? 'Completed' : `${Math.round(progress)}%`}
            </span>
          </div>
        </div>

        <ChevronDown className={cn('w-5 h-5 text-muted-foreground transition-transform duration-200 shrink-0', expanded && 'rotate-180')} />
      </button>

      {/* Progress bar */}
      <div className="px-5 sm:px-6">
        <div className="w-full h-1 bg-secondary/60 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className={cn('h-full rounded-full', isComplete ? 'bg-emerald-500' : 'bg-primary')}
          />
        </div>
      </div>

      {/* Items */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-5 sm:px-6 pb-5 sm:pb-6 pt-4 space-y-1">
              {checklist.items
                .sort((a, b) => a.sort_order - b.sort_order)
                .map((item, index) => (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.03 }}
                    className={cn(
                      'flex items-start gap-3 p-3 rounded-xl transition-colors group',
                      'hover:bg-secondary/30',
                      item.is_completed && 'opacity-60'
                    )}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleItem(checklist.id, item.id, !item.is_completed);
                      }}
                      className="mt-0.5 shrink-0"
                    >
                      {item.is_completed ? (
                        <CheckCircle2 className="w-[18px] h-[18px] text-emerald-400" />
                      ) : (
                        <Circle className="w-[18px] h-[18px] text-muted-foreground/40 group-hover:text-muted-foreground/60 transition-colors" />
                      )}
                    </button>

                    <div className="flex-1 min-w-0">
                      <p className={cn(
                        'text-sm font-medium text-foreground leading-snug',
                        item.is_completed && 'line-through text-muted-foreground'
                      )}>
                        {item.title}
                      </p>
                      {item.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{item.description}</p>
                      )}
                    </div>

                    {item.due_date && (
                      <div className={cn(
                        'shrink-0 flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md',
                        item.is_completed
                          ? 'text-muted-foreground/60'
                          : new Date(item.due_date) < new Date()
                            ? 'text-rose-400 bg-rose-500/8'
                            : 'text-muted-foreground bg-secondary/40'
                      )}>
                        <Clock className="w-3 h-3" />
                        {new Date(item.due_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                      </div>
                    )}
                  </motion.div>
                ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const ChecklistsPage = () => {
  const [checklists, setChecklists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, active, completed

  useEffect(() => {
    fetchChecklists();
  }, []);

  const fetchChecklists = async () => {
    try {
      const response = await api.get('/checklists');
      setChecklists(response.data.checklists || []);
    } catch (error) {
      console.error('Failed to load checklists, using demo', error);
      setChecklists(DEMO_CHECKLISTS);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleItem = async (checklistId, itemId, isCompleted) => {
    // Optimistic update
    setChecklists(prev =>
      prev.map(cl => {
        if (cl.id !== checklistId) return cl;
        const updatedItems = cl.items.map(item =>
          item.id === itemId
            ? { ...item, is_completed: isCompleted, completed_at: isCompleted ? new Date().toISOString() : null }
            : item
        );
        const allDone = updatedItems.every(i => i.is_completed);
        return { ...cl, items: updatedItems, status: allDone ? 'completed' : 'active' };
      })
    );

    try {
      await api.patch(`/checklists/${checklistId}/items/${itemId}`, { is_completed: isCompleted });
    } catch (error) {
      console.error('Failed to update item (demo mode)', error);
    }
  };

  const filteredChecklists = checklists.filter(cl => {
    if (filter === 'active') return cl.status === 'active';
    if (filter === 'completed') return cl.status === 'completed';
    return true;
  });

  const totalTasks = checklists.reduce((acc, cl) => acc + cl.items.length, 0);
  const completedTasks = checklists.reduce((acc, cl) => acc + cl.items.filter(i => i.is_completed).length, 0);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-[28px] font-bold text-foreground tracking-tight">Checklists</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          AI-generated step-by-step application guides for your matched schemes.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl p-4 border border-border/30 bg-secondary/50">
          <p className="text-xs text-muted-foreground font-medium">Total Checklists</p>
          <p className="text-2xl font-bold text-foreground mt-1">{checklists.length}</p>
        </div>
        <div className="rounded-xl p-4 border border-border/30 bg-primary/6">
          <p className="text-xs text-muted-foreground font-medium">Active</p>
          <p className="text-2xl font-bold text-primary mt-1">{checklists.filter(c => c.status === 'active').length}</p>
        </div>
        <div className="rounded-xl p-4 border border-border/30 bg-emerald-500/6">
          <p className="text-xs text-muted-foreground font-medium">Completed Tasks</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{completedTasks}/{totalTasks}</p>
        </div>
        <div className="rounded-xl p-4 border border-border/30 bg-amber-500/6">
          <p className="text-xs text-muted-foreground font-medium">Pending Tasks</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">{totalTasks - completedTasks}</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {[
          { key: 'all', label: 'All' },
          { key: 'active', label: 'Active' },
          { key: 'completed', label: 'Completed' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={cn(
              'px-4 py-2 rounded-xl text-xs font-medium transition-all border',
              filter === tab.key
                ? 'bg-primary/12 text-primary border-primary/20'
                : 'bg-secondary/40 text-muted-foreground border-border/30 hover:bg-secondary/70'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Checklists */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-7 h-7 animate-spin text-primary" />
        </div>
      ) : filteredChecklists.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary/60 flex items-center justify-center mb-4">
            <CheckSquare className="w-7 h-7 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground font-medium">No checklists yet</p>
          <p className="text-sm text-muted-foreground/60 mt-1">
            Checklists are generated when you match with eligible schemes
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredChecklists.map((checklist) => (
            <ChecklistCard
              key={checklist.id}
              checklist={checklist}
              onToggleItem={handleToggleItem}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default ChecklistsPage;
