/**
 * query-parser.test.ts
 *
 * Tests para el parser de queries computacionales.
 */

import { describe, it, expect } from 'vitest';
import {
  extractMunicipality,
  extractYear,
  extractKeywords,
  parseComputationalQuery,
  isComputationalQuery
} from '../query-parser';
import type { StructuredTable } from '@/lib/types';

const mockTable: StructuredTable = {
  id: 'test-table',
  title: 'Tasas Viales',
  context: 'Boletín 82',
  description: 'Aranceles de tasas viales',
  position: 1,
  schema: {
    columns: ['Categoria', 'Tasa', 'Unidad'],
    types: ['string', 'number', 'string']
  },
  data: [],
  stats: { row_count: 0, numeric_stats: {} },
  markdown: '',
  extraction_errors: []
};

describe('query-parser', () => {
  describe('extractMunicipality', () => {
    it('debería extraer "Carlos Tejedor"', () => {
      expect(extractMunicipality('tasas en Carlos Tejedor')).toBe('Carlos Tejedor');
    });

    it('debería extraer "Bahía Blanca" con y sin tilde', () => {
      expect(extractMunicipality('Bahía Blanca tasas')).toBe('Bahía Blanca');
      expect(extractMunicipality('Bahia Blanca tasas')).toBe('Bahia Blanca');
    });

    it('debería extraer "Pilar"', () => {
      expect(extractMunicipality('ordenanzas de Pilar')).toBe('Pilar');
    });

    it('debería devolver null si no hay municipio', () => {
      expect(extractMunicipality('cuales son las tasas')).toBeNull();
    });
  });

  describe('extractYear', () => {
    it('debería extraer año 2025', () => {
      expect(extractYear('ordenanzas de 2025')).toBe(2025);
    });

    it('debería extraer año 2024', () => {
      expect(extractYear('en 2024 se aprobaron')).toBe(2024);
    });

    it('debería devolver null si no hay año', () => {
      expect(extractYear('ordenanzas recientes')).toBeNull();
    });
  });

  describe('extractKeywords', () => {
    it('debería extraer keyword "tasa"', () => {
      const result = extractKeywords('cuales son las tasas viales');
      expect(result).toContain('tasa');
    });

    it('debería extraer keyword "salario"', () => {
      const result = extractKeywords('gastos en salarios');
      expect(result).toContain('salario');
    });

    it('debería extraer keyword "vial"', () => {
      const result = extractKeywords('tasas viales');
      expect(result).toContain('vial');
    });
  });

  describe('isComputationalQuery', () => {
    it('debería detectar query de suma', () => {
      expect(isComputationalQuery('suma de todas las tasas')).toBe(true);
    });

    it('debería detectar query de máximo', () => {
      expect(isComputationalQuery('cuál es la tasa máxima')).toBe(true);
    });

    it('debería detectar query de mínimo', () => {
      expect(isComputationalQuery('municipio con menor tasa')).toBe(true);
    });

    it('debería detectar query de comparación', () => {
      expect(isComputationalQuery('comparar tasas entre municipios')).toBe(true);
    });

    it('debería detectar query de conteo', () => {
      expect(isComputationalQuery('cuántas tasas hay')).toBe(true);
    });

    it('no debería detectar como computacional si es simple', () => {
      expect(isComputationalQuery('qué dice la ordenanza 123')).toBe(false);
    });
  });

  describe('parseComputationalQuery', () => {
    it('debería parsear query de suma', () => {
      const result = parseComputationalQuery('suma de tasas', [mockTable]);
      expect(result).toBeDefined();
      expect(result?.operation).toBe('sum');
    });

    it('debería parsear query de comparación', () => {
      const result = parseComputationalQuery('comparar tasas entre municipios', [mockTable]);
      expect(result).toBeDefined();
      expect(result?.operation).toBe('compare');
    });

    it('debería devolver null si no hay tablas', () => {
      const result = parseComputationalQuery('suma de tasas', []);
      expect(result).toBeNull();
    });

    it('debería identificar columna objetivo', () => {
      const result = parseComputationalQuery('cuál es la suma de tasas', [mockTable]);
      expect(result?.targetColumn).toBe('Tasa');
    });
  });
});
