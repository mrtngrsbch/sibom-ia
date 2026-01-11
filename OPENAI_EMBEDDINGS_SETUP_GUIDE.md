# Guía Completa: Setup de OpenAI Embeddings

## 💰 Costos Totales (Desglose Completo)

### Setup Inicial (One-time)

| Item | Cantidad | Costo Unitario | Total |
|------|----------|----------------|-------|
| **Generar embeddings** | 216K docs × 500 tokens | $0.02/1M tokens | **$0.22** |
| **OpenAI API mínimo** | Recarga inicial | - | **$5.00** |
| **Vector DB setup** | Depende de opción | Ver abajo | **$0-70** |
| **TOTAL INICIAL** | - | - | **$5.22 - $75.22** |

### Costos Mensuales (Recurrentes)

#### Escenario 1: 1,000 queries/mes
| Item | Costo |
|------|-------|
| Query embeddings (1K × 10 tokens) | $0.0002 |
| Vector DB (Pinecone/Qdrant) | $0 (free tier) o $25-70 |
| **TOTAL MENSUAL** | **$0.0002 - $70** |

#### Escenario 2: 10,000 queries/mes
| Item | Costo |
|------|-------|
| Query embeddings (10K × 10 tokens) | $0.002 |
| Vector DB (Pinecone/Qdrant) | $25-70 |
| **TOTAL MENSUAL** | **$25.002 - $70.002** |

## 🎯 Opciones de Vector Database

### Opción A: Pinecone (Más Fácil)

**Free Tier:**
- ✅ 1 índice
- ✅ 100K vectores (1536 dims)
- ✅ 100K queries/mes
- ❌ **PROBLEMA:** Tenés 216K docs (no alcanza)

**Paid Tier (Starter):**
- ✅ 1 índice
- ✅ 500K vectores
- ✅ Queries ilimitadas
- 💰 **$70/mes**

**Pros:**
- ✅ Setup en 5 minutos
- ✅ Zero mantenimiento
- ✅ Performance excelente
- ✅ Dashboard visual

**Contras:**
- ❌ Caro ($70/mes)
- ❌ Free tier insuficiente

**Setup:**
```bash
# 1. Crear cuenta en https://www.pinecone.io
# 2. Obtener API key
# 3. Instalar SDK
pnpm add @pinecone-database/pinecone

# 4. Código
import { Pinecone } from '@pinecone-database/pinecone';

const pinecone = new Pinecone({
  apiKey: process.env.PINECONE_API_KEY,
});

const index = pinecone.index('normativas');
```

### Opción B: Qdrant (Mejor Relación Precio/Performance)

**Free Tier:**
- ✅ 1GB storage (~200K vectores de 1536 dims)
- ✅ Queries ilimitadas
- ✅ **SUFICIENTE para 216K docs**

**Paid Tier:**
- ✅ 2GB storage
- ✅ Queries ilimitadas
- 💰 **$25/mes**

**Pros:**
- ✅ Free tier suficiente para tu caso
- ✅ Open source (podés self-hostear)
- ✅ Performance excelente
- ✅ Más barato que Pinecone

**Contras:**
- ⚠️ Setup un poco más complejo
- ⚠️ Menos conocido que Pinecone

**Setup:**
```bash
# 1. Crear cuenta en https://cloud.qdrant.io
# 2. Crear cluster (free tier)
# 3. Obtener API key y URL
# 4. Instalar SDK
pnpm add @qdrant/js-client-rest

# 5. Código
import { QdrantClient } from '@qdrant/js-client-rest';

const client = new QdrantClient({
  url: process.env.QDRANT_URL,
  apiKey: process.env.QDRANT_API_KEY,
});
```

### Opción C: Local con SQLite (Gratis pero Complejo)

**Pros:**
- ✅ 100% gratis
- ✅ Sin límites
- ✅ Privacidad total
- ✅ Control completo

**Contras:**
- ❌ Más lento (sin optimizaciones de vector DB)
- ❌ Más complejo de implementar
- ❌ Tenés que manejar indexing vos
- ❌ No escala bien (>1M vectores)

**Setup:**
```bash
# 1. Instalar dependencias
pnpm add better-sqlite3 @types/better-sqlite3

# 2. Crear tabla
CREATE TABLE embeddings (
  id TEXT PRIMARY KEY,
  vector BLOB,  -- Array de 1536 floats
  metadata TEXT -- JSON con municipio, tipo, etc.
);

# 3. Implementar búsqueda por similitud coseno
# (código más complejo, ~200 líneas)
```

## 📋 Plan de Implementación Completo

### Fase 1: Setup de OpenAI API (5 minutos)

1. **Crear cuenta en OpenAI:**
   - Ir a https://platform.openai.com
   - Crear cuenta (diferente de ChatGPT)
   - Verificar email

2. **Agregar crédito:**
   - Ir a Billing → Add payment method
   - Agregar tarjeta
   - Cargar mínimo $5 (recomendado $10)

3. **Crear API Key:**
   - Ir a API Keys
   - Create new secret key
   - Copiar y guardar (no se muestra de nuevo)

4. **Agregar a .env:**
   ```bash
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
   ```

### Fase 2: Elegir Vector DB (10-30 minutos)

**Recomendación:** Qdrant (free tier suficiente)

1. **Crear cuenta en Qdrant:**
   - Ir a https://cloud.qdrant.io
   - Crear cuenta
   - Crear cluster (free tier)

2. **Obtener credenciales:**
   - Copiar URL del cluster
   - Crear API key
   - Guardar ambos

3. **Agregar a .env:**
   ```bash
   QDRANT_URL=https://xxxxx.qdrant.io
   QDRANT_API_KEY=xxxxxxxxxxxxx
   ```

### Fase 3: Generar Embeddings (30-60 minutos)

**Script Python para generar embeddings:**

```python
# python-cli/generate_embeddings.py
import json
import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import os
from tqdm import tqdm

# Configurar OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configurar Qdrant
client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY'),
)

# Crear colección
client.create_collection(
    collection_name="normativas",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

# Cargar índice de normativas
with open('normativas_index_minimal.json', 'r') as f:
    normativas = json.load(f)

print(f"Generando embeddings para {len(normativas)} normativas...")

# Procesar en batches de 100
batch_size = 100
for i in tqdm(range(0, len(normativas), batch_size)):
    batch = normativas[i:i+batch_size]
    
    # Generar embeddings
    texts = [f"{n['ti']} {n['m']} {n['t']} {n['n']}" for n in batch]
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    
    # Subir a Qdrant
    points = []
    for j, n in enumerate(batch):
        points.append(PointStruct(
            id=n['id'],
            vector=response.data[j].embedding,
            payload={
                'municipality': n['m'],
                'type': n['t'],
                'number': n['n'],
                'year': n['y'],
                'title': n['ti'],
                'url': n['url'],
            }
        ))
    
    client.upsert(collection_name="normativas", points=points)

print("✅ Embeddings generados y subidos a Qdrant")
```

**Ejecutar:**
```bash
cd python-cli
python3 generate_embeddings.py
```

**Tiempo estimado:** 30-60 minutos (depende de tu conexión)
**Costo:** $0.22

### Fase 4: Implementar Búsqueda (2-3 horas)

**Crear `chatbot/src/lib/rag/vector-search.ts`:**

```typescript
import { QdrantClient } from '@qdrant/js-client-rest';
import OpenAI from 'openai';

const qdrant = new QdrantClient({
  url: process.env.QDRANT_URL!,
  apiKey: process.env.QDRANT_API_KEY!,
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!,
});

export async function vectorSearch(
  query: string,
  filters?: {
    municipality?: string;
    type?: string;
    year?: number;
  },
  limit: number = 10
) {
  // 1. Generar embedding de query
  const embedding = await openai.embeddings.create({
    model: "text-embedding-3-small",
    input: query,
  });

  // 2. Construir filtros de Qdrant
  const qdrantFilter: any = {};
  if (filters?.municipality) {
    qdrantFilter.municipality = { $eq: filters.municipality };
  }
  if (filters?.type) {
    qdrantFilter.type = { $eq: filters.type };
  }
  if (filters?.year) {
    qdrantFilter.year = { $eq: filters.year };
  }

  // 3. Buscar en Qdrant
  const results = await qdrant.search('normativas', {
    vector: embedding.data[0].embedding,
    filter: Object.keys(qdrantFilter).length > 0 ? qdrantFilter : undefined,
    limit,
    with_payload: true,
  });

  // 4. Retornar resultados
  return results.map(r => ({
    id: r.id,
    score: r.score,
    municipality: r.payload?.municipality,
    type: r.payload?.type,
    number: r.payload?.number,
    year: r.payload?.year,
    title: r.payload?.title,
    url: r.payload?.url,
  }));
}
```

**Integrar en `retriever.ts`:**

```typescript
import { vectorSearch } from './vector-search';

export async function retrieveContext(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  // Usar vector search en vez de BM25
  const vectorResults = await vectorSearch(query, {
    municipality: options.municipality,
    type: options.type,
    year: options.dateFrom ? parseInt(options.dateFrom.split('-')[0]) : undefined,
  }, options.limit || 10);

  // Cargar contenido de los documentos encontrados
  const documents = await Promise.all(
    vectorResults.map(async (r) => {
      const content = await loadDocumentContent(r.id);
      return {
        ...r,
        content,
      };
    })
  );

  // Construir contexto y fuentes
  return {
    context: buildContext(documents),
    sources: buildSources(documents),
  };
}
```

### Fase 5: Testing (1 hora)

**Test queries:**
```typescript
// Test 1: Búsqueda semántica
await vectorSearch("sueldos de carlos tejedor");
// Debería encontrar documentos con "remuneraciones"

// Test 2: Con filtros
await vectorSearch("ordenanzas de tránsito", {
  municipality: "Carlos Tejedor",
  year: 2025,
});

// Test 3: Comparar con BM25
const bm25Results = await bm25Search("sueldos");
const vectorResults = await vectorSearch("sueldos");
// Comparar accuracy
```

## 💰 Resumen de Costos

### Opción Recomendada: Qdrant Free Tier

| Item | Costo |
|------|-------|
| **Setup inicial** | |
| OpenAI API recarga | $5.00 |
| Generar embeddings | $0.22 |
| Qdrant free tier | $0.00 |
| **TOTAL INICIAL** | **$5.22** |
| | |
| **Mensual (1K queries)** | |
| Query embeddings | $0.0002 |
| Qdrant free tier | $0.00 |
| **TOTAL MENSUAL** | **$0.0002** |

### Comparación con Cohere

| | OpenAI + Qdrant | Cohere Rerank |
|---|---|---|
| **Setup inicial** | $5.22 | $0 |
| **Mensual (1K queries)** | $0.0002 | $2.00 |
| **Mensual (10K queries)** | $0.002 | $20.00 |
| **Anual (1K queries/mes)** | $5.22 + $0.002 = **$5.24** | **$24.00** |
| **Anual (10K queries/mes)** | $5.22 + $0.024 = **$5.24** | **$240.00** |

**Conclusión:** OpenAI + Qdrant es **4.5x más barato** que Cohere a partir del primer año.

## 🎯 Decisión Final

**¿Cuándo usar cada opción?**

### Usar OpenAI + Qdrant si:
- ✅ Tenés $5 para invertir inicialmente
- ✅ Esperás >1000 queries/mes
- ✅ Querés la solución más barata a largo plazo
- ✅ Tenés 1 semana para implementar

### Usar Cohere si:
- ✅ Querés probar YA (1 día)
- ✅ No querés invertir nada inicialmente
- ✅ Volumen bajo (<1000 queries/mes)
- ✅ Priorizás simplicidad sobre costo

## 📝 Checklist de Setup

- [ ] Crear cuenta OpenAI
- [ ] Agregar $5-10 de crédito
- [ ] Crear API key de OpenAI
- [ ] Crear cuenta Qdrant (free tier)
- [ ] Crear cluster en Qdrant
- [ ] Obtener URL y API key de Qdrant
- [ ] Agregar credenciales a .env
- [ ] Instalar dependencias (openai, @qdrant/js-client-rest)
- [ ] Ejecutar script de generación de embeddings
- [ ] Implementar vector-search.ts
- [ ] Integrar en retriever.ts
- [ ] Testear con queries reales
- [ ] Deploy a producción

**Tiempo total estimado:** 1 semana (incluyendo testing)
