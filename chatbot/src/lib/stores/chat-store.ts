/**
 * chat-store.ts
 *
 * Store de Zustand para el estado del chat.
 * Maneja mensajes, filtros y configuración con persistencia en localStorage.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage, ChatFilters } from '@/lib/types';

interface ChatState {
  // Mensajes
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  clearMessages: () => void;

  // Filtros
  filters: ChatFilters;
  setFilters: (filters: Partial<ChatFilters>) => void;
  setMunicipality: (municipality: string | null) => void;
  setOrdinanceType: (type: ChatFilters['ordinanceType']) => void;
  setDateRange: (from: string | null, to: string | null) => void;
  resetFilters: () => void;

  // Estado de la UI
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Utilidades
  lastQuery: string;
  setLastQuery: (query: string) => void;
}

const defaultFilters: ChatFilters = {
  municipality: null,
  ordinanceType: 'all',
  dateFrom: null,
  dateTo: null,
};

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Mensajes
      messages: [],
      addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),
      setMessages: (messages) => set({ messages }),
      clearMessages: () => set({ messages: [] }),

      // Filtros
      filters: defaultFilters,
      setFilters: (newFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...newFilters },
        })),
      setMunicipality: (municipality) =>
        set((state) => ({
          filters: { ...state.filters, municipality },
        })),
      setOrdinanceType: (ordinanceType) =>
        set((state) => ({
          filters: { ...state.filters, ordinanceType },
        })),
      setDateRange: (dateFrom, dateTo) =>
        set((state) => ({
          filters: { ...state.filters, dateFrom, dateTo },
        })),
      resetFilters: () => set({ filters: defaultFilters }),

      // Estado de la UI
      isSidebarOpen: false,
      toggleSidebar: () =>
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setSidebarOpen: (open) => set({ isSidebarOpen: open }),

      // Utilidades
      lastQuery: '',
      setLastQuery: (query) => set({ lastQuery: query }),
    }),
    {
      name: 'chat-storage',
      // Solo persistir campos específicos
      partialize: (state) => ({
        messages: state.messages,
        filters: state.filters,
        lastQuery: state.lastQuery,
      }),
    }
  )
);
