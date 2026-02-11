/**
 * ui-store.ts
 *
 * Store de Zustand para el estado de la UI global.
 * Maneja modales, notificaciones y estado visual.
 */

import { create } from 'zustand';

interface Toast {
  id: string;
  title: string;
  message?: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

interface UIState {
  // Modales
  isMobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
  toggleMobileMenu: () => void;

  // Filtros avanzados
  showAdvancedFilters: boolean;
  setShowAdvancedFilters: (show: boolean) => void;
  toggleAdvancedFilters: () => void;

  // Loading states
  isLoading: boolean;
  setLoading: (loading: boolean) => void;

  // Toast notifications
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;

  // Errors
  error: Error | null;
  setError: (error: Error | null) => void;
  clearError: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  // Modales
  isMobileMenuOpen: false,
  setMobileMenuOpen: (open) => set({ isMobileMenuOpen: open }),
  toggleMobileMenu: () =>
    set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),

  // Filtros avanzados
  showAdvancedFilters: false,
  setShowAdvancedFilters: (show) => set({ showAdvancedFilters: show }),
  toggleAdvancedFilters: () =>
    set((state) => ({ showAdvancedFilters: !state.showAdvancedFilters })),

  // Loading states
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),

  // Toast notifications
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).substring(7);
    const newToast: Toast = { ...toast, id };
    set((state) => ({ toasts: [...state.toasts, newToast] }));

    // Auto-remove después del duration (default 5000ms)
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        get().removeToast(id);
      }, duration);
    }
  },
  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
  clearToasts: () => set({ toasts: [] }),

  // Errors
  error: null,
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
