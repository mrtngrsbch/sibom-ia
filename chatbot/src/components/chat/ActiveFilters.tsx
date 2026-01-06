'use client';

import { X, Filter } from '@/lib/icons';
import { Badge } from '@/components/ui/badge';

export interface ActiveFiltersProps {
  municipality?: string | null;
  ordinanceType?: string;
  dateFrom?: string | null;
  dateTo?: string | null;
  onRemoveFilter: (filterKey: 'municipality' | 'ordinanceType' | 'dateFrom' | 'dateTo') => void;
  onShowAdvancedFilters?: () => void;
}

/**
 * Componente que muestra los filtros activos como badges
 * Solo se muestran los filtros que están realmente aplicados
 */
export function ActiveFilters({
  municipality,
  ordinanceType,
  dateFrom,
  dateTo,
  onRemoveFilter,
  onShowAdvancedFilters
}: ActiveFiltersProps) {
  const hasAnyFilter = municipality || (ordinanceType && ordinanceType !== 'all') || dateFrom || dateTo;

  // Formatear rango de fechas de forma legible
  const formatDateRange = () => {
    if (dateFrom && dateTo) {
      const from = new Date(dateFrom);
      const to = new Date(dateTo);

      // Si es el mismo año completo (01/01 a 31/12), mostrar solo el año
      if (
        from.getMonth() === 0 && from.getDate() === 1 &&
        to.getMonth() === 11 && to.getDate() === 31 &&
        from.getFullYear() === to.getFullYear()
      ) {
        return `Año ${from.getFullYear()}`;
      }

      // Si es el mismo año, mostrar mes/día
      if (from.getFullYear() === to.getFullYear()) {
        return `${from.toLocaleDateString('es-AR', { month: 'short', day: 'numeric' })} - ${to.toLocaleDateString('es-AR', { month: 'short', day: 'numeric', year: 'numeric' })}`;
      }

      // Años diferentes
      return `${from.toLocaleDateString('es-AR', { year: 'numeric', month: 'short' })} - ${to.toLocaleDateString('es-AR', { year: 'numeric', month: 'short' })}`;
    }

    if (dateFrom) return `Desde ${new Date(dateFrom).toLocaleDateString('es-AR')}`;
    if (dateTo) return `Hasta ${new Date(dateTo).toLocaleDateString('es-AR')}`;
    return null;
  };

  const dateLabel = formatDateRange();

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Badges de filtros activos */}
      {municipality && (
        <Badge
          variant="secondary"
          className="gap-1.5 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          <span className="text-slate-700 dark:text-slate-300">{municipality}</span>
          <button
            onClick={() => onRemoveFilter('municipality')}
            className="hover:bg-slate-300 dark:hover:bg-slate-600 rounded-full p-0.5 transition-colors"
            aria-label={`Quitar filtro de municipio: ${municipality}`}
          >
            <X className="w-3 h-3" />
          </button>
        </Badge>
      )}

      {ordinanceType && ordinanceType !== 'all' && (
        <Badge
          variant="secondary"
          className="gap-1.5 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          <span className="text-slate-700 dark:text-slate-300 capitalize">{ordinanceType}</span>
          <button
            onClick={() => onRemoveFilter('ordinanceType')}
            className="hover:bg-slate-300 dark:hover:bg-slate-600 rounded-full p-0.5 transition-colors"
            aria-label={`Quitar filtro de tipo: ${ordinanceType}`}
          >
            <X className="w-3 h-3" />
          </button>
        </Badge>
      )}

      {dateLabel && (
        <Badge
          variant="secondary"
          className="gap-1.5 cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          <span className="text-slate-700 dark:text-slate-300">{dateLabel}</span>
          <button
            onClick={() => {
              onRemoveFilter('dateFrom');
              onRemoveFilter('dateTo');
            }}
            className="hover:bg-slate-300 dark:hover:bg-slate-600 rounded-full p-0.5 transition-colors"
            aria-label="Quitar filtro de fecha"
          >
            <X className="w-3 h-3" />
          </button>
        </Badge>
      )}

      {/* Botón "Filtros avanzados" - solo se muestra si NO hay filtros activos */}
      {!hasAnyFilter && onShowAdvancedFilters && (
        <Badge
          variant="outline"
          className="gap-1.5 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          onClick={onShowAdvancedFilters}
        >
          <Filter className="w-3 h-3 text-slate-500 dark:text-slate-400" />
          <span className="text-slate-500 dark:text-slate-400">Filtros avanzados</span>
        </Badge>
      )}

      {/* Indicador de filtros activos con botón para expandir */}
      {hasAnyFilter && onShowAdvancedFilters && (
        <Badge
          variant="outline"
          className="gap-1.5 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          onClick={onShowAdvancedFilters}
        >
          <Filter className="w-3 h-3 text-blue-500 dark:text-blue-400" />
          <span className="text-slate-500 dark:text-slate-400">Editar filtros</span>
        </Badge>
      )}
    </div>
  );
}
