import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { BottomBar } from './BottomBar';
import { ErrorBoundary } from '../common/ErrorBoundary';

export const DesktopLayout: React.FC = () => {
  return (
    <div className="flex flex-col h-screen w-full bg-background overflow-hidden text-gray-100 font-sans selection:bg-primary/30">
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col h-full relative w-full overflow-hidden bg-background">
          <Topbar />
          <main className="flex-1 overflow-hidden p-4 relative">
            <ErrorBoundary>
              <Outlet />
            </ErrorBoundary>
          </main>
        </div>
      </div>
      <BottomBar />
    </div>
  );
};
