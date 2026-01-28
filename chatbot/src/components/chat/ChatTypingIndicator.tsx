/**
 * ChatTypingIndicator.tsx
 *
 * Indicador de que el asistente está escribiendo.
 */

'use client';

import { Bot, Loader2 } from '@/lib/icons';

export function ChatTypingIndicator() {
  return (
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
  );
}
