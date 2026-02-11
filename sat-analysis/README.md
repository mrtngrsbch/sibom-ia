# sat-analysis

Sistema de detección de anegamiento y salinización usando imágenes satelitales Sentinel-2, HLS (Harmonized Landsat-Sentinel-2) y Microsoft Planetary Computer.

**Dos modos de uso:**
- 🖥️ **CLI** - Línea de comandos para análisis local
- 🌐 **Web** - Interfaz Gradio para deploy en la nube

## Características

- Consulta de parcelas catastrales ARBA por partida
- Descarga de imágenes Sentinel-2 L2A y HLS desde STAC Planetary Computer
- Cálculo de índices espectrales: NDWI, MNDWI, NDVI, NDMI, NDSI, Salinity Index
- Clasificación de píxeles en: Agua, Humedal, Vegetación, Otros
- Detección de salinización usando banda SWIR2 (B12)
- Análisis temporal con tendencias
- Exportación de resultados en JSON

---

## 🌐 Interfaz Web (Gradio)

### Instalación con dependencias web

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

El sistema ahora soporta múltiples formatos de partida ARBA:

```bash
# Formato completo (9 dígitos: partido + partida)
sat-analysis analyze 002004606

# Formato con guiones y verificador
sat-analysis analyze 002-004606-0

# Formato con guiones sin verificador
sat-analysis analyze 002-004606

# Formato legacy (solo partida, usa partido por defecto 002)
sat-analysis analyze 4606

# Otros partidos (ej: La Plata = 055)
sat-analysis analyze 055123456
```

### Formatos de Partida Aceptados

| Formato | Ejemplo | Descripción |
|---------|---------|-------------|
| `002004606` | 9 dígitos sin separadores | Partido (002) + Partida (004606) |
| `00200460` | 8 dígitos sin separadores | Partido (002) + Partida (00460, se completa a 004606) |
| `002-004606-0` | Con guiones y verificador | Partido + Partida + Dígito verificador |
| `002-004606` | Con guiones sin verificador | Partido + Partida |
| `4606` | Solo partida (legacy) | Usa partido por defecto (002 Alberti) |

> **Nota técnica:** El servicio WFS de ARBA almacena el número de partida en un campo único `pda` con **9 dígitos** (partido + partida). Por ejemplo, la partida `017001378` se compone del partido `017` (Carlos Tejedor) y la partida individual `001378`.

### Usar coordenadas fijas (sin ARBA)

```bash
sat-analysis analyze coords:-60.144,-35.173,-60.116,-35.150
```

### Opciones avanzadas

```bash
# Análisis con muestreo trimestral (default: 4 imágenes por año)
sat-analysis analyze 002004606 \
  --years 10 \
  --samples-per-year 4 \
  --max-clouds 20

# Análisis con muestreo mensual (12 imágenes por año = 120 imágenes en 10 años)
sat-analysis analyze 002004606 \
  --years 10 \
  --samples-per-year 12 \
  --max-clouds 30

# Comportamiento clásico (solo imágenes más recientes)
sat-analysis analyze 002004606 \
  --years 2 \
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
| `--samples-per-year` | `-s` | Imágenes por año con distribución uniforme (1-12) | 4 |
| `--max-images` | `-n` | Máximo de imágenes (deprecated, usa --samples-per-year) | 10 |
| `--max-clouds` | `-c` | Máximo % de nubes (0-100) | 20 |
| `--output` | `-o` | Archivo JSON de salida | - |
| `--verbose` | `-v` | Output detallado | - |
| `--logs-dir` | `-l` | Directorio para archivos de log | `logs` |
| `--images-dir` | `-i` | Directorio para imágenes | `logs_images` |

### Muestreo Temporal

El parámetro `--samples-per-year` implementa **muestreo temporal uniforme**:

- **Default: 4** (muestreo trimestral)
- Divide el período en intervalos regulares
- Selecciona la mejor imagen de cada intervalo
- Total de imágenes = `samples_per_year × years`

**Ejemplos:**

| Años | Samples/Year | Total Imágenes | Distribución |
|------|--------------|----------------|--------------|
| 2 | 4 | 8 | 1 por trimestre |
| 5 | 4 | 20 | 1 por trimestre |
| 10 | 4 | 40 | 1 por trimestre |
| 10 | 12 | 120 | 1 por mes |

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

El sistema calcula 6 índices espectrales desde las bandas de Sentinel-2:

| Índice | Fórmula | Banda | Descripción | Fuente Científica | Estado |
|--------|---------|-------|-------------|-------------------|--------|
| **NDWI** | (Green - NIR) / (Green + NIR) | B03, B08 | Normalized Difference Water Index - Agua | McFeeters (1996) | ✅ VÁLIDO |
| **MNDWI** | (Green - SWIR1) / (Green + SWIR1) | B03, B11 | Modified NDWI - Agua turbia | Xu (2006) | ✅ VÁLIDO |
| **NDVI** | (NIR - Red) / (NIR + Red) | B08, B04 | Normalized Difference Vegetation Index - Vegetación | Rouse et al. (1973) | ✅ VÁLIDO |
| **NDMI** | (NIR - SWIR1) / (NIR + SWIR1) | B08, B11 | Normalized Difference Moisture Index - Humedad | Wilson & Sader (2002) | ✅ VÁLIDO |
| **NDSI** | (Green - SWIR2) / (Green + SWIR2) | B03, B12 | Normalized Difference Salinity Index - Salinidad | SoilSaltIndex R Package | ⚠️ VARIANTE |
| **SI** | SWIR2 / (SWIR2 + NIR) | B12, B08 | Salinity Index - Salinidad | SoilSaltIndex R Package | ⚠️ VARIANTE |

## Clasificación de Píxeles

Los píxeles se clasifican en 4 categorías según umbrales ajustados para Argentina:

| Clase | Condición | Color |
|-------|-----------|-------|
| **Agua** | NDWI > 0.15 OR MNDWI > 0.25 | Azul |
| **Humedal** | NDVI > 0.35 AND NDMI > 0.10 AND NDWI > -0.6 | Verde oscuro |
| **Vegetación** | NDVI > 0.5 AND NDMI < 0.2 | Verde claro |
| **Otros** | Resto | Gris |

### Ajuste de Umbrales

Los umbrales de clasificación se pueden modificar editando el archivo `thresholds.yaml`:

```bash
# Ubicación: sat-analysis/thresholds.yaml
# Editar con cualquier editor de texto
nano thresholds.yaml
```

Ejemplo del archivo `thresholds.yaml`:

```yaml
# Umbrales de clasificación

water:
  ndwi_threshold: 0.18      # NDWI > agua (default: 0.15)
  mndwi_threshold: 0.28     # MNDWI > agua turbia (default: 0.25)

wetland:
  ndvi_threshold: 0.38      # NDVI > vegetación húmeda (default: 0.35)
  ndmi_threshold: 0.12      # NDMI > humedad (default: 0.10)
  ndwi_threshold: -0.5      # NDWI > permite vegetación húmeda (default: -0.6)

vegetation:
  ndvi_threshold: 0.52      # NDVI > vegetación seca (default: 0.5)
  ndmi_threshold: 0.18      # NDMI < límite superior (default: 0.2)
```

**Valores por defecto** (ajustados para humedales de Argentina):

| Umbral | Water | Wetland | Vegetation | Descripción |
|--------|-------|---------|------------|-------------|
| `ndwi_threshold` | 0.15 | -0.6 | - | NDWI para agua/humedal |
| `mndwi_threshold` | 0.25 | - | - | MNDWI para agua turbia |
| `ndvi_threshold` | - | 0.35 | 0.5 | NDVI para vegetación |
| `ndmi_threshold` | - | 0.10 | 0.2 | NDMI para humedad |

### Validación Científica de Umbrales

Los umbrales utilizados han sido validados contra literatura científica peer-reviewed:

| Parámetro | Valor Actual | Rango Científico | Fuente |
|-----------|--------------|------------------|--------|
| `water.ndwi_threshold` | 0.15 | 0.0 - 0.3 | McFeeters 1996; FarmOnaut 2024 ✅ |
| `water.mndwi_threshold` | 0.25 | 0.2 - 0.4 | Xu 2006; MDPI studies ✅ |
| `wetland.ndvi_threshold` | 0.35 | 0.125 - 0.5 | UNEP 2010; Al-Maliki 2022 ✅ |
| `wetland.ndmi_threshold` | 0.10 | 0.0 - 0.2 | Berca 2022; Al-Maliki 2022 ✅ |
| `vegetation.ndvi_threshold` | 0.5 | 0.4 - 0.6 | UNEP 2010; Al-Maliki 2022 ✅ |

**Precisión reportada en literatura:** 78-90% según el método y región. Las tasas de error del 15-25% son típicas en clasificación de humedales por teledetección.

**Referencias:**
- Al-Maliki et al. (2022). Water 14(10):1523. [DOI:10.3390/w14101523](https://doi.org/10.3390/w14101523)
- Xu (2006). Int. J. Remote Sensing 27:3025-3033. [DOI:10.1080/01431160600589179](https://doi.org/10.1080/01431160600589179)
- McFeeters (1996). Int. J. Remote Sensing 17:1425-1432.

### Script de Calibración

Para ajustar los umbrales con un grupo de partidas de referencia:

```bash
# Usar el script de calibración
python scripts/calibrate_thresholds.py reference_parcels.json

# Probar una partida individual con valores conocidos
python scripts/calibrate_thresholds.py --partida 002004606 --water 5.2 --wetland 95.0 --vegetation 0.5 --other 232.1
```

## Fuentes Satelitales

### Sentinel-2 L2A

- **Resolución:** 10m (RGB, NIR), 20m (SWIR)
- **Frecuencia:** Cada 5 días
- **Bandas:** B02(Blue), B03(Green), B04(Red), B08(NIR), B11(SWIR1), B12(SWIR2)

### HLS (Harmonized Landsat-Sentinel-2)

- **Resolución:** 10m
- **Frecuencia:** 2-3 días (combinando S30 y L30)
- **Colecciones:**
  - `HLS.S30`: Datos harmonizados de Sentinel-2
  - `HLS.L30`: Datos harmonizados de Landsat 8

El sistema puede buscar en múltiples colecciones simultáneamente para maximizar la frecuencia de imágenes disponibles.

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

### 1. Análisis histórico con muestreo trimestral (recomendado)

```bash
# 10 años de histórico, 4 imágenes por año = 40 imágenes distribuidas uniformemente
sat-analysis analyze 002004606 --years 10 --samples-per-year 4
```

### 2. Análisis con muestreo mensual

```bash
# 5 años de histórico, 12 imágenes por año = 60 imágenes (1 por mes)
sat-analysis analyze 002004606 --years 5 --samples-per-year 12 --max-clouds 30
```

### 3. Análisis rápido de últimos años

```bash
# 2 años, 2 imágenes por año = 4 imágenes (semestral)
sat-analysis analyze 002004606 --years 2 --samples-per-year 2
```

### 4. Análisis de área específica (sin partida)

```bash
sat-analysis analyze coords:-60.144,-35.173,-60.116,-35.150 \
  --years 5 \
  --samples-per-year 4
```

### 5. Generar imágenes de diagnóstico

```bash
python scripts/diagnose_indices.py
```

### 6. Validar servicios antes de análisis

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
| `No se encontraron imágenes` | Aumenta `--years`, `--samples-per-year` o `--max-clouds` |
| `Timeout al consultar ARBA` | Reintenta, el servicio puede estar saturado |
| `Error descargando bandas: No module named 'dask'` | Reinstala: `pip install -e .` |
| `--samples-per-year debe estar entre 1 y 12` | El valor debe ser entre 1 y 12 imágenes por año |

---

## 🚀 Deploy en Railway

La interfaz web con Gradio puede hacer deploy directamente en Railway.

### Paso 1: Preparar el repositorio

Asegúrate de tener estos archivos en la raíz del proyecto `sat-analysis/`:

```
sat-analysis/
├── app.py              # Interfaz Gradio
├── requirements.txt    # Dependencias para Railway
└── src/sat_analysis/   # Código del proyecto
```

### Paso 2: Crear servicio en Railway

1. Ve a [railway.app](https://railway.app/)
2. Crea un nuevo proyecto
3. Selecciona "Deploy from GitHub repo"
4. Elige el repositorio `sibom-ia`
5. Configura:
   - **Root Directory:** `sat-analysis`
   - **Python Version:** `3.13`
   - **Start Command:** `python app.py`

### Paso 3: Variables de entorno

No se requieren variables de entorno para el funcionamiento básico.

### Paso 4: Deploy

Railway detectará automáticamente `requirements.txt` e instalará las dependencias.

### Ejecutar localmente

```bash
# Instalar dependencias web
pip install -e ".[web]"

# O desde requirements.txt
pip install -r requirements.txt

# Ejecutar la app
python app.py
```

La interfaz estará disponible en `http://localhost:7860`

### Roadmap - Fase 2 (FastAPI + Frontend)

Para una versión más avanzada, se planea:

- **Backend:** FastAPI con endpoints REST
- **Frontend:** Next.js + React
- **Autenticación:** Usuarios protegidos
- **Base de datos:** Historial de análisis
- **Mapas interactivos:** Leaflet/MapLibre

---

## Licencia

MIT
