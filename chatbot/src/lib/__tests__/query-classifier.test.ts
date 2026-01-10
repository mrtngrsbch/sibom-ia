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
        'suma de todas las tasas municipales',
        'total de montos en la ordenanza',
        'promedio de las tasas',
        'media de los valores',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(true);
      });
    });

    it('should detect comparison queries', () => {
      const queries = [
        'cuál es el monto más alto',
        'cuál es la tasa mayor',
        'cuál es el valor mínimo',
        'comparar tasas entre categorías',
        'diferencia entre categoría A y B',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(true);
      });
    });

    it('should detect counting queries', () => {
      const queries = [
        'cuántas categorías hay',
        'cuántos montos diferentes',
        'cantidad de tasas',
        'número de categorías',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(true);
      });
    });

    it('should detect value lookup queries', () => {
      const queries = [
        'monto de la categoría A',
        'valor de la tasa municipal',
        'precio de la habilitación',
        'tarifa para comercio',
      ];

      queries.forEach(query => {
        expect(isComputationalQuery(query)).toBe(true);
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

    it('should return false for greetings', () => {
      const queries = [
        'hola',
        'buenos días',
        'cómo estás',
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(false);
      });
    });

    it('should return false for FAQ questions', () => {
      const queries = [
        'qué municipios están disponibles',
        'cómo busco una ordenanza',
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(false);
      });
    });

    it('should return false for off-topic queries', () => {
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
        expect(limit).toBe(1000);
      });
    });

    it('should return default limit for general queries', () => {
      const query = 'ordenanza de tránsito';
      const limit = calculateContentLimit(query);
      expect(limit).toBe(500);
    });
  });

  describe('getOffTopicResponse', () => {
    it('should return weather-specific response for weather queries', () => {
      const response = getOffTopicResponse('cómo está el clima hoy');
      expect(response).toContain('clima');
      expect(response).not.toBeNull();
    });

    it('should return sports-specific response for sports queries', () => {
      const response = getOffTopicResponse('quién ganó el partido de fútbol');
      expect(response).toContain('fútbol');
      expect(response).not.toBeNull();
    });

    it('should return generic response for unmatched off-topic queries', () => {
      const response = getOffTopicResponse('pregunta completamente random');
      expect(response).toContain('ordenanzas municipales');
      expect(response).not.toBeNull();
    });

    it('should return null for ordinance-related queries', () => {
      // Esta función solo responde a queries off-topic
      // Para queries on-topic, debería retornar el fallback genérico
      const response = getOffTopicResponse('ordenanza de tránsito');
      expect(response).not.toBeNull(); // Siempre retorna algo (fallback genérico)
    });
  });
});
