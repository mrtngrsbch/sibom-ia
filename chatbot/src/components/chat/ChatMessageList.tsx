/**
 * ChatMessageList.tsx
 *
 * Lista de mensajes del chat con renderizado optimizado.
 */

'use client';

import { useRef, useEffect, useState } from 'react';
import { Bot, User, ChevronDown, FileText } from '@/lib/icons';
import { clsx } from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import type { Message } from '@ai-sdk/react';
import type { Source } from '@/lib/types';
import { Citations } from './Citations';
import { TokenUsage } from './TokenUsage';

interface ChatMessageListProps {
  messages: Message[];
  data: unknown;
}

// Tipos para los datos del stream
interface StreamDataSource {
  type: 'sources';
  sources: Source[];
}

interface StreamDataUsage {
  type: 'usage';
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
    model: string;
  };
}

// Helpers para extraer datos del stream
function extractSourcesFromData(data: unknown): Source[] {
  if (!Array.isArray(data)) return [];
  const sourcesItem = data.find((d): d is StreamDataSource => d?.type === 'sources');
  return sourcesItem?.sources || [];
}

// Extraer fuentes del contenido del mensaje (formato <!--SOURCES:{json}-->)
function extractSourcesFromContent(content: string): Source[] {
  const match = content.match(/<!--SOURCES:(.+?)-->/);
  if (match && match[1]) {
    try {
      const data = JSON.parse(match[1]);
      if (data.type === 'sources' && Array.isArray(data.sources)) {
        return data.sources;
      }
    } catch (e) {
      console.error('Error parsing sources from content:', e);
    }
  }
  return [];
}

// Limpiar el contenido removiendo el JSON de fuentes
function cleanContent(content: string): string {
  return content.replace(/<!--SOURCES:.+?-->/g, '');
}

function extractUsageFromData(data: unknown): { promptTokens: number; completionTokens: number; totalTokens: number; model: string } | undefined {
  if (!Array.isArray(data)) return undefined;
  const usageItem = data.find((d): d is StreamDataUsage => d?.type === 'usage');
  return usageItem?.usage;
}

// Componentes de markdown memoizados
const markdownComponents: Components = {
  a: ({ node, ...props }) => (
    <a {...props} target="_blank" rel="noopener noreferrer" />
  ),
  table: ({ node, ...props }) => (
    <div className="overflow-x-auto my-4">
      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700 border border-slate-200 dark:border-slate-700 rounded-lg" {...props} />
    </div>
  ),
  thead: ({ node, ...props }) => (
    <thead className="bg-slate-100 dark:bg-slate-800" {...props} />
  ),
  tbody: ({ node, ...props }) => (
    <tbody className="bg-white dark:bg-slate-900 divide-y divide-slate-200 dark:divide-slate-700" {...props} />
  ),
  tr: ({ node, ...props }) => (
    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors" {...props} />
  ),
  th: ({ node, ...props }) => (
    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider" {...props} />
  ),
  td: ({ node, ...props }) => (
    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400 whitespace-nowrap" {...props} />
  ),
};

const remarkPlugins = [remarkGfm];

export function ChatMessageList({ messages, data }: ChatMessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [autoScrolled, setAutoScrolled] = useState<Set<string>>(new Set());

  // Auto-scroll al final cuando hay nuevos mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-scroll hacia las fuentes cuando el último mensaje termina de generarse
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage || lastMessage.role !== 'assistant') return;

    const messageId = lastMessage.id;
    // Ya hicimos auto-scroll para este mensaje
    if (autoScrolled.has(messageId)) return;

    // Extraer fuentes del mensaje
    const sources = extractSourcesFromContent(lastMessage.content) || extractSourcesFromData(data);

    // Solo hacer auto-scroll si hay fuentes y el mensaje está completo
    if (sources.length > 0 && lastMessage.content && !lastMessage.content.includes('<think>')) {
      // Esperar un poco para que el DOM se actualice
      const timer = setTimeout(() => {
        const sourcesElement = document.getElementById(`sources-${messageId}`);
        if (sourcesElement) {
          sourcesElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          setAutoScrolled(prev => new Set(prev).add(messageId));
        }
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [messages, data, autoScrolled]);

  return (
    <>
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
                  {cleanContent(message.content)}
                </ReactMarkdown>
              )}
            </div>

            {/* Metadatos del mensaje - extraer fuentes del contenido si no hay data */}
            {message.role === 'assistant' && message.content && (
              <MessageMetadata message={message} data={data} messageId={message.id} />
            )}
          </div>

          {message.role === 'user' && (
            <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
            </div>
          )}
        </div>
      ))}

      <div ref={messagesEndRef} />
    </>
  );
}

interface MessageMetadataProps {
  message: Message;
  data: unknown;
  messageId: string;
}

function MessageMetadata({ message, data, messageId }: MessageMetadataProps) {
  // Primero intentar extraer del data global, si no hay, buscar en el contenido
  let sourcesData = extractSourcesFromData(data);
  if (sourcesData.length === 0 && message.content) {
    sourcesData = extractSourcesFromContent(message.content);
  }

  const usageData = extractUsageFromData(data);

  if (sourcesData.length === 0 && !usageData) {
    return null;
  }

  // Indicador visual dentro del mensaje cuando hay fuentes
  // Esto ayuda al usuario a saber que hay contenido más abajo
  const showInlineIndicator = sourcesData.length > 0;

  return (
    <>
      {showInlineIndicator && (
        <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <button
            onClick={() => {
              // Disparar evento para expandir las fuentes
              window.dispatchEvent(new Event('expand-citations'));
              // Scroll hacia las fuentes
              const sourcesElement = document.getElementById(`sources-${messageId}`);
              sourcesElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }}
            className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors group"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>{sourcesData.length} fuente{sourcesData.length !== 1 ? 's' : ''} consultada{sourcesData.length !== 1 ? 's' : ''}</span>
            <ChevronDown className="w-3.5 h-3.5 group-hover:translate-y-0.5 transition-transform" />
          </button>
        </div>
      )}
      <div id={`sources-${messageId}`}>
        {sourcesData.length > 0 && <Citations sources={sourcesData} />}
      </div>
      <TokenUsage
        promptTokens={usageData?.promptTokens}
        completionTokens={usageData?.completionTokens}
        totalTokens={usageData?.totalTokens}
        model={usageData?.model}
      />
    </>
  );
}
