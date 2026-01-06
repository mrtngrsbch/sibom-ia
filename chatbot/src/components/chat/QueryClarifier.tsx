'use client';

import { Bot } from '@/lib/icons';
import { ClarificationNeeded } from '@/lib/query-analyzer';

interface QueryClarifierProps {
  clarification: ClarificationNeeded;
  onSelect: (selection: string) => void;
}

/**
 * Componente de clarificación inline estilo Claude
 * @description Pregunta al usuario cuando la query es ambigua
 */
export function QueryClarifier({ clarification, onSelect }: QueryClarifierProps) {
  return (
    <div className="flex gap-4 justify-start animate-slide-up">
      <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded-xl px-5 py-3 max-w-[80%]">
        <p className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
          🤔 {clarification.message}
        </p>
        <div className="flex flex-wrap gap-2">
          {clarification.suggestions.map(suggestion => (
            <button
              key={suggestion}
              onClick={() => onSelect(suggestion)}
              className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-blue-200 dark:border-blue-700 rounded-lg text-sm text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-800 transition-colors"
            >
              {suggestion}
            </button>
          ))}
          <button
            onClick={() => onSelect('all')}
            className="px-3 py-1.5 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors"
          >
            Buscar en todos
          </button>
        </div>
      </div>
    </div>
  );
}
