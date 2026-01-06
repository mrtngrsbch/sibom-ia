/**
 * types.ts
 *
 * Tipos TypeScript centralizados para el proyecto.
 * Evita duplicación y uso de 'any'.
 */

import { DocumentType } from './constants';

/**
 * Filtros de búsqueda aplicables desde UI o query
 */
export interface SearchFilters {
  municipality?: string | null;
  type?: string;
  dateFrom?: string | null;
  dateTo?: string | null;
  limit?: number;
}

/**
 * Filtros del chat (versión UI)
 */
export interface ChatFilters {
  municipality: string | null;
  ordinanceType: 'all' | DocumentType;
  dateFrom: string | null;
  dateTo: string | null;
}

/**
 * Entrada del índice de documentos
 */
export interface IndexEntry {
  id: string;
  municipality: string;
  type: 'ordenanza' | 'decreto' | 'boletin';
  number: string;
  title: string;
  date: string;
  url: string;
  status: string;
  filename: string;
  documentTypes?: DocumentType[];
}

/**
 * Fuente consultada en una búsqueda
 */
export interface Source {
  title: string;
  url: string;
  municipality: string;
  type: string;
  status?: string;
  documentTypes?: DocumentType[];
}

/**
 * Resultado de una búsqueda RAG
 */
export interface SearchResult {
  context: string;
  sources: Source[];
}

/**
 * Documento completo (con contenido)
 */
export interface Document {
  id: string;
  municipality: string;
  type: 'ordenanza' | 'decreto' | 'boletin';
  number: string;
  title: string;
  content: string;
  date: string;
  url: string;
  status: string;
  documentTypes?: DocumentType[];
}

/**
 * Estadísticas de la base de datos
 */
export interface DatabaseStats {
  totalDocuments: number;
  municipalities: number;
  municipalityList: string[];
  lastUpdated?: string | null;
}

/**
 * Análisis de query
 */
export interface QueryAnalysis {
  isBroad: boolean;
  needsClarification: boolean;
  suggestedMunicipality?: string;
  extractedFilters?: SearchFilters;
}

/**
 * Uso de tokens (para estadísticas)
 */
export interface TokenUsage {
  prompt: number;
  completion: number;
  total: number;
}
