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
import { calculateContentLimit } from '@/lib/query-classifier';
import { BM25Index, tokenize } from './bm25';
import { vectorSearch, isVectorSearchAvailable } from './vector-search';
import type { StructuredTable } from '@/lib/types';

const gunzipAsync = promisify(gunzip);

/** Contenido de un archivo JSON de boletín */
export interface BulletinFileContent {
  fullText?: string;
  tables?: StructuredTable[];
  metadata?: {
    municipality?: string;
    bulletinNumber?: string;
    date?: string;
    documentTypes?: string[];
  };
  [key: string]: unknown; // permite props adicionales sin romper tipado
}

/**
 * Tipos de documentos
 */
export type DocumentType = 'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion' | 'balances' | 'presupuestos' | 'concursos' | 'licitaciones';

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
  type: DocumentType;
  number: string;
  title: string;
  date: string;
  url: string;
  status: string;
  filename: string;
  documentTypes?: Array<'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion' | 'balances' | 'presupuestos' | 'concursos' | 'licitaciones'>;
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
  sources: Source[];
  totalCount?: number;  // Total de resultados disponibles (sin aplicar límite de retrieval)
}

/**
 * Fuente de documento legal
 */
export interface Source {
  title: string;
  url: string;
  municipality: string;
  type: string;
  status?: string;
  documentTypes?: Array<'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion' | 'balances' | 'presupuestos' | 'concursos' | 'licitaciones'>;
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

// Sprint 4: USE_NORMATIVAS_INDEX eliminado — siempre activo (216K normativas > 1738 boletines)

/**
 * Parsea una fecha en formato DD/MM/YYYY a objeto Date usando date-fns
 * @param dateStr - Fecha en formato DD/MM/YYYY o "Municipio, DD/MM/YYYY"
 * @returns Date object o null si el formato es inválido
 */
function parseDate(dateStr: string): Date | null {
  if (!dateStr || typeof dateStr !== 'string') return null;
  
  // Si la fecha tiene formato "Municipio, DD/MM/YYYY", extraer solo la fecha
  let cleanDate = dateStr;
  if (dateStr.includes(',')) {
    const parts = dateStr.split(',');
    if (parts.length >= 2) {
      cleanDate = parts[1].trim();
    }
  }
  
  const parsed = parse(cleanDate, 'dd/MM/yyyy', new Date());
  return isValid(parsed) ? parsed : null;
}

// Cache de archivos JSON completos (30 min - ahorro masivo de bandwidth)
interface BulletinContent {
  fullText?: string;
  tables?: import('@/lib/types').StructuredTable[];
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

interface FileCacheEntry {
  content: BulletinContent;
  timestamp: number;
}
const fileCache = new Map<string, FileCacheEntry>();
const FILE_CACHE_DURATION = 30 * 60 * 1000; // 30 minutos

// ============================================================================
// FUNCIONES DE CONFIGURACIÓN
// ============================================================================

/**
 * Filtra documentos válidos excluyendo archivos especiales
 * @param documents - Array de documentos del índice
 * @returns Array filtrado sin archivos de progreso, test, etc.
 */
function filterValidDocuments(documents: IndexEntry[]): IndexEntry[] {
  return documents.filter(d => {
    // Excluir archivos de progreso (.progress_*.json)
    if (d.filename && d.filename.startsWith('.progress_')) return false;
    
    // Excluir archivos de test (Test_*.json)
    if (d.filename && d.filename.startsWith('Test_')) return false;
    
    // Excluir municipios vacíos o inválidos
    if (!d.municipality || d.municipality.trim() === '') return false;
    
    return true;
  });
}

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
 * @returns Ruta al directorio de datos (python-cli/data/indexes)
 */
function getDataBasePath(): string {
  if (process.env.DATA_PATH) {
    return process.env.DATA_PATH;
  }
  // Los índices están en python-cli/data/indexes/
  return path.join(process.cwd(), '..', 'python-cli', 'data', 'indexes');
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

  console.log(`[RAG] 🔄 loadNormativasIndex() - useGitHub: ${useGitHub()}, cache size: ${normativasCache.length}`);

  if (useGitHub()) {
    if (normativasCache.length > 0 && now - normativasCacheTimestamp < CACHE_DURATION) {
      console.log('[RAG] ♻️ Usando índice de normativas cacheado (GitHub)');
      return normativasCache;
    }
  } else {
    const fileChanged = await hasNormativasIndexFileChanged();
    if (normativasCache.length > 0 && !fileChanged && now - normativasCacheTimestamp < CACHE_DURATION) {
      console.log('[RAG] ♻️ Usando índice de normativas cacheado (local)');
      return normativasCache;
    }
    if (fileChanged && normativasCache.length > 0) {
      console.log(`[RAG] 🔄 Detectado cambio en índice de normativas - Recargando...`);
    }
  }

  try {
    console.log(`[RAG] 📥 Cargando índice de normativas desde ${useGitHub() ? 'GitHub' : 'local'}...`);
    
    const data = useGitHub()
      ? await fetchGitHubNormativasIndex()
      : await readLocalNormativasIndex();

    console.log(`[RAG] ✅ Datos cargados: ${data.length} normativas`);

    normativasCache = data;
    normativasCacheTimestamp = now;

    console.log(`[RAG] ✅ Índice de normativas cargado: ${normativasCache.length} normativas (fuente: ${useGitHub() ? 'GitHub' : 'local'})`);
    return normativasCache;
  } catch (error) {
    console.error('[RAG] ❌ Error cargando índice de normativas:', error);
    console.error('[RAG] Error details:', error instanceof Error ? error.message : String(error));
    if (normativasCache.length > 0) {
      console.warn('[RAG] ⚠️ Usando cache de normativas antiguo como fallback');
      return normativasCache;
    }
    console.error('[RAG] ❌ No hay cache disponible, devolviendo array vacío');
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
async function fetchGitHubFile(filename: string): Promise<BulletinFileContent> {
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
async function readLocalFile(filename: string): Promise<BulletinFileContent> {
  // Verificar cache de archivo
  const cached = fileCache.get(filename);
  if (cached && Date.now() - cached.timestamp < FILE_CACHE_DURATION) {
    return cached.content;
  }

  const basePath = getDataBasePath();
  const boletinesPath = path.join(basePath, 'boletines');
  const filePath = path.join(boletinesPath, filename);

  // Intentar leer el archivo normalmente
  try {
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
  } catch (err) {
    // Si no se encontró, buscar en subdirectorios (para documentos de transparencia)
    // Los archivos de transparencia están en: boletines/{Municipio}/{Archivo}.json
    try {
      const dirs = await fs.readdir(boletinesPath, { withFileTypes: true });
      for (const dir of dirs) {
        if (dir.isDirectory()) {
          const subPath = path.join(boletinesPath, dir.name, `${filename}.json`);
          try {
            const stats = await fs.stat(subPath);
            if (stats.isFile()) {
              const content = await fs.readFile(subPath, 'utf-8');
              const data = JSON.parse(content);

              // Guardar en cache
              fileCache.set(filename, {
                content: data,
                timestamp: Date.now()
              });

              return data;
            }
          } catch {
            // Continuar al siguiente directorio
            continue;
          }
        }
      }
    } catch {
      // Ignorar errores en la búsqueda en subdirectorios
    }

    // Si no se encontró en ningún lado, lanzar el error original
    throw new Error(`Archivo no encontrado: ${filename}`);
  }
}

/**
 * Lee contenido de un archivo (automático: GitHub o local)
 */
async function readFileContent(filename: string): Promise<BulletinFileContent> {
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

  console.log('[RAG] 📥 Cargando índice de normativas...');
  
  // 1. Cargar índice de normativas
  const normativas = await loadNormativasIndex();

  console.log(`[RAG] 📊 Índice cargado: ${normativas.length} normativas`);

  if (normativas.length === 0) {
    console.log('[RAG] ⚠️ Índice de normativas vacío');
    return { context: `No se encontró información para: "${query}"`, sources: [] };
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

  // Para listados masivos, limitar el contexto para no explotar los tokens del LLM
  // Si hay más de 100 resultados, solo incluir un resumen en el contexto
  const MAX_CONTEXT_ENTRIES = 100;

  let context: string;
  if (isMetadataOnly) {
    // Modo listado: solo metadatos (eficiente para queries de conteo)
    if (resultNormativas.length > MAX_CONTEXT_ENTRIES) {
      // Listado masivo: solo resumen, no incluir todos los entries
      context = `LISTADO MASIVO: Se encontraron ${resultNormativas.length} normativas.
Las primeras ${MAX_CONTEXT_ENTRIES} se muestran abajo como referencia:
` +
      resultNormativas.slice(0, MAX_CONTEXT_ENTRIES)
        .map(n => `[${n.m}] ${n.t.toUpperCase()} N° ${n.n}/${n.y} - ${n.d}`)
        .join('\n');
    } else {
      context = resultNormativas
        .map(n => `[${n.m}] ${n.t.toUpperCase()} N° ${n.n}/${n.y} - ${n.d} - ${n.ti}`)
        .join('\n');
    }
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
  const contextEntries = isMetadataOnly && resultNormativas.length > MAX_CONTEXT_ENTRIES
    ? MAX_CONTEXT_ENTRIES
    : resultNormativas.length;
  console.log(`[RAG] ✅ Query completada en ${duration}ms - ${resultNormativas.length} normativas recuperadas, ${contextEntries} en contexto`);

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

// retrieveContextFromBoletines ELIMINADA en Sprint 4 — legacy path redundante.
// El índice de normativas (216K entries) reemplaza completamente al índice de boletines (1738 entries).
// Si se necesita fallback, retrieveContextFromNormativas ya lo maneja internamente.

/**
 * Recupera contexto usando Vector Search (OpenAI embeddings + Qdrant)
 * Proporciona búsqueda semántica que entiende sinónimos y contexto
 */
async function retrieveContextWithVectorSearch(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const startTime = Date.now();

  // 1. Realizar búsqueda vectorial
  const vectorResults = await vectorSearch(query, {
    municipality: options.municipality,
    type: options.type,
    year: options.dateFrom ? parseInt(options.dateFrom.split('-')[0]) : undefined,
    limit: options.limit || 10,
  });

  console.log(`[RAG] Vector search encontró ${vectorResults.length} resultados`);

  // 2. Cargar contenido de los documentos encontrados
  const documents = await Promise.all(
    vectorResults.map(async (r) => {
      try {
        const data = await readFileContent(`${r.source_bulletin}.json`);
        return {
          id: r.id,
          municipality: r.municipality,
          type: r.type as DocumentType,
          number: r.number,
          title: r.title,
          content: data.fullText || '',
          date: `${r.municipality}, ${r.year}`,
          url: r.url,
          status: 'vigente',
          filename: `${r.source_bulletin}.json`,
        };
      } catch (err) {
        console.warn(`[RAG] Error cargando ${r.source_bulletin}:`, err);
        return null;
      }
    })
  );

  const validDocuments = documents.filter(d => d !== null) as Document[];

  // 3. Construir contexto
  const contentLimit = calculateContentLimit(query);
  const isMetadataOnly = contentLimit <= 200;

  let context: string;
  if (isMetadataOnly) {
    // Modo listado: solo metadatos
    context = validDocuments
      .map(doc => `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status}`)
      .join('\n\n---\n\n');
  } else {
    // Modo detallado: incluir contenido
    context = validDocuments
      .map((doc) => {
        const contentChunk = doc.content.slice(0, contentLimit);
        return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status}
Contenido: ${contentChunk}...`;
      })
      .join('\n\n---\n\n');
  }

  // 4. Construir fuentes
  const sources = validDocuments.map((doc) => ({
    title: `${doc.type} ${doc.number} - ${doc.municipality}`,
    url: buildBulletinUrl(doc.url),
    municipality: doc.municipality,
    type: doc.type,
    status: doc.status,
  }));

  const duration = Date.now() - startTime;
  console.log(`[RAG] ✅ Vector search completado en ${duration}ms - ${validDocuments.length} docs`);

  return {
    context: context || `No se encontró información específica para: "${query}"`,
    sources,
  };
}

/**
 * Recupera contexto relevante para una consulta.
 *
 * 2 paths:
 *   1. Vector Search (Qdrant + OpenAI embeddings) — semántico
 *   2. BM25 sobre índice de normativas — keyword fallback
 *
 * @version 2.0.0 — Sprint 4: simplificado de 3 a 2 paths
 */
export async function retrieveContext(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  // 1. Vector Search (si Qdrant está configurado)
  if (isVectorSearchAvailable()) {
    try {
      console.log('[RAG] 🔍 Vector Search (semántico)');
      const result = await retrieveContextWithVectorSearch(query, options);
      console.log('[RAG] ✅ Vector Search exitoso');
      return result;
    } catch (error) {
      console.error('[RAG] ⚠️ Vector Search falló, fallback a BM25:', error);
    }
  }

  // 2. BM25 sobre índice de normativas (keyword search)
  try {
    console.log('[RAG] 📝 BM25 (keyword search)');
    const result = await retrieveContextFromNormativas(query, options);
    console.log('[RAG] ✅ BM25 exitoso');
    return result;
  } catch (error) {
    console.error('[RAG] ❌ Error crítico en BM25:', error);
    return { context: `Error recuperando información para: "${query}"`, sources: [] };
  }
}

/**
 * Obtiene estadísticas de la base de datos
 */
export async function getDatabaseStats() {
  try {
    const normativas = await loadNormativasIndex();
    const municipalities = new Set(normativas.map(n => n.m));
    
    // Obtener fecha de última actualización
    let lastUpdated: string | null = null;
    try {
      if (useGitHub()) {
        lastUpdated = normativasCacheTimestamp > 0 ? new Date(normativasCacheTimestamp).toISOString() : null;
      } else {
        const basePath = getDataBasePath();
        const indexPath = path.join(basePath, 'normativas_index_minimal.json');
        const stats = await fs.stat(indexPath);
        lastUpdated = stats.mtime.toISOString();
      }
    } catch (err) {
      console.warn('[RAG] No se pudo obtener fecha de actualización del índice de normativas');
    }
    
    return {
      totalDocuments: normativas.length,
      municipalities: municipalities.size,
      municipalityList: Array.from(municipalities).sort(),
      lastUpdated,
      source: useGitHub() ? 'GitHub' : 'Local',
    };
  } catch (error) {
    console.error('[RAG] Error cargando stats:', error);
    return {
      totalDocuments: 0,
      municipalities: 0,
      municipalityList: [],
      lastUpdated: null,
      source: useGitHub() ? 'GitHub' : 'Local',
    };
  }
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
