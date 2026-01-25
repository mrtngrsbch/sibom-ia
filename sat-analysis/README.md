# sat-analysis

Sistema de detección de anegamiento y salinización usando imágenes satelitales Sentinel-2 y Microsoft Planetary Computer.

## Características

- Consulta de parcelas catastrales ARBA por partida
- Descarga de imágenes Sentinel-2 L2A desde STAC Planetary Computer
- Cálculo de índices espectrales: NDWI, MNDWI, NDVI, NDMI
- Clasificación de píxeles en: Agua, Humedal, Vegetación, Otros
- Análisis temporal con tendencias
- Exportación de resultados en JSON

## Instalación

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# o
.venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -e .
```

## Uso Básico

### Analizar una partida catastral

```bash
sat-analysis analyze 002004606
```

### Usar coordenadas fijas (sin ARBA)

```bash
sat-analysis analyze coords:-60.144,-35.173,-60.116,-35.150
```

### Opciones avanzadas

```bash
sat-analysis analyze 002004606 \
  --years 3 \
  --max-images 10 \
  --max-clouds 20 \
  --output resultados.json \
  --verbose
```

## Comandos Disponibles

### `analyze`

Analiza una partida catastral para detectar anegamiento.

Las imágenes de índices espectrales se guardan automáticamente en cada ejecución.

| Opción | Corto | Descripción | Por defecto |
|--------|-------|-------------|-------------|
| `--years` | `-y` | Años de histórico a analizar (1-10) | 2 |
| `--max-images` | `-n` | Máximo de imágenes a procesar | 10 |
| `--max-clouds` | `-c` | Máximo % de nubes (0-100) | 20 |
| `--output` | `-o` | Archivo JSON de salida | - |
| `--verbose` | `-v` | Output detallado | - |
| `--logs-dir` | `-l` | Directorio para archivos de log | `logs` |
| `--images-dir` | `-i` | Directorio para imágenes | `logs_images` |

### `validate`

Valida las conexiones a los servicios externos.

```bash
# Validar ambos servicios
sat-analysis validate

# Validar solo ARBA
sat-analysis validate --arba --partida 002004606

# Validar solo STAC
sat-analysis validate --stac
```

### `version`

Muestra la versión del programa.

```bash
sat-analysis version
```

## Formato de Partida

El formato correcto para partidas catastrales de ARBA es **8 dígitos** con ceros a la izquierda:

```bash
# Correcto
sat-analysis analyze 002004606

# Incorrecto (se debe completar con ceros)
sat-analysis analyze 4606
```

## Índices Espectrales

El sistema calcula 4 índices espectrales desde las bandas de Sentinel-2:

| Índice | Fórmula | Banda | Descripción |
|--------|---------|-------|-------------|
| **NDWI** | (Green - NIR) / (Green + NIR) | B03, B08 | Normalized Difference Water Index - Agua |
| **MNDWI** | (Green - SWIR) / (Green + SWIR) | B03, B11 | Modified NDWI - Agua turbia |
| **NDVI** | (NIR - Red) / (NIR + Red) | B08, B04 | Normalized Difference Vegetation Index - Vegetación |
| **NDMI** | (NIR - SWIR) / (NIR + SWIR) | B08, B11 | Normalized Difference Moisture Index - Humedad |

## Clasificación de Píxeles

Los píxeles se clasifican en 4 categorías según umbrales ajustados para Argentina:

| Clase | Condición | Color |
|-------|-----------|-------|
| **Agua** | NDWI > 0.15 OR MNDWI > 0.25 | Azul |
| **Humedal** | NDVI > 0.35 AND NDMI > 0.10 AND NDWI > -0.6 | Verde oscuro |
| **Vegetación** | NDVI > 0.5 AND NDMI < 0.2 | Verde claro |
| **Otros** | Resto | Gris |

## Salida

### Terminal

```
📍 Consultando partida 002004606...
✅ Parcela encontrada
   BBOX: [-60.144216, -35.173456, -60.115567, -35.150093]
   Área: 333.6 ha (desde ARBA)

🛰️ Buscando imágenes...
   Período: 2024-01-26/2026-01-25
   Máx nubes: 20%
✅ 5 imágenes encontradas

📊 Procesando imágenes...

┏━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Fecha      ┃ Agua (ha) ┃ Humedal (ha) ┃ Vegetación (ha) ┃ Otros (ha) ┃ Nubes % ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━┩
│ 2026-01-22 │       0.0 │        189.3 │           0.3 │      144.1 │       0 │
│ 2026-01-20 │       0.0 │        206.3 │           0.1 │      127.2 │       2 │
└────────────┴───────────┴──────────────┴───────────────┴────────────┴─────────┘

Área total: 333.6 ha

Resumen:
   Máximo agua: 0.0 ha
   Máximo humedal: 207.9 ha
   Promedio agua: 0.0 ha
   Promedio humedal: 196.7 ha

Porcentaje máximo afectado:
   Agua + Humedal: 207.9 ha (62.3%)

Tendencia agua: ➡️ (+0.0 ha)
Tendencia humedal: ↗️ (+8.8 ha)
```

### JSON (con --output)

```json
{
  "partida": "002004606",
  "bbox": [-60.144216, -35.173456, -60.115567, -35.150093],
  "total_area_hectares": 333.6,
  "date_range": "2023-01-26/2025-01-25",
  "images_analyzed": 5,
  "results": [
    {
      "date": "2026-01-22T13:46:59.024000Z",
      "water_ha": 0.0,
      "wetland_ha": 189.3,
      "vegetation_ha": 0.3,
      "other_ha": 144.1,
      "cloud_cover": 0.0
    }
  ]
}
```

### Archivos de Log

Cada ejecución genera automáticamente un archivo de log con el formato `log_{partida}_{fecha}_{hora}.log`:

```
logs/
├── log_002004606_2026-01-25_143022.log
├── log_004567890_2026-01-24_091530.log
└── ...
```

El log contiene:
- Fecha y hora de ejecución
- Parámetros de análisis
- Progreso de descarga y procesamiento
- Tabla de resultados en formato texto
- Resumen estadístico

**Especificar directorio de logs:**

```bash
sat-analysis analyze 002004606 --logs-dir ~/mis-logs
```

## Scripts de Diagnóstico

### `diagnose_indices.py`

Genera imágenes PNG de los índices espectrales para análisis visual.

```bash
python scripts/diagnose_indices.py
```

**Archivos generados:** `diagnostic_output/`

- `ndwi_{partida}_{fecha}.png` - Índice de agua
- `mndwi_{partida}_{fecha}.png` - Índice de agua turbia
- `ndvi_{partida}_{fecha}.png` - Índice de vegetación
- `ndmi_{partida}_{fecha}.png` - Índice de humedad
- `clasificación_{partida}_{fecha}.png` - Mapa de clasificación

### Scripts de validación

```bash
# Validar conexión STAC Planetary Computer
python scripts/validate_stac.py

# Validar conexión ARBA WFS
python scripts/validate_arba.py
```

## Servicios Utilizados

### ARBA WFS

- **URL:** `https://geo.arba.gov.ar/geoserver/idera/wfs`
- **Capa:** `idera:Parcela`
- **CRS:** EPSG:5347 (UTM Zona 20S - Argentina)
- **Campos:**
  - `pda`: Partida (8 dígitos)
  - `ara1`: Superficie en m²
  - `cca`: Nomenclatura catastral

### Microsoft Planetary Computer STAC

- **URL:** `https://planetarycomputer.microsoft.com/api/stac/v1`
- **Colección:** `sentinel-2-l2a`
- **Bandas:** B02, B03, B04, B08 (10m), B11 (20m→10m)
- **Frecuencia:** Cada 5 días
- **Resolución:** 10m

## Casos de Uso

### 1. Análisis de una parcela rural

```bash
sat-analysis analyze 002004606 --years 3 --max-clouds 30
```

### 2. Análisis con máximo detalle

```bash
sat-analysis analyze 002004606 \
  --years 5 \
  --max-images 20 \
  --max-clouds 10 \
  --verbose \
  --output analisis_completo.json
```

### 3. Análisis de área específica (sin partida)

```bash
sat-analysis analyze coords:-60.144,-35.173,-60.116,-35.150 \
  --years 2 \
  --max-images 5
```

### 4. Generar imágenes de diagnóstico

```bash
python scripts/diagnose_indices.py
```

### 5. Validar servicios antes de análisis

```bash
sat-analysis validate --arba --partida 002004606
```

## Dependencias

```
pystac-client      # Cliente STAC
planetary-computer # Signing de URLs Azure
rasterio           # Lectura de imágenes geoespaciales
xarray             # Arrays multidimensionales
rioxarray          # Geo-xarray integration
dask               # Procesamiento paralelo
scipy              # Remuestreo de bandas
numpy              # Cálculos numéricos
requests           # HTTP client
pydantic           # Validación de datos
typer              # CLI
rich               # Terminal output formateado
pyproj             # Transformaciones de coordenadas
shapely            # Operaciones geométricas
```

## Estructura del Proyecto

```
sat-analysis/
├── src/sat_analysis/
│   ├── __init__.py
│   ├── cli.py              # Entry point CLI
│   ├── config.py           # Configuración
│   ├── models/
│   │   └── schemas.py      # Modelos Pydantic
│   └── services/
│       ├── arba.py         # Cliente ARBA WFS
│       ├── stac.py         # Cliente Planetary Computer
│       └── classifier.py   # Clasificador de píxeles
├── scripts/
│   ├── validate_arba.py    # Validación ARBA
│   ├── validate_stac.py    # Validación STAC
│   └── diagnose_indices.py # Generación de imágenes de diagnóstico
├── diagnostic_output/      # Imágenes PNG generadas
└── pyproject.toml          # Dependencias
```

## Notas Técnicas

### Factor de Corrección

Como el recorte por bbox es rectangular, se aplica un factor de corrección basado en el área real de la parcela (campo ARA1 de ARBA):

```
factor = área_ARBA / área_bbox_recortado
áreas_corregidas = áreas_crudas × factor
```

### Conversión de Coordenadas

ARBA devuelve coordenadas en **EPSG:5347** (UTM Zona 20S). El sistema las convierte automáticamente a **EPSG:4326** (WGS84) para consultar Planetary Computer.

### Resolución de Bandas

- B02, B03, B04, B08: 10m
- B11: 20m (remuestreada a 10m usando scipy.ndimage.zoom)

## Errores Comunes

| Error | Solución |
|-------|----------|
| `Partida no encontrada` | Usa formato 8 dígitos: `002004606` |
| `No se encontraron imágenes` | Aumenta `--years` o `--max-clouds` |
| `Timeout al consultar ARBA` | Reintenta, el servicio puede estar saturado |
| `Error descargando bandas: No module named 'dask'` | Reinstala: `pip install -e .` |

## Licencia

MIT
