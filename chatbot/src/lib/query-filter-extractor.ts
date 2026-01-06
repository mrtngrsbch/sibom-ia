/**
 * query-filter-extractor.ts
 *
 * Extrae filtros automáticamente de la consulta del usuario.
 * Detecta: municipio, año, rango de fechas, tipo de normativa.
 *
 * FIX: Bug donde "cuantas ordenanzas tuvo carlos tejedor en el 2025?"
 * no aplicaba el filtro de año 2025.
 */

import { SearchOptions } from './rag/retriever';

/**
 * Extrae el año mencionado en la query
 * @param query - Consulta del usuario
 * @returns Año como string (YYYY) o null
 */
export function extractYear(query: string): string | null {
  // Patrones comunes:
  // - "en el 2025"
  // - "del 2024"
  // - "en 2023"
  // - "año 2022"
  const yearPatterns = [
    /\ben\s+el\s+(\d{4})\b/i,
    /\bdel\s+(\d{4})\b/i,
    /\ben\s+(\d{4})\b/i,
    /\baño\s+(\d{4})\b/i,
    /\b(\d{4})\b/  // Fallback: cualquier número de 4 dígitos
  ];

  for (const pattern of yearPatterns) {
    const match = query.match(pattern);
    if (match && match[1]) {
      const year = parseInt(match[1], 10);
      // Validar que sea un año razonable (2010-2030)
      if (year >= 2010 && year <= 2030) {
        return match[1];
      }
    }
  }

  return null;
}

/**
 * Extrae el municipio mencionado en la query
 * @param query - Consulta del usuario
 * @param availableMunicipalities - Lista de municipios disponibles
 * @returns Nombre del municipio o null
 */
export function extractMunicipality(
  query: string,
  availableMunicipalities: string[]
): string | null {
  const lowerQuery = query.toLowerCase();

  // Buscar coincidencia exacta (case-insensitive)
  for (const municipality of availableMunicipalities) {
    if (lowerQuery.includes(municipality.toLowerCase())) {
      return municipality;
    }
  }

  return null;
}

/**
 * Extrae el tipo de normativa mencionado en la query
 * @param query - Consulta del usuario
 * @returns Tipo de normativa o null
 */
export function extractOrdinanceType(query: string): string | null {
  const lowerQuery = query.toLowerCase();

  const typePatterns = [
    { pattern: /\bordenanza/i, type: 'ordenanza' },
    { pattern: /\bdecreto/i, type: 'decreto' },
    { pattern: /\bresolución|resolucion/i, type: 'resolucion' },
    { pattern: /\bdisposición|disposicion/i, type: 'disposicion' },
    { pattern: /\bconvenio/i, type: 'convenio' },
    { pattern: /\blicitación|licitacion/i, type: 'licitacion' },
    { pattern: /\bboletín|boletin/i, type: 'boletin' }
  ];

  for (const { pattern, type } of typePatterns) {
    if (pattern.test(lowerQuery)) {
      return type;
    }
  }

  return null;
}

/**
 * Convierte un año a rango de fechas ISO (YYYY-01-01 a YYYY-12-31)
 * @param year - Año como string (YYYY)
 * @returns Objeto con dateFrom y dateTo
 */
export function yearToDateRange(year: string): { dateFrom: string; dateTo: string } {
  return {
    dateFrom: `${year}-01-01`,
    dateTo: `${year}-12-31`
  };
}

/**
 * Extrae filtros automáticamente de la consulta del usuario
 * @param query - Consulta del usuario
 * @param availableMunicipalities - Lista de municipios disponibles
 * @param existingFilters - Filtros ya aplicados (desde UI)
 * @returns SearchOptions con filtros extraídos + existentes
 */
export function extractFiltersFromQuery(
  query: string,
  availableMunicipalities: string[],
  existingFilters: Partial<SearchOptions> = {}
): Partial<SearchOptions> {
  const extractedFilters: Partial<SearchOptions> = {};

  // 1. Extraer municipio (solo si no hay filtro existente)
  if (!existingFilters.municipality) {
    const municipality = extractMunicipality(query, availableMunicipalities);
    if (municipality) {
      extractedFilters.municipality = municipality;
    }
  }

  // 2. Extraer año (solo si no hay filtros de fecha existentes)
  if (!existingFilters.dateFrom && !existingFilters.dateTo) {
    const year = extractYear(query);
    if (year) {
      const dateRange = yearToDateRange(year);
      extractedFilters.dateFrom = dateRange.dateFrom;
      extractedFilters.dateTo = dateRange.dateTo;
    }
  }

  // 3. Extraer tipo de normativa (solo si no hay filtro existente)
  if (!existingFilters.type || existingFilters.type === 'all') {
    const ordinanceType = extractOrdinanceType(query);
    if (ordinanceType) {
      extractedFilters.type = ordinanceType;
    }
  }

  // Combinar filtros: existentes tienen prioridad SOLO si no son null/undefined
  return {
    municipality: existingFilters.municipality || extractedFilters.municipality,
    type: (existingFilters.type && existingFilters.type !== 'all') ? existingFilters.type : extractedFilters.type,
    dateFrom: existingFilters.dateFrom || extractedFilters.dateFrom,
    dateTo: existingFilters.dateTo || extractedFilters.dateTo,
    limit: existingFilters.limit
  };
}
