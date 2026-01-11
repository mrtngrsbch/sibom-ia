/**
 * Citations.tsx
 *
 * Componente para visualizar las fuentes legales citadas por el asistente.
 * Incluye manejo inteligente de listados grandes con:
 * - Warning para listados >500 resultados
 * - Buscador interno para filtrar
 * - Paginación con "Cargar más"
 * - Estado colapsado/expandido
 *
 * @version 2.0.0
 * @created 2025-12-31
 * @modified 2026-01-10
 * @author Kilo Code
 *
 * @dependencies
 *   - lucide-react: ^0.400.0
 *   - clsx: ^2.1.0
 */

'use client';

import { FileText, ExternalLink, AlertTriangle, Search, X, ChevronDown, ChevronUp } from '@/lib/icons';
import { clsx } from 'clsx';
import { useState, useMemo } from 'react';

interface Source {
  title: string;
  url: string;
  municipality: string;
  type: string;
  status?: string;
  documentTypes?: string[];
}

interface CitationsProps {
  sources: Source[];
}

/**
 * Componente para mostrar las fuentes legales citadas
 * Con manejo inteligente de listados grandes
 */
export function Citations({ sources }: CitationsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [displayCount, setDisplayCount] = useState(50);

  // Filtrar fuentes según búsqueda
  const filteredSources = useMemo(() => {
    if (!searchQuery.trim()) return sources;
    
    const query = searchQuery.toLowerCase();
    return sources.filter(source => 
      source.title.toLowerCase().includes(query) ||
      source.municipality.toLowerCase().includes(query) ||
      source.type.toLowerCase().includes(query)
    );
  }, [sources, searchQuery]);

  // Fuentes a mostrar (con paginación)
  const displayedSources = useMemo(() => {
    return filteredSources.slice(0, displayCount);
  }, [filteredSources, displayCount]);

  const hasMore = displayedSources.length < filteredSources.length;
  const isLargeList = sources.length > 500;
  const isMediumList = sources.length > 100 && sources.length <= 500;

  if (sources.length === 0) {
    return null;
  }

  // Para listados muy grandes (>500), mostrar warning primero
  if (isLargeList && !isExpanded) {
    return (
      <div className="mt-6 border-t border-slate-200 dark:border-slate-700 pt-4">
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-yellow-900 dark:text-yellow-200 mb-2">
                Listado muy extenso ({sources.length} resultados)
              </h4>
              <p className="text-sm text-yellow-800 dark:text-yellow-300 mb-3">
                Este listado contiene {sources.length} documentos. Para una mejor experiencia:
              </p>
              <ul className="text-sm text-yellow-800 dark:text-yellow-300 space-y-1 mb-4 ml-4">
                <li>• Usa los filtros arriba para refinar tu búsqueda</li>
                <li>• Busca por número específico (ej: "decreto 2025")</li>
                <li>• Filtra por rango de fechas más corto</li>
              </ul>
              <div className="flex flex-col sm:flex-row gap-2">
                <button
                  onClick={() => setIsExpanded(true)}
                  className="flex items-center justify-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  Ver listado completo ({sources.length})
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Título colapsado */}
        <button
          onClick={() => setIsExpanded(true)}
          className="mt-4 w-full flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
        >
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-500 dark:text-slate-400" />
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              {sources.length} Fuentes Consultadas
            </span>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-500 dark:text-slate-400" />
        </button>
      </div>
    );
  }

  return (
    <div className="mt-6 border-t border-slate-200 dark:border-slate-700 pt-4">
      {/* Header con contador y botón colapsar */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-2">
          <FileText className="w-3 h-3" />
          {sources.length} Fuentes Consultadas
        </h4>
        {isLargeList && isExpanded && (
          <button
            onClick={() => {
              setIsExpanded(false);
              setSearchQuery('');
              setDisplayCount(50);
            }}
            className="text-xs text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 flex items-center gap-1"
          >
            <ChevronUp className="w-3 h-3" />
            Colapsar
          </button>
        )}
      </div>

      {/* Warning para listas medianas (101-500) */}
      {isMediumList && (
        <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-xs text-blue-800 dark:text-blue-300">
            💡 Tip: Este listado tiene {sources.length} resultados. Usa el buscador abajo para encontrar documentos específicos.
          </p>
        </div>
      )}

      {/* Buscador interno (para listas >100) */}
      {(isLargeList || isMediumList) && (
        <div className="mb-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setDisplayCount(50); // Reset al buscar
              }}
              placeholder="Buscar por número, palabra clave..."
              className="w-full pl-10 pr-10 py-2 text-sm border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setDisplayCount(50);
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          {searchQuery && (
            <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
              🎯 {filteredSources.length === 0 ? 'No se encontraron' : `Encontrados ${filteredSources.length}`} resultado{filteredSources.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      )}

      {/* Contador de resultados mostrados */}
      {filteredSources.length > 50 && (
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
          Mostrando {displayedSources.length} de {filteredSources.length} resultado{filteredSources.length !== 1 ? 's' : ''}
        </p>
      )}

      {/* Lista de fuentes */}
      <div className="grid grid-cols-1 gap-2">
        {displayedSources.map((source, index) => (
          <a
            key={index}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-start gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/10 transition-all"
          >
            <FileText className="w-4 h-4 text-slate-400 dark:text-slate-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                    {source.title}
                  </p>
                  {source.status && (
                    <span className={clsx(
                      "text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase",
                      source.status === 'vigente' ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" :
                      source.status === 'derogada' ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" :
                      source.status === 'modificada' ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" :
                      "bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-400"
                    )}>
                      {source.status}
                    </span>
                  )}
                </div>
                <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-blue-500 flex-shrink-0 mt-0.5" />
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {source.municipality}
              </p>
            </div>
          </a>
        ))}
      </div>

      {/* Botón "Cargar más" */}
      {hasMore && (
        <button
          onClick={() => setDisplayCount(prev => prev + 50)}
          className="mt-3 w-full py-2 px-4 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
        >
          <ChevronDown className="w-4 h-4" />
          Cargar 50 más ({filteredSources.length - displayedSources.length} restantes)
        </button>
      )}

      {/* Mensaje cuando no hay resultados de búsqueda */}
      {searchQuery && filteredSources.length === 0 && (
        <div className="text-center py-8">
          <Search className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No se encontraron resultados para "{searchQuery}"
          </p>
          <button
            onClick={() => setSearchQuery('')}
            className="mt-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Limpiar búsqueda
          </button>
        </div>
      )}
    </div>
  );
}
