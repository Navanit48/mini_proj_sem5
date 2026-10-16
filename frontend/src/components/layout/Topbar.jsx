import React from 'react';
import { Bell, Menu, Search, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Topbar = () => {
  const { user } = useAuth();

  const displayName = user?.user_metadata?.full_name || 'Citizen';
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="h-16 border-b border-border/40 flex items-center justify-between px-4 sm:px-6 z-10 sticky top-0 bg-background/80 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <button className="md:hidden text-muted-foreground hover:text-foreground transition-colors p-2 rounded-lg hover:bg-secondary/60">
          <Menu className="w-5 h-5" />
        </button>

        {/* Search */}
        <div className="hidden sm:flex items-center relative w-72">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 pointer-events-none" />
          <input
            type="text"
            placeholder="Search schemes, documents..."
            className="w-full pl-10 pr-4 py-2 bg-secondary/50 border border-border/50 rounded-xl text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary/40 transition-all duration-200"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Notification */}
        <button className="relative p-2.5 text-muted-foreground hover:text-foreground hover:bg-secondary/60 rounded-xl transition-all duration-200">
          <Bell className="w-[18px] h-[18px]" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full ring-2 ring-background" />
        </button>

        {/* Divider */}
        <div className="w-px h-8 bg-border/40 hidden sm:block" />

        {/* Profile */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-foreground leading-tight">{displayName}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/30 to-purple-500/20 border border-primary/20 flex items-center justify-center text-primary font-semibold text-xs">
            {initials}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
