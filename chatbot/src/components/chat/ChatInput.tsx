/**
 * ChatInput.tsx
 *
 * Componente de entrada de mensajes con auto-resize.
 */

'use client';

import { useRef, useEffect } from 'react';
import { Send } from '@/lib/icons';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  isLoading: boolean;
  placeholder: string;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  onKeyDown,
  isLoading,
  placeholder
}: ChatInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Resetear altura después de enviar
  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.style.height = 'auto';
    }
  }, [isLoading]);

  return (
    <div className="p-4 bg-white dark:bg-slate-900">
      <div className="max-w-3xl mx-auto">
        <form onSubmit={onSubmit} className="relative">
          <textarea
            ref={inputRef}
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={placeholder}
            rows={1}
            className="w-full pl-4 pr-12 py-3 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none overflow-hidden"
            disabled={isLoading}
            style={{
              minHeight: '44px',
              maxHeight: '200px',
            }}
            onInput={(e) => {
              // Auto-resize del textarea (sin llamar a onChange para evitar bucle)
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, 200) + 'px';
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !value?.trim()}
            className="absolute right-2 bottom-3 p-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Enviar mensaje"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        {/* Footer del chat */}
        <div className="mt-2 text-left">
          <p className="text-xs text-slate-400 dark:text-slate-500">
            Las respuestas son generadas por IA. Verificá la información en las fuentes oficiales.
          </p>
        </div>
      </div>
    </div>
  );
}
