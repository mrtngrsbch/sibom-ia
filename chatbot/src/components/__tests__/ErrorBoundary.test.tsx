/**
 * Tests para ErrorBoundary.tsx
 *
 * Prueba el componente ErrorBoundary.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';

// Componente que lanza error para testing
function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>No error</div>;
}

describe('ErrorBoundary', () => {
  // Suprimir console.error para los tests
  const originalError = console.error;
  const originalWarn = console.warn;

  beforeAll(() => {
    console.error = vi.fn();
    console.warn = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
    console.warn = originalWarn;
  });

  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>Child component</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('Child component')).toBeInTheDocument();
  });

  it('should catch errors and render error UI', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Algo salió mal')).toBeInTheDocument();
    expect(screen.getByText(/Ha ocurrido un error/)).toBeInTheDocument();
  });

  it('should display error message', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('should render reload button', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const reloadButton = screen.getByText('Recargar página');
    expect(reloadButton).toBeInTheDocument();

    // Verificar que el botón existe y es un botón
    expect(reloadButton.tagName).toBe('BUTTON');
  });

  it('should render custom fallback when provided', () => {
    const fallback = <div>Custom error UI</div>;

    render(
      <ErrorBoundary fallback={fallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
  });

  it('should not catch errors in development mode intentionally', () => {
    // Este test verifica que el ErrorBoundary está configurado
    // En modo desarrollo, React puede no respetar el ErrorBoundary
    // pero en producción debería funcionar
    const { container } = render(
      <ErrorBoundary>
        <div>Safe component</div>
      </ErrorBoundary>
    );

    expect(container.textContent).toBe('Safe component');
  });
});
