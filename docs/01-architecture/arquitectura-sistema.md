# Arquitectura con Function Calling - LLM + Tools

**Date:** 2026-01-10  
**Updated:** 2026-02-06  
**Status:** 📋 Propuesta  
**Goal:** Permitir que el LLM decida cuándo usar SQL vs búsqueda de contenido

> **Stack real:** LLM: Gemini 3 Flash (principal), GLM 4.7 (alternativo) | Vector DB: Qdrant | Embeddings: text-embedding-3-small

## Problema Actual

El usuario pregunta: **"¿Cómo sabe el LLM qué hay en SQL vs qué hay en los JSON?"**

**Respuesta:** Actualmente NO lo sabe. Nosotros decidimos con código cuándo usar SQL.

## Solución: Function Calling (Tools)

Implementar **tools** que el LLM puede llamar para acceder a diferentes fuentes de datos:

### Tool 1: `query_metadata_sql`
**Propósito:** Consultas sobre metadatos (contar, listar, comparar)  
**Datos disponibles en SQL:**
- `municipality` - Nombre del municipio
- `type` - Tipo de normativa (ordenanza, decreto, resolución, etc.)
- `number` - Número de la normativa
- `year` - Año de publicación
- `date` - Fecha exacta (YYYY-MM-DD)
- `title` - Título de la normativa
- `url` - URL al documento en SIBOM
- `status` - Estado (vigente, derogada, etc.)

**Ejemplos de uso:**
- "¿Cuántos decretos hay de Carlos Tejedor en 2025?"
- "Lista todas las ordenanzas de Merlo"
- "¿Qué municipio tiene más decretos?"
- "Compara cantidad de normativas entre municipios"

**Schema:**
```typescript
const queryMetadataSQL = tool({
  description: `Query the SQL database for metadata about normativas.
  
  Use this tool when the user asks about:
  - Counting normativas (cuántas, cantidad, total)
  - Listing by metadata (all decretos, all ordenanzas)
  - Comparing municipalities (cuál tiene más, diferencias)
  - Finding by number/year (ordenanza 2947, decretos de 2025)
  
  Available fields: municipality, type, number, year, date, title, url, status
  
  DO NOT use this for content-based queries (e.g., "ordenanzas sobre tránsito")`,
  
  parameters: z.object({
    query: z.string().describe('Natural language query about metadata'),
    filters: z.object({
      municipality: z.string().optional(),
      type: z.enum(['ordenanza', 'decreto', 'resolucion', 'disposicion', 'convenio']).optional(),
      year: z.number().optional(),
      dateFrom: z.string().optional(),
      dateTo: z.string().optional(),
    }).optional()
  }),
  
  execute: async ({ query, filters }) => {
    // Convert natural language to SQL and execute
    const result = await executeQuery(query, filters);
    return result;
  }
});
```

### Tool 2: `search_content`
**Propósito:** Búsqueda semántica en el contenido de las normativas  
**Datos disponibles en JSON:**
- Contenido completo de cada normativa
- Texto extraído de PDFs
- Tablas estructuradas (montos, categorías, etc.)
- Artículos y considerandos

**Ejemplos de uso:**
- "Ordenanzas sobre sueldos de Carlos Tejedor"
- "Normativas de tránsito en Merlo"
- "Decretos que hablan de tasas municipales"
- "¿Qué dice la ordenanza 2947 sobre habilitaciones?"

**Schema:**
```typescript
const searchContent = tool({
  description: `Search the full content of normativas using semantic search.
  
  Use this tool when the user asks about:
  - Topics/themes (sueldos, tránsito, salud, educación)
  - Content of specific normativas (qué dice, contenido)
  - Semantic search (ordenanzas sobre X, decretos que hablan de Y)
  
  This searches the FULL TEXT content, not just metadata.`,
  
  parameters: z.object({
    query: z.string().describe('Natural language query about content'),
    filters: z.object({
      municipality: z.string().optional(),
      type: z.enum(['ordenanza', 'decreto', 'resolucion', 'disposicion', 'convenio']).optional(),
      year: z.number().optional(),
      limit: z.number().default(10).describe('Max results to return')
    }).optional()
  }),
  
  execute: async ({ query, filters }) => {
    // Use BM25 + RAG to search content
    const result = await retrieveContext(query, filters);
    return result;
  }
});
```

### Tool 3: `get_database_stats`
**Propósito:** Información sobre qué datos están disponibles  
**Uso:** Preguntas sobre el sistema

**Schema:**
```typescript
const getDatabaseStats = tool({
  description: `Get statistics about available data in the system.
  
  Use this when the user asks:
  - What municipalities are available?
  - How many documents do we have?
  - What types of normativas exist?`,
  
  parameters: z.object({}),
  
  execute: async () => {
    const stats = await getDatabaseStats();
    return stats;
  }
});
```

## Implementación en route.ts

```typescript
// Define tools
const tools = {
  query_metadata_sql: queryMetadataSQL,
  search_content: searchContent,
  get_database_stats: getDatabaseStatsToolimport { tool } from 'ai';
import { z } from 'zod';

// En el streamText
const result = streamText({
  model: openrouter(modelId), // TODO: actualizar a Gemini 3 Flash / GLM 4.7 via OpenRouter
  system: systemPrompt,
  messages: coreMessages,
  temperature: 0.3,
  maxTokens: 4000,
  
  // ✅ AGREGAR TOOLS
  tools: {
    query_metadata_sql: queryMetadataSQL,
    search_content: searchContent,
    get_database_stats: getDatabaseStatsTool
  },
  
  // Permitir múltiples llamadas a tools
  maxToolRoundtrips: 3,
  
  onFinish: (completion) => {
    // Log tool calls
    if (completion.toolCalls && completion.toolCalls.length > 0) {
      console.log(`[ChatAPI] 🔧 Tools used: ${completion.toolCalls.map(t => t.toolName).join(', ')}`);
    }
    
    // ... existing onFinish logic
  }
});
```

## System Prompt Actualizado

```markdown
# Sistema de Prompt para Chatbot Legal Municipal

## Herramientas Disponibles

Tenés acceso a 3 herramientas para responder consultas:

### 1. `query_metadata_sql` - Base de Datos SQL
**Cuándo usar:** Consultas sobre METADATOS (contar, listar, comparar)
**Datos disponibles:**
- Municipio, tipo, número, año, fecha, título, URL, estado
- Ideal para: conteos, listados, comparaciones entre municipios

**Ejemplos:**
- "¿Cuántos decretos hay de Carlos Tejedor en 2025?" → USA ESTA TOOL
- "Lista todas las ordenanzas de Merlo" → USA ESTA TOOL
- "¿Qué municipio tiene más decretos?" → USA ESTA TOOL

### 2. `search_content` - Búsqueda Semántica
**Cuándo usar:** Consultas sobre CONTENIDO (temas, conceptos)
**Datos disponibles:**
- Texto completo de normativas, artículos, considerandos, tablas
- Ideal para: búsqueda por tema, análisis de contenido

**Ejemplos:**
- "Ordenanzas sobre sueldos de Carlos Tejedor" → USA ESTA TOOL
- "Normativas de tránsito en Merlo" → USA ESTA TOOL
- "¿Qué dice la ordenanza 2947 sobre habilitaciones?" → USA ESTA TOOL

### 3. `get_database_stats` - Estadísticas del Sistema
**Cuándo usar:** Preguntas sobre qué datos están disponibles
**Ejemplos:**
- "¿Qué municipios están disponibles?" → USA ESTA TOOL
- "¿Cuántos documentos hay en total?" → USA ESTA TOOL

## Reglas de Uso de Herramientas

1. **SIEMPRE usa una herramienta** antes de responder sobre normativas
2. **Elige la herramienta correcta:**
   - Metadatos (contar, listar) → `query_metadata_sql`
   - Contenido (temas, conceptos) → `search_content`
   - Info del sistema → `get_database_stats`
3. **Podés usar múltiples herramientas** si es necesario
4. **Explicá los resultados** en lenguaje natural después de usar las tools

## Ejemplo de Flujo

**User:** "¿Cuántas ordenanzas sobre tránsito hay en Carlos Tejedor?"

**Pensamiento del LLM:**
1. "tránsito" es un TEMA (contenido) → necesito `search_content`
2. Pero también quiero CONTAR → podría usar `query_metadata_sql` después

**Acción:**
1. Llamar `search_content` con query="ordenanzas sobre tránsito" y filters={municipality: "Carlos Tejedor"}
2. Analizar resultados y contar cuántas son relevantes
3. Responder: "Encontré X ordenanzas de Carlos Tejedor que tratan sobre tránsito: [lista]"
```

## Ventajas de Function Calling

### ✅ Ventajas
1. **El LLM decide** - No necesitamos clasificar queries con regex
2. **Más flexible** - El LLM puede combinar tools según necesidad
3. **Transparente** - Vemos qué tools usa el LLM en los logs
4. **Escalable** - Fácil agregar nuevas tools (ej: `extract_tables`, `compare_content`)

### ⚠️ Consideraciones
1. **Costo** - Cada tool call agrega tokens (pero es mínimo)
2. **Latencia** - Tool calls son secuenciales (pero rápidos con SQL)
3. **Complejidad** - Más código que mantener

## Comparación: Antes vs Después

### Antes (Clasificación Manual)
```typescript
if (isCountQuery(query)) {
  // Usar SQL
} else if (isSemanticSearch(query)) {
  // Usar RAG
} else {
  // ¿?
}
```
**Problema:** Nunca cubrimos todos los casos

### Después (Function Calling)
```typescript
// El LLM decide qué tool usar
const result = streamText({
  tools: { query_metadata_sql, search_content },
  // ...
});
```
**Ventaja:** El LLM entiende la intención y elige la tool correcta

## Implementación Paso a Paso

### Fase 1: Crear Tools (1-2 horas)
- [ ] Implementar `queryMetadataSQL` tool
- [ ] Implementar `searchContent` tool
- [ ] Implementar `getDatabaseStats` tool
- [ ] Agregar tests para cada tool

### Fase 2: Integrar en route.ts (1 hora)
- [ ] Importar `tool` y `z` de Vercel AI SDK
- [ ] Agregar tools al `streamText`
- [ ] Configurar `maxToolRoundtrips`
- [ ] Agregar logging de tool calls

### Fase 3: Actualizar System Prompt (30 min)
- [ ] Documentar cada tool
- [ ] Agregar ejemplos de cuándo usar cada una
- [ ] Agregar reglas de uso

### Fase 4: Testing (1 hora)
- [ ] Probar queries de metadatos
- [ ] Probar queries de contenido
- [ ] Probar queries mixtas
- [ ] Verificar que el LLM elige la tool correcta

## Métricas de Éxito

- ✅ El LLM usa `query_metadata_sql` para conteos/listados
- ✅ El LLM usa `search_content` para búsquedas por tema
- ✅ Respuestas correctas para queries ambiguas
- ✅ Latencia < 3s para queries simples
- ✅ Costo < $0.05 por query

## Próximos Pasos

1. ¿Implementar function calling?
2. ¿O mantener el sistema simplificado actual (solo LLM + RAG)?

**Recomendación:** Implementar function calling. Es la arquitectura correcta y escalable.
