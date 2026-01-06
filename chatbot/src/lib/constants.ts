/**
 * constants.ts
 *
 * Constantes centralizadas del proyecto para evitar números mágicos
 * y facilitar configuración futura.
 */

/**
 * Límites de recuperación de documentos según tipo de query
 */
export const RETRIEVAL_LIMITS = {
  /** Queries de listado completo (ej: "lista de ordenanzas", "todas las ordenanzas") */
  LISTING_WITH_FILTERS: 50,

  /** Queries generales con filtros aplicados (municipio, año, tipo) */
  FILTERED_QUERY: 10,

  /** Queries amplias sin filtros */
  UNFILTERED_QUERY: 3,

  /** Límite de caracteres de contenido por documento en el contexto */
  CONTENT_CHARS_PER_DOC: 2000,
} as const;

/**
 * Duraciones de cache
 */
export const CACHE_DURATIONS = {
  /** Cache del índice en memoria (ms) */
  INDEX_MS: 5 * 60 * 1000, // 5 minutos

  /** Cache de archivos individuales (ms) */
  FILE_MS: 15 * 60 * 1000, // 15 minutos

  /** Detección de cambios en archivo local (ms) */
  FILE_CHECK_MS: 1 * 60 * 1000, // 1 minuto
} as const;

/**
 * Tipos de documentos legales soportados
 */
export const DOCUMENT_TYPES = [
  'ordenanza',
  'decreto',
  'boletin',
  'resolucion',
  'disposicion',
  'convenio',
  'licitacion'
] as const;

export type DocumentType = typeof DOCUMENT_TYPES[number];

/**
 * Patrones de queries que requieren listado completo
 */
export const LISTING_QUERY_PATTERNS = [
  /cuántas|cuantas|cantidad|total/i,
  /lista|listar|listado/i,
  /todos.*los|todas.*las/i,
  /qué.*hay|que.*hay/i,
] as const;

/**
 * Patrones de queries amplias que necesitan clarificación
 */
export const BROAD_QUERY_PATTERNS = [
  /^(ordenanzas?|decretos?|resoluciones?|boletines?)$/i,
  /^qué es /i,
  /^cómo /i,
] as const;

/**
 * Stopwords para tokenización en español (BM25)
 */
export const SPANISH_STOPWORDS = new Set([
  'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
  'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo',
  'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese',
  'la', 'si', 'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy',
  'sin', 'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo',
  'yo', 'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así', 'primero',
  'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella',
  'si', 'día', 'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
  'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde', 'ahora', 'parte',
  'después', 'vida', 'quedar', 'siempre', 'creer', 'hablar', 'llevar', 'dejar',
]);

/**
 * Configuración de BM25
 */
export const BM25_CONFIG = {
  /** Factor de saturación de términos (k1) */
  K1: 1.5,

  /** Factor de normalización de longitud (b) */
  B: 0.75,

  /** Peso del título vs contenido */
  TITLE_WEIGHT: 3,
} as const;

/**
 * URLs del proyecto
 */
export const URLS = {
  SIBOM_BASE: 'https://sibom.slyt.gba.gob.ar',
  SIBOM_VIEWER: 'https://sibom.slyt.gba.gob.ar/vistas/verActa.php',
} as const;

/**
 * Configuración de API
 */
export const API_CONFIG = {
  /** Timeout para requests a GitHub (ms) */
  GITHUB_TIMEOUT_MS: 10000, // 10 segundos

  /** Reintentos en caso de error */
  MAX_RETRIES: 3,
} as const;
