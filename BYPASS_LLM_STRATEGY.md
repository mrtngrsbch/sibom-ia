# Estrategia de Bypass del LLM - Ahorro Masivo de Tokens

## 🎯 Objetivo

Reducir el consumo de tokens del LLM respondiendo queries simples **DIRECTAMENTE desde el índice JSON** sin necesidad de procesamiento con IA.

## 📊 Problema Identificado

### Antes de la Optimización
- **Query:** "decretos carlos tejedor de 2025"
- **Tokens de entrada:** 60,625 tokens ($0.18)
- **Tokens de salida:** 48 tokens ($0.0007)
- **Total:** $0.1826 por query
- **Problema:** Enviamos TODO el contexto al LLM solo para que genere un resumen de 2 líneas

### Análisis del Desperdicio
- El LLM recibe 500 documentos completos en el contexto
- Solo genera: "Se encontraron 500 decretos de Carlos Tejedor del año 2025..."
- **95% de los tokens son desperdicio** - el LLM no necesita leer los documentos para contar

## 💡 Solución Implementada

### Clasificador de Intención de Query

**Archivo:** `chatbot/src/lib/query-intent-classifier.ts`

Clasifica queries en 10 categorías:

#### ✅ Queries SIN LLM (respuesta directa desde JSON)

1. **`simple-listing`** - Listados simples
   - Ejemplos: "decretos de carlos tejedor 2025", "ordenanzas de merlo"
   - Respuesta: Contar en índice + generar template
   - Ahorro: ~60,000 tokens

2. **`count`** - Conteos
   - Ejemplos: "cuántas ordenanzas hay en merlo", "cantidad de decretos 2025"
   - Respuesta: Contar en índice
   - Ahorro: ~60,000 tokens

3. **`search-by-number`** - Búsqueda por número
   - Ejemplos: "ordenanza 2947 de carlos tejedor", "decreto 123"
   - Respuesta: Buscar en índice por número
   - Ahorro: ~60,000 tokens

4. **`latest`** - Última normativa
   - Ejemplos: "última ordenanza de merlo", "decreto más reciente"
   - Respuesta: Ordenar por fecha + tomar primera
   - Ahorro: ~60,000 tokens

5. **`off-topic`** - Fuera de tema
   - Ejemplos: "cómo está el clima", "receta de pizza"
   - Respuesta: Template pre-definido
   - Ahorro: ~60,000 tokens

#### ❌ Queries CON LLM (requieren procesamiento)

6. **`content-analysis`** - Análisis de contenido
   - Ejemplos: "qué dice la ordenanza 2947 sobre donaciones"
   - Requiere: Leer contenido + analizar
   - Tokens: Normal (~4,000)

7. **`semantic-search`** - Búsqueda semántica
   - Ejemplos: "ordenanzas relacionadas con tránsito"
   - Requiere: BM25 + ranking semántico
   - Tokens: Normal (~4,000)

8. **`comparison`** - Comparaciones
   - Ejemplos: "diferencias entre ordenanza X y Y"
   - Requiere: Leer ambos documentos + comparar
   - Tokens: Alto (~8,000)

9. **`faq`** - Preguntas frecuentes
   - Ejemplos: "qué municipios hay disponibles", "cómo funciona"
   - Requiere: LLM económico (Gemini Flash)
   - Tokens: Bajo (~500)

10. **`date-range`** - Rango de fechas (futuro)
    - Ejemplos: "ordenanzas de enero 2025"
    - Actualmente: Filtro + listado simple
    - Tokens: 0 (respuesta directa)

### Flujo de Decisión

```
Usuario hace query
    ↓
classifyQueryIntent(query)
    ↓
¿needsLLM = false?
    ↓ SÍ
generateDirectResponse()
    ↓
Devolver respuesta + fuentes
    ↓
0 tokens consumidos ✅
    
    ↓ NO
Cargar contexto RAG
    ↓
Llamar LLM
    ↓
~4,000-60,000 tokens ❌
```

## 📈 Métricas de Ahorro

### Queries Comunes y su Ahorro

| Query | Antes | Después | Ahorro |
|-------|-------|---------|--------|
| "decretos carlos tejedor 2025" | 60,625 tokens ($0.18) | 0 tokens ($0.00) | **100%** |
| "cuántas ordenanzas hay en merlo" | 60,625 tokens ($0.18) | 0 tokens ($0.00) | **100%** |
| "ordenanza 2947" | 4,000 tokens ($0.012) | 0 tokens ($0.00) | **100%** |
| "última ordenanza de merlo" | 4,000 tokens ($0.012) | 0 tokens ($0.00) | **100%** |
| "qué dice la ordenanza 2947 sobre X" | 4,000 tokens ($0.012) | 4,000 tokens ($0.012) | 0% (necesita LLM) |

### Proyección de Ahorro Mensual

Asumiendo 1,000 queries/mes:

**Distribución estimada:**
- 60% queries simples (listados, conteos) → 600 queries
- 20% búsquedas específicas → 200 queries
- 15% análisis de contenido → 150 queries
- 5% FAQ → 50 queries

**Antes:**
- 600 × $0.18 = $108.00 (listados masivos)
- 200 × $0.012 = $2.40 (búsquedas)
- 150 × $0.012 = $1.80 (análisis)
- 50 × $0.0007 = $0.035 (FAQ)
- **Total: $112.24/mes**

**Después:**
- 600 × $0.00 = $0.00 (bypass LLM) ✅
- 200 × $0.00 = $0.00 (bypass LLM) ✅
- 150 × $0.012 = $1.80 (necesita LLM)
- 50 × $0.0007 = $0.035 (FAQ económico)
- **Total: $1.84/mes**

**Ahorro: $110.40/mes (98.4%)**

## 🔧 Implementación Técnica

### 1. Clasificador de Intención

```typescript
// chatbot/src/lib/query-intent-classifier.ts
export function classifyQueryIntent(query: string): QueryIntentResult {
  // Detecta patrones en la query
  // Retorna: { intent, needsLLM, confidence, reason }
}
```

### 2. Generador de Respuestas Directas

```typescript
export function generateDirectResponse(
  intent: QueryIntent,
  sources: any[],
  filters: { municipality?, type?, year? }
): string {
  // Genera respuesta usando templates
  // Sin llamar al LLM
}
```

### 3. Integración en API Route

```typescript
// chatbot/src/app/api/chat/route.ts

// Clasificar intención
const intentResult = classifyQueryIntent(query);

// Si NO necesita LLM, bypass
if (!intentResult.needsLLM) {
  const directResponse = generateDirectResponse(
    intentResult.intent,
    retrievedContext.sources,
    filters
  );
  
  // Devolver respuesta directa (0 tokens)
  return streamDirectResponse(directResponse, sources);
}

// Si necesita LLM, continuar normal
const result = streamText({ model, system, messages });
```

### 4. Mejora en UI - Contador de Fuentes

```typescript
// chatbot/src/components/chat/Citations.tsx
<h4>
  {sources.length} Fuentes Consultadas
</h4>
```

## 🧪 Testing

### Casos de Prueba

1. **Listado masivo**
   - Query: "decretos carlos tejedor de 2025"
   - Esperado: 0 tokens, respuesta directa
   - Verificar: Log muestra "BYPASS LLM"

2. **Conteo**
   - Query: "cuántas ordenanzas hay en merlo"
   - Esperado: 0 tokens, número exacto
   - Verificar: Respuesta sin llamar LLM

3. **Búsqueda por número**
   - Query: "ordenanza 2947"
   - Esperado: 0 tokens, documento específico
   - Verificar: Bypass LLM

4. **Análisis de contenido (necesita LLM)**
   - Query: "qué dice la ordenanza 2947 sobre donaciones"
   - Esperado: ~4,000 tokens, análisis detallado
   - Verificar: LLM se llama normalmente

### Logs de Verificación

```
[ChatAPI] 🎯 Intención detectada: simple-listing (confidence: 0.95, needsLLM: false)
[ChatAPI] 📝 Razón: Listado simple - respuesta directa desde índice
[ChatAPI] 🚀 BYPASS LLM - Generando respuesta directa
[ChatAPI] ✅ Respuesta directa generada (0 tokens LLM)
[ChatAPI] 💰 Ahorro estimado: ~60,000 tokens (~$0.18)
```

## 📋 Checklist de Implementación

- [x] ✅ Crear clasificador de intención (`query-intent-classifier.ts`)
- [x] ✅ Implementar generador de respuestas directas
- [x] ✅ Integrar bypass en API route
- [x] ✅ Agregar contador de fuentes en UI
- [x] ✅ Logging detallado para debugging
- [ ] ⏳ Tests unitarios para clasificador
- [ ] ⏳ Tests de integración para bypass
- [ ] ⏳ Monitoreo de ahorro real en producción
- [ ] ⏳ Dashboard de métricas de uso

## 🚀 Próximos Pasos

### Fase 2: Optimizaciones Adicionales

1. **Cache de respuestas frecuentes**
   - Guardar queries comunes en localStorage
   - Evitar incluso la búsqueda en índice
   - Ahorro adicional: latencia

2. **Índice SQL.js (opcional)**
   - Migrar índice JSON a SQLite en memoria
   - Queries SQL más rápidas
   - Mejor para datasets >100MB

3. **Prefetching inteligente**
   - Precargar municipios populares
   - Anticipar queries comunes
   - Mejor UX

4. **Compresión de índice**
   - Usar MessagePack en vez de JSON
   - Reducir tamaño de descarga
   - Mejor performance en móviles

### Fase 3: Analytics y Monitoreo

1. **Dashboard de métricas**
   - Queries por tipo de intención
   - Ahorro de tokens en tiempo real
   - Queries más frecuentes

2. **A/B Testing**
   - Comparar bypass vs LLM siempre
   - Medir satisfacción del usuario
   - Optimizar clasificador

## 📚 Referencias

- **Clasificador:** `chatbot/src/lib/query-intent-classifier.ts`
- **API Route:** `chatbot/src/app/api/chat/route.ts`
- **UI Citations:** `chatbot/src/components/chat/Citations.tsx`
- **Documentación anterior:** `FIX_MASSIVE_LISTINGS.md`

## 🎓 Lecciones Aprendidas

1. **No todo necesita IA**: El 80% de las queries son simples y se pueden responder con lógica básica
2. **Los datos estructurados son oro**: Nuestros JSON tienen toda la info necesaria
3. **El LLM es caro**: 60,000 tokens para decir "hay 500 decretos" es un desperdicio
4. **La clasificación temprana es clave**: Detectar la intención ANTES de cargar contexto
5. **Los templates son suficientes**: Para queries simples, un template bien hecho es mejor que el LLM

## 💬 Feedback del Usuario

> "60,625 tokens es una locura! Debemos pensar en otra estrategia que no consuma tokens."

**Solución implementada:** Bypass completo del LLM para queries simples.

**Resultado:** 98.4% de ahorro en costos mensuales estimados.
