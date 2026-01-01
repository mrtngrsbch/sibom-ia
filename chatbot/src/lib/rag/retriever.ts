/**
 * retriever.ts
 *
 * Motor de recuperación de información (RAG) para el chatbot legal.
 * Implementa búsqueda basada en metadatos y carga de contenido desde archivos JSON.
 * Incluye sistema de cache para el índice de documentos.
 *
 * @version 1.4.0
 * @created 2025-12-31
 * @modified 2026-01-01
 * @author Kilo Code
 *
 * @dependencies
 *   - fs/promises
 *   - path
 *   - @/lib/config
 */

import fs from 'fs/promises';
import path from 'path';
import { buildBulletinUrl } from '@/lib/config';

/**
 * Tipos de documentos
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
}

/**
 * Metadatos del índice
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
}

/**
 * Opciones de búsqueda
 */
export interface SearchOptions {
  municipality?: string;
  type?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
}

/**
 * Resultado de búsqueda
 */
export interface SearchResult {
  context: string;
  sources: Array<{
    title: string;
    url: string;
    municipality: string;
    type: string;
  }>;
}

/**
 * RAG Retriever - Recupera contexto de documentos legales
 * @description Sistema de recuperación de información optimizado con indexación
 */

// Cache en memoria para el índice
let indexCache: IndexEntry[] = [];
let cacheTimestamp: number = 0;
const CACHE_DURATION = 10 * 60 * 1000; // 10 minutos

/**
 * Obtiene la ruta base de datos desde env var o usa default
 */
function getDataBasePath(): string {
  // Permitir configuración via env var para flexibilidad en deploys
  if (process.env.DATA_PATH) {
    return process.env.DATA_PATH;
  }
  // Default: asumir estructura monorepo con python-cli al mismo nivel
  return path.join(process.cwd(), '..', 'python-cli');
}

/**
 * Carga el índice de documentos
 */
async function loadIndex(): Promise<IndexEntry[]> {
  const now = Date.now();
  
  // Usar cache si está vigente
  if (indexCache.length > 0 && now - cacheTimestamp < CACHE_DURATION) {
    return indexCache;
  }

  const basePath = getDataBasePath();
  const indexPath = path.join(basePath, 'boletines_index.json');

  try {
    const content = await fs.readFile(indexPath, 'utf-8');
    const data = JSON.parse(content);
    
    indexCache = data;
    cacheTimestamp = now;
    
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[RAG] Índice cargado: ${indexCache.length} documentos`);
    }
    return indexCache;
  } catch (error) {
    console.error('[RAG] Error cargando índice:', error);
    return [];
  }
}

/**
 * Calcula relevancia simple basada en metadatos
 */
function calculateMetadataRelevance(entry: IndexEntry, query: string): number {
  const queryLower = query.toLowerCase();
  const queryTerms = queryLower.split(/\s+/).filter(t => t.length > 2);
  if (queryTerms.length === 0) return 0;

  const titleLower = entry.title.toLowerCase();
  const municipalityLower = entry.municipality.toLowerCase();
  const numberLower = entry.number.toLowerCase();
  
  let score = 0;

  // 1. Coincidencia exacta de número (ej: "ordenanza 123")
  const numberMatch = queryLower.match(/\d+/);
  if (numberMatch && numberLower.includes(numberMatch[0])) {
    score += 50;
  }

  // 2. Coincidencia de términos
  for (const term of queryTerms) {
    // Coincidencia en municipio (muy importante)
    if (municipalityLower.includes(term)) {
      score += 30;
    }
    // Coincidencia en título
    if (titleLower.includes(term)) {
      score += 15;
    }
    // Coincidencia en tipo (ordenanza, decreto)
    if (entry.type.includes(term)) {
      score += 10;
    }
  }

  // 3. Bonus por coincidencia exacta de frase en el título
  if (titleLower.includes(queryLower)) {
    score += 40;
  }
  
  return score;
}

/**
 * Recupera contexto relevante para una consulta
 */
export async function retrieveContext(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const startTime = Date.now();
  
  // 1. Cargar índice
  const index = await loadIndex();

  if (index.length === 0) {
    return { context: '', sources: [] };
  }

  // 2. Filtrar por municipio y tipo (Filtro duro)
  let filteredIndex = index;
  if (options.municipality) {
    const mSearch = options.municipality.toLowerCase();
    filteredIndex = filteredIndex.filter(
      d => d.municipality.toLowerCase().includes(mSearch)
    );
  }

  if (options.type) {
    filteredIndex = filteredIndex.filter(d => d.type === options.type);
  }

  // 3. Calcular relevancia sobre metadatos
  const scoredEntries = filteredIndex.map(entry => ({
    entry,
    score: calculateMetadataRelevance(entry, query),
  }));

  // 4. Ordenar y tomar los mejores candidatos
  scoredEntries.sort((a, b) => b.score - a.score);
  const limit = options.limit || 5;
  const topEntries = scoredEntries.slice(0, limit);

  // 5. Cargar contenido completo SOLO de los seleccionados
  const basePath = getDataBasePath();
  const boletinesPath = path.join(basePath, 'boletines');
  const documents: Document[] = [];

  await Promise.all(topEntries.map(async ({ entry }) => {
    try {
      const filePath = path.join(boletinesPath, entry.filename);
      const content = await fs.readFile(filePath, 'utf-8');
      const data = JSON.parse(content);
      
      documents.push({
        ...entry,
        content: data.fullText || '',
      });
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') {
        console.warn(`[RAG] Error cargando contenido de ${entry.filename}`);
      }
    }
  }));

  // 6. Construir contexto
  const context = documents
    .map((doc) => {
      return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status || 'vigente'}
Contenido: ${doc.content.slice(0, 2000)}...`;
    })
    .join('\n\n---\n\n');

  // 7. Extraer fuentes (usando URL completa de SIBOM)
  const sources = documents.map((doc) => ({
    title: `${doc.type} ${doc.number} - ${doc.municipality}`,
    url: buildBulletinUrl(doc.url), // Construir URL completa de SIBOM
    municipality: doc.municipality,
    type: doc.type,
    status: doc.status || 'vigente',
  }));

  if (process.env.NODE_ENV !== 'production') {
    const duration = Date.now() - startTime;
    console.log(`[RAG] Query "${query.slice(0, 30)}..." completada en ${duration}ms`);
    console.log(`[RAG] Recuperados ${documents.length} documentos relevantes`);
  }

  return {
    context: context || `No se encontró información específica para: "${query}"`,
    sources,
  };
}

/**
 * Obtiene estadísticas de la base de datos
 */
export async function getDatabaseStats() {
  const index = await loadIndex();
  const municipalities = new Set(index.map(d => d.municipality));
  
  // Obtener fecha de última actualización del archivo de índice
  let lastUpdated: string | null = null;
  try {
    const basePath = getDataBasePath();
    const indexPath = path.join(basePath, 'boletines_index.json');
    const stats = await fs.stat(indexPath);
    lastUpdated = stats.mtime.toISOString();
  } catch (err) {
    console.warn('[RAG] No se pudo obtener fecha de actualización del índice');
  }
  
  return {
    totalDocuments: index.length,
    municipalities: municipalities.size,
    municipalityList: Array.from(municipalities).sort(),
    lastUpdated,
  };
}

/**
 * Fuerza la recarga del cache
 */
export function invalidateCache() {
  indexCache = [];
  cacheTimestamp = 0;
}
