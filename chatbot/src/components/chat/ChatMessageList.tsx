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
import type { UIMessage } from '@ai-sdk/react';
import type { Source } from '@/lib/types';
import { Citations } from './Citations';
import { TokenUsage } from './TokenUsage';

interface ChatMessageListProps {
  messages: UIMessage[];
}

// Tipos para los datos del metadata
interface MessageMetadata {
  sources?: Source[];
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
    model: string;
  };
}

// Extended Message type with metadata
interface MessageWithMetadata extends UIMessage {
  metadata?: MessageMetadata;
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

// Extraer sources del metadata del mensaje
function extractSourcesFromMetadata(metadata: unknown): Source[] {
  if (!metadata || typeof metadata !== 'object') return [];
  const meta = metadata as MessageMetadata;
  return meta.sources || [];
}

// Extraer contenido de texto del mensaje (UIMessage usa parts)
function getMessageText(message: UIMessage): string {
  return message.parts?.map(p => p.type === 'text' ? p.text : '').join('') || '';
}

// Limpiar el contenido removiendo el JSON de fuentes
function cleanContent(content: string): string {
  return content.replace(/<!--SOURCES:.+?-->/g, '');
}

// Extraer usage del metadata del mensaje
function extractUsageFromMetadata(metadata: unknown): MessageMetadata['usage'] | undefined {
  if (!metadata || typeof metadata !== 'object') return undefined;
  const meta = metadata as MessageMetadata;
  return meta.usage;
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

export function ChatMessageList({ messages }: ChatMessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [autoScrolled, setAutoScrolled] = useState<Set<string>>(new Set());

  // Auto-scroll al final cuando hay nuevos mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-scroll hacia las fuentes cuando el último mensaje termina de generarse
  useEffect(() => {
    const lastMessage = messages[messages.length - 1] as MessageWithMetadata | undefined;
    if (!lastMessage || lastMessage.role !== 'assistant') return;

    const messageId = lastMessage.id;
    // Ya hicimos auto-scroll para este mensaje
    if (autoScrolled.has(messageId)) return;

    // Extraer fuentes del metadata o del contenido
    const messageContent = getMessageText(lastMessage);
    const sources = extractSourcesFromMetadata(lastMessage.metadata) || extractSourcesFromContent(messageContent);

    // Solo hacer auto-scroll si hay fuentes y el mensaje está completo
    if (sources.length > 0 && messageContent) {
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
  }, [messages, autoScrolled]);

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
                <p className="text-white">{getMessageText(message)}</p>
              ) : (
                <ReactMarkdown
                  remarkPlugins={remarkPlugins}
                  components={markdownComponents}
                >
                  {cleanContent(getMessageText(message))}
                </ReactMarkdown>
              )}
            </div>

            {/* Metadatos del mensaje - fuentes desde metadata */}
            {message.role === 'assistant' && getMessageText(message) && (
              <MessageMetadata message={message as MessageWithMetadata} messageId={message.id} />
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
  message: MessageWithMetadata;
  messageId: string;
}

function MessageMetadata({ message, messageId }: MessageMetadataProps) {
  // Extraer fuentes del metadata o del contenido
  let sourcesData = extractSourcesFromMetadata(message.metadata);
  const messageText = getMessageText(message);
  if (sourcesData.length === 0 && messageText) {
    sourcesData = extractSourcesFromContent(messageText);
  }

  const usageData = extractUsageFromMetadata(message.metadata);

  if (sourcesData.length === 0 && !usageData) {
    return null;
  }

  // Indicador visual dentro del mensaje cuando hay fuentes
  const showInlineIndicator = sourcesData.length > 0;

  return (
    <>
      {showInlineIndicator && (
        <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
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
