/**
 * ChatWelcome.tsx
 *
 * Pantalla de bienvenida con preguntas frecuentes.
 */

'use client';

import { Sparkles, Bot } from '@/lib/icons';
import type { ChatMessage } from '@/lib/types';

interface ChatWelcomeProps {
  isLoading: boolean;
  onQuestionClick: (question: string) => void;
}

const faqQuestions = [
  '¿Cuáles municipios tienen información disponible?',
  '¿Cómo busco una ordenanza específica?',
  '¿Qué tipos de normativas puedo consultar?',
  '¿Cómo cito una norma en mi búsqueda?',
];

export function ChatWelcome({ isLoading, onQuestionClick }: ChatWelcomeProps) {
  return (
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

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {faqQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
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
  );
}
