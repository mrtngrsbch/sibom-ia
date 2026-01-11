/**
 * sql-retriever.ts
 *
 * SQLite-based retriever for computational queries and aggregations.
 * Uses sql.js to run queries directly in the browser/server without LLM.
 *
 * @version 1.0.0
 * @created 2026-01-10
 * @author Kiro AI (MIT Engineering Standards)
 *
 * ARCHITECTURE:
 * - Loads SQLite database in memory
 * - Executes SQL queries for aggregations
 * - Returns structured results for direct response generation
 * - Zero LLM calls for computational queries
 */

import initSqlJs, { Database } from 'sql.js';
import path from 'path';
import fs from 'fs/promises';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface SQLQueryResult {
  success: boolean;
  data?: any[];
  error?: string;
  query?: string;
  executionTime?: number;
}

export interface AggregationResult {
  municipality: string;
  total: number;
  decretos?: number;
  ordenanzas?: number;
  resoluciones?: number;
  year_min?: number;
  year_max?: number;
}

export interface ComparisonResult {
  success: boolean;
  answer: string;
  data: AggregationResult[];
  markdown?: string;
}

// ============================================================================
// DATABASE INITIALIZATION
// ============================================================================

let dbInstance: Database | null = null;
let dbLoadTime: number = 0;

/**
 * Loads SQLite database into memory
 * @returns Database instance
 */
async function loadDatabase(): Promise<Database> {
  // Return cached instance if available (< 5 minutes old)
  if (dbInstance && Date.now() - dbLoadTime < 5 * 60 * 1000) {
    return dbInstance;
  }

  console.log('[SQL] Loading database...');
  const startTime = Date.now();

  try {
    // Initialize sql.js
    const SQL = await initSqlJs({
      locateFile: (file) => `https://sql.js.org/dist/${file}`
    });

    // Determine database path
    const isProduction = process.env.NODE_ENV === 'production';
    const dbPath = isProduction
      ? path.join(process.cwd(), 'public', 'data', 'normativas.db')
      : path.join(process.cwd(), '..', 'python-cli', 'boletines', 'normativas.db');

    // Read database file
    const buffer = await fs.readFile(dbPath);
    const db = new SQL.Database(buffer);

    // Cache instance
    dbInstance = db;
    dbLoadTime = Date.now();

    const loadTime = Date.now() - startTime;
    console.log(`[SQL] Database loaded in ${loadTime}ms`);

    return db;
  } catch (error) {
    console.error('[SQL] Error loading database:', error);
    throw new Error(`Failed to load database: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * Executes a SQL query
 * @param query - SQL query string
 * @returns Query result
 */
export async function executeQuery(query: string): Promise<SQLQueryResult> {
  const startTime = Date.now();

  try {
    const db = await loadDatabase();
    const results = db.exec(query);

    const executionTime = Date.now() - startTime;

    if (results.length === 0) {
      return {
        success: true,
        data: [],
        query,
        executionTime
      };
    }

    // Convert results to array of objects
    const columns = results[0].columns;
    const values = results[0].values;

    const data = values.map(row => {
      const obj: any = {};
      columns.forEach((col, i) => {
        obj[col] = row[i];
      });
      return obj;
    });

    return {
      success: true,
      data,
      query,
      executionTime
    };
  } catch (error) {
    console.error('[SQL] Query error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      query
    };
  }
}

// ============================================================================
// AGGREGATION QUERIES
// ============================================================================

/**
 * Gets statistics by municipality
 * @param filters - Optional filters (type, year)
 * @returns Aggregation results
 */
export async function getStatsByMunicipality(filters?: {
  type?: string;
  year?: number;
}): Promise<SQLQueryResult> {
  let query = `
    SELECT 
      municipality,
      COUNT(*) as total,
      SUM(CASE WHEN type = 'decreto' THEN 1 ELSE 0 END) as decretos,
      SUM(CASE WHEN type = 'ordenanza' THEN 1 ELSE 0 END) as ordenanzas,
      SUM(CASE WHEN type = 'resolucion' THEN 1 ELSE 0 END) as resoluciones,
      MIN(year) as year_min,
      MAX(year) as year_max
    FROM normativas
  `;

  const conditions: string[] = [];

  if (filters?.type) {
    conditions.push(`type = '${filters.type}'`);
  }

  if (filters?.year) {
    conditions.push(`year = ${filters.year}`);
  }

  if (conditions.length > 0) {
    query += ` WHERE ${conditions.join(' AND ')}`;
  }

  query += `
    GROUP BY municipality
    ORDER BY total DESC
  `;

  return executeQuery(query);
}

/**
 * Finds municipality with most/least normativas
 * @param type - Type of normativa (decreto, ordenanza, etc.)
 * @param year - Year filter
 * @param mode - 'max' or 'min'
 * @returns Comparison result
 */
export async function findMunicipalityByCount(
  type?: string,
  year?: number,
  mode: 'max' | 'min' = 'max'
): Promise<ComparisonResult> {
  const startTime = Date.now();

  try {
    const result = await getStatsByMunicipality({ type, year });

    if (!result.success || !result.data || result.data.length === 0) {
      return {
        success: false,
        answer: 'No se encontraron datos para la consulta.',
        data: []
      };
    }

    const data = result.data as AggregationResult[];

    // Sort by total (ascending for min, descending for max)
    const sorted = [...data].sort((a, b) => 
      mode === 'max' ? b.total - a.total : a.total - b.total
    );

    const winner = sorted[0];
    const typeLabel = type ? type : 'normativas';
    const yearLabel = year ? ` del año ${year}` : '';

    // Generate answer
    const answer = mode === 'max'
      ? `**${winner.municipality}** es el municipio con más ${typeLabel}${yearLabel}, con un total de **${winner.total.toLocaleString('es-AR')}**.`
      : `**${winner.municipality}** es el municipio con menos ${typeLabel}${yearLabel}, con un total de **${winner.total.toLocaleString('es-AR')}**.`;

    // Generate markdown table with top 5
    const top5 = sorted.slice(0, 5);
    let markdown = '\n\n### Ranking de Municipios\n\n';
    markdown += '| Posición | Municipio | Total |\n';
    markdown += '|----------|-----------|-------|\n';
    top5.forEach((item, index) => {
      markdown += `| ${index + 1} | ${item.municipality} | ${item.total.toLocaleString('es-AR')} |\n`;
    });

    const executionTime = Date.now() - startTime;
    console.log(`[SQL] Comparison query completed in ${executionTime}ms`);

    return {
      success: true,
      answer,
      data: sorted,
      markdown
    };
  } catch (error) {
    console.error('[SQL] Comparison error:', error);
    return {
      success: false,
      answer: 'Error al procesar la consulta comparativa.',
      data: []
    };
  }
}

/**
 * Gets count by municipality and type
 * @param municipality - Municipality name
 * @param type - Type of normativa
 * @param year - Year filter
 * @returns Count result
 */
export async function getCountByMunicipalityAndType(
  municipality?: string,
  type?: string,
  year?: number
): Promise<SQLQueryResult> {
  let query = `
    SELECT 
      municipality,
      type,
      COUNT(*) as count
    FROM normativas
  `;

  const conditions: string[] = [];

  if (municipality) {
    conditions.push(`municipality = '${municipality}'`);
  }

  if (type) {
    conditions.push(`type = '${type}'`);
  }

  if (year) {
    conditions.push(`year = ${year}`);
  }

  if (conditions.length > 0) {
    query += ` WHERE ${conditions.join(' AND ')}`;
  }

  query += `
    GROUP BY municipality, type
    ORDER BY count DESC
  `;

  return executeQuery(query);
}

/**
 * Gets temporal statistics (by year)
 * @param municipality - Municipality filter
 * @param type - Type filter
 * @returns Temporal stats
 */
export async function getTemporalStats(
  municipality?: string,
  type?: string
): Promise<SQLQueryResult> {
  let query = `
    SELECT 
      year,
      COUNT(*) as total,
      SUM(CASE WHEN type = 'decreto' THEN 1 ELSE 0 END) as decretos,
      SUM(CASE WHEN type = 'ordenanza' THEN 1 ELSE 0 END) as ordenanzas,
      SUM(CASE WHEN type = 'resolucion' THEN 1 ELSE 0 END) as resoluciones
    FROM normativas
  `;

  const conditions: string[] = [];

  if (municipality) {
    conditions.push(`municipality = '${municipality}'`);
  }

  if (type) {
    conditions.push(`type = '${type}'`);
  }

  if (conditions.length > 0) {
    query += ` WHERE ${conditions.join(' AND ')}`;
  }

  query += `
    GROUP BY year
    ORDER BY year DESC
  `;

  return executeQuery(query);
}

// ============================================================================
// QUERY DETECTION AND ROUTING
// ============================================================================

/**
 * Detects if query is a comparison between municipalities
 * @param query - User query
 * @returns true if comparison query
 */
export function isComparisonQuery(query: string): boolean {
  const comparisonPatterns = [
    /cu[aá]l.*municipio.*(m[aá]s|menos|mayor|menor|m[aá]ximo|m[ií]nimo)/i,
    /qu[eé].*municipio.*(m[aá]s|menos|mayor|menor|m[aá]ximo|m[ií]nimo)/i,
    /qu[eé].*partido.*(m[aá]s|menos|mayor|menor|m[aá]ximo|m[ií]nimo)/i,
    /municipio.*(con|que|tiene).*(m[aá]s|menos|mayor|menor)/i,
    /ranking.*municipios/i,
    /comparar.*municipios/i,
  ];

  return comparisonPatterns.some(p => p.test(query));
}

/**
 * Extracts filters from comparison query
 * @param query - User query
 * @returns Extracted filters
 */
export function extractComparisonFilters(query: string): {
  type?: string;
  year?: number;
  mode: 'max' | 'min';
} {
  const lowerQuery = query.toLowerCase();

  // Extract type
  let type: string | undefined;
  if (/decretos?/i.test(query)) type = 'decreto';
  else if (/ordenanzas?/i.test(query)) type = 'ordenanza';
  else if (/resoluciones?/i.test(query)) type = 'resolucion';

  // Extract year
  const yearMatch = query.match(/\b(20\d{2})\b/);
  const year = yearMatch ? parseInt(yearMatch[1], 10) : undefined;

  // Extract mode (más/menos)
  const mode = /menos|menor|m[ií]nimo/i.test(query) ? 'min' : 'max';

  return { type, year, mode };
}

/**
 * Handles comparison query end-to-end
 * @param query - User query
 * @returns Comparison result
 */
export async function handleComparisonQuery(query: string): Promise<ComparisonResult> {
  console.log(`[SQL] Handling comparison query: "${query}"`);

  const filters = extractComparisonFilters(query);
  console.log(`[SQL] Extracted filters:`, filters);

  return findMunicipalityByCount(filters.type, filters.year, filters.mode);
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Gets database statistics
 * @returns Database stats
 */
export async function getDatabaseStats(): Promise<{
  totalNormativas: number;
  municipalities: number;
  years: { min: number; max: number };
  byType: Record<string, number>;
}> {
  try {
    const db = await loadDatabase();

    // Total normativas
    const totalResult = db.exec('SELECT COUNT(*) as total FROM normativas');
    const total = totalResult[0]?.values[0]?.[0] as number || 0;

    // Municipalities
    const munResult = db.exec('SELECT COUNT(DISTINCT municipality) as count FROM normativas');
    const municipalities = munResult[0]?.values[0]?.[0] as number || 0;

    // Years
    const yearResult = db.exec('SELECT MIN(year) as min, MAX(year) as max FROM normativas');
    const years = {
      min: yearResult[0]?.values[0]?.[0] as number || 0,
      max: yearResult[0]?.values[0]?.[1] as number || 0
    };

    // By type
    const typeResult = db.exec('SELECT type, COUNT(*) as count FROM normativas GROUP BY type');
    const byType: Record<string, number> = {};
    typeResult[0]?.values.forEach(row => {
      byType[row[0] as string] = row[1] as number;
    });

    return {
      totalNormativas: total,
      municipalities,
      years,
      byType
    };
  } catch (error) {
    console.error('[SQL] Error getting stats:', error);
    return {
      totalNormativas: 0,
      municipalities: 0,
      years: { min: 0, max: 0 },
      byType: {}
    };
  }
}

/**
 * Closes database connection
 */
export function closeDatabase(): void {
  if (dbInstance) {
    dbInstance.close();
    dbInstance = null;
    dbLoadTime = 0;
    console.log('[SQL] Database closed');
  }
}
