# Task Prompts
<!-- Creado: 2025-01-16 | Modificado: 2026-02-06 -->

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
2. Generar embedding del contenido con text-embedding-3-small
3. Preparar payload para Qdrant con metadata
4. Indexar con retry logic (3 intentos)
5. Verificar indexación exitosa
6. Loggear resultado

**Validaciones:**
- `id` no vacío
- `content` ≥ 50 caracteres
- `date` formato ISO (YYYY-MM-DD)
- `type` uno de: ordenanza, decreto, resolución

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
- Archivos JSON en R2
- Reporte CSV con estadísticas

**Pasos:**
1. Request a URL del municipio
2. Parsear HTML con BeautifulSoup
3. Extraer boletines con Gemini 3 Flash (temperature=0.1, JSON mode)
4. Por cada boletín: extraer metadata + contenido, validar, guardar en R2
5. Generar reporte de scraping

**Validaciones:**
- URL válida y accesible
- HTML contiene tabla de boletines
- Cada boletín tiene número y fecha
- Rate limit respetado (3 req/s)

---

## generate-commit

**Tarea:** Generar 3 opciones de mensajes de commit

**Input:**
```bash
git status --short
git diff --cached    # staged files
git diff             # unstaged changes
git log -5 --format="%h | %s"
```

**Output esperado:**
- 3 opciones de commit (type + scope + subject + body)
- Sugerencia de cuál usar
- Indicación si dividir en múltiples commits

**Pasos:**
1. Leer cambios del git
2. Categorizar por directorio → scope (chatbot/, python-cli/, .agents/, *.md, .github/)
3. Detectar tipo de cambio (feat/fix/docs/refactor/test/chore)
4. Verificar umbrales (>5 archivos → WARNING, >10 → CRITICAL)
5. Generar 3 opciones: general, técnica, alternativa
6. Validar formato (50-72 chars, minúsculas, sin punto)

**Ejemplo:**

Input: `M chatbot/src/lib/rag/retriever.ts (+45, -12)` + `M chatbot/src/lib/types.ts (+15, -5)`

Output:
```
1. feat(chatbot): improve vector search relevance
   - Adjust similarity threshold
   - Add type narrowing

2. fix(rag): fix vector search type errors
   - Fix TypeScript errors
   - Update interfaces

3. refactor(rag): optimize search matching
   - Simplify similarity calc
   - Improve type safety
```

---

## Template para Nuevas Tareas

```markdown
## nombre-tarea

**Tarea:** [Descripción]

**Input:** [Formato]

**Output esperado:** [Lista]

**Pasos:** [Numerados]

**Validaciones:** [Lista]
```
