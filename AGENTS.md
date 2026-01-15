# AGENTS.md - Sibom Scraper Assistant

Repository configuration and workflows for autonomous agents.

## 🎯 Arquitectura de Agentes

**Este proyecto usa `.agents/` como fuente principal de coordinación para agentes AI.**

- **Leer primero:** `.agents/specs/` - Arquitectura concisa del proyecto
- **Respetar siempre:** `.agents/steering/` - Reglas obligatorias para agentes
- **Consultar si necesario:** `.kiro/specs/` - Análisis técnico profundo

Ver [`.agents/COORDINACION.md`](.agents/COORDINACION.md) para detalles completos.

## 🏗️ Project Structure

This is a polyglot repository with two main applications:

- `/chatbot`: Next.js 16 (TypeScript) frontend for querying bulletins.
- `/python-cli`: Python 3.13 CLI tool for scraping SIBOM.

## 🚀 Common Commands

### Chatbot (Next.js)

- **Install**: `cd chatbot && npm install`
- **Dev**: `cd chatbot && npm run dev`
- **Build**: `cd chatbot && npm run build`
- **Start (production)**: `cd chatbot && npm run start`
- **Lint**: `cd chatbot && npm run lint`
- **Test**: `cd chatbot && npm test`
- **Test UI**: `cd chatbot && npm run test:ui`
- **Test Coverage**: `cd chatbot && npm run test:coverage`

#### Ejecutar un solo test (Chatbot)

```bash
# Test específico con filtro
cd chatbot && npm test -- test-query-analyzer

# Test con watch mode
cd chatbot && npm test -- --watch test-query-analyzer

# Test específico con coverage
cd chatbot && npm run test:coverage -- test-query-analyzer

# Test en un archivo específico
cd chatbot && npm test -- src/lib/rag/__tests__/table-formatter.test.ts

# Test con modo verbose
cd chatbot && npm test -- --reporter=verbose

# Actualizar snapshots
cd chatbot && npm test -- -u
```

### Scraper (Python CLI)

- **Setup**: `cd python-cli && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- **Run Scraper**: `python3 sibom_scraper.py --limit 5`
- **Run Tests**: `pytest` (requires venv activation)
- **Test Coverage**: `pytest --cov=. --cov-report=html`
- **Extraction Tools**: Scripts like `monto_extractor.py` and `table_extractor.py` are used for post-processing.

#### Ejecutar un solo test (Python)

```bash
# Test específico
cd python-cli && pytest tests/test_table_extractor.py -v

# Test específico con función
cd python-cli && pytest tests/test_table_extractor.py::test_extract_table -v

# Test con salida detallada
cd python-cli && pytest -v --tb=short

# Test con coverage
cd python-cli && pytest --cov=. tests/test_table_extractor.py
```

## 🛠️ Development Workflow

1. **Environment**: Both apps require a `.env` file (see `.env.example` in respective directories).
2. **Data Flow**: The scraper saves JSON files to `python-cli/boletines/`. The chatbot's RAG system consumes these files.
3. **Commit Convention**: Follow existing style (mostly Spanish/English mix, concise).
4. **Agent Rules**: Always check `.agents/` directory for detailed architecture specs before making structural changes.

## 🧪 Testing Policy

- **Chatbot**: Use `vitest`. Ensure new logic in `src/lib` has corresponding tests in `__tests__` or `src/tests/unit`.
- **Python**: Use `pytest`. Tests are located in `python-cli/tests/`.

## 📚 Documentation for Agents

### Quick Start for AI Agents

1. **Read:** [`.agents/specs/`](.agents/specs/) - Understand project architecture
2. **Follow:** [`.agents/steering/`](.agents/steering/) - Respect mandatory patterns
3. **Reference:** [`.kiro/specs/`](.kiro/specs/) - Consult for technical details (optional)

### Configuration Files

- **Claude Code:** See `.claude/CLAUDE.md`
- **Droid/Factory:** See `.factory/config.yml`
- **Coordination:** See `.agents/COORDINACION.md`

## 🎨 Code Style Guidelines

### TypeScript (Chatbot)

#### Imports

- **Order:**
  1. External libraries (node_modules)
  2. Internal modules (@/ imports)
  3. Relative imports
  4. Type-only imports

```typescript
// ✅ CORRECTO
import fs from 'fs/promises';
import path from 'path';
import { streamText } from 'ai';
import { z } from 'zod';
import type { Document } from '@/lib/types';
import { retrieveContext } from '@/lib/rag/retriever';
import type { SearchOptions } from './types';

// ❌ INCORRECTO - mezclado sin orden
import type { Document } from '@/lib/types';
import fs from 'fs/promises';
import { streamText } from 'ai';
import type { SearchOptions } from './types';
```

- **Named vs Default:**
  - Use named exports por defecto
  - Default exports solo para componentes React principales

```typescript
// ✅ CORRECTO - Named exports
export function calculateScore(): number { }
export interface SearchOptions { }
export type DocumentType = 'a' | 'b';

// ✅ CORRECTO - Default export (solo componentes React)
export default function ChatContainer() { }

// ❌ INCORRECTO - Default exports para utilidades
export default function calculateScore() { }
```

#### Formatting

- **Indentación:** 2 espacios (no tabs)
- **Semicolons:** Obligatorios
- **Quotes:** Single quotes para strings, template literals para interpolación
- **Max line length:** 100 caracteres (soft limit)

```typescript
// ✅ CORRECTO
const message = 'Hello world';
const greeting = `Hello, ${name}!`;

// ❌ INCORRECTO
const message = "Hello world";
const greeting = 'Hello, ' + name + '!';
```

#### Types

- **Interfaces vs Types:**
  - Use `interface` para objetos con propiedades
  - Use `type` para unions, tuples, primitives

```typescript
// ✅ CORRECTO
export interface SearchOptions {
  municipality?: string;
  type?: string;
  limit?: number;
}

export type DocumentType = 'ordenanza' | 'decreto' | 'resolucion';
export type SearchResult = { success: true; data: any } | { success: false; error: string };
```

- **Type Guards:** Implementar type guards para narrowing

```typescript
function isComputationalResult(result: any): result is ComputationalSearchResult {
  return result && typeof result === 'object' && 'computationResult' in result;
}
```

#### Naming Conventions

- **Variables/Functions:** camelCase
- **Constants:** UPPER_SNAKE_CASE
- **Classes:** PascalCase

```typescript
// ✅ CORRECTO
const searchResults = [];
const MAX_RESULTS = 100;
class DocumentRetriever { }
```

#### Error Handling

- **Throw custom errors** con mensajes descriptivos
- **Log errors** con contexto suficiente
- **Never swallow errors** sin logging

```typescript
// ✅ CORRECTO
class DocumentNotFoundError extends Error {
  constructor(documentId: string) {
    super(`Document not found: ${documentId}`);
  }
}

// ✅ CORRECTO - Error handling con logging
async function retrieveDocument(id: string): Promise<Document> {
  try {
    const doc = await fetchDocument(id);
    if (!doc) throw new DocumentNotFoundError(id);
    return doc;
  } catch (error) {
    console.error(`[DocumentService] Failed to retrieve ${id}:`, error);
    throw error;
  }
}
```

- **API errors** deben tener status codes apropiados

```typescript
export async function GET() {
  try {
    const data = await fetchData();
    return NextResponse.json(data);
  } catch (error) {
    console.error('[API] Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

#### Async/Await

- **Use async/await** en vez de callbacks
- **Handle Promise rejections** siempre
- **Use Promise.all** para paralelismo (no loops con await)

```typescript
// ✅ CORRECTO - Parallel loading
async function loadDocuments(ids: string[]): Promise<Document[]> {
  const documents = await Promise.all(
    ids.map(id => fetchDocument(id))
  );
  return documents.filter(doc => doc !== null);
}

// ❌ INCORRECTO - Sequential loading (slow)
async function loadDocuments(ids: string[]): Promise<Document[]> {
  const documents = [];
  for (const id of ids) {
    const doc = await fetchDocument(id);
    if (doc) documents.push(doc);
  }
  return documents;
}
```

#### Comments

- **JSDoc comments** para funciones exportadas
- **Inline comments** solo para lógica compleja
- **NO comments** para código obvio
- **Spanish/English mix** aceptado (sigue estilo del proyecto)

```typescript
/**
 * Retrieves context from documents using RAG
 * @param query - Search query string
 * @param options - Search options (municipality, type, etc.)
 * @returns Search result with context and sources
 */
export async function retrieveContext(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  // Lógica compleja: explica el porqué
  const limit = options.limit || 10; // Default 10 to balance performance
}
```

### Python (Scraper)

#### Imports

- **Order:**
  1. Standard library
  2. Third-party libraries
  3. Local modules

```python
# ✅ CORRECTO
import os
from pathlib import Path
from typing import Optional, List, Dict

import requests
from bs4 import BeautifulSoup

from .scraper import SIBOMScraper
from .utils import format_date

# ❌ INCORRECTO
from .scraper import SIBOMScraper
import os
import requests
```

#### Formatting

- **Indentación:** 4 espacios (no tabs)
- **Max line length:** 100 caracteres
- **Imports:** Cada import en una línea
- **Blank lines:** 2 entre funciones, 1 entre métodos en clases

```python
# ✅ CORRECTO
from typing import List, Optional

def scrape_bulletins(limit: Optional[int] = None) -> List[Dict]:
    """Scrape SIBOM bulletins."""
    pass

class SIBOMScraper:
    def __init__(self, url: str):
        pass

    def parse(self) -> Dict:
        pass
```

#### Type Hints

- **Obligatorias** en todas las funciones exportadas
- **Use Optional[T]** para valores opcionales

```python
# ✅ CORRECTO
def scrape_bulletins(
    url: str,
    limit: Optional[int] = None
) -> List[Dict[str, str]]:
    pass

# ❌ INCORRECTO
def scrape_bulletins(url, limit=None):
    pass
```

#### Error Handling

- **Use exceptions** para errores, no return codes
- **Log errors** con contexto
- **Custom exceptions** para dominio específico

```python
# ✅ CORRECTO
class ScrapingError(Exception):
    pass

def scrape_bulletin(url: str) -> Dict:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return parse_content(response.text)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise ScrapingError(f"Could not scrape {url}") from e
```

#### Naming Conventions

- **Variables/Functions:** snake_case
- **Constants:** UPPER_SNAKE_CASE
- **Classes:** PascalCase
- **Private methods:** prefijo `_`

```python
# ✅ CORRECTO
MAX_RETRIES = 3

class SIBOMScraper:
    def __init__(self, url: str):
        self.url = url
        self._cache = {}

    def _fetch_pages(self):
        pass
```

#### Docstrings

- **Use Google style** o NumPy style
- **Incluir:** resumen, params, returns, raises

```python
# ✅ CORRECTO - Google style
def scrape_bulletins(url: str, limit: Optional[int] = None) -> List[Dict]:
    """Scrape bulletins from SIBOM.

    Args:
        url: Base URL of SIBOM municipality page.
        limit: Maximum number of bulletins to scrape.

    Returns:
        List of bulletins with metadata.

    Raises:
        ScrapingError: If scraping fails.
    """
    pass
```

### File Organization

#### TypeScript (Chatbot)

```
src/
├── app/                    # API routes y páginas
├── components/
│   ├── chat/              # Chat components
│   ├── layout/            # Layout components
│   └── ui/                # Reusable UI components
├── lib/
│   ├── rag/               # RAG system
│   ├── computation/       # Computation engine
│   └── utils.ts           # Utility functions
├── contexts/              # React contexts
└── types.ts               # Shared types
```

#### Python (Scraper)

```
python-cli/
├── sibom_scraper.py       # Main scraper
├── build_database.py      # Database builder
├── generate_embeddings.py # Embeddings generator
├── tests/                 # Tests
│   └── test_*.py
├── data/                  # Data files
└── boletines/             # Scraped bulletins
```

## 🎯 Testing Best Practices

- **Test one thing** per test
- **Arrange-Act-Assert** pattern
- **Use descriptive names**
- **Mock external dependencies**

```typescript
// ✅ CORRECTO
describe('calculateRelevance', () => {
  it('should return 200 for exact number match', () => {
    const entry = { number: '123' };
    const query = 'ordenanza 123';
    const score = calculateRelevance(entry, query);
    expect(score).toBe(200);
  });
});
```

## 🔒 Security Guidelines

- **Never commit** secrets or API keys (use `.env`)
- **Validate all user input**
- **Use parameterized queries** to prevent SQL injection
- **Implement rate limiting** on public APIs
- **Use HTTPS** in production
- **Sanitize output** to prevent XSS

## 📊 Performance Guidelines

- **Lazy load** heavy components
- **Use memoization** (React.memo, useMemo, useCallback)
- **Implement caching**
- **Optimize images** (Next.js Image component)
- **Minimize bundle size** (tree shaking, code splitting)

## 🔄 Git Workflow

- **Branch naming:** `feature/feature-name`, `fix/bug-description`
- **Commit messages:** `type: description` (ej: `feat: add vector search`)
- **Create PR** for all changes (no direct pushes to main)

## 📝 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vitest Guide](https://vitest.dev/guide/)
- [Python Documentation](https://docs.python.org/3/)

---

**For complete documentation, see:** [`.agents/README.md`](.agents/README.md)
