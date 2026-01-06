/**
 * Citations.tsx
 *
 * Componente para visualizar las fuentes legales citadas por el asistente.
 * Muestra el tipo de norma, título, municipio y estado de vigencia.
 *
 * @version 1.1.0
 * @created 2025-12-31
 * @modified 2025-12-31
 * @author Kilo Code
 *
 * @dependencies
 *   - lucide-react: ^0.400.0
 *   - clsx: ^2.1.0
 */

'use client';

import { ExternalLink, FileText } from '@/lib/icons';
import { clsx } from 'clsx';

interface Source {
  title: string;
  url: string;
  municipality: string;
  type: string;
  status: string;
}

interface CitationsProps {
  sources: Source[];
}

/**
 * Componente para mostrar las fuentes legales citadas
 */
export function Citations({ sources }: CitationsProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
      <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <FileText className="w-3 h-3" />
        Fuentes Consultadas
      </h4>
      <div className="grid grid-cols-1 gap-2">
        {sources.map((source, index) => (
          <a
            key={index}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:border-primary-500 dark:hover:border-primary-500 transition-colors group"
          >
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-900 dark:text-slate-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  {source.type.toUpperCase()} {source.title}
                </span>
                <span className={clsx(
                  "text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase",
                  source.status === 'vigente' ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
                  source.status === 'derogada' ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                  source.status === 'modificada' ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                  "bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-400"
                )}>
                  {source.status}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 dark:text-slate-500">
                Municipio de {source.municipality}
              </span>
            </div>
            <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-primary-500 transition-colors" />
          </a>
        ))}
      </div>
    </div>
  );
}
