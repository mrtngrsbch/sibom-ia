/**
 * table-engine.ts
 *
 * Motor de cómputo tabular para queries computacionales sobre datos estructurados.
 * Permite SUM, MIN, MAX, AVG, FILTER, AGGREGATE sobre tablas extraídas de boletines.
 *
 * @version 1.0.0
 * @created 2026-01-09
 * @author Kilo Code
 */

import type { StructuredTable, ColumnStats } from '@/lib/types';

/**
 * Resultado de una operación de cómputo
 */
export interface ComputationResult {
  operation: string;
  result: number | string | Record<string, any>;
  tableName?: string;
  column?: string;
  unit?: string;
  metadata?: Record<string, any>;
}

/**
 * Resultado de una agregación por grupo
 */
export interface AggregationResult {
  group: string;
  value: number;
  count: number;
}

/**
 * Filtro para filas de tabla
 */
export interface RowFilter {
  column: string;
  operator: 'equals' | 'contains' | 'gt' | 'lt' | 'gte' | 'lte' | 'between';
  value: any;
  value2?: any; // Para operador 'between'
}

/**
 * Columnas irrelevantes para cómputos de tasas/tarifas
 * Incluye códigos, números de tabla, porcentajes, etc.
 */
const IRRELEVANT_COLUMN_PATTERNS = [
  /^numero|^n[º°]|num/i,           // Números de tabla, artículo
  /^tabla|^tipologia|^tipo[^a-z]/i,  // Tipologías, códigos de tabla
  /^cod|^id|^ref/i,                // Códigos, IDs, referencias
  /^jurisdiccion|^prog|^categ|^fuente|^actividad/i,  // Códigos presupuestarios
  /^columna|^sin_nombre/i,         // Columnas genéricas
];

/**
 * Determina si una columna es relevante para cómputos monetarios
 */
function isRelevantColumn(columnName: string): boolean {
  const lower = columnName.toLowerCase();

  // Excluir columnas irrelevantes
  for (const pattern of IRRELEVANT_COLUMN_PATTERNS) {
    if (pattern.test(lower)) return false;
  }

  return true;
}

/**
 * Determina si un valor es un monto monetario plausible
 */
function isPlausibleMonetaryValue(value: number): boolean {
  // Rechazar valores muy pequeños (probablemente códigos)
  if (value < 10) return false;

  // Rechazar valores muy grandes (probablemente códigos presupuestarios)
  if (value > 1000000000) return false;

  // Aceptar valores en rango de tasas razonables
  return true;
}

/**
 * Extrae el valor numérico de una celda (maneja formato argentino)
 */
function parseCellValue(value: any): number | null {
  if (typeof value === 'number') {
    // Validar que sea un monto plausible
    return isPlausibleMonetaryValue(value) ? value : null;
  }
  if (typeof value !== 'string') return null;

  // Eliminar espacios y símbolos de moneda
  const cleaned = value
    .trim()
    .replace(/\s/g, '')
    .replace(/\$/g, '')
    .replace(/\./g, '') // Eliminar separadores de miles
    .replace(/,/g, '.'); // Convertir coma decimal a punto

  const parsed = parseFloat(cleaned);
  if (isNaN(parsed)) return null;

  // Validar que sea un monto plausible
  return isPlausibleMonetaryValue(parsed) ? parsed : null;
}

/**
 * Formatea un número al formato argentino
 */
function formatArgentineNumber(num: number): string {
  const parts = num.toFixed(2).split('.');
  const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const decimalPart = parts[1];

  if (decimalPart === '00') return integerPart;
  return `${integerPart},${decimalPart}`;
}

// ============================================================================
// OPERACIONES DE AGREGACIÓN SIMPLE
// ============================================================================

/**
 * Suma todos los valores numéricos de una columna
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna a sumar
 * @returns Suma total o null si no hay datos
 */
export function sumColumn(
  tables: StructuredTable[],
  columnName: string
): ComputationResult | null {
  let total = 0;
  let count = 0;
  let sourceTable = '';

  for (const table of tables) {
    // Verificar si la columna existe y es relevante
    if (!table.schema.columns.includes(columnName)) continue;
    if (!isRelevantColumn(columnName)) continue;

    for (const row of table.data) {
      const value = parseCellValue(row[columnName]);
      if (value !== null) {
        total += value;
        count++;
        if (!sourceTable) sourceTable = table.title;
      }
    }
  }

  if (count === 0) return null;

  return {
    operation: 'SUM',
    result: total,
    tableName: sourceTable,
    column: columnName,
    metadata: { count, average: total / count }
  };
}

/**
 * Encuentra el valor máximo de una columna
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna
 * @returns Valor máximo o null
 */
export function maxColumn(
  tables: StructuredTable[],
  columnName: string
): ComputationResult | null {
  let maxValue: number | null = null;
  let sourceTable = '';

  for (const table of tables) {
    if (!table.schema.columns.includes(columnName)) continue;
    if (!isRelevantColumn(columnName)) continue;

    for (const row of table.data) {
      const value = parseCellValue(row[columnName]);
      if (value !== null && (maxValue === null || value > maxValue)) {
        maxValue = value;
        sourceTable = table.title;
      }
    }
  }

  if (maxValue === null) return null;

  return {
    operation: 'MAX',
    result: maxValue,
    tableName: sourceTable,
    column: columnName
  };
}

/**
 * Encuentra el valor mínimo de una columna
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna
 * @returns Valor mínimo o null
 */
export function minColumn(
  tables: StructuredTable[],
  columnName: string
): ComputationResult | null {
  let minValue: number | null = null;
  let sourceTable = '';

  for (const table of tables) {
    if (!table.schema.columns.includes(columnName)) continue;
    if (!isRelevantColumn(columnName)) continue;

    for (const row of table.data) {
      const value = parseCellValue(row[columnName]);
      if (value !== null && (minValue === null || value < minValue)) {
        minValue = value;
        sourceTable = table.title;
      }
    }
  }

  if (minValue === null) return null;

  return {
    operation: 'MIN',
    result: minValue,
    tableName: sourceTable,
    column: columnName
  };
}

/**
 * Calcula el promedio de una columna
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna
 * @returns Promedio o null
 */
export function avgColumn(
  tables: StructuredTable[],
  columnName: string
): ComputationResult | null {
  let sum = 0;
  let count = 0;
  let sourceTable = '';

  for (const table of tables) {
    if (!table.schema.columns.includes(columnName)) continue;
    if (!isRelevantColumn(columnName)) continue;

    for (const row of table.data) {
      const value = parseCellValue(row[columnName]);
      if (value !== null) {
        sum += value;
        count++;
        if (!sourceTable) sourceTable = table.title;
      }
    }
  }

  if (count === 0) return null;

  return {
    operation: 'AVG',
    result: sum / count,
    tableName: sourceTable,
    column: columnName,
    metadata: { sum, count }
  };
}

/**
 * Cuenta el número de filas que cumplen una condición
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna
 * @param filters - Filtros opcionales
 * @returns Conteo de filas
 */
export function countRows(
  tables: StructuredTable[],
  columnName?: string,
  filters?: RowFilter[]
): ComputationResult | null {
  let count = 0;
  let sourceTable = '';

  for (const table of tables) {
    if (columnName && !table.schema.columns.includes(columnName)) continue;
    if (columnName && !isRelevantColumn(columnName)) continue;

    for (const row of table.data) {
      if (filters && filters.length > 0) {
        if (matchesFilters(row, filters)) {
          count++;
          if (!sourceTable) sourceTable = table.title;
        }
      } else {
        count++;
        if (!sourceTable) sourceTable = table.title;
      }
    }
  }

  if (count === 0) return null;

  return {
    operation: 'COUNT',
    result: count,
    tableName: sourceTable,
    column: columnName
  };
}

// ============================================================================
// OPERACIONES DE BÚSQUEDA Y COMPARACIÓN
// ============================================================================

/**
 * Encuentra la fila con el valor mínimo de una columna
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna a comparar
 * @returns Fila completa con el valor mínimo o null
 */
export function findMinRow(
  tables: StructuredTable[],
  columnName: string
): { table: StructuredTable; row: Record<string, any>; value: number } | null {
  let result: { table: StructuredTable; row: Record<string, any>; value: number } | null = null;

  for (const table of tables) {
    if (!table.schema.columns.includes(columnName)) continue;
    if (!isRelevantColumn(columnName)) continue;

    for (const row of table.data) {
      const value = parseCellValue(row[columnName]);
      if (value !== null) {
        if (result === null || value < result.value) {
          result = { table, row, value };
        }
      }
    }
  }

  return result;
}

/**
 * Encuentra la fila con el valor máximo de una columna
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna a comparar
 * @returns Fila completa con el valor máximo o null
 */
export function findMaxRow(
  tables: StructuredTable[],
  columnName: string
): { table: StructuredTable; row: Record<string, any>; value: number } | null {
  let result: { table: StructuredTable; row: Record<string, any>; value: number } | null = null;

  for (const table of tables) {
    if (!table.schema.columns.includes(columnName)) continue;
    if (!isRelevantColumn(columnName)) continue;

    for (const row of table.data) {
      const value = parseCellValue(row[columnName]);
      if (value !== null) {
        if (result === null || value > result.value) {
          result = { table, row, value };
        }
      }
    }
  }

  return result;
}

/**
 * Compara valores entre múltiples municipios/tablas
 * @param tables - Array de tablas estructuradas
 * @param columnName - Nombre de la columna a comparar
 * @param groupByColumn - Columna por la que agrupar (ej: "municipio")
 * @returns Array de resultados agrupados ordenados por valor
 */
export function compareAcrossGroups(
  tables: StructuredTable[],
  columnName: string,
  groupByColumn?: string
): AggregationResult[] {
  const groupMap = new Map<string, { sum: number; count: number }>();

  for (const table of tables) {
    if (!table.schema.columns.includes(columnName)) continue;

    // Determinar el nombre del grupo
    const groupKey = groupByColumn && table.schema.columns.includes(groupByColumn)
      ? String(groupByColumn)
      : table.title;

    for (const row of table.data) {
      const value = parseCellValue(row[columnName]);
      if (value !== null) {
        const current = groupMap.get(groupKey) || { sum: 0, count: 0 };
        current.sum += value;
        current.count++;
        groupMap.set(groupKey, current);
      }
    }
  }

  // Convertir a array y ordenar
  return Array.from(groupMap.entries())
    .map(([group, data]) => ({
      group,
      value: data.sum,
      count: data.count
    }))
    .sort((a, b) => b.value - a.value);
}

// ============================================================================
// OPERACIONES DE FILTRADO
// ============================================================================

/**
 * Verifica si una fila cumple con los filtros especificados
 */
function matchesFilters(row: Record<string, any>, filters: RowFilter[]): boolean {
  return filters.every(filter => {
    const cellValue = row[filter.column];
    if (cellValue === undefined || cellValue === null) return false;

    switch (filter.operator) {
      case 'equals':
        return String(cellValue).toLowerCase() === String(filter.value).toLowerCase();
      case 'contains':
        return String(cellValue).toLowerCase().includes(String(filter.value).toLowerCase());
      case 'gt':
        const cellValGt = parseCellValue(cellValue);
        const filterValGt = parseCellValue(filter.value);
        return cellValGt !== null && filterValGt !== null && cellValGt > filterValGt;
      case 'lt':
        const cellValLt = parseCellValue(cellValue);
        const filterValLt = parseCellValue(filter.value);
        return cellValLt !== null && filterValLt !== null && cellValLt < filterValLt;
      case 'gte':
        const cellValGte = parseCellValue(cellValue);
        const filterValGte = parseCellValue(filter.value);
        return cellValGte !== null && filterValGte !== null && cellValGte >= filterValGte;
      case 'lte':
        const cellValLte = parseCellValue(cellValue);
        const filterValLte = parseCellValue(filter.value);
        return cellValLte !== null && filterValLte !== null && cellValLte <= filterValLte;
      case 'between':
        const val = parseCellValue(cellValue);
        const min = parseCellValue(filter.value);
        const max = parseCellValue(filter.value2);
        return val !== null && min !== null && max !== null && val >= min && val <= max;
      default:
        return false;
    }
  });
}

/**
 * Filtra filas de tablas según condiciones
 * @param tables - Array de tablas estructuradas
 * @param filters - Array de filtros a aplicar
 * @returns Filas que cumplen los filtros
 */
export function filterRows(
  tables: StructuredTable[],
  filters: RowFilter[]
): Array<{ table: StructuredTable; row: Record<string, any> }> {
  const results: Array<{ table: StructuredTable; row: Record<string, any> }> = [];

  for (const table of tables) {
    for (const row of table.data) {
      if (matchesFilters(row, filters)) {
        results.push({ table, row });
      }
    }
  }

  return results;
}

/**
 * Filtra tablas que contienen keywords específicas
 * @param tables - Array de tablas estructuradas
 * @param keywords - Keywords a buscar en título, descripción o contexto
 * @returns Tablas filtradas
 */
export function filterTablesByKeywords(
  tables: StructuredTable[],
  keywords: string[]
): StructuredTable[] {
  const keywordLower = keywords.map(k => k.toLowerCase());

  return tables.filter(table => {
    const searchText = [
      table.title,
      table.description,
      table.context,
      ...table.schema.columns
    ].join(' ').toLowerCase();

    return keywordLower.some(kw => searchText.includes(kw));
  });
}

// ============================================================================
// OPERACIONES DE AGRUPACIÓN
// ============================================================================

/**
 * Agrupa filas por el valor de una columna y calcula agregaciones
 * @param tables - Array de tablas estructuradas
 * @param groupByColumn - Columna por la que agrupar
 * @param aggColumn - Columna a agregar (ej: "monto")
 * @param operation - Operación: 'sum', 'avg', 'count', 'min', 'max'
 * @returns Resultados agrupados
 */
export function groupByColumn(
  tables: StructuredTable[],
  groupByColumn: string,
  aggColumn: string,
  operation: 'sum' | 'avg' | 'count' | 'min' | 'max' = 'sum'
): AggregationResult[] {
  const groupMap = new Map<string, number[]>();

  for (const table of tables) {
    if (!table.schema.columns.includes(groupByColumn)) continue;
    if (!table.schema.columns.includes(aggColumn)) continue;
    if (!isRelevantColumn(aggColumn)) continue;

    for (const row of table.data) {
      const groupKey = String(row[groupByColumn] || 'Sin categoría');
      const aggValue = parseCellValue(row[aggColumn]);

      if (aggValue !== null) {
        const values = groupMap.get(groupKey) || [];
        values.push(aggValue);
        groupMap.set(groupKey, values);
      }
    }
  }

  // Calcular agregación por grupo
  return Array.from(groupMap.entries())
    .map(([group, values]) => {
      let value: number;
      switch (operation) {
        case 'sum':
          value = values.reduce((a, b) => a + b, 0);
          break;
        case 'avg':
          value = values.reduce((a, b) => a + b, 0) / values.length;
          break;
        case 'count':
          value = values.length;
          break;
        case 'min':
          value = Math.min(...values);
          break;
        case 'max':
          value = Math.max(...values);
          break;
      }
      return { group, value, count: values.length };
    })
    .sort((a, b) => b.value - a.value);
}

// ============================================================================
// BÚSQUEDA DE TABLAS RELEVANTES
// ============================================================================

/**
 * Encuentra tablas relevantes basándose en keywords de la query
 * @param tables - Array de tablas estructuradas
 * @param query - Query del usuario
 * @returns Tablas ordenadas por relevancia
 */
export function findRelevantTables(
  tables: StructuredTable[],
  query: string
): StructuredTable[] {
  const queryLower = query.toLowerCase();
  const terms = queryLower.split(/\s+/).filter(t => t.length > 3);

  if (terms.length === 0) return tables;

  // Mapeo de keywords comunes a términos de tablas
  const keywordMappings: Record<string, string[]> = {
    'tasa': ['tasa', 'tarifa', 'tributo', 'impuesto'],
    'vial': ['vial', 'vialidad', 'calles', 'rutas'],
    'salario': ['salario', 'sueldo', 'remuneración', 'honorarios'],
    'pago': ['pago', 'pagado', 'abono', 'cancelación'],
    'gasto': ['gasto', 'egreso', 'erogación', 'gastos'],
    'comercial': ['comercial', 'comercio', 'negocio'],
    'industrial': ['industrial', 'industria'],
    'profesional': ['profesional', 'profesión'],
  };

  const scoredTables = tables.map(table => {
    let score = 0;
    const searchableText = [
      table.title,
      table.description,
      table.context,
      ...table.schema.columns
    ].join(' ').toLowerCase();

    // Búsqueda directa de términos
    for (const term of terms) {
      if (searchableText.includes(term)) {
        score += 10;
      }
    }

    // Búsqueda por mapeo de keywords
    for (const [key, synonyms] of Object.entries(keywordMappings)) {
      if (queryLower.includes(key)) {
        for (const synonym of synonyms) {
          if (searchableText.includes(synonym)) {
            score += 5;
          }
        }
      }
    }

    return { table, score };
  });

  return scoredTables
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score)
    .map(({ table }) => table);
}

// ============================================================================
// FORMATEO DE RESULTADOS
// ============================================================================

/**
 * Formatea un resultado de cómputo como texto legible
 * @param result - Resultado de una operación
 * @returns String formateado para mostrar al usuario
 */
export function formatComputationResult(result: ComputationResult): string {
  const formattedValue = typeof result.result === 'number'
    ? formatArgentineNumber(result.result)
    : result.result;

  switch (result.operation) {
    case 'SUM':
      return `**Total:** ${formattedValue}${result.unit ? ' ' + result.unit : ''}`;
    case 'AVG':
      return `**Promedio:** ${formattedValue}${result.unit ? ' ' + result.unit : ''}`;
    case 'MIN':
      return `**Mínimo:** ${formattedValue}${result.unit ? ' ' + result.unit : ''}`;
    case 'MAX':
      return `**Máximo:** ${formattedValue}${result.unit ? ' ' + result.unit : ''}`;
    case 'COUNT':
      return `**Cantidad:** ${formattedValue}`;
    default:
      return String(formattedValue);
  }
}

/**
 * Formatea resultados agrupados como tabla Markdown
 * @param results - Array de resultados agrupados
 * @param label - Etiqueta para la columna de valor
 * @returns Tabla Markdown
 */
export function formatAggregationAsMarkdown(
  results: AggregationResult[],
  label: string = 'Valor'
): string {
  if (results.length === 0) return '*No se encontraron datos*';

  const lines: string[] = ['| Grupo | ' + label + ' | Cantidad |', '|---|---|---|'];

  for (const result of results) {
    const formattedValue = formatArgentineNumber(result.value);
    lines.push(`| ${result.group} | $${formattedValue} | ${result.count} |`);
  }

  return lines.join('\n');
}

/**
 * Formatea filas como tabla Markdown
 * @param rows - Filas a formatear
 * @param columns - Columnas a incluir (todas si no se especifica)
 * @returns Tabla Markdown
 */
export function formatRowsAsMarkdown(
  rows: Array<{ table: StructuredTable; row: Record<string, any> }>,
  columns?: string[]
): string {
  if (rows.length === 0) return '*No se encontraron resultados*';

  // Determinar columnas a mostrar
  const cols = columns || Object.keys(rows[0].row);

  const header = '| ' + cols.join(' | ') + ' |';
  const separator = '| ' + cols.map(() => '---').join(' | ') + ' |';

  const dataRows = rows.map(({ row }) => {
    const values = cols.map(col => {
      const val = row[col];
      return typeof val === 'number' ? formatArgentineNumber(val) : String(val ?? '');
    });
    return '| ' + values.join(' | ') + ' |';
  });

  return [header, separator, ...dataRows].join('\n');
}

// ============================================================================
// UTILIDADES
// ============================================================================

/**
 * Extrae estadísticas de las tablas para mostrar en el contexto
 * @param tables - Array de tablas estructuradas
 * @returns Resumen de estadísticas
 */
export function getTablesSummary(tables: StructuredTable[]): string {
  if (tables.length === 0) return '*No hay tablas disponibles*';

  const lines: string[] = ['## 📊 Resumen de Tablas Disponibles', ''];

  for (const table of tables) {
    lines.push(`### ${table.title}`);
    if (table.description) {
      lines.push(`*${table.description}*`);
    }
    lines.push(`- **Filas:** ${table.stats.row_count}`);
    lines.push(`- **Columnas:** ${table.schema.columns.join(', ')}`);

    // Mostrar columnas numéricas con estadísticas
    const numericCols = Object.keys(table.stats.numeric_stats);
    if (numericCols.length > 0) {
      lines.push('- **Columnas numéricas:**');
      for (const col of numericCols) {
        const stats = table.stats.numeric_stats[col];
        lines.push(`  - ${col}: suma=${formatArgentineNumber(stats.sum)}, ` +
                   `máx=${formatArgentineNumber(stats.max)}, ` +
                   `mín=${formatArgentineNumber(stats.min)}, ` +
                   `prom=${formatArgentineNumber(stats.avg)}`);
      }
    }
    lines.push('');
  }

  return lines.join('\n');
}

/**
 * Busca una columna por nombre o alias en las tablas
 * @param tables - Array de tablas estructuradas
 * @param searchTerm - Término de búsqueda
 * @returns Array de {table, column} encontrados
 */
export function findColumnByName(
  tables: StructuredTable[],
  searchTerm: string
): Array<{ table: StructuredTable; column: string }> {
  const results: Array<{ table: StructuredTable; column: string }> = [];
  const searchLower = searchTerm.toLowerCase();

  // Mapeo de alias comunes
  const aliases: Record<string, string[]> = {
    'monto': ['monto', 'importe', 'total', 'suma', 'valor', 'cantidad', 'haberes'],
    'tasa': ['tasa', 'tarifa', 'valor', 'importe'],
    'salario': ['salario', 'sueldo', 'remuneracion', 'remuneración', 'honorarios', 'haberes'],
    'vial': ['vial', 'vialidad', 'calle'],
  };

  const searchTerms = [searchLower, ...(aliases[searchLower] || [])];

  for (const table of tables) {
    for (const column of table.schema.columns) {
      const columnLower = column.toLowerCase();
      if (searchTerms.some(term => columnLower.includes(term) || term.includes(columnLower))) {
        results.push({ table, column });
        break; // Una columna por tabla es suficiente
      }
    }
  }

  return results;
}
