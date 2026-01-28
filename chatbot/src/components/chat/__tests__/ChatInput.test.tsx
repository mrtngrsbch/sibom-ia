/**
 * Tests para ChatInput.tsx
 *
 * Prueba el componente de entrada de mensajes.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../ChatInput';

describe('ChatInput', () => {
  it('should render textarea with placeholder', () => {
    render(
      <ChatInput
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        onKeyDown={vi.fn()}
        isLoading={false}
        placeholder="Escribe tu mensaje..."
      />
    );

    const textarea = screen.getByPlaceholderText('Escribe tu mensaje...');
    expect(textarea).toBeInTheDocument();
  });

  it('should call onChange when input changes', () => {
    const handleChange = vi.fn();
    render(
      <ChatInput
        value=""
        onChange={handleChange}
        onSubmit={vi.fn()}
        onKeyDown={vi.fn()}
        isLoading={false}
        placeholder="Placeholder"
      />
    );

    const textarea = screen.getByPlaceholderText('Placeholder');
    fireEvent.change(textarea, { target: { value: 'Hola' } });

    expect(handleChange).toHaveBeenCalledWith('Hola');
  });

  it('should call onSubmit when form is submitted', () => {
    const handleSubmit = vi.fn((e) => e.preventDefault());
    render(
      <ChatInput
        value="Test message"
        onChange={vi.fn()}
        onSubmit={handleSubmit}
        onKeyDown={vi.fn()}
        isLoading={false}
        placeholder="Placeholder"
      />
    );

    // Buscar el form por el elemento (no por role)
    const form = document.querySelector('form');
    if (form) {
      fireEvent.submit(form);
    }

    expect(handleSubmit).toHaveBeenCalledTimes(1);
  });

  it('should disable submit button when loading', () => {
    render(
      <ChatInput
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        onKeyDown={vi.fn()}
        isLoading={true}
        placeholder="Placeholder"
      />
    );

    const button = screen.getByRole('button', { name: /enviar mensaje/i });
    expect(button).toBeDisabled();
  });

  it('should disable submit button when input is empty', () => {
    render(
      <ChatInput
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        onKeyDown={vi.fn()}
        isLoading={false}
        placeholder="Placeholder"
      />
    );

    const button = screen.getByRole('button', { name: /enviar mensaje/i });
    expect(button).toBeDisabled();
  });

  it('should enable submit button when input has value', () => {
    render(
      <ChatInput
        value="Test"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        onKeyDown={vi.fn()}
        isLoading={false}
        placeholder="Placeholder"
      />
    );

    const button = screen.getByRole('button', { name: /enviar mensaje/i });
    expect(button).not.toBeDisabled();
  });

  it('should call onKeyDown when key is pressed', () => {
    const handleKeyDown = vi.fn();
    render(
      <ChatInput
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        onKeyDown={handleKeyDown}
        isLoading={false}
        placeholder="Placeholder"
      />
    );

    const textarea = screen.getByPlaceholderText('Placeholder');
    fireEvent.keyDown(textarea, { key: 'Enter' });

    expect(handleKeyDown).toHaveBeenCalled();
  });

  it('should render footer text', () => {
    render(
      <ChatInput
        value=""
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        onKeyDown={vi.fn()}
        isLoading={false}
        placeholder="Placeholder"
      />
    );

    expect(screen.getByText(/Las respuestas son generadas por IA/)).toBeInTheDocument();
  });
});
