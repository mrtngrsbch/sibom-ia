/**
 * reranker.ts
 *
 * Re-ranking de resultados de búsqueda para mejorar precisión.
 * Basado en técnicas del MIT RAG-end2end paper para mejorar Top-5/Top-20 accuracy.
 *
 * El paper muestra que el re-ranking es crítico para reducir alucinaciones:
 * - "Higher retrieval precision results in higher end-to-end QA accuracy"
 * - Cross-encoder re-ranking mejora significativamente la precisión
 *
 * @version 1.0.0
 * @created 2026-01-28
 */

import type { Source, SearchResult } from './retriever';

/**
 * Resultado de búsqueda con score para re-ranking
 */
export interface ScoredSource extends Source {
  rerankScore: number;
  matchReasons: string[];
}

/**
 * Calcula un score de re-ranking para una fuente basado en la query
 * Usa heurísticas que mimetizan un cross-encoder
 */
function calculateRerankScore(source: Source, query: string): { score: number; reasons: string[] } {
  const queryLower = query.toLowerCase();
  const titleLower = source.title.toLowerCase();
  const reasons: string[] = [];
  let score = 0;

  // 1. Match exacto de número (highest priority)
  const queryNumber = queryLower.match(/\b(\d{2,5})\b/)?.[1];
  if (queryNumber) {
    // El título tiene formato "tipo numero/año - municipio"
    const titleNumber = source.title.match(/\b(\d{2,5})\//)?.[1];

    if (titleNumber === queryNumber) {
      score += 1000; // Match exacto de número
      reasons.push(`exact_number:${queryNumber}`);
    } else if (titleNumber?.includes(queryNumber)) {
      score += 500;
      reasons.push(`partial_number:${queryNumber}`);
    }
  }

  // 2. Match exacto de tipo
  const types = ['ordenanza', 'decreto', 'resolución', 'resolucion', 'disposición', 'disposicion', 'convenio'];
  for (const type of types) {
    if (queryLower.includes(type) && titleLower.includes(type)) {
      score += 100;
      reasons.push(`exact_type:${type}`);
      break;
    }
  }

  // 3. Match exacto de año
  const queryYear = queryLower.match(/\b(20\d{2}|19\d{2})\b/)?.[1];
  if (queryYear) {
    if (source.title.includes(`/${queryYear}`) || source.title.includes(`-${queryYear}`)) {
      score += 50;
      reasons.push(`exact_year:${queryYear}`);
    }
  }

  // 4. Match exacto de municipio
  if (source.municipality) {
    const municipalityLower = source.municipality.toLowerCase();
    if (queryLower.includes(municipalityLower) || municipalityLower.includes(queryLower)) {
      score += 30;
      reasons.push(`municipality:${source.municipality}`);
    }
  }

  // 5. Términos del título
  const queryTerms = queryLower.split(/\s+/).filter(t => t.length > 3);
  for (const term of queryTerms) {
    if (titleLower.includes(term) && !types.includes(term)) {
      score += 10;
      reasons.push(`title_term:${term}`);
    }
  }

  // 6. Búsqueda por frase en el título (para "Ordenanza Impositiva", etc)
  if (queryLower.length > 10 && titleLower.includes(queryLower)) {
    score += 200;
    reasons.push('phrase_match');
  }

  return { score, reasons };
}

/**
 * Re-rankea las fuentes usando scoring heurístico (mimetiza cross-encoder)
 *
 * @param sources - Fuentes recuperadas por el retriever inicial
 * @param query - Query del usuario
 * @returns Fuentes re-rankeadas por relevancia
 */
export function rerankSources(sources: Source[], query: string): Source[] {
  if (sources.length === 0) return sources;

  // Calcular scores para cada fuente
  const scored: ScoredSource[] = sources.map(source => {
    const { score, reasons } = calculateRerankScore(source, query);
    return {
      ...source,
      rerankScore: score,
      matchReasons: reasons,
    };
  });

  // Ordenar por score descendente
  scored.sort((a, b) => b.rerankScore - a.rerankScore);

  // Log para debugging
  console.log('[Reranker] Re-ranking completado:');
  scored.slice(0, 5).forEach((s, i) => {
    console.log(`  [${i}] score=${s.rerankScore} ${s.title} (${s.matchReasons.join(', ')})`);
  });

  // Retornar fuentes re-rankeadas (sin los metadatos de reranking)
  return scored.map(({ rerankScore, matchReasons, ...source }) => source);
}

/**
 * Re-rankea un SearchResult completo
 */
export function rerankSearchResult(result: SearchResult, query: string): SearchResult {
  return {
    ...result,
    sources: rerankSources(result.sources, query),
  };
}

/**
 * Filtra fuentes que no tienen un score mínimo de relevancia
 * Útil para evitar resultados irrelevantes que causan alucinaciones
 */
export function filterByRelevance(
  sources: Source[],
  query: string,
  minScore: number = 20
): { relevant: Source[]; irrelevant: Source[] } {
  if (sources.length === 0) return { relevant: [], irrelevant: [] };

  const scored: ScoredSource[] = sources.map(source => {
    const { score, reasons } = calculateRerankScore(source, query);
    return {
      ...source,
      rerankScore: score,
      matchReasons: reasons,
    };
  });

  const relevant = scored
    .filter(s => s.rerankScore >= minScore)
    .map(({ rerankScore, matchReasons, ...source }) => source);

  const irrelevant = scored
    .filter(s => s.rerankScore < minScore)
    .map(({ rerankScore, matchReasons, ...source }) => source);

  if (irrelevant.length > 0) {
    console.log(`[Reranker] Filtradas ${irrelevant.length} fuentes irrelevantes (score < ${minScore})`);
  }

  return { relevant, irrelevant };
}

/**
 * Detecta si una búsqueda es "específica" (requiere match exacto)
 * vs "general" (puede tolerar resultados aproximados)
 */
export function isSpecificSearch(query: string): boolean {
  const specificPatterns = [
    /\b\d{2,5}\/\d{2,4}\b/,  // "2947/2024"
    /ordenanza\s+\d+/i,       // "ordenanza 2947"
    /decreto\s+\d+/i,          // "decreto 123"
    /n[º°]?\s*\d+/i,          // "n° 123"
    /impositiva/i,             // "ordenanza impositiva"
    /tasa\s+vial/i,           // "tasa vial"
  ];

  return specificPatterns.some(pattern => pattern.test(query));
}
