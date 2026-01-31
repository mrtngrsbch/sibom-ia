/**
 * query-classifier-semantic.test.ts
 *
 * Tests for semantic search classification
 * Ensures content-based queries are properly detected
 */

import { describe, it, expect } from 'vitest';
import { classifyQueryIntent } from '@/lib/query-classifier';

describe('Query Classifier - Semantic Search Detection', () => {
  describe('Content-based queries (should be semantic-search)', () => {
    it('should classify salary queries as semantic search', () => {
      const queries = [
        'sueldos de carlos tejedor de 2025',
        'salarios municipales merlo',
        'remuneraciones del personal',
        'jornada laboral ordenanzas',
      ];

      queries.forEach(query => {
        const result = classifyQueryIntent(query);
        expect(result.intent).toBe('semantic-search');
        expect(result.needsLLM).toBe(true);
        expect(result.needsRAG).toBe(true);
      });
    });

    it('should classify traffic queries as semantic search', () => {
      const queries = [
        'ordenanzas de tránsito carlos tejedor',
        'normativas viales',
        'estacionamiento prohibido',
        'velocidad máxima en zona urbana',
      ];

      queries.forEach(query => {
        const result = classifyQueryIntent(query);
        expect(result.intent).toBe('semantic-search');
        expect(result.needsLLM).toBe(true);
      });
    });

    it('should classify tax queries as semantic search', () => {
      const queries = [
        'tasas municipales merlo',
        'impuestos comerciales',
        'tributos vigentes',
      ];

      queries.forEach(query => {
        const result = classifyQueryIntent(query);
        expect(result.intent).toBe('semantic-search');
        expect(result.needsLLM).toBe(true);
      });
    });

    it('should classify permit queries as semantic search', () => {
      const queries = [
        'habilitación comercial',
        'permisos de construcción',
        'licencias de conducir',
      ];

      queries.forEach(query => {
        const result = classifyQueryIntent(query);
        expect(result.intent).toBe('semantic-search');
        expect(result.needsLLM).toBe(true);
      });
    });
  });

  describe('Simple listing queries (LLM interprets)', () => {
    it('should classify simple listings as semantic-search (LLM decides)', () => {
      const queries = [
        'decretos de carlos tejedor 2025',
        'ordenanzas de merlo 2024',
        'resoluciones de la plata',
      ];

      queries.forEach(query => {
        const result = classifyQueryIntent(query);
        // Simplified: now everything that's not off-topic/FAQ/computational is semantic-search
        // The LLM will decide whether to list or search content
        expect(result.intent).toBe('semantic-search');
        expect(result.needsLLM).toBe(true);
        expect(result.needsRAG).toBe(true);
      });
    });

    it('should classify count queries as semantic-search (LLM decides)', () => {
      const queries = [
        'cuántas ordenanzas hay de carlos tejedor',
        'cantidad de decretos 2025',
      ];

      queries.forEach(query => {
        const result = classifyQueryIntent(query);
        // Simplified: LLM handles counting via RAG
        expect(result.intent).toBe('semantic-search');
        expect(result.needsLLM).toBe(true);
        expect(result.needsRAG).toBe(true);
      });
    });
  });

  describe('Edge cases', () => {
    it('should handle queries with both content and metadata', () => {
      // "sueldos" is content keyword → semantic search
      const result = classifyQueryIntent('sueldos de carlos tejedor 2025');
      expect(result.intent).toBe('semantic-search');
      expect(result.needsLLM).toBe(true);
      expect(result.needsRAG).toBe(true);
    });

    it('should handle queries without municipality', () => {
      const result = classifyQueryIntent('ordenanzas sobre salud');
      expect(result.intent).toBe('semantic-search');
      expect(result.needsLLM).toBe(true);
      expect(result.needsRAG).toBe(true);
    });

    it('should handle queries with accents', () => {
      const result = classifyQueryIntent('educación en carlos tejedor');
      expect(result.intent).toBe('semantic-search');
      expect(result.needsLLM).toBe(true);
      expect(result.needsRAG).toBe(true);
    });

    it('should detect FAQ questions', () => {
      const result = classifyQueryIntent('qué municipios están disponibles');
      expect(result.intent).toBe('faq');
      expect(result.needsRAG).toBe(false);
      expect(result.needsLLM).toBe(true);
    });

    it('should detect off-topic queries', () => {
      const result = classifyQueryIntent('receta de empanadas');
      expect(result.intent).toBe('off-topic');
      expect(result.needsRAG).toBe(false);
      expect(result.needsLLM).toBe(false);
    });

    it('should detect computational queries', () => {
      const result = classifyQueryIntent('cuál municipio tiene más decretos');
      expect(result.intent).toBe('computational');
      expect(result.needsRAG).toBe(true);
      expect(result.needsLLM).toBe(true);
    });
  });
});
