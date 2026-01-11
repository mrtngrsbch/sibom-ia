# Estrategia para Queries Comparativas - Enfoque Correcto

## 🎯 Problema Real

**Query:** "cual municipio publico mas decretos en el año 2025?"

**Lo que pasó:**
- ✅ Detectó que es comparativa
- ✅ Usó LLM (no bypass)
- ❌ Envió 1,249 decretos COMPLETOS al LLM
- ❌ System prompt de 303,822 caracteres
- ❌ 149,003 tokens consumidos ($0.45)

## ❌ Enfoque Incorrecto (lo que intenté)

Hardcodear patrones regex para detectar queries comparativas:
```typescript
/cu[aá]l.*(municipio|partido).*(m[aá]s|menos)/i
```

**Problemas:**
1. Usuario puede preguntar de mil formas diferentes
2. Imposible cubrir todos los casos
3. Código frágil y difícil de mantener
4. No escala

## ✅ Enfoque Correcto

### Principio: **Dejar que el LLM entienda la intención**

El LLM es BUENO entendiendo intenciones. NO necesitamos hardcodear patrones.

### Estrategia en 3 pasos:

#### 1. Detectar si menciona "municipio/partido" en contexto comparativo

```typescript
// Simple: ¿Menciona municipio/partido?
const mentionsMunicipality = /municipio|partido/i.test(query);

// Si menciona, NO aplicar filtro de municipio
// Dejar que el LLM decida qué hacer
```

#### 2. Enviar SOLO metadata agregada por municipio

En vez de enviar 1,249 decretos completos:

```typescript
// Agrupar por municipio
const byMunicipality = {
  "Carlos Tejedor": { decretos: 1249, ordenanzas: 45, ... },
  "Merlo": { decretos: 234, ordenanzas: 67, ... },
  "La Plata": { decretos: 456, ordenanzas: 89, ... }
};

// Enviar solo esta tabla al LLM (< 1,000 tokens)
```

#### 3. LLM analiza y responde

El LLM recibe:
- Query del usuario
- Tabla agregada por municipio
- Instrucción: "Analiza y responde la pregunta del usuario"

El LLM decide:
- Si es comparativa → compara municipios
- Si es listado → lista normativas
- Si es búsqueda específica → busca en un municipio

## 📊 Implementación

### Paso 1: Modificar `retrieveContext()` para queries con "municipio/partido"

```typescript
// En route.ts
const mentionsMunicipality = /municipio|partido/i.test(query);

if (mentionsMunicipality) {
  // NO aplicar filtro de municipio
  searchOptions.municipality = undefined;
  
  // Recuperar metadata agregada
  const aggregated = await getAggregatedStats({
    type: enhancedFilters.type,
    dateFrom: enhancedFilters.dateFrom,
    dateTo: enhancedFilters.dateTo
  });
  
  // Enviar solo tabla agregada al LLM
  context = formatAggregatedTable(aggregated);
}
```

### Paso 2: Crear función `getAggregatedStats()`

```typescript
// En retriever.ts
export async function getAggregatedStats(filters: {
  type?: string;
  dateFrom?: string;
  dateTo?: string;
}): Promise<Record<string, MunicipalityStats>> {
  const index = await loadIndex();
  
  // Filtrar por tipo y fecha
  let filtered = index;
  if (filters.type) {
    filtered = filtered.filter(doc => doc.type === filters.type);
  }
  if (filters.dateFrom && filters.dateTo) {
    filtered = filtered.filter(doc => {
      const docDate = parseDate(doc.date);
      return docDate >= filters.dateFrom && docDate <= filters.dateTo;
    });
  }
  
  // Agrupar por municipio
  const byMunicipality: Record<string, MunicipalityStats> = {};
  for (const doc of filtered) {
    if (!byMunicipality[doc.municipality]) {
      byMunicipality[doc.municipality] = {
        total: 0,
        byType: {}
      };
    }
    byMunicipality[doc.municipality].total++;
    byMunicipality[doc.municipality].byType[doc.type] = 
      (byMunicipality[doc.municipality].byType[doc.type] || 0) + 1;
  }
  
  return byMunicipality;
}
```

### Paso 3: Formatear tabla para el LLM

```typescript
function formatAggregatedTable(stats: Record<string, MunicipalityStats>): string {
  let table = "# Estadísticas por Municipio\n\n";
  table += "| Municipio | Total | Decretos | Ordenanzas | Resoluciones |\n";
  table += "|-----------|-------|----------|------------|-------------|\n";
  
  for (const [municipality, data] of Object.entries(stats)) {
    table += `| ${municipality} | ${data.total} | ${data.byType.decreto || 0} | ${data.byType.ordenanza || 0} | ${data.byType.resolucion || 0} |\n`;
  }
  
  return table;
}
```

## 📈 Resultado Esperado

### Antes (Incorrecto)
```
Query: "cual municipio publico mas decretos en el año 2025?"
    ↓
Envía 1,249 decretos completos al LLM
    ↓
System prompt: 303,822 caracteres
Tokens: 149,003 ($0.45)
    ↓
Respuesta: "Carlos Tejedor publicó 1,249 decretos..."
```

### Después (Correcto)
```
Query: "cual municipio publico mas decretos en el año 2025?"
    ↓
Detecta: menciona "municipio"
    ↓
Agrupa por municipio:
  Carlos Tejedor: 1,249 decretos
  Merlo: 234 decretos
  La Plata: 456 decretos
    ↓
Envía tabla agregada al LLM
    ↓
System prompt: ~2,000 caracteres
Tokens: ~1,500 ($0.0045)
    ↓
Respuesta: "Carlos Tejedor publicó 1,249 decretos en 2025, siendo el municipio con más decretos ese año."
```

## 🎯 Beneficios

1. **99% reducción de tokens** (149,003 → 1,500)
2. **99% reducción de costos** ($0.45 → $0.0045)
3. **Más rápido** (20s → 2s)
4. **Más flexible** - LLM entiende cualquier forma de preguntar
5. **Más simple** - Sin regex complejos
6. **Más escalable** - Funciona con cualquier query

## 🚀 Próximos Pasos

1. Implementar `getAggregatedStats()`
2. Modificar `route.ts` para detectar "municipio/partido"
3. Formatear tabla agregada
4. Probar con queries variadas
5. Documentar límite de 5,000 tokens máximo

## 📚 Regla de Oro

**NUNCA enviar más de 5,000 tokens al LLM**

Si una query requiere más contexto:
1. Agregar datos
2. Resumir contenido
3. Paginar resultados
4. Pedir al usuario que refine la búsqueda

---

**Autor:** Feedback del usuario (correcto)
**Fecha:** 2026-01-10
