/**
 * sqlite-retriever.ts
 *
 * Retriever de normativas usando SQLite como backend.
 * Mucho más eficiente que parsear archivos JSON gigantes.
 *
 * @version 1.0.0
 * @created 2026-01-28
 */

import Database from 'better-sqlite3';
import path from 'path';
import type { Source, SearchResult, SearchOptions } from './retriever';

// Singleton de la base de datos
let dbInstance: Database.Database | null = null;

/**
 * Obtiene la conexión a la base de datos SQLite
 */
function getDatabase(): Database.Database {
  if (dbInstance) return dbInstance;

  // Ruta a la base de datos (en python-cli)
  const dbPath = path.join(process.cwd(), '..', 'python-cli', 'normativas.db');

  console.log(`[SQLite] 📂 Abriendo BD: ${dbPath}`);

  dbInstance = new Database(dbPath, {
    readonly: true, // Solo lectura para consultas
    fileMustExist: true,
  });

  // Optimizaciones de rendimiento
  dbInstance.pragma('journal_mode = WAL');
  dbInstance.pragma('synchronous = NORMAL');
  dbInstance.pragma('cache_size = -64000'); // 64MB cache
  dbInstance.pragma('temp_store = MEMORY');

  console.log('[SQLite] ✅ BD abierta correctamente');

  return dbInstance;
}

/**
 * Construye la cláusula WHERE para filtros de búsqueda
 */
function buildWhereClause(options: SearchOptions): { where: string; params: (string | number)[] } {
  const conditions: string[] = [];
  const params: (string | number)[] = [];

  if (options.municipality) {
    conditions.push('municipality LIKE ?');
    params.push(`%${options.municipality}%`);
  }

  if (options.type && options.type !== 'all') {
    conditions.push('type = ?');
    params.push(options.type);
  }

  // Filtro de fecha: convertir DD/MM/YYYY a YYYY-MM-DD para comparación
  if (options.dateFrom) {
    // SQLite guarda fechas como DD/MM/YYYY, necesitamos invertir para comparar
    conditions.push("substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2) >= ?");
    params.push(options.dateFrom);
  }

  if (options.dateTo) {
    conditions.push("substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2) <= ?");
    params.push(options.dateTo);
  }

  return {
    where: conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '',
    params,
  };
}

/**
 * Obtiene el conteo total de resultados para filtros dados
 */
function getCount(db: Database.Database, options: SearchOptions): number {
  const { where, params } = buildWhereClause(options);
  const stmt = db.prepare(`SELECT COUNT(*) as count FROM normativas ${where}`);
  const result = stmt.get(...params) as { count: number };
  return result?.count || 0;
}

/**
 * Recupera normativas usando SQLite
 */
export async function retrieveFromSQLite(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const startTime = Date.now();

  try {
    const db = getDatabase();
    const { where, params } = buildWhereClause(options);

    // Límite de resultados
    const limit = options.limit || 10;

    // Para listados masivos, primero obtener conteo
    const totalCount = getCount(db, options);

    console.log(`[SQLite] 📊 Total coincidencias: ${totalCount.toLocaleString()}`);

    // Consulta principal - solo campos necesarios
    const searchQuery = `
      SELECT
        id,
        municipality,
        type,
        number,
        year,
        date,
        title,
        source_bulletin,
        url
      FROM normativas
      ${where}
      ORDER BY date DESC
      LIMIT ${Math.min(limit, 10000)}
    `;

    const stmt = db.prepare(searchQuery);
    const rows = stmt.all(...params) as Array<{
      id: string;
      municipality: string;
      type: string;
      number: string;
      year: string;
      date: string;
      title: string;
      source_bulletin: string;
      url: string;
      status: string;
    }>;

    // Construir fuentes
    const sources: Source[] = rows.map(row => ({
      title: `${row.type} ${row.number}/${row.year} - ${row.municipality}`,
      url: row.url || `https://sibom.slyt.gba.gob.ar/`,
      municipality: row.municipality,
      type: row.type,
      status: row.status || 'vigente',
    }));

    // Construir contexto (metadata only)
    const MAX_CONTEXT_ENTRIES = 100;
    const contextRows = rows.slice(0, MAX_CONTEXT_ENTRIES);

    const context = contextRows.length > 0
      ? contextRows.map(row =>
          `[${row.municipality}] ${row.type.toUpperCase()} N° ${row.number}/${row.year} - ${row.date}\nTítulo: ${row.title?.substring(0, 100) || 'Sin título'}`
        ).join('\n\n---\n\n')
      : `No se encontró información específica para: "${query}"`;

    const duration = Date.now() - startTime;
    console.log(`[SQLite] ✅ Query completada en ${duration}ms - ${rows.length.toLocaleString()} resultados (total: ${totalCount.toLocaleString()})`);

    return { context, sources, totalCount };
  } catch (error) {
    console.error('[SQLite] Error en consulta:', error);
    throw error;
  }
}

/**
 * Obtiene estadísticas de la base de datos SQLite
 */
export async function getSQLiteStats() {
  try {
    const db = getDatabase();

    const totalStmt = db.prepare('SELECT COUNT(*) as count FROM normativas');
    const total = (totalStmt.get() as { count: number })?.count || 0;

    const munStmt = db.prepare('SELECT COUNT(DISTINCT municipality) as count FROM normativas');
    const municipalities = (munStmt.get() as { count: number })?.count || 0;

    const listStmt = db.prepare(`
      SELECT DISTINCT municipality FROM normativas ORDER BY municipality
    `);
    const listRows = listStmt.all() as Array<{ municipality: string }>;
    const municipalityList = listRows.map(r => r.municipality);

    // Obtener fecha de última actualización del archivo
    const fs = await import('fs/promises');
    const dbPath = path.join(process.cwd(), '..', 'python-cli', 'normativas.db');
    let lastUpdated: string | null = null;
    try {
      const stats = await fs.stat(dbPath);
      lastUpdated = stats.mtime.toISOString();
    } catch {
      // Ignorar error si no existe el archivo
    }

    return {
      totalDocuments: total,
      municipalities,
      municipalityList,
      lastUpdated,
      source: 'SQLite',
    };
  } catch (error) {
    console.error('[SQLite] Error obteniendo estadísticas:', error);
    throw error;
  }
}

/**
 * Verifica si SQLite está disponible y tiene datos
 */
export function isSQLiteAvailable(): boolean {
  try {
    const dbPath = path.join(process.cwd(), '..', 'python-cli', 'normativas.db');
    const fs = require('fs');
    return fs.existsSync(dbPath);
  } catch {
    return false;
  }
}
