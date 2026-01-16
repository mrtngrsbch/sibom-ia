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
