/**
 * query-analyzer.ts
 *
 * Analiza queries del usuario para detectar ambigüedades y extraer filtros automáticamente.
 * NO hardcodea municipios - los recibe como parámetro dinámico desde la API.
 */

export interface ClarificationNeeded {
  type: 'municipality' | 'ordinanceType' | 'tooManyResults';
  message: string;
  suggestions: string[];
}

export interface QueryAnalysisResult {
  needsClarification: boolean;
  clarification?: ClarificationNeeded;
  extractedFilters?: {
    municipality?: string;
    ordinanceType?: 'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion';
  };
}

/**
 * Analiza una query y determina si necesita clarificación
 * @param query - Consulta del usuario
 * @param currentFilters - Filtros actualmente aplicados
 * @param municipalities - Lista dinámica de municipios desde /api/stats (NO hardcodeada)
 */
export function analyzeQuery(
  query: string,
  currentFilters: { municipality?: string | null },
  municipalities: string[] = []
): QueryAnalysisResult {
  const lowerQuery = query.toLowerCase();

  // 0. Si el usuario dice "en todos los municipios" → NO clarificar
  if (/en todos.*municipios|todos los municipios|buscar en todos/i.test(query)) {
    return {
      needsClarification: false,
      extractedFilters: {} // Sin filtro = buscar en todos
    };
  }

  // 1. Intentar extraer municipio mencionado en la query
  const extractedMunicipality = municipalities.find(m =>
    lowerQuery.includes(m.toLowerCase())
  );

  // Si detectamos un municipio en la query pero NO está seleccionado en filtros
  // → PREGUNTAR antes de aplicar (Estrategia B)
  const hasMunicipalityFilter = currentFilters.municipality !== null &&
                                  currentFilters.municipality !== undefined &&
                                  currentFilters.municipality !== '';

  if (extractedMunicipality && !hasMunicipalityFilter) {
    return {
      needsClarification: true,
      clarification: {
        type: 'municipality',
        message: `Detecté que mencionás "${extractedMunicipality}". ¿Querés que filtre por ese municipio?`,
        suggestions: [extractedMunicipality] // Sugerir el municipio detectado
      },
      extractedFilters: { municipality: extractedMunicipality }
    };
  }

  // 2. Detectar si es una pregunta amplia que necesita municipio
  const broadQuestions = [
    /cuál.*última.*ordenanza/i,
    /cuál.*tasa/i,
    /cuánto.*cuesta/i,
    /ordenanza.*\d+/i,  // "ordenanza 123" sin municipio
    /decreto.*\d+/i,    // "decreto 456" sin municipio
    /cuántos?.*(decretos|ordenanzas|boletines|resoluciones)/i, // "cuantos decretos/resoluciones" sin municipio
    /(decretos|ordenanzas|boletines|resoluciones).*en.*\d{4}/i, // "decretos/resoluciones en 2025" sin municipio
    /última.*norma/i,
    /vigente/i,
    /última/i,
    /más reciente/i
  ];

  const isBroadQuestion = broadQuestions.some(pattern => pattern.test(query));

  // 3. Si no hay municipio activo y es pregunta amplia → clarificar
  // IMPORTANTE: Verificar tanto null como undefined porque FilterBar usa null
  const hasMunicipality = currentFilters.municipality !== null && currentFilters.municipality !== undefined && currentFilters.municipality !== '';

  if (isBroadQuestion && !hasMunicipality) {
    return {
      needsClarification: true,
      clarification: {
        type: 'municipality',
        message: '¿De qué municipio querés consultar?',
        suggestions: municipalities.slice(0, 6)  // Top 6 municipios
      }
    };
  }

  // 4. Detectar tipo de norma mencionada
  let ordinanceType: 'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion' | undefined;
  if (lowerQuery.includes('ordenanza')) ordinanceType = 'ordenanza';
  else if (lowerQuery.includes('decreto')) ordinanceType = 'decreto';
  else if (lowerQuery.includes('boletin') || lowerQuery.includes('boletín')) ordinanceType = 'boletin';
  else if (lowerQuery.includes('resolución') || lowerQuery.includes('resolucion')) ordinanceType = 'resolucion';
  else if (lowerQuery.includes('disposición') || lowerQuery.includes('disposicion')) ordinanceType = 'disposicion';
  else if (lowerQuery.includes('convenio')) ordinanceType = 'convenio';
  else if (lowerQuery.includes('licitación') || lowerQuery.includes('licitacion')) ordinanceType = 'licitacion';

  return {
    needsClarification: false,
    extractedFilters: {
      ...(extractedMunicipality && { municipality: extractedMunicipality }),
      ...(ordinanceType && { ordinanceType })
    }
  };
}
