'use client';

import { useRef, useEffect, useState, useMemo } from 'react';
import { useChat } from 'ai/react';
import { Send, Bot, User, Sparkles, Loader2 } from '@/lib/icons';
import { clsx } from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Citations } from './Citations';
import type { ChatFilters } from '@/lib/types';
import { TokenUsage } from './TokenUsage';
import { extractFiltersFromQuery } from '@/lib/query-filter-extractor';

/**
 * Función de debounce para reducir frecuencia de ejecución
 * @param func Función a ejecutar
 * @param wait Milisegundos de espera
 */
function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
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
 * @description Interface de chat optimizada usando AI SDK con persistencia
 *
 * SINCRONIZACIÓN DE FILTROS:
 * - Detecta filtros en la query del usuario
 * - Actualiza el estado del padre vía onFiltersChange
 * - Los badges se actualizan automáticamente
 */
export function ChatContainer({ filters, municipalities, onClearHistory, onFiltersChange }: ChatContainerProps) {
  const [chatKey, setChatKey] = useState(0); // Key para forzar reinicio del hook useChat

  const { messages, input, handleInputChange, handleSubmit, isLoading, error, append, data, setMessages, reload, setInput } = useChat({
    api: '/api/chat',
    id: `chat-${chatKey}`, // Cambiar key reinicia el hook completamente
    onError: (err) => {
      console.error('Chat error:', err);
    }
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isUserAtBottom = useRef(true);

  // Memoizar remarkPlugins para evitar recrearlos en cada render
  const remarkPlugins = useMemo(() => [remarkGfm], []);

  // Memoizar componentes de ReactMarkdown para evitar recrearlos en cada render
  // Mejora esperada: 70% más rápido en mensajes largos
  const markdownComponents = useMemo(() => ({
    a: ({ node, ...props }: any) => (
      <a {...props} target="_blank" rel="noopener noreferrer" />
    ),
    table: ({ node, ...props }: any) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700 border border-slate-200 dark:border-slate-700 rounded-lg" {...props} />
      </div>
    ),
    thead: ({ node, ...props }: any) => (
      <thead className="bg-slate-100 dark:bg-slate-800" {...props} />
    ),
    tbody: ({ node, ...props }: any) => (
      <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-700" {...props} />
    ),
    tr: ({ node, ...props }: any) => (
      <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors" {...props} />
    ),
    th: ({ node, ...props }: any) => (
      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider" {...props} />
    ),
    td: ({ node, ...props }: any) => (
      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400 whitespace-nowrap" {...props} />
    ),
  }), []);

  // Manejar Shift+Enter para nueva línea, Enter solo para enviar
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevenir el salto de línea por defecto
      handleFormSubmit(e as any); // Enviar el formulario
    }
    // Si es Shift+Enter, dejar que el textarea maneje el salto de línea normalmente
  };

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

  // Función de guardado con debounce (500ms)
  // Reducción esperada: 95% en escrituras (200 → 10 por respuesta)
  const debouncedSaveHistory = useMemo(
    () => debounce((msgs: any[]) => {
      localStorage.setItem('chat-history', JSON.stringify(msgs));
    }, 500),
    []
  );

  // Guardar historial en localStorage cuando cambian los mensajes (con debounce)
  useEffect(() => {
    debouncedSaveHistory(messages);
  }, [messages, debouncedSaveHistory]);

  // Detectar si usuario está al final del scroll
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const threshold = 100; // px desde el final
    const isAtBottom =
      target.scrollHeight - target.scrollTop - target.clientHeight < threshold;
    isUserAtBottom.current = isAtBottom;
  };

  // Auto-scroll inteligente: solo si usuario está al final
  // Evita arrastrar al usuario si está leyendo mensajes anteriores
  useEffect(() => {
    if (isUserAtBottom.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Código eliminado: Auto-reenvío de query pendiente (Estrategia B deprecada)

  // Preguntas frecuentes - editar aquí para agregar más
  const faqQuestions = [
    '¿Cuáles municipios tienen información disponible?',
    '¿Cómo busco una ordenanza específica?',
    '¿Qué tipos de normativas puedo consultar?',
    '¿Cómo cito una norma en mi búsqueda?',
  ];

  // Manejar click en FAQ
  const handleFaqClick = (question: string) => {
    append({
      role: 'user',
      content: question,
    });
  };

  // Handler interceptado para el formulario
  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) return;

    // Resetear altura del textarea después de enviar
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    // ✅ ESTRATEGIA A: Extraer filtros automáticamente de la query
    const uiFilters = {
      municipality: filters.municipality,
      type: filters.ordinanceType === 'all' ? undefined : filters.ordinanceType,
      dateFrom: filters.dateFrom,
      dateTo: filters.dateTo
    };

    const extractedFilters = extractFiltersFromQuery(input, municipalities, uiFilters);

    // Construir filtros finales para enviar al backend
    const finalFilters = {
      municipality: extractedFilters.municipality,
      ordinanceType: extractedFilters.type,
      dateFrom: extractedFilters.dateFrom,
      dateTo: extractedFilters.dateTo
    };

    // 🔄 SINCRONIZACIÓN: Actualizar UI con filtros extraídos
    if (onFiltersChange) {
      const hasNewFilters =
        (extractedFilters.municipality && extractedFilters.municipality !== filters.municipality) ||
        (extractedFilters.type && extractedFilters.type !== filters.ordinanceType) ||
        (extractedFilters.dateFrom && extractedFilters.dateFrom !== filters.dateFrom) ||
        (extractedFilters.dateTo && extractedFilters.dateTo !== filters.dateTo);

      if (hasNewFilters) {
        onFiltersChange({
          municipality: extractedFilters.municipality || filters.municipality,
          ordinanceType: (extractedFilters.type as any) || filters.ordinanceType,
          dateFrom: extractedFilters.dateFrom || filters.dateFrom,
          dateTo: extractedFilters.dateTo || filters.dateTo,
        });
      }
    }

    // ✅ Enviar al chat con filtros aplicados (búsqueda optimizada)
    handleSubmit(e, {
      body: {
        filters: finalFilters
      }
    });
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950">
      {/* Área de mensajes */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6"
      >
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Mensaje de bienvenida */}
          {messages.length === 0 && (
            <div className="animate-fade-in">
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-2xl mb-4">
                  <Sparkles className="w-8 h-8 text-primary-600 dark:text-primary-400" />
                </div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                  ¿En qué puedo ayudarte?
                </h2>
                <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
                  Consultá legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires.
                </p>
              </div>

              {/* Preguntas frecuentes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {faqQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleFaqClick(question)}
                    disabled={isLoading}
                    className="flex items-center gap-3 p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:border-primary-500 dark:hover:border-primary-500 hover:shadow-md transition-all text-left disabled:opacity-50"
                  >
                    <div className="w-8 h-8 bg-slate-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
                      <Bot className="w-4 h-4 text-slate-600 dark:text-slate-400" />
                    </div>
                    <span className="text-sm text-slate-700 dark:text-slate-300">
                      {question}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Mensajes del chat */}
          {messages.map((message) => (
              <div
                key={message.id}
                className={clsx(
                  'flex gap-4 animate-slide-up',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}

                <div
                  className={clsx(
                    'max-w-[80%] rounded-2xl px-5 py-3',
                    message.role === 'user'
                      ? 'bg-primary-500 text-white'
                      : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800'
                  )}
                >
                  <div className={clsx(
                    'prose prose-sm max-w-none',
                    message.role === 'user'
                      ? 'prose-invert'
                      : 'prose-slate dark:prose-invert prose-headings:text-slate-800 dark:prose-headings:text-slate-200 prose-p:text-slate-700 dark:prose-p:text-slate-300 prose-strong:text-slate-800 dark:prose-strong:text-slate-200 prose-li:text-slate-700 dark:prose-li:text-slate-300 prose-table:text-sm'
                  )}>
                    {message.role === 'user' ? (
                      <p className="text-white">{message.content}</p>
                    ) : (
                      <ReactMarkdown
                        remarkPlugins={remarkPlugins}
                        components={markdownComponents}
                      >
                        {message.content}
                      </ReactMarkdown>
                    )}
                  </div>

                  {/* Mostrar Citations y TokenUsage si es el mensaje del asistente y es el último mensaje */}
                  {(() => {
                    const sourcesData = Array.isArray(data)
                      ? (data as any[])
                          .filter(d => d.type === 'sources')
                          .pop()?.sources || []
                      : [];

                    const usageData = Array.isArray(data)
                      ? (data as any[])
                          .filter(d => d.type === 'usage')
                          .pop()?.usage
                      : undefined;

                    const isLastAssistantMessage = message.role === 'assistant' &&
                      message.id === messages[messages.length - 1]?.id;

                    return isLastAssistantMessage && (
                      <>
                        {sourcesData.length > 0 && (
                          <Citations sources={sourcesData} />
                        )}
                        <TokenUsage
                          promptTokens={usageData?.promptTokens}
                          completionTokens={usageData?.completionTokens}
                          totalTokens={usageData?.totalTokens}
                          model={usageData?.model}
                        />
                      </>
                    );
                  })()}
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
                  </div>
                )}
              </div>
            ))}

          {/* Indicador de escritura */}
          {isLoading && messages[messages.length - 1]?.role === 'user' && (
            <div className="flex gap-4 justify-start animate-slide-up">
              <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl px-5 py-3">
                <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Buscando información...</span>
                </div>
              </div>
            </div>
          )}

          {/* Mensaje de error */}
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400 flex flex-col gap-2">
              <p className="font-semibold">Hubo un error al procesar tu mensaje.</p>
              <p className="text-xs opacity-80">{error.message}</p>
              <button
                onClick={() => reload()}
                className="mt-2 text-xs font-bold uppercase tracking-wider hover:underline text-left"
              >
                Reintentar consulta
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Área de entrada */}
      <div className="p-4 bg-white dark:bg-slate-900">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleFormSubmit} className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={
                filters.municipality
                  ? `Preguntá sobre ${filters.municipality}...`
                  : `Ej: "decretos de Carlos Tejedor en 2025"`
              }
              rows={1}
              className="w-full pl-4 pr-12 py-3 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none overflow-hidden"
              disabled={isLoading}
              style={{
                minHeight: '44px',
                maxHeight: '200px',
              }}
              onInput={(e) => {
                // Auto-resize del textarea
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = Math.min(target.scrollHeight, 200) + 'px';
              }}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
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
    </div>
  );
}
