/**
 * RAG index.ts
 *
 * Punto de entrada unificado para el módulo RAG.
 */

// Exportar desde retriever.ts
export {
  retrieveContext,
  getDatabaseStats,
  invalidateCache,
  type SearchOptions,
  type SearchResult,
  type Document,
  type IndexEntry,
  type DocumentType
} from './retriever';

// Exportar desde bm25.ts
export { BM25Index, tokenize } from './bm25';

// Exportar desde table-formatter.ts
export {
  formatTableForLLM,
  formatTablesForLLM,
  filterRelevantTables
} from './table-formatter';

// computational-retriever.ts eliminado (Sprint 4 — dead code)
