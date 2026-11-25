import { Menu } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Topbar = ({ mobileNavOpen, mobileMenuButtonRef, onMenuClick }) => {
  const { user } = useAuth();

  const displayName = user?.profile?.full_name || 'Citizen';
  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="h-16 border-b border-border/40 flex items-center justify-between px-4 sm:px-6 z-10 sticky top-0 bg-background/80 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <button
          ref={mobileMenuButtonRef}
          type="button"
          onClick={onMenuClick}
          aria-label={mobileNavOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={mobileNavOpen}
          aria-controls="primary-navigation"
          className="md:hidden text-muted-foreground hover:text-foreground transition-colors p-2 rounded-lg hover:bg-secondary/60"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      <div className="flex items-center gap-3">
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
