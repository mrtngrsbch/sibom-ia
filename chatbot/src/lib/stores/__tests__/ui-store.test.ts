/**
 * Tests para ui-store.ts
 *
 * Prueba el store de Zustand para la UI.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUIStore } from '../ui-store';

describe('useUIStore', () => {
  beforeEach(() => {
    // Limpiar el store antes de cada test
    const { result } = renderHook(() => useUIStore());
    act(() => {
      result.current.clearToasts();
      result.current.setMobileMenuOpen(false);
      result.current.setShowAdvancedFilters(false);
      result.current.setLoading(false);
      result.current.clearError();
    });
  });

  describe('mobile menu', () => {
    it('should initialize mobile menu as closed', () => {
      const { result } = renderHook(() => useUIStore());
      expect(result.current.isMobileMenuOpen).toBe(false);
    });

    it('should toggle mobile menu', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.toggleMobileMenu();
      });

      expect(result.current.isMobileMenuOpen).toBe(true);

      act(() => {
        result.current.toggleMobileMenu();
      });

      expect(result.current.isMobileMenuOpen).toBe(false);
    });

    it('should set mobile menu open state', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.setMobileMenuOpen(true);
      });

      expect(result.current.isMobileMenuOpen).toBe(true);
    });
  });

  describe('advanced filters', () => {
    it('should initialize advanced filters as hidden', () => {
      const { result } = renderHook(() => useUIStore());
      expect(result.current.showAdvancedFilters).toBe(false);
    });

    it('should toggle advanced filters', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.toggleAdvancedFilters();
      });

      expect(result.current.showAdvancedFilters).toBe(true);

      act(() => {
        result.current.toggleAdvancedFilters();
      });

      expect(result.current.showAdvancedFilters).toBe(false);
    });

    it('should set advanced filters visibility', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.setShowAdvancedFilters(true);
      });

      expect(result.current.showAdvancedFilters).toBe(true);
    });
  });

  describe('loading state', () => {
    it('should initialize as not loading', () => {
      const { result } = renderHook(() => useUIStore());
      expect(result.current.isLoading).toBe(false);
    });

    it('should set loading state', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.setLoading(true);
      });

      expect(result.current.isLoading).toBe(true);

      act(() => {
        result.current.setLoading(false);
      });

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('toasts', () => {
    it('should initialize with empty toasts', () => {
      const { result } = renderHook(() => useUIStore());
      expect(result.current.toasts).toEqual([]);
    });

    it('should add a success toast', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addToast({
          title: 'Success',
          message: 'Operation completed',
          type: 'success',
        });
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].title).toBe('Success');
      expect(result.current.toasts[0].type).toBe('success');
    });

    it('should add an error toast', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addToast({
          title: 'Error',
          message: 'Something went wrong',
          type: 'error',
        });
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('error');
    });

    it('should add a warning toast', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addToast({
          title: 'Warning',
          type: 'warning',
        });
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('warning');
    });

    it('should add an info toast', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addToast({
          title: 'Info',
          type: 'info',
        });
      });

      expect(result.current.toasts).toHaveLength(1);
      expect(result.current.toasts[0].type).toBe('info');
    });

    it('should generate unique IDs for toasts', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addToast({ title: 'Toast 1', type: 'info' });
        result.current.addToast({ title: 'Toast 2', type: 'info' });
      });

      const ids = result.current.toasts.map((t) => t.id);
      expect(new Set(ids).size).toBe(2); // IDs deben ser únicos
    });

    it('should remove a toast by ID', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addToast({
          title: 'Test',
          type: 'info',
          duration: 0, // No auto-eliminar para este test
        });
      });

      const toastId = result.current.toasts[0].id;
      expect(result.current.toasts).toHaveLength(1);

      act(() => {
        result.current.removeToast(toastId);
      });

      expect(result.current.toasts).toHaveLength(0);
    });

    it('should clear all toasts', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.addToast({ title: 'Toast 1', type: 'info' });
        result.current.addToast({ title: 'Toast 2', type: 'info' });
        result.current.addToast({ title: 'Toast 3', type: 'info' });
      });

      expect(result.current.toasts).toHaveLength(3);

      act(() => {
        result.current.clearToasts();
      });

      expect(result.current.toasts).toHaveLength(0);
    });
  });

  describe('errors', () => {
    it('should initialize with no error', () => {
      const { result } = renderHook(() => useUIStore());
      expect(result.current.error).toBeNull();
    });

    it('should set error', () => {
      const { result } = renderHook(() => useUIStore());
      const error = new Error('Test error');

      act(() => {
        result.current.setError(error);
      });

      expect(result.current.error).toBe(error);
    });

    it('should clear error', () => {
      const { result } = renderHook(() => useUIStore());

      act(() => {
        result.current.setError(new Error('Test'));
      });

      expect(result.current.error).not.toBeNull();

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });
});
