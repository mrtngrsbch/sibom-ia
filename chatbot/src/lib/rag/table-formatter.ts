/**
 * table-formatter.ts
 *
 * Formatea tablas estructuradas para consumo del LLM en queries computacionales.
 * Incluye datos tabulares en Markdown + estadísticas pre-calculadas.
 *
 * @version 1.0.0
 * @created 2026-01-08
 * @author Kilo Code
 */

import type { StructuredTable, ColumnStats } from '@/lib/types';

/**
 * Formatea una tabla estructurada para el LLM
 * @param table - Tabla estructurada extraída del boletín
 * @returns String formateado con Markdown + estadísticas
 */
export function formatTableForLLM(table: StructuredTable): string {
  const parts: string[] = [];

  // 1. Título y contexto
  parts.push(`### ${table.title}`);
  if (table.context) {
    parts.push(`**Contexto:** ${table.context}`);
  }
  if (table.description) {
    parts.push(`**Descripción:** ${table.description}`);
  }
  parts.push(''); // Línea en blanco

  // 2. Tabla en formato Markdown
  parts.push('**Datos:**');
  parts.push(table.markdown);
  parts.push(''); // Línea en blanco

  // 3. Estadísticas pre-calculadas (si existen columnas numéricas)
  if (Object.keys(table.stats.numeric_stats).length > 0) {
    parts.push('**Estadísticas:**');
    
    for (const [columnName, stats] of Object.entries(table.stats.numeric_stats)) {
      parts.push(`- **${columnName}:**`);
      parts.push(`  - Total: ${formatNumber(stats.sum)}`);
      parts.push(`  - Máximo: ${formatNumber(stats.max)}`);
      parts.push(`  - Mínimo: ${formatNumber(stats.min)}`);
      parts.push(`  - Promedio: ${formatNumber(stats.avg)}`);
      parts.push(`  - Cantidad de valores: ${stats.count}`);
    }
    parts.push(''); // Línea en blanco
  }

  // 4. Información adicional
  parts.push(`**Total de filas:** ${table.stats.row_count}`);
  parts.push(`**Columnas:** ${table.schema.columns.join(', ')}`);

  // 5. Advertencias de errores (si existen)
  if (table.extraction_errors.length > 0) {
    parts.push('');
    parts.push('**⚠️ Advertencias de extracción:**');
    table.extraction_errors.forEach(error => {
      parts.push(`- ${error}`);
    });
  }

  return parts.join('\n');
}

/**
 * Formatea múltiples tablas para el LLM
 * @param tables - Array de tablas estructuradas
 * @returns String formateado con todas las tablas separadas
 */
export function formatTablesForLLM(tables: StructuredTable[]): string {
  if (tables.length === 0) {
    return '';
  }

  const parts: string[] = [];
  parts.push('## 📊 DATOS TABULARES ESTRUCTURADOS');
  parts.push('');
  parts.push('Los siguientes datos provienen de tablas extraídas del boletín oficial.');
  parts.push('Puedes realizar cálculos, comparaciones y agregaciones sobre estos datos.');
  parts.push('');
  parts.push('---');
  parts.push('');

  tables.forEach((table, index) => {
    parts.push(formatTableForLLM(table));
    
    // Separador entre tablas (excepto la última)
    if (index < tables.length - 1) {
      parts.push('');
      parts.push('---');
      parts.push('');
    }
  });

  return parts.join('\n');
}

/**
 * Formatea un número con separador de miles para legibilidad
 * @param num - Número a formatear
 * @returns String formateado (ej: 1500.50 → "1.500,50")
 */
function formatNumber(num: number): string {
  // Formato argentino: punto como separador de miles, coma como decimal
  const parts = num.toFixed(2).split('.');
  const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const decimalPart = parts[1];
  
  // Si no hay decimales significativos, omitir
  if (decimalPart === '00') {
    return integerPart;
  }
  
  return `${integerPart},${decimalPart}`;
}

/**
 * Extrae tablas relevantes basándose en la query
 * @param tables - Array de todas las tablas disponibles
 * @param query - Query del usuario
 * @returns Array de tablas relevantes (filtradas por keywords)
 */
export function filterRelevantTables(
  tables: StructuredTable[],
  query: string
): StructuredTable[] {
  const queryLower = query.toLowerCase();
  const queryTerms = queryLower.split(/\s+/).filter(t => t.length > 2);

  if (queryTerms.length === 0) {
    return tables; // Si no hay términos, devolver todas
  }

  // Calcular score de relevancia para cada tabla
  const scoredTables = tables.map(table => {
    let score = 0;

    // Match en título (peso alto)
    const titleLower = table.title.toLowerCase();
    queryTerms.forEach(term => {
      if (titleLower.includes(term)) {
        score += 10;
      }
    });

    // Match en descripción (peso medio)
    const descLower = table.description.toLowerCase();
    queryTerms.forEach(term => {
      if (descLower.includes(term)) {
        score += 5;
      }
    });

    // Match en contexto (peso bajo)
    const contextLower = table.context.toLowerCase();
    queryTerms.forEach(term => {
      if (contextLower.includes(term)) {
        score += 2;
      }
    });

    // Match en nombres de columnas (peso medio)
    table.schema.columns.forEach(col => {
      const colLower = col.toLowerCase();
      queryTerms.forEach(term => {
        if (colLower.includes(term)) {
          score += 5;
        }
      });
    });

    return { table, score };
  });

  // Filtrar tablas con score > 0 y ordenar por relevancia
  return scoredTables
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score)
    .map(({ table }) => table);
}
