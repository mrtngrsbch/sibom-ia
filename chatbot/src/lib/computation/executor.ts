/**
 * executor.ts
 *
 * Ejecuta queries computacionales combinando el parser y el motor de cómputo.
 * Es el punto de entrada principal para el sistema RAG.
 *
 * @version 1.0.0
 * @created 2026-01-09
 * @author Kilo Code
 */

import type { StructuredTable } from '@/lib/types';
import type {
  ParsedComputationalQuery,
  ComputationalQueryResult,
  ComputationOperation
} from './query-parser';
import type { ComputationResult, AggregationResult } from './table-engine';

import {
  parseComputationalQuery,
  extractMunicipality,
  explainOperation
} from './query-parser';

import {
  sumColumn,
  avgColumn,
  minColumn,
  maxColumn,
  countRows,
  findMinRow,
  findMaxRow,
  filterRows,
  groupByColumn,
  compareAcrossGroups,
  findRelevantTables,
  formatComputationResult,
  formatAggregationAsMarkdown,
  formatRowsAsMarkdown,
  findColumnByName,
} from './table-engine';

/**
 * Ejecuta una query computacional sobre las tablas disponibles
 * @param query - Query del usuario en lenguaje natural
 * @param allTables - Todas las tablas disponibles (del boletín)
 * @returns Resultado formateado para mostrar al usuario
 */
export function executeComputationalQuery(
  query: string,
  allTables: StructuredTable[]
): ComputationalQueryResult {
  // 1. Verificar que haya tablas
  if (!allTables || allTables.length === 0) {
    return {
      success: false,
      operation: 'search',
      answer: 'No hay tablas estructuradas disponibles en este boletín para realizar cómputos.',
      error: 'NO_TABLES'
    };
  }

  // 2. Filtrar tablas relevantes por keywords
  const relevantTables = findRelevantTables(allTables, query);

  if (relevantTables.length === 0) {
    return {
      success: false,
      operation: 'search',
      answer: 'No se encontraron tablas relevantes para esta consulta.',
      error: 'NO_RELEVANT_TABLES'
    };
  }

  // 3. Parsear la query
  const parsed = parseComputationalQuery(query, relevantTables);

  if (!parsed) {
    return {
      success: false,
      operation: 'parse',
      answer: 'No pude entender qué operación cómputo deseas realizar. ' +
               'Intenta reformular la pregunta (ej: "¿cuál es la suma de todos los salarios?").',
      error: 'PARSE_ERROR'
    };
  }

  // 4. Ejecutar la operación correspondiente
  try {
    return executeOperation(parsed, relevantTables, query);
  } catch (error) {
    return {
      success: false,
      operation: parsed.operation,
      answer: `Error al ejecutar la operación: ${error instanceof Error ? error.message : 'desconocido'}`,
      error: 'EXECUTION_ERROR'
    };
  }
}

/**
 * Ejecuta una operación específica basada en la query parseada
 */
function executeOperation(
  parsed: ParsedComputationalQuery,
  tables: StructuredTable[],
  originalQuery: string
): ComputationalQueryResult {
  const { operation, targetColumn, keywords } = parsed;

  // Si no se identificó una columna, intentar encontrarla
  let column = targetColumn;
  if (!column) {
    const columnMatches = findColumnByName(tables, keywords[0] || 'monto');
    if (columnMatches.length > 0) {
      column = columnMatches[0].column;
    }
  }

  if (!column) {
    return {
      success: false,
      operation,
      answer: 'No pude identificar qué columna de la tabla deseas consultar. ' +
               'Por favor sé más específico (ej: "¿cuál es la suma de las tasas viales?").',
      error: 'NO_COLUMN_IDENTIFIED'
    };
  }

  // Ejecutar según tipo de operación
  switch (operation) {
    case 'sum':
      return executeSum(tables, column);

    case 'avg':
      return executeAvg(tables, column);

    case 'min':
      return executeMin(tables, column);

    case 'max':
      return executeMax(tables, column);

    case 'count':
      return executeCount(tables, column, parsed.filters);

    case 'find_min_row':
      return executeFindMinRow(tables, column, originalQuery);

    case 'find_max_row':
      return executeFindMaxRow(tables, column, originalQuery);

    case 'filter':
      return executeFilter(tables, column, parsed.filters, originalQuery);

    case 'compare':
      return executeCompare(tables, column, originalQuery);

    case 'group_by':
      return executeGroupBy(tables, column, originalQuery);

    default:
      return {
        success: false,
        operation,
        answer: `La operación "${operation}" aún no está implementada.`,
        error: 'NOT_IMPLEMENTED'
      };
  }
}

// ============================================================================
// EJECUTORES ESPECÍFICOS
// ============================================================================

function executeSum(tables: StructuredTable[], column: string): ComputationalQueryResult {
  const result = sumColumn(tables, column);

  if (!result) {
    return {
      success: false,
      operation: 'sum',
      answer: `No se encontraron valores numéricos válidos de tasas o montos monetarios en los datos disponibles. ` +
               `Los boletines municipales contienen descripciones de tasas pero no los valores numéricos específicos. ` +
               `Para obtener los valores exactos, se debe consultar la ordenanza impositiva vigente de cada municipio directamente.`,
      error: 'NO_NUMERIC_VALUES'
    };
  }

  return {
    success: true,
    operation: 'SUM',
    answer: formatComputationResult(result),
    metadata: {
      tableName: result.tableName,
      column: result.column,
      count: result.metadata?.count,
      average: result.metadata?.average
    }
  };
}

function executeAvg(tables: StructuredTable[], column: string): ComputationalQueryResult {
  const result = avgColumn(tables, column);

  if (!result) {
    return {
      success: false,
      operation: 'avg',
      answer: `No se encontraron valores numéricos válidos de tasas o montos monetarios en los datos disponibles. ` +
               `Los boletines municipales contienen descripciones de tasas pero no los valores numéricos específicos. ` +
               `Para obtener los valores exactos, se debe consultar la ordenanza impositiva vigente de cada municipio directamente.`,
      error: 'NO_NUMERIC_VALUES'
    };
  }

  return {
    success: true,
    operation: 'AVG',
    answer: formatComputationResult(result),
    metadata: {
      tableName: result.tableName,
      column: result.column,
      sum: result.metadata?.sum,
      count: result.metadata?.count
    }
  };
}

function executeMin(tables: StructuredTable[], column: string): ComputationalQueryResult {
  const result = minColumn(tables, column);

  if (!result) {
    return {
      success: false,
      operation: 'min',
      answer: `No se encontraron valores numéricos válidos de tasas o montos monetarios en los datos disponibles. ` +
               `Los boletines municipales contienen descripciones de tasas pero no los valores numéricos específicos. ` +
               `Para obtener los valores exactos, se debe consultar la ordenanza impositiva vigente de cada municipio directamente.`,
      error: 'NO_NUMERIC_VALUES'
    };
  }

  return {
    success: true,
    operation: 'MIN',
    answer: formatComputationResult(result),
    metadata: {
      tableName: result.tableName,
      column: result.column
    }
  };
}

function executeMax(tables: StructuredTable[], column: string): ComputationalQueryResult {
  const result = maxColumn(tables, column);

  if (!result) {
    return {
      success: false,
      operation: 'max',
      answer: `No se encontraron valores numéricos válidos de tasas o montos monetarios en los datos disponibles. ` +
               `Los boletines municipales contienen descripciones de tasas pero no los valores numéricos específicos. ` +
               `Para obtener los valores exactos, se debe consultar la ordenanza impositiva vigente de cada municipio directamente.`,
      error: 'NO_NUMERIC_VALUES'
    };
  }

  return {
    success: true,
    operation: 'MAX',
    answer: formatComputationResult(result),
    metadata: {
      tableName: result.tableName,
      column: result.column
    }
  };
}

function executeCount(
  tables: StructuredTable[],
  column: string,
  filters?: any[]
): ComputationalQueryResult {
  const result = countRows(tables, column, filters);

  if (!result) {
    return {
      success: false,
      operation: 'count',
      answer: `No se encontraron filas para contar.`,
      error: 'NO_ROWS'
    };
  }

  return {
    success: true,
    operation: 'COUNT',
    answer: formatComputationResult(result),
    metadata: {
      tableName: result.tableName,
      column: result.column
    }
  };
}

function executeFindMinRow(
  tables: StructuredTable[],
  column: string,
  query: string
): ComputationalQueryResult {
  const result = findMinRow(tables, column);

  if (!result) {
    return {
      success: false,
      operation: 'find_min_row',
      answer: `No se encontraron valores numéricos en la columna "${column}".`,
      error: 'NO_NUMERIC_VALUES'
    };
  }

  // Buscar columna que identifica la entidad (municipio, categoría, etc.)
  const entityColumn = result.table.schema.columns.find(c =>
    /municipio|partido|categoria|categoría|tipo|descri/.test(c.toLowerCase())
  );

  const entityName = entityColumn ? String(result.row[entityColumn]) : 'Registro';
  const entityValue = entityColumn ? String(result.row[entityColumn] || 'N/A') : 'N/A';

  return {
    success: true,
    operation: 'FIND_MIN',
    answer: `**${entityName}**: ${entityValue}\n` +
             `**Valor mínimo**: ${formatArgentineNumber(result.value)}`,
    markdown: formatRowAsMarkdown(result.table, result.row),
    metadata: {
      tableName: result.table.title,
      column,
      entityColumn: entityColumn || 'N/A',
      value: result.value
    }
  };
}

function executeFindMaxRow(
  tables: StructuredTable[],
  column: string,
  query: string
): ComputationalQueryResult {
  const result = findMaxRow(tables, column);

  if (!result) {
    return {
      success: false,
      operation: 'find_max_row',
      answer: `No se encontraron valores numéricos en la columna "${column}".`,
      error: 'NO_NUMERIC_VALUES'
    };
  }

  // Buscar columna que identifica la entidad
  const entityColumn = result.table.schema.columns.find(c =>
    /municipio|partido|categoria|categoría|tipo|descri/.test(c.toLowerCase())
  );

  const entityName = entityColumn ? String(result.row[entityColumn]) : 'Registro';
  const entityValue = entityColumn ? String(result.row[entityColumn] || 'N/A') : 'N/A';

  return {
    success: true,
    operation: 'FIND_MAX',
    answer: `**${entityName}**: ${entityValue}\n` +
             `**Valor máximo**: ${formatArgentineNumber(result.value)}`,
    markdown: formatRowAsMarkdown(result.table, result.row),
    metadata: {
      tableName: result.table.title,
      column,
      entityColumn: entityColumn || 'N/A',
      value: result.value
    }
  };
}

function executeFilter(
  tables: StructuredTable[],
  column: string,
  filters: any[] | undefined,
  query: string
): ComputationalQueryResult {
  // Extraer filtros de la query (ej: "local comercial")
  const filtersToApply = filters || extractFiltersFromQuery(query, tables);

  let rows;
  if (filtersToApply.length > 0) {
    rows = filterRows(tables, filtersToApply);
  } else {
    // Sin filtros específicos, mostrar las primeras filas de tablas relevantes
    rows = tables.slice(0, 1).flatMap(table =>
      table.data.slice(0, 10).map(row => ({ table, row }))
    );
  }

  if (rows.length === 0) {
    return {
      success: false,
      operation: 'filter',
      answer: 'No se encontraron resultados que coincidan con los criterios.',
      error: 'NO_RESULTS'
    };
  }

  return {
    success: true,
    operation: 'FILTER',
    answer: `**Encontrados ${rows.length} resultados:**\n\n${formatRowsAsMarkdown(rows)}`,
    markdown: formatRowsAsMarkdown(rows),
    metadata: {
      count: rows.length,
      filters: filtersToApply
    }
  };
}

function executeCompare(
  tables: StructuredTable[],
  column: string,
  query: string
): ComputationalQueryResult {
  // Buscar columna de agrupación (municipio, categoría, etc.)
  const groupColumn = tables[0]?.schema.columns.find(c =>
    /municipio|partido|categoria|categoría|tipo|descri/.test(c.toLowerCase())
  );

  if (!groupColumn) {
    // Si no hay columna de agrupación, comparar entre tablas
    const results = compareAcrossGroups(tables, column);

    if (results.length === 0) {
      return {
        success: false,
        operation: 'compare',
        answer: 'No se encontraron datos para comparar.',
        error: 'NO_DATA'
      };
    }

    return {
      success: true,
      operation: 'COMPARE',
      answer: `**Comparación de valores:**\n\n${formatAggregationAsMarkdown(results, column)}`,
      markdown: formatAggregationAsMarkdown(results, column),
      metadata: { results }
    };
  }

  // Agrupar por columna identificada
  const grouped = groupByColumn(tables, groupColumn, column, 'sum');

  if (grouped.length === 0) {
    return {
      success: false,
      operation: 'compare',
      answer: 'No se encontraron datos para comparar.',
      error: 'NO_DATA'
    };
  }

  return {
    success: true,
    operation: 'COMPARE',
    answer: `**Comparación por ${groupColumn}:**\n\n${formatAggregationAsMarkdown(grouped, column)}`,
    markdown: formatAggregationAsMarkdown(grouped, column),
    metadata: { groupColumn, grouped }
  };
}

function executeGroupBy(
  tables: StructuredTable[],
  column: string,
  query: string
): ComputationalQueryResult {
  // Intentar identificar columna de agrupación
  const groupColumn = tables[0]?.schema.columns.find(c =>
    /categor[íi]a|tipo|municipio|partido/.test(c.toLowerCase())
  );

  if (!groupColumn) {
    return {
      success: false,
      operation: 'group_by',
      answer: 'No se pudo identificar una columna para agrupar los datos.',
      error: 'NO_GROUP_COLUMN'
    };
  }

  const grouped = groupByColumn(tables, groupColumn, column, 'sum');

  if (grouped.length === 0) {
    return {
      success: false,
      operation: 'group_by',
      answer: 'No se encontraron datos para agrupar.',
      error: 'NO_DATA'
    };
  }

  return {
    success: true,
    operation: 'GROUP_BY',
    answer: `**Agrupado por ${groupColumn}:**\n\n${formatAggregationAsMarkdown(grouped, column)}`,
    markdown: formatAggregationAsMarkdown(grouped, column),
    metadata: { groupColumn, grouped }
  };
}

// ============================================================================
// UTILIDADES
// ============================================================================

function formatArgentineNumber(num: number): string {
  const parts = num.toFixed(2).split('.');
  const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const decimalPart = parts[1];

  if (decimalPart === '00') return integerPart;
  return `${integerPart},${decimalPart}`;
}

function formatRowAsMarkdown(table: StructuredTable, row: Record<string, any>): string {
  const columns = table.schema.columns;
  const header = '| ' + columns.join(' | ') + ' |';
  const separator = '| ' + columns.map(() => '---').join(' | ') + ' |';

  const values = columns.map(col => {
    const val = row[col];
    return typeof val === 'number' ? formatArgentineNumber(val) : String(val ?? '');
  });
  const dataRow = '| ' + values.join(' | ') + ' |';

  return [header, separator, dataRow].join('\n');
}

function extractFiltersFromQuery(query: string, tables: StructuredTable[]): any[] {
  const filters: any[] = [];
  const lowerQuery = query.toLowerCase();

  // Buscar categoría en la query
  const categoryMatch = query.match(/(?:local|categoria|categoría)\s+([^,\s]+)/i);
  if (categoryMatch) {
    // Buscar columna de categoría
    const catColumn = tables[0]?.schema.columns.find(c =>
      /categor[íi]a|tipo/.test(c.toLowerCase())
    );
    if (catColumn) {
      filters.push({
        column: catColumn,
        operator: 'contains',
        value: categoryMatch[1]
      });
    }
  }

  return filters;
}
