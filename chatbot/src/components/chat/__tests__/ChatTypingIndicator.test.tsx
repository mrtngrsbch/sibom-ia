/**
 * Tests para ChatTypingIndicator.tsx
 *
 * Prueba el indicador de escritura.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ChatTypingIndicator } from '../ChatTypingIndicator';

describe('ChatTypingIndicator', () => {
  it('should render typing indicator', () => {
    render(<ChatTypingIndicator />);

    expect(screen.getByText('Buscando información...')).toBeInTheDocument();
  });

  it('should render bot avatar', () => {
    const { container } = render(<ChatTypingIndicator />);

    const avatar = container.querySelector('.bg-primary-500.rounded-full');
    expect(avatar).toBeInTheDocument();
  });

  it('should render message container', () => {
    const { container } = render(<ChatTypingIndicator />);

    const messageContainer = container.querySelector('.bg-white');
    expect(messageContainer).toBeInTheDocument();
  });

  it('should have correct CSS classes', () => {
    const { container } = render(<ChatTypingIndicator />);

    // Verificar que tiene la clase de animación
    const animatedDiv = container.querySelector('.animate-slide-up');
    expect(animatedDiv).toBeInTheDocument();
  });
});
