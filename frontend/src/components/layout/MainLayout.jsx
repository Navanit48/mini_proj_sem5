import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

const MainLayout = () => {
  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 overflow-hidden min-w-0">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-[1360px] mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
