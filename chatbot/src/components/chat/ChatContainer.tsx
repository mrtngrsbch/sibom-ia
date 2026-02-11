/**
 * ChatContainer.tsx
 *
 * Componente principal del chat refactorizado con componentes modulares.
 * @description Interface de chat optimizada usando AI SDK v5 con persistencia
 */

'use client';

import { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { ChatWelcome } from './ChatWelcome';
import { ChatMessageList } from './ChatMessageList';
import { ChatTypingIndicator } from './ChatTypingIndicator';
import { ChatInput } from './ChatInput';
import { ChatErrorMessage } from './ChatErrorMessage';

/**
 * Función de debounce para reducir frecuencia de ejecución
 */
function debounce<T extends (...args: unknown[]) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args as Parameters<T>), wait);
  };
}

interface ChatContainerProps {
  onClearHistory: () => void;
}

/**
 * Componente principal del chat
 */
export function ChatContainer({
  onClearHistory: _onClearHistory
}: ChatContainerProps) {
  const [chatKey] = useState(0);
  // AI SDK v5: manejar estado del input manualmente
  const [input, setInput] = useState('');

  const {
    messages,
    status,
    error,
    setMessages,
    sendMessage,
    regenerate
  } = useChat({
    transport: new DefaultChatTransport({ api: '/api/chat' }),
    id: `chat-${chatKey}`,
    onError: (err) => {
      console.error('Chat error:', err);
    }
  });

  // Determinar si está cargando basado en el status
  const isLoading = status === 'submitted' || status === 'streaming';

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isUserAtBottom = useRef(true);

  // Función de guardado con debounce
  const debouncedSaveHistory = useMemo(
    () => debounce((msgs: unknown) => {
      localStorage.setItem('chat-history', JSON.stringify(msgs));
    }, 500),
    []
  );

  // Cargar historial de localStorage al inicio
  useEffect(() => {
    const saved = localStorage.getItem('chat-history');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
        }
      } catch (e) {
        console.error('Error loading history:', e);
      }
    }
  }, [setMessages]);

  // Guardar historial en localStorage cuando cambian los mensajes
  useEffect(() => {
    debouncedSaveHistory(messages);
  }, [messages, debouncedSaveHistory]);

  // Detectar posición del scroll para auto-scroll inteligente
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const threshold = 100;
    const isAtBottom =
      target.scrollHeight - target.scrollTop - target.clientHeight < threshold;
    isUserAtBottom.current = isAtBottom;
  }, []);

  // Manejar click en pregunta frecuente
  const handleFaqClick = useCallback((question: string) => {
    sendMessage({ text: question });
  }, [sendMessage]);

  // Manejar envío de mensaje
  const handleSubmit = useCallback((e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim()) return;

    sendMessage({ text: input });
    setInput('');
  }, [input, sendMessage]);

  // Manejar Enter para enviar, Shift+Enter para nueva línea
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  // Placeholder dinámico
  const placeholder = `Ej: "decretos de Carlos Tejedor en 2025"`;

  const showTypingIndicator = isLoading && messages[messages.length - 1]?.role === 'user';

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950">
      {/* Área de mensajes */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6"
      >
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Pantalla de bienvenida */}
          {messages.length === 0 && (
            <ChatWelcome isLoading={isLoading} onQuestionClick={handleFaqClick} />
          )}

          {/* Lista de mensajes */}
          {messages.length > 0 && (
            <ChatMessageList messages={messages} />
          )}

          {/* Indicador de escritura */}
          {showTypingIndicator && <ChatTypingIndicator />}

          {/* Mensaje de error */}
          {error && <ChatErrorMessage error={error} onRetry={() => regenerate()} />}
        </div>
      </div>

      {/* Área de entrada */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        onKeyDown={handleKeyDown}
        isLoading={isLoading}
        placeholder={placeholder}
      />
    </div>
  );
}
