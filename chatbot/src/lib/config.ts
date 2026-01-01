/**
 * config.ts
 *
 * Configuración centralizada de la aplicación.
 * Contiene constantes y URLs base que se usan en toda la app.
 *
 * @version 1.0.0
 * @created 2026-01-01
 * @author Kilo Code
 */

/**
 * URL base del Sistema de Boletines Municipales (SIBOM)
 * Este es el dominio oficial donde se publican los boletines.
 */
export const SIBOM_BASE_URL = 'https://sibom.slyt.gba.gob.ar';

/**
 * Construye la URL completa de un boletín a partir de su path relativo
 * @param relativePath - Path relativo como "/bulletins/358" o "bulletins/358"
 * @returns URL completa al boletín en SIBOM
 */
export function buildBulletinUrl(relativePath: string): string {
  if (!relativePath) return SIBOM_BASE_URL;
  
  // Si ya es una URL completa, devolverla tal cual
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
    return relativePath;
  }
  
  // Asegurar que el path comience con /
  const path = relativePath.startsWith('/') ? relativePath : `/${relativePath}`;
  
  return `${SIBOM_BASE_URL}${path}`;
}

/**
 * Configuración de la aplicación
 */
export const APP_CONFIG = {
  /** Nombre de la aplicación */
  appName: 'Asistente Legal Municipal',
  
  /** Descripción breve */
  description: 'Chatbot especializado en legislación municipal de Buenos Aires',
  
  /** Duración del cache del índice en milisegundos */
  indexCacheDuration: 10 * 60 * 1000, // 10 minutos
  
  /** Número máximo de documentos a recuperar por consulta */
  defaultRetrievalLimit: 5,
  
  /** URL base de SIBOM */
  sibomBaseUrl: SIBOM_BASE_URL,
} as const;

export default APP_CONFIG;
