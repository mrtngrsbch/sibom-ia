# python-cli v3.0

Scraper de normativas municipales argentinas. Extrae datos de SIBOM, sitios web y documentos de transparencia usando Vision API.

## Instalación

```bash
cd python-cli

# Opción 1: Usar install.sh (recomendado)
bash install.sh

# Opción 2: Manual con uv
uv venv .venv
source .venv/bin/activate  # macOS/Linux: .venv\Scripts\activate (Windows)
uv pip install -r requirements.txt

# Instalar poppler (requerido para Vision API)
# macOS: brew install poppler
# Ubuntu: sudo apt-get install poppler-utils
```

## Configuración

Crear `.env`:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-...  # opcional
```

## Uso

```bash
# Ver ayuda general
python cli.py --help

# SIBOM - un municipio
python cli.py sibom --municipality "Carlos Tejedor" --limit 1

# SIBOM - todos
python cli.py sibom --all --limit 5

# Web scraping (lee desde sources_user.yaml)
python cli.py web --filter "Carlos Tejedor"

# Transparency - automático (lee URLs desde sources_user.yaml)
python cli.py transparency --municipality "Carlos Tejedor" --category balances

# Transparency - manual (para tests con URL específica)
python cli.py transparency --municipality "Carlos Tejedor" --category balances --url <URL>

# Transparency con skip-existing (para retomar)
python cli.py transparency --municipality "Carlos Tejedor" --category balances --skip-existing

# Transparency con límite (para probar)
python cli.py transparency --municipality "Carlos Tejedor" --category balances --limit 3

# Discovery - Descubrir PDFs automáticamente
python scripts/discover_carlos_tejedor.py --category balances
python scripts/discover_carlos_tejedor.py --category balances presupuestos concursos
python scripts/discover_carlos_tejedor.py --enable-all  # Habilitar todas las categorías

# Estado del scraping - Ver progreso
python scripts/status_carlos_tejedor.py
python scripts/status_carlos_tejedor.py --pending balances  # Ver PDFs pendientes

# Base de datos
python cli.py db --stats
python cli.py db --search --municipality "Carlos Tejedor"
python cli.py db --export output.json

# Vision API test
python cli.py vision --test

# Reconstruir índices
python cli.py index --rebuild
```

## Estructura

```
python-cli/
├── cli.py                     # CLI principal
├── core/                      # Scrapers
│   ├── sibom_scraper.py       # SIBOM
│   ├── web_scraper.py         # Web
│   └── data_models.py         # Dataclasses
├── extractors/                # Extractores
│   ├── vision_extractor.py    # Vision API
│   └── ...
├── utils/                     # Utilidades
│   └── sqlite_manager.py      # SQLite
├── config/                    # Configuración
│   ├── sources.yaml           # Plantilla
│   └── sources_user.yaml      # Tus fuentes (auto-generada por discovery)
├── scripts/                   # Scripts utilitarios
│   ├── discover_carlos_tejedor.py  # Discovery automático de PDFs
│   └── status_carlos_tejedor.py     # Estado del scraping
├── boletines/                 # JSON de boletines
│   └── {Municipio}/           # Por municipio
│       ├── .{category}_progress.json  # Archivo de progreso
│       ├── pdfs/              # PDFs originales (solo con --keep-pdf)
│       ├── *_Boletin_*.json   # SIBOM
│       ├── *_Ordenanzas*.json # Web
│       └── *_Balances_*.json  # Transparency (uno por PDF)
├── data/                      # BD e índices
│   ├── indexes/
│   └── normativas.db
└── requirements.txt
```

## Formato JSON

### Boletín (SIBOM/Web)
```json
{
  "municipio": "Carlos Tejedor",
  "numero_boletin": "57º",
  "total_normas": 432,
  "normas": [
    {
      "id": "1925688",
      "tipo": "ordenanza",
      "numero": "2833/23",
      "titulo": "Ordenanza Nº 2833/23",
      "contenido": "...",
      "tablas_md": [],
      "montos_extraidos": []
    }
  ]
}
```

### Transparency
```json
{
  "municipio": "Carlos Tejedor",
  "tipo_documento": "balance_sumas_saldos",
  "tablas_md": ["| Cuenta | Debe | Haber |"],
  "calidad": {"confidence": 0.9}
}
```

**Nota sobre el guardado de datos:**
- Cada PDF se guarda **individualmente** en un archivo JSON separado
- Formato: `{Municipio}_{Categoria}_{timestamp}_{hash}.json`
- Se mantiene un archivo `.progress.json` para retomar procesos interrumpidos
- **Ctrl+C ahora es seguro**: los PDFs procesados se guardan antes de salir

## SQLite

- **normativas**: metadata ligera
- **normativa_content**: contenido pesado (tablas_md, montos)

## Discovery - Descubrimiento Automático de PDFs

El script `discover_carlos_tejedor.py` scrapea automáticamente las páginas de transparencia y descubre todos los PDFs disponibles.

```bash
# Descubrir PDFs de Balances (actualiza sources_user.yaml)
python scripts/discover_carlos_tejedor.py --category balances

# Descubrir múltiples categorías
python scripts/discover_carlos_tejedor.py --category balances presupuestos concursos

# Descubrir todas y habilitarlas
python scripts/discover_carlos_tejedor.py --enable-all
```

**Categorías disponibles:**
- `balances` - Balances, Tesorería, Gastos, Recursos (~170 PDFs)
- `presupuestos` - Presupuestos anuales (~45 PDFs)
- `concursos` - Concursos de precios
- `licitaciones_privadas` - Licitaciones privadas
- `licitaciones_publicas` - Licitaciones públicas

Luego de ejecutar el discovery, las URLs se agregan automáticamente a `config/sources_user.yaml` y puedes usar el comando de transparency:

```bash
python cli.py transparency --municipality "Carlos Tejedor" --category balances --skip-existing
```

## Tests

```bash
python cli.py vision --test
python cli.py db --stats
```

## Script de Estado

El script `status_carlos_tejedor.py` muestra el estado completo del scraping:

```bash
python scripts/status_carlos_tejedor.py
```

**Muestra:**
- PDFs descubiertos por categoría
- PDFs procesados vs pendientes
- Archivos JSON generados
- Calidad de extracción
- Rate limit de Vision API
- Progreso global con barras visuales

**Ver PDFs pendientes:**
```bash
python scripts/status_carlos_tejedor.py --pending balances
```
