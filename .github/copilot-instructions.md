# SIBOM IA - Agent Instructions

**Stack Actual (2026-02)**: Gemini 3 Flash + GLM 4.7, Qdrant, Next.js 16, React 19, pnpm, FastAPI

## 🚨 CRITICAL: Coding Standards & Steering

**Copilot MUST strictly follow the specialized patterns defined in `.agents/steering/`:**

- **TypeScript/React**: [`.agents/steering/typescript-patterns.md`](../.agents/steering/typescript-patterns.md)
  - *Key Rules*: No `any`, strict null checks, Zod for env vars, NO Server Actions (use API Routes).
- **Python**: [`.agents/steering/python-patterns.md`](../.agents/steering/python-patterns.md)
  - *Key Rules*: Type hints everywhere, Pydantic models, context managers for resources.
- **Git Workflow**: [`.agents/steering/git-workflow.md`](../.agents/steering/git-workflow.md)
  - *Key Rules*: Conventional Commits, atomic changes.

---

## 🏗️ Arquitectura de 3 Componentes

### 1. Python CLI (`python-cli/`) - Scraper + Indexación

Extrae boletines oficiales municipales desde SIBOM usando LLMs y genera índices estructurados.

**Tech**: Python 3.13, OpenRouter API, SQLite, Vision API (poppler)

**Comandos principales**:

```bash
cd python-cli
source .venv/bin/activate
python cli.py sibom --municipality "Carlos Tejedor" --limit 5
python cli.py transparency --municipality "X" --category balances
python cli.py db --stats  # Ver estadísticas SQLite
```

**Outputs**:

- JSON individuales en `boletines/{Municipio}/`
- Índices JSON en `data/indexes/` (boletines_index.json, normativas_index\*.json)
- DB SQLite en `data/indexes/sibom.db` (216K+ normativas)

### 2. Sat-Analysis (`sat-analysis/`) - API Satelital

Backend FastAPI para análisis de imágenes Sentinel-2, detección de anegamiento/salinización.

**Tech**: FastAPI, Microsoft Planetary Computer, STAC

**Running**:

```bash
cd sat-analysis
source .venv/bin/activate
uvicorn api.main:app --reload --port 8001
```

**Outputs**: 8 tipos de imágenes (RGB, clasificación, 6 índices espectrales: NDWI, MNDWI, NDVI, NDMI, NDSI, SWIR2+NIR)

### 3. Chatbot (`chatbot/`) - Frontend Next.js + RAG

Chat con búsqueda semántica sobre normativas municipales + visualización de análisis satelital.

**Tech**: Next.js 16, React 19, TypeScript, Vercel AI SDK, pnpm, Qdrant, BM25

**Running**:

```bash
cd chatbot
pnpm install
pnpm run dev
# Abre http://localhost:3000
```

**Deployment**: Vercel con instalación vía pnpm

## 🤖 Active Agents

The `.agents/` folder contains autonomous agents and tooling:

- **Commit Agent**: [`.agents/agents/commit-agent.yaml`](../.agents/agents/commit-agent.yaml)
  - Automatically generates Conventional Commits messages.
  - Script: `.agents/scripts/commit_agent.py`
- **RAG Indexer**: [`.agents/agents/rag-indexer.yaml`](../.agents/agents/rag-indexer.yaml)
  - Handles ingestion from R2 to Qdrant.

## 🔑 Convenciones del Proyecto

### File Structure Patterns

- **Normativas individuales**: `{Municipio}_{tipo}_{numero}_{año}_*.json`
  - Ejemplo: `Carlos_Tejedor_Ordenanza_1234_2024_Boletin_5678.json`
- **Balances**: `{Municipio}_Balances_YYYYMMDD_HHMMSS.json` (uno por PDF)
- **Índices RAG**: `python-cli/data/indexes/*.json` (no cambiar ubicación)

### Naming Conventions

- **DocumentType**: `'ordenanza' | 'decreto' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion' | 'balances' | 'presupuestos'`
- **Índices abreviados**: `NormativaIndexEntry` usa campos cortos (`m`, `t`, `n`, `y`, `d`, `ti`, `sb`) para reducir tamaño
- **Config files**: `.env` en raíz (compartido), `.env.local` en chatbot (Next.js)

### Data Flow

```
SIBOM scraper → JSON files → Índices JSON/SQLite → RAG retriever → LLM → Streaming response
                                                  ↓
                                            Qdrant (opcional)
```

### Critical Integration Points

**RAG System** (`chatbot/src/lib/rag/`):

- `retriever.ts`: Motor principal, lee índices desde `python-cli/data/indexes/`
- `bm25.ts`: Búsqueda por keywords (tokenización: lowercase, acentos)
- `vector-search.ts`: Embeddings con Qdrant (desactivado si `QDRANT_URL` vacío)
- `sql-retriever.ts`: Consultas SQL directas para comparaciones/agregaciones

**Query Classification** (`chatbot/src/lib/query-classifier.ts`):

- Detecta si query necesita RAG, es FAQ, o off-topic
- Calcula límite óptimo de resultados: 3-5 (normal), 10-15 (con filtros), 20-30 (comparaciones)

**API Chat** (`chatbot/src/app/api/chat/route.ts`):

- Endpoint: `POST /api/chat`
- Integration: OpenRouter → Vercel AI SDK → Streaming response
- Incluye metadatos de fuentes + timestamps

**Satellite API** (`sat-analysis/api/main.py`):

- Endpoint principal: `POST /api/analyze`
- CORS habilitado para `localhost:3000` + `sibom-assistant.vercel.app`
- Outputs en `/web_output` (local) o `/app/data` (producción)

## 🚀 Development Workflows

### Start Full Stack (Recommended)

```bash
./scripts/dev.sh  # Usa Overmind para gestionar servicios
# Inicia: sat-analysis (8001) + chatbot (3000)
```

### Manual Start

```bash
# Terminal 1: Backend
cd sat-analysis && source .venv/bin/activate && uvicorn api.main:app --reload --port 8001

# Terminal 2: Frontend
cd chatbot && pnpm run dev
```

### Testing

```bash
# Chatbot tests
cd chatbot && pnpm run test  # Vitest

# Python CLI (no tiene tests formales, usar scripts)
cd python-cli && python cli.py sibom --limit 1 --municipality "Azul"
```

### Scraping + Indexing Workflow

1. **Scrape**: `python cli.py sibom --all --limit 10` → genera JSON en `boletines/`
2. **Index**: Automático (índices actualizados on-the-fly)
3. **Verify**: `python cli.py db --stats` (ver cantidad de normativas indexadas)
4. **Use**: Chatbot lee automáticamente los índices actualizados

### Docker Deployment

```bash
docker-compose up -d  # Inicia todos los servicios
# Chatbot: localhost:3000
# Sat-Analysis: localhost:8001
# Qdrant (si configurado): localhost:6333
```

## 📂 Key Files Reference

### Must-Read for Context

- `README.md`: Overview + estado actual del proyecto
- `python-cli/CLAUDE.md`: Comandos Python CLI + opciones
- `chatbot/README.md`: Stack del frontend + características
- **Coding Standards**: `.agents/steering/*.md`

### LLM Configuration

- **Env vars**: `LLM_MODEL_PRIMARY`, `LLM_MODEL_ECONOMIC` (en `.env`)
- **Default models**: `google/gemini-3-flash-preview` (primary), `zai/glm-4.7` (economic)
- **API**: OpenRouter (todos los modelos)

### RAG Implementation Details

- **BM25 tokenization**: `tokenize()` normaliza lowercase + quita acentos (importante para español)
- **Vector search**: Opcional (requiere `QDRANT_URL` + `OPENAI_API_KEY` para embeddings)
- **Hybrid search**: BM25 + Vector (si Qdrant disponible) → Rerank por score
- **Content limits**: Dynamic según tipo de query (3-30 resultados)

### Table Extraction

- **Python CLI**: `table_extractor.py` usa Vision API + regex para tablas complejas
- **Formatters**: `chatbot/src/lib/rag/table-formatter.ts` convierte tablas a markdown
- **Filtering**: `filterRelevantTables()` usa keywords para reducir ruido

## 🔧 Specific Patterns

### Error Handling: OpenRouter API

```typescript
// En route.ts: Siempre verificar API key antes de crear provider
const apiKey = process.env.OPENROUTER_API_KEY;
if (!apiKey) {
  return new Response(JSON.stringify({ error: "Falta API Key" }), {
    status: 500,
  });
}
```

### Streaming Response Pattern

```typescript
// Usar streamText() de Vercel AI SDK
return streamText({
  model: openrouter(modelName),
  system: systemPrompt,
  messages: relevantMessages,
  maxTokens: 4000,
  temperature: 0.1,
});
```

### Date Parsing (Spanish Format)

```typescript
// Siempre usar date-fns con formato DD/MM/YYYY
import { parse, isValid } from "date-fns";
const parsed = parse(dateString, "dd/MM/yyyy", new Date());
```

### SQLite Query Pattern

```typescript
// En sql-retriever.ts: Usar queries preparados + bindings
const stmt = db.prepare("SELECT * FROM normativas WHERE municipality = ?");
const results = stmt.all(municipality);
```

## ⚠️ Important Gotchas

1. **Path references**: Chatbot lee índices desde `/python-cli/data/indexes/` (path absoluto relativo a workspace root)
2. **pnpm**: Desarrollo y CI usan pnpm; no mezclar lockfiles o gestores
3. **Model defaults**: Si falta config, usa `google/gemini-3-flash-preview` (NO usar modelos caros sin confirmar)
4. **Cache invalidation**: El chatbot NO cachea índices, los lee fresh en cada búsqueda (por diseño)
5. **CORS**: Sat-analysis debe estar corriendo para que el módulo satelital funcione en el chatbot
6. **Poppler required**: Python CLI necesita `poppler-utils` instalado para Vision API (macOS: `brew install poppler`)

## 🎯 Common Tasks

**Add a new DocumentType**:

1. Update `types.ts`: `export type DocumentType = ... | 'nuevo_tipo'`
2. Update `data_models.py`: `DOCUMENT_TYPES` enum
3. Update extractors si necesario

**Change LLM model**:

1. Edit `.env`: `LLM_MODEL_PRIMARY=nuevo/modelo`
2. Restart chatbot: `cd chatbot && pnpm run dev`

**Fix RAG not finding results**:

1. Check if indices exist: `ls python-cli/data/indexes/`
2. Verify SQLite: `python cli.py db --stats`
3. Test BM25: Add `console.log` in `retriever.ts` → `performBM25Search()`

**Add a new municipality**:

1. Scrape: `python cli.py sibom --municipality "Nuevo" --limit 5`
2. Verify: Check `boletines/Nuevo/` exists
3. Index: Automático (índices se actualizan)
4. Test: Chatbot → "Buscar en Nuevo municipio"

---

**Version**: 2.1 (2026-02-19)
**Last updated**: Standardized Agent Integration
