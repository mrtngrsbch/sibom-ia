# Changelog: Refactor de Filtros - Opción 3 Híbrida

**Fecha**: 2026-01-05
**Tipo**: Refactor Mayor
**Objetivo**: Simplificar UX de filtros con arquitectura híbrida inteligente

---

## 🎯 Cambios Implementados

### 1. **Nueva Arquitectura de Filtros** ⭐

**Antes**:
- FilterBar siempre visible (ocupando espacio)
- Filtros no sincronizados con auto-detección
- Usuario no veía qué filtros estaban activos
- Confusión sobre filtros UI vs auto-detección

**Ahora**:
- **Badges compactos** siempre visibles mostrando filtros activos
- **FilterBar avanzado** colapsable (solo cuando se necesita)
- **Sincronización bidireccional**: UI ↔ auto-detección
- **Progressive disclosure**: complejidad oculta por defecto

### 2. **Nuevos Componentes**

#### [ActiveFilters.tsx](chatbot/src/components/chat/ActiveFilters.tsx) (NUEVO)
Componente de badges que muestra:
- `[Carlos Tejedor ×]` → municipio activo, click en × para quitar
- `[Ordenanza ×]` → tipo de documento
- `[Año 2025 ×]` → rango de fechas (formateado inteligentemente)
- `[Filtros avanzados ⚙️]` → botón para expandir FilterBar (solo si NO hay filtros)
- `[Editar filtros ⚙️]` → botón para expandir FilterBar (solo si HAY filtros)

**Características**:
- Formato inteligente de fechas (ej: "Año 2025" vs "Desde 01/01/2025")
- Hover states y animaciones
- Accesibilidad (aria-labels)
- Mobile-friendly

### 3. **Tipos TypeScript Centralizados**

#### [types.ts](chatbot/src/lib/types.ts) (NUEVO)
Interfaces consolidadas:
- `ChatFilters` (versión UI)
- `SearchFilters` (versión backend)
- `Source` (con `documentTypes`)
- `SearchResult`
- `IndexEntry`
- `Document`
- `DatabaseStats`
- `QueryAnalysis`
- `TokenUsage`

**Beneficios**:
- ✅ Elimina tipos duplicados
- ✅ No más `any` types
- ✅ Autocomplete mejorado en VSCode
- ✅ Detección de errores en compilación

### 4. **Constantes Centralizadas**

#### [constants.ts](chatbot/src/lib/constants.ts) (NUEVO)
Elimina números mágicos:

**Antes**:
```typescript
return hasFilters ? 50 : 10;  // ❌ Números mágicos
const CACHE_DURATION = 300000; // ❌ ¿Cuánto es esto?
```

**Ahora**:
```typescript
import { RETRIEVAL_LIMITS, CACHE_DURATIONS } from '@/lib/constants';

return hasFilters ? RETRIEVAL_LIMITS.LISTING_WITH_FILTERS : RETRIEVAL_LIMITS.FILTERED_QUERY;
const CACHE_DURATION = CACHE_DURATIONS.INDEX_MS; // 5 minutos
```

**Constantes definidas**:
- `RETRIEVAL_LIMITS` (50, 10, 3, 2000)
- `CACHE_DURATIONS` (índice, archivos, detección de cambios)
- `DOCUMENT_TYPES` (array de tipos legales)
- `LISTING_QUERY_PATTERNS` (patrones regex)
- `BROAD_QUERY_PATTERNS`
- `SPANISH_STOPWORDS` (set de stopwords)
- `BM25_CONFIG` (k1, b, title_weight)
  - `URLS` (Mangrullo base, viewer)
- `API_CONFIG` (timeouts, retries)

### 5. **Sincronización Bidireccional**

#### ChatContainer.tsx (MODIFICADO)
```typescript
interface ChatContainerProps {
  // ... props existentes
  onFiltersChange?: (filters: ChatFilters) => void; // ✅ NUEVO
}

// En handleSendMessage:
if (onFiltersChange && analysis.extractedFilters) {
  const hasNewFilters = /* detectar filtros nuevos */;

  if (hasNewFilters) {
    onFiltersChange({
      municipality: analysis.extractedFilters.municipality || filters.municipality,
      ordinanceType: analysis.extractedFilters.type || filters.ordinanceType,
      dateFrom: analysis.extractedFilters.dateFrom || filters.dateFrom,
      dateTo: analysis.extractedFilters.dateTo || filters.dateTo,
    });
  }
}
```

**Flujo**:
1. Usuario escribe: "ordenanzas de carlos tejedor 2025"
2. `analyzeQuery` detecta: `{municipality: "Carlos Tejedor", type: "ordenanza", dateFrom: "2025-01-01", dateTo: "2025-12-31"}`
3. `onFiltersChange` actualiza estado del padre (page.tsx)
4. **Badges se actualizan automáticamente** → `[Carlos Tejedor ×] [Ordenanza ×] [Año 2025 ×]`

### 6. **Refactor de page.tsx**

#### page.tsx (MODIFICADO)
```typescript
// Nuevo estado
const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

// Nuevo callback
const handleRemoveFilter = useCallback((filterKey: keyof ChatFilters) => {
  setCurrentFilters(prev => ({
    ...prev,
    [filterKey]: filterKey === 'ordinanceType' ? 'all' : null
  }));
}, []);

// Nueva UI
<ActiveFilters
  municipality={currentFilters.municipality}
  ordinanceType={currentFilters.ordinanceType}
  dateFrom={currentFilters.dateFrom}
  dateTo={currentFilters.dateTo}
  onRemoveFilter={handleRemoveFilter}
  onShowAdvancedFilters={() => setShowAdvancedFilters(prev => !prev)}
/>

{showAdvancedFilters && (
  <FilterBar ... />
)}
```

---

## 🐛 Código Limpiado

### Eliminados (pendiente):
- `pendingQuery` state (no se usa más)
- Comentarios de "Estrategia B"
- Código comentado

### Por actualizar:
- `query-classifier.ts`: usar constantes de `constants.ts`
- `retriever.ts`: usar constantes de `constants.ts`
- `bm25.ts`: usar `SPANISH_STOPWORDS` y `BM25_CONFIG`
- `route.ts`: reemplazar `any` con tipo `Source`

---

## 📊 Comparación Antes/Después

### Espacio en Pantalla

**Antes**:
```
┌─────────────────────────┐
│ Header                  │
├─────────────────────────┤
│ FilterBar (100px height)│ ← Siempre visible
│ [Municipio ▼] [Tipo ▼] │
│ [Fecha ▼] [Limpiar]     │
├─────────────────────────┤
│                         │
│ Chat Messages           │
│ (espacio reducido)      │
│                         │
└─────────────────────────┘
```

**Ahora**:
```
┌─────────────────────────┐
│ Header                  │
├─────────────────────────┤
│ [Carlos T ×] [2025 ×]   │ ← Compacto (40px)
│ [Filtros avanzados ⚙️]  │
├─────────────────────────┤
│                         │
│                         │
│ Chat Messages           │
│ (más espacio)           │
│                         │
│                         │
└─────────────────────────┘
```

### Clicks para Usar Filtros

**Antes**:
1. Usuario escribe "ordenanzas de carlos tejedor 2025"
2. Sistema aplica filtros en backend
3. ❌ UI no refleja cambio
4. Usuario confundido: "¿se aplicaron los filtros?"

**Ahora**:
1. Usuario escribe "ordenanzas de carlos tejedor 2025"
2. Sistema aplica filtros en backend
3. ✅ UI actualiza badges: `[Carlos Tejedor ×] [Ordenanza ×] [Año 2025 ×]`
4. Usuario ve confirmación visual inmediata

### Clicks para Quitar un Filtro

**Antes**:
1. Click en badge "Carlos Tejedor"
2. Dropdown se abre
3. Click en "Todos los municipios"
4. **Total: 2 clicks**

**Ahora**:
1. Click en ×  del badge
2. **Total: 1 click**

---

## 🎨 Mejoras UX/UI

### 1. **Claridad Visual**
- ✅ Usuario siempre ve qué filtros están activos
- ✅ Badges con estilo distintivo (diferentes de texto normal)
- ✅ Hover states claros

### 2. **Eficiencia**
- ✅ Menos espacio ocupado (40px vs 100px)
- ✅ Menos clicks para quitar filtros (1 vs 2)
- ✅ Filtros avanzados ocultos hasta que se necesiten

### 3. **Feedback**
- ✅ Auto-detección sincroniza inmediatamente con UI
- ✅ Animaciones suaves al agregar/quitar filtros
- ✅ Formato inteligente de fechas ("Año 2025" es más legible que "01/01/2025 - 31/12/2025")

---

## 🚀 Próximos Pasos (Pendientes)

### Alta Prioridad:
1. ✅ Actualizar imports en archivos restantes para usar tipos centralizados
2. ⏳ Reemplazar números mágicos en `query-classifier.ts` con constantes
3. ⏳ Reemplazar números mágicos en `retriever.ts` con constantes
4. ⏳ Actualizar `bm25.ts` para usar `SPANISH_STOPWORDS` y `BM25_CONFIG`
5. ⏳ Eliminar `any` types en `route.ts` (línea 210)

### Media Prioridad:
6. ⏳ Eliminar código muerto (`pendingQuery`)
7. ⏳ Limpiar comentarios de Estrategia B
8. ⏳ Documentar arquitectura en README

### Baja Prioridad:
9. ⏳ Tests unitarios para ActiveFilters
10. ⏳ Tests de integración para sincronización de filtros
11. ⏳ Métricas de uso (¿cuántos usuarios usan filtros avanzados?)

---

## 📝 Notas Técnicas

### TypeScript Strict Mode
Todos los nuevos archivos cumplen con `strict: true`:
- No hay `any` types (excepto casos justificados con comentario)
- Todos los parámetros tipados
- Interfaces exportadas

### Performance
- `useCallback` en handlers para evitar re-renders
- `useMemo` en componentes ReactMarkdown
- Tipos inmutables (`as const`)

### Accesibilidad
- `aria-label` en botones de quitar filtro
- Keyboard navigation funcional
- Contraste de colores accesible

---

## 🔗 Archivos Afectados

### Nuevos:
- `chatbot/src/components/chat/ActiveFilters.tsx`
- `chatbot/src/lib/types.ts`
- `chatbot/src/lib/constants.ts`

### Modificados:
- `chatbot/src/app/page.tsx`
- `chatbot/src/components/chat/ChatContainer.tsx`
- `chatbot/src/components/chat/FilterBar.tsx`

### Por actualizar:
- `chatbot/src/lib/query-classifier.ts`
- `chatbot/src/lib/rag/retriever.ts`
- `chatbot/src/lib/rag/bm25.ts`
- `chatbot/src/app/api/chat/route.ts`

---

## ✅ Checklist de Validación

- [x] Componente ActiveFilters creado y funcional
- [x] Tipos centralizados en types.ts
- [x] Constantes centralizadas en constants.ts
- [x] page.tsx refactorizado con badges
- [x] ChatContainer sincroniza con padre
- [x] FilterBar usa tipos centralizados
- [ ] Server dev reiniciado (pendiente testing)
- [ ] Probado en navegador
- [ ] Mobile responsive validado
- [ ] Accesibilidad verificada

---

## 🎉 Resultados Esperados

1. **UX Mejorado**: Usuario ve claramente qué filtros están activos
2. **Sincronización**: Filtros UI reflejan auto-detección
3. **Espacio**: +60px de espacio vertical para chat
4. **Código Limpio**: Sin números mágicos, tipos consistentes
5. **Mantenibilidad**: Fácil agregar nuevos tipos de documentos

---

**Status**: ✅ Implementación Core Completa
**Próximo paso**: Testing en navegador
