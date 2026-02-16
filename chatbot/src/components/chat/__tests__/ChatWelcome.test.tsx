/**
 * Tests para ChatWelcome.tsx
 *
 * Prueba la pantalla de bienvenida con preguntas frecuentes.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatWelcome } from '../ChatWelcome';

describe('ChatWelcome', () => {
  it('should render welcome message', () => {
    render(<ChatWelcome isLoading={false} onQuestionClick={vi.fn()} />);

    expect(screen.getByText('¿En qué puedo ayudarte?')).toBeInTheDocument();
    expect(screen.getByText(/observatorio independiente de la decepción municipal/i)).toBeInTheDocument();
  });

  it('should render all FAQ questions', () => {
    render(<ChatWelcome isLoading={false} onQuestionClick={vi.fn()} />);

    expect(screen.getByText('¿Cuáles municipios tienen información disponible?')).toBeInTheDocument();
    expect(screen.getByText('¿Cómo busco una ordenanza específica?')).toBeInTheDocument();
    expect(screen.getByText('¿Qué tipos de normativas puedo consultar?')).toBeInTheDocument();
    expect(screen.getByText('¿Cómo cito una norma en mi búsqueda?')).toBeInTheDocument();
  });

  it('should call onQuestionClick when FAQ is clicked', () => {
    const handleClick = vi.fn();
    render(<ChatWelcome isLoading={false} onQuestionClick={handleClick} />);

    const button = screen.getByText('¿Cuáles municipios tienen información disponible?');
    fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(handleClick).toHaveBeenCalledWith('¿Cuáles municipios tienen información disponible?');
  });

  it('should disable buttons when loading', () => {
    render(<ChatWelcome isLoading={true} onQuestionClick={vi.fn()} />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('should not disable buttons when not loading', () => {
    render(<ChatWelcome isLoading={false} onQuestionClick={vi.fn()} />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).not.toBeDisabled();
    });
  });
});
