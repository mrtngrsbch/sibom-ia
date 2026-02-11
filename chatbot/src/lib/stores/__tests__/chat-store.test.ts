/**
 * Tests para chat-store.ts
 *
 * Prueba el store de Zustand para el chat.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useChatStore } from '../chat-store';

describe('useChatStore', () => {
  beforeEach(() => {
    // Limpiar el store antes de cada test
    const { result } = renderHook(() => useChatStore());
    act(() => {
      result.current.clearMessages();
      result.current.resetFilters();
    });
  });

  describe('messages', () => {
    it('should initialize with empty messages array', () => {
      const { result } = renderHook(() => useChatStore());
      expect(result.current.messages).toEqual([]);
    });

    it('should add a message', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.addMessage({
          id: '1',
          role: 'user',
          content: 'Hola',
        });
      });

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].content).toBe('Hola');
    });

    it('should add multiple messages', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.addMessage({
          id: '1',
          role: 'user',
          content: 'Hola',
        });
        result.current.addMessage({
          id: '2',
          role: 'assistant',
          content: '¿En qué puedo ayudarte?',
        });
      });

      expect(result.current.messages).toHaveLength(2);
    });

    it('should set messages', () => {
      const { result } = renderHook(() => useChatStore());
      const messages = [
        { id: '1', role: 'user' as const, content: 'Test' },
        { id: '2', role: 'assistant' as const, content: 'Response' },
      ];

      act(() => {
        result.current.setMessages(messages);
      });

      expect(result.current.messages).toEqual(messages);
    });

    it('should clear messages', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.addMessage({
          id: '1',
          role: 'user',
          content: 'Test',
        });
      });

      expect(result.current.messages).toHaveLength(1);

      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.messages).toEqual([]);
    });
  });

  describe('filters', () => {
    it('should initialize with default filters', () => {
      const { result } = renderHook(() => useChatStore());

      expect(result.current.filters).toEqual({
        municipality: null,
        ordinanceType: 'all',
        dateFrom: null,
        dateTo: null,
      });
    });

    it('should set municipality', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setMunicipality('Carlos Tejedor');
      });

      expect(result.current.filters.municipality).toBe('Carlos Tejedor');
    });

    it('should set ordinance type', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setOrdinanceType('decreto');
      });

      expect(result.current.filters.ordinanceType).toBe('decreto');
    });

    it('should set date range', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setDateRange('2024-01-01', '2024-12-31');
      });

      expect(result.current.filters.dateFrom).toBe('2024-01-01');
      expect(result.current.filters.dateTo).toBe('2024-12-31');
    });

    it('should set multiple filters at once', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setFilters({
          municipality: 'Merlo',
          ordinanceType: 'ordenanza',
        });
      });

      expect(result.current.filters.municipality).toBe('Merlo');
      expect(result.current.filters.ordinanceType).toBe('ordenanza');
    });

    it('should reset filters to default', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setMunicipality('Carlos Tejedor');
        result.current.setOrdinanceType('decreto');
      });

      expect(result.current.filters.municipality).toBe('Carlos Tejedor');

      act(() => {
        result.current.resetFilters();
      });

      expect(result.current.filters).toEqual({
        municipality: null,
        ordinanceType: 'all',
        dateFrom: null,
        dateTo: null,
      });
    });
  });

  describe('ui state', () => {
    it('should initialize sidebar as closed', () => {
      const { result } = renderHook(() => useChatStore());
      expect(result.current.isSidebarOpen).toBe(false);
    });

    it('should toggle sidebar', () => {
      const { result } = renderHook(() => useChatStore());

      expect(result.current.isSidebarOpen).toBe(false);

      act(() => {
        result.current.toggleSidebar();
      });

      expect(result.current.isSidebarOpen).toBe(true);

      act(() => {
        result.current.toggleSidebar();
      });

      expect(result.current.isSidebarOpen).toBe(false);
    });

    it('should set sidebar open state', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setSidebarOpen(true);
      });

      expect(result.current.isSidebarOpen).toBe(true);
    });
  });

  describe('lastQuery', () => {
    it('should set last query', () => {
      const { result } = renderHook(() => useChatStore());

      act(() => {
        result.current.setLastQuery('ordenanzas de tránsito');
      });

      expect(result.current.lastQuery).toBe('ordenanzas de tránsito');
    });
  });
});
