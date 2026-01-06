/**
 * date-utils.ts
 *
 * Funciones centralizadas para manejo de fechas en el proyecto.
 * FORMATO ESTÁNDAR: ISO 8601 (YYYY-MM-DD)
 */

/**
 * Parsea fecha en formato DD/MM/YYYY (del índice) a Date
 */
export function parseDDMMYYYY(dateStr: string): Date | null {
  if (!dateStr || typeof dateStr !== 'string') return null;
  const parts = dateStr.split('/');
  if (parts.length !== 3) return null;
  const [day, month, year] = parts.map(p => parseInt(p, 10));
  if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
  return new Date(year, month - 1, day);
}

/**
 * Convierte fecha DD/MM/YYYY a formato ISO (YYYY-MM-DD)
 */
export function ddmmyyyyToISO(dateStr: string): string | null {
  const date = parseDDMMYYYY(dateStr);
  if (!date) return null;
  return date.toISOString().split('T')[0];
}

/**
 * Parsea fecha ISO (YYYY-MM-DD) a Date
 */
export function parseISO(dateStr: string): Date | null {
  if (!dateStr || typeof dateStr !== 'string') return null;
  const date = new Date(dateStr);
  return isNaN(date.getTime()) ? null : date;
}

/**
 * Formatea Date a ISO (YYYY-MM-DD)
 */
export function formatISO(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Extrae año de cualquier formato de fecha
 */
export function extractYear(dateStr: string): number | null {
  // Intentar DD/MM/YYYY
  const ddmmyyyy = parseDDMMYYYY(dateStr);
  if (ddmmyyyy) return ddmmyyyy.getFullYear();

  // Intentar ISO
  const iso = parseISO(dateStr);
  if (iso) return iso.getFullYear();

  // Fallback: buscar 4 dígitos
  const match = dateStr.match(/(\d{4})/);
  if (match) {
    const year = parseInt(match[1], 10);
    if (year >= 2000 && year <= 2030) return year;
  }

  return null;
}

/**
 * Constantes de formato
 */
export const DATE_FORMAT = {
  ISO: 'YYYY-MM-DD',
  DISPLAY: 'DD/MM/YYYY',
} as const;
