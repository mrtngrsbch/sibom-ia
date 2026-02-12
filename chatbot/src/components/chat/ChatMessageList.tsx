/**
 * ChatMessageList.tsx
 *
 * Lista de mensajes del chat con renderizado optimizado.
 */

'use client';

import { useRef, useEffect } from 'react';
import { Bot, User } from '@/lib/icons';
import { clsx } from 'clsx';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import type { Source } from '@/lib/types';
import { Citations } from './Citations';
import { TokenUsage } from './TokenUsage';
import type { ChatMessage } from '@/lib/types';

interface ChatMessageListProps {
  messages: any[];
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

function extractUsageFromData(data: unknown): { promptTokens: number; completionTokens: number; totalTokens: number; model: string } | undefined {
  if (!Array.isArray(data)) return undefined;
  const usageItem = data.find((d): d is StreamDataUsage => d?.type === 'usage');
  return usageItem?.usage;
}

// Helper para extraer el contenido de texto del mensaje
function getTextFromMessage(message: any): string {
  // 🔍 DIAGNÓSTICO: Log del formato del mensaje recibido
  console.log('[ChatMessageList] 📋 Mensaje completo:', JSON.stringify(message, null, 2));
  console.log('[ChatMessageList] 📋 ¿Tiene "content"?', 'content' in message);
  console.log('[ChatMessageList] 📋 ¿Tiene "parts"?', 'parts' in message);
  if (message.parts) {
    console.log('[ChatMessageList] 📋 Parts:', JSON.stringify(message.parts, null, 2));
  }
  
  // Soportar ambos formatos (content y parts) durante la migración
  if (message.content) {
    return message.content;
  }
  if (message.parts && Array.isArray(message.parts)) {
    return message.parts
      .filter((p: any) => p.type === 'text')
      .map((p: any) => p.text)
      .join('');
  }
  return '';
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

  // Auto-scroll al final cuando hay nuevos mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
                <p className="text-white">{getTextFromMessage(message)}</p>
              ) : (
                <ReactMarkdown
                  remarkPlugins={remarkPlugins}
                  components={markdownComponents}
                >
                  {getTextFromMessage(message)}
                </ReactMarkdown>
              )}
            </div>

            {/* Metadatos del mensaje */}
            {message.role === 'assistant' && message.content && (
              <MessageMetadata data={data} />
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
  data: unknown;
}

function MessageMetadata({ data }: MessageMetadataProps) {
  const sourcesData = extractSourcesFromData(data);
  const usageData = extractUsageFromData(data);

  if (sourcesData.length === 0 && !usageData) {
    return null;
  }

  return (
    <>
      {sourcesData.length > 0 && <Citations sources={sourcesData} />}
      <TokenUsage
        promptTokens={usageData?.promptTokens}
        completionTokens={usageData?.completionTokens}
        totalTokens={usageData?.totalTokens}
        model={usageData?.model}
      />
    </>
  );
}
