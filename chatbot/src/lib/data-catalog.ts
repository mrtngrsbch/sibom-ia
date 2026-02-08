/**
 * data-catalog.ts
 *
 * Data catalog that describes available data sources and their schemas.
 * This catalog is injected into the LLM system prompt so it knows:
 * - What SQL tables/columns exist
 * - What structured data is available in JSON files
 * - When to use SQL vs content search
 *
 * @version 1.0.0
 * @created 2026-01-10
 * @author Kiro AI (MIT Engineering Standards)
 */

// ============================================================================
// SQL DATABASE SCHEMA
// ============================================================================

export const SQL_SCHEMA = {
  tables: {
    normativas: {
      description: 'Tabla principal con todas las normativas municipales indexadas',
      columns: {
        id: { type: 'TEXT', description: 'ID único de la normativa' },
        municipality: { type: 'TEXT', description: 'Nombre del municipio' },
        type: { type: 'TEXT', description: 'Tipo: decreto, ordenanza, resolucion, disposicion, convenio, licitacion' },
        number: { type: 'TEXT', description: 'Número de la normativa' },
        year: { type: 'INTEGER', description: 'Año de publicación' },
        date: { type: 'TEXT', description: 'Fecha en formato DD/MM/YYYY' },
        title: { type: 'TEXT', description: 'Título de la normativa (truncado a 100 chars)' },
        source_bulletin: { type: 'TEXT', description: 'Nombre del archivo JSON del boletín' },
        url: { type: 'TEXT', description: 'URL del boletín en SIBOM' },
      },
      indexes: ['municipality', 'type', 'year'],
      rowCount: '~216,000 normativas',
    },
  },
  capabilities: [
    'Contar normativas por municipio, tipo, año',
    'Comparar municipios (cuál tiene más/menos normativas)',
    'Estadísticas agregadas (totales, promedios, máximos, mínimos)',
    'Filtrado por múltiples criterios (municipio + tipo + año)',
    'Ranking de municipios por cantidad de normativas',
  ],
  limitations: [
    'NO contiene el contenido completo de las normativas (solo metadatos)',
    'NO puede buscar por palabras clave en el contenido (usar RAG para eso)',
    'NO tiene información sobre el contenido específico de cada normativa',
  ],
} as const;

// ============================================================================
// JSON STRUCTURED DATA SCHEMA
// ============================================================================

export const JSON_SCHEMA = {
  bulletins: {
    description: 'Archivos JSON con boletines municipales completos',
    location: 'python-cli/data/indexes/boletines_index.json',
    structure: {
      fullText: { type: 'string', description: 'Texto completo del boletín' },
      tables: {
        type: 'array',
        description: 'Tablas estructuradas extraídas del boletín',
        schema: {
          title: { type: 'string', description: 'Título de la tabla' },
          headers: { type: 'string[]', description: 'Encabezados de columnas' },
          rows: { type: 'string[][]', description: 'Filas de datos' },
          metadata: {
            type: 'object',
            description: 'Metadatos de la tabla',
            fields: {
              source: 'Fuente de la tabla',
              page: 'Número de página',
              confidence: 'Nivel de confianza de la extracción',
            },
          },
        },
      },
      metadata: {
        type: 'object',
        description: 'Metadatos del boletín',
        fields: {
          municipality: 'Municipio',
          bulletinNumber: 'Número de boletín',
          date: 'Fecha de publicación',
          documentTypes: 'Tipos de documentos incluidos',
        },
      },
    },
  },
  capabilities: [
    'Datos tabulares (sueldos, presupuestos, tasas, etc.)',
    'Contenido completo de normativas',
    'Búsqueda semántica por palabras clave',
    'Extracción de información específica del contenido',
  ],
  limitations: [
    'Requiere carga de archivos completos (más lento)',
    'No optimizado para agregaciones numéricas (usar SQL)',
    'No optimizado para comparaciones entre municipios (usar SQL)',
  ],
} as const;

// ============================================================================
// DECISION TREE FOR LLM
// ============================================================================

export const DECISION_TREE = {
  useSQLWhen: [
    'El usuario pregunta "cuántos" o "cuántas" (conteo)',
    'El usuario compara municipios ("cuál tiene más/menos")',
    'El usuario pide estadísticas agregadas (total, promedio, máximo, mínimo)',
    'El usuario pide un ranking o listado ordenado por cantidad',
    'La pregunta es sobre METADATOS (municipio, tipo, año, número)',
  ],
  useRAGWhen: [
    'El usuario pregunta sobre el CONTENIDO de una normativa ("qué dice", "establece", "dispone")',
    'El usuario busca por TEMA o CONCEPTO ("sueldos", "tránsito", "salud")',
    'El usuario necesita el TEXTO COMPLETO de una normativa',
    'El usuario busca información específica dentro del contenido',
    'El usuario pregunta sobre datos tabulares (tablas de sueldos, presupuestos)',
  ],
  examples: {
    sql: [
      '"¿Cuántos decretos tiene Carlos Tejedor en 2025?" → SQL (conteo)',
      '"¿Qué municipio tiene más ordenanzas?" → SQL (comparación)',
      '"Lista todos los decretos de Merlo" → SQL (listado por metadatos)',
      '"¿Cuántas normativas hay en total?" → SQL (agregación)',
    ],
    rag: [
      '"¿Qué dice la ordenanza 2947 sobre tránsito?" → RAG (contenido)',
      '"Sueldos de Carlos Tejedor 2025" → RAG (búsqueda por tema)',
      '"Ordenanzas sobre habilitación comercial" → RAG (búsqueda semántica)',
      '"Mostrar tabla de sueldos del decreto 123" → RAG (datos tabulares)',
    ],
  },
} as const;

// ============================================================================
// CATALOG GENERATION FOR LLM PROMPT
// ============================================================================

/**
 * Generates a human-readable catalog description for the LLM system prompt
 */
export function generateDataCatalog(): string {
  return `
## 📊 CATÁLOGO DE DATOS DISPONIBLES

### 1. BASE DE DATOS SQL (Metadatos)

**Tabla: normativas**
- **Descripción:** ${SQL_SCHEMA.tables.normativas.description}
- **Registros:** ${SQL_SCHEMA.tables.normativas.rowCount}
- **Columnas:**
${Object.entries(SQL_SCHEMA.tables.normativas.columns)
  .map(([name, info]) => `  - \`${name}\` (${info.type}): ${info.description}`)
  .join('\n')}

**Capacidades SQL:**
${SQL_SCHEMA.capabilities.map(c => `- ${c}`).join('\n')}

**Limitaciones SQL:**
${SQL_SCHEMA.limitations.map(l => `- ${l}`).join('\n')}

### 2. ARCHIVOS JSON (Contenido Completo)

**Estructura de Boletines:**
- **fullText:** Texto completo del boletín (búsqueda semántica)
- **tables:** Tablas estructuradas (sueldos, presupuestos, tasas)
- **metadata:** Información del boletín (municipio, fecha, tipos de documentos)

**Capacidades RAG/JSON:**
${JSON_SCHEMA.capabilities.map(c => `- ${c}`).join('\n')}

**Limitaciones RAG/JSON:**
${JSON_SCHEMA.limitations.map(l => `- ${l}`).join('\n')}

### 3. ÁRBOL DE DECISIÓN - ¿CUÁNDO USAR QUÉ?

**Usar SQL cuando:**
${DECISION_TREE.useSQLWhen.map(w => `- ${w}`).join('\n')}

**Usar RAG/JSON cuando:**
${DECISION_TREE.useRAGWhen.map(w => `- ${w}`).join('\n')}

**Ejemplos de Clasificación:**

SQL (Metadatos/Agregaciones):
${DECISION_TREE.examples.sql.map(e => `  ${e}`).join('\n')}

RAG (Contenido/Búsqueda Semántica):
${DECISION_TREE.examples.rag.map(e => `  ${e}`).join('\n')}

---

**REGLA CRÍTICA:** Si la pregunta es sobre CONTENIDO o TEMAS (sueldos, tránsito, salud), SIEMPRE usar RAG.
Si la pregunta es sobre CONTEO o COMPARACIÓN de metadatos, SIEMPRE usar SQL.
`.trim();
}

/**
 * Generates a concise catalog for FAQ responses
 */
export function generateConciseCatalog(): string {
  return `
**Datos Disponibles:**
- ${SQL_SCHEMA.tables.normativas.rowCount} en base de datos SQL
- Contenido completo en archivos JSON
- Tablas estructuradas (sueldos, presupuestos, tasas)

**Capacidades:**
- Búsqueda por contenido (temas, palabras clave)
- Estadísticas y comparaciones entre municipios
- Datos tabulares y numéricos
`.trim();
}
