# Task Prompts

Prompts de tareas específicas con **inputs, outputs y pasos** detallados.

---

## indexing

**Tarea:** Indexar documento JSON a Qdrant

**Input:**
```json
{
  "id": "carlos-tejedor-2025-001",
  "municipality": "Carlos Tejedor",
  "type": "ordenanza",
  "number": "001/2025",
  "title": "Ordenanza de Tránsito Municipal",
  "content": "ARTÍCULO 1°: Se establece...",
  "date": "2025-01-15",
  "url": "https://sibom.slyt.gba.gob.ar/..."
}
```

**Output esperado:**
- Embedding generado (1536 dimensiones)
- Documento indexado en Qdrant
- Metadata preservada
- Log de éxito/error

**Pasos:**
1. Validar estructura JSON (campos obligatorios)
2. Generar embedding del contenido usando OpenRouter
3. Preparar payload para Qdrant con metadata
4. Indexar con retry logic (3 intentos)
5. Verificar indexación exitosa
6. Loggear resultado

**Validaciones:**
- `id` no debe estar vacío
- `content` debe tener al menos 50 caracteres
- `date` debe ser formato ISO (YYYY-MM-DD)
- `type` debe ser uno de: ordenanza, decreto, resolución

---

## scraping

**Tarea:** Scrapear boletines de un municipio

**Input:**
```yaml
municipality: Carlos Tejedor
url: https://sibom.slyt.gba.gob.ar/MunicipioConsulta.aspx?id=123
limit: 10  # Opcional
```

**Output esperado:**
- Lista de boletines extraídos
- Archivos JSON guardados en R2
- Log de scraping
- Reporte CSV con estadísticas

**Pasos:**
1. Hacer request a URL del municipio
2. Parsear HTML con BeautifulSoup
3. Extraer lista de boletines con LLM
4. Para cada boletín:
   a. Extraer metadata (número, fecha, tipo)
   b. Extraer contenido completo
   c. Validar datos
   d. Guardar JSON en R2
5. Generar reporte de scraping
6. Loggear estadísticas

**Validaciones:**
- URL debe ser válida y accesible
- HTML debe contener tabla de boletines
- Cada boletín debe tener número y fecha
- Rate limit respetado (3 req/s)

---

## validation

**Tarea:** Validar integridad de datos JSON

**Input:**
```bash
r2://sibom-cleaned-data/carlos-tejedor/*.json
```

**Output esperado:**
- Reporte de validación (CSV)
- Lista de errores encontrados
- Métricas de calidad de datos
- Sugerencias de corrección

**Pasos:**
1. Leer todos los JSON del bucket
2. Para cada documento:
   a. Validar estructura con Pydantic
   b. Verificar campos obligatorios
   c. Detectar duplicados (por ID)
   d. Validar formatos (fechas, URLs)
3. Generar reporte de errores
4. Calcular métricas de calidad
5. Sugerir correcciones

**Validaciones:**
- Estructura JSON válida
- Campos obligatorios presentes
- Tipos de datos correctos
- Sin duplicados
- Fechas en formato ISO
- URLs accesibles

---

## generate-commit

**Tarea:** Generar 3 opciones de mensajes de commit para cambios actuales

**Input:**
```bash
git status --short
git diff --cached  # si hay staged files
git diff          # si hay unstaged changes
git log -5 --format="%h | %s"  # contexto de commits recientes
```

**Output esperado:**
- 3 opciones de mensajes de commit completos (type + scope + subject + body)
- Sugerencia de cuál opción usar según tipo de cambios
- Indicación de si hay que dividir en múltiples commits

**Pasos:**

1. **Leer cambios del git:**
   - Ejecutar `git status --short` para ver archivos modificados
   - Si hay staged files, ejecutar `git diff --cached`
   - Si no, ejecutar `git diff`
   - Parsear output para extraer lista de archivos y cambios

2. **Categorizar cambios:**
   - Group archivos por directorio:
     - `chatbot/` → scope: `chatbot`
     - `python-cli/` → scope: `scraper`
     - `.agents/` → scope: `agents`
     - `*.md`, `README*` → scope: `docs`
     - `.github/`, `.husky/` → scope: `ci`
   - Si hay múltiples módulos → scope: `(ninguno)`

3. **Detectar tipo de cambio:**
   - `feat`: Nueva funcionalidad, nuevas features
   - `fix`: Corrección de bug, error handling
   - `docs`: Cambios en documentación
   - `refactor`: Refactorización sin cambio funcional
   - `test`: Agregar/modificar tests
   - `chore`: Dependencias, configuración

4. **Verificar umbrales:**
   - Contar archivos: >5 → WARNING, >10 → CRITICAL, >20 → EMERGENCY
   - Contar líneas: >300 → WARNING, >1000 → CRITICAL
   - Ver tiempo desde último commit: >4h → WARNING, >8h → CRITICAL
   - Si supera umbrales, recomendar dividir en múltiples commits

5. **Generar 3 opciones:**

   **Opción 1 - General:**
   - Resumen del cambio principal
   - Body con 2-3 items importantes
   - Formato: `type(scope): subject`

   **Opción 2 - Técnica:**
   - Enfoque en detalles técnicos
   - Menciona tecnologías específicas
   - Body con 3-4 items detallados

   **Opción 3 - Alternativa:**
   - Enfoque diferente del mismo cambio
   - Puede ser más general o más específica
   - Body con 2-3 items

6. **Validar mensajes:**
   - Formato: `type(scope): subject`
   - Subject: 50-72 caracteres, minúsculas, sin punto
   - Body: max 72 chars por línea, lista con guiones
   - Type: feat/fix/docs/refactor/test/chore
   - Scope: chatbot/scraper/agents/docs/ci o (ninguno)

7. **Seleccionar mejor opción:**
   - Analizar cuál opción describe mejor el cambio
   - Considerar contexto del proyecto
   - Recomendar la opción más apropiada

**Validaciones:**

✅ **Commit message correcto:**
```
feat(chatbot): add vector search for bulletin queries

- Implement vector search using Qdrant
- Add relevance scoring with threshold 0.75
- Fallback to keyword search if no results
```

❌ **Commit message incorrecto:**
```
Add vector search for bulletin queries
fix error
update files
```

**Tipos de commits:**
- `feat`: Nueva funcionalidad (add, implement, create)
- `fix`: Corrección de bug (fix, handle, resolve)
- `docs`: Documentación (add, update, fix)
- `refactor`: Refactorización (improve, optimize, simplify)
- `test`: Tests (add, fix, update)
- `chore`: Mantenimiento (upgrade, update, add config)

**División de commits:**

Si hay >5 archivos o >300 líneas:
1. Agrupar por módulo:
   - Commit 1: chatbot/src/lib/rag/ (3 archivos)
   - Commit 2: chatbot/src/lib/api/ (2 archivos)
   - Commit 3: chatbot/components/ (2 archivos)

2. Agrupar por funcionalidad:
   - Commit 1: Feature A (archivos relacionados)
   - Commit 2: Feature B (archivos relacionados)

3. Agrupar por tipo:
   - Commit 1: feat (nueva funcionalidad)
   - Commit 2: fix (correcciones)
   - Commit 3: refactor (reorganización)

**Ejemplo completo:**

Input:
```bash
git status --short
M chatbot/src/lib/rag/retriever.ts
M chatbot/src/lib/rag/vector_search.ts
M chatbot/src/lib/rag/types.ts
M chatbot/src/lib/api/chat.ts
M chatbot/src/lib/api/query.ts
```

Output:
```
⚠️  WARNING: 5 archivos modificados

📋 Opciones de mensajes de commit:

1. feat(chatbot): add vector search for bulletin queries
   - Implement vector search using Qdrant in rag/
   - Add API endpoints in api/
   - Add relevance scoring with threshold 0.75

2. feat(rag): add vector search with relevance scoring
   - Implement Qdrant client in rag/
   - Add embedding generation
   - Implement similarity search with threshold 0.75

3. feat(api): add chatbot API for bulletin queries
   - Implement /api/query endpoint
   - Add /api/validate endpoint
   - Integrate with vector search

Recomendación: Opción 2 (más específica al módulo RAG)
```

---

## Template para Nuevas Tareas

```markdown
## nombre-tarea

**Tarea:** [Descripción breve]

**Input:**
```
[Formato de entrada]
```

**Output esperado:**
- [Output 1]
- [Output 2]
- [Output 3]

**Pasos:**
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

**Validaciones:**
- [Validación 1]
- [Validación 2]
- [Validación 3]
```
