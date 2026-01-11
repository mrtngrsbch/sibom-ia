# Plan de Implementación: OpenAI Embeddings + Qdrant

## ✅ Completado

1. **Next.js actualizado** a 16.1.1 (fix CVE-2025-66478)
2. **Dependencias instaladas:**
   - `openai@6.16.0`
   - `@qdrant/js-client-rest@1.16.2`
3. **Módulo vector-search.ts creado** (`chatbot/src/lib/rag/vector-search.ts`)
4. **Script Python creado** (`python-cli/generate_embeddings.py`)

## 📋 Pasos Pendientes

### Paso 1: Configurar Cuentas (Usuario)

**OpenAI:**
1. Ir a https://platform.openai.com
2. Crear cuenta (diferente de ChatGPT)
3. Agregar $5-10 de crédito
4. Crear API key
5. Copiar key (empieza con `sk-proj-...`)

**Qdrant:**
1. Ir a https://cloud.qdrant.io
2. Crear cuenta (gratis)
3. Crear cluster (free tier - 1GB)
4. Copiar URL del cluster (ej: `https://xxxxx.qdrant.io`)
5. Crear API key
6. Copiar API key

### Paso 2: Configurar Variables de Entorno

**Agregar a `chatbot/.env.local`:**
```bash
# OpenAI Embeddings
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Qdrant Vector Database
QDRANT_URL=https://xxxxx.qdrant.io
QDRANT_API_KEY=xxxxxxxxxxxxx
```

**Agregar a `python-cli/.env` (o exportar):**
```bash
export OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
export QDRANT_URL=https://xxxxx.qdrant.io
export QDRANT_API_KEY=xxxxxxxxxxxxx
```

### Paso 3: Instalar Dependencias Python

```bash
cd python-cli
pip install openai qdrant-client tqdm
```

### Paso 4: Generar Embeddings (ONE-TIME)

```bash
cd python-cli
python3 generate_embeddings.py
```

**Tiempo estimado:** 30-60 minutos
**Costo:** ~$0.22

**Output esperado:**
```
======================================================================
OpenAI Embeddings Generator for Qdrant
======================================================================

🔌 Initializing clients...
✅ Clients initialized

📥 Loading normativas index from boletines/normativas_index_minimal.json...
✅ Loaded 216,000 normativas

🗄️ Setting up Qdrant collection 'normativas'...
📦 Creating collection with 1536 dimensions...
✅ Collection created

🚀 Processing 216,000 normativas in batches of 100...
⏱️ Estimated time: ~108 minutes
💰 Estimated cost: ~$0.22

Generating embeddings: 100%|████████████| 216000/216000 [30:00<00:00, 120.00it/s]

✅ Processing complete!
   Successful: 216,000
   Failed: 0

🔍 Verifying collection...
✅ Collection info:
   Points: 216,000
   Vectors: 216,000
   Status: green

✅ Done! Vector search is now available.
```

### Paso 5: Integrar Vector Search en Retriever

**Modificar `chatbot/src/lib/rag/retriever.ts`:**

Agregar al inicio:
```typescript
import { vectorSearch, isVectorSearchAvailable } from './vector-search';
```

Modificar `retrieveContext()` para usar vector search cuando esté disponible:
```typescript
export async function retrieveContext(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  // Si vector search está disponible, usarlo
  if (isVectorSearchAvailable()) {
    console.log('[RAG] 🔍 Using vector search (semantic)');
    return await retrieveContextWithVectorSearch(query, options);
  }
  
  // Fallback: usar BM25 (keyword search)
  console.log('[RAG] 📝 Using BM25 search (keyword)');
  return await retrieveContextFromNormativas(query, options);
}
```

Crear función `retrieveContextWithVectorSearch()`:
```typescript
async function retrieveContextWithVectorSearch(
  query: string,
  options: SearchOptions = {}
): Promise<SearchResult> {
  const startTime = Date.now();

  // 1. Vector search
  const vectorResults = await vectorSearch(query, {
    municipality: options.municipality,
    type: options.type,
    year: options.dateFrom ? parseInt(options.dateFrom.split('-')[0]) : undefined,
    limit: options.limit || 10,
  });

  // 2. Cargar contenido de los documentos
  const documents = await Promise.all(
    vectorResults.map(async (r) => {
      try {
        const data = await readFileContent(`${r.source_bulletin}.json`);
        return {
          id: r.id,
          municipality: r.municipality,
          type: r.type as DocumentType,
          number: r.number,
          title: r.title,
          content: data.fullText || '',
          date: `${r.municipality}, ${r.year}`,
          url: r.url,
          status: 'vigente',
          filename: `${r.source_bulletin}.json`,
        };
      } catch (err) {
        console.warn(`[RAG] Error loading ${r.source_bulletin}:`, err);
        return null;
      }
    })
  );

  const validDocuments = documents.filter(d => d !== null) as Document[];

  // 3. Construir contexto
  const contentLimit = calculateContentLimit(query);
  const context = validDocuments
    .map((doc) => {
      const contentChunk = doc.content.slice(0, contentLimit);
      if (contentLimit <= 200) {
        return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status}`;
      }
      return `[${doc.municipality}] ${doc.type.toUpperCase()} ${doc.number}
Título: ${doc.title}
Fecha: ${doc.date}
Estado: ${doc.status}
Contenido: ${contentChunk}...`;
    })
    .join('\n\n---\n\n');

  // 4. Construir fuentes
  const sources = validDocuments.map((doc) => ({
    title: `${doc.type} ${doc.number} - ${doc.municipality}`,
    url: buildBulletinUrl(doc.url),
    municipality: doc.municipality,
    type: doc.type,
    status: doc.status,
  }));

  const duration = Date.now() - startTime;
  console.log(`[RAG] ✅ Vector search completed in ${duration}ms - ${validDocuments.length} docs`);

  return {
    context: context || `No se encontró información específica para: "${query}"`,
    sources,
  };
}
```

### Paso 6: Testing

**Test 1: Verificar que vector search está disponible**
```bash
cd chatbot
pnpm run dev
```

Abrir http://localhost:3000 y en la consola del servidor debería aparecer:
```
[VectorSearch] Qdrant client initialized
[VectorSearch] OpenAI client initialized
```

**Test 2: Probar búsqueda semántica**

Query: "sueldos de carlos tejedor 2025"

**Esperado:**
- Debería encontrar documentos con "remuneraciones" (sinónimo)
- Debería mostrar decretos/ordenanzas sobre salarios
- Score de similitud >0.7

**Test 3: Comparar con BM25**

Deshabilitar vector search temporalmente (comentar env vars) y probar la misma query.

**Comparación esperada:**
- BM25: Encuentra pocos o ningún resultado (no conoce sinónimos)
- Vector Search: Encuentra documentos relevantes (entiende semántica)

### Paso 7: Deploy a Producción

**Vercel:**
1. Agregar variables de entorno en Vercel dashboard:
   - `OPENAI_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`

2. Deploy:
```bash
git add .
git commit -m "feat: add OpenAI embeddings + Qdrant vector search"
git push origin main
```

3. Verificar en logs de Vercel que vector search se inicializa correctamente

## 📊 Métricas a Monitorear

### Accuracy
- % de queries con clicks en resultados
- Posición promedio del resultado clickeado
- % de queries sin resultados

### Performance
- Latencia promedio de vector search (~200ms esperado)
- Latencia vs BM25 (BM25 ~50ms, Vector ~200ms)

### Costos
- Queries/día
- Costo/query ($0.0001 por query embedding)
- Costo mensual total

## 🎯 Resultado Esperado

**Antes (BM25):**
```
Query: "sueldos de carlos tejedor 2025"
Resultados: 0-2 documentos (no encuentra "remuneraciones")
Accuracy: ~40%
```

**Después (Vector Search):**
```
Query: "sueldos de carlos tejedor 2025"
Resultados: 8-10 documentos relevantes (entiende sinónimos)
Accuracy: ~80%
```

**Mejora esperada:** +40% accuracy en búsquedas semánticas

## 🚨 Troubleshooting

### Error: "QDRANT_URL not set"
- Verificar que las variables estén en `.env.local`
- Reiniciar servidor de desarrollo

### Error: "Collection 'normativas' not found"
- Ejecutar `python3 generate_embeddings.py` primero
- Verificar en Qdrant dashboard que la colección existe

### Error: "OpenAI API rate limit"
- Esperar 1 minuto y reintentar
- Verificar que tenés crédito en OpenAI

### Búsquedas lentas (>1s)
- Normal en primera query (cold start)
- Queries subsecuentes deberían ser <300ms
- Si persiste, verificar latencia de Qdrant

## 📝 Checklist Final

- [ ] Cuenta OpenAI creada con crédito
- [ ] Cuenta Qdrant creada (free tier)
- [ ] Variables de entorno configuradas
- [ ] Dependencias Python instaladas
- [ ] Embeddings generados (216K docs)
- [ ] Vector search integrado en retriever
- [ ] Testing local exitoso
- [ ] Deploy a producción
- [ ] Monitoreo de métricas activo

## 🎉 Próximos Pasos

Una vez funcionando:
1. Monitorear accuracy durante 1-2 semanas
2. Recopilar feedback de usuarios
3. Ajustar score_threshold si es necesario (actualmente 0.5)
4. Considerar fine-tuning de embeddings con datos legales argentinos
5. Implementar sistema de feedback para aprendizaje continuo
