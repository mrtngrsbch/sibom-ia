'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

/**
 * ThemeContext
 *
 * Contexto para gestionar el tema de la aplicación (claro/oscuro).
 * Persiste la preferencia en localStorage y respeta prefers-color-scheme del sistema.
 *
 * @version 1.0.0
 * @created 2026-01-01
 */

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_KEY = 'theme-preference';

/**
 * Determina el tema efectivo basado en la preferencia y el sistema
 */
function getResolvedTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  }
  return theme;
}

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
}

export function ThemeProvider({ children, defaultTheme = 'system' }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  // Cargar tema de localStorage al montar
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    if (stored && ['light', 'dark', 'system'].includes(stored)) {
      setThemeState(stored);
    }
    setMounted(true);
  }, []);

  // Aplicar tema al documento y actualizar resolvedTheme
  useEffect(() => {
    if (!mounted) return;

    const resolved = getResolvedTheme(theme);
    setResolvedTheme(resolved);

    // Aplicar clase al documento
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolved);

    // Persistir preferencia
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme, mounted]);

  // Escuchar cambios en preferencia del sistema
  useEffect(() => {
    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      const newTheme = e.matches ? 'dark' : 'light';
      setResolvedTheme(newTheme);
      document.documentElement.classList.remove('light', 'dark');
      document.documentElement.classList.add(newTheme);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    setThemeState(prev => {
      if (prev === 'light') return 'dark';
      if (prev === 'dark') return 'light';
      // Si está en system, cambiar al opuesto del actual
      return resolvedTheme === 'dark' ? 'light' : 'dark';
    });
  };

  // Evitar flash de contenido incorrecto durante hidratación
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Hook para acceder al contexto de tema
 * Proporciona un fallback seguro si se usa fuera de ThemeProvider
 */
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  
  // Fallback seguro para cuando no hay provider (SSR o pre-render)
  if (context === undefined) {
    return {
      theme: 'system',
      resolvedTheme: 'light',
      setTheme: () => {},
      toggleTheme: () => {},
    };
  }
  return context;
}
