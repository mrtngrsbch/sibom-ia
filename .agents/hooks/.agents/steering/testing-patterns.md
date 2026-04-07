# testing-patterns

## ⚠️ BASE EDITABLE

Este archivo fue copiado desde: `.kiro/steering/testing-patterns.md`

**Puedes EDITAR este archivo** para agregar reglas específicas para agentes AI.

Para regenerar desde .kiro/:
```bash
python .agents/hooks/sync_from_kiro.py
```

---

# Patrones de Testing y Validación - SIBOM Scraper Assistant

## Estrategia de Testing Implementada

### 1. Testing Scripts de Desarrollo

#### Scripts de Testing Específicos
**Ubicación:** `chatbot/` (archivos test-*.ts)

```typescript
// chatbot/test-bm25.ts - Testing del algoritmo BM25
import { BM25Index, tokenize } from './src/lib/rag/bm25';

const testDocuments = [
  "ordenanza municipal de tránsito carlos tejedor",
  "decreto de habilitación comercial merlo",
  "resolución de tasas municipales"
];

const tokenizedDocs = testDocuments.map(doc => tokenize(doc));
const bm25 = new BM25Index(tokenizedDocs);

// Test de búsqueda
const results = bm25.search("ordenanza tránsito", 3);
console.log('Resultados BM25:', results);

// Test de explicación de score
const explanation = bm25.explainScore("ordenanza tránsito", 0);
console.log('Explicación del score:', explanation);
```

```typescript
// chatbot/test-query-analyzer.ts - Testing del clasificador de consultas
import { needsRAGSearch, isFAQQuestion, calculateOptimalLimit } from './src/lib/query-classifier';
import { extractFiltersFromQuery } from './src/lib/query-filter-extractor';

const testQueries = [
  "ordenanzas de carlos tejedor 2025",
  "hola como estas",
  "cuántos municipios hay disponibles",
  "decreto 123 de merlo"
];

testQueries.forEach(query => {
  console.log(`\nQuery: "${query}"`);
  console.log(`Necesita RAG: ${needsRAGSearch(query)}`);
  console.log(`Es FAQ: ${isFAQQuestion(query)}`);
  console.log(`Límite óptimo: ${calculateOptimalLimit(query, false)}`);
  
  const filters = extractFiltersFromQuery(query, ['Carlos Tejedor', 'Merlo']);
  console.log(`Filtros extraídos:`, filters);
});
```

```typescript
// chatbot/test-retriever.ts - Testing del sistema RAG
import { retrieveContext, getDatabaseStats } from './src/lib/rag/retriever';

async function testRetriever() {
  // Test de estadísticas
  const stats = await getDatabaseStats();
  console.log('Estadísticas DB:', stats);
  
  // Test de búsqueda básica
  const result1 = await retrieveContext("ordenanzas de tránsito", {
    municipality: "Carlos Tejedor",
    limit: 3
  });
  console.log('Búsqueda con filtros:', result1.sources.length, 'fuentes');
  
  // Test de búsqueda sin filtros
  const result2 = await retrieveContext("decreto habilitación", { limit: 5 });
  console.log('Búsqueda sin filtros:', result2.sources.length, 'fuentes');
}

testRetriever().catch(console.error);
```

### 2. Testing de Componentes React

#### Testing con React Testing Library
```typescript
// chatbot/src/components/chat/__tests__/ActiveFilters.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ActiveFilters from '../ActiveFilters';
import type { ChatFilters } from '@/lib/types';

describe('ActiveFilters', () => {
  const defaultProps = {
    municipality: null,
    ordinanceType: 'all' as const,
    dateFrom: null,
    dateTo: null,
    onRemoveFilter: vi.fn(),
    onShowAdvancedFilters: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display municipality filter badge when municipality is set', () => {
    render(
      <ActiveFilters 
        {...defaultProps} 
        municipality="Carlos Tejedor" 
      />
    );
    
    expect(screen.getByText('Carlos Tejedor')).toBeInTheDocument();
    expect(screen.getByLabelText('Remove municipality filter')).toBeInTheDocument();
  });

  it('should call onRemoveFilter when filter badge is clicked', async () => {
    const onRemoveFilter = vi.fn();
    
    render(
      <ActiveFilters 
        {...defaultProps} 
        municipality="Carlos Tejedor"
        onRemoveFilter={onRemoveFilter}
      />
    );
    
    fireEvent.click(screen.getByLabelText('Remove municipality filter'));
    
    await waitFor(() => {
      expect(onRemoveFilter).toHaveBeenCalledWith('municipality');
    });
  });

  it('should format date ranges intelligently', () => {
    render(
      <ActiveFilters 
        {...defaultProps} 
        dateFrom="2025-01-01"
        dateTo="2025-12-31"
      />
    );
    
    // Should show "Año 2025" instead of full date range
    expect(screen.getByText('Año 2025')).toBeInTheDocument();
  });

  it('should show advanced filters button when no filters are active', () => {
    render(<ActiveFilters {...defaultProps} />);
    
    expect(screen.getByText('Filtros avanzados')).toBeInTheDocument();
  });

  it('should show edit filters button when filters are active', () => {
    render(
      <ActiveFilters 
        {...defaultProps} 
        municipality="Carlos Tejedor"
      />
    );
    
    expect(screen.getByText('Editar filtros')).toBeInTheDocument();
  });
});
```

#### Testing de Hooks Personalizados
```typescript
// chatbot/src/hooks/__tests__/useChat.test.tsx
import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useChat } from 'ai/react';

// Mock del hook de Vercel AI
vi.mock('ai/react', () => ({
  useChat: vi.fn()
}));

describe('useChat integration', () => {
  const mockUseChat = vi.mocked(useChat);

  beforeEach(() => {
    mockUseChat.mockReturnValue({
      messages: [],
      input: '',
      handleInputChange: vi.fn(),
      handleSubmit: vi.fn(),
      isLoading: false,
      error: null,
      reload: vi.fn(),
      stop: vi.fn(),
      append: vi.fn(),
      setMessages: vi.fn(),
      setInput: vi.fn(),
    });
  });

  it('should handle chat initialization', () => {
    const { result } = renderHook(() => useChat({
      api: '/api/chat',
      onError: vi.fn(),
    }));

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle error states', () => {
    const onError = vi.fn();
    mockUseChat.mockReturnValue({
      ...mockUseChat.mock.results[0].value,
      error: new Error('Test error'),
    });

    const { result } = renderHook(() => useChat({
      api: '/api/chat',
      onError,
    }));

    expect(result.current.error).toBeInstanceOf(Error);
  });
});
```

### 3. Testing de API Routes

#### Testing de Endpoints Next.js
```typescript
// chatbot/src/app/api/chat/__tests__/route.test.ts
import { POST } from '../route';
import { NextRequest } from 'next/server';

// Mock de dependencias
vi.mock('@/lib/rag/retriever', () => ({
  retrieveContext: vi.fn(),
  getDatabaseStats: vi.fn(),
}));

vi.mock('@ai-sdk/openai', () => ({
  createOpenAI: vi.fn(() => ({
    // Mock del cliente OpenRouter
  })),
}));

describe('/api/chat', () => {
  beforeEach(() => {
    // Setup environment variables
    process.env.OPENROUTER_API_KEY = 'test-key';
  });

  it('should handle valid chat request', async () => {
    const request = new NextRequest('http://localhost:3000/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages: [
          { role: 'user', content: 'ordenanzas de carlos tejedor' }
        ]
      }),
    });

    const response = await POST(request);
    
    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toContain('text/plain');
  });

  it('should handle missing API key', async () => {
    delete process.env.OPENROUTER_API_KEY;
    
    const request = new NextRequest('http://localhost:3000/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages: [{ role: 'user', content: 'test' }]
      }),
    });

    const response = await POST(request);
    
    expect(response.status).toBe(500);
    const body = await response.json();
    expect(body.error).toContain('API Key');
  });

  it('should handle off-topic queries without LLM call', async () => {
    const request = new NextRequest('http://localhost:3000/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        messages: [
          { role: 'user', content: 'como esta el clima hoy' }
        ]
      }),
    });

    const response = await POST(request);
    
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.content).toContain('clima');
  });
});
```

### 4. Testing de Utilidades y Lógica de Negocio

#### Testing de Query Classifier
```typescript
// chatbot/src/lib/__tests__/query-classifier.test.ts
import { 
  needsRAGSearch, 
  isFAQQuestion, 
  calculateOptimalLimit,
  getOffTopicResponse 
} from '../query-classifier';

describe('Query Classifier', () => {
  describe('needsRAGSearch', () => {
    it('should return true for ordinance-related queries', () => {
      const queries = [
        'ordenanza de tránsito',
        'decreto municipal',
        'normativa vigente',
        'resolución del concejo'
      ];

      queries.forEach(query => {
        expect(needsRAGSearch(query)).toBe(true);
      });
    });

    it('should return false for greetings', () => {
      const greetings = [
        'hola',
        'buenos días',
        'cómo estás',
        'qué tal'
      ];

      greetings.forEach(greeting => {
        expect(needsRAGSearch(greeting)).toBe(false);
      });
    });

    it('should return false for FAQ questions', () => {
      const faqQuestions = [
        'qué municipios están disponibles',
        'cómo busco una ordenanza',
        'cómo funciona el chat'
      ];

      faqQuestions.forEach(question => {
        expect(needsRAGSearch(question)).toBe(false);
        expect(isFAQQuestion(question)).toBe(true);
      });
    });
  });

  describe('calculateOptimalLimit', () => {
    it('should return higher limit for listing queries with filters', () => {
      const listingQueries = [
        'cuántas ordenanzas hay',
        'lista todas las ordenanzas de 2025',
        'ordenanzas de carlos tejedor 2024'
      ];

      listingQueries.forEach(query => {
        const limit = calculateOptimalLimit(query, true);
        expect(limit).toBeGreaterThan(10);
      });
    });

    it('should return 1 for exact number searches with filters', () => {
      const exactQueries = [
        'ordenanza 123',
        'decreto 456 de merlo'
      ];

      exactQueries.forEach(query => {
        const limit = calculateOptimalLimit(query, true);
        expect(limit).toBe(1);
      });
    });
  });

  describe('getOffTopicResponse', () => {
    it('should return weather-specific response for weather queries', () => {
      const response = getOffTopicResponse('como está el clima hoy');
      expect(response).toContain('clima');
      expect(response).toContain('ordenanza');
    });

    it('should return generic response for unmatched off-topic queries', () => {
      const response = getOffTopicResponse('pregunta completamente random');
      expect(response).toContain('ordenanzas municipales');
      expect(response).toContain('normativas');
    });
  });
});
```

#### Testing de Filter Extractor
```typescript
// chatbot/src/lib/__tests__/query-filter-extractor.test.ts
import { 
  extractYear, 
  extractMunicipality, 
  extractOrdinanceType,
  extractFiltersFromQuery 
} from '../query-filter-extractor';

describe('Query Filter Extractor', () => {
  describe('extractYear', () => {
    it('should extract year from various patterns', () => {
      const testCases = [
        { query: 'ordenanzas en el 2025', expected: '2025' },
        { query: 'decretos del 2024', expected: '2024' },
        { query: 'normativas en 2023', expected: '2023' },
        { query: 'año 2022', expected: '2022' },
      ];

      testCases.forEach(({ query, expected }) => {
        expect(extractYear(query)).toBe(expected);
      });
    });

    it('should return null for invalid years', () => {
      const invalidQueries = [
        'ordenanzas en el 1999', // Too old
        'decretos del 2050',     // Too future
        'normativas sin año'     // No year
      ];

      invalidQueries.forEach(query => {
        expect(extractYear(query)).toBeNull();
      });
    });
  });

  describe('extractMunicipality', () => {
    const municipalities = ['Carlos Tejedor', 'Merlo', 'La Plata'];

    it('should extract municipality case-insensitively', () => {
      const testCases = [
        { query: 'ordenanzas de carlos tejedor', expected: 'Carlos Tejedor' },
        { query: 'decretos de MERLO', expected: 'Merlo' },
        { query: 'normativas la plata', expected: 'La Plata' },
      ];

      testCases.forEach(({ query, expected }) => {
        expect(extractMunicipality(query, municipalities)).toBe(expected);
      });
    });

    it('should return null for unknown municipalities', () => {
      const query = 'ordenanzas de ciudad inexistente';
      expect(extractMunicipality(query, municipalities)).toBeNull();
    });
  });

  describe('extractFiltersFromQuery', () => {
    const municipalities = ['Carlos Tejedor', 'Merlo'];

    it('should extract multiple filters from complex query', () => {
      const query = 'ordenanzas de carlos tejedor en el 2025';
      const filters = extractFiltersFromQuery(query, municipalities);

      expect(filters).toEqual({
        municipality: 'Carlos Tejedor',
        type: 'ordenanza',
        dateFrom: '2025-01-01',
        dateTo: '2025-12-31',
        limit: undefined
      });
    });

    it('should preserve existing filters when they have priority', () => {
      const query = 'decretos de merlo 2024';
      const existingFilters = { municipality: 'Carlos Tejedor' };
      
      const filters = extractFiltersFromQuery(query, municipalities, existingFilters);

      expect(filters.municipality).toBe('Carlos Tejedor'); // Preserved
      expect(filters.type).toBe('decreto'); // Extracted
    });
  });
});
```

### 5. Testing de BM25 Algorithm

#### Testing del Algoritmo de Ranking
```typescript
// chatbot/src/lib/rag/__tests__/bm25.test.ts
import { BM25Index, tokenize, calculateIDF } from '../bm25';

describe('BM25 Algorithm', () => {
  describe('tokenize', () => {
    it('should tokenize Spanish text correctly', () => {
      const text = 'La ordenanza municipal de tránsito está vigente';
      const tokens = tokenize(text);
      
      // Should remove stopwords and normalize
      expect(tokens).not.toContain('la');
      expect(tokens).not.toContain('de');
      expect(tokens).toContain('ordenanza');
      expect(tokens).toContain('municipal');
      expect(tokens).toContain('tránsito');
      expect(tokens).toContain('vigente');
    });

    it('should handle accents and special characters', () => {
      const text = 'Resolución N° 123/2024 - Habilitación';
      const tokens = tokenize(text);
      
      expect(tokens).toContain('resolucion'); // Accent removed
      expect(tokens).toContain('habilitacion'); // Accent removed
      expect(tokens).toContain('123');
      expect(tokens).toContain('2024');
    });
  });

  describe('BM25Index', () => {
    const testDocuments = [
      'ordenanza municipal de tránsito carlos tejedor',
      'decreto de habilitación comercial merlo',
      'resolución de tasas municipales la plata',
      'ordenanza de ruidos molestos carlos tejedor'
    ];

    let bm25: BM25Index;

    beforeEach(() => {
      const tokenizedDocs = testDocuments.map(doc => tokenize(doc));
      bm25 = new BM25Index(tokenizedDocs);
    });

    it('should rank documents by relevance', () => {
      const results = bm25.search('ordenanza carlos tejedor', 4);
      
      expect(results).toHaveLength(4);
      expect(results[0].score).toBeGreaterThan(results[1].score);
      
      // Documents with "ordenanza" and "carlos tejedor" should rank higher
      const topDoc = testDocuments[results[0].index];
      expect(topDoc).toContain('ordenanza');
      expect(topDoc).toContain('carlos tejedor');
    });

    it('should handle queries with no matches', () => {
      const results = bm25.search('palabra inexistente', 10);
      expect(results).toHaveLength(0);
    });

    it('should explain scores for debugging', () => {
      const explanation = bm25.explainScore('ordenanza municipal', 0);
      
      expect(explanation.totalScore).toBeGreaterThan(0);
      expect(explanation.termScores).toHaveLength(2); // 'ordenanza' + 'municipal'
      
      const ordenanzaScore = explanation.termScores.find(t => t.term === 'ordenanza');
      expect(ordenanzaScore).toBeDefined();
      expect(ordenanzaScore!.tf).toBeGreaterThan(0);
      expect(ordenanzaScore!.idf).toBeGreaterThan(0);
    });

    it('should handle different BM25 parameters', () => {
      const conservativeBM25 = new BM25Index(
        testDocuments.map(doc => tokenize(doc)),
        1.0, // Lower k1 (less term frequency saturation)
        0.5  // Lower b (less length normalization)
      );

      const aggressiveBM25 = new BM25Index(
        testDocuments.map(doc => tokenize(doc)),
        2.0, // Higher k1
        1.0  // Higher b
      );

      const query = 'ordenanza municipal';
      const conservativeResults = conservativeBM25.search(query, 2);
      const aggressiveResults = aggressiveBM25.search(query, 2);

      // Scores should be different due to different parameters
      expect(conservativeResults[0].score).not.toBe(aggressiveResults[0].score);
    });
  });
});
```

### 6. Integration Testing

#### Testing de Flujo Completo
```typescript
// chatbot/src/__tests__/integration/chat-flow.test.ts
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ChatPage from '@/app/page';

// Mock de fetch para API calls
global.fetch = vi.fn();

describe('Chat Integration Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock successful API response
    (global.fetch as any).mockResolvedValue({
      ok: true,
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode('data: {"content":"Test response"}\n\n'));
          controller.close();
        }
      })
    });
  });

  it('should complete full chat interaction', async () => {
    render(<ChatPage />);

    // User types a query
    const input = screen.getByPlaceholderText(/escribe tu consulta/i);
    fireEvent.change(input, { target: { value: 'ordenanzas de carlos tejedor' } });

    // User submits
    const submitButton = screen.getByRole('button', { name: /enviar/i });
    fireEvent.click(submitButton);

    // Should show loading state
    expect(screen.getByText(/consultando/i)).toBeInTheDocument();

    // Should eventually show response
    await waitFor(() => {
      expect(screen.getByText('Test response')).toBeInTheDocument();
    });

    // Should update filters based on query
    await waitFor(() => {
      expect(screen.getByText('Carlos Tejedor')).toBeInTheDocument();
    });
  });

  it('should handle filter interactions', async () => {
    render(<ChatPage />);

    // Apply municipality filter
    const municipalitySelect = screen.getByLabelText(/municipio/i);
    fireEvent.change(municipalitySelect, { target: { value: 'Carlos Tejedor' } });

    // Should show active filter badge
    expect(screen.getByText('Carlos Tejedor')).toBeInTheDocument();

    // Remove filter
    const removeButton = screen.getByLabelText(/remove municipality filter/i);
    fireEvent.click(removeButton);

    // Filter should be removed
    await waitFor(() => {
      expect(screen.queryByText('Carlos Tejedor')).not.toBeInTheDocument();
    });
  });
});
```

### 7. Performance Testing

#### Testing de Performance de BM25
```typescript
// chatbot/src/lib/rag/__tests__/bm25-performance.test.ts
import { BM25Index, tokenize } from '../bm25';

describe('BM25 Performance', () => {
  it('should handle large document collections efficiently', () => {
    // Generate 1000 test documents
    const largeDocumentSet = Array.from({ length: 1000 }, (_, i) => 
      `documento ${i} con contenido de prueba ordenanza municipal ${i % 10}`
    );

    const tokenizedDocs = largeDocumentSet.map(doc => tokenize(doc));
    
    const startTime = performance.now();
    const bm25 = new BM25Index(tokenizedDocs);
    const indexTime = performance.now() - startTime;

    // Index creation should be reasonably fast (< 1 second)
    expect(indexTime).toBeLessThan(1000);

    const searchStartTime = performance.now();
    const results = bm25.search('ordenanza municipal', 10);
    const searchTime = performance.now() - searchStartTime;

    // Search should be very fast (< 100ms)
    expect(searchTime).toBeLessThan(100);
    expect(results).toHaveLength(10);
  });

  it('should handle memory usage efficiently', () => {
    const memoryBefore = process.memoryUsage().heapUsed;
    
    // Create multiple BM25 indexes
    const indexes = Array.from({ length: 10 }, () => {
      const docs = Array.from({ length: 100 }, (_, i) => `documento ${i}`);
      return new BM25Index(docs.map(doc => tokenize(doc)));
    });

    const memoryAfter = process.memoryUsage().heapUsed;
    const memoryIncrease = memoryAfter - memoryBefore;

    // Memory increase should be reasonable (< 50MB)
    expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    
    // Cleanup
    indexes.length = 0;
  });
});
```

### 8. Testing Configuration

#### Vitest Configuration
```typescript
// chatbot/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        'src/app/layout.tsx', // Next.js boilerplate
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### Test Setup
```typescript
// chatbot/src/test/setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
}));

// Mock environment variables
process.env.OPENROUTER_API_KEY = 'test-key';
process.env.NODE_ENV = 'test';

// Mock fetch globally
global.fetch = vi.fn();

// Mock localStorage
Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  },
  writable: true,
});
```

## Testing Strategy Summary

### 1. **Unit Testing** (80% coverage target)
- Funciones puras (tokenize, extractYear, calculateIDF)
- Lógica de negocio (query classification, filter extraction)
- Algoritmos (BM25 scoring, ranking)

### 2. **Component Testing** (React Testing Library)
- Componentes aislados con props mockeadas
- Interacciones de usuario (clicks, form submissions)
- Estados de loading y error

### 3. **Integration Testing**
- Flujos completos de usuario
- Interacción entre componentes
- API calls y responses

### 4. **Performance Testing**
- Benchmarks de BM25 con datasets grandes
- Memory usage monitoring
- Response time validation

### 5. **Manual Testing Scripts**
- Scripts de desarrollo para testing rápido
- Validación de algoritmos con datos reales
- Debugging de edge cases

## Checklist de Testing

- [ ] ✅ Scripts de testing manual implementados
- [ ] ⏳ Unit tests para query classifier
- [ ] ⏳ Unit tests para filter extractor  
- [ ] ⏳ Unit tests para BM25 algorithm
- [ ] ⏳ Component tests para ActiveFilters
- [ ] ⏳ Component tests para ChatContainer
- [ ] ⏳ API route tests para /api/chat
- [ ] ⏳ Integration tests para chat flow
- [ ] ⏳ Performance tests para BM25
- [ ] ⏳ Error scenario testing
- [ ] ⏳ Accessibility testing
- [ ] ⏳ Mobile responsive testing