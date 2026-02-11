/**
 * types.ts — Tipos internos del API chat
 *
 * Single source of truth para tipos usados exclusivamente en el handler de chat.
 * Los tipos compartidos con el resto de la app viven en @/lib/types.
 */

import type { Source } from '@/lib/rag/retriever';

/** Body parseado del request */
export interface ChatRequestBody {
  messages: ChatMessageInput[];
}

/** Mensaje de entrada (formato AI SDK) */
export interface ChatMessageInput {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

/** Filtros extraídos para la búsqueda */
export interface EnhancedFilters {
  municipality?: string;
  type?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  isManualTypeFilter?: boolean;
}

/** Contexto recuperado por RAG */
export interface RetrievedContext {
  context: string;
  sources: Source[];
  totalCount?: number;
  computationResult?: {
    success: boolean;
    answer: string;
    markdown?: string;
  };
}

/** Estadísticas de la base de datos */
export interface StatsResult {
  totalDocuments: number;
  municipalities: number;
  municipalityList: string[];
  lastUpdated?: string | null;
}

/** Contexto conversacional extraído de mensajes previos */
export interface ConversationContext {
  municipality?: string;
  year?: string;
  type?: string;
}
