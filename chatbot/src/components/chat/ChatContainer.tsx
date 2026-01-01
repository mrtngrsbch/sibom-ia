'use client';

import { useRef, useEffect, useState } from 'react';
import { useChat } from 'ai/react';
import { Send, Bot, User, Sparkles, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import ReactMarkdown from 'react-markdown';
import { Citations } from './Citations';

/**
 * Componente principal del chat
 * @description Interface de chat optimizada usando AI SDK con persistencia
 */
export function ChatContainer() {
  const [chatKey, setChatKey] = useState(0); // Key para forzar reinicio del hook useChat

  const { messages, input, handleInputChange, handleSubmit, isLoading, error, append, data, setMessages, reload, setInput } = useChat({
    api: '/api/chat',
    id: `chat-${chatKey}`, // Cambiar key reinicia el hook completamente
    onError: (err) => {
      console.error('Chat error:', err);
    }
  });

  /**
   * Limpia el chat sin recargar la página
   * Resetea mensajes, localStorage, e incrementa la key para reiniciar useChat
   */
  const handleClearChat = () => {
    setMessages([]);
    setInput('');
    localStorage.removeItem('chat-history');
    setChatKey(prev => prev + 1); // Incrementar key fuerza reinicio limpio del hook
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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
    localStorage.setItem('chat-history', JSON.stringify(messages));
  }, [messages]);

  // Auto-scroll al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Preguntas frecuentes - editar aquí para agregar más
  const faqQuestions = [
    '¿Qué municipios tienen información disponible?',
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

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-950">
      {/* Área de mensajes */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
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
                    : 'prose-slate dark:prose-invert prose-headings:text-slate-800 dark:prose-headings:text-slate-200 prose-p:text-slate-700 dark:prose-p:text-slate-300 prose-strong:text-slate-800 dark:prose-strong:text-slate-200 prose-li:text-slate-700 dark:prose-li:text-slate-300'
                )}>
                  {message.role === 'user' ? (
                    <p className="text-white">{message.content}</p>
                  ) : (
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  )}
                </div>

                {/* Mostrar Citations si es el mensaje del asistente y es el último mensaje */}
                {message.role === 'assistant' &&
                 message.id === messages[messages.length - 1]?.id &&
                 data && data.length > 0 && (
                  <Citations
                    sources={Array.isArray(data)
                      ? (data as any[])
                          .filter(d => d.type === 'sources')
                          .pop()?.sources || []
                      : []}
                  />
                )}
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
      <div className="p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
        <div className="max-w-3xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={handleInputChange}
              placeholder="Escribí tu pregunta sobre legislación municipal..."
              className="w-full pl-4 pr-12 py-3 bg-slate-100 dark:bg-slate-800 border-0 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 placeholder:text-slate-400 dark:placeholder:text-slate-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-label="Enviar mensaje"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          
          {/* Footer del chat */}
          <div className="mt-2 flex items-center justify-between">
            <button
              onClick={handleClearChat}
              className="text-xs text-slate-400 hover:text-red-500 transition-colors"
            >
              Limpiar historial y nuevo chat
            </button>
            <p className="text-center text-xs text-slate-400 dark:text-slate-500">
              Las respuestas son generadas por IA. Verificá la información en las fuentes oficiales.
            </p>
            <div className="w-20" /> {/* Spacer */}
          </div>
        </div>
      </div>
    </div>
  );
}
