import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Search,
  User,
  FileText,
  CheckSquare,
  BarChart3,
  LogOut,
  ChevronLeft,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../lib/utils';

const navItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Discover Schemes', path: '/schemes', icon: Search },
  { name: 'My Eligibility', path: '/eligibility', icon: User },
  { name: 'Documents', path: '/documents', icon: FileText },
  { name: 'Checklists', path: '/checklists', icon: CheckSquare },
  { name: 'Analytics', path: '/analytics', icon: BarChart3 },
];

const Sidebar = () => {
  const { logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 256 }}
      transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
      className="hidden md:flex flex-col border-r border-border/60 relative"
      style={{ background: 'hsl(228, 14%, 10%)' }}
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-border/40">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white font-bold text-sm shrink-0 shadow-lg shadow-primary/20">
            <Sparkles className="w-4.5 h-4.5" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ duration: 0.15 }}
                className="font-bold text-foreground text-[15px] tracking-tight whitespace-nowrap"
              >
                AidFlow AI
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative',
                  collapsed && 'justify-center px-0',
                  isActive
                    ? 'bg-primary/12 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/60'
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 rounded-xl bg-primary/10 border border-primary/15"
                      transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
                    />
                  )}
                  <Icon className={cn('w-[18px] h-[18px] shrink-0 relative z-10', isActive && 'text-primary')} />
                  <AnimatePresence>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.1 }}
                        className="relative z-10 whitespace-nowrap"
                      >
                        {item.name}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-card border border-border flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors z-20"
      >
        <ChevronLeft className={cn('w-3.5 h-3.5 transition-transform duration-200', collapsed && 'rotate-180')} />
      </button>

      {/* Sign Out */}
      <div className="p-3 border-t border-border/40">
        <button
          onClick={logout}
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-400/80 hover:text-red-400 hover:bg-red-500/8 w-full transition-all duration-200',
            collapsed && 'justify-center px-0'
          )}
        >
          <LogOut className="w-[18px] h-[18px] shrink-0" />
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.1 }}
              >
                Sign Out
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
