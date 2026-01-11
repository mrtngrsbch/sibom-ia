# Resumen: Catálogo de Datos para el LLM

## 🎯 Tu Pregunta

> "¿Cómo sabe el LLM lo que guardamos en el SQL para ser usado? ¿Cómo sabe el LLM todo lo que tenemos en los JSON?"

## 💡 Respuesta Corta

**Antes:** NO LO SABÍA. El LLM solo veía los documentos que BM25 le pasaba.

**Ahora:** SÍ LO SABE. Le damos un "catálogo de datos" completo en el system prompt que describe:
- Qué tablas/columnas hay en SQL
- Qué datos estructurados hay en JSON
- Cuándo usar SQL vs RAG
- Ejemplos concretos

## 🔧 Qué Hice

### 1. Creé `data-catalog.ts`

Un archivo que describe TODO lo que tenemos:

```typescript
// Schema de SQL
SQL_SCHEMA = {
  tables: {
    normativas: {
      columns: { municipality, type, number, year, date, title... },
      rowCount: '~216,000 normativas',
      capabilities: ['Contar', 'Comparar', 'Agregar'],
      limitations: ['NO tiene contenido completo']
    }
  }
}

// Schema de JSON
JSON_SCHEMA = {
  bulletins: {
    structure: { fullText, tables, metadata },
    capabilities: ['Búsqueda semántica', 'Datos tabulares'],
    limitations: ['Más lento', 'No optimizado para agregaciones']
  }
}

// Árbol de decisión
DECISION_TREE = {
  useSQLWhen: ['conteo', 'comparación', 'estadísticas'],
  useRAGWhen: ['contenido', 'temas', 'búsqueda semántica'],
  examples: {
    sql: ['"¿Cuántos decretos?" → SQL'],
    rag: ['"Sueldos de Carlos Tejedor" → RAG']
  }
}
```

### 2. Lo Inyecté en el System Prompt

Ahora el LLM recibe esto ANTES de cada respuesta:

```
## 📊 CATÁLOGO DE DATOS DISPONIBLES

### 1. BASE DE DATOS SQL (Metadatos)
- Tabla: normativas (~216,000 registros)
- Columnas: id, municipality, type, number, year, date, title...
- Capacidades: Contar, comparar, agregar, rankear
- Limitaciones: NO tiene contenido completo

### 2. ARCHIVOS JSON (Contenido Completo)
- fullText: Texto completo del boletín
- tables: Tablas estructuradas (sueldos, presupuestos)
- Capacidades: Búsqueda semántica, datos tabulares
- Limitaciones: Más lento, no optimizado para agregaciones

### 3. ÁRBOL DE DECISIÓN
Usar SQL cuando: conteo, comparación, estadísticas
Usar RAG cuando: contenido, temas, búsqueda semántica

Ejemplos:
- "¿Cuántos decretos?" → SQL
- "Sueldos de Carlos Tejedor" → RAG
```

## 🎯 Impacto en "Sueldos de Carlos Tejedor 2025"

### Antes
```
Usuario: "sueldos de carlos tejedor 2025"
LLM: [No sabe qué hacer, responde genérico]
     "Se encontraron 10 decretos..."
```

### Ahora
```
Usuario: "sueldos de carlos tejedor 2025"
LLM: [Ve en el catálogo: "búsqueda por TEMA → usar RAG"]
     [Analiza el CONTENIDO de los documentos]
     "Encontré información sobre remuneraciones en el Decreto X..."
```

## ✅ Qué Logra Esto

1. **El LLM sabe qué datos existen**
   - "Tengo 216,000 normativas en SQL"
   - "Tengo contenido completo en JSON"
   - "Tengo tablas estructuradas con sueldos"

2. **El LLM sabe qué puede hacer**
   - "Puedo contar con SQL"
   - "Puedo buscar contenido con RAG"
   - "Puedo extraer datos tabulares"

3. **El LLM sabe cuándo usar cada herramienta**
   - "¿Cuántos?" → SQL
   - "¿Qué dice sobre X?" → RAG
   - "Sueldos de..." → RAG (búsqueda por tema)

4. **El LLM puede explicar su razonamiento**
   - "Para contar normativas, consulté la base de datos SQL..."
   - "Para buscar información sobre sueldos, analicé el contenido..."

## 🧪 Status

✅ **Implementado**
✅ **Build exitoso** (pnpm run build)
⏳ **Pendiente:** Testear con queries reales

## 📁 Archivos Creados/Modificados

1. **NUEVO:** `chatbot/src/lib/data-catalog.ts` (catálogo completo)
2. **MODIFICADO:** `chatbot/src/app/api/chat/route.ts` (inyección del catálogo)
3. **MODIFICADO:** `chatbot/src/prompts/system.md` (placeholder para catálogo)

## 🎓 Conclusión

**Tu pregunta:** "¿Cómo sabe el LLM lo que tenemos en SQL y JSON?"

**Mi respuesta:** Ahora se lo decimos explícitamente. El LLM recibe un "manual de usuario" completo de todos los datos disponibles antes de responder cada query.

**Resultado:** El LLM pasa de ser un "respondedor ciego" a un "asistente informado" que conoce toda la arquitectura de datos y puede tomar decisiones inteligentes.

---

**¿Quieres que pruebe el sistema con la query "sueldos de carlos tejedor 2025" para ver si ahora funciona mejor?**
