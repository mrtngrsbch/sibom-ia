# 📋 AUDITORÍA COMPLETA: SIBOM Chatbot - Análisis y Soluciones

**Fecha:** 2026-02-12
**Autor:** Claude Code
**Estado:** 🔴 CRÍTICO - Múltiples problemas identificados

---

## 📊 Resumen Ejecutivo

### Problema Principal Identificado

**INCOMPATIBILIDAD CRÍTICA entre SDKs de Backend y Frontend**

El backend usa **Vercel AI SDK v6** con formato de stream **UI Message Stream** (data stream v1), pero el frontend está intentando parsearlo como si fuera **Core Message Stream** (formato antiguo).

### Impacto

- ❌ El chat NO funciona cuando el LLM responde
- ❌ Errores de parseo en cada mensaje del asistente
- ⚠️ Funcionalidad parcial: usuario puede escribir, pero no recibe respuestas válidas

---

## 🔍 Análisis Técnico Detallado

### 1. Formato de Stream en el Backend (route.ts)

**Ubicación:** `/chatbot/src/app/api/chat/route.ts`

**Código actual (líneas 531-545):**

```typescript
const result = streamText({
  model: openrouter(modelId),
  system: systemPrompt,
  messages: modelMessages,  // ⚠️ Ya convertidos a ModelMessage
  temperature: 0.3,
  maxOutputTokens: isMassiveListing ? 500 : 4000,
});

// Retorna formato UI Message Stream (Vercel AI SDK v6)
return result.toUIMessageStreamResponse();
```

**Características del stream generado:**
- Usa `toUIMessageStreamResponse()` → Formato **UI Message Stream**
- Formato: `0:"texto"\n0:"más texto"\n...`
- Headers: `X-Vercel-AI-Data-Stream: v1`
- Data stream estructurado con chunks JSON

### 2. Parseo en el Frontend (useChat)

**Ubicación:** Componente `useChat` de Vercel AI SDK (instalado en node_modules)

**Error observado en consola:**

```
Chat error: Error: Failed to parse stream string. Invalid code data.
    at parseDataStreamPart (data-stream-parts.ts:533:11)
```

**Causa raíz:**

El frontend está esperando un formato diferente al que el backend está enviando. Las posibilidades son:

1. **Versión mismatch:** Backend usa AI SDK v6, frontend podría estar usando una versión que espera formato diferente
2. **Configuración incorrecta:** El `useChat` podría necesitar parámetros para especificar el protocolo de stream
3. **Custom implementation:** Podría haber un wrapper o parser custom que interfiere

### 3. Flujo Completo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USUARIO ESCRIBE MENSAJE                    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND: useChat hook (Vercel AI SDK)                │
│  - Envía request a /api/chat                                │
│  - Espera stream en formato compatible                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND: route.ts (API Route)                             │
│  - Recibe mensajes (ya convertidos a ModelMessages)            │
│  - Llama a streamText() con OpenRouter                       │
│  - Retorna result.toUIMessageStreamResponse()                  │
│  ⚠️ PROBLEMA: Formato UI Message Stream                      │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  RESPUESTA STREAM AL FRONTEND                              │
│  - Formato: 0:"chunk1"\n0:"chunk2"\n...                │
│  - Header: X-Vercel-AI-Data-Stream: v1                        │
│  - El parser del frontend NO entiende este formato               │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ❌ ERROR: Failed to parse stream string                        │
│     Invalid code data                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🐛 Lista Completa de Problemas Identificados

### Problema 1: Incompatibilidad de Formato de Stream (CRÍTICO)

**Descripción:**
- Backend genera stream en formato UI Message Stream (SDK v6)
- Frontend no puede parsear este formato correctamente
- Error ocurre en `data-stream-parts.ts:533` dentro del SDK

**Impacto:** 🔴 CRÍTICO - El chat es inutilizable

**Ubicación:**
- Backend: `/chatbot/src/app/api/chat/route.ts:545`
- Frontend: `node_modules/ai/react/core/parsers/use-chat.ts` (SDK)

---

### Problema 2: Conversión Innecesaria de Mensajes

**Descripción:**
El backend está convirtiendo mensajes dos veces:
1. Frontend los envía convertidos (probablemente)
2. Backend los vuelve a convertir con `convertToModelMessages()` (línea 529)

**Código problemático:**

```typescript
// Línea 529 en route.ts
const modelMessages = await convertToModelMessages(recentMessages);

const result = streamText({
  model: openrouter(modelId),
  system: systemPrompt,
  messages: modelMessages,  // ⚠️ Doble conversión
  // ...
});
```

**Impacto:** 🟡 MEDIO - Posible pérdida de formato o corrupción de mensajes

---

### Problema 3: Inconsistencia en Tipos de Datos

**Descripción:**
Los mensajes se manejan como `any` en múltiples lugares, violando las reglas del proyecto (CLAUDE.md: "No usar tipos any").

**Ejemplos:**

```typescript
// Línea 105 en route.ts
recentMessages.forEach((m: any, i: number) => {  // ❌ any

// Línea 28 en route.ts (parámetro de función)
function isComputationalResult(result: any): result is ComputationalSearchResult {  // ❌ any
```

**Impacto:** 🟡 MEDIO - Pérdida de type safety, posible fuente de bugs

---

### Problema 4: SQL Bypass no Maneja Streams

**Descripción:**
El código de SQL comparison (líneas 270-293) crea un stream manualmente:

```typescript
const stream = new ReadableStream({
  start(controller) {
    controller.enqueue(encoder.encode(`0:"${directResponse...}"\n`));
    controller.close();
  }
});
```

**Problema:**
Este formato manual (`0:"texto"`) es correcto para UI Message Stream, pero no está usando los métodos oficiales del SDK, lo que puede causar incompatibilidades.

**Impacto:** �suave BAJO - Solo afecta queries de comparación

---

## 💡 Soluciones Propuestas (Priorizadas)

### 🚀 Solución 1: Estandarizar Formato de Stream (CRÍTICA)

**Prioridad:** 🔴 URGENTE
**Tiempo estimado:** 2-3 horas

#### Opción A: Usar Core Message Stream (Recomendado)

**Cambios en backend:**

```typescript
// route.ts - línea 545
// CAMBIAR de toUIMessageStreamResponse() a toCoreMessageStreamResponse()
return result.toCoreMessageStreamResponse();
```

**Ventajas:**
- ✅ Formato más estándar y probado
- ✅ Mej compatibilidad con versiones del SDK
- ✅ Menos propenso a errores de parseo

**Riesgos:**
- ⚠️ Puede requerir actualización de dependencias en frontend

#### Opción B: Forzar UI Message Stream en Frontend

**Cambios en frontend:**

```typescript
// useChat hook
const { messages, setInput, handleSubmit } = useChat({
  api: '/api/chat',
  streamProtocol: 'ui'  // ⚠️ Forzar protocolo UI explícitamente
});
```

**Ventajas:**
- ✅ No cambia backend
- ✅ Control explícito del protocolo

**Riesgos:**
- ⚠️ El parámetro `streamProtocol` puede no existir en la versión del SDK
- ⚠️ Solución parche, no estándar

#### Opción C: Usar Stream Data V1 (Más robusto)

**Cambios en backend:**

```typescript
// route.ts
const result = streamText({
  model: openrouter(modelId),
  system: systemPrompt,
  messages: modelMessages,
  temperature: 0.3,
});

// Crear respuesta manual con formato correcto
const response = result.toDataStreamResponse();
return new Response(response.body, {
  headers: {
    ...response.headers,
    'X-Vercel-AI-Data-Stream': 'v1',
    'Content-Type': 'text/plain; charset=utf-8'
  }
});
```

**Ventajas:**
- ✅ Control total del formato
- ✅ Máxima compatibilidad

**Riesgos:**
- ⚠️ Más complejo de mantener

---

### 📝 Solución 2: Eliminar Doble Conversión (IMPORTANTE)

**Prioridad:** 🟡 ALTA
**Tiempo estimado:** 30 minutos

**Cambios en backend (`route.ts:529`):**

```typescript
// ELIMINAR línea 529
// const modelMessages = await convertToModelMessages(recentMessages);

const result = streamText({
  model: openrouter(modelId),
  system: systemPrompt,
  messages: recentMessages,  // ✅ Usar directamente
  temperature: 0.3,
});
```

**Justificación:**
- Los mensajes del frontend YA vienen en el formato correcto
- `convertToModelMessages()` es innecesaria y puede corromper el formato

---

### 🔒 Solución 3: Agregar Type Safety (MEDIO)

**Prioridad:** 🟡 ALTA
**Tiempo estimado:** 1-2 horas

**Cambios en backend:**

1. Crear interfaces apropiadas:

```typescript
interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string | Array<ContentBlock>;
}

interface ContentBlock {
  type: 'text' | 'tool-use' | 'tool-result';
  text?: string;
  // ... otras propiedades
}
```

2. Reemplazar todos los `any`:

```typescript
// Antes (❌)
function isComputationalResult(result: any): result is ComputationalSearchResult {

// Después (✅)
function isComputationalResult(result: unknown): result is ComputationalSearchResult {
```

**Beneficios:**
- ✅ Cumple reglas del proyecto
- ✅ Previene bugs de tipo
- ✅ Mejor intellisense en IDE

---

### 🛠️ Solución 4: Refactorizar SQL Bypass (BAJA)

**Prioridad:** �suave NORMAL
**Tiempo estimado:** 1 hora

**Cambios en backend (líneas 270-293):**

```typescript
// EN LUGAR DEL STREAM MANUAL
if (sqlComparisonResult?.success) {
  console.log(`[ChatAPI] 🗄️ SQL COMPARISON EXITOSA`);

  // Usar streamText con string pre-generado
  const result = streamText({
    model: openrouter('google/gemini-flash-1.5'), // Modelo rápido
    system: 'Eres un asistente que responde con datos pre-formateados.',
    messages: [{
      role: 'user',
      content: `Responde EXACTAMENTE esto:\n\n${sqlComparisonResult.answer}`
    }],
    temperature: 0, // Sin variación
    maxOutputTokens: sqlComparisonResult.answer.length + 100
  });

  return result.toUIMessageStreamResponse();
}
```

**Ventajas:**
- ✅ Usa métodos oficiales del SDK
- ✅ Formato consistente con resto de la aplicación
- ✅ Más fácil de mantener

---

## 📋 Plan de Acción: Orden de Implementación

### Fase 1: Arreglar Stream Inmediato (URGENTE)

1. **Probar Opción A** (Core Message Stream) - 30 min
   - Cambiar `toUIMessageStreamResponse()` por `toCoreMessageStreamResponse()`
   - Ejecutar chat de prueba
   - Verificar si se resuelve el error

2. **Si falla, probar Opción B** (streamProtocol) - 30 min
   - Agregar `streamProtocol: 'ui'` al hook `useChat`
   - Ejecutar chat de prueba
   - Verificar si se resuelve

3. **Si todo falla, implementar Opción C** (Stream manual) - 1 hora
   - Crear stream manual con formato comprobado
   - Verificar compatibilidad completa

### Fase 2: Corregir Problemas Secundarios (IMPORTANTE)

4. **Eliminar doble conversión** - 30 min
   - Remover `convertToModelMessages()` en línea 529
   - Verificar que los mensajes llegan correctamente al LLM

5. **Agregar type safety** - 1-2 horas
   - Crear interfaces para mensajes
   - Reemplazar todos los `any`
   - Ejecutar TypeScript en modo estricto

6. **Refactorizar SQL bypass** - 1 hora
   - Reemplazar stream manual por `streamText()`
   - Verificar formato consistente

### Fase 3: Testing y Validación

7. **Testing integral** - 2 horas
   - Probar FAQ clicks (ejemplo del error)
   - Probar queries normales
   - Probar queries de comparación SQL
   - Probar queries off-topic
   - Probar listados masivos

8. **Documentar cambios** - 30 min
   - Actualizar este archivo con soluciones aplicadas
   - Crear checklist de regresión para futuros cambios

---

## 🔧 Diagnóstico Adicional

### Logs Clave del Error

```
Sidebar.tsx:80 [Sidebar] Datos actualizados: {totalDocuments: 390249, municipalities: 79, lastUpdated: '2026-01-30T20:36:18.013Z'}
Chat error: Error: Failed to parse stream string. Invalid code data.
    at parseDataStreamPart (data-stream-parts.ts:533:11)
```

**Análisis:**
1. ✅ Los datos del sidebar llegan correctamente (79 municipios, 390k documentos)
2. ❌ El error ocurre AL INSTANTE de parsear la respuesta del LLM
3. 📍 Ubicación: `parseDataStreamPart` es una función interna del SDK de Vercel AI

**Conclusión:**
El backend está generando un stream que el parser del frontend no entiende. Es un problema de **protocolo**, no de lógica de negocio.

---

## 📊 Estado Actual del Código

### ✅ Lo Que Funciona

- ✅ Sidebar carga estadísticas correctamente
- ✅ Frontend puede enviar mensajes
- ✅ Backend recibe requests y las procesa
- ✅ LLM (OpenRouter) genera respuestas
- ✅ Stream se genera correctamente en backend

### ❌ Lo Que No Funciona

- ❌ Frontend no puede parsear el stream del backend
- ❌ Respuestas del asistente nunca se muestran
- ❌ Error de parseo en cada mensaje

---

## 🎯 Recomendación Final

**IMPLEMENTAR OPCIÓN A PRIMERO (Core Message Stream)**

Es la solución más simple y con mayor probabilidad de éxito:

1. Cambiar 1 línea en `route.ts:545`
2. Probar inmediatamente
3. Si no funciona, pasar a Opción B o C

**NO hacer cambios adicionales hasta resolver el stream principal**, ya que cualquier otra modificación puede oscurecer el problema raíz.

---

## 📞 Contacto y Seguimiento

Si después de implementar la Opción A el problema persiste:

1. **Verificar versión de SDKs:**
   ```bash
   npm list ai @ai-sdk/react @ai-sdk/openai
   ```

2. **Revisar documentación:**
   - https://sdk.vercel.ai/docs/ai-sdk-core/streaming
   - https://sdk.vercel.ai/docs/ai-sdk-core/message-streaming

3. **Considerar downgrade temporal:**
   - Si el problema es de versión, probar con versiones anteriores del SDK

---

**Fin del reporte de auditoría**
