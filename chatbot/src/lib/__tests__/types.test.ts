/**
 * Tests para types.ts
 *
 * Prueba los tipos y validaciones del proyecto.
 */

import { describe, it, expect } from 'vitest';
import type { ChatMessage, ChatFilters, Source, SearchResult, DatabaseStats } from '../types';

describe('Types', () => {
  describe('ChatMessage', () => {
    it('should accept valid user message', () => {
      const message: ChatMessage = {
        id: '123',
        role: 'user',
        content: 'Hola',
        createdAt: Date.now(),
      };

      expect(message.role).toBe('user');
    });

    it('should accept valid assistant message', () => {
      const message: ChatMessage = {
        id: '456',
        role: 'assistant',
        content: 'Respuesta',
      };

      expect(message.role).toBe('assistant');
    });

    it('should accept valid system message', () => {
      const message: ChatMessage = {
        id: '789',
        role: 'system',
        content: 'System prompt',
      };

      expect(message.role).toBe('system');
    });

    it('should make createdAt optional', () => {
      const message: ChatMessage = {
        id: '123',
        role: 'user',
        content: 'Test',
      };

      expect(message.createdAt).toBeUndefined();
    });
  });

  describe('ChatFilters', () => {
    it('should accept valid empty filters', () => {
      const filters: ChatFilters = {
        municipality: null,
        ordinanceType: 'all',
        dateFrom: null,
        dateTo: null,
      };

      expect(filters.municipality).toBeNull();
      expect(filters.ordinanceType).toBe('all');
    });

    it('should accept valid filters with municipality', () => {
      const filters: ChatFilters = {
        municipality: 'Carlos Tejedor',
        ordinanceType: 'all',
        dateFrom: null,
        dateTo: null,
      };

      expect(filters.municipality).toBe('Carlos Tejedor');
    });

    it('should accept valid ordinance types', () => {
      const types: ChatFilters['ordinanceType'][] = [
        'all',
        'ordenanza',
        'decreto',
        'boletin',
        'resolucion',
        'disposicion',
        'convenio',
        'licitacion',
      ];

      types.forEach((type) => {
        const filters: ChatFilters = {
          municipality: null,
          ordinanceType: type,
          dateFrom: null,
          dateTo: null,
        };

        expect(filters.ordinanceType).toBe(type);
      });
    });

    it('should accept date range', () => {
      const filters: ChatFilters = {
        municipality: null,
        ordinanceType: 'all',
        dateFrom: '2024-01-01',
        dateTo: '2024-12-31',
      };

      expect(filters.dateFrom).toBe('2024-01-01');
      expect(filters.dateTo).toBe('2024-12-31');
    });
  });

  describe('Source', () => {
    it('should accept valid source with required fields', () => {
      const source: Source = {
        title: 'Ordenanza 123',
        url: 'https://example.com',
        municipality: 'Carlos Tejedor',
        type: 'ordenanza',
        status: 'vigente',
      };

      expect(source.title).toBe('Ordenanza 123');
      expect(source.municipality).toBe('Carlos Tejedor');
    });

    it('should accept source with optional documentTypes', () => {
      const source: Source = {
        title: 'Boletín',
        url: 'https://example.com',
        municipality: 'Merlo',
        type: 'boletin',
        documentTypes: ['ordenanza', 'decreto'],
      };

      expect(source.documentTypes).toEqual(['ordenanza', 'decreto']);
    });

    it('should accept source without status', () => {
      const source: Source = {
        title: 'Test',
        url: 'https://example.com',
        municipality: 'Test',
        type: 'decreto',
      };

      expect(source.status).toBeUndefined();
    });
  });

  describe('SearchResult', () => {
    it('should accept valid search result', () => {
      const result: SearchResult = {
        context: 'Contexto de búsqueda',
        sources: [
          {
            title: 'Ordenanza 123',
            url: 'https://example.com/1',
            municipality: 'Carlos Tejedor',
            type: 'ordenanza',
            status: 'vigente',
          },
          {
            title: 'Decreto 456',
            url: 'https://example.com/2',
            municipality: 'Carlos Tejedor',
            type: 'decreto',
            status: 'vigente',
          },
        ],
      };

      expect(result.sources).toHaveLength(2);
    });

    it('should accept search result with empty sources', () => {
      const result: SearchResult = {
        context: 'No se encontraron resultados',
        sources: [],
      };

      expect(result.sources).toHaveLength(0);
    });
  });

  describe('DatabaseStats', () => {
    it('should accept valid database stats', () => {
      const stats: DatabaseStats = {
        totalDocuments: 150000,
        municipalities: 50,
        municipalityList: ['Carlos Tejedor', 'Merlo', 'La Plata'],
        lastUpdated: '2024-01-01T00:00:00Z',
      };

      expect(stats.totalDocuments).toBe(150000);
      expect(stats.municipalities).toBe(50);
      expect(stats.municipalityList).toHaveLength(3);
    });

    it('should accept database stats without lastUpdated', () => {
      const stats: DatabaseStats = {
        totalDocuments: 100000,
        municipalities: 30,
        municipalityList: ['Carlos Tejedor'],
      };

      expect(stats.lastUpdated).toBeUndefined();
    });
  });
});
