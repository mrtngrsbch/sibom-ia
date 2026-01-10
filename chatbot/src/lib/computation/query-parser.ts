/**
 * query-parser.ts
 *
 * Parser de queries computacionales para el motor de cómputo tabular.
 * Interpreta preguntas en lenguaje natural y determina qué operaciones ejecutar.
 *
 * @version 1.0.0
 * @created 2026-01-09
 * @author Kilo Code
 */

import type { StructuredTable } from '@/lib/types';
import type { RowFilter } from './table-engine';

/**
 * Operación computacional a ejecutar
 */
export type ComputationOperation =
  | 'sum'
  | 'avg'
  | 'min'
  | 'max'
  | 'count'
  | 'find_min_row'
  | 'find_max_row'
  | 'filter'
  | 'group_by'
  | 'compare';

/**
 * Query computacional parseada
 */
export interface ParsedComputationalQuery {
  operation: ComputationOperation;
  targetColumn?: string;
  groupByColumn?: string;
  filters?: RowFilter[];
  keywords: string[];
  aggregateType?: 'sum' | 'avg' | 'count' | 'min' | 'max';
  limit?: number;
  sortBy?: 'asc' | 'desc';
}

/**
 * Resultado de ejecutar una query computacional
 */
export interface ComputationalQueryResult {
  success: boolean;
  operation: string;
  answer: string;
  markdown?: string;
  metadata?: Record<string, any>;
  error?: string;
}

// ============================================================================
// EXTRACCIÓN DE ENTIDADES
// ============================================================================

/**
 * Extrae el nombre del municipio de una query
 */
export function extractMunicipality(query: string): string | null {
  const lowerQuery = query.toLowerCase();

  // Lista de municipios de Buenos Aires (completa según DB)
  const municipalities = [
    'carlos tejedor',
    'bahía blanca',
    'bahia blanca',
    'pilar',
    'alberti',
    'trenque lauquen',
    'daireaux',
    'pellegrini',
    'tres lomas',
    'guaminí',
    'la plata',
    'mar del plata',
    'mendoza',
    'córdoba',
    'rosario',
    'san miguel',
    'quilmes',
    'lanús',
    'morón',
    'san isidro',
    'vicente lópez',
    'lavallol',
    'burzaco',
    'longchamps',
    'temperley',
    'banfield',
    'olivos',
    'martín',
    'martin',
    'santa teresita',
    'mar del tuyú',
    'san clemente',
    'pinamar',
    'villa gesell',
    'necochea',
    'miramar',
  ];

  for (const municipio of municipalities) {
    if (lowerQuery.includes(municipio)) {
      // Capitalizar correctamente
      return municipio.split(' ').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      ).join(' ');
    }
  }

  return null;
}

/**
 * Extrae el año de una query
 */
export function extractYear(query: string): number | null {
  const yearMatch = query.match(/\b(20\d{2}|19\d{2})\b/);
  return yearMatch ? parseInt(yearMatch[1], 10) : null;
}

/**
 * Extrae un número de ordenanza/decreto de una query
 */
export function extractOrdinanceNumber(query: string): string | null {
  const match = query.match(/n?º?\s*(\d{1,5})/i);
  return match ? match[1] : null;
}

/**
 * Extrae keywords relevantes para búsqueda de tablas
 */
export function extractKeywords(query: string): string[] {
  const keywords: string[] = [];
  const lowerQuery = query.toLowerCase();

  // Keywords de dominio específico
  const domainKeywords = [
    'tasa', 'tasas', 'tarifa', 'tarifas', 'tributo', 'tributos',
    'vial', 'vialidad', 'calle', 'calles', 'ruta', 'rutas',
    'salario', 'salarios', 'sueldo', 'sueldos', 'remuneracion', 'remuneración',
    'haberes', 'honorarios', 'gasto', 'gastos', 'egreso', 'egresos',
    'comercial', 'comercio', 'industrial', 'industria', 'profesional',
    'seguridad', 'higiene', 'inspeccion', 'inspección',
    'patente', 'licencia', 'habilitacion', 'habilitación',
    'obra', 'obras', 'inversion', 'inversión', 'inversiones',
    'pago', 'pagos', 'cobro', 'recaudacion', 'recaudación',
    'presupuesto', 'finanzas', 'rentas',
  ];

  for (const keyword of domainKeywords) {
    if (lowerQuery.includes(keyword)) {
      // Agregar el lema (singular) para mejor matching
      const lemma = keyword.replace(/es$/, '').replace(/s$/, '');
      if (!keywords.includes(lemma)) {
        keywords.push(lemma);
      }
    }
  }

  // Extraer categorías específicas
  const categoryMatch = query.match(/(?:categor[íi]a|tipo)\s+(?:de\s+)?([^,\s]+(?:\s+[^,\s]+)?)/i);
  if (categoryMatch) {
    keywords.push(categoryMatch[1].toLowerCase());
  }

  return keywords.length > 0 ? keywords : ['tasa']; // Default a tasa si no hay keywords
}

// ============================================================================
// PARSEO DE OPERACIONES
// ============================================================================

/**
 * Determina la operación computacional basándose en la query
 */
function determineOperation(query: string): ComputationOperation {
  const lowerQuery = query.toLowerCase();

  // Operaciones de mínimo/máximo con entidad completa
  if (/menor.*tasa|mínima.*tasa|menor.*tarifa|mínima.*tarifa/.test(lowerQuery)) {
    return 'find_min_row';
  }
  if (/mayor.*tasa|máxima.*tasa|mayor.*tarifa|máxima.*tarifa/.test(lowerQuery)) {
    return 'find_max_row';
  }

  // Comparaciones entre municipios
  if (/comparar|tabla comparativa|entre.*municipios|diferencia|municipio.*menor|municipio.*mayor/.test(lowerQuery)) {
    return 'compare';
  }

  // Agrupaciones
  if (/por.*categor[íi]a|por.*tipo|agrupar|separar/.test(lowerQuery)) {
    return 'group_by';
  }

  // Sumas/totales
  if (/suma|sumar|total|totales|totalizar|gastos.*en|montos?/.test(lowerQuery)) {
    return 'sum';
  }

  // Promedios
  if (/promedio|media|average/.test(lowerQuery)) {
    return 'avg';
  }

  // Mínimos
  if (/m[ií]nimo|m[ií]nima|menor/.test(lowerQuery)) {
    return 'min';
  }

  // Máximos
  if (/m[aá]ximo|m[aá]xima|mayor/.test(lowerQuery)) {
    return 'max';
  }

  // Conteos
  if (/cu[aá]ntos|cu[aá]ntas|cuenta|cantidad|n[uú]mero de/.test(lowerQuery)) {
    return 'count';
  }

  // Filtros (qué tasas paga X)
  if (/qu[ée].*paga|cuales?|listar|mostrar|ver/.test(lowerQuery)) {
    return 'filter';
  }

  // Default: filtrado
  return 'filter';
}

/**
 * Determina la columna objetivo basándose en la query
 */
function determineTargetColumn(query: string, tables: StructuredTable[]): string | null {
  const lowerQuery = query.toLowerCase();

  // Mapeo de términos a columnas probables
  const columnMappings: Record<string, string[]> = {
    'tasa': ['tasa', 'tarifa', 'importe', 'monto', 'valor'],
    'vial': ['vial', 'vialidad', 'calle'],
    'salario': ['salario', 'sueldo', 'remuneracion', 'haberes', 'honorarios'],
    'gasto': ['gasto', 'egreso', 'monto', 'importe'],
    'pago': ['pago', 'abono', 'cancelado', 'pagado'],
  };

  // Buscar términos de la query en los mappings
  for (const [term, possibleColumns] of Object.entries(columnMappings)) {
    if (lowerQuery.includes(term)) {
      // Verificar si alguna de estas columnas existe en las tablas
      for (const table of tables) {
        for (const col of possibleColumns) {
          if (table.schema.columns.some(c => c.toLowerCase().includes(col))) {
            // Devolver la columna real encontrada
            const realColumn = table.schema.columns.find(c =>
              c.toLowerCase().includes(col)
            );
            return realColumn || null;
          }
        }
      }
    }
  }

  // Si no se encontró por mapping, buscar columna numérica más común
  const columnCounts = new Map<string, number>();
  for (const table of tables) {
    for (const col of table.schema.columns) {
      const count = columnCounts.get(col) || 0;
      columnCounts.set(col, count + 1);
    }
  }

  // Devolver la columna más frecuente que parezca numérica
  const sortedColumns = Array.from(columnCounts.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([col]) => col);

  for (const col of sortedColumns) {
    const lower = col.toLowerCase();
    if (/monto|importe|valor|tasa|tarifa|total|suma/.test(lower)) {
      return col;
    }
  }

  return sortedColumns[0] || null;
}

/**
 * Extrae filtros de la query (ej: "local comercial" → category = "Comercial")
 */
function extractFilters(query: string, tables: StructuredTable[]): RowFilter[] {
  const filters: RowFilter[] = [];
  const lowerQuery = query.toLowerCase();

  // Buscar columna de categoría
  let categoryColumn: string | null = null;
  for (const table of tables) {
    const col = table.schema.columns.find(c =>
      /categor[íi]a|tipo|clase/.test(c.toLowerCase())
    );
    if (col) {
      categoryColumn = col;
      break;
    }
  }

  if (categoryColumn) {
    // Extraer valor de categoría de la query
    const categoryMatch = query.match(/(?:local|categoria|categoría|tipo)\s+([^,\s]+)/i);
    if (categoryMatch) {
      filters.push({
        column: categoryColumn,
        operator: 'contains',
        value: categoryMatch[1]
      });
    }
  }

  // Filtro de municipio si está en una columna
  const municipio = extractMunicipality(query);
  if (municipio) {
    let municipioColumn: string | null = null;
    for (const table of tables) {
      const col = table.schema.columns.find(c =>
        /municipio|partido|localidad/.test(c.toLowerCase())
      );
      if (col) {
        municipioColumn = col;
        break;
      }
    }

    if (municipioColumn) {
      filters.push({
        column: municipioColumn,
        operator: 'contains',
        value: municipio
      });
    }
  }

  return filters;
}

// ============================================================================
// FUNCIÓN PRINCIPAL DE PARSEO
// ============================================================================

/**
 * Parsea una query computacional en lenguaje natural
 * @param query - Query del usuario
 * @param tables - Tablas disponibles (para inferir columnas)
 * @returns Query parseada con operación y parámetros
 */
export function parseComputationalQuery(
  query: string,
  tables: StructuredTable[]
): ParsedComputationalQuery | null {
  if (tables.length === 0) {
    return null;
  }

  const operation = determineOperation(query);
  const targetColumn = determineTargetColumn(query, tables);
  const keywords = extractKeywords(query);
  const filters = extractFilters(query, tables);

  return {
    operation,
    targetColumn: targetColumn || undefined,
    groupByColumn: undefined, // Se puede inferir de la query si es necesario
    filters: filters.length > 0 ? filters : undefined,
    keywords,
  };
}

/**
 * Verifica si una query es computacional (requiere operaciones sobre datos tabulares)
 */
export function isComputationalQuery(query: string): boolean {
  const computationalPatterns = [
    // Operaciones de agregación
    /suma|sumar|total|totalizar/i,
    /promedio|media|average/i,

    // Operaciones de comparación
    /cu[aá]l.*m[aá]s.*alto|mayor|m[aá]ximo/i,
    /cu[aá]l.*m[aá]s.*bajo|menor|m[ií]nimo/i,
    /comparar|diferencia|vs|versus/i,
    /entre.*y/i, // "diferencia entre X y Y"

    // Operaciones de conteo
    /cu[aá]ntos|cu[aá]ntas|cantidad|n[uú]mero de/i,

    // Búsqueda de valores específicos en tablas
    /monto|valor|precio|tasa|tarifa/i,
    /categor[ií]a|tipo.*de/i,

    // Operaciones de ordenamiento
    /ordenar|listar.*por|ranking/i,

    // Operaciones de filtrado sobre datos numéricos
    /mayor.*que|menor.*que|igual.*a/i,
    /entre.*\d+.*y.*\d+/i, // "entre 1000 y 5000"
  ];

  return computationalPatterns.some(pattern => pattern.test(query));
}

/**
 * Genera un texto explicativo de la operación realizada
 */
export function explainOperation(operation: ComputationOperation): string {
  const explanations: Record<ComputationOperation, string> = {
    'sum': 'Se sumaron todos los valores de la columna',
    'avg': 'Se calculó el promedio de los valores de la columna',
    'min': 'Se encontró el valor mínimo de la columna',
    'max': 'Se encontró el valor máximo de la columna',
    'count': 'Se contaron las filas que cumplen con los criterios',
    'find_min_row': 'Se encontró el registro con el valor mínimo',
    'find_max_row': 'Se encontró el registro con el valor máximo',
    'filter': 'Se filtraron los registros según los criterios especificados',
    'group_by': 'Se agruparon y agregaron los valores por categoría',
    'compare': 'Se compararon los valores entre diferentes grupos',
  };

  return explanations[operation] || 'Se realizó una operación sobre los datos';
}
