/**
 * semantic-router.ts - Layer 3: Semantic Query Router
 *
 * Analiza queries y determina qué tiers de chunks jerárquicos buscar.
 * Optimiza la recuperación de información priorizando chunks más relevantes.
 *
 * @version 1.0.0
 * @created 2026-02-15
 * @author AI Agent
 */

/**
 * Tipos de queries reconocidos
 */
export type QueryType =
  | 'executive_summary'  // "¿Cuál es el saldo inicial?"
  | 'comparison'         // "¿Diferencia entre trimestres?"
  | 'detail'             // "¿Qué cuenta específica...?"
  | 'aggregation'        // "¿Cuánto gastaron en total?"
  | 'general';           // Query general (usar todos los tiers)

/**
 * Requisitos de tiers para una query
 */
export interface TierRequirement {
  /** Tiers a buscar (1 = executive, 2 = subsection, 3 = detail) */
  tiers: number[];
  
  /** Máximo de resultados a retornar */
  maxResults: number;
  
  /** Tipo de query detectado */
  queryType: QueryType;
  
  /** Confianza en la clasificación (0-1) */
  confidence: number;
  
  /** Razón de la clasificación (para debugging) */
  reason: string;
}

/**
 * Patrones de keywords para cada tipo de query
 */
const QUERY_PATTERNS = {
  executive_summary: {
    keywords: [
      // Totales
      'saldo inicial', 'saldo final', 'total ingresos', 'total egresos', 'total recaudado',
      'balance general', 'resumen ejecutivo', 'totales', 'balance completo',
      // Preguntas directas sobre totales
      'cuál es el saldo', 'cuánto es el saldo', 'monto inicial', 'monto final',
      'cuánto ingresó', 'cuánto gastó', 'cuántos ingresos', 'cuántos egresos',
      // Contexto de períodos (sin detalles)
      'trimestre', 'anual', 'período', 'ejercicio',
    ],
    // Exclusiones (palabras que indican que NO es executive summary)
    exclusions: [
      'cuenta específica', 'partida', 'detalle', 'línea por línea',
      'diferencia entre', 'comparar', 'versus', 'vs',
    ],
    tiers: [1],           // Solo TIER-1 (executive)
    maxResults: 1,        // Un solo chunk ejecutivo es suficiente
    confidence: 0.9,      // Alta confianza si matchea
  },
  
  comparison: {
    keywords: [
      // Comparaciones temporales
      'diferencia entre', 'comparar', 'versus', 'vs', 'contra',
      'mayor que', 'menor que', 'más que', 'menos que',
      'variación', 'cambio', 'incremento', 'decremento',
      'tendencia', 'evolución', 'histórico',
      // Agregaciones multi-entidad
      'suma de', 'total de varios', 'todos los', 'entre todos',
    ],
    exclusions: [],
    tiers: [1, 2],        // Executive + Subsections
    maxResults: 10,       // Múltiples chunks para comparar
    confidence: 0.85,
  },
  
  detail: {
    keywords: [
      // Consultas específicas
      'cuenta', 'partida', 'código', 'rubro específico', 'línea',
      'qué cuenta', 'cuál es la cuenta', 'detalle de', 'desglose',
      'cuenta número', 'partida presupuestaria',
      // Nombres de cuentas (patrones comunes)
      'sueldos', 'honorarios', 'viáticos', 'servicios', 'obras',
    ],
    exclusions: [],
    tiers: [2, 3],        // Subsections + Details
    maxResults: 20,       // Muchos detalles posibles
    confidence: 0.8,
  },
  
  aggregation: {
    keywords: [
      // Agregaciones
      'cuánto gastaron en total', 'suma de gastos', 'total de ingresos',
      'cuántos', 'cantidad de', 'suma total', 'agregado',
      'en total', 'total de', 'total en',
      // SQL-like
      'sumar', 'contar', 'promedio', 'máximo', 'mínimo',
    ],
    exclusions: [],
    tiers: [1, 2],        // Executive + Subsections (para cálculos)
    maxResults: 15,
    confidence: 0.85,     // Alta prioridad (más específica que detail)
  },
};

/**
 * Detecta el tipo de query analizando keywords
 */
function detectQueryType(query: string): { type: QueryType; confidence: number; reason: string } {
  const normalizedQuery = query.toLowerCase().trim();
  
  // Verificar cada tipo en orden de prioridad (más específico primero)
  const types: Array<[QueryType, typeof QUERY_PATTERNS[keyof typeof QUERY_PATTERNS]]> = [
    ['executive_summary', QUERY_PATTERNS.executive_summary],
    ['comparison', QUERY_PATTERNS.comparison],
    ['aggregation', QUERY_PATTERNS.aggregation],  // Antes de detail (más específico)
    ['detail', QUERY_PATTERNS.detail],
  ];
  
  for (const [type, pattern] of types) {
    // Verificar exclusiones primero
    if (pattern.exclusions.length > 0) {
      const hasExclusion = pattern.exclusions.some(exclusion => 
        normalizedQuery.includes(exclusion.toLowerCase())
      );
      if (hasExclusion) {
        continue; // Saltar este tipo
      }
    }
    
    // Verificar keywords
    const matchedKeywords: string[] = [];
    for (const keyword of pattern.keywords) {
      if (normalizedQuery.includes(keyword.toLowerCase())) {
        matchedKeywords.push(keyword);
      }
    }
    
    if (matchedKeywords.length > 0) {
      // Confianza proporcional a cantidad de keywords matched
      const baseConfidence = pattern.confidence;
      const keywordBonus = Math.min(matchedKeywords.length * 0.05, 0.15); // Max +15%
      const confidence = Math.min(baseConfidence + keywordBonus, 1.0);
      
      return {
        type,
        confidence,
        reason: `Matched ${matchedKeywords.length} keywords: ${matchedKeywords.slice(0, 3).join(', ')}${matchedKeywords.length > 3 ? '...' : ''}`,
      };
    }
  }
  
  // Fallback: query general
  return {
    type: 'general',
    confidence: 0.5,
    reason: 'No specific pattern matched, using general search',
  };
}

/**
 * Detecta si la query es sobre documentos Balance
 */
function isBalanceQuery(query: string): boolean {
  const normalizedQuery = query.toLowerCase();
  
  const balanceKeywords = [
    'balance', 'tesorería', 'tesorer',
    'saldo', 'ingresos', 'egresos',
    'caja', 'disponibilidades',
    'trimestre', 'balance de',
    // Keywords financieros indirectos
    'cuenta', 'partida', 'código', 'codigo', 'rubro',
    'sueldos', 'salarios', 'personal municipal',
    'gastaron', 'servicios', 'bienes', 'obras',
    'transferencias', 'amortización', 'amortizacion',
    'déficit', 'deficit', 'superávit', 'superavit',
    'ejecución presupuestaria', 'ejecucion presupuestaria'
  ];
  
  return balanceKeywords.some(keyword => normalizedQuery.includes(keyword));
}

/**
 * Router principal: analiza query y determina requisitos de tiers
 */
export function routeQuery(query: string, documentType?: string): TierRequirement {
  console.log('[SemanticRouter] 🎯 Analizando query:', query);
  
  // 1. Detectar si es query sobre Balance
  const isBalance = documentType === 'balances' || isBalanceQuery(query);
  
  if (!isBalance) {
    // Para documentos no-Balance, no hay tiers jerárquicos
    // Retornar configuración general
    console.log('[SemanticRouter] ℹ️ Query no es sobre Balance, usando búsqueda estándar');
    return {
      tiers: [1, 2, 3], // Todos los tiers (aunque no existan)
      maxResults: 10,
      queryType: 'general',
      confidence: 1.0,
      reason: 'Non-balance document, using standard search',
    };
  }
  
  // 2. Detectar tipo de query Balance
  const { type, confidence, reason } = detectQueryType(query);
  const pattern = QUERY_PATTERNS[type as keyof typeof QUERY_PATTERNS];
  
  // 3. Construir requisitos
  const requirement: TierRequirement = {
    tiers: pattern?.tiers || [1, 2, 3],
    maxResults: pattern?.maxResults || 10,
    queryType: type,
    confidence,
    reason,
  };
  
  console.log('[SemanticRouter] ✅ Routing decision:', {
    queryType: type,
    tiers: requirement.tiers,
    maxResults: requirement.maxResults,
    confidence: confidence.toFixed(2),
    reason,
  });
  
  return requirement;
}

/**
 * Filtra chunks por tier según requisitos del router
 */
export function filterChunksByTier(
  chunks: Array<{ tier?: number; [key: string]: any }>,
  requirement: TierRequirement
): Array<{ tier?: number; [key: string]: any }> {
  const { tiers, maxResults } = requirement;
  
  // Filtrar por tier
  const filtered = chunks.filter(chunk => {
    // Si el chunk no tiene tier, asumimos que es TIER-3 (legacy)
    const chunkTier = chunk.tier || 3;
    return tiers.includes(chunkTier);
  });
  
  // Ordenar por tier (TIER-1 primero) y limitar resultados
  const sorted = filtered.sort((a, b) => {
    const tierA = a.tier || 3;
    const tierB = b.tier || 3;
    return tierA - tierB; // Ascendente: TIER-1, TIER-2, TIER-3
  });
  
  return sorted.slice(0, maxResults);
}

/**
 * Utilidad: determina si una query necesita TIER-1 (executive summary) prioritariamente
 */
export function needsExecutiveSummary(query: string): boolean {
  const requirement = routeQuery(query);
  return requirement.queryType === 'executive_summary' && requirement.tiers.includes(1);
}

/**
 * Utilidad: obtiene la explicación human-readable del routing
 */
export function explainRouting(requirement: TierRequirement): string {
  const tierNames = requirement.tiers.map(t => {
    switch (t) {
      case 1: return 'TIER-1 (Executive Summary)';
      case 2: return 'TIER-2 (Subsections)';
      case 3: return 'TIER-3 (Details)';
      default: return `TIER-${t}`;
    }
  });
  
  return `Query Type: ${requirement.queryType} (confidence: ${(requirement.confidence * 100).toFixed(0)}%)\n` +
         `Search Strategy: ${tierNames.join(' + ')}\n` +
         `Max Results: ${requirement.maxResults}\n` +
         `Reason: ${requirement.reason}`;
}
