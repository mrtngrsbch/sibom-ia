'use client';

import { Menu, Moon, Sun } from '@/lib/icons';
import { useTheme } from '@/contexts/ThemeContext';

interface HeaderProps {
  onMenuClick?: () => void;
}

/**
 * Header de la aplicación
 * @description Barra superior con controles de tema y menú móvil
 */
export function Header({ onMenuClick }: HeaderProps) {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <div className="flex items-center justify-between w-full">
      {/* Título o logo (opcional) */}
      <div className="flex-1">
        {/* Espacio reservado para logo o título futuro */}
      </div>

      {/* Acciones - Orden: Tema | Hamburguesa (mobile) */}
      <div className="flex items-center gap-2">
        {/* Botón de tema (siempre visible) */}
        <button
          onClick={toggleTheme}
          className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          aria-label={resolvedTheme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
        >
          {resolvedTheme === 'dark' ? (
            <Sun className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          ) : (
            <Moon className="w-5 h-5 text-slate-600 dark:text-slate-400" />
          )}
        </button>

        {/* Botón hamburguesa (solo mobile) */}
        <button
          className="lg:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          onClick={onMenuClick}
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5 text-slate-600 dark:text-slate-400" />
        </button>
      </div>
    </div>
  );
}
