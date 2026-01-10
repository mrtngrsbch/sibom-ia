/**
 * computation/index.ts
 *
 * Punto de entrada unificado para el módulo de cómputo tabular.
 * Exporta todas las funcionalidades del motor de cómputo.
 */

// Exportar tipos
export type {
  ComputationResult,
  AggregationResult,
  RowFilter
} from './table-engine';

export type {
  ComputationOperation,
  ParsedComputationalQuery,
  ComputationalQueryResult
} from './query-parser';

// Exportar funciones del motor de cómputo
export {
  sumColumn,
  maxColumn,
  minColumn,
  avgColumn,
  countRows,
  findMinRow,
  findMaxRow,
  compareAcrossGroups,
  filterRows,
  filterTablesByKeywords,
  groupByColumn,
  findRelevantTables,
  formatComputationResult,
  formatAggregationAsMarkdown,
  formatRowsAsMarkdown,
  getTablesSummary,
  findColumnByName
} from './table-engine';

// Exportar funciones del parser
export {
  extractMunicipality,
  extractYear,
  extractOrdinanceNumber,
  extractKeywords,
  parseComputationalQuery,
  isComputationalQuery,
  explainOperation
} from './query-parser';

// Exportar función principal de ejecución
export { executeComputationalQuery } from './executor';
