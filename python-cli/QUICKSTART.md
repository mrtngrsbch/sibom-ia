# SIBOM Scraper - Quick Start

Comandos esenciales para empezar a usar el scraper rápidamente.

## Setup (una sola vez)

```bash
cd python-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env: OPENROUTER_API_KEY=sk-or-v1-tu-key
```

## Comandos Esenciales

```bash
# Activar entorno (siempre primero)
source venv/bin/activate

# Probar scraper - 1 boletín
python3 sibom_scraper.py --limit 1

# 5 boletines
python3 sibom_scraper.py --limit 5

# Todas las páginas, automático
python3 sibom_scraper.py --skip-existing

# Boletín específico (modo individual)
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556

# Con paralelismo (más rápido)
python3 sibom_scraper.py --limit 20 --parallel 3

# Modelo gratuito (costo $0)
python3 sibom_scraper.py --limit 10 --model z-ai/glm-4.5-air:free
```

## URLs Útiles

| Ciudad | URL |
|--------|-----|
| Carlos Tejedor (default) | `https://sibom.slyt.gba.gob.ar/cities/22` |
| Merlo | `https://sibom.slyt.gba.gob.ar/cities/23` |

## Solución de Problemas

```bash
# Ver si hay errores en boletines procesados
cat boletines/boletines.md | grep "❌"

# Re-procesar un boletín con error
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/[ID]

# Ver ayuda completa
python3 sibom_scraper.py --help
```

## Archivos Importantes

| Archivo | Contenido |
|---------|-----------|
| `boletines/boletines.md` | Índice de boletines procesados |
| `boletines/*.json` | Boletines individuales |
| `sibom_results.json` | Resumen consolidado |
| `normativas_index_minimal.json` | Índice para chatbot |
