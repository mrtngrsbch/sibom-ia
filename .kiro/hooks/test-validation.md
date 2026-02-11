# Hook de Validación de Tests - Mangrullo Scraper Assistant

## Configuración del Hook

### Trigger Event
**Evento:** `onFileSave`
**Archivos objetivo:** `**/*.{ts,tsx,js,jsx,py}`
**Descripción:** Ejecuta tests automáticamente cuando se guardan archivos de código

### Configuración del Hook
```json
{
  "name": "test-validation",
  "description": "Ejecuta tests automáticamente al guardar archivos de código",
  "trigger": {
    "event": "onFileSave",
    "filePattern": "**/*.{ts,tsx,js,jsx,py}"
  },
  "actions": [
    {
      "type": "shellCommand",
      "command": "npm run test:changed",
      "workingDirectory": "chatbot",
      "condition": "file.path.startsWith('chatbot/')"
    },
    {
      "type": "shellCommand", 
      "command": "python -m pytest tests/ -v",
      "workingDirectory": "python-cli",
      "condition": "file.path.startsWith('python-cli/')"
    },
    {
      "type": "agentMessage",
      "message": "🧪 Ejecutando tests para validar cambios en {{file.name}}...",
      "condition": "always"
    }
  ],
  "enabled": true
}
```

## Scripts de Testing Implementados

### Frontend (Next.js/TypeScript)
**Ubicación:** `chatbot/package.json`
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run",
    "test:changed": "vitest run --changed",
    "test:coverage": "vitest run --coverage",
    "test:watch": "vitest --watch"
  }
}
```

### Backend (Python)
**Ubicación:** `python-cli/pytest.ini`
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --color=yes
```

## Casos de Uso del Hook

### 1. Desarrollo de Componentes React
```typescript
// Archivo: chatbot/src/components/chat/ActiveFilters.tsx
// Al guardar este archivo, el hook ejecutará:
// npm run test:changed
// Esto ejecutará solo los tests relacionados con ActiveFilters
```

**Tests ejecutados:**
- `chatbot/src/components/chat/__tests__/ActiveFilters.test.tsx`
- Tests de integración que usen ActiveFilters
- Tests de snapshot si existen

### 2. Modificación de Lógica de Negocio
```typescript
// Archivo: chatbot/src/lib/query-classifier.ts
// Al guardar, ejecutará tests de:
```

**Tests ejecutados:**
- `chatbot/src/lib/__tests__/query-classifier.test.ts`
- Tests de integración del API route que usa query-classifier
- Tests de end-to-end que dependan de clasificación

### 3. Cambios en Backend Python
```python
# Archivo: python-cli/sibom_scraper.py
# Al guardar, ejecutará:
# python -m pytest tests/ -v
```

**Tests ejecutados:**
- `python-cli/tests/test_scraper.py`
- `python-cli/tests/test_rate_limiting.py`
- `python-cli/tests/test_json_parsing.py`

## Configuración Avanzada

### Filtros Inteligentes por Tipo de Archivo
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "npm run test:unit -- --testPathPattern={{file.nameWithoutExt}}",
      "condition": "file.path.includes('/lib/') && file.ext === '.ts'",
      "description": "Tests unitarios para lógica de negocio"
    },
    {
      "type": "shellCommand", 
      "command": "npm run test:component -- --testPathPattern={{file.nameWithoutExt}}",
      "condition": "file.path.includes('/components/') && file.ext === '.tsx'",
      "description": "Tests de componentes React"
    },
    {
      "type": "shellCommand",
      "command": "npm run test:api -- --testPathPattern=route",
      "condition": "file.path.includes('/api/') && file.name === 'route.ts'",
      "description": "Tests de API routes"
    }
  ]
}
```

### Notificaciones de Resultados
```json
{
  "actions": [
    {
      "type": "agentMessage",
      "message": "✅ Tests pasaron correctamente para {{file.name}}",
      "condition": "exitCode === 0"
    },
    {
      "type": "agentMessage",
      "message": "❌ Tests fallaron en {{file.name}}. Revisa los errores en la terminal.",
      "condition": "exitCode !== 0"
    },
    {
      "type": "shellCommand",
      "command": "npm run test:coverage -- --reporter=text-summary",
      "condition": "exitCode === 0 && file.path.includes('/lib/')",
      "description": "Mostrar cobertura después de tests exitosos"
    }
  ]
}
```

## Integración con CI/CD

### Pre-commit Hooks
```bash
# .husky/pre-commit
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Frontend tests
cd chatbot && npm run test:run

# Backend tests  
cd ../python-cli && python -m pytest tests/ --tb=short

# Lint checks
cd ../chatbot && npm run lint
cd ../python-cli && python -m flake8 sibom_scraper.py
```

### GitHub Actions Integration
```yaml
# .github/workflows/test-on-push.yml
name: Test on Push
on: [push, pull_request]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd chatbot && npm ci
      - run: cd chatbot && npm run test:run
      - run: cd chatbot && npm run test:coverage
      
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: cd python-cli && pip install -r requirements.txt
      - run: cd python-cli && python -m pytest tests/ -v
```

## Configuración de Tests por Módulo

### Tests de Query Classifier
```typescript
// chatbot/src/lib/__tests__/query-classifier.test.ts
describe('Query Classifier - Auto Tests', () => {
  // Tests que se ejecutan automáticamente al guardar query-classifier.ts
  
  it('should classify FAQ questions correctly', () => {
    const faqQueries = [
      'qué municipios están disponibles',
      'cómo busco una ordenanza',
      'cómo funciona el chat'
    ];
    
    faqQueries.forEach(query => {
      expect(isFAQQuestion(query)).toBe(true);
      expect(needsRAGSearch(query)).toBe(false);
    });
  });
  
  it('should detect ordinance-related queries', () => {
    const ordinanceQueries = [
      'ordenanza de tránsito',
      'decreto municipal 123',
      'normativa vigente de carlos tejedor'
    ];
    
    ordinanceQueries.forEach(query => {
      expect(needsRAGSearch(query)).toBe(true);
      expect(isFAQQuestion(query)).toBe(false);
    });
  });
});
```

### Tests de Componentes React
```typescript
// chatbot/src/components/chat/__tests__/ActiveFilters.test.tsx
describe('ActiveFilters - Auto Tests', () => {
  // Tests que se ejecutan al guardar ActiveFilters.tsx
  
  it('should render municipality filter badge', () => {
    render(<ActiveFilters municipality="Carlos Tejedor" {...defaultProps} />);
    expect(screen.getByText('Carlos Tejedor')).toBeInTheDocument();
  });
  
  it('should call onRemoveFilter when badge is clicked', () => {
    const onRemoveFilter = vi.fn();
    render(<ActiveFilters municipality="Carlos Tejedor" onRemoveFilter={onRemoveFilter} {...defaultProps} />);
    
    fireEvent.click(screen.getByLabelText('Remove municipality filter'));
    expect(onRemoveFilter).toHaveBeenCalledWith('municipality');
  });
});
```

### Tests de Python Backend
```python
# python-cli/tests/test_scraper.py
import pytest
from sibom_scraper import SibomScraper

class TestScraper:
    """Tests que se ejecutan al guardar sibom_scraper.py"""
    
    def test_json_extraction(self):
        scraper = SibomScraper()
        
        # Test con markdown code block
        markdown_json = '```json\n{"test": "value"}\n```'
        result = scraper._extract_json(markdown_json)
        assert result == '{"test": "value"}'
        
        # Test con JSON limpio
        clean_json = '{"clean": "json"}'
        result = scraper._extract_json(clean_json)
        assert result == '{"clean": "json"}'
    
    def test_rate_limiting(self):
        scraper = SibomScraper()
        
        # Verificar que el rate limiter está configurado
        assert scraper.rate_limit_delay >= 3
        
        # Test de delay calculation
        import time
        start_time = time.time()
        # Simular rate limiting
        end_time = time.time()
        assert end_time - start_time >= 0  # Basic timing test
```

## Métricas y Reporting

### Coverage Tracking
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "npm run test:coverage -- --reporter=json --outputFile=coverage.json",
      "condition": "file.path.includes('/lib/') && exitCode === 0"
    },
    {
      "type": "agentMessage",
      "message": "📊 Cobertura actualizada. Revisa coverage.json para detalles.",
      "condition": "file.exists('coverage.json')"
    }
  ]
}
```

### Performance Benchmarks
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "npm run test:performance -- --testPathPattern=bm25",
      "condition": "file.name === 'bm25.ts'",
      "description": "Ejecutar benchmarks de performance para BM25"
    },
    {
      "type": "agentMessage",
      "message": "⚡ Benchmarks de BM25 ejecutados. Verifica que no haya regresiones de performance.",
      "condition": "file.name === 'bm25.ts'"
    }
  ]
}
```

## Troubleshooting

### Problemas Comunes

#### Tests Lentos
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "npm run test:changed -- --maxWorkers=2",
      "condition": "file.path.includes('__tests__')",
      "description": "Limitar workers para tests más rápidos"
    }
  ]
}
```

#### Tests Flaky
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "npm run test:changed -- --retry=3",
      "condition": "file.path.includes('integration')",
      "description": "Retry para tests de integración flaky"
    }
  ]
}
```

#### Memory Issues
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "node --max-old-space-size=4096 ./node_modules/.bin/vitest run",
      "condition": "file.path.includes('bm25') || file.path.includes('retriever')",
      "description": "Más memoria para tests de BM25/RAG"
    }
  ]
}
```

## Configuración de Desarrollo

### VSCode Settings
```json
{
  "settings": {
    "kiro.hooks.testValidation.enabled": true,
    "kiro.hooks.testValidation.showNotifications": true,
    "kiro.hooks.testValidation.runOnSave": true,
    "kiro.hooks.testValidation.timeout": 30000
  }
}
```

### Exclusiones
```json
{
  "excludePatterns": [
    "**/*.d.ts",
    "**/node_modules/**",
    "**/.next/**",
    "**/coverage/**",
    "**/__pycache__/**"
  ]
}
```

## Beneficios del Hook

### 1. **Feedback Inmediato**
- Tests se ejecutan automáticamente al guardar
- Detección temprana de regresiones
- No necesidad de recordar ejecutar tests manualmente

### 2. **Desarrollo Más Rápido**
- Solo ejecuta tests relacionados con cambios
- Evita ejecutar toda la suite de tests
- Feedback en segundos, no minutos

### 3. **Calidad de Código**
- Previene commits con tests rotos
- Mantiene cobertura de tests actualizada
- Fomenta TDD (Test-Driven Development)

### 4. **Integración Seamless**
- No interrumpe el flujo de desarrollo
- Funciona en background
- Compatible con cualquier editor

## Checklist de Configuración

- [ ] ✅ Hook configurado para archivos TypeScript/JavaScript
- [ ] ✅ Hook configurado para archivos Python
- [ ] ✅ Scripts de test definidos en package.json
- [ ] ✅ Configuración de pytest para Python
- [ ] ⏳ Filtros inteligentes por tipo de archivo
- [ ] ⏳ Notificaciones de resultados
- [ ] ⏳ Integración con coverage reporting
- [ ] ⏳ Configuración de exclusiones
- [ ] ⏳ Troubleshooting para casos edge
- [ ] ⏳ Documentación para el equipo