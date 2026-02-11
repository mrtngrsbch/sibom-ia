/**
 * rag-handler.ts — Recuperación de contexto RAG
 *
 * Responsabilidad única: dado un query y filtros, recuperar contexto relevante
 * y aplicar re-ranking. NO construye prompts ni decide qué hacer con el resultado.
 *
 * @version 2.1.0 — Sprint 4: eliminada lógica SQLite duplicada
 */

import { retrieveContext, getDatabaseStats } from '@/lib/rag/retriever';
import { rerankSources, filterByRelevance, isSpecificSearch } from '@/lib/rag/reranker';
import type { EnhancedFilters, RetrievedContext, StatsResult } from '../types';

// ============================================================================
// Stats
// ============================================================================

/**
 * Obtiene estadísticas de la base de datos
 */
export async function getStats(): Promise<StatsResult> {
  return await getDatabaseStats();
}

// ============================================================================
// Retrieval + Reranking
// ============================================================================

/**
 * Recupera contexto y aplica re-ranking en un solo paso.
 *
 * Flujo interno (gestionado por retriever.ts):
 *   1. Qdrant disponible? → Vector search (semántico)
 *   2. Fallback → BM25 sobre índice de normativas (keyword)
 */
export async function retrieveAndRerank(
  query: string,
  options: EnhancedFilters
): Promise<RetrievedContext> {
  // 1. Recuperar contexto (retriever.ts decide Vector vs BM25)
  const result = await retrieveContext(query, options);

  // 2. Re-ranking
  if (result.sources.length > 0) {
    const beforeRerank = result.sources.length;
    const queryIsSpecific = isSpecificSearch(query);

    if (queryIsSpecific) {
      const { relevant, irrelevant } = filterByRelevance(result.sources, query, 30);
      result.sources = rerankSources(relevant, query);
      console.log(`[RAGHandler] 🎯 Re-ranking específico: ${beforeRerank} → ${result.sources.length} (${irrelevant.length} filtradas)`);
    } else {
      result.sources = rerankSources(result.sources, query);
      console.log(`[RAGHandler] 🎯 Re-ranking general: ${beforeRerank} fuentes re-rankeadas`);
    }
  }

  console.log(`[RAGHandler] 📊 Fuentes finales: ${result.sources.length}`);
  return result;
}
