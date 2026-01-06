/**
 * retriever.ts
 *
 * Motor de recuperación de información (RAG) para el chatbot legal.
 * Implementa búsqueda basada en metadatos y carga de contenido desde archivos JSON.
 * Soporta múltiples fuentes: archivos locales o GitHub Raw (para deployment en Vercel).
 * Incluye sistema de cache multi-nivel y soporte para archivos gzip.
 *
 * @version 2.0.0 - Híbrido (Local + GitHub Raw + Gzip)
 * @created 2025-12-31
 * @modified 2026-01-01
 * @author Kilo Code
 *
 * @dependencies
 *   - fs/promises (solo para modo local)
 *   - path
 *   - zlib (para descompresión gzip)
 *   - @/lib/config
 */

import fs from 'fs/promises';
import path from 'path';
import { promisify } from 'util';
import { gunzip } from 'zlib';
import { buildBulletinUrl } from '@/lib/config';
import { calculateContentLimit } from '@/lib/query-classifier';
import { BM25Index, tokenize } from './bm25';

const gunzipAsync = promisify(gunzip);

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
  documentTypes?: Array<'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion'>; // Nuevo: tipos de documentos dentro del boletín
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
    status?: string;
    documentTypes?: Array<'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion'>;
  }>;
}

/**
 * RAG Retriever - Recupera contexto de documentos legales
 * @description Sistema de recuperación híbrido que soporta archivos locales y GitHub Raw
 */

// ============================================================================
// CONFIGURACIÓN DE CACHE MULTI-NIVEL
// ============================================================================

// Cache del índice (configurable via env var)
let indexCache: IndexEntry[] = [];
let cacheTimestamp: number = 0;
let lastFileModTime: number = 0;
// Default: 5 minutos para detectar cambios más rápido
// Con webhook de GitHub, usar 1 hora (3600000)
const CACHE_DURATION = parseInt(process.env.INDEX_CACHE_DURATION || '300000'); // 5 min default

/**
 * Parsea una fecha en formato DD/MM/YYYY a objeto Date
 * @param dateStr - Fecha en formato DD/MM/YYYY
 * @returns Date object o null si el formato es inválido
 */
function parseDate(dateStr: string): Date | null {
  if (!dateStr || typeof dateStr !== 'string') return null;
  const parts = dateStr.split('/');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(p => parseInt(p, 10));
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

// Cache de archivos JSON completos (30 min - ahorro masivo de bandwidth)
interface FileCacheEntry {
  content: any;
  timestamp: number;
}
const fileCache = new Map<string, FileCacheEntry>();
const FILE_CACHE_DURATION = 30 * 60 * 1000; // 30 minutos

// ============================================================================
// FUNCIONES DE CONFIGURACIÓN
// ============================================================================

/**
 * Determina si se debe usar GitHub Raw o archivos locales
 */
function useGitHub(): boolean {
  return !!process.env.GITHUB_DATA_REPO;
}

/**
 * Obtiene la URL base de GitHub Raw
 */
function getGitHubRawBase(): string {
  const repo = process.env.GITHUB_DATA_REPO; // Formato: "usuario/repo"
  const branch = process.env.GITHUB_DATA_BRANCH || 'main';
  return `https://raw.githubusercontent.com/${repo}/${branch}`;
}

/**
 * Obtiene la ruta base de datos locales
 */
function getDataBasePath(): string {
  if (process.env.DATA_PATH) {
    return process.env.DATA_PATH;
  }
  return path.join(process.cwd(), '..', 'python-cli');
}

// ============================================================================
// FUNCIONES DE LECTURA (HÍBRIDAS CON SOPORTE GZIP)
// ============================================================================

/**
 * Descomprime un buffer gzip si es necesario
 */
async function decompressIfNeeded(arrayBuffer: ArrayBuffer, isGzipped: boolean): Promise<string> {
  const uint8Array = new Uint8Array(arrayBuffer);

  if (!isGzipped) {
    const decoder = new TextDecoder('utf-8');
    return decoder.decode(uint8Array);
  }

  try {
    const decompressed = await gunzipAsync(uint8Array);
    const decoder = new TextDecoder('utf-8');
    return decoder.decode(decompressed);
  } catch (error) {
    console.error('[RAG] Error descomprimiendo archivo:', error);
    throw error;
  }
}

/**
 * Lee el índice desde GitHub Raw con retry y soporte gzip
 */
async function fetchGitHubIndex(): Promise<IndexEntry[]> {
  const baseUrl = getGitHubRawBase();
  const useGzip = process.env.GITHUB_USE_GZIP === 'true';
  const url = useGzip
    ? `${baseUrl}/boletines_index.json.gz`
    : `${baseUrl}/boletines_index.json`;

  console.log(`[RAG] 📥 Descargando índice desde GitHub: ${url}`);

  try {
    const response = await fetch(url, {
      cache: 'force-cache', // Cache agresivo del navegador
      next: { revalidate: 3600 } // Cache de Next.js: 1 hora
    });

    if (!response.ok) {
      throw new Error(`GitHub respondió con status ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const content = await decompressIfNeeded(arrayBuffer, useGzip);
    const data = JSON.parse(content);

    console.log(`[RAG] ✅ Índice descargado: ${data.length} documentos (${useGzip ? 'gzip' : 'sin comprimir'})`);
    return data;
  } catch (error) {
    console.error('[RAG] ❌ Error descargando índice de GitHub:', error);
    throw error;
  }
}

/**
 * Lee el índice desde archivos locales
 */
async function readLocalIndex(): Promise<IndexEntry[]> {
  const basePath = getDataBasePath();
  const indexPath = path.join(basePath, 'boletines_index.json');

  try {
    const content = await fs.readFile(indexPath, 'utf-8');
    const data = JSON.parse(content);
    return data;
  } catch (error) {
    console.error('[RAG] ❌ Error leyendo índice local:', error);
    throw error;
  }
}

/**
 * Verifica si el archivo de índice local ha cambiado (solo para modo local)
 */
async function hasIndexFileChanged(): Promise<boolean> {
  if (useGitHub()) return false; // En GitHub no verificamos cambios de archivo

  const basePath = getDataBasePath();
  const indexPath = path.join(basePath, 'boletines_index.json');

  try {
    const stats = await fs.stat(indexPath);
    const fileModTime = stats.mtimeMs;

    if (lastFileModTime === 0 || fileModTime > lastFileModTime) {
      lastFileModTime = fileModTime;
      return true;
    }
    return false;
  } catch (error) {
    console.error('[RAG] Error verificando cambios en índice:', error);
    return false;
  }
}

/**
 * Carga el índice con detección automática de fuente y cache
 */
async function loadIndex(): Promise<IndexEntry[]> {
  const now = Date.now();

  // Verificar cache (1 hora)
  if (useGitHub()) {
    // En GitHub: cache por tiempo
    if (indexCache.length > 0 && now - cacheTimestamp < CACHE_DURATION) {
      console.log('[RAG] ♻️ Usando índice cacheado (GitHub)');
      return indexCache;
    }
  } else {
    // En local: cache por tiempo + detección de cambios
    const fileChanged = await hasIndexFileChanged();
    if (indexCache.length > 0 && !fileChanged && now - cacheTimestamp < CACHE_DURATION) {
      return indexCache;
    }
    if (fileChanged && indexCache.length > 0) {
      console.log(`[RAG] 🔄 Detectado cambio en índice local - Recargando...`);
    }
  }

  try {
    // Cargar desde GitHub o local
    const data = useGitHub()
      ? await fetchGitHubIndex()
      : await readLocalIndex();

    indexCache = data;
    cacheTimestamp = now;

    console.log(`[RAG] ✅ Índice cargado: ${indexCache.length} documentos (fuente: ${useGitHub() ? 'GitHub' : 'local'})`);
    return indexCache;
  } catch (error) {
    console.error('[RAG] ❌ Error cargando índice:', error);
    // Si falla GitHub, intentar con cache viejo si existe
    if (indexCache.length > 0) {
      console.warn('[RAG] ⚠️ Usando cache antiguo como fallback');
      return indexCache;
    }
    return [];
  }
}

/**
 * Lee contenido de un archivo JSON desde GitHub con cache y soporte gzip
 */
async function fetchGitHubFile(filename: string): Promise<any> {
  // Verificar cache de archivo
  const cached = fileCache.get(filename);
  if (cached && Date.now() - cached.timestamp < FILE_CACHE_DURATION) {
    return cached.content;
  }

  const baseUrl = getGitHubRawBase();
  const useGzip = process.env.GITHUB_USE_GZIP === 'true';
  const url = useGzip
    ? `${baseUrl}/boletines/${filename}.gz`
    : `${baseUrl}/boletines/${filename}`;

  try {
    const response = await fetch(url, {
      cache: 'force-cache', // Cache agresivo
      next: { revalidate: 1800 } // Cache de Next.js: 30 min
    });

    if (!response.ok) {
      throw new Error(`GitHub respondió con status ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const content = await decompressIfNeeded(arrayBuffer, useGzip);
    const data = JSON.parse(content);

    // Guardar en cache
    fileCache.set(filename, {
      content: data,
      timestamp: Date.now()
    });

    return data;
  } catch (error) {
    console.error(`[RAG] Error descargando ${filename} de GitHub:`, error);
    throw error;
  }
}

/**
 * Lee contenido de un archivo JSON local con cache
 */
async function readLocalFile(filename: string): Promise<any> {
  // Verificar cache de archivo
  const cached = fileCache.get(filename);
  if (cached && Date.now() - cached.timestamp < FILE_CACHE_DURATION) {
    return cached.content;
  }

  const basePath = getDataBasePath();
  const boletinesPath = path.join(basePath, 'boletines');
  const filePath = path.join(boletinesPath, filename);

  const stats = await fs.stat(filePath);
  if (!stats.isFile()) {
    throw new Error(`${filename} no es un archivo regular`);
  }

  const content = await fs.readFile(filePath, 'utf-8');
  const data = JSON.parse(content);

  // Guardar en cache
  fileCache.set(filename, {
    content: data,
    timestamp: Date.now()
  });

  return data;
}

/**
 * Lee contenido de un archivo (automático: GitHub o local)
 */
async function readFileContent(filename: string): Promise<any> {
  return useGitHub()
    ? await fetchGitHubFile(filename)
    : await readLocalFile(filename);
}

// ============================================================================
// FUNCIONES DE BÚSQUEDA
// ============================================================================

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

  // 1. Match exacto de número → máxima prioridad
  const queryNumber = queryLower.match(/\b(\d{1,5})\b/)?.[1];
  if (queryNumber) {
    // Match exacto completo
    if (entry.number === queryNumber) {
      score += 200;  // Garantiza que sea el primero
    }
    // Match parcial (número contiene el buscado)
    else if (numberLower.includes(queryNumber)) {
      score += 100;
    }
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
    const typeFilter = options.type;
    filteredIndex = filteredIndex.filter(d => {
      // Nuevo: usar documentTypes (array) en lugar de type (string único)
      if (d.documentTypes && Array.isArray(d.documentTypes)) {
        return d.documentTypes.includes(typeFilter as any);
      }
      // Fallback: compatibilidad con índice antiguo
      return d.type === typeFilter;
    });
    console.log(`[RAG] Filtrado por tipo "${typeFilter}": ${filteredIndex.length} docs`);
  }

  // Filtrar por rango de fechas
  if (options.dateFrom || options.dateTo) {
    filteredIndex = filteredIndex.filter(d => {
      if (!d.date) return false;
      const docDate = parseDate(d.date);
      if (!docDate) return false;

      if (options.dateFrom) {
        const fromDate = new Date(options.dateFrom);
        if (docDate < fromDate) return false;
      }

      if (options.dateTo) {
        const toDate = new Date(options.dateTo);
        if (docDate > toDate) return false;
      }

      return true;
    });
    console.log(`[RAG] Filtrado por fecha (${options.dateFrom || '...'} - ${options.dateTo || '...'}): ${filteredIndex.length} docs`);
  }

  console.log(`[RAG] Después de filtros: ${filteredIndex.length} documentos`);

  // 3. Cargar contenido de TODOS los documentos filtrados para indexar con BM25
  // NOTA: Esto puede ser costoso la primera vez, pero se cachea
  const docsWithContent: Array<{ entry: IndexEntry; content: string }> = [];

  await Promise.all(filteredIndex.map(async (entry) => {
    try {
      const data = await readFileContent(entry.filename);
      docsWithContent.push({
        entry,
        content: data.fullText || ''
      });
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') {
        console.warn(`[RAG] Error cargando ${entry.filename}:`, err instanceof Error ? err.message : err);
      }
    }
  }));

  console.log(`[RAG] Documentos cargados para BM25: ${docsWithContent.length}`);

  // 4. Construir índice BM25 sobre el contenido
  const tokenizedDocs = docsWithContent.map(d => {
    // Tokenizar: título + contenido (priorizando título con repetición)
    const titleTokens = tokenize(d.entry.title);
    const contentTokens = tokenize(d.content.slice(0, 2000)); // Solo primeros 2000 chars para performance

    // Repetir tokens del título 3 veces para dar más peso
    return [...titleTokens, ...titleTokens, ...titleTokens, ...contentTokens];
  });

  const bm25 = new BM25Index(
    tokenizedDocs,
    1.5,  // k1: saturación de término (1.2-2.0, mayor = más peso a TF)
    0.75  // b: normalización por longitud (0-1, mayor = más penalización a docs largos)
  );

  console.log(`[RAG] Índice BM25 construido con ${tokenizedDocs.length} docs`);

  // 5. Buscar con BM25 y obtener top-k resultados
  const limit = options.limit || 5;
  console.log(`[RAG] 🎯 LÍMITE SOLICITADO: ${limit} documentos`);
  const bm25Results = bm25.search(query, limit);

  console.log(`[RAG] BM25 top ${limit} resultados:`, bm25Results.map(r => ({
    title: docsWithContent[r.index].entry.title,
    score: r.score.toFixed(2)
  })));
  console.log(`[RAG] ✅ Devolviendo ${bm25Results.length} documentos al LLM`);

  // 6. Construir documentos finales con los resultados rankeados
  const documents: Document[] = bm25Results.map(result => {
    const { entry, content } = docsWithContent[result.index];
    return {
      ...entry,
      content,
    };
  });

  // 7. Construir contexto con truncamiento dinámico
  const contentLimit = calculateContentLimit(query);
  const context = documents
    .map((doc) => {
      const contentChunk = doc.content.slice(0, contentLimit);

      // Si es metadata-only (limit 200), NO incluir contenido
      if (contentLimit <= 200) {
        return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status || 'vigente'}`;
      }

      // Incluir extracto de contenido
      return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status || 'vigente'}
Contenido: ${contentChunk}...`;
    })
    .join('\n\n---\n\n');

  // 7. Extraer fuentes (usando URL completa de SIBOM)
  const sources = documents.map((doc) => ({
    title: `${doc.type} ${doc.number} - ${doc.municipality}`,
    url: buildBulletinUrl(doc.url),
    municipality: doc.municipality,
    type: doc.type,
    status: doc.status || 'vigente',
    documentTypes: doc.documentTypes, // ✅ Incluir tipos de documentos dentro del boletín
  }));

  if (process.env.NODE_ENV !== 'production') {
    const duration = Date.now() - startTime;
    console.log(`[RAG] Query "${query.slice(0, 30)}..." completada en ${duration}ms`);
    console.log(`[RAG] Recuperados ${documents.length} documentos relevantes`);
    console.log(`[RAG] Cache: ${fileCache.size} archivos en memoria`);
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

  // Obtener fecha de última actualización
  let lastUpdated: string | null = null;
  try {
    if (useGitHub()) {
      // En GitHub, usar timestamp del cache
      lastUpdated = cacheTimestamp > 0 ? new Date(cacheTimestamp).toISOString() : null;
    } else {
      // En local, usar mtime del archivo
      const basePath = getDataBasePath();
      const indexPath = path.join(basePath, 'boletines_index.json');
      const stats = await fs.stat(indexPath);
      lastUpdated = stats.mtime.toISOString();
    }
  } catch (err) {
    console.warn('[RAG] No se pudo obtener fecha de actualización del índice');
  }

  return {
    totalDocuments: index.length,
    municipalities: municipalities.size,
    municipalityList: Array.from(municipalities).sort(),
    lastUpdated,
    source: useGitHub() ? 'GitHub' : 'Local',
  };
}

/**
 * Fuerza la recarga del cache en la próxima consulta
 */
export function invalidateCache() {
  indexCache = [];
  cacheTimestamp = 0;
  lastFileModTime = 0;
  fileCache.clear(); // Limpiar también cache de archivos
  console.log('[RAG] 🔄 Cache invalidado completamente - se recargará en la próxima consulta');
}
