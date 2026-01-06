'use client';

import { useState, useRef, useEffect } from 'react';
import { X, MapPin, FileText, Calendar, ChevronDown, Trash2 } from '@/lib/icons';
import { Badge } from '@/components/ui/badge';
import type { ChatFilters } from '@/lib/types';

interface FilterBarProps {
  filters: ChatFilters;
  municipalities: string[];
  onChange: (filters: ChatFilters) => void;
  onClearHistory?: () => void;
}

/**
 * Barra de filtros estilo badges compactos
 * @description Filtros mostrados como badges en la parte inferior
 */
export function FilterBar({ filters, municipalities, onChange, onClearHistory }: FilterBarProps) {
  const [showMunicipalityDropdown, setShowMunicipalityDropdown] = useState(false);
  const [showTypeDropdown, setShowTypeDropdown] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTooltip, setShowTooltip] = useState(true);

  const municipalityRef = useRef<HTMLDivElement>(null);
  const typeRef = useRef<HTMLDivElement>(null);
  const dateRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdowns al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (municipalityRef.current && !municipalityRef.current.contains(event.target as Node)) {
        setShowMunicipalityDropdown(false);
      }
      if (typeRef.current && !typeRef.current.contains(event.target as Node)) {
        setShowTypeDropdown(false);
      }
      if (dateRef.current && !dateRef.current.contains(event.target as Node)) {
        setShowDatePicker(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const updateFilter = (key: keyof ChatFilters, value: any) => {
    onChange({ ...filters, [key]: value });
  };

  const typeLabels: Record<string, string> = {
    all: 'Todos los tipos',
    ordenanza: 'Ordenanzas',
    decreto: 'Decretos',
    boletin: 'Boletines',
    resolucion: 'Resoluciones',
    disposicion: 'Disposiciones',
    convenio: 'Convenios',
    licitacion: 'Licitaciones'
  };

  return (
    <div className="bg-slate-50 dark:bg-slate-950 p-4 relative">
      <div className="max-w-3xl mx-auto">
        {/* Tooltip de ayuda */}
        {showTooltip && !filters.municipality && (
          <div className="mb-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-700 dark:text-blue-300 flex items-start gap-2">
            <span>💡</span>
            <div className="flex-1">
              <p className="font-medium mb-1">Consejo: Usá los filtros para búsquedas específicas</p>
              <p className="text-xs opacity-90">Seleccioná un municipio, tipo de normativa o rango de fechas para resultados más precisos.</p>
            </div>
            <button
              onClick={() => setShowTooltip(false)}
              className="text-blue-700 dark:text-blue-300 hover:opacity-70"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Filtros:
          </span>

          {/* Municipio Badge */}
          <div className="relative" ref={municipalityRef}>
            <Badge
              variant={filters.municipality ? "default" : "outline"}
              className="cursor-pointer hover:opacity-80 transition-opacity pl-2 pr-1 py-1 gap-1"
              onClick={() => setShowMunicipalityDropdown(!showMunicipalityDropdown)}
            >
              <MapPin className={`w-3 h-3 ${filters.municipality ? 'text-[rgb(218,41,28)]' : 'text-slate-500 dark:text-slate-400'}`} />
              <span className={filters.municipality ? 'text-[rgb(218,41,28)]' : 'text-slate-500 dark:text-slate-400'}>{filters.municipality || 'Municipio'}</span>
              {filters.municipality ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    updateFilter('municipality', null);
                  }}
                  className="ml-1 hover:bg-white/20 rounded-full p-0.5"
                >
                  <X className="w-3 h-3 text-[rgb(218,41,28)]" />
                </button>
              ) : (
                <ChevronDown className="w-3 h-3 text-slate-500 dark:text-slate-400" />
              )}
            </Badge>

            {/* Dropdown Municipios */}
            {showMunicipalityDropdown && (
              <div className="absolute top-full mt-2 left-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg max-h-60 overflow-y-auto w-56 z-50">
                <div className="p-2 space-y-1">
                  {municipalities.map((muni) => (
                    <button
                      key={muni}
                      onClick={() => {
                        updateFilter('municipality', muni);
                        setShowMunicipalityDropdown(false);
                      }}
                      className="w-full text-left px-3 py-2 text-sm rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
                    >
                      {muni}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Tipo Badge */}
          <div className="relative" ref={typeRef}>
            <Badge
              variant={filters.ordinanceType !== 'all' ? "default" : "outline"}
              className="cursor-pointer hover:opacity-80 transition-opacity pl-2 pr-1 py-1 gap-1"
              onClick={() => setShowTypeDropdown(!showTypeDropdown)}
            >
              <FileText className={`w-3 h-3 ${filters.ordinanceType !== 'all' ? 'text-[rgb(218,41,28)]' : 'text-slate-500 dark:text-slate-400'}`} />
              <span className={filters.ordinanceType !== 'all' ? 'text-[rgb(218,41,28)]' : 'text-slate-500 dark:text-slate-400'}>{typeLabels[filters.ordinanceType]}</span>
              {filters.ordinanceType !== 'all' ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    updateFilter('ordinanceType', 'all');
                  }}
                  className="ml-1 hover:bg-white/20 rounded-full p-0.5"
                >
                  <X className="w-3 h-3 text-[rgb(218,41,28)]" />
                </button>
              ) : (
                <ChevronDown className="w-3 h-3 text-slate-500 dark:text-slate-400" />
              )}
            </Badge>

            {/* Dropdown Tipos */}
            {showTypeDropdown && (
              <div className="absolute top-full mt-2 left-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg w-48 max-h-80 overflow-y-auto z-50">
                <div className="p-2 space-y-1">
                  {(['all', 'ordenanza', 'decreto', 'boletin', 'resolucion', 'disposicion', 'convenio', 'licitacion'] as const).map((type) => (
                    <button
                      key={type}
                      onClick={() => {
                        updateFilter('ordinanceType', type);
                        setShowTypeDropdown(false);
                      }}
                      className="w-full text-left px-3 py-2 text-sm rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
                    >
                      {typeLabels[type]}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Fecha Badge */}
          <div className="relative" ref={dateRef}>
            <Badge
              variant={filters.dateFrom || filters.dateTo ? "default" : "outline"}
              className="cursor-pointer hover:opacity-80 transition-opacity pl-2 pr-1 py-1 gap-1"
              onClick={() => setShowDatePicker(!showDatePicker)}
            >
              <Calendar className={`w-3 h-3 ${filters.dateFrom || filters.dateTo ? 'text-[rgb(218,41,28)]' : 'text-slate-500 dark:text-slate-400'}`} />
              <span className={filters.dateFrom || filters.dateTo ? 'text-[rgb(218,41,28)]' : 'text-slate-500 dark:text-slate-400'}>
                {filters.dateFrom || filters.dateTo
                  ? `${filters.dateFrom || '...'} - ${filters.dateTo || '...'}`
                  : 'Fecha'}
              </span>
              {(filters.dateFrom || filters.dateTo) ? (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    updateFilter('dateFrom', null);
                    updateFilter('dateTo', null);
                  }}
                  className="ml-1 hover:bg-white/20 rounded-full p-0.5"
                >
                  <X className="w-3 h-3 text-[rgb(218,41,28)]" />
                </button>
              ) : (
                <ChevronDown className="w-3 h-3 text-slate-500 dark:text-slate-400" />
              )}
            </Badge>

            {/* Dropdown Fechas */}
            {showDatePicker && (
              <div className="absolute top-full mt-2 left-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg p-4 w-72 z-50">
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Desde
                    </label>
                    <input
                      type="date"
                      value={filters.dateFrom || ''}
                      onChange={(e) => updateFilter('dateFrom', e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Hasta
                    </label>
                    <input
                      type="date"
                      value={filters.dateTo || ''}
                      onChange={(e) => updateFilter('dateTo', e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-sm"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Botón limpiar filtros */}
          {(filters.municipality || filters.ordinanceType !== 'all' || filters.dateFrom || filters.dateTo) && (
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors pl-2 pr-2 py-1 gap-1"
              onClick={() => {
                onChange({
                  municipality: null,
                  ordinanceType: 'all',
                  dateFrom: null,
                  dateTo: null
                });
              }}
            >
              <X className="w-3 h-3 text-slate-500 dark:text-slate-400" />
              <span className="text-slate-500 dark:text-slate-400">Limpiar filtros</span>
            </Badge>
          )}

          {/* Botón limpiar historial */}
          {onClearHistory && (
            <Badge
              variant="outline"
              className="cursor-pointer hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors pl-2 pr-2 py-1 gap-1"
              onClick={onClearHistory}
            >
              <Trash2 className="w-3 h-3 text-slate-500 dark:text-slate-400" />
              <span className="text-slate-500 dark:text-slate-400">Nuevo chat</span>
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}
