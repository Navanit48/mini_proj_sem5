import React from 'react';
import { Bell, Menu, Search, User as UserIcon } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Topbar = () => {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sm:px-6 z-10 sticky top-0">
      <div className="flex items-center gap-4">
        <button className="md:hidden text-slate-500 hover:text-slate-700">
          <Menu className="w-6 h-6" />
        </button>
        
        {/* Search Bar - hidden on mobile */}
        <div className="hidden sm:flex items-center relative w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3" />
          <input 
            type="text" 
            placeholder="Search schemes..." 
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 text-slate-500 hover:bg-slate-50 rounded-full transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full ring-2 ring-white"></span>
        </button>
        
        <div className="flex items-center gap-3 pl-4 border-l border-slate-200">
          <div className="hidden sm:block text-right">
            <p className="text-sm font-medium text-slate-700">{user?.user_metadata?.full_name || 'Citizen'}</p>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-medium border border-blue-200">
            <UserIcon className="w-5 h-5" />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
