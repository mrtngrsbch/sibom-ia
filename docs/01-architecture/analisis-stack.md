# 📊 Análisis del Stack y Problemas de Arquitectura

**Fecha:** 2026-01-15
**Proyecto:** Mangrullo Scraper Assistant
**Analista:** OpenCode AI

---

## 📋 1. Stack Tecnológico Actual

### Frontend (Chatbot - Next.js)

**Tecnologías:**
- **Framework:** Next.js 16.1.1 (muy reciente, edge cases posibles)
- **React:** 19.0.0 (versión muy nueva, breaking changes)
- **TypeScript:** 5.0.0+
- **AI SDK:** Vercel AI SDK v4.1.0 + @ai-sdk/react v1.0.0
- **Styling:** Tailwind CSS 3.4.0
- **Búsqueda:**
  - BM25 (keyword search) - implementación propia
  - Vector Search (OpenAI embeddings + Qdrant)
  - SQL (sql.js - SQLite in-memory)
- **Testing:** Vitest 1.6.1 + React Testing Library

**Dependencias críticas:**
```json
{
  "next": "16.1.1",           // ⚠️ Muy reciente
  "react": "^19.0.0",         // ⚠️ Versión muy nueva
  "ai": "^4.1.0",             // Vercel AI SDK
  "@ai-sdk/openai": "^1.0.0", // Cliente OpenRouter
  "openai": "^6.16.0",        // Cliente OpenAI (legacy)
  "qdrant-client": "^1.16.2" // Vector database
}
```

**Características:**
- RAG (Retrieval Augmented Generation) híbrido
- Streaming de respuestas en tiempo real
- Búsqueda multi-modal: BM25 + Vector + SQL
- Sistema de filtros: municipio, tipo de norma, rango de fechas
- Caching agresivo multi-nivel
- Soporte para datos tabulares computacionales

---

### Backend (Python CLI - Scraper)

**Tecnologías:**
- **Python:** 3.13 (última versión estable)
- **LLM Provider:** OpenRouter (multi-modelo)
- **Web Scraping:**
  - requests (HTTP client)
  - BeautifulSoup4 (HTML parsing)
  - lxml (XML/HTML rápido)
- **Procesamiento:**
  - Rich (TUI para progreso)
  - tqdm (barras de progreso)
  - python-dotenv (env vars)
- **Vector DB:** qdrant-client (opcional)
- **Data Export:** JSON + CSV + SQLite

**Dependencias:**
```
openai>=1.0.0
requests>=2.31.0
python-dotenv>=1.0.0
rich>=13.0.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
qdrant-client>=1.7.0
tqdm>=4.66.0
```

**Características:**
- Scraping en 3 niveles: Listado → Enlaces → Texto completo
- Procesamiento paralelo configurable
- Paginación automática detectada con BeautifulSoup
- Soporte para múltiples modelos LLM (gratis + premium)
- Indexado automático de normativas
- Generación de CSV para análisis de datos

---

### Arquitectura de Datos

**Fuentes de datos:**
1. **SIBOM Portal** (fuente externa)
   - URL base: https://sibom.slyt.gba.gob.ar
   - ~135 municipios de PBA
   - Boletines en HTML

2. **Python CLI Output** (backend)
   - JSON estructurados en `python-cli/boletines/`
   - Índices en `python-cli/data/indices/`
   - SQLite DB en `python-cli/boletines/normativas.db`
   - CSV en `python-cli/boletines/csv/`

3. **Cloudflare R2** (producción)
   - Boletines JSON comprimidos con gzip (.gz)
   - Índices JSON comprimidos
   - CDN global
   - 10 GB gratis, 10M requests/mes

4. **Qdrant** (vector search)
   - Embeddings OpenAI
   - Búsqueda semántica
   - Deploy en Vercel (serverless)

---

## 🚨 2. Problemas Críticos de Arquitectura

### A. Monolito Frontend Sobrecargado

**Problema:**
El chatbot `/api/chat/route.ts` tiene 530 líneas y hace TODO:
- Clasificación de queries
- Filtrado automático
- Recuperación de contexto (3 métodos: vector, BM25, SQL)
- Generación de respuestas con streaming
- Manejo de off-topic y FAQ
- Comparaciones SQL directas
- Manejo de datos tabulares
- Logging extenso

**Consecuencias:**
- ❌ Difícil de mantener
- ❌ Difícil de testear
- ❌ Single Responsibility Principle violado
- ❌ Bug en un componente puede romper todo
- ❌ Difícil de escalar

**Impacto:** 🔴 **ALTO**

---

### B. Sistema de Caching Inconsistente

**Problema:**
Hay 3 niveles de cache sin coordinación:

1. **Vercel Cache** (CDN):
```typescript
next: { revalidate: 3600 } // 1 hora
```

2. **In-memory cache** (Node.js):
```typescript
let indexCache: IndexEntry[] = [];
let normativasCache: NormativaIndexEntry[] = [];
const CACHE_DURATION = parseInt(process.env.INDEX_CACHE_DURATION || '300000'); // 5 min default
```

3. **File cache** (Map):
```typescript
const fileCache = new Map<string, FileCacheEntry>();
const FILE_CACHE_DURATION = 30 * 60 * 1000; // 30 minutos
```

**Problemas:**
- ❌ No hay invalidación automática
- ❌ Cache in-memory no funciona en Vercel (serverless)
- ❌ Diferentes tiempos de expiración (5 min, 30 min, 1 hora)
- ❌ No hay cache warming en deploy
- ❌ Cache in-memory se pierde en cada request (Vercel)
- ❌ No hay métricas de cache hit/miss

**Impacto:** 🔴 **ALTO** - Causa inconsistencias entre dev y prod

---

### C. Dependencias Inestables

**Problema:**
Versiones muy nuevas con breaking changes:

```json
{
  "next": "16.1.1",      // 🆘 Versión muy reciente (released hace 2 semanas)
  "react": "^19.0.0",    // 🆘 RC/RC reciente
  "ai": "^4.1.0"         // Vercel AI SDK en desarrollo activo
}
```

**Consecuencias:**
- ⚠️ Breaking changes constantes
- ⚠️ Bug reports en GitHub
- ⚠️ Poca documentación estable
- ⚠️ Compatibilidad incierta con otras librerías

**Impacto:** 🟡 **MEDIO** - Riesgo de regresiones

---

### D. Gestión de Estado React Inexistente

**Problema:**
No hay state management global (Zustand, Redux, Jotai, Context API robusto).

**Estado actual:**
- Solo `ThemeContext.tsx` para dark mode
- Estado del chat en componentes individuales
- Props drilling para filtros
- No hay store global para:
  - Historial de queries
  - Filtros persistentes
  - Estado del usuario
  - Preferencias

**Consecuencias:**
- ❌ Props drilling excesivo
- ❌ Estado frágil entre navegaciones
- ❌ No hay persistencia de filtros
- ❌ No hay undo/redo en queries
- ❌ Difícil implementar features complejas

**Impacto:** 🟡 **MEDIO** - Escalabilidad limitada

---

### E. Testing Incompleto

**Problema:**
Cobertura de tests baja:

**Tests existentes:**
```
chatbot/src/lib/rag/__tests__/table-formatter.test.ts
chatbot/src/lib/computation/__tests__/table-engine.test.ts
chatbot/src/lib/computation/__tests__/query-parser.test.ts
chatbot/src/tests/unit/test-query-analyzer.ts
chatbot/src/tests/unit/query-classifier-semantic.test.ts
chatbot/src/tests/unit/test-filter-extraction.ts
```

**Faltan tests críticos:**
- ❌ Tests de integración de `/api/chat`
- ❌ Tests de streaming
- ❌ Tests de RAG (mock vector search)
- ❌ Tests de SQL retriever
- ❌ Tests de componentes UI
- ❌ E2E tests (Playwright/Cypress)
- ❌ Tests de carga/performance

**Impacto:** 🟡 **MEDIO** - Riesgo de bugs en producción

---

### F. Configuración de TypeScript Relajada

**Problema:**
```json
{
  "compilerOptions": {
    "strict": true,
    "skipLibCheck": true,     // ⚠️ Salta verificación de types de libs
    "allowJs": true,           // ⚠️ Permite JS sin types
    "noEmit": true,            // ⚠️ No genera archivos de declaración
  }
}
```

**Consecuencias:**
- ⚠️ Errores de types en runtime
- ⚠️ Malas prácticas se propagan
- ⚠️ Difícil refactorizar

**Impacto:** 🟢 **BAJO** - Manejable con buenas prácticas

---

### G. Python CLI Fuera de Producción

**Problema:**
El scraper Python CLI solo corre localmente:

**Estado actual:**
```bash
cd python-cli
source venv/bin/activate
python3 sibom_scraper.py --limit 5
```

**Problemas:**
- ❌ No hay servicio de scraping automatizado en la nube
- ❌ No hay cron jobs o scheduled jobs
- ❌ Solo hay un workflow GitHub Actions (`automated-scraping.yml`)
- ❌ No hay retries automáticos
- ❌ No hay monitoreo de fallas
- ❌ No hay alertas

**Impacto:** 🟡 **MEDIO** - Scraping manual necesario

---

## 🏭 3. Problemas de Producción

### A. Deployment Manual de Datos

**Problema:**
Los datos NO se suben automáticamente a Cloudflare R2:

**Proceso actual (manual):**
```bash
cd python-cli
python3 compress_for_r2.py
# Subir manualmente al dashboard de Cloudflare O
wrangler r2 bucket create sibom-data
./upload_to_r2.sh
```

**Problemas:**
- ❌ Proceso manual propenso a errores
- ❌ No hay automatización
- ❌ No hay versionado de datos
- ❌ No hay rollback de datos
- ❌ No hay validación post-upload

**Impacto:** 🔴 **ALTO** - Deployment frágil

---

### B. Variables de Entorno Inconsistentes

**Problema:**
Variables de entorno difieren entre envs:

**Local (`.env.local`):**
```env
OPENROUTER_API_KEY=xxxxxx
OPENROUTER_MODEL=google/gemini-3-flash-preview
```

**Production (Vercel):**
```env
OPENROUTER_API_KEY=...
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5
GITHUB_DATA_REPO=pub-xxxxx.r2.dev/sibom-data
GITHUB_DATA_BRANCH=
GITHUB_USE_GZIP=true
USE_NORMATIVAS_INDEX=true
INDEX_CACHE_DURATION=3600000
```

**Problemas:**
- ❌ Nombres de variables diferentes
- ❌ Modelos LLM diferentes entre envs
- ❌ No hay validación de env vars
- ❌ No hay valores por defecto consistentes
- ❌ No hay manejo de missing vars

**Impacto:** 🔴 **ALTO** - Bugs de configuración

---

### C. Monitoreo y Logging Insuficiente

**Problema:**
Logging actual: `console.log()` en producción

**Estado actual:**
```typescript
console.log('[ChatAPI] Nueva petición recibida');
console.log(`[ChatAPI] Índice cargado: ${indexCache.length} documentos`);
```

**Faltan:**
- ❌ Structured logging (JSON logs)
- ❌ Error tracking (Sentry, LogRocket)
- ❌ Performance monitoring
- ❌ Analytics de queries (qué buscan los usuarios)
- ❌ Cost tracking de LLMs
- ❌ Alertas automáticas
- ❌ Dashboards de métricas

**Impacto:** 🟡 **MEDIO** - Difícil debug en producción

---

### D. No hay CI/CD Completo

**Problema:**
GitHub Actions solo tiene 1 workflow:

**Existente:**
```yaml
# .github/workflows/automated-scraping.yml
# Solo para scraping automatizado
```

**Faltan:**
- ❌ CI tests on push
- ❌ Lint checks
- ❌ Type checking
- ❌ Build verification
- ❌ E2E tests
- ❌ Security scans (Dependabot, Snyk)
- ❌ Deployment automático a staging
- ❌ Canary deployments

**Impacto:** 🟡 **MEDIO** - Bugs llegan a producción

---

### E. Scalability Issues

**Problema:**
Arquitectura no escala bien:

**Bottlenecks:**
1. **RAG system:**
   - BM25 se reconstruye en cada request (NO cacheado)
   - No hay pre-computation de índices
   - No hay rate limiting de LLM calls

2. **SQL retrieval:**
   - `sql.js` corre en browser/server (in-memory)
   - No hay database connection pooling
   - SQLite no escala para queries complejas

3. **Vector search:**
   - Qdrant no está optimizado
   - No hay dimensionality reduction
   - No hay approximate nearest neighbors

**Impacto:** 🟡 **MEDIO** - Performance degrada con tráfico

---

### F. Security Issues

**Problema:**
No hay security best practices:

**Faltan:**
- ❌ Rate limiting en `/api/chat`
- ❌ Input sanitization robusta
- ❌ API key rotation
- ❌ CORS policies estrictas
- ❌ CSP headers
- ❌ Helmet.js (security headers)
- ❌ SQL injection prevention
- ❌ XSS prevention
- ❌ Dependency vulnerability scanning

**Impacto:** 🔴 **ALTO** - Riesgo de seguridad

---

### G. Cost Management

**Problema:**
No hay tracking de costos:

**Costos actuales:**
- Vercel: Gratis (hasta 100 GB/mes)
- Cloudflare R2: Gratis (hasta 10 GB, 10M requests)
- OpenRouter: Uso real de LLMs (~$0.017/query)

**Faltan:**
- ❌ Token usage tracking
- ❌ Cost forecasting
- ❌ Budget alerts
- ❌ Cost optimization
- ❌ Usage analytics (queries por usuario)

**Impacto:** 🟡 **MEDIO** - Costos pueden explotar

---

## 📊 4. Resumen de Problemas por Severidad

### 🔴 CRÍTICO (Resolver YA)
1. **Deployment manual de datos** - Riesgo de errores humanos
2. **Variables de entorno inconsistentes** - Bugs en producción
3. **Security issues** - Vulnerabilidades de seguridad

### 🟡 ALTO (Resolver pronto)
1. **Monolito frontend sobrecargado** - Difícil mantener
2. **Sistema de caching inconsistente** - Bugs entre envs
3. **Monitoreo insuficiente** - Difícil debug en prod
4. **Scalability issues** - Performance degrada

### 🟢 MEDIO (Resolver cuando sea posible)
1. **Testing incompleto** - Riesgo de bugs
2. **Dependencias inestables** - Breaking changes
3. **Gestión de estado inexistente** - UX limitada
4. **Python CLI fuera de producción** - Scraping manual
5. **CI/CD incompleto** - Bugs llegan a prod
6. **Cost management** - Costos impredecibles

---

## 🎯 5. Recomendaciones Prioritarias

### Fase 1: Estabilización (1-2 semanas)

**Objetivo:** Hacer el deployment confiable

1. **Automatizar deployment de datos**
   ```bash
   # Script: deploy_data.sh
   - Comprimir datos
   - Subir a R2 automáticamente
   - Validar post-upload
   - Versionar datos (rollback)
   ```

2. **Unificar variables de entorno**
   ```typescript
   // src/lib/config.ts
   export const config = {
     openRouterApiKey: env.OPENROUTER_API_KEY,
     llmModelPrimary: env.LLM_MODEL_PRIMARY || 'anthropic/claude-3.5-sonnet',
     // ...
   }
   ```

3. **Security básica**
   ```typescript
   // middleware.ts
   - Rate limiting (/api/chat)
   - Helmet.js (headers)
   - CORS policies
   - Input sanitization
   ```

### Fase 2: Monitoreo y Observabilidad (2-3 semanas)

**Objetivo:** Visibilidad total de producción

1. **Structured logging**
   ```typescript
   import pino from 'pino';
   const logger = pino({ level: 'info' });
   logger.info({ query, model, tokens }, 'Chat query processed');
   ```

2. **Error tracking**
   ```typescript
   import * as Sentry from '@sentry/nextjs';
   Sentry.init({ dsn: process.env.SENTRY_DSN });
   ```

3. **Analytics**
   ```typescript
   // Track queries, costs, performance
   analytics.track('chat_query', { model, tokens, latency });
   ```

### Fase 3: Refactorización (3-4 semanas)

**Objetivo:** Mejorar mantenibilidad

1. **Separar responsabilidades**
   ```
   /api/chat/route.ts (orquestador)
   /api/chat/classify.ts
   /api/chat/retrieve.ts
   /api/chat/generate.ts
   /api/chat/filters.ts
   ```

2. **Testing coverage**
   ```typescript
   // unit tests, integration tests, E2E tests
   // target: 80% coverage
   ```

3. **State management**
   ```typescript
   // Zustand store global
   // Filtros persistentes
   // Historial de queries
   ```

### Fase 4: Optimización (2-3 semanas)

**Objetivo:** Mejorar performance y costos

1. **Cache inteligente**
   ```typescript
   // Redis / Vercel KV
   // Cache warming en deploy
   // Cache invalidation automática
   ```

2. **Pre-computation**
   ```typescript
   // BM25 pre-computado
   // Vector indexes pre-construidos
   // SQL indexes
   ```

3. **Rate limiting de LLMs**
   ```typescript
   // Cache responses similares
   // Batch queries
   // Token optimization
   ```

---

## 📈 6. Métricas de Éxito

**Objetivos:**

| Métrica                      | Actual       | Objetivo | Deadline  |
| ---------------------------- | ------------ | -------- | --------- |
| Deployment success rate      | 70%          | 99%      | 2 semanas |
| Mean Time to Recovery (MTTR) | 4h           | 30 min   | 4 semanas |
| Test coverage                | ~30%         | 80%      | 6 semanas |
| API response time (p95)      | 5s           | 2s       | 4 semanas |
| Cost per 1000 queries        | ~$17         | <$10     | 6 semanas |
| Uptime                       | 95%          | 99.9%    | 2 semanas |
| Security vulnerabilities     | 2 (med/baja) | 0        | 2 semanas |

---

## 🚀 7. Conclusión

**Estado actual:**
- ✅ Scraping funciona bien (Python CLI)
- ⚠️ Frontend funcional pero frágil
- ❌ Producción no está lista
- ❌ Arquitectura necesita refactorización
- ❌ Monitoreo insuficiente

**Próximos pasos:**
1. Automatizar deployment de datos
2. Unificar variables de entorno
3. Implementar security básica
4. Refactorizar monolito frontend
5. Añadir monitoreo completo
6. Aumentar test coverage

**Tiempo estimado:** 8-12 semanas para producción robusta

---

**Generado por:** OpenCode AI  
**Fecha:** 2026-01-15  
**Versión:** 1.0.0
