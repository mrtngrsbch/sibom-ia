/**
 * ChatContainer.tsx
 *
 * Componente principal del chat refactorizado con componentes modulares.
 * @description Interface de chat optimizada usando AI SDK con persistencia
 */

'use client';

import { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { useChat } from 'ai/react';
import type { ChatFilters, ChatMessage } from '@/lib/types';
import { extractFiltersFromQuery } from '@/lib/query-filter-extractor';
import type { SearchOptions } from '@/lib/rag/retriever';
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
  filters: ChatFilters;
  municipalities: string[];
  onClearHistory: () => void;
  onFiltersChange?: (filters: ChatFilters) => void;
}

/**
 * Componente principal del chat
 *
 * SINCRONIZACIÓN DE FILTROS:
 * - Detecta filtros en la query del usuario
 * - Actualiza el estado del padre vía onFiltersChange
 * - Los badges se actualizan automáticamente
 */
export function ChatContainer({
  filters,
  municipalities,
  onClearHistory,
  onFiltersChange
}: ChatContainerProps) {
  const [chatKey, setChatKey] = useState(0);

  const {
    messages,
    input,
    handleInputChange,
    handleSubmit,
    isLoading,
    error,
    append,
    data,
    setMessages,
    reload,
    setInput
  } = useChat({
    api: '/api/chat',
    id: `chat-${chatKey}`,
    onError: (err) => {
      console.error('Chat error:', err);
    }
  });

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
    append({
      role: 'user',
      content: question,
    });
  }, [append]);

  // Handler de envío de formulario con extracción de filtros
  const handleFormSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) return;

    // Extraer filtros automáticamente de la query
    const uiFilters: Partial<SearchOptions> = {
      municipality: filters.municipality || undefined,
      type: filters.ordinanceType === 'all' ? undefined : filters.ordinanceType,
      dateFrom: filters.dateFrom || undefined,
      dateTo: filters.dateTo || undefined
    };

    const extractedFilters = extractFiltersFromQuery(input, municipalities, uiFilters);

    // Construir filtros finales para enviar al backend
    const finalFilters = {
      municipality: extractedFilters.municipality,
      ordinanceType: extractedFilters.type,
      dateFrom: extractedFilters.dateFrom,
      dateTo: extractedFilters.dateTo
    };

    // Sincronizar filtros con la UI
    if (onFiltersChange) {
      const hasNewFilters =
        (extractedFilters.municipality && extractedFilters.municipality !== filters.municipality) ||
        (extractedFilters.type && extractedFilters.type !== filters.ordinanceType) ||
        (extractedFilters.dateFrom && extractedFilters.dateFrom !== filters.dateFrom) ||
        (extractedFilters.dateTo && extractedFilters.dateTo !== filters.dateTo);

      if (hasNewFilters) {
        const validOrdinanceType: ChatFilters['ordinanceType'] =
          extractedFilters.type === 'all' || !extractedFilters.type
            ? filters.ordinanceType
            : extractedFilters.type as ChatFilters['ordinanceType'];

        onFiltersChange({
          municipality: extractedFilters.municipality || filters.municipality,
          ordinanceType: validOrdinanceType,
          dateFrom: extractedFilters.dateFrom || filters.dateFrom,
          dateTo: extractedFilters.dateTo || filters.dateTo,
        });
      }
    }

    // Enviar al chat con filtros aplicados
    handleSubmit(e, {
      body: {
        filters: finalFilters
      }
    });
  }, [input, filters, municipalities, onFiltersChange, handleSubmit]);

  // Manejar Enter para enviar, Shift+Enter para nueva línea
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const syntheticEvent = { preventDefault: () => {} } as React.FormEvent;
      handleFormSubmit(syntheticEvent);
    }
  }, [handleFormSubmit]);

  // Placeholder dinámico según filtro
  const placeholder = filters.municipality
    ? `Preguntá sobre ${filters.municipality}...`
    : `Ej: "decretos de Carlos Tejedor en 2025"`;

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
            <ChatMessageList messages={messages} data={data} />
          )}

          {/* Indicador de escritura */}
          {showTypingIndicator && <ChatTypingIndicator />}

          {/* Mensaje de error */}
          {error && <ChatErrorMessage error={error} onRetry={() => reload()} />}
        </div>
      </div>

      {/* Área de entrada */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={handleFormSubmit}
        onKeyDown={handleKeyDown}
        isLoading={isLoading}
        placeholder={placeholder}
      />
    </div>
  );
}
