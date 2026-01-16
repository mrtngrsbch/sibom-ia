# SIBOM Scraper - Python CLI

Scraper de boletines oficiales de SIBOM usando IA (OpenRouter + LLMs).

## Inicio Rápido

```bash
# 1. Instalación
cd python-cli
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configurar API key
cp .env.example .env
# Editar .env y agregar: OPENROUTER_API_KEY=sk-or-v1-...

# 3. Inicializar CITY_MAP (recomendado antes de escrapear)
python3 init_city_map.py

# 4. Ejecutar
python3 sibom_scraper.py --limit 5
```

**Sobre CITY_MAP.json:**

El archivo `boletines/CITY_MAP.json` contiene el mapeo de 85 ciudades (IDs a nombres) generado automáticamente desde SIBOM. Este archivo es necesario para que el scraper muestre los nombres correctos de las ciudades en el encabezado.

- **Generado automáticamente:** Ejecutando `python3 init_city_map.py`
- **Ubicación:** `boletines/CITY_MAP.json`
- **Contenido:** Mapeo de IDs a nombres de 85 ciudades
- **Edición:** Puedes editarlo manualmente si es necesario

```bash
# Para regenerar el CITY_MAP (si se agregan nuevas ciudades)
python3 init_city_map.py
```

## Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `python3 sibom_scraper.py --url https://.../cities/22` | Escrapear una ciudad específica (muestra nombre en encabezado) |
| `python3 sibom_scraper.py --limit 5` | Primeros 5 boletines |
| `python3 sibom_scraper.py --skip-existing` | Todas las páginas, salta existentes |
| `python3 sibom_scraper.py --url https://.../bulletins/13556` | Un boletín específico |
| `python3 sibom_scraper.py --limit 10 --parallel 3` | Con paralelismo |
| `python3 sibom_scraper.py --model z-ai/glm-4.5-air:free` | Con modelo gratuito |
| `python3 sibom_scraper.py --cities '1-21,23-136' --skip-existing --parallel 1` | Multi-ciudad con rangos |
| `python3 sibom_scraper.py --cities 1-136 --skip-existing --start-from 50` | Retomar desde ciudad 50 |
| `python3 sibom_scraper.py --cities 22 --limit 10` | Una ciudad específica (modo multi-ciudad) |

## Opciones CLI

| Opción | Default | Descripción |
|--------|---------|-------------|
| `--url` | `None` | URL de listado o boletín individual (ignorado con --cities) |
| `--cities` | `None` | Rangos de ciudades (ej: `"'1-21,23-136'"`) |
| `--start-from` | `None` | Retomar desde esta ciudad ID (solo con --cities) |
| `--limit` | `None` (todos) | Máximo de boletines a procesar por ciudad |
| `--parallel` | `1` | Boletines en paralelo |
| `--output` | `sibom_results.json` | Archivo de salida |
| `--model` | `z-ai/glm-4.5-air:free` | Modelo LLM de OpenRouter |
| `--skip-existing` | `False` | Saltar automáticamente existentes |
| `--api-key` | Desde `.env` | API key de OpenRouter |

## Estructura del Proyecto

```
python-cli/
├── sibom_scraper.py              # Scraper principal
├── init_city_map.py              # Script de inicialización de CITY_MAP
├── table_extractor.py            # Extracción de tablas
├── monto_extractor.py            # Extracción de montos
├── normativas_extractor.py       # Extracción de normativas
├── scripts/                      # Scripts auxiliares
├── tests/                        # Tests unitarios
├── docs/                         # Documentación técnica
├── boletines/                    # Boletines procesados
│   ├── *_*.json                  # Boletines individuales (todas las ciudades)
│   ├── CITY_MAP.json             # Mapeo completo de 85 ciudades (IDs a nombres)
│   └── boletines.md              # Índice markdown
├── sibom_results.json            # Resumen consolidado
├── montos_index.json             # Índice de montos
└── normativas_index_*.json       # Índices de normativas
```

## Modelos LLM

| Modelo | Costo | Calidad | Uso recomendado |
|--------|-------|---------|-----------------|
| `z-ai/glm-4.5-air:free` | GRATIS | Buena | Pruebas |
| `google/gemini-2.5-flash-lite` | Muy bajo | Muy buena | Producción económica |
| `google/gemini-3-flash-preview` | Bajo | Excelente | Balance calidad-precio |
| `x-ai/grok-4.1-fast` | Alto | Premium | Calidad máxima |

Ver [docs/modelos.md](docs/modelos.md) para análisis detallado.

## Modos de Operación

### Modo Listado

```bash
# Procesar boletines de una ciudad (muestra nombre en encabezado)
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22 --limit 5

# Con paginación automática
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22 --skip-existing
```

**Encabezado de ejemplo:**

```
╭─────────────── 🚀 Iniciando ────────────────╮
│ SIBOM Scraper                                │
│ Modo: 📋 Listado                             │
│ Ciudad: Carlos Tejedor (ID 22)               │
│ URL: https://sibom.slyt.gba.gob.ar/cities/22 │
│ Modelo: google/gemini-3-flash-preview        │
│ Límite: 5                                     │
│ Paralelismo: 1                                │
╰──────────────────────────────────────────────╯
```

**Sistema CITY_MAP.json:**

El scraper usa un archivo `boletines/CITY_MAP.json` que contiene el mapeo de 85 ciudades (IDs a nombres). Este archivo se generó automáticamente consultando SIBOM.

Para regenerar el CITY_MAP.json:
```bash
python3 init_city_map.py
```

**Comportamiento:**
- El encabezado muestra "Ciudad: [Nombre] (ID [ID])" directamente
- Si el ID no está en CITY_MAP.json, muestra "Ciudad ID: [ID]"
- Puedes editar manualmente `boletines/CITY_MAP.json` para agregar o corregir ciudades

### Modo Boletín Individual

```bash
# Un boletín específico
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556
```

### Modo Página Específica

```bash
# Solo una página (con ?page=)
python3 sibom_scraper.py --url "https://sibom.slyt.gba.gob.ar/cities/22?page=6"
```

### Modo Multi-Ciudad

```bash
# Múltiples ciudades con rangos concatenados
python3 sibom_scraper.py --cities '1-21,23-136' --skip-existing --parallel 1

# Retomar desde una ciudad específica (útil si se detuvo)
python3 sibom_scraper.py --cities 1-136 --skip-existing --start-from 50 --parallel 1

# Una sola ciudad
python3 sibom_scraper.py --cities 22 --limit 10

# Múltiples rangos con paralelismo
python3 sibom_scraper.py --cities 1-10,15-20,25-30 --parallel 4 --skip-existing
```

**Encabezado de ejemplo (multi-ciudad):**

```
╭─────────────── 🚀 Iniciando ────────────────╮
│ SIBOM Scraper                                │
│ Modo: Multi-Ciudad                           │
│ Ciudades: 21 (IDs 1-21)                      │
│ Nombres: Adolfo Alsina, Adolfo Gonzales Chaves... y 18 más
│ Límite: sin límite                            │
│ Paralelismo: 1                                │
│ Skip existing: True                           │
╰──────────────────────────────────────────────╯
```

**Notas:**
- El encabezado muestra los nombres de las ciudades (desde CITY_MAP.json)
- Sistema de CITY_MAP.json: Contiene el mapeo de 85 ciudades (IDs a nombres) generado automáticamente
- Todos los boletines se guardan en `boletines/` (sin subcarpetas)
- `--limit` se aplica por ciudad (no total)
- Compatible con `--skip-existing` y `--parallel`
- Usa `--start-from ID` para retomar desde una ciudad específica
- Los archivos JSON existentes se conservan (no se eliminan)

**Sistema CITY_MAP.json:**

El archivo `boletines/CITY_MAP.json` contiene el mapeo completo de IDs a nombres de ciudades. Este archivo se generó automáticamente consultando SIBOM.

```json
{
  "1": "Adolfo Alsina",
  "2": "Adolfo Gonzales Chaves",
  "22": "Carlos Tejedor",
  ...
}
```

Para regenerar el CITY_MAP.json:
```bash
python3 init_city_map.py
```

## Menú Interactivo

Cuando un boletín ya existe:

```
⚠ El archivo Carlos_Tejedor_105.json ya existe

¿Qué deseas hacer con el boletín 105º?
  1. Saltar y continuar con el siguiente
  2. Sobreescribir este boletín
  3. Cancelar todo el proceso

Elige una opción (1-3) [1]:
```

Usa `--skip-existing` para evitar el menú.

## Troubleshooting

| Error | Solución |
|-------|----------|
| `No se encontró OPENROUTER_API_KEY` | Crear `.env` con la API key |
| Procesamiento lento | Usar `--parallel 3` o modelo gratuito |
| Error en un boletín | Re-procesar individualmente con su URL |

## Documentación Adicional

- [docs/modelos.md](docs/modelos.md) - Guía completa de modelos LLM
- [docs/architecture.md](docs/architecture.md) - Arquitectura del sistema
- [docs/formato_v2.md](docs/formato_v2.md) - Formato de salida V2
- [docs/embeddings.md](docs/embeddings.md) - Configuración de embeddings

## Changelog

- **v4.0** - Sistema CITY_MAP.json con mapeo completo de 85 ciudades desde SIBOM
- **v3.1** - Nombre de ciudad se muestra después de procesar primer boletín, actualización automática de caché
- **v3.0** - Sistema de caché de ciudades (`.city_cache.json`) para almacenar nombres, método simplificado `get_city_name()`
- **v2.9** - Mejora en extracción de nombres de ciudades (múltiples patrones para HTML)
- **v2.8** - Encabezado mejorado con nombres de ciudades, obtención automática de nombres desde SIBOM
- **v2.7** - Modo multi-ciudad sin subcarpetas (todo en `boletines/`), opción `--start-from`, logs detallados de archivos saltados
- **v2.6** - Modo multi-ciudad con `--cities` (rangos concatenados: `"'1-21,23-136'"`)
- **v2.5** - Modelos LLM configurables
- **v2.4** - Modo boletín individual
- **v2.3** - Menú interactivo simplificado
- **v2.1** - Archivos `boletines.md` y `--skip-existing`
- **v2.0** - Normas individuales con URLs específicas
