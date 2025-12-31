# SIBOM Scraper - Python CLI

Herramienta de línea de comandos para extraer boletines oficiales de SIBOM usando IA (OpenRouter + Gemini 3 Flash Preview).

## 🚀 Instalación

### 1. Crear entorno virtual

```bash
cd python-cli
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar API key

Copia el archivo `.env.example` a `.env`:

```bash
cp .env.example .env
```

Edita `.env` y agrega tu API key de OpenRouter:

```
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aqui
```

Obtén tu API key en: [https://openrouter.ai/keys](https://openrouter.ai/keys)

## 📖 Uso

### Activar entorno virtual (SIEMPRE PRIMERO)

```bash
cd python-cli
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### Comandos rápidos

**Procesar un boletín específico:**
```bash
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556
```

**Procesar desde listado de ciudad (con paginación automática):**
```bash
python3 sibom_scraper.py --limit 5  # Primeros 5 boletines (de todas las páginas)
```

**Procesar TODAS las páginas automáticamente:**
```bash
python3 sibom_scraper.py --skip-existing  # Detecta y procesa todas las páginas (ej: 14 páginas = ~105 boletines)
```

**Procesar UNA página específica:**
```bash
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22?page=6 --limit 5
```

**Con procesamiento paralelo:**
```bash
python3 sibom_scraper.py --limit 10 --parallel 3
```

**Modo automático masivo (todas las páginas, sin preguntas):**
```bash
python3 sibom_scraper.py --skip-existing --parallel 3  # Procesa ~105 boletines en 4-6 minutos
```

**Con modelo gratuito:**
```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free
```

### Ver ayuda completa

```bash
python3 sibom_scraper.py --help
```

## 🎮 Menú Interactivo

Cuando un boletín ya existe, el scraper muestra un menú interactivo:

```
⚠ El archivo Carlos_Tejedor_105.json ya existe

¿Qué deseas hacer con el boletín 105º?
  1. Saltar y continuar con el siguiente
  2. Sobreescribir este boletín
  3. Cancelar todo el proceso

Elige una opción (1-3) [1]:
```

**Navegación:**
- **Números 1-3**: Seleccionar opción
- **Enter**: Confirmar (default: opción 1)
- **Ctrl+C**: Cancelar proceso

**Opciones:**
1. **Saltar y continuar** (defecto): Mantiene el archivo y procesa el siguiente boletín
2. **Sobreescribir**: Re-procesa este boletín
3. **Cancelar**: Termina el programa

Para evitar el menú interactivo, usa `--skip-existing`.

## 📊 Opciones disponibles

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--url` | URL de la página de listado O de un boletín individual. **NUEVO:** Soporta URLs con `?page=N` para procesar una página específica | `https://sibom.slyt.gba.gob.ar/cities/22` (Carlos Tejedor) |
| `--limit` | Número máximo de boletines a procesar (global, de todas las páginas) | `None` (todos) |
| `--parallel` | Número de boletines a procesar en paralelo | `1` |
| `--output` | Archivo de salida JSON (resumen consolidado) | `sibom_results.json` |
| `--model` | Modelo LLM de OpenRouter a usar | `z-ai/glm-4.5-air:free` (GRATIS) |
| `--api-key` | OpenRouter API key (si no usas `.env`) | `None` |
| `--skip-existing` | Saltar automáticamente boletines ya procesados | `False` (pregunta) |

## 🤖 Modelos LLM Disponibles

El scraper soporta diferentes modelos LLM con distintos costos y calidades. Ver [MODELOS.md](MODELOS.md) para guía completa.

### Comparación rápida

| Modelo | Costo | Calidad | Comando |
|--------|-------|---------|---------|
| `z-ai/glm-4.5-air:free` | **GRATIS** | Buena | (default) |
| `google/gemini-2.5-flash-lite` | Muy bajo | Muy buena | `--model google/gemini-2.5-flash-lite` |
| `google/gemini-3-flash-preview` | Bajo | Excelente | `--model google/gemini-3-flash-preview` |
| `x-ai/grok-4.1-fast` | Alto | Premium | `--model x-ai/grok-4.1-fast` |

### Ejemplos

```bash
# Modelo gratuito (ideal para pruebas)
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free

# Modelo económico (75% más barato, buena calidad)
python3 sibom_scraper.py --limit 100 \
  --model google/gemini-2.5-flash-lite \
  --skip-existing

# Comparar modelos automáticamente
./comparar_modelos.sh https://sibom.slyt.gba.gob.ar/bulletins/13556
```

**Documentación completa:** Ver [MODELOS.md](MODELOS.md) para análisis detallado de costos, calidad y estrategias de optimización.

## 📝 Ejemplos

### Ejemplo 1: Procesar un boletín específico

```bash
python sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556
```

Esto procesará SOLO el boletín 98º (ID 13556).

### Ejemplo 2: Procesar 5 boletines desde el listado (con paginación automática) 🆕

```bash
python sibom_scraper.py --limit 5
```

**NUEVO:** El scraper detecta automáticamente todas las páginas (ej: 14 páginas), obtiene todos los boletines (~105 total) y luego aplica el límite de 5.

### Ejemplo 3: Procesar TODAS las páginas automáticamente 🆕

```bash
python sibom_scraper.py --skip-existing
```

**NUEVO:** Procesa automáticamente las 14 páginas de Carlos Tejedor (~105 boletines) sin intervención manual.

**Salida:**
```
🔄 Modo: Detección automática de paginación
✓ Detectadas 14 páginas totales
  Página 1/14: 8 boletines
📄 Página 2/14...
  Página 2/14: 8 boletines (total acumulado: 16)
...
✓ Total: 105 boletines de 14 páginas
```

### Ejemplo 4: Procesar UNA página específica 🆕

```bash
python sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22?page=6 --limit 5
```

**NUEVO:** Al incluir `?page=6`, procesa SOLO esa página (no itera por otras).

### Ejemplo 5: Procesamiento rápido con paralelismo

```bash
python sibom_scraper.py --limit 10 --parallel 3
```

### Ejemplo 6: Otra ciudad con salida personalizada

```bash
python sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/cities/15 \
  --limit 5 \
  --output otra_ciudad.json
```

### Ejemplo 7: Modo automático masivo (todas las páginas)

Útil para scraping masivo automatizado:

```bash
python sibom_scraper.py --skip-existing --parallel 3
```

**NUEVO:** Esto:
- Detecta automáticamente todas las páginas (14 páginas)
- Procesa ~105 boletines totales
- Salta automáticamente los ya procesados (sin preguntar)
- Usa 3 hilos paralelos para mayor velocidad
- **Tiempo estimado:** 4-6 minutos (vs. 10-15 minutos sin paralelismo)

## 🔄 Paginación Automática 🆕

El scraper ahora detecta y procesa automáticamente todas las páginas de un municipio sin intervención manual.

### ¿Cómo funciona?

1. **Detección automática**: Analiza el elemento `<ul class="pagination">` usando BeautifulSoup
2. **Extracción del total**: Encuentra el enlace "Última »" y extrae el número de páginas
3. **Iteración automática**: Procesa página por página agregando `?page=N` a la URL
4. **Límite global**: El parámetro `--limit` se aplica sobre TODOS los boletines, no por página

### Modos de operación

**Modo automático** (sin `?page=` en la URL):
```bash
python3 sibom_scraper.py --skip-existing
```
- Detecta 14 páginas → Procesa ~105 boletines
- Costo: **$0** (BeautifulSoup nativo)
- Tiempo: ~2 segundos para obtener listados

**Modo página única** (con `?page=N`):
```bash
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22?page=6
```
- Procesa SOLO página 6
- NO itera por otras páginas

### Ventajas

✅ **Zero intervención manual** - No más copy-paste de URLs
✅ **Costo $0** - Detección con BeautifulSoup, sin llamadas LLM
✅ **Rápido** - 14 páginas en ~2 segundos
✅ **Robusto** - Si falla una página, continúa con las demás
✅ **Compatible** - Funciona con `--limit`, `--skip-existing` y `--parallel`

## 🎯 Ventajas vs versión React

✅ **Más rápido**: Sin proxies CORS, acceso directo
✅ **Paginación automática**: Detecta y procesa todas las páginas sin intervención 🆕
✅ **Procesamiento paralelo**: Múltiples boletines simultáneos
✅ **Menos rate limiting**: Sin restricciones del navegador
✅ **Más confiable**: Sin problemas de CORS
✅ **Mejor UI**: Progreso con Rich library
✅ **Portátil**: Ejecuta en cualquier sistema

## 📂 Formato de salida

El script genera archivos JSON con esta estructura:

### Archivos individuales (carpeta `boletines/`)

Cada boletín se guarda en un archivo separado:
- Ubicación: `boletines/`
- Nomenclatura: `{Ciudad}_{Numero}.json`
- Ejemplos:
  - `boletines/Carlos_Tejedor_105.json`
  - `boletines/Carlos_Tejedor_104.json`

```json
{
  "number": "105º",
  "date": "30/12/2025",
  "description": "105º de Carlos Tejedor",
  "link": "/bulletins/12345",
  "status": "completed",
  "fullText": "[DOC 1]\nORDENANZA N° 123...\n[DOC 2]\nDECRETO N° 456..."
}
```

### Archivo resumen consolidado

Adicionalmente se genera un archivo con todos los boletines (por defecto `sibom_results.json`):

```json
[
  {
    "number": "105º",
    "date": "30/12/2025",
    "description": "105º de Carlos Tejedor",
    "link": "/bulletins/12345",
    "status": "completed",
    "fullText": "..."
  },
  ...
]
```

### Índice markdown (`boletines.md`)

Se genera automáticamente un índice en formato markdown dentro de `boletines/`:

```markdown
# Boletines Procesados

| Number | Date | Description | Link | Status |
|--------|------|-------------|------|--------|
| 105º | 23/12/2025 | 105º de Carlos Tejedor | [https://sibom.slyt.gba.gob.ar/bulletins/14046](https://sibom.slyt.gba.gob.ar/bulletins/14046) | ✅ Completado |
| 104º | 11/12/2025 | 104º de Carlos Tejedor | [https://sibom.slyt.gba.gob.ar/bulletins/14045](https://sibom.slyt.gba.gob.ar/bulletins/14045) | ✅ Completado |
```

**Características:**
- 📋 Tabla con todos los boletines procesados
- 🔗 URLs clickeables a los boletines originales
- ✅ Status visual con emojis:
  - ✅ Completado (procesado en esta ejecución)
  - 🤖 Creado (ya existía, fue saltado)
  - ❌ Error (error real de scraping)
  - ⚠️ Sin contenido (sin enlaces)
- 🔄 Se actualiza automáticamente con cada ejecución
- 📝 Compatible con GitHub, GitLab y editores markdown

## 🔧 Troubleshooting

### Error: No se encontró OPENROUTER_API_KEY

Solución: Verifica que creaste el archivo `.env` y agregaste tu API key.

### Error de conexión

Solución: Verifica tu conexión a internet. El scraper accede directamente a SIBOM sin proxies.

### Procesamiento muy lento

Solución: Usa `--parallel 3` o más (recomendado: 3-5).

## 🛠️ Desarrollo

### Estructura del código

```
sibom_scraper.py
├── SIBOMScraper        # Clase principal
│   ├── parse_listing_page()         # Nivel 1: Listado
│   ├── parse_bulletin_content_links() # Nivel 2: Enlaces
│   ├── parse_final_content()        # Nivel 3: Texto
│   └── scrape()                     # Orquestador
└── main()              # CLI
```

### Rate limiting

El scraper espera 3 segundos entre llamadas LLM (configurable en `self.rate_limit_delay`).

### Modelo LLM

Actualmente usa `z-ai/glm-4.5-air:free` (GRATIS) vía OpenRouter. Puedes cambiar el modelo editando:

```python
self.model = "z-ai/glm-4.5-air:free"  # Modelo GRATIS por defecto
```

Otros modelos disponibles en: [https://openrouter.ai/models](https://openrouter.ai/models)

## 📄 Licencia

Mismo proyecto que la versión React (ver LICENSE en la raíz).
