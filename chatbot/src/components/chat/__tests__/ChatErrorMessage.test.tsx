/**
 * Tests para ChatErrorMessage.tsx
 *
 * Prueba el componente de mensaje de error.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatErrorMessage } from '../ChatErrorMessage';

describe('ChatErrorMessage', () => {
  it('should render error title', () => {
    render(
      <ChatErrorMessage
        error={new Error('Test error')}
        onRetry={vi.fn()}
      />
    );

    expect(screen.getByText('Hubo un error al procesar tu mensaje.')).toBeInTheDocument();
  });

  it('should render error message', () => {
    const errorMessage = 'Connection failed';
    render(
      <ChatErrorMessage
        error={new Error(errorMessage)}
        onRetry={vi.fn()}
      />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('should call onRetry when retry button is clicked', () => {
    const handleRetry = vi.fn();
    render(
      <ChatErrorMessage
        error={new Error('Test error')}
        onRetry={handleRetry}
      />
    );

    const retryButton = screen.getByText('Reintentar consulta');
    fireEvent.click(retryButton);

    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('should render with correct styling classes', () => {
    const { container } = render(
      <ChatErrorMessage
        error={new Error('Test error')}
        onRetry={vi.fn()}
      />
    );

    const errorDiv = container.querySelector('.bg-red-50');
    expect(errorDiv).toBeInTheDocument();
  });
});
