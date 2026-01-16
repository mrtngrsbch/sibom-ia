# SIBOM Scraper - Guía para Claude Code

**Última actualización:** 2025-01-16

## Comandos Principales

```bash
# Activar entorno
source venv/bin/activate

# Procesar N boletines
python3 sibom_scraper.py --limit N

# Boletín específico
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/[ID]

# Con paralelismo
python3 sibom_scraper.py --limit N --parallel 3

# Skip existentes
python3 sibom_scraper.py --skip-existing
```

## Opciones CLI Disponibles

| Opción | Default | Descripción |
|--------|---------|-------------|
| `--url` | `cities/22` | URL de listado o boletín individual |
| `--limit` | `None` (todos) | Máximo de boletines a procesar |
| `--parallel` | `1` | Boletines en paralelo |
| `--output` | `sibom_results.json` | Archivo de salida |
| `--model` | `z-ai/glm-4.5-air:free` | Modelo LLM |
| `--skip-existing` | `False` | Saltar existentes automáticamente |
| `--api-key` | Desde `.env` | API key de OpenRouter |

## Estructura de Archivos

```
python-cli/
├── sibom_scraper.py        # Scraper principal
├── table_extractor.py      # Extracción de tablas
├── monto_extractor.py      # Extracción de montos
├── normativas_extractor.py # Extracción de normativas
├── scripts/                # Scripts auxiliares
├── tests/                  # Tests unitarios
├── docs/                   # Documentación técnica
├── boletines/              # Boletines individuales
├── README.md               # Documentación principal
├── QUICKSTART.md           # Referencia rápida
└── CLAUDE.md               # Este archivo
```

## Documentación

- [README.md](README.md) - Documentación principal
- [QUICKSTART.md](QUICKSTART.md) - Referencia rápida
- [docs/modelos.md](docs/modelos.md) - Guía de modelos LLM
- [docs/architecture.md](docs/architecture.md) - Arquitectura
- [docs/formato_v2.md](docs/formato_v2.md) - Formato V2
- [docs/embeddings.md](docs/embeddings.md) - Configuración embeddings

## Notas Importantes

1. **NO existe `--cities`** - El comando `--cities 1-21,23-136` mencionado en documentación antigua NO está implementado
2. **Modelo por defecto:** `z-ai/glm-4.5-air:free` (GRATIS)
3. **Paginación automática:** Detecta todas las páginas sin intervención
4. **Modo boletín individual:** Soporta URLs `/bulletins/[ID]`
