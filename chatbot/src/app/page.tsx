'use client';

import { useState, useCallback } from 'react';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';

/**
 * Página principal del Chatbot Legal Municipal
 * @description Interface de chat con panel lateral de navegación
 */
export default function HomePage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [chatKey, setChatKey] = useState(0);

  // Limpiar historial del chat
  const handleClearHistory = useCallback(() => {
    localStorage.removeItem('chat-history');
    setChatKey(prev => prev + 1); // Forzar reinicio del ChatContainer
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Contenido principal */}
      <main className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 bg-white dark:bg-slate-900">
          <Header onMenuClick={() => setIsMobileMenuOpen(true)} />
        </header>

        {/* Área del chat */}
        <div className="flex-1 overflow-hidden">
          <ChatContainer
            key={chatKey}
            onClearHistory={handleClearHistory}
          />
        </div>
      </main>

      {/* Panel lateral - Desktop (a la derecha) */}
      <aside className="hidden lg:flex w-72 flex-col border-l border-slate-200 dark:border-slate-800">
        <Sidebar showNavigation={true} />
      </aside>

      {/* Panel lateral - Mobile (Drawer desde la derecha) */}
      <MobileDrawer isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)}>
        <Sidebar showNavigation={true} />
      </MobileDrawer>
    </div>
  );
}
