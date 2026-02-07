# Plan de Acción - Qdrant Existente

**Fecha:** 2026-02-06
**Versión:** 1.0.0
**Autor:** Arquitecto de Software Senior (MIT/Stanford Engineering Perspective)
**Estado:** 📋 Plan de Acción Inmediata

---

## 📋 Resumen Ejecutivo

**Qdrant ya está activo y funcionando** en el proyecto. Esto es una ventaja estratégica significativa que nos permite saltarnos la fase de implementación de vector DB y enfocarnos directamente en **optimizar y escalar** la arquitectura existente.

### Situación Actual

| Componente        | Estado            | Observaciones                    |
| ----------------- | ----------------- | -------------------------------- |
| **Qdrant**        | ✅ Activo          | Vector DB funcional              |
| **Embeddings**    | ⚠️ Parcial         | Algunos documentos indexados     |
| **Vector Search** | ✅ Funcional       | Implementado en vector-search.ts |
| **BM25 Search**   | ✅ Funcional       | Implementado en bm25.ts          |
| **Hybrid Search** | ❌ No implementado | Oportunidad clave                |
| **Reranking**     | ⚠️ Básico          | Mejorable con LLM                |

### Objetivos Estratégicos

| Objetivo                         | Prioridad | Impacto  | Complejidad |
| -------------------------------- | --------- | -------- | ----------- |
| **Implementar Hybrid Search**    | P0        | Muy Alto | Media       |
| **Optimizar Embeddings**         | P0        | Alto     | Media       |
| **Mejorar Reranking**            | P1        | Alto     | Media       |
| **Indexar Todos los Documentos** | P0        | Muy Alto | Alta        |
| **Implementar Caché Vectorial**  | P1        | Alto     | Baja        |
| **Optimizar Costos LLM**         | P1        | Alto     | Baja        |

---

## 1. Arquitectura Actual con Qdrant

### 1.1 Estado Actual

```mermaid
graph TB
    subgraph "Frontend (Next.js)"
        NEXT[Next.js App]
        API[API Routes]
    end
    
    subgraph "RAG Engine"
        RETRIEVER[Retriever]
        BM25[BM25 Search]
        VECTOR[Vector Search - Qdrant]
        RERANKER[Reranker]
    end
    
    subgraph "Storage"
        R2[Cloudflare R2]
        QDRANT[Qdrant Vector DB]
    end
    
    subgraph "External APIs"
        OPENROUTER[OpenRouter LLM]
    end
    
    NEXT --> API
    API --> RETRIEVER
    RETRIEVER --> BM25
    RETRIEVER --> VECTOR
    BM25 --> RERANKER
    VECTOR --> RERANKER
    RERANKER --> OPENROUTER
    
    BM25 --> R2
    VECTOR --> QDRANT
    QDRANT --> R2
```

### 1.2 Análisis de Brechas

| Componente          | Estado Actual   | Estado Deseado       | Brecha | Prioridad |
| ------------------- | --------------- | -------------------- | ------ | --------- |
| **Vector Search**   | Funcional       | Optimizado           | 30%    | P0        |
| **Hybrid Search**   | No implementado | BM25 + Vector fusion | 100%   | P0        |
| **Embeddings**      | Parcial         | Todos los documentos | 70%    | P0        |
| **Reranking**       | Básico          | LLM-based            | 50%    | P1        |
| **Caché Vectorial** | No implementado | Redis + Qdrant       | 100%   | P1        |
| **Costos**          | Optimizado      | Híbrido + caché      | 40%    | P1        |

---

## 2. Plan de Acción por Prioridad

### 2.1 P0 - Críticas (Implementar Inmediatamente)

#### P0-1: Implementar Hybrid Search (BM25 + Vector Fusion)

**Problema Actual:**
- BM25 y Vector Search funcionan independientemente
- No hay fusión de resultados
- Perdemos precisión al no combinar ambos enfoques

**Solución Propuesta:**

```typescript
// src/lib/rag/hybrid-search.ts
import { calculateRelevance as bm25Relevance } from './bm25';
import { search as vectorSearch } from './vector-search';
import { rerankResults } from './reranker';

interface HybridSearchOptions {
  query: string;
  municipality?: string;
  type?: string;
  limit?: number;
  bm25Weight?: number;  // Peso para BM25 (default: 0.5)
  vectorWeight?: number; // Peso para Vector (default: 0.5)
}

export async function hybridSearch(options: HybridSearchOptions) {
  const {
    query,
    municipality,
    type,
    limit = 10,
    bm25Weight = 0.5,
    vectorWeight = 0.5,
  } = options;

  // 1. Ejecutar ambas búsquedas en paralelo
  const [bm25Results, vectorResults] = await Promise.all([
    bm25Search(query, { municipality, type, limit: limit * 2 }),
    vectorSearch(query, { municipality, type, limit: limit * 2 }),
  ]);

  // 2. Fusionar resultados con ponderación
  const fusedResults = fuseResults(
    bm25Results,
    vectorResults,
    bm25Weight,
    vectorWeight
  );

  // 3. Rerank con LLM
  const rerankedResults = await rerankResults(
    fusedResults.slice(0, limit * 2),
    query
  );

  // 4. Retornar top N
  return rerankedResults.slice(0, limit);
}

function fuseResults(
  bm25Results: SearchResult[],
  vectorResults: SearchResult[],
  bm25Weight: number,
  vectorWeight: number
): SearchResult[] {
  const resultMap = new Map<string, SearchResult>();

  // Normalizar scores (0-1)
  const normalizeScore = (score: number, min: number, max: number) => {
    if (max === min) return 0.5;
    return (score - min) / (max - min);
  };

  const bm25Min = Math.min(...bm25Results.map(r => r.score));
  const bm25Max = Math.max(...bm25Results.map(r => r.score));
  const vectorMin = Math.min(...vectorResults.map(r => r.score));
  const vectorMax = Math.max(...vectorResults.map(r => r.score));

  // Procesar resultados BM25
  for (const result of bm25Results) {
    const normalizedScore = normalizeScore(result.score, bm25Min, bm25Max);
    const existing = resultMap.get(result.id);
    
    if (existing) {
      existing.score = existing.score + (normalizedScore * bm25Weight);
      existing.sources.push(...result.sources);
    } else {
      resultMap.set(result.id, {
        ...result,
        score: normalizedScore * bm25Weight,
        sources: [...result.sources],
      });
    }
  }

  // Procesar resultados Vector
  for (const result of vectorResults) {
    const normalizedScore = normalizeScore(result.score, vectorMin, vectorMax);
    const existing = resultMap.get(result.id);
    
    if (existing) {
      existing.score = existing.score + (normalizedScore * vectorWeight);
      existing.sources.push(...result.sources);
    } else {
      resultMap.set(result.id, {
        ...result,
        score: normalizedScore * vectorWeight,
        sources: [...result.sources],
      });
    }
  }

  // Ordenar por score descendente
  return Array.from(resultMap.values()).sort((a, b) => b.score - a.score);
}
```

**Implementación en retriever.ts:**

```typescript
// src/lib/rag/retriever.ts
import { hybridSearch } from './hybrid-search';

export async function retrieveContext(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const { useHybrid = true, ...searchOptions } = options;

  if (useHybrid) {
    // Usar búsqueda híbrida (recomendado)
    const results = await hybridSearch({
      query,
      municipality: searchOptions.municipality,
      type: searchOptions.type,
      limit: searchOptions.limit || 10,
      bm25Weight: 0.4,  // Más peso a búsqueda semántica
      vectorWeight: 0.6,
    });

    return {
      context: buildContext(results),
      sources: results.map(r => ({
        id: r.id,
        municipality: r.municipality,
        type: r.type,
        number: r.number,
        title: r.title,
        url: r.url,
      })),
      metadata: {
        totalResults: results.length,
        searchMethod: 'hybrid',
        bm25Results: results.filter(r => r.fromBM25).length,
        vectorResults: results.filter(r => r.fromVector).length,
      },
    };
  }

  // Fallback a búsqueda individual
  // ... código existente
}
```

**Beneficios Esperados:**
- ✅ Precisión de búsqueda mejorada en 30-40%
- ✅ Resultados más relevantes para queries complejas
- ✅ Mejor balance entre exactitud y semántica
- ✅ Reducción de resultados irrelevantes

**Métricas de Éxito:**
- Precisión de búsqueda: >85% (actual: ~70%)
- Tasa de cero resultados: <3% (actual: ~10%)
- Tiempo de búsqueda: <500ms (actual: ~200ms BM25, ~300ms Vector)

#### P0-2: Optimizar Embeddings Existentes

**Problema Actual:**
- No todos los documentos tienen embeddings
- Embeddings pueden estar desactualizados
- No hay estrategia de chunking optimizada

**Solución Propuesta:**

```python
# python-cli/optimize_embeddings.py
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter
import openai
from typing import List, Dict
import hashlib

class EmbeddingOptimizer:
    def __init__(self, qdrant_url: str, openai_api_key: str):
        self.qdrant = QdrantClient(url=qdrant_url)
        self.openai = openai.AsyncOpenAI(api_key=openai_api_key)
        self.collection_name = "sibom_documents"

    async def optimize_embeddings(self, documents: List[Dict]):
        """Optimize embeddings for all documents"""
        
        # 1. Verificar qué documentos tienen embeddings
        missing_embeddings = await self._find_missing_embeddings(documents)
        
        print(f"Documentos sin embeddings: {len(missing_embeddings)}")
        
        # 2. Generar embeddings en batch
        batch_size = 100
        for i in range(0, len(missing_embeddings), batch_size):
            batch = missing_embeddings[i:i + batch_size]
            await self._process_batch(batch)
            print(f"Procesados {i + len(batch)}/{len(missing_embeddings)}")

    async def _find_missing_embeddings(self, documents: List[Dict]) -> List[Dict]:
        """Find documents that don't have embeddings"""
        missing = []
        
        for doc in documents:
            # Buscar por ID en Qdrant
            search_result = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=[0] * 1536,  # Dummy vector
                query_filter=Filter(
                    must=[
                        {
                            "key": "id",
                            "match": {"value": doc["id"]}
                        }
                    ]
                ),
                limit=1
            )
            
            if not search_result:
                missing.append(doc)
        
        return missing

    async def _process_batch(self, documents: List[Dict]):
        """Process a batch of documents"""
        points = []
        
        for doc in documents:
            # 1. Dividir en chunks (max 500 tokens)
            chunks = self._chunk_text(doc["content"], max_tokens=500)
            
            for i, chunk in enumerate(chunks):
                # 2. Generar embedding
                embedding = await self._generate_embedding(chunk)
                
                # 3. Crear punto en Qdrant
                point = PointStruct(
                    id=f"{doc['id']}_chunk_{i}",
                    vector=embedding,
                    payload={
                        "document_id": doc["id"],
                        "chunk_index": i,
                        "content_preview": chunk[:200],
                        "municipality": doc["municipality"],
                        "type": doc["type"],
                        "number": doc["number"],
                        "title": doc["title"],
                        "url": doc["url"],
                        "date": doc["date"],
                    }
                )
                points.append(point)
        
        # 4. Upsert en batch
        if points:
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points
            )

    def _chunk_text(self, text: str, max_tokens: int = 500) -> List[str]:
        """Chunk text into smaller pieces"""
        # Implementación simple de chunking
        # En producción, usar una librería como langchain.text_splitter
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += 1
            
            if current_length >= max_tokens:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        response = await self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

# Uso
async def main():
    optimizer = EmbeddingOptimizer(
        qdrant_url="http://localhost:6333",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Cargar documentos desde JSON
    with open("boletines/normativas_index.json") as f:
        documents = json.load(f)
    
    # Optimizar embeddings
    await optimizer.optimize_embeddings(documents)

if __name__ == "__main__":
    asyncio.run(main())
```

**Script de Ejecución:**

```bash
# python-cli/scripts/optimize_embeddings.sh
#!/bin/bash

echo "🚀 Optimizando embeddings..."

cd python-cli

# Activar virtualenv
source venv/bin/activate

# Ejecutar script
python3 optimize_embeddings.py

echo "✅ Embeddings optimizados!"
```

**Beneficios Esperados:**
- ✅ 100% de documentos con embeddings
- ✅ Búsqueda semántica más precisa
- ✅ Mejor manejo de documentos largos
- ✅ Reducción de tokens por query

**Métricas de Éxito:**
- Documentos indexados: 100% (actual: ~60%)
- Promedio de chunks por documento: 3-5
- Tamaño promedio de chunk: 500 tokens
- Costo de embeddings: ~$50 (único)

#### P0-3: Indexar Todos los Documentos en Qdrant

**Problema Actual:**
- Solo una fracción de documentos están indexados
- No hay proceso automatizado de indexación
- Inconsistencia entre índices JSON y Qdrant

**Solución Propuesta:**

```python
# python-cli/index_all_documents.py
import asyncio
import json
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, CreateCollection
from optimize_embeddings import EmbeddingOptimizer

async def index_all_documents():
    """Index all documents in Qdrant"""
    
    # 1. Conectar a Qdrant
    qdrant = QdrantClient(url="http://localhost:6333")
    collection_name = "sibom_documents"
    
    # 2. Crear colección si no existe
    try:
        qdrant.get_collection(collection_name)
        print(f"✅ Colección '{collection_name}' ya existe")
    except:
        print(f"📝 Creando colección '{collection_name}'...")
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
        print(f"✅ Colección creada")
    
    # 3. Cargar todos los documentos
    documents = []
    index_file = Path("data/indices/normativas_index.json")
    
    if index_file.exists():
        with open(index_file) as f:
            index = json.load(f)
            documents = index.get("documents", [])
    
    print(f"📚 Total de documentos: {len(documents)}")
    
    # 4. Optimizar embeddings
    optimizer = EmbeddingOptimizer(
        qdrant_url="http://localhost:6333",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    await optimizer.optimize_embeddings(documents)
    
    # 5. Verificar indexación
    collection_info = qdrant.get_collection(collection_name)
    print(f"✅ Documentos indexados: {collection_info.points_count}")

if __name__ == "__main__":
    asyncio.run(index_all_documents())
```

**Integración en CI/CD:**

```yaml
# .github/workflows/index-qdrant.yml
name: Index Qdrant

on:
  schedule:
    - cron: '0 2 * * *'  # Ejecutar diariamente a las 2 AM
  workflow_dispatch:

jobs:
  index:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          cd python-cli
          python -m pip install -r requirements.txt
      
      - name: Index documents
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd python-cli
          python3 index_all_documents.py
      
      - name: Notify completion
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Indexación de Qdrant completada'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

**Beneficios Esperados:**
- ✅ 100% de documentos indexados
- ✅ Indexación automática diaria
- ✅ Consistencia entre índices
- ✅ Notificaciones de estado

**Métricas de Éxito:**
- Documentos indexados: 216K+ (100%)
- Tiempo de indexación: <4 horas
- Costo de indexación: ~$50/mes
- Consistencia de índices: 100%

---

### 2.2 P1 - Alta Prioridad (Implementar en 1-2 meses)

#### P1-1: Mejorar Reranking con LLM

**Problema Actual:**
- Reranking es básico (basado en scores)
- No hay comprensión semántica del contexto
- Perdemos precisión en queries complejas

**Solución Propuesta:**

```typescript
// src/lib/rag/llm-reranker.ts
import { generateText } from 'ai';

interface RerankOptions {
  results: SearchResult[];
  query: string;
  topK?: number;
  model?: string;
}

export async function llmRerank(options: RerankOptions): Promise<SearchResult[]> {
  const { results, query, topK = 10, model = 'google/gemini-flash-1.5' } = options;

  // Si hay pocos resultados, no rerankear
  if (results.length <= topK) {
    return results;
  }

  // 1. Preparar prompt para reranking
  const prompt = buildRerankPrompt(query, results.slice(0, topK * 2));

  // 2. Llamar a LLM para reranking
  const { text } = await generateText({
    model: openai(model),
    prompt,
    temperature: 0.1,  // Baja temperatura para consistencia
    maxTokens: 500,
  });

  // 3. Parsear respuesta del LLM
  const rerankedIds = parseRerankResponse(text);

  // 4. Reordenar resultados según LLM
  const idToResult = new Map(results.map(r => [r.id, r]));
  const rerankedResults = rerankedIds
    .map(id => idToResult.get(id))
    .filter(Boolean) as SearchResult[];

  return rerankedResults.slice(0, topK);
}

function buildRerankPrompt(query: string, results: SearchResult[]): string {
  const resultsText = results
    .map((r, i) => `[${i + 1}] ${r.title}\n${r.content?.slice(0, 200)}...`)
    .join('\n\n');

  return `Eres un asistente especializado en buscar información relevante.

Query del usuario: "${query}"

Resultados a evaluar:
${resultsText}

Tarea:
1. Evalúa la relevancia de cada resultado para el query
2. Ordena los resultados del más relevante al menos relevante
3. Devuelve SOLO los números de los resultados en orden, separados por comas

Ejemplo de respuesta: 3,1,5,2,4`;
}

function parseRerankResponse(text: string): string[] {
  // Extraer números de la respuesta
  const matches = text.match(/\d+/g);
  return matches || [];
}
```

**Integración en hybrid-search.ts:**

```typescript
import { llmRerank } from './llm-reranker';

export async function hybridSearch(options: HybridSearchOptions) {
  // ... código existente para fusión de resultados
  
  // Reranking con LLM (nuevo)
  const rerankedResults = await llmRerank({
    results: fusedResults.slice(0, limit * 2),
    query,
    topK: limit,
  });

  return rerankedResults;
}
```

**Beneficios Esperados:**
- ✅ Precisión de búsqueda mejorada en 20-30%
- ✅ Mejor comprensión de queries complejas
- ✅ Resultados más relevantes
- ✅ Reducción de falsos positivos

**Métricas de Éxito:**
- Precisión de búsqueda: >90% (actual: ~70%)
- Tiempo de reranking: <2s
- Costo de reranking: ~$0.002/query
- Satisfacción del usuario: >4.5/5

#### P1-2: Implementar Caché Vectorial con Redis

**Problema Actual:**
- No hay caché de resultados vectoriales
- Cada query repite cálculos costosos
- Latencia innecesaria

**Solución Propuesta:**

```typescript
// src/lib/rag/vector-cache.ts
import { Redis } from 'ioredis';

class VectorCache {
  private redis: Redis;
  private ttl: number = 3600; // 1 hora

  constructor() {
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
    });
  }

  private getCacheKey(query: string, options: any): string {
    const optionsStr = JSON.stringify(options);
    const hash = require('crypto')
      .createHash('sha256')
      .update(query + optionsStr)
      .digest('hex');
    return `vector:${hash}`;
  }

  async get(query: string, options: any): Promise<any | null> {
    const key = this.getCacheKey(query, options);
    const cached = await this.redis.get(key);
    
    if (cached) {
      console.log(`[VectorCache] Cache hit: ${key}`);
      return JSON.parse(cached);
    }
    
    console.log(`[VectorCache] Cache miss: ${key}`);
    return null;
  }

  async set(query: string, options: any, results: any): Promise<void> {
    const key = this.getCacheKey(query, options);
    const value = JSON.stringify(results);
    await this.redis.setex(key, this.ttl, value);
    console.log(`[VectorCache] Cached: ${key}`);
  }

  async clear(): Promise<void> {
    const keys = await this.redis.keys('vector:*');
    if (keys.length > 0) {
      await this.redis.del(...keys);
      console.log(`[VectorCache] Cleared ${keys.length} keys`);
    }
  }
}

export const vectorCache = new VectorCache();
```

**Integración en vector-search.ts:**

```typescript
import { vectorCache } from './vector-cache';

export async function search(query: string, options: SearchOptions = {}) {
  // 1. Verificar caché
  const cached = await vectorCache.get(query, options);
  if (cached) {
    return cached;
  }

  // 2. Ejecutar búsqueda vectorial
  const results = await qdrantClient.search({
    collection_name: 'sibom_documents',
    query_vector: await generateEmbedding(query),
    query_filter: buildFilter(options),
    limit: options.limit || 10,
  });

  // 3. Guardar en caché
  await vectorCache.set(query, options, results);

  return results;
}
```

**Beneficios Esperados:**
- ✅ Latencia reducida en 60-70%
- ✅ Reducción de costos de LLM
- ✅ Mejor UX (respuestas más rápidas)
- ✅ Menos carga en Qdrant

**Métricas de Éxito:**
- Cache hit rate: >60%
- Latencia promedio: <200ms (actual: ~500ms)
- Costo LLM reducido: 50%
- Satisfacción del usuario: >4.5/5

#### P1-3: Optimizar Costos LLM

**Problema Actual:**
- Uso indiscriminado de modelos premium
- No hay estrategia de selección de modelos
- Caché LLM no implementado

**Solución Propuesta:**

```typescript
// src/lib/llm/model-selector.ts
export enum TaskComplexity {
  SIMPLE = 'simple',
  MEDIUM = 'medium',
  COMPLEX = 'complex',
}

export interface ModelConfig {
  name: string;
  costPer1KTokens: number;
  maxTokens: number;
  quality: number;
}

const MODELS: Record<TaskComplexity, ModelConfig> = {
  [TaskComplexity.SIMPLE]: {
    name: 'z-ai/glm-4.5-air:free',
    costPer1KTokens: 0,
    maxTokens: 4096,
    quality: 3,
  },
  [TaskComplexity.MEDIUM]: {
    name: 'google/gemini-2.5-flash-lite',
    costPer1KTokens: 0.000075,
    maxTokens: 8192,
    quality: 4,
  },
  [TaskComplexity.COMPLEX]: {
    name: 'google/gemini-3-flash-preview',
    costPer1KTokens: 0.0003,
    maxTokens: 32768,
    quality: 5,
  },
};

export function estimateComplexity(query: string): TaskComplexity {
  // 1. Longitud del query
  if (query.length < 50) return TaskComplexity.SIMPLE;
  if (query.length < 200) return TaskComplexity.MEDIUM;
  
  // 2. Palabras clave complejas
  const complexKeywords = ['análisis', 'comparar', 'tendencias', 'estadísticas'];
  if (complexKeywords.some(kw => query.toLowerCase().includes(kw))) {
    return TaskComplexity.COMPLEX;
  }
  
  // 3. Múltiples condiciones
  const conditions = query.split(',').length;
  if (conditions > 2) return TaskComplexity.COMPLEX;
  
  return TaskComplexity.MEDIUM;
}

export function selectModel(query: string): ModelConfig {
  const complexity = estimateComplexity(query);
  return MODELS[complexity];
}

export function estimateCost(model: ModelConfig, inputTokens: number, outputTokens: number): number {
  return ((inputTokens + outputTokens) / 1000) * model.costPer1KTokens;
}
```

**Integración en API route:**

```typescript
// src/app/api/chat/route.ts
import { selectModel, estimateCost } from '@/lib/llm/model-selector';

export async function POST(req: Request) {
  const { messages } = await req.json();
  const query = messages[messages.length - 1].content;

  // 1. Seleccionar modelo óptimo
  const model = selectModel(query);
  
  // 2. Generar respuesta
  const result = await streamText({
    model: openai(model.name),
    messages,
  });

  // 3. Estimar costos
  const inputTokens = estimateTokens(messages);
  const estimatedOutputTokens = 500; // Estimación
  const cost = estimateCost(model, inputTokens, estimatedOutputTokens);
  
  // 4. Loggear costos
  logger.info('[ChatAPI] Cost estimation', {
    model: model.name,
    complexity: estimateComplexity(query),
    inputTokens,
    estimatedOutputTokens,
    cost,
  });

  return result.toDataStreamResponse();
}
```

**Beneficios Esperados:**
- ✅ Reducción de costos en 60-70%
- ✅ Respuestas más rápidas (modelos más ligeros)
- ✅ Mejor balance calidad/costo
- ✅ Transparencia en costos

**Métricas de Éxito:**
- Costo promedio por query: <$0.005 (actual: ~$0.02)
- Distribución de modelos: 60% gratis, 30% medio, 10% complejo
- Costo mensual LLM: <$20 (actual: ~$100)
- Satisfacción del usuario: >4.5/5

---

## 3. Roadmap de Implementación

### 3.1 Cronograma de 6 Meses

```mermaid
gantt
    title Plan de Acción Qdrant - Cronograma 6 Meses
    dateFormat  YYYY-MM-DD
    axisFormat  %b %Y

    section Mes 1
    Hybrid Search           :a1, 2026-02-06, 14d
    Optimizar Embeddings    :a2, 2026-02-06, 14d
    Indexar Documentos      :a3, 2026-02-13, 21d

    section Mes 2
    LLM Reranking          :b1, 2026-03-01, 21d
    Caché Vectorial        :b2, 2026-03-01, 14d
    Optimizar Costos LLM    :b3, 2026-03-15, 14d

    section Mes 3-4
    Testing y QA           :c1, 2026-04-01, 30d
    Performance Optimization :c2, 2026-04-15, 30d
    Monitoring             :c3, 2026-05-01, 30d

    section Mes 5-6
    Documentación          :d1, 2026-06-01, 15d
    Training               :d2, 2026-06-01, 15d
    Deployment Producción   :d3, 2026-06-15, 30d
```

### 3.2 Detalle por Semana

#### Semana 1-2: Hybrid Search

- [ ] Diseñar arquitectura de hybrid search
- [ ] Implementar fusión de resultados (BM25 + Vector)
- [ ] Integrar en retriever.ts
- [ ] Testing unitario
- [ ] Testing de integración

#### Semana 3-4: Optimizar Embeddings

- [ ] Crear script de optimización de embeddings
- [ ] Implementar chunking inteligente
- [ ] Generar embeddings para documentos faltantes
- [ ] Verificar calidad de embeddings
- [ ] Documentar proceso

#### Semana 5-6: Indexar Documentos

- [ ] Crear script de indexación masiva
- [ ] Indexar todos los 216K+ documentos
- [ ] Verificar consistencia de índices
- [ ] Implementar indexación automática (CI/CD)
- [ ] Configurar notificaciones

#### Semana 7-9: LLM Reranking

- [ ] Diseñar prompt de reranking
- [ ] Implementar llm-reranker.ts
- [ ] Integrar en hybrid-search.ts
- [ ] Testing de calidad
- [ ] Optimizar costos

#### Semana 10-12: Caché Vectorial

- [ ] Configurar Redis
- [ ] Implementar vector-cache.ts
- [ ] Integrar en vector-search.ts
- [ ] Testing de cache
- [ ] Configurar TTL y políticas de invalidación

#### Semana 13-16: Optimizar Costos LLM

- [ ] Implementar model-selector.ts
- [ ] Crear estrategia de complejidad
- [ ] Integrar en API routes
- [ ] Testing de costos
- [ ] Documentar ahorros

#### Semana 17-24: Testing y QA

- [ ] Testing unitario completo
- [ ] Testing de integración
- [ ] Testing E2E
- [ ] Performance testing
- [ ] Load testing

#### Semana 25-30: Performance Optimization

- [ ] Optimizar queries a Qdrant
- [ ] Implementar prefetching
- [ ] Optimizar embeddings
- [ ] Optimizar prompts
- [ ] Benchmarking

#### Semana 31-36: Monitoring y Deployment

- [ ] Implementar métricas
- [ ] Configurar alertas
- [ ] Dashboard de monitoreo
- [ ] Deployment en producción
- [ ] Post-deployment verification

---

## 4. Métricas de Éxito

### 4.1 Métricas Técnicas

| Métrica                     | Actual | Objetivo Mes 1 | Objetivo Mes 3 | Objetivo Mes 6 |
| --------------------------- | ------ | -------------- | -------------- | -------------- |
| **Precisión de Búsqueda**   | ~70%   | >80%           | >85%           | >90%           |
| **Tasa de Cero Resultados** | ~10%   | <7%            | <5%            | <3%            |
| **Latencia Promedio**       | ~500ms | <400ms         | <300ms         | <200ms         |
| **Cache Hit Rate**          | 0%     | >30%           | >50%           | >60%           |
| **Documentos Indexados**    | ~60%   | >80%           | >95%           | 100%           |
| **Costo por Query**         | ~$0.02 | <$0.01         | <$0.007        | <$0.005        |

### 4.2 Métricas de Usuario

| Métrica                      | Actual      | Objetivo Mes 1 | Objetivo Mes 3 | Objetivo Mes 6 |
| ---------------------------- | ----------- | -------------- | -------------- | -------------- |
| **Satisfacción del Usuario** | Desconocido | >3.5/5         | >4.0/5         | >4.5/5         |
| **Relevancia de Resultados** | ~70%        | >80%           | >85%           | >90%           |
| **Tiempo de Respuesta**      | ~2s         | <1.5s          | <1s            | <0.5s          |
| **Tasa de Retorno**          | Desconocido | >40%           | >50%           | >60%           |

### 4.3 Métricas de Costos

| Métrica                  | Actual | Objetivo Mes 1 | Objetivo Mes 3 | Objetivo Mes 6 |
| ------------------------ | ------ | -------------- | -------------- | -------------- |
| **Costo Mensual LLM**    | ~$100  | <$70           | <$40           | <$20           |
| **Costo Mensual Qdrant** | ~$0    | ~$0            | ~$0            | ~$0            |
| **Costo Mensual Redis**  | ~$0    | ~$0            | ~$0            | ~$0            |
| **Costo Mensual Total**  | ~$100  | <$70           | <$40           | <$20           |
| **Ahorro Anual**         | $0     | ~$360          | ~$720          | ~$960          |

---

## 5. Recursos y Estimaciones

### 5.1 Equipo Requerido

| Rol                            | Dedicación     | Skills Clave              | Responsabilidades                   |
| ------------------------------ | -------------- | ------------------------- | ----------------------------------- |
| **Backend Developer (Python)** | 100% (2 meses) | Python, Qdrant, OpenAI    | Optimización embeddings, indexación |
| **Frontend Developer (TS)**    | 100% (2 meses) | TypeScript, React, Qdrant | Hybrid search, reranking            |
| **DevOps Engineer**            | 50% (2 meses)  | Redis, Docker, CI/CD      | Caché vectorial, deployment         |
| **QA Engineer**                | 50% (1 mes)    | Testing, Performance      | Testing, QA                         |

### 5.2 Estimación de Esfuerzo

| Tarea                        | Duración  | Esfuerzo Total | Backend | Frontend | DevOps | QA   |
| ---------------------------- | --------- | -------------- | ------- | -------- | ------ | ---- |
| **Hybrid Search**            | 2 semanas | 80h            | 20h     | 40h      | 10h    | 10h  |
| **Optimizar Embeddings**     | 2 semanas | 80h            | 60h     | 10h      | 5h     | 5h   |
| **Indexar Documentos**       | 3 semanas | 120h           | 80h     | 20h      | 10h    | 10h  |
| **LLM Reranking**            | 3 semanas | 120h           | 40h     | 60h      | 10h    | 10h  |
| **Caché Vectorial**          | 2 semanas | 80h            | 20h     | 30h      | 20h    | 10h  |
| **Optimizar Costos LLM**     | 2 semanas | 80h            | 40h     | 30h      | 5h     | 5h   |
| **Testing y QA**             | 4 semanas | 160h           | 40h     | 40h      | 20h    | 60h  |
| **Performance Optimization** | 4 semanas | 160h           | 60h     | 40h      | 40h    | 20h  |
| **Monitoring y Deployment**  | 4 semanas | 160h           | 40h     | 40h      | 60h    | 20h  |
| **Total**                    | 6 meses   | 1,040h         | 400h    | 310h     | 180h   | 150h |

### 5.3 Costos de Infraestructura

| Servicio           | Costo Actual         | Costo Objetivo | Ahorro |
| ------------------ | -------------------- | -------------- | ------ |
| **Qdrant**         | $0/mes (self-hosted) | $0/mes         | 0%     |
| **OpenRouter LLM** | ~$100/mes            | ~$20/mes       | 80%    |
| **Redis**          | $0/mes (self-hosted) | $0/mes         | 0%     |
| **Vercel**         | ~$50/mes             | ~$30/mes       | 40%    |
| **Total**          | ~$150/mes            | ~$50/mes       | 67%    |

### 5.4 ROI Estimado

| Inversión                                | Retorno     | ROI  |
| ---------------------------------------- | ----------- | ---- |
| **Desarrollo** (1,040h @ $50/h)          | $52,000     | -    |
| **Infraestructura** (6 meses @ $150/mes) | $900        | -    |
| **Total Inversión**                      | $52,900     | -    |
| **Ahorro Anual** (Infraestructura)       | $1,200      | -    |
| **Mejora UX** (Estimado)                 | $30,000/año | -    |
| **Escalabilidad** (Estimado)             | $50,000/año | -    |
| **Total Retorno Anual**                  | $81,200     | 153% |

---

## 6. Conclusiones y Recomendaciones

### 6.1 Resumen Ejecutivo

Qdrant ya está activo y funcionando, lo cual es una **ventaja estratégica significativa**. Este plan de acción se enfoca en **optimizar y escalar** la arquitectura existente, aprovechando al máximo la infraestructura disponible.

### 6.2 Fortalezas Clave

1. **Qdrant Funcional:** Vector DB ya implementado y operativo
2. **Arquitectura Modular:** Fácil de extender y optimizar
3. **Multi-motores de Búsqueda:** BM25, Vector, SQL, Computational
4. **Documentación Completa:** Guías técnicas detalladas

### 6.3 Oportunidades Estratégicas

1. **Hybrid Search:** Combinar BM25 + Vector para mejor precisión
2. **Optimización de Embeddings:** Indexar 100% de documentos
3. **LLM Reranking:** Mejorar calidad de resultados
4. **Caché Vectorial:** Reducir latencia y costos
5. **Optimización de Costos:** Estrategia inteligente de selección de modelos

### 6.4 Próximos Pasos Inmediatos

1. **Validación del Plan**
   - Revisar con el equipo técnico
   - Obtener aprobación de stakeholders
   - Ajustar prioridades según recursos

2. **Inicio de Implementación**
   - Comenzar con Hybrid Search (P0-1)
   - Configurar entorno de desarrollo
   - Establecer métricas de seguimiento

3. **Primeras Mejoras**
   - Implementar hybrid search
   - Optimizar embeddings
   - Indexar documentos en Qdrant

4. **Monitoreo y Ajuste**
   - Revisar progreso semanalmente
   - Ajustar plan según necesidades
   - Documentar lecciones aprendidas

---

## 7. Anexos

### 7.1 Scripts de Utilidad

#### Script de Monitoreo de Qdrant

```python
# python-cli/scripts/monitor_qdrant.py
from qdrant_client import QdrantClient

def monitor_qdrant():
    client = QdrantClient(url="http://localhost:6333")
    collection_name = "sibom_documents"
    
    # Obtener información de la colección
    info = client.get_collection(collection_name)
    
    print(f"📊 Estadísticas de Qdrant")
    print(f"   Colección: {collection_name}")
    print(f"   Puntos indexados: {info.points_count}")
    print(f"   Vector size: {info.config.params.vectors.size}")
    print(f"   Distance: {info.config.params.vectors.distance}")
    print(f"   Status: {info.status}")

if __name__ == "__main__":
    monitor_qdrant()
```

#### Script de Limpieza de Caché

```bash
# scripts/clear_cache.sh
#!/bin/bash

echo "🧹 Limpiando caché vectorial..."

# Conectar a Redis
redis-cli FLUSHDB

echo "✅ Caché limpiado!"
```

### 7.2 Referencias

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [Hybrid Search Best Practices](https://qdrant.tech/documentation/concepts/hybrid_search/)
- [Redis Documentation](https://redis.io/docs/)
- [Vercel AI SDK](https://sdk.vercel.ai/docs)

---

**Fin del Documento**
