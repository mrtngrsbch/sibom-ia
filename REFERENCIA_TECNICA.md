# 📚 REFERENCIA TÉCNICA RÁPIDA - Qdrant Anti-Hallucination System

**Versión**: 1.0  
**Última actualización**: 15 feb 2026  
**Propósito**: Especificaciones técnicas de implementación

---

## 🗂️ ESTRUCTURA DE ARCHIVOS

### Nuevos archivos creados
```
chatbot/src/lib/rag/
├── qdrant-retriever.ts              (272 líneas, NEW)
└── balance-retriever-integration.ts  (186 líneas, NEW)

python-cli/scripts/
└── migrate_balances_to_qdrant.py     (458 líneas, UPDATED)
```

### Archivos modificados
```
chatbot/src/app/api/chat/
└── route.ts                (UPDATED: +50 líneas de lógica)
```

---

## 🔧 CONFIGURACIÓN

### Environment Variables (requiere)
```
# Qdrant Cloud
QDRANT_URL=https://861a549d-9361-4411-ac18-c9d0e8d66752.sa-east-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=<YOUR_API_KEY>

# OpenAI (para embeddings)
OPENAI_API_KEY=<YOUR_OPENAI_KEY>

# Ya existentes (unchanged)
OPENROUTER_API_KEY=...
```

### Qdrant Collection Schema
```
Collection: normativas
Vectors: 1536 dims (text-embedding-3-small)
Distance: Cosine
Payload schema:
{
  "municipio": "string",
  "tipo_documento": "string",
  "tipo_detalle": "string",
  "periodo": "string",
  "is_executive_summary": boolean,
  "contains_key_numbers": boolean,
  "source": "string",
  "content": "string",
  "relevance": number
}
```

### Indexes (6 total)
```
INDEX 1: tipo_documento (KEYWORD)
INDEX 2: municipio (KEYWORD)
INDEX 3: periodo (KEYWORD)
INDEX 4: tipo_detalle (KEYWORD)
INDEX 5: is_executive_summary (BOOL)
INDEX 6: contains_key_numbers (BOOL)
```

---

## 💻 INTERFACES TYPESCRIPT

### qdrant-retriever.ts

```typescript
interface RetrievedChunk {
  id: string;
  content: string;
  metadata: {
    municipio: string;
    tipo_documento: string;
    tipo_detalle: string;
    periodo: string;
    is_executive_summary: boolean;
    contains_key_numbers: boolean;
    source: string;
  };
  score: number;
}

async function retrieveFromQdrant(
  query: string,
  filters?: Record<string, any>,
  maxResults?: number
): Promise<RetrievedChunk[]>

async function retrieveBalanceTotals(
  municipio: string,
  periodo?: string
): Promise<RetrievedChunk[]>

function rankChunks(chunks: RetrievedChunk[]): RetrievedChunk[]

function formatChunksForLLM(chunks: RetrievedChunk[]): string

function extractNumbers(chunks: RetrievedChunk[]): Set<string>

function buildQdrantFilters(
  filters?: Record<string, any>
): Record<string, any>
```

### balance-retriever-integration.ts

```typescript
interface BalanceQueryResult {
  context: string;
  sources: Array<{
    title: string;
    file: string;
    relevance: number;
  }>;
}

function isBalanceQuery(query: string): boolean

function extractMunicipalityFromQuery(query: string): string | undefined

function extractPeriodFromQuery(query: string): string | undefined

async function retrieveBalanceContext(
  query: string,
  municipio?: string,
  periodo?: string
): Promise<BalanceQueryResult>

function buildBalanceSystemMessage(): {
  role: "system";
  content: string;
}

const BALANCE_ANTI_HALLUCINATION_SYSTEM_PROMPT: string
// 250+ caracteres de reglas CRÍTICAS
```

---

## 🧮 ALGORITMO DE DETECCIÓN

### isBalanceQuery()
```
Keywords: [
  "balance", "tesorería", "recursos", "gastos",
  "saldo", "disponibilidad", "ingresos", "egresos",
  "presupuesto", "total", "dinero"
]

Rules:
- Si 2+ keywords en query → isBalance = true
- Si 1 keyword AND query contains "tesor" → isBalance = true
- Else → isBalance = false
```

### extractMunicipalityFromQuery()
```
Ciudades conocidas: [
  "Carlos Tejedor", "Azul", "Balcarce", "Bragado", ...
]

Process:
1. Case-insensitive search en query
2. Si encuentra → return municipio
3. Else → try regex: /(?:de|en|para|municipio|ciudad)\s+([A-Z]\w+)/
4. Else → undefined
```

### extractPeriodFromQuery()
```
Pattern: YYYY-TN (donde N = 1-4)

Process:
1. Find year (YYYY) en query
2. Find trimestre (T1|T2|T3|T4)
3. Return "YYYY-TN" format
4. Support variants: "primer trimestre", "Q1", etc.
```

---

## 📊 FLOW DIAGRAM

```
route.ts (POST /api/chat)
  ↓
[1] isBalanceQuery(query)?
    ├─ YES → [BRANCH A: Balance Logic]
    └─ NO  → [BRANCH B: SQL/JSON RAG]

[BRANCH A] Balance Logic
  ├─ extractMunicipalityFromQuery()
  ├─ extractPeriodFromQuery()
  ├─ retrieveBalanceContext(query, municipio, periodo)
  │   ├─ retrieveFromQdrant()
  │   │   ├─ Generate OpenAI embedding
  │   │   ├─ Query Qdrant with filters
  │   │   └─ rankChunks()
  │   ├─ formatChunksForLLM()
  │   └─ return {context, sources}
  ├─ buildBalanceSystemMessage() → inject prompt
  └─ streamText() with anti-hallucination prompt

[BRANCH B] SQL/JSON RAG
  └─ Normal retrieval logic (unchanged)
```

---

## 🚨 ERROR HANDLING

### Common Issues & Solutions

#### Issue: Division by Zero (FIXED)
```python
# BEFORE (BUG):
avg_chunks_per_file = total_chunks / sample_size  # Crashes if sample_size=0

# AFTER (FIXED):
if len(balance_files) == 0:
    return {estimates...}
avg_chunks_per_file = total_chunks / sample_size if sample_size > 0 else 0
```

#### Issue: Checkpoint Desynced (FIXED)
```python
# BEFORE (BUG):
checkpoint["processed_files"] += 5  # Hardcoded, accumulates incorrectly

# AFTER (FIXED):
checkpoint["processed_files"] = len(checkpoint["processed_file_paths"])  # Actual count
```

#### Issue: Query Detection Too Strict
```typescript
// If user says "presupuestos municipales" (no "balance" keyword)
// Solution: Expand keyword list or add "presupuesto" as alias
```

---

## 📈 PERFORMANCE TUNING

### Vector Search Optimization
```
Max results: 10 (default, tunable)
Filters: Applied at Qdrant level (not post-processing)
Ranking: O(n) single pass
Total latency: ~200-300ms including OpenAI embedding
```

### Token Budgeting
```
Per query:
- Query embedding: ~5-30 tokens
- Top 10 chunks: ~800-1000 tokens
- System prompt: ~50 tokens
- Total context window: <2000 tokens (safe for 4K models)
```

### Cost Optimization
```
OpenAI embed-small: $0.02 per 1M tokens
Per balance chunk: ~50 tokens
2,700 chunks: 135K tokens → $0.0027
Batch processing: 5 files at once → reduced API calls
```

---

## 🔒 SECURITY & VALIDATION

### Data Validation Pipeline
```
JSON File → Chunker → Embeddings → Qdrant → Retriever → LLM
                         ↓
                    (Add metadata)
                         ↓
                  (Verify structure)
                         ↓
                  (No NaN/null values)
```

### Prompt Injection Prevention
```
User query: "${process.env.OPENAI_KEY}"
System prompt: Hard-coded in TypeScript (not from user input)
LLM constraint: Temperature=0.1 (highly deterministic)
Output format: Constrained by rules in system prompt
```

---

## 🧪 TESTING CHECKLIST

### Unit Tests (when adding tests)
```
✓ isBalanceQuery edge cases
✓ extractMunicipalityFromQuery (known cities)
✓ extractPeriodFromQuery (various formats)
✓ rankChunks ordering
✓ extractNumbers (Argentine currency patterns)
```

### Integration Tests
```
✓ retrieveBalanceContext end-to-end
✓ Qdrant connectivity
✓ OpenAI embedding API
✓ Anti-hallucination prompt injection
```

### Manual Testing (post-migration)
```
✓ "¿Balance Carlos Tejedor 2024-T1?" → Real numbers + source
✓ "¿Saldo final?" → Period specified, not ambiguous
✓ Off-topic query → Falls back to SQL/RAG, works fine
✓ Typo in municipio → Graceful "no data" response
```

---

## 📝 DEPLOYMENT CHECKLIST

```
Pre-deployment:
  ✓ pnpm run build (no errors)
  ✓ All TS files compile
  ✓ route.ts properly updated
  ✓ Environment variables set
  ✓ Qdrant Cloud online
  ✓ Migration complete

Deployment:
  ✓ git push origin main
  ✓ Vercel detects push
  ✓ Vercel builds (2-3 min)
  ✓ Vercel deploys

Post-deployment:
  ✓ Check logs for errors
  ✓ Test 3-5 balance queries
  ✓ Monitor error rate
  ✓ Verify no hallucinations
```

---

## 📚 API REFERENCE

### Qdrant SDK (Python)
```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"]
)

# Search
results = client.search(
    collection_name="normativas",
    query_vector=embedding,  # 1536 dims
    query_filter={"must": [{"key": "source", "match": {"value": "balance_migration_v1"}}]},
    limit=10,
    with_vectors=False
)
```

### OpenAI SDK (TypeScript)
```typescript
import OpenAI from "openai";

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const embedding = await client.embeddings.create({
  model: "text-embedding-3-small",
  input: query,
  dimensions: 1536
});
```

---

## 🎯 Success Metrics

| Metric                   | Target  | How to Measure      |
| ------------------------ | ------- | ------------------- |
| Zero hallucinations      | 100%    | Manual test queries |
| Query detection accuracy | 95%+    | Log true positives  |
| Qdrant uptime            | 99%+    | Qdrant API health   |
| Response latency         | <1s     | Logging middleware  |
| Cost per query           | <$0.001 | OpenAI usage logs   |

---

**Versión**: 1.0  
**Creado**: 15 feb 2026  
**Última revisión**: 15 feb 2026

