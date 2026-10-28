import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckSquare, Plus, Loader2, CheckCircle2, Circle,
  ChevronDown, Clock, ListChecks
} from 'lucide-react';
import api from '../lib/api';
import { cn } from '../lib/utils';

const ChecklistCard = ({ checklist, onToggleItem, pendingItems }) => {
  const [expanded, setExpanded] = useState(checklist.status === 'active');
  const items = checklist.items || [];
  const completedItems = items.filter(i => i.is_completed).length;
  const totalItems = items.length;
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
              {[...items]
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
                      type="button"
                      disabled={pendingItems[`${checklist.id}:${item.id}`]}
                      aria-label={`${item.is_completed ? 'Mark incomplete' : 'Mark complete'}: ${item.title}`}
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
  const [schemes, setSchemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, active, completed
  const [selectedSchemeId, setSelectedSchemeId] = useState('');
  const [creating, setCreating] = useState(false);
  const [pendingItems, setPendingItems] = useState({});
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([api.get('/checklists'), api.get('/schemes', { params: { per_page: 50 } })])
      .then(([checklistResponse, schemeResponse]) => {
        if (!active) return;
        setChecklists(checklistResponse.data.checklists || []);
        setSchemes(schemeResponse.data.schemes || []);
      })
      .catch(() => {
        if (active) setLoadError('Checklists and schemes could not be loaded. Please refresh and try again.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, []);

  const handleCreateChecklist = async (event) => {
    event.preventDefault();
    if (!selectedSchemeId) return;
    setCreating(true);
    setActionError('');
    try {
      const response = await api.post('/checklists/generate', { scheme_id: selectedSchemeId });
      setChecklists(current => [response.data, ...current]);
      setSelectedSchemeId('');
    } catch (error) {
      setActionError(error.response?.data?.detail || 'Could not create this checklist. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleItem = async (checklistId, itemId, isCompleted) => {
    const pendingKey = `${checklistId}:${itemId}`;
    const previousItem = checklists
      .find(checklist => checklist.id === checklistId)
      ?.items.find(item => item.id === itemId);
    setActionError('');
    setPendingItems(current => ({ ...current, [pendingKey]: true }));
    setChecklists(prev =>
      prev.map(cl => {
        if (cl.id !== checklistId) return cl;
        const updatedItems = cl.items.map(item =>
          item.id === itemId
            ? { ...item, is_completed: isCompleted, completed_at: isCompleted ? new Date().toISOString() : null }
            : item
        );
        const allDone = updatedItems.length > 0 && updatedItems.every(i => i.is_completed);
        return { ...cl, items: updatedItems, status: allDone ? 'completed' : 'active' };
      })
    );

    try {
      await api.patch(`/checklists/${checklistId}/items/${itemId}`, { is_completed: isCompleted });
    } catch (error) {
      setChecklists(current => current.map(cl => {
        if (cl.id !== checklistId) return cl;
        const restoredItems = cl.items.map(item => item.id === itemId
          ? { ...item, is_completed: !isCompleted, completed_at: previousItem?.completed_at || null }
          : item);
        const allRestored = restoredItems.length > 0 && restoredItems.every(item => item.is_completed);
        return { ...cl, items: restoredItems, status: allRestored ? 'completed' : 'active' };
      }));
      setActionError(error.response?.data?.detail || 'Could not save that checklist update. Please try again.');
    } finally {
      setPendingItems(current => {
        const next = { ...current };
        delete next[pendingKey];
        return next;
      });
    }
  };

  const filteredChecklists = checklists.filter(cl => {
    if (filter === 'active') return cl.status === 'active';
    if (filter === 'completed') return cl.status === 'completed';
    return true;
  });

  const totalTasks = checklists.reduce((acc, cl) => acc + (cl.items || []).length, 0);
  const completedTasks = checklists.reduce((acc, cl) => acc + (cl.items || []).filter(i => i.is_completed).length, 0);
  const existingSchemeIds = new Set(checklists.map(checklist => checklist.scheme_id));
  const availableSchemes = schemes.filter(scheme => !existingSchemeIds.has(scheme.id));

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
          Create a scheme checklist and track your application tasks.
        </p>
      </div>

      <form onSubmit={handleCreateChecklist} className="bg-card border border-border/50 rounded-2xl p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-end gap-3">
          <div className="flex-1 space-y-1.5">
            <label htmlFor="checklist-scheme" className="block text-sm font-medium text-foreground">Choose a scheme</label>
            <select
              id="checklist-scheme"
              value={selectedSchemeId}
              onChange={event => setSelectedSchemeId(event.target.value)}
              disabled={loading || availableSchemes.length === 0}
              required
              className="w-full px-3.5 py-2.5 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40"
            >
              <option value="">{availableSchemes.length ? 'Select a scheme' : 'No schemes available for a new checklist'}</option>
              {availableSchemes.map(scheme => <option key={scheme.id} value={scheme.id}>{scheme.name}</option>)}
            </select>
          </div>
          <button
            type="submit"
            disabled={loading || creating || !selectedSchemeId}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {creating ? 'Creating…' : 'Create Checklist'}
          </button>
        </div>
        {schemes.length > 0 && availableSchemes.length === 0 && (
          <p className="text-xs text-muted-foreground mt-2">A checklist already exists for every available scheme.</p>
        )}
      </form>

      {actionError && <p role="alert" className="text-sm text-rose-400">{actionError}</p>}

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
      ) : loadError ? (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5 text-sm text-rose-400">
          {loadError}
        </div>
      ) : filteredChecklists.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-2xl bg-secondary/60 flex items-center justify-center mb-4">
            <CheckSquare className="w-7 h-7 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground font-medium">No checklists yet</p>
          <p className="text-sm text-muted-foreground/60 mt-1">
            Choose a scheme above to create your first checklist.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredChecklists.map((checklist) => (
            <ChecklistCard
              key={checklist.id}
              checklist={checklist}
              onToggleItem={handleToggleItem}
              pendingItems={pendingItems}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
};

export default ChecklistsPage;
