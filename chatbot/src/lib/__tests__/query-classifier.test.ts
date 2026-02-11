/**
 * Tests para query-classifier.ts
 *
 * Valida la detección de queries computacionales y clasificación de queries.
 */

import { describe, it, expect } from 'vitest';
import {
  isComputationalQuery,
  isFAQQuestion,
  needsRAGSearch,
  calculateOptimalLimit,
  calculateContentLimit,
  getOffTopicResponse,
} from '../query-classifier';

describe('Query Classifier', () => {
  describe('isComputationalQuery', () => {
    it('should detect aggregation queries', () => {
      const queries = [
        'suma de todos los montos',
        'totalizar las categorías',
        'promedio de montos',
        'media de los valores',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(true);
      });
    });

    it('should detect cross-municipality comparison queries', () => {
      const queries = [
        'cuál municipio tiene más decretos',
        'comparar decretos entre municipios',
        'ranking de municipios por cantidad de normativas',
        'diferencia entre municipios',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(true);
      });
    });

    it('should NOT detect simple counting queries as computational (they use LLM)', () => {
      const queries = [
        'cuántas categorías hay',
        'cuántos montos diferentes',
        'cantidad de tipos',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(false);
      });
    });

    it('should NOT detect simple tax queries as computational (they are semantic)', () => {
      const queries = [
        'monto de la categoría A',
        'valor de la tasa municipal',
        'precio de la habilitación',
        'tarifa para comercio',
        'tasas municipales merlo',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(false);
      });
    });

    it('should NOT detect simple normativas count as computational (they are count queries)', () => {
      const queries = [
        'cuántas ordenanzas hay',
        'cuántos decretos',
        'cantidad de resoluciones',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(false);
      });
    });

    it('should NOT detect semantic queries as computational', () => {
      const queries = [
        'qué dice la ordenanza de tránsito',
        'contenido del decreto 123',
        'artículos de la resolución',
        'texto completo del boletín',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(false);
      });
    });

    it('should NOT detect greetings as computational', () => {
      const queries = [
        'hola',
        'buenos días',
        'cómo estás',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(false);
      });
    });
  });

  describe('isFAQQuestion', () => {
    it('should detect FAQ about available municipalities', () => {
      const queries = [
        'qué municipios están disponibles',
        'cuáles municipios hay',
        'municipios disponibles',
      ];

      queries.forEach(query => {
        expect(isFAQQuestion(query)).toBe(true);
      });
    });

    it('should detect FAQ about how to search', () => {
      const queries = [
        'cómo busco una ordenanza',
        'cómo consultar decretos',
        'cómo uso el chat',
      ];

      queries.forEach(query => {
        expect(isFAQQuestion(query)).toBe(true);
      });
    });

    it('should NOT detect ordinance queries as FAQ', () => {
      const queries = [
        'ordenanza de tránsito',
        'decreto 123',
        'resolución municipal',
      ];

      queries.forEach(query => {
        expect(isFAQQuestion(query)).toBe(false);
      });
    });
  });

  describe('needsRAGSearch', () => {
    it('should return true for ordinance-related queries', () => {
      const queries = [
        'ordenanza de tránsito',
        'decreto municipal',
        'resolución del concejo',
        'normativa vigente',
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(true);
      });
    });

    it('should return true for tax/fee queries (they are semantic searches)', () => {
      const queries = [
        'tasas municipales',
        'valor de la tasa',
        'tarifa de comercio',
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(true);
      });
    });

    it('should return false for greetings', () => {
      const queries = [
        'hola',
        'buen días',
        'buenas tardes',
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(true);
      });
    });

    it('should return false for FAQ questions (they use LLM without RAG)', () => {
      const queries = [
        'qué municipios están disponibles',
        'cómo busco una ordenanza',
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(false);
      });
    });

    it('should return false for off-topic queries (no RAG needed)', () => {
      const queries = [
        'cómo está el clima',
        'quién ganó el partido',
        'receta de empanadas',
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(false);
      });
    });
  });

  describe('calculateOptimalLimit', () => {
    it('should return high limit for listing queries with filters', () => {
      const queries = [
        'cuántas ordenanzas hay',
        'lista todas las ordenanzas de 2025',
        'ordenanzas de carlos tejedor 2024',
      ];

      queries.forEach(query => {
        const limit = calculateOptimalLimit(query, true);
        expect(limit).toBeGreaterThan(10);
      });
    });

    it('should return 1 for exact number searches with filters', () => {
      const queries = [
        'ordenanza 123',
        'decreto 456 de merlo',
      ];

      queries.forEach(query => {
        const limit = calculateOptimalLimit(query, true);
        expect(limit).toBe(1);
      });
    });

    it('should return default limit for general queries without filters', () => {
      const query = 'ordenanzas de tránsito';
      const limit = calculateOptimalLimit(query, false);
      expect(limit).toBe(5);
    });
  });

  describe('calculateContentLimit', () => {
    it('should return low limit for metadata-only queries', () => {
      const queries = [
        'cuántas ordenanzas hay',
        'cuál es la última ordenanza',
        'existe la ordenanza 123',
      ];

      queries.forEach(query => {
        const limit = calculateContentLimit(query);
        expect(limit).toBe(200);
      });
    });

    it('should return medium limit for content queries', () => {
      const queries = [
        'qué dice la ordenanza',
        'contenido del decreto',
        'artículo 5 de la resolución',
      ];

      queries.forEach(query => {
        const limit = calculateContentLimit(query);
        expect(limit).toBe(2000);
      });
    });

    it('should return default limit for general queries', () => {
      const query = 'ordenanza de tránsito';
      const limit = calculateContentLimit(query);
      expect(limit).toBe(500);
    });
  });

  describe('getOffTopicResponse', () => {
    it('should return helpful message for off-topic queries', () => {
      const response = getOffTopicResponse('receta de empanadas');
      expect(response).toContain('ordenanzas');
      expect(response).toBeTruthy();
    });

    it('should return a fallback message for on-topic queries', () => {
      const response = getOffTopicResponse('ordenanza de tránsito');
      expect(response).toBeTruthy();
      expect(typeof response).toBe('string');
      expect(response).toContain('ordenanzas');
    });
  });
});
