/**
 * Tests para table-formatter.ts
 * 
 * Valida el formateo de tablas estructuradas para el LLM.
 */

import { describe, it, expect } from 'vitest';
import {
  formatTableForLLM,
  formatTablesForLLM,
  filterRelevantTables,
} from '../table-formatter';
import type { StructuredTable } from '@/lib/types';

describe('Table Formatter', () => {
  const mockTable: StructuredTable = {
    id: 'TABLA_1',
    title: 'Escala de Tasas Municipales 2026',
    context: 'Artículo 2: Las tasas se aplicarán según la siguiente escala:',
    description: 'Tabla de tasas municipales con montos por categoría',
    position: 247,
    schema: {
      columns: ['categoria', 'descripcion', 'monto_pesos'],
      types: ['string', 'string', 'number'],
    },
    data: [
      { categoria: 'A', descripcion: 'Comercio menor', monto_pesos: 1500 },
      { categoria: 'B', descripcion: 'Comercio mayor', monto_pesos: 3000 },
    ],
    stats: {
      row_count: 2,
      numeric_stats: {
        monto_pesos: {
          sum: 4500,
          max: 3000,
          min: 1500,
          avg: 2250,
          count: 2,
        },
      },
    },
    markdown: '| Categoría | Descripción | Monto ($) |\n|---|---|---|\n| A | Comercio menor | 1.500 |\n| B | Comercio mayor | 3.000 |',
    extraction_errors: [],
  };

  describe('formatTableForLLM', () => {
    it('should format table with title and context', () => {
      const formatted = formatTableForLLM(mockTable);

      expect(formatted).toContain('### Escala de Tasas Municipales 2026');
      expect(formatted).toContain('**Contexto:** Artículo 2');
      expect(formatted).toContain('**Descripción:** Tabla de tasas municipales');
    });

    it('should include markdown table', () => {
      const formatted = formatTableForLLM(mockTable);

      expect(formatted).toContain('**Datos:**');
      expect(formatted).toContain('| Categoría | Descripción | Monto ($) |');
    });

    it('should include statistics for numeric columns', () => {
      const formatted = formatTableForLLM(mockTable);

      expect(formatted).toContain('**Estadísticas:**');
      expect(formatted).toContain('- **monto_pesos:**');
      expect(formatted).toContain('Total: 4.500');
      expect(formatted).toContain('Máximo: 3.000');
      expect(formatted).toContain('Mínimo: 1.500');
      expect(formatted).toContain('Promedio: 2.250');
    });

    it('should include row count and column names', () => {
      const formatted = formatTableForLLM(mockTable);

      expect(formatted).toContain('**Total de filas:** 2');
      expect(formatted).toContain('**Columnas:** categoria, descripcion, monto_pesos');
    });

    it('should include extraction errors if present', () => {
      const tableWithErrors: StructuredTable = {
        ...mockTable,
        extraction_errors: ['Error parseando valor numérico en fila 3'],
      };

      const formatted = formatTableForLLM(tableWithErrors);

      expect(formatted).toContain('**⚠️ Advertencias de extracción:**');
      expect(formatted).toContain('- Error parseando valor numérico en fila 3');
    });

    it('should handle table without numeric columns', () => {
      const textOnlyTable: StructuredTable = {
        ...mockTable,
        schema: {
          columns: ['nombre', 'descripcion'],
          types: ['string', 'string'],
        },
        stats: {
          row_count: 2,
          numeric_stats: {}, // Sin estadísticas numéricas
        },
      };

      const formatted = formatTableForLLM(textOnlyTable);

      expect(formatted).not.toContain('**Estadísticas:**');
      expect(formatted).toContain('**Total de filas:** 2');
    });
  });

  describe('formatTablesForLLM', () => {
    it('should format multiple tables with separators', () => {
      const table2: StructuredTable = {
        ...mockTable,
        id: 'TABLA_2',
        title: 'Otra Tabla',
      };

      const formatted = formatTablesForLLM([mockTable, table2]);

      expect(formatted).toContain('## 📊 DATOS TABULARES ESTRUCTURADOS');
      expect(formatted).toContain('### Escala de Tasas Municipales 2026');
      expect(formatted).toContain('### Otra Tabla');
      expect(formatted).toContain('---'); // Separador entre tablas
    });

    it('should return empty string for empty array', () => {
      const formatted = formatTablesForLLM([]);
      expect(formatted).toBe('');
    });

    it('should include instructions for LLM', () => {
      const formatted = formatTablesForLLM([mockTable]);

      expect(formatted).toContain('Los siguientes datos provienen de tablas');
      expect(formatted).toContain('Puedes realizar cálculos, comparaciones y agregaciones');
    });
  });

  describe('filterRelevantTables', () => {
    const tables: StructuredTable[] = [
      {
        ...mockTable,
        id: 'TABLA_1',
        title: 'Escala de Tasas Municipales',
        description: 'Tasas para comercios',
      },
      {
        ...mockTable,
        id: 'TABLA_2',
        title: 'Horarios de Atención',
        description: 'Horarios de oficinas municipales',
        schema: {
          columns: ['oficina', 'horario'],
          types: ['string', 'string'],
        },
      },
      {
        ...mockTable,
        id: 'TABLA_3',
        title: 'Tasas de Habilitación',
        description: 'Montos de habilitación comercial',
        schema: {
          columns: ['tipo', 'monto'],
          types: ['string', 'number'],
        },
      },
    ];

    it('should filter tables by title match', () => {
      const query = 'tasas municipales';
      const filtered = filterRelevantTables(tables, query);

      expect(filtered.length).toBeGreaterThan(0);
      expect(filtered[0].title).toContain('Tasas');
    });

    it('should filter tables by description match', () => {
      const query = 'comercios';
      const filtered = filterRelevantTables(tables, query);

      expect(filtered.length).toBeGreaterThan(0);
      const titles = filtered.map(t => t.title);
      expect(titles).toContain('Escala de Tasas Municipales');
    });

    it('should filter tables by column name match', () => {
      const query = 'monto';
      const filtered = filterRelevantTables(tables, query);

      expect(filtered.length).toBeGreaterThan(0);
      // Debería incluir tablas que tienen columna "monto"
      const hasMontoColumn = filtered.some(t => 
        t.schema.columns.includes('monto') || t.schema.columns.includes('monto_pesos')
      );
      expect(hasMontoColumn).toBe(true);
    });

    it('should return all tables if query has no valid terms', () => {
      const query = 'a b'; // Términos muy cortos (< 3 chars)
      const filtered = filterRelevantTables(tables, query);

      expect(filtered.length).toBe(tables.length);
    });

    it('should return empty array if no tables match', () => {
      const query = 'palabra inexistente xyz';
      const filtered = filterRelevantTables(tables, query);

      expect(filtered.length).toBe(0);
    });

    it('should sort tables by relevance score', () => {
      const query = 'tasas comercio';
      const filtered = filterRelevantTables(tables, query);

      // La primera tabla debería tener mayor score (match en título Y descripción)
      expect(filtered[0].title).toContain('Tasas');
      expect(filtered[0].description).toContain('comercios');
    });
  });
});
