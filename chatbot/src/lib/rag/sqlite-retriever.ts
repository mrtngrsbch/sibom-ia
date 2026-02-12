/**
 * SQLite Retriever - Accesses SQLite database for document retrieval
 * Uses sqlite3 package (better-sqlite3 replacement)
 */

import sqlite3 from 'sqlite3';
import { Database } from 'sqlite3';

const DB_PATH = process.env.SQLITE_DB_PATH || './data/boletines.db';

// Singleton database instance
let dbInstance: Database | null = null;

/**
 * Get or create database connection
 */
export function getDatabase(): Database {
  if (dbInstance) {
    return dbInstance;
  }

  const db = new sqlite3.Database(DB_PATH, (err) => {
    if (err) {
      console.error('Error opening database:', err);
      throw err;
    }
  });

  // Set pragmas for performance
  db.run('PRAGMA journal_mode = WAL');
  db.run('PRAGMA synchronous = NORMAL');
  db.run('PRAGMA cache_size = -64000'); // 64MB cache
  db.run('PRAGMA temp_store = MEMORY');

  dbInstance = db;
  return dbInstance;
}

/**
 * Check if SQLite database is available
 */
export function isSQLiteAvailable(): boolean {
  try {
    // Check if database file exists
    const fs = require('fs');
    if (!fs.existsSync(DB_PATH)) {
      return false;
    }
    
    // Try to open database to verify it's accessible
    const db = getDatabase();
    if (!db) {
      return false;
    }
    
    return true;
  } catch (error) {
    console.error('SQLite availability check failed:', error);
    return false;
  }
}

/**
 * Search documents by query
 */
export async function searchDocuments(
  query: string,
  limit: number = 10,
  filters?: {
    municipality?: string;
    type?: string;
    year?: string;
  }
): Promise<Array<{
  id: string;
  municipality: string;
  type: string;
  number: string;
  year: string;
  date: string;
  title: string;
  source_bulletin: string;
  norma_url: string;
  status: string;
}>> {
  const db = getDatabase();

  let sql = `
    SELECT
      id,
      municipality,
      type,
      number,
      year,
      date,
      title,
      source_bulletin,
      norma_url,
      status
    FROM documents
    WHERE 1=1
  `;

  const params: any[] = [];

  // Add filters
  if (filters?.municipality) {
    sql += ` AND municipality = ?`;
    params.push(filters.municipality);
  }

  if (filters?.type) {
    sql += ` AND type = ?`;
    params.push(filters.type);
  }

  if (filters?.year) {
    sql += ` AND year = ?`;
    params.push(filters.year);
  }

  // Add search query
  if (query) {
    sql += ` AND (title LIKE ? OR content LIKE ?)`;
    const searchTerm = `%${query}%`;
    params.push(searchTerm, searchTerm);
  }

  sql += ` ORDER BY date DESC LIMIT ?`;
  params.push(limit);

  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) {
        reject(err);
      } else {
        resolve(rows as any);
      }
    });
  });
}

/**
 * Get document by ID
 */
export async function getDocumentById(
  id: string
): Promise<{
  id: string;
  municipality: string;
  type: string;
  number: string;
  year: string;
  date: string;
  title: string;
  source_bulletin: string;
  norma_url: string;
  status: string;
  content?: string;
} | null> {
  const db = getDatabase();

  const sql = `
    SELECT
      id,
      municipality,
      type,
      number,
      year,
      date,
      title,
      source_bulletin,
      norma_url,
      status,
      content
    FROM documents
    WHERE id = ?
  `;

  return new Promise((resolve, reject) => {
    db.get(sql, [id], (err, row) => {
      if (err) {
        reject(err);
      } else {
        resolve(row as any || null);
      }
    });
  });
}

/**
 * Get document count
 */
export async function getDocumentCount(filters?: {
  municipality?: string;
  type?: string;
  year?: string;
}): Promise<number> {
  const db = getDatabase();

  let sql = 'SELECT COUNT(*) as count FROM documents WHERE 1=1';
  const params: any[] = [];

  if (filters?.municipality) {
    sql += ` AND municipality = ?`;
    params.push(filters.municipality);
  }

  if (filters?.type) {
    sql += ` AND type = ?`;
    params.push(filters.type);
  }

  if (filters?.year) {
    sql += ` AND year = ?`;
    params.push(filters.year);
  }

  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row: any) => {
      if (err) {
        reject(err);
      } else {
        resolve(row?.count || 0);
      }
    });
  });
}

/**
 * Get unique municipalities
 */
export async function getMunicipalities(): Promise<string[]> {
  const db = getDatabase();

  const sql = 'SELECT DISTINCT municipality FROM documents ORDER BY municipality';

  return new Promise((resolve, reject) => {
    db.all(sql, [], (err, rows: any[]) => {
      if (err) {
        reject(err);
      } else {
        resolve(rows.map(row => row.municipality));
      }
    });
  });
}

/**
 * Get unique document types
 */
export async function getDocumentTypes(): Promise<string[]> {
  const db = getDatabase();

  const sql = 'SELECT DISTINCT type FROM documents ORDER BY type';

  return new Promise((resolve, reject) => {
    db.all(sql, [], (err, rows: any[]) => {
      if (err) {
        reject(err);
      } else {
        resolve(rows.map(row => row.type));
      }
    });
  });
}

/**
 * Get unique years
 */
export async function getYears(): Promise<string[]> {
  const db = getDatabase();

  const sql = 'SELECT DISTINCT year FROM documents ORDER BY year DESC';

  return new Promise((resolve, reject) => {
    db.all(sql, [], (err, rows: any[]) => {
      if (err) {
        reject(err);
      } else {
        resolve(rows.map(row => row.year));
      }
    });
  });
}

/**
 * Get statistics
 */
export async function getStatistics(): Promise<{
  total: number;
  municipalities: number;
  types: number;
  years: number;
}> {
  const db = getDatabase();

  const totalSql = 'SELECT COUNT(*) as count FROM documents';
  const municipalitiesSql = 'SELECT COUNT(DISTINCT municipality) as count FROM documents';
  const typesSql = 'SELECT COUNT(DISTINCT type) as count FROM documents';
  const yearsSql = 'SELECT COUNT(DISTINCT year) as count FROM documents';

  const [total, municipalities, types, years] = await Promise.all([
    new Promise<number>((resolve, reject) => {
      db.get(totalSql, [], (err, row: any) => {
        if (err) reject(err);
        else resolve(row?.count || 0);
      });
    }),
    new Promise<number>((resolve, reject) => {
      db.get(municipalitiesSql, [], (err, row: any) => {
        if (err) reject(err);
        else resolve(row?.count || 0);
      });
    }),
    new Promise<number>((resolve, reject) => {
      db.get(typesSql, [], (err, row: any) => {
        if (err) reject(err);
        else resolve(row?.count || 0);
      });
    }),
    new Promise<number>((resolve, reject) => {
      db.get(yearsSql, [], (err, row: any) => {
        if (err) reject(err);
        else resolve(row?.count || 0);
      });
    }),
  ]);

  return {
    total,
    municipalities,
    types,
    years,
  };
}

/**
 * Close database connection
 */
export function closeDatabase(): void {
  if (dbInstance) {
    dbInstance.close();
    dbInstance = null;
  }
}
