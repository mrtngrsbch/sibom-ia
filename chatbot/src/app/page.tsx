'use client';

import { useState, useEffect, useCallback } from 'react';
import { ChatContainer } from '@/components/chat/ChatContainer';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';
import { FilterBar } from '@/components/chat/FilterBar';
import { ActiveFilters } from '@/components/chat/ActiveFilters';
import type { ChatFilters } from '@/lib/types';

/**
 * Página principal del Chatbot Legal Municipal
 * @description Interface de chat con panel lateral de navegación y filtros inteligentes
 *
 * ARQUITECTURA HÍBRIDA:
 * - Badges de filtros activos siempre visibles
 * - FilterBar avanzado colapsable
 * - Sincronización bidireccional: UI ↔ auto-detección
 */
export default function HomePage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [chatKey, setChatKey] = useState(0);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [currentFilters, setCurrentFilters] = useState<ChatFilters>({
    municipality: null,
    ordinanceType: 'all',
    dateFrom: null,
    dateTo: null
  });
  const [municipalities, setMunicipalities] = useState<string[]>([]);
  const [isFiltersLoaded, setIsFiltersLoaded] = useState(false);

  // Cargar filtros de localStorage
  useEffect(() => {
    const saved = localStorage.getItem('chat-filters');
    if (saved) {
      try {
        setCurrentFilters(JSON.parse(saved));
      } catch (e) {
        console.error('Error loading filters:', e);
      }
    }
    setIsFiltersLoaded(true);
  }, []);

  // Cargar municipios disponibles desde API
  useEffect(() => {
    fetch('/api/stats')
      .then(res => res.json())
      .then(data => setMunicipalities(data.municipalityList || []))
      .catch(console.error);
  }, []);

  // Guardar filtros en localStorage cuando cambian
  useEffect(() => {
    if (isFiltersLoaded) {
      localStorage.setItem('chat-filters', JSON.stringify(currentFilters));
    }
  }, [currentFilters, isFiltersLoaded]);

  // Limpiar historial del chat
  const handleClearHistory = useCallback(() => {
    localStorage.removeItem('chat-history');
    setChatKey(prev => prev + 1); // Forzar reinicio del ChatContainer
  }, []);

  // Quitar filtro individual
  const handleRemoveFilter = useCallback((filterKey: keyof ChatFilters) => {
    setCurrentFilters(prev => ({
      ...prev,
      [filterKey]: filterKey === 'ordinanceType' ? 'all' : null
    }));
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Contenido principal */}
      <main className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 bg-white dark:bg-slate-900">
          <Header onMenuClick={() => setIsMobileMenuOpen(true)} />
        </header>

        {/* Barra de filtros activos - siempre visible, compacta */}
        <div className="border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-2">
          <ActiveFilters
            municipality={currentFilters.municipality}
            ordinanceType={currentFilters.ordinanceType}
            dateFrom={currentFilters.dateFrom}
            dateTo={currentFilters.dateTo}
            onRemoveFilter={handleRemoveFilter}
            onShowAdvancedFilters={() => setShowAdvancedFilters(prev => !prev)}
          />
        </div>

        {/* FilterBar avanzado - colapsable */}
        {showAdvancedFilters && (
          <div className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900">
            <FilterBar
              filters={currentFilters}
              municipalities={municipalities}
              onChange={setCurrentFilters}
              onClearHistory={handleClearHistory}
            />
          </div>
        )}

        {/* Área del chat */}
        <div className="flex-1 overflow-hidden">
          <ChatContainer
            key={chatKey}
            filters={currentFilters}
            municipalities={municipalities}
            onClearHistory={handleClearHistory}
            onFiltersChange={setCurrentFilters}
          />
        </div>
      </main>

      {/* Panel lateral - Desktop (a la derecha) */}
      <aside className="hidden lg:flex w-72 flex-col border-l border-slate-200 dark:border-slate-800">
        <Sidebar showNavigation={true} currentMunicipality={currentFilters.municipality} />
      </aside>

      {/* Panel lateral - Mobile (Drawer desde la derecha) */}
      <MobileDrawer isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)}>
        <Sidebar showNavigation={true} currentMunicipality={currentFilters.municipality} />
      </MobileDrawer>
    </div>
  );
}
