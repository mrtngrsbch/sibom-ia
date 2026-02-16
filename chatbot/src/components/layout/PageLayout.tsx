'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';

interface PageLayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
}

export function PageLayout({ children, showSidebar = true }: PageLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Contenido principal */}
      <main className="flex flex-1 flex-col min-w-0 overflow-hidden relative">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 bg-white dark:bg-slate-900 z-10">
          <Header onMenuClick={() => setIsMobileMenuOpen(true)} />
        </header>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden p-6">
          {children}
        </div>
      </main>

      {/* Panel lateral - Desktop (a la derecha) */}
      {showSidebar && (
        <aside className="hidden lg:flex w-72 flex-col border-l border-slate-200 dark:border-slate-800 h-full bg-slate-50 dark:bg-slate-950/50">
          <Sidebar showNavigation={true} />
        </aside>
      )}

      {/* Panel lateral - Mobile (Drawer desde la derecha) */}
      <MobileDrawer isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)}>
        <Sidebar showNavigation={true} />
      </MobileDrawer>
    </div>
  );
}
