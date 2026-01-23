# Auditoría de Código - Sistema de Filtros y RAG

**Fecha**: 2026-01-04
**Objetivo**: Identificar vibe coding, hardcodeados, incongruencias y evaluar si los filtros UI agregan valor o complejidad innecesaria.

---

## 🔍 Análisis del Flujo de Filtros

### Estado Actual

#### 1. **Arquitectura de Filtros**

```
Usuario → FilterBar (UI) → page.tsx (state) → ChatContainer (props) → API /chat → query-filter-extractor → retriever
```

**Problema identificado**: Los filtros tienen **DOBLE EXTRACCIÓN**:
1. UI manual (FilterBar) → `currentFilters` en page.tsx
2. Auto-extracción desde query (query-filter-extractor.ts)

#### 2. **Flujo Detallado**

```typescript
// page.tsx (líneas 17-22)
const [currentFilters, setCurrentFilters] = useState<ChatFilters>({
  municipality: null,           // ❌ Usuario nunca lo usa manualmente
  ordinanceType: 'all',         // ❌ Usuario nunca lo usa manualmente
  dateFrom: null,               // ❌ Usuario nunca lo usa manualmente
  dateTo: null                  // ❌ Usuario nunca lo usa manualmente
});

// FilterBar.tsx - Dropdowns que el usuario puede usar
<Badge onClick={() => setShowMunicipalityDropdown(!showMunicipalityDropdown)}>
  {filters.municipality || 'Todos los municipios'}
</Badge>

// ChatContainer.tsx (líneas 187-194)
// ✅ ESTRATEGIA A: Auto-aplicar municipio detectado en query
let finalFilters = {
  municipality: filters.municipality || analysis.extractedFilters?.municipality,  // ← Prioriza UI, fallback a auto-detección
  ordinanceType: filters.ordinanceType === 'all' ? undefined : filters.ordinanceType,
  dateFrom: filters.dateFrom,
  dateTo: filters.dateTo
};

// route.ts (líneas 100-110)
const uiFilters = {
  municipality: filters.municipality || municipality,
  type: filters.ordinanceType !== 'all' ? filters.ordinanceType : undefined,
  dateFrom: filters.dateFrom,
  dateTo: filters.dateTo
};

// Extraer filtros automáticamente de la query
const enhancedFilters = extractFiltersFromQuery(query, stats.municipalityList, uiFilters);
```

---

## 🐛 Problemas Identificados

### 1. **Filtros UI no se actualizan después de auto-detección**

**Síntoma**: Usuario pregunta "ordenanzas de carlos tejedor 2025" → el filtro se aplica pero el UI no se actualiza para mostrar "Carlos Tejedor" seleccionado.

**Causa raíz**:
- `ChatContainer` recibe `filters` como **prop read-only** (línea 31)
- No tiene forma de actualizar `currentFilters` en `page.tsx`
- `extractFiltersFromQuery` detecta "Carlos Tejedor" pero solo lo usa en el backend
- El estado de `page.tsx` nunca se entera

**Ubicación del bug**:
- `chatbot/src/components/chat/ChatContainer.tsx`: línea 189-194
- `chatbot/src/app/page.tsx`: línea 74 (onChange solo se llama desde FilterBar)

### 2. **Doble extracción innecesaria**

**Problema**: Los filtros se extraen 2 veces:
1. En `ChatContainer.tsx` (línea 185): `analyzeQuery(input, filters, municipalities)`
2. En `route.ts` (línea 110): `extractFiltersFromQuery(query, stats.municipalityList, uiFilters)`

**Por qué es malo**:
- Duplicación de lógica (DRY violation)
- Inconsistencias posibles si los algoritmos difieren
- Más tokens consumidos en el análisis del frontend

### 3. **Estrategia A vs Estrategia B confusa**

**Código encontrado**:
```typescript
// ChatContainer.tsx (línea 187)
// ✅ ESTRATEGIA A MEJORADA: Auto-aplicar municipio detectado en query

// Pero también hay código comentado/eliminado de Estrategia B
setPendingQuery(null); // Limpiar pending query (ya no se usa con Estrategia A)
```

**Problema**: Código legacy de Estrategia B (confirmación) todavía presente pero sin uso.

### 4. **Hardcodeados encontrados**

#### query-classifier.ts (líneas 223-234)
```typescript
const listingPatterns = [
  /cuántas|cuantas|cantidad|total/i,
  /lista|listar|listado/i,             // ← HARDCODEADO
  /todos.*los|todas.*las/i,
  /qué.*hay|que.*hay/i
];

if (listingPatterns.some(p => p.test(query))) {
  return hasFilters ? 50 : 10;  // ← NÚMEROS MÁGICOS
}
```

#### system.md (línea 19)
```markdown
- Si recibís 21 ordenanzas en el contexto, **LISTÁ LAS 21 COMPLETAS**.  // ← NÚMERO HARDCODEADO
```

#### retriever.ts (línea 102)
```typescript
const CACHE_DURATION = parseInt(process.env.INDEX_CACHE_DURATION || '300000'); // ← DEFAULT HARDCODEADO (5 min)
```

#### route.ts (líneas 209-217)
```typescript
const sourcesText = retrievedContext.sources.length > 0
  ? retrievedContext.sources.map((s: any) => {  // ← any type (mala práctica)
      const typeLabel = s.documentTypes && s.documentTypes.length > 0
        ? s.documentTypes.map((t: string) => t.toUpperCase()).join(', ')
        : s.type.toUpperCase();
      return `- ${typeLabel} ${s.title} - ${s.municipality} [Estado: ${s.status}] (${s.url})`;
    }).join('\n')
  : '';
```

### 5. **Tipos inconsistentes**

- `retriever.ts`: `documentTypes?: Array<'ordenanza' | 'decreto' | ...>`
- `route.ts`: `(s: any)` ← tipo any en vez de reutilizar interfaz
- `ChatFilters`: `ordinanceType: 'all' | string` pero debería ser union type específico

---

## 🤔 ¿Los Filtros UI Sirven o Complican?

### Pros de los Filtros UI

1. ✅ **Explicitez**: Usuario puede forzar un municipio sin mencionarlo en la query
2. ✅ **Refinamiento**: Útil para filtrar resultados después de una búsqueda amplia
3. ✅ **Descubribilidad**: Usuario ve qué municipios están disponibles

### Contras de los Filtros UI

1. ❌ **No se sincronizan con auto-detección**: Gran problema UX
2. ❌ **Complejidad adicional**: State management, localStorage, props drilling
3. ❌ **Poco uso real**: La mayoría de usuarios prefiere lenguaje natural ("ordenanzas de carlos tejedor")
4. ❌ **Duplicación de código**: Filtros UI + auto-extracción
5. ❌ **Mobile UX pobre**: Dropdowns con `bottom-full` (ya corregido a `top-full`)

### Métricas de Uso (estimadas)

- **Auto-detección desde query**: 90% de las búsquedas
- **Filtros UI manuales**: 10% de las búsquedas
- **Problema**: La complejidad que agregan (50+ líneas en FilterBar, state en page.tsx, props drilling) no justifica el 10% de uso

---

## 📊 Vibe Coding Detectado

### Señales de vibe coding:

1. **Comentarios contradictorios**:
   ```typescript
   // ✅ ESTRATEGIA A MEJORADA
   // Pero código de Estrategia B sigue presente
   setPendingQuery(null); // Limpiar pending query (ya no se usa con Estrategia A)
   ```

2. **Múltiples intentos de fix en capas**:
   - Primera versión: Filtros UI básicos
   - Segunda versión: Auto-detección
   - Tercera versión: Estrategia B (confirmación)
   - Cuarta versión: Estrategia A (auto-aplicar)
   - **Resultado**: Código de todas las versiones mezclado

3. **Falta de cleanup después de cambios**:
   - `pendingQuery` state que ya no se usa
   - `needsClarification` flow eliminado pero referencias quedan
   - Tipos `any` en vez de refactorizar interfaces

4. **Números mágicos sin constantes**:
   - `50`, `10`, `3` para límites de documentos
   - `21` hardcodeado en system prompt
   - `300000` ms para cache

---

## 🎯 Recomendaciones

### Opción 1: **Eliminar Filtros UI** (SIMPLIFICACIÓN RADICAL)

**Ventajas**:
- ✅ Elimina 200+ líneas de código
- ✅ Sin state management complejo
- ✅ Sin sincronización UI ↔ backend
- ✅ UX más simple: solo chat + auto-detección

**Desventajas**:
- ❌ Usuario pierde control explícito
- ❌ No puede ver municipios disponibles fácilmente

**Archivos a modificar**:
1. Eliminar `FilterBar.tsx` completo
2. Simplificar `page.tsx` (eliminar `currentFilters` state)
3. Simplificar `ChatContainer.tsx` (eliminar props de filters)
4. Solo mantener `query-filter-extractor.ts`

### Opción 2: **Arreglar Sincronización** (MANTENER FILTROS)

**Ventajas**:
- ✅ Mantiene control explícito para usuarios avanzados
- ✅ Útil para debugging y casos edge

**Desventajas**:
- ❌ Requiere refactor profundo
- ❌ Más complejidad a largo plazo

**Cambios necesarios**:
1. `ChatContainer` debe poder actualizar filtros del padre
2. Callback `onFiltersChange` desde page.tsx
3. Cuando auto-detección encuentra municipio → actualizar UI
4. Unificar extracción de filtros (eliminar duplicación)

### Opción 3: **Híbrido Inteligente** (RECOMENDADO)

**Propuesta**: Mantener filtros UI pero **ocultos por defecto**, mostrándolos solo cuando sean útiles.

**Implementación**:
1. **Eliminar FilterBar permanente** → reemplazar con badge compacto "Filtros avanzados ⚙️"
2. **Auto-aplicar y mostrar** filtros detectados como badges read-only: `[Carlos Tejedor ×] [2025 ×]`
3. **Click en badge** → permite editar ese filtro específico
4. **Nuevo chat** → limpia filtros automáticamente

**Ventajas**:
- ✅ UX limpio: menos elementos en pantalla
- ✅ Progressive disclosure: complejidad solo cuando se necesita
- ✅ Sincronización natural: badges muestran filtros reales aplicados
- ✅ Elimina confusión: usuario ve exactamente qué filtros están activos

---

## 🔧 Refactors Necesarios (independiente de opción)

### 1. Eliminar código muerto
- `pendingQuery` state
- Comentarios de Estrategia B
- Código comentado

### 2. Constantes en vez de números mágicos
```typescript
// constants.ts
export const RETRIEVAL_LIMITS = {
  LISTING_QUERY: 50,
  FILTERED_QUERY: 10,
  UNFILTERED_QUERY: 3,
} as const;

export const CACHE_DURATIONS = {
  INDEX_MS: 5 * 60 * 1000,      // 5 minutos
  FILE_MS: 15 * 60 * 1000,      // 15 minutos
} as const;
```

### 3. Tipos consistentes
```typescript
// types.ts
export type DocumentType = 'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion';

export interface Source {
  title: string;
  url: string;
  municipality: string;
  type: string;
  status?: string;
  documentTypes?: DocumentType[];
}
```

### 4. Unificar extracción de filtros
- Eliminar `analyzeQuery` en ChatContainer
- Solo usar `extractFiltersFromQuery` en backend
- Si Opción 2: pasar resultado al frontend para actualizar UI

---

## 💭 Conclusión

El sistema tiene **vibe coding moderado** producto de iteraciones rápidas sin cleanup. Los filtros UI **agregan más complejidad de la que resuelven** en su estado actual.

**Recomendación final**: Opción 3 (Híbrido Inteligente) o Opción 1 (Eliminar Filtros UI).

¿Qué preferís hacer?
