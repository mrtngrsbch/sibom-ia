"use client";

import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';

export default function DatosLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <main className="flex flex-1 flex-col min-w-0">
        <header className="flex h-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 bg-white dark:bg-slate-900">
          <Header onMenuClick={() => setIsDrawerOpen(true)} />
        </header>

        <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950">
          {children}
        </div>
      </main>

        <aside className="hidden lg:block w-80 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
          <Sidebar showNavigation={true} />
        </aside>

      <MobileDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)}>
        <Sidebar showNavigation={true} />
      </MobileDrawer>
    </div>
  );
}
