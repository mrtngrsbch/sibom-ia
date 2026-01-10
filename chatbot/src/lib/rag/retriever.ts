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
import { parse, isAfter, isBefore, isValid, startOfDay, endOfDay } from 'date-fns';
import { buildBulletinUrl } from '@/lib/config';
import { calculateContentLimit, isComputationalQuery } from '@/lib/query-classifier';
import { BM25Index, tokenize } from './bm25';
import { formatTablesForLLM, filterRelevantTables } from './table-formatter';
import type { StructuredTable } from '@/lib/types';

const gunzipAsync = promisify(gunzip);

/**
 * Tipos de documentos
 */
export type DocumentType = 'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion';

export interface Document {
  id: string;
  municipality: string;
  type: DocumentType;
  number: string;
  title: string;
  content: string;
  date: string;
  url: string;
  status: string;
  filename?: string; // Nombre del archivo JSON (opcional, para datos tabulares)
  documentTypes?: DocumentType[]; // Tipos de documentos en el boletín (opcional)
}

/**
 * Metadatos del índice (formato antiguo - boletines)
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
  documentTypes?: Array<'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion'>;
}

/**
 * Entrada del índice de normativas (formato nuevo - individual)
 * Campos abreviados para optimizar tamaño
 */
export interface NormativaIndexEntry {
  id: string;         // ID único
  m: string;          // municipality
  t: DocumentType;    // type
  n: string;          // number
  y: string;          // year
  d: string;          // date (DD/MM/YYYY)
  ti: string;         // title (truncado a 100 chars)
  sb: string;         // source_bulletin (filename del boletín)
  url: string;        // URL del boletín en SIBOM
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
  // Indica si el filtro de tipo viene de la selección manual del usuario (true)
  // o de la detección automática desde la query (false)
  isManualTypeFilter?: boolean;
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

// Cache del índice de boletines (legacy)
let indexCache: IndexEntry[] = [];
let cacheTimestamp: number = 0;
let lastFileModTime: number = 0;

// Cache del índice de normativas (nuevo)
let normativasCache: NormativaIndexEntry[] = [];
let normativasCacheTimestamp: number = 0;
let normativasLastFileModTime: number = 0;

// Default: 5 minutos para detectar cambios más rápido
// Con webhook de GitHub, usar 1 hora (3600000)
const CACHE_DURATION = parseInt(process.env.INDEX_CACHE_DURATION || '300000'); // 5 min default

// Flag para usar nuevo índice de normativas (activar cuando esté listo)
const USE_NORMATIVAS_INDEX = process.env.USE_NORMATIVAS_INDEX !== 'false'; // true por defecto

/**
 * Parsea una fecha en formato DD/MM/YYYY a objeto Date usando date-fns
 * @param dateStr - Fecha en formato DD/MM/YYYY
 * @returns Date object o null si el formato es inválido
 */
function parseDate(dateStr: string): Date | null {
  if (!dateStr || typeof dateStr !== 'string') return null;
  const parsed = parse(dateStr, 'dd/MM/yyyy', new Date());
  return isValid(parsed) ? parsed : null;
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
 * Determina si se debe usar fuente remota (GitHub/R2/S3) o archivos locales
 */
function useGitHub(): boolean {
  return !!process.env.GITHUB_DATA_REPO;
}

/**
 * Obtiene la URL base de datos remotos
 * Soporta:
 * - GitHub Raw: GITHUB_DATA_REPO="usuario/repo"
 * - Cloudflare R2: GITHUB_DATA_REPO="pub-xxxxx.r2.dev/bucket"
 * - S3/Custom: GITHUB_DATA_REPO="custom-domain.com/path"
 */
function getGitHubRawBase(): string {
  const repo = process.env.GITHUB_DATA_REPO || '';
  const branch = process.env.GITHUB_DATA_BRANCH || 'main';

  // Si es URL directa (R2, S3, custom domain)
  if (repo.includes('.') && !repo.includes('github')) {
    // R2 y otros servicios: usar URL directa
    return `https://${repo}`;
  }

  // GitHub Raw: construir URL estándar
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

// ============================================================================
// FUNCIONES DE LECTURA - ÍNDICE DE NORMATIVAS (NUEVO)
// ============================================================================

/**
 * Lee el índice de normativas desde GitHub Raw
 */
async function fetchGitHubNormativasIndex(): Promise<NormativaIndexEntry[]> {
  const baseUrl = getGitHubRawBase();
  const useGzip = process.env.GITHUB_USE_GZIP === 'true';
  const url = useGzip
    ? `${baseUrl}/normativas_index_minimal.json.gz`
    : `${baseUrl}/normativas_index_minimal.json`;

  console.log(`[RAG] 📥 Descargando índice de normativas desde GitHub: ${url}`);

  try {
    const response = await fetch(url, {
      cache: 'force-cache',
      next: { revalidate: 3600 }
    });

    if (!response.ok) {
      throw new Error(`GitHub respondió con status ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const content = await decompressIfNeeded(arrayBuffer, useGzip);
    const data = JSON.parse(content);

    console.log(`[RAG] ✅ Índice de normativas descargado: ${data.length} normativas`);
    return data;
  } catch (error) {
    console.error('[RAG] ❌ Error descargando índice de normativas de GitHub:', error);
    throw error;
  }
}

/**
 * Lee el índice de normativas desde archivos locales
 */
async function readLocalNormativasIndex(): Promise<NormativaIndexEntry[]> {
  const basePath = getDataBasePath();
  const indexPath = path.join(basePath, 'normativas_index_minimal.json');

  try {
    const content = await fs.readFile(indexPath, 'utf-8');
    const data = JSON.parse(content);
    return data;
  } catch (error) {
    console.error('[RAG] ❌ Error leyendo índice de normativas local:', error);
    throw error;
  }
}

/**
 * Verifica si el archivo de índice de normativas ha cambiado
 */
async function hasNormativasIndexFileChanged(): Promise<boolean> {
  if (useGitHub()) return false;

  const basePath = getDataBasePath();
  const indexPath = path.join(basePath, 'normativas_index_minimal.json');

  try {
    const stats = await fs.stat(indexPath);
    const fileModTime = stats.mtimeMs;

    if (normativasLastFileModTime === 0 || fileModTime > normativasLastFileModTime) {
      normativasLastFileModTime = fileModTime;
      return true;
    }
    return false;
  } catch (error) {
    console.error('[RAG] Error verificando cambios en índice de normativas:', error);
    return false;
  }
}

/**
 * Carga el índice de normativas con cache
 */
async function loadNormativasIndex(): Promise<NormativaIndexEntry[]> {
  const now = Date.now();

  if (useGitHub()) {
    if (normativasCache.length > 0 && now - normativasCacheTimestamp < CACHE_DURATION) {
      console.log('[RAG] ♻️ Usando índice de normativas cacheado (GitHub)');
      return normativasCache;
    }
  } else {
    const fileChanged = await hasNormativasIndexFileChanged();
    if (normativasCache.length > 0 && !fileChanged && now - normativasCacheTimestamp < CACHE_DURATION) {
      return normativasCache;
    }
    if (fileChanged && normativasCache.length > 0) {
      console.log(`[RAG] 🔄 Detectado cambio en índice de normativas - Recargando...`);
    }
  }

  try {
    const data = useGitHub()
      ? await fetchGitHubNormativasIndex()
      : await readLocalNormativasIndex();

    normativasCache = data;
    normativasCacheTimestamp = now;

    console.log(`[RAG] ✅ Índice de normativas cargado: ${normativasCache.length} normativas (fuente: ${useGitHub() ? 'GitHub' : 'local'})`);
    return normativasCache;
  } catch (error) {
    console.error('[RAG] ❌ Error cargando índice de normativas:', error);
    if (normativasCache.length > 0) {
      console.warn('[RAG] ⚠️ Usando cache de normativas antiguo como fallback');
      return normativasCache;
    }
    return [];
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
 * Recupera contexto usando el NUEVO índice de normativas (más eficiente)
 *
 * Ventajas:
 * - 216K normativas indexadas individualmente vs 1738 boletines
 * - Búsqueda directa por tipo (decreto, ordenanza, etc.)
 * - No necesita cargar archivos para BM25 (usa metadatos)
 * - Contenido se carga bajo demanda solo para resultados top-k
 */
async function retrieveContextFromNormativas(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const startTime = Date.now();

  // 1. Cargar índice de normativas
  const normativas = await loadNormativasIndex();

  if (normativas.length === 0) {
    console.log('[RAG] ⚠️ Índice de normativas vacío, intentando fallback a boletines');
    return retrieveContextFromBoletines(query, options);
  }

  console.log(`[RAG] 🔍 INICIO - Índice de normativas: ${normativas.length} registros`);

  // 2. Filtrar por municipio, tipo y fecha
  let filtered = normativas;

  // Filtrar por municipio
  if (options.municipality) {
    const mSearch = options.municipality.toLowerCase();
    filtered = filtered.filter(n => n.m.toLowerCase().includes(mSearch));
    console.log(`[RAG] 🏘️ Filtro municipio "${options.municipality}": ${filtered.length} normativas`);
  }

  // Filtrar por tipo (ahora funciona directamente porque cada normativa tiene su tipo)
  if (options.type && options.type !== 'all') {
    const typeFilter = options.type.toLowerCase();
    filtered = filtered.filter(n => n.t === typeFilter);
    console.log(`[RAG] 📋 Filtro tipo "${typeFilter}": ${filtered.length} normativas`);
  }

  // Filtrar por rango de fechas
  if (options.dateFrom || options.dateTo) {
    const beforeSize = filtered.length;
    filtered = filtered.filter(n => {
      if (!n.d) return false;
      const docDate = parseDate(n.d);
      if (!docDate) return false;

      if (options.dateFrom) {
        const fromDate = parse(options.dateFrom, 'yyyy-MM-dd', new Date());
        if (isBefore(docDate, startOfDay(fromDate))) return false;
      }

      if (options.dateTo) {
        const toDate = parse(options.dateTo, 'yyyy-MM-dd', new Date());
        if (isAfter(docDate, endOfDay(toDate))) return false;
      }

      return true;
    });
    console.log(`[RAG] 📅 Filtro fecha: ${beforeSize} → ${filtered.length} normativas`);
  }

  console.log(`[RAG] ✅ Después de filtros: ${filtered.length} normativas`);

  // 3. Construir índice BM25 sobre metadatos (título + tipo + número + año)
  // NO necesitamos cargar archivos - usamos los datos del índice
  const tokenizedDocs = filtered.map(n => {
    const titleTokens = tokenize(n.ti);
    const typeTokens = tokenize(n.t);
    const numberTokens = tokenize(n.n);
    const yearTokens = n.y ? tokenize(n.y) : [];
    const municipalityTokens = tokenize(n.m);

    // Peso: título (3x) + municipio (2x) + tipo + número + año
    return [
      ...titleTokens, ...titleTokens, ...titleTokens,
      ...municipalityTokens, ...municipalityTokens,
      ...typeTokens,
      ...numberTokens,
      ...yearTokens
    ];
  });

  const bm25 = new BM25Index(tokenizedDocs, 1.5, 0.75);
  console.log(`[RAG] Índice BM25 construido con ${tokenizedDocs.length} normativas`);

  // 4. Buscar con BM25
  const limit = options.limit || 10; // Aumentado porque las normativas son más pequeñas
  const bm25Results = bm25.search(query, limit);

  console.log(`[RAG] BM25 top ${limit} resultados:`, bm25Results.map(r => ({
    id: filtered[r.index].id,
    type: filtered[r.index].t,
    number: filtered[r.index].n,
    score: r.score.toFixed(2)
  })));

  // 5. Cargar contenido de los resultados top-k (bajo demanda)
  // Agrupamos por boletín para optimizar la carga
  const resultNormativas = bm25Results.map(r => filtered[r.index]);

  // Agrupar por source_bulletin para cargar cada archivo una sola vez
  const bulletinGroups = new Map<string, NormativaIndexEntry[]>();
  for (const n of resultNormativas) {
    const group = bulletinGroups.get(n.sb) || [];
    group.push(n);
    bulletinGroups.set(n.sb, group);
  }

  // Cargar contenido de cada boletín necesario
  const bulletinContents = new Map<string, string>();
  for (const [bulletinName] of bulletinGroups) {
    try {
      const data = await readFileContent(`${bulletinName}.json`);
      bulletinContents.set(bulletinName, data.fullText || '');
    } catch (err) {
      console.warn(`[RAG] Error cargando ${bulletinName}:`, err);
      bulletinContents.set(bulletinName, '');
    }
  }

  // 6. Construir contexto
  const contentLimit = calculateContentLimit(query);
  const isMetadataOnly = contentLimit <= 200;

  let context: string;
  if (isMetadataOnly) {
    // Modo listado: solo metadatos (eficiente para queries de conteo)
    context = resultNormativas
      .map(n => `[${n.m}] ${n.t.toUpperCase()} N° ${n.n}/${n.y} - ${n.d} - ${n.ti}`)
      .join('\n');
  } else {
    // Modo detallado: incluir extracto de contenido
    context = resultNormativas
      .map(n => {
        const fullContent = bulletinContents.get(n.sb) || '';
        // Buscar el documento específico dentro del boletín
        const docMarker = `[DOC `;
        const contentChunk = extractNormativaContent(fullContent, n.n, n.t, contentLimit);

        return `[${n.m}] ${n.t.toUpperCase()} N° ${n.n}/${n.y}
Título: ${n.ti}
Fecha: ${n.d}
Estado: vigente
Fuente: ${n.sb}
Contenido: ${contentChunk}...`;
      })
      .join('\n\n---\n\n');
  }

  // 7. Construir fuentes
  const sources = resultNormativas.map(n => ({
    title: `${n.t} ${n.n}/${n.y} - ${n.m}`,
    url: buildBulletinUrl(n.url),
    municipality: n.m,
    type: n.t,
    status: 'vigente',
  }));

  const duration = Date.now() - startTime;
  console.log(`[RAG] ✅ Query completada en ${duration}ms - ${resultNormativas.length} normativas`);

  return {
    context: context || `No se encontró información específica para: "${query}"`,
    sources,
  };
}

/**
 * Extrae el contenido específico de una normativa dentro del texto del boletín
 */
function extractNormativaContent(
  fullText: string,
  numero: string,
  tipo: string,
  maxLength: number
): string {
  // Buscar patrón de la normativa (ej: "Decreto N° 293" o "Ordenanza N° 2929")
  const patterns = [
    new RegExp(`${tipo}\\s*N[º°]?\\s*${numero}[^\\d]`, 'i'),
    new RegExp(`\\[DOC \\d+\\][\\s\\S]*?${tipo}\\s*N[º°]?\\s*${numero}`, 'i'),
  ];

  for (const pattern of patterns) {
    const match = fullText.match(pattern);
    if (match && match.index !== undefined) {
      // Extraer desde la posición encontrada
      const start = Math.max(0, match.index - 100); // Un poco de contexto previo
      const chunk = fullText.slice(start, start + maxLength);
      return chunk;
    }
  }

  // Fallback: devolver el inicio del documento
  return fullText.slice(0, maxLength);
}

/**
 * Versión legacy: recupera contexto usando el índice de boletines
 * (mantener para compatibilidad y fallback)
 */
async function retrieveContextFromBoletines(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const startTime = Date.now();

  // 1. Cargar índice
  const index = await loadIndex();

  if (index.length === 0) {
    return { context: '', sources: [] };
  }

  // 1.5. Detectar si es query computacional
  const isComputational = isComputationalQuery(query);
  if (isComputational) {
    console.log('[RAG] 🧮 Query computacional detectada - incluyendo datos tabulares');
  }

  // 2. Filtrar por municipio y tipo (Filtro duro)
  let filteredIndex = index;
  console.log(`[RAG] 🔍 INICIO (legacy) - Índice total: ${index.length} documentos`);

  if (options.municipality) {
    const mSearch = options.municipality.toLowerCase();
    filteredIndex = filteredIndex.filter(
      d => d.municipality.toLowerCase().includes(mSearch)
    );
    console.log(`[RAG] 🏘️ Filtro municipio "${options.municipality}": ${filteredIndex.length} docs restantes`);
  }

  // Filtrado por tipo: SOLO si es filtro manual del usuario (dropdown UI)
  if (options.type && options.type !== 'all' && options.isManualTypeFilter === true) {
    const typeFilter = options.type;
    filteredIndex = filteredIndex.filter(d => {
      if (d.documentTypes && Array.isArray(d.documentTypes)) {
        return d.documentTypes.includes(typeFilter as any);
      }
      return d.type === typeFilter;
    });
    console.log(`[RAG] 📋 Filtro tipo MANUAL "${typeFilter}": ${filteredIndex.length} docs restantes`);
  } else if (options.type && options.type !== 'all' && options.isManualTypeFilter !== true) {
    console.log(`[RAG] 📋 Tipo "${options.type}" detectado en query - buscando en contenido de boletines`);
  }

  // Filtrar por rango de fechas
  if (options.dateFrom || options.dateTo) {
    const beforeSize = filteredIndex.length;
    filteredIndex = filteredIndex.filter(d => {
      if (!d.date) return false;
      const docDate = parseDate(d.date);
      if (!docDate) return false;

      if (options.dateFrom) {
        const fromDate = parse(options.dateFrom, 'yyyy-MM-dd', new Date());
        if (isBefore(docDate, startOfDay(fromDate))) return false;
      }

      if (options.dateTo) {
        const toDate = parse(options.dateTo, 'yyyy-MM-dd', new Date());
        if (isAfter(docDate, endOfDay(toDate))) return false;
      }

      return true;
    });
    console.log(`[RAG] 📅 Filtro fecha: ${beforeSize} → ${filteredIndex.length} docs`);
  }

  console.log(`[RAG] ✅ FINAL - Después de todos los filtros: ${filteredIndex.length} documentos`);

  // 3. Cargar contenido de TODOS los documentos filtrados para indexar con BM25
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
    const titleTokens = tokenize(d.entry.title);
    const contentTokens = tokenize(d.content.slice(0, 50000));
    return [...titleTokens, ...titleTokens, ...titleTokens, ...contentTokens];
  });

  const bm25 = new BM25Index(tokenizedDocs, 1.5, 0.75);
  console.log(`[RAG] Índice BM25 construido con ${tokenizedDocs.length} docs`);

  // 5. Buscar con BM25
  const limit = options.limit || 5;
  const bm25Results = bm25.search(query, limit);

  console.log(`[RAG] BM25 top ${limit} resultados:`, bm25Results.map(r => ({
    title: docsWithContent[r.index].entry.title,
    score: r.score.toFixed(2)
  })));

  // 6. Construir documentos finales
  const documents: Document[] = bm25Results.map(result => {
    const { entry, content } = docsWithContent[result.index];
    return { ...entry, content };
  });

  // 6.5. Si es query computacional, cargar datos tabulares
  let allTables: StructuredTable[] = [];
  if (isComputational) {
    for (const doc of documents) {
      try {
        if (!doc.filename) continue;
        const data = await readFileContent(doc.filename);
        if (data.tables && Array.isArray(data.tables) && data.tables.length > 0) {
          allTables.push(...data.tables);
        }
      } catch (error) {
        console.warn(`[RAG] ⚠️ Error cargando tablas de ${doc.filename}:`, error);
      }
    }
    if (allTables.length > 0) {
      const relevantTables = filterRelevantTables(allTables, query);
      allTables = relevantTables;
    }
  }

  // 7. Construir contexto
  const contentLimit = calculateContentLimit(query);
  let context = documents
    .map((doc) => {
      const contentChunk = doc.content.slice(0, contentLimit);
      if (contentLimit <= 200) {
        return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status || 'vigente'}`;
      }
      return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status || 'vigente'}
Contenido: ${contentChunk}...`;
    })
    .join('\n\n---\n\n');

  if (isComputational && allTables.length > 0) {
    const tablesContext = formatTablesForLLM(allTables);
    context = `${context}\n\n---\n\n${tablesContext}`;
  }

  // 8. Extraer fuentes
  const sources = documents.map((doc) => ({
    title: `${doc.type} ${doc.number} - ${doc.municipality}`,
    url: buildBulletinUrl(doc.url),
    municipality: doc.municipality,
    type: doc.type,
    status: doc.status || 'vigente',
    documentTypes: doc.documentTypes,
  }));

  const duration = Date.now() - startTime;
  console.log(`[RAG] Query "${query.slice(0, 30)}..." completada en ${duration}ms`);

  return {
    context: context || `No se encontró información específica para: "${query}"`,
    sources,
  };
}

/**
 * Recupera contexto relevante para una consulta
 * Elige automáticamente entre índice de normativas (nuevo) o boletines (legacy)
 */
export async function retrieveContext(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  // Usar índice de normativas si está habilitado y disponible
  if (USE_NORMATIVAS_INDEX) {
    try {
      return await retrieveContextFromNormativas(query, options);
    } catch (error) {
      console.error('[RAG] ❌ Error con índice de normativas, usando fallback:', error);
      return await retrieveContextFromBoletines(query, options);
    }
  }

  // Fallback: usar índice de boletines (legacy)
  return await retrieveContextFromBoletines(query, options);
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
  // Cache de boletines (legacy)
  indexCache = [];
  cacheTimestamp = 0;
  lastFileModTime = 0;

  // Cache de normativas (nuevo)
  normativasCache = [];
  normativasCacheTimestamp = 0;
  normativasLastFileModTime = 0;

  // Cache de archivos
  fileCache.clear();

  console.log('[RAG] 🔄 Cache invalidado completamente - se recargará en la próxima consulta');
}
