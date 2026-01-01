'use client';

import { useState } from 'react';
import { Menu, Search, X, Moon, Sun } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

/**
 * Header de la aplicación
 * @description Barra superior con controles de tema
 */
export function Header() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <div className="flex items-center justify-between w-full">
      {/* Logo y título */}
      <div className="flex items-center gap-3">
        <button
          className="lg:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">SIBOM</span>
          </div>
          <div className="hidden sm:block min-w-0">
            <h1 className="text-sm font-semibold text-slate-900 dark:text-white truncate">
              Asistente Legal Municipal
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Consultas de legislación BA
            </p>
          </div>
        </div>
      </div>

      {/* Barra de búsqueda (expandible) */}
      <div className="flex-1 max-w-xl mx-4">
        <div className={`relative ${isSearchOpen ? 'flex' : 'hidden sm:flex'}`}>
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar ordenanzas, decretos..."
              className="w-full pl-10 pr-4 py-2 bg-slate-100 dark:bg-slate-800 border-0 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              className="sm:hidden absolute right-3 top-1/2 -translate-y-1/2"
              onClick={() => setIsSearchOpen(false)}
              aria-label="Cerrar búsqueda"
            >
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Acciones */}
      <div className="flex items-center gap-2">
        <button
          className="sm:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
          onClick={() => setIsSearchOpen(!isSearchOpen)}
          aria-label="Buscar"
        >
          <Search className="w-5 h-5" />
        </button>
        <button
          onClick={toggleTheme}
          className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
          aria-label={resolvedTheme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
        >
          {resolvedTheme === 'dark' ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
}
