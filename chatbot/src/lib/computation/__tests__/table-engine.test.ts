/**
 * table-engine.test.ts
 *
 * Tests para el motor de cómputo tabular.
 */

import { describe, it, expect } from 'vitest';
import type { StructuredTable } from '@/lib/types';
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
  formatRowsAsMarkdown,
  formatAggregationAsMarkdown,
  findColumnByName
} from '../table-engine';
import type { RowFilter } from '../table-engine';

// Mock de tablas para testing
const mockTables: StructuredTable[] = [
  {
    id: 'table-1',
    title: 'Tasas Viales',
    context: 'Boletín 82 - Carlos Tejedor',
    description: 'Aranceles de tasas viales por categoría',
    position: 1,
    schema: {
      columns: ['Categoria', 'Tasa', 'Unidad'],
      types: ['string', 'number', 'string']
    },
    data: [
      { Categoria: 'Comercial', Tasa: 1500, Unidad: 'Mensual' },
      { Categoria: 'Industrial', Tasa: 2500, Unidad: 'Mensual' },
      { Categoria: 'Profesional', Tasa: 800, Unidad: 'Mensual' },
      { Categoria: 'Residencial', Tasa: 500, Unidad: 'Mensual' }
    ],
    stats: {
      row_count: 4,
      numeric_stats: {
        Tasa: { sum: 5300, max: 2500, min: 500, avg: 1325, count: 4 }
      }
    },
    markdown: '| Categoria | Tasa | Unidad |\n|---|---|---|\n| Comercial | 1500 | Mensual |',
    extraction_errors: []
  },
  {
    id: 'table-2',
    title: 'Gastos en Salarios',
    context: 'Boletín 82 - Carlos Tejedor',
    description: 'Desglose de gastos en salarios por área',
    position: 2,
    schema: {
      columns: ['Area', 'Monto', 'Empleados'],
      types: ['string', 'number', 'number']
    },
    data: [
      { Area: 'Administración', Monto: 1500000, Empleados: 10 },
      { Area: 'Obras Públicas', Monto: 3200000, Empleados: 25 },
      { Area: 'Salud', Monto: 2800000, Empleados: 20 },
      { Area: 'Educación', Monto: 4100000, Empleados: 35 }
    ],
    stats: {
      row_count: 4,
      numeric_stats: {
        Monto: { sum: 11600000, max: 4100000, min: 1500000, avg: 2900000, count: 4 },
        Empleados: { sum: 90, max: 35, min: 10, avg: 22.5, count: 4 }
      }
    },
    markdown: '| Area | Monto | Empleados |\n|---|---|---|\n| Administración | 1500000 | 10 |',
    extraction_errors: []
  }
];

describe('table-engine', () => {
  describe('sumColumn', () => {
    it('debería sumar correctamente una columna numérica', () => {
      const result = sumColumn(mockTables, 'Tasa');
      expect(result).toBeDefined();
      expect(result?.operation).toBe('SUM');
      expect(result?.result).toBe(5300);
      expect(result?.column).toBe('Tasa');
    });

    it('debería devolver null para columna inexistente', () => {
      const result = sumColumn(mockTables, 'ColumnaInexistente');
      expect(result).toBeNull();
    });
  });

  describe('avgColumn', () => {
    it('debería calcular el promedio correctamente', () => {
      const result = avgColumn(mockTables, 'Tasa');
      expect(result).toBeDefined();
      expect(result?.operation).toBe('AVG');
      expect(result?.result).toBe(1325);
    });
  });

  describe('minColumn', () => {
    it('debería encontrar el valor mínimo', () => {
      const result = minColumn(mockTables, 'Tasa');
      expect(result).toBeDefined();
      expect(result?.operation).toBe('MIN');
      expect(result?.result).toBe(500);
    });
  });

  describe('maxColumn', () => {
    it('debería encontrar el valor máximo', () => {
      const result = maxColumn(mockTables, 'Tasa');
      expect(result).toBeDefined();
      expect(result?.operation).toBe('MAX');
      expect(result?.result).toBe(2500);
    });
  });

  describe('countRows', () => {
    it('debería contar todas las filas sin filtros', () => {
      const result = countRows(mockTables, 'Tasa');
      expect(result).toBeDefined();
      expect(result?.operation).toBe('COUNT');
      expect(result?.result).toBe(4);
    });
  });

  describe('findMinRow', () => {
    it('debería encontrar la fila con valor mínimo', () => {
      const result = findMinRow(mockTables, 'Tasa');
      expect(result).toBeDefined();
      expect(result?.value).toBe(500);
      expect(result?.row.Categoria).toBe('Residencial');
    });
  });

  describe('findMaxRow', () => {
    it('debería encontrar la fila con valor máximo', () => {
      const result = findMaxRow(mockTables, 'Tasa');
      expect(result).toBeDefined();
      expect(result?.value).toBe(2500);
      expect(result?.row.Categoria).toBe('Industrial');
    });

    it('debería encontrar el monto máximo de salarios', () => {
      const result = findMaxRow(mockTables, 'Monto');
      expect(result).toBeDefined();
      expect(result?.value).toBe(4100000);
      expect(result?.row.Area).toBe('Educación');
    });
  });

  describe('filterRows', () => {
    it('debería filtrar por operador equals', () => {
      const filters: RowFilter[] = [
        { column: 'Categoria', operator: 'equals', value: 'Comercial' }
      ];
      const result = filterRows(mockTables, filters);
      expect(result).toHaveLength(1);
      expect(result[0].row.Categoria).toBe('Comercial');
    });

    it('debería filtrar por operador contains', () => {
      const filters: RowFilter[] = [
        { column: 'Area', operator: 'contains', value: 'Admin' }
      ];
      const result = filterRows(mockTables, filters);
      expect(result).toHaveLength(1);
      expect(result[0].row.Area).toBe('Administración');
    });

    it('debería filtrar por operador gt (greater than)', () => {
      const filters: RowFilter[] = [
        { column: 'Tasa', operator: 'gt', value: '1000' }
      ];
      const result = filterRows(mockTables, filters);
      expect(result.length).toBeGreaterThan(0);
      // Comercial (1500) e Industrial (2500)
      expect(result.length).toBe(2);
    });
  });

  describe('groupByColumn', () => {
    it('debería agrupar y sumar valores', () => {
      const result = groupByColumn(mockTables, 'Categoria', 'Tasa', 'sum');
      expect(result).toHaveLength(4);
      expect(result[0].group).toBe('Industrial'); // Ordenado descendente
      expect(result[0].value).toBe(2500);
    });

    it('debería agrupar áreas con montos', () => {
      const result = groupByColumn(mockTables, 'Area', 'Monto', 'sum');
      expect(result).toHaveLength(4);
      // Educación debería ser la máxima
      const educacion = result.find(r => r.group === 'Educación');
      expect(educacion?.value).toBe(4100000);
    });
  });

  describe('formatRowsAsMarkdown', () => {
    it('debería formatear filas como tabla Markdown', () => {
      const rows = [{ table: mockTables[0], row: mockTables[0].data[0] }];
      const result = formatRowsAsMarkdown(rows);
      expect(result).toContain('| Categoria | Tasa | Unidad |');
      expect(result).toContain('| Comercial | 1.500 | Mensual |');
    });
  });

  describe('formatAggregationAsMarkdown', () => {
    it('debería formatear agregaciones como tabla Markdown', () => {
      const result = formatAggregationAsMarkdown([
        { group: 'Industrial', value: 2500, count: 1 },
        { group: 'Comercial', value: 1500, count: 1 }
      ], 'Tasa');
      expect(result).toContain('| Grupo | Tasa | Cantidad |');
      expect(result).toContain('| Industrial |');
      expect(result).toContain('| Comercial |');
    });
  });

  describe('findColumnByName', () => {
    it('debería encontrar columnas por nombre', () => {
      const result = findColumnByName(mockTables, 'tasa');
      expect(result.length).toBeGreaterThan(0);
      expect(result[0].column).toBe('Tasa');
    });

    it('debería encontrar columnas por alias', () => {
      const result = findColumnByName(mockTables, 'monto');
      expect(result.length).toBeGreaterThan(0);
      expect(result[0].column).toBe('Monto');
    });
  });
});
