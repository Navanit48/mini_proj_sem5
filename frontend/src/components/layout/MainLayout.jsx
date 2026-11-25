import { useEffect, useRef, useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import AssistantLauncher from '../assistant/AssistantLauncher';

const MainLayout = () => {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const mobileMenuButtonRef = useRef(null);
  const mobileCloseButtonRef = useRef(null);
  const previouslyOpen = useRef(false);

  useEffect(() => {
    if (mobileNavOpen) {
      mobileCloseButtonRef.current?.focus();
    } else if (previouslyOpen.current) {
      mobileMenuButtonRef.current?.focus();
    }
    previouslyOpen.current = mobileNavOpen;
  }, [mobileNavOpen]);

  useEffect(() => {
    if (!mobileNavOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setMobileNavOpen(false);
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [mobileNavOpen]);

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {mobileNavOpen && (
        <button
          type="button"
          aria-label="Close navigation menu"
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setMobileNavOpen(false)}
        />
      )}
      <Sidebar
        mobileOpen={mobileNavOpen}
        onMobileClose={() => setMobileNavOpen(false)}
        mobileCloseButtonRef={mobileCloseButtonRef}
      />
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <Topbar
          mobileNavOpen={mobileNavOpen}
          mobileMenuButtonRef={mobileMenuButtonRef}
          onMenuClick={() => setMobileNavOpen((open) => !open)}
        />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-[1360px] mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
      <AssistantLauncher />
    </div>
  );
};

export default MainLayout;
