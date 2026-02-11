# Arquitectura del Backend: Python CLI Scraper

## Introducción

El backend del SIBOM Scraper es una herramienta CLI en Python que implementa un sistema de extracción de datos de 3 niveles con procesamiento híbrido. Ubicado en `python-cli/`, representa la parte de "extracción" del ecosistema.

## Arquitectura Principal

### Clase Central: SIBOMScraper

**Ubicación**: `python-cli/sibom_scraper.py:32-848`

```python
class SIBOMScraper:
    def __init__(self, api_key: str, model: str = "z-ai/glm-4.5-air:free"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self.rate_limit_delay = 3  # segundos entre llamadas
        self.last_call_time = 0
```

**Patrón de Diseño**: Facade + Strategy Pattern
- **Facade**: Simplifica la complejidad del scraping en una interfaz única
- **Strategy**: Permite cambiar modelos LLM dinámicamente

### Pipeline de 3 Niveles

#### Nivel 1: Extracción de Listados
**Método**: `parse_listing_page(html: str, url: str) -> List[Dict]`
**Líneas**: `python-cli/sibom_scraper.py:200-250`

```python
def parse_listing_page(self, html: str, url: str) -> List[Dict]:
    """Nivel 1: Extrae listado de boletines usando BeautifulSoup (con fallback a LLM)"""
    try:
        # Intentar con BeautifulSoup primero (95% de casos)
        soup = BeautifulSoup(html, 'lxml')
        bulletin_divs = soup.find_all('div', class_='row bulletin')
        
        for bulletin_div in bulletin_divs:
            title_elem = bulletin_div.find('p', class_='bulletin-title')
            date_elem = bulletin_div.find('p', class_='bulletin-date')
            form_elem = bulletin_div.find('form', class_='button_to')
            # ... extracción de metadatos
            
    except Exception as e:
        # Fallback a LLM si BeautifulSoup falla
        prompt = f"""Analiza este HTML de SIBOM..."""
        response = self._make_llm_call(prompt, use_json_mode=True)
```

**Estrategia Híbrida**:
- **Primario**: BeautifulSoup (rápido, gratis, 95% casos)
- **Fallback**: LLM (robusto, costoso, 5% casos complejos)

#### Nivel 2: Extracción de Enlaces
**Método**: `parse_bulletin_content_links(html: str) -> List[str]`
**Líneas**: `python-cli/sibom_scraper.py:320-380`

```python
def parse_bulletin_content_links(self, html: str) -> List[str]:
    """Nivel 2: Extrae enlaces de contenido específico"""
    try:
        soup = BeautifulSoup(html, 'lxml')
        content_links = soup.find_all('a', class_='content-link')
        links = [link.get('href', '') for link in content_links if link.get('href')]
        
        if links:
            return links
        else:
            raise ValueError("No se encontraron enlaces con BeautifulSoup")
    except Exception as e:
        # Fallback a LLM con manejo robusto de JSON malformado
        response = self._make_llm_call(prompt, use_json_mode=True)
        # ... manejo de errores JSON con extracción manual
```

**Manejo de Errores JSON**: `python-cli/sibom_scraper.py:360-378`
- Intenta parsear JSON normal
- Si falla, extrae manualmente el primer objeto JSON válido
- Logging detallado para debugging

#### Nivel 3: Extracción de Contenido
**Método**: `parse_final_content(html: str) -> str`
**Líneas**: `python-cli/sibom_scraper.py:380-450`

```python
def parse_final_content(self, html: str) -> str:
    """Nivel 3: Extrae texto completo usando BeautifulSoup mejorado (sin LLM)"""
    
    # Estrategia 1: Buscar contenedor principal por ID
    container = soup.find('div', id='frontend-container')
    
    if not container:
        # Estrategia 2: Buscar por clase que contenga 'content'
        container = soup.find('div', class_=lambda x: x and 'content' in str(x).lower())
    
    if not container:
        # Estrategia 3: Elementos semánticos
        container = soup.find('main') or soup.find('article')
    
    if not container:
        # Estrategia 4: Body limpio
        body = soup.find('body')
        for unwanted in body.find_all(['script', 'style', 'nav', 'footer']):
            unwanted.decompose()
        container = body
```

**Optimización**: Solo BeautifulSoup (sin LLM) para reducir costos

## Características Avanzadas

### Detección Automática de Paginación
**Método**: `detect_total_pages(html: str) -> int`
**Líneas**: `python-cli/sibom_scraper.py:252-318`

```python
def detect_total_pages(self, html: str) -> int:
    """Detecta número total de páginas usando BeautifulSoup"""
    soup = BeautifulSoup(html, 'lxml')
    pagination = soup.find('ul', class_='pagination')
    
    # Buscar enlace "Última" que contiene el número total
    last_page_link = pagination.find('a', string=lambda text: text and 'Última' in text)
    
    if last_page_link:
        href = last_page_link.get('href', '')
        match = re.search(r'page=(\d+)', href)
        if match:
            return int(match.group(1))
```

**Ventajas**:
- ✅ **Zero intervención manual**: No más copy-paste de URLs
- ✅ **Costo $0**: Detección con BeautifulSoup, sin LLM
- ✅ **Rápido**: 14 páginas en ~2 segundos

### Procesamiento Paralelo
**Método**: `scrape()` con ThreadPoolExecutor
**Líneas**: `python-cli/sibom_scraper.py:700-730`

```python
if parallel > 1:
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {executor.submit(self.process_bulletin, b, base_url, output_dir, skip_existing): b 
                  for b in bulletins}
        
        with Progress(SpinnerColumn(), TextColumn(), BarColumn()) as progress:
            task = progress.add_task(f"[cyan]Procesando...", total=len(bulletins))
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                progress.update(task, advance=1)
```

**Configuración**:
- **Default**: 1 hilo (secuencial)
- **Recomendado**: 3 hilos (`--parallel 3`)
- **Performance**: 2-3s por boletín vs. 5-7s secuencial

### Rate Limiting Inteligente
**Método**: `_wait_for_rate_limit()`
**Líneas**: `python-cli/sibom_scraper.py:42-48`

```python
def _wait_for_rate_limit(self):
    """Espera según rate limiting"""
    elapsed = time.time() - self.last_call_time
    if elapsed < self.rate_limit_delay:
        time.sleep(self.rate_limit_delay - elapsed)
    self.last_call_time = time.time()
```

**Configuración**: 3 segundos entre llamadas LLM (configurable)

### Gestión de Archivos Existentes
**Método**: `process_bulletin()` con menú interactivo
**Líneas**: `python-cli/sibom_scraper.py:520-580`

```python
if filepath.exists():
    if skip_existing:
        # Modo automático: saltar sin preguntar
        return existing_data
    else:
        # Modo interactivo: menú de opciones
        console.print("¿Qué deseas hacer con el boletín?")
        console.print("  [cyan]1.[/cyan] Saltar y continuar")
        console.print("  [cyan]2.[/cyan] Sobreescribir")
        console.print("  [cyan]3.[/cyan] Cancelar todo")
        
        choice = input("\nElige una opción (1-3) [1]: ").strip() or "1"
```

**Modos**:
- **Interactivo** (default): Pregunta al usuario
- **Automático** (`--skip-existing`): Salta automáticamente

## Sanitización de Nombres de Archivo

**Método**: `_sanitize_filename(description: str, number: str) -> str`
**Líneas**: `python-cli/sibom_scraper.py:60-100`

```python
def _sanitize_filename(self, description: str, number: str = None) -> str:
    """
    Convierte descripción en nombre válido.
    Ejemplo: "105º de Carlos Tejedor" -> "Carlos_Tejedor_105"
    """
    # Extraer número del boletín
    number_match = re.search(r'(\d+)', number or description)
    num = number_match.group(1) if number_match else "0"
    
    # Para descripciones largas, extraer nombre de ciudad
    if len(description) > 50:
        city_match = re.search(r'(?:de\s+)([A-Z][a-zA-Z\s]+)', description)
        if city_match:
            cleaned = city_match.group(1).strip()
            return f"{cleaned}_{num}"
    
    # Limpiar caracteres especiales
    cleaned = re.sub(r'[^\w\s-]', '', description)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    return f"{cleaned}_{num}"
```

**Patrones**:
- Descripciones cortas: `"105º de Carlos Tejedor"` → `"Carlos_Tejedor_105"`
- Descripciones largas: `"Boletín Municipal de Carlos Tejedor..."` → `"Carlos_Tejedor_98"`

## Sistema de Índices

### Índice Markdown Automático
**Método**: `_update_index_md(bulletin: Dict, output_dir: Path, base_url: str)`
**Líneas**: `python-cli/sibom_scraper.py:102-150`

```python
def _update_index_md(self, bulletin: Dict, output_dir: Path, base_url: str):
    """Actualiza boletines.md con información del boletín procesado"""
    index_file = output_dir / "boletines.md"
    
    # Crear archivo si no existe
    if not index_file.exists():
        with index_file.open('w', encoding='utf-8') as f:
            f.write("# Boletines Procesados\n\n")
            f.write("| Number | Date | Description | Link | Status |\n")
            f.write("|--------|------|-------------|------|--------|\n")
    
    # Status con emojis
    status_display = {
        'completed': '✅ Completado',
        'skipped': '🤖 Creado', 
        'error': '❌ Error',
        'no_content': '⚠️ Sin contenido'
    }.get(status, status)
```

**Características**:
- 📋 Tabla markdown con todos los boletines
- 🔗 URLs clickeables a SIBOM
- ✅ Status visual con emojis
- 🔄 Actualización automática
- 📝 Compatible con GitHub/GitLab

### Utilidades de Indexación

#### `indexar_boletines.py`
**Función**: Genera índice JSON estructurado
```python
def indexar():
    boletines_path = Path('boletines')
    index = []
    
    for file_path in boletines_path.glob('*.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entry = {
            'id': file_path.name.replace('.json', ''),
            'municipality': extract_municipality(file_path.name),
            'type': detect_type(full_text),
            'number': data.get('number', '0'),
            'title': data.get('description'),
            'date': data.get('date', ''),
            'url': data.get('link'),
            'status': detect_status(full_text),
            'filename': file_path.name
        }
        index.append(entry)
```

#### `enrich_index_with_types.py`
**Función**: Enriquece índice con tipos de documentos
```python
def extract_document_types(full_text: str) -> Set[str]:
    """Extrae tipos de documentos del texto"""
    patterns = {
        'ordenanza': r'\bOrdenanza\s*N[°º]\s*\d+',
        'decreto': r'\bDecreto\s*N[°º]\s*\d+',
        'resolucion': r'\bResolución\s*N[°º]\s*\d+',
        'disposicion': r'\bDisposición\s*N[°º]\s*\d+',
        'convenio': r'\bConvenio\s*N[°º]\s*\d+',
        'licitacion': r'\bLicitación\s*N[°º]\s*\d+',
    }
    
    types_found = set()
    for doc_type, pattern in patterns.items():
        if re.search(pattern, full_text, re.IGNORECASE):
            types_found.add(doc_type)
    
    return types_found
```

#### `comprimir_boletines.py`
**Función**: Compresión gzip para distribución
```python
def comprimir_archivo(archivo: Path, mantener_original: bool = False):
    """Comprime archivo JSON con gzip"""
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    archivo_gz = archivo.with_suffix('.json.gz')
    with gzip.open(archivo_gz, 'wt', encoding='utf-8', compresslevel=9) as f:
        f.write(contenido)
    
    # Ahorro: ~533 MB → ~100 MB (80% reducción)
```

## Configuración de Modelos LLM

### Modelos Soportados
**Archivo**: `python-cli/MODELOS.md`

| Modelo | Costo | Calidad | Uso Recomendado |
|--------|-------|---------|-----------------|
| `z-ai/glm-4.5-air:free` | **GRATIS** | Buena | Pruebas, experimentación |
| `google/gemini-2.5-flash-lite` | Muy bajo | Muy buena | Producción económica |
| `google/gemini-3-flash-preview` | Bajo | Excelente | Balance calidad-precio |
| `x-ai/grok-4.1-fast` | Alto | Premium | Máxima calidad |

### Configuración Dinámica
```bash
# Modelo gratuito
python3 sibom_scraper.py --model z-ai/glm-4.5-air:free

# Modelo económico  
python3 sibom_scraper.py --model google/gemini-2.5-flash-lite

# Modelo premium
python3 sibom_scraper.py --model x-ai/grok-4.1-fast
```

## CLI y Argumentos

### Argumentos Principales
**Archivo**: `python-cli/sibom_scraper.py:750-800`

```python
parser.add_argument('--url', 
    default='https://sibom.slyt.gba.gob.ar/cities/22',
    help='URL de la página de listado O boletín individual')

parser.add_argument('--limit', type=int, default=None,
    help='Número máximo de boletines a procesar')

parser.add_argument('--parallel', type=int, default=1,
    help='Número de boletines en paralelo')

parser.add_argument('--model', type=str, 
    default='google/gemini-3-flash-preview',
    help='Modelo LLM de OpenRouter')

parser.add_argument('--skip-existing', action='store_true',
    help='Saltar automáticamente boletines existentes')
```

### Ejemplos de Uso
```bash
# Procesar boletín específico
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556

# Procesamiento masivo paralelo
python3 sibom_scraper.py --parallel 3 --skip-existing

# Página específica con límite
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22?page=6 --limit 5

# Modelo gratuito para pruebas
python3 sibom_scraper.py --limit 5 --model z-ai/glm-4.5-air:free
```

## Estructura de Salida

### Archivos Individuales
**Ubicación**: `boletines/{Ciudad}_{Numero}.json`
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

### Resumen Consolidado
**Ubicación**: `sibom_results.json` (configurable con `--output`)
```json
[
  {
    "number": "105º",
    "date": "30/12/2025",
    "description": "105º de Carlos Tejedor", 
    "link": "/bulletins/12345",
    "status": "completed",
    "fullText": "..."
  }
]
```

### Índice Navegable
**Ubicación**: `boletines/boletines.md`
```markdown
| Number | Date | Description | Link | Status |
|--------|------|-------------|------|--------|
| 105º | 23/12/2025 | 105º de Carlos Tejedor | [Link](https://sibom.slyt.gba.gob.ar/bulletins/14046) | ✅ Completado |
```

## Métricas de Performance

### Velocidad de Procesamiento
- **Secuencial**: 5-7s por boletín
- **Paralelo x3**: 2-3s por boletín efectivo
- **100 boletines**: ~3-5 minutos (paralelo) vs. ~10 minutos (secuencial)

### Precisión de Extracción
- **BeautifulSoup**: 95% casos exitosos
- **LLM Fallback**: 5% casos complejos
- **Tasa de éxito global**: >99%

### Costos por Modelo
- **Gratuito**: $0 (z-ai/glm-4.5-air:free)
- **Económico**: $0.06 por boletín (gemini-2.5-flash-lite)
- **Premium**: $0.24 por boletín (gemini-3-flash-preview)
- **Ultra**: $0.64 por boletín (grok-4.1-fast)

## Ventajas Arquitecturales

### vs. Versión React Original
- ✅ **Más rápido**: Sin proxies CORS, acceso directo
- ✅ **Procesamiento paralelo**: Múltiples boletines simultáneos  
- ✅ **Menos rate limiting**: Sin restricciones del navegador
- ✅ **Más confiable**: Sin problemas de CORS
- ✅ **Portátil**: Ejecuta en cualquier sistema

### Patrones de Diseño Aplicados
- **Hybrid Processing**: BeautifulSoup + LLM fallback
- **Strategy Pattern**: Modelos LLM intercambiables
- **Template Method**: Pipeline de 3 niveles consistente
- **Observer Pattern**: Progress tracking con Rich
- **Factory Pattern**: Creación de clientes OpenAI

## Conclusión

El backend Python representa una solución robusta y escalable para web scraping inteligente. Su arquitectura híbrida optimiza costos y performance, mientras que las características avanzadas como paginación automática y procesamiento paralelo lo hacen adecuado tanto para uso experimental como producción masiva.