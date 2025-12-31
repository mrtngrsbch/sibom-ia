# SIBOM Scraper Assistant

Herramienta de extracción de boletines oficiales municipales de SIBOM (Sistema Integrado de Boletines Oficiales Municipales de la Provincia de Buenos Aires).

## 🐍 Proyecto Python CLI

Este proyecto ha sido migrado completamente a Python. Toda la documentación y el código fuente están en la carpeta `python-cli/`.

**Ver documentación completa:** [python-cli/README.md](python-cli/README.md)

## 🚀 Inicio Rápido

```bash
cd python-cli
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env y agrega tu OPENROUTER_API_KEY
python3 sibom_scraper.py --limit 5
```

## 📂 Estructura del Proyecto

```
sibom-scraper-assistant/
├── python-cli/               # Proyecto principal (Python)
│   ├── sibom_scraper.py     # Script principal del scraper
│   ├── boletines/           # Boletines extraídos (JSON)
│   │   └── csv/             # Herramientas de conversión JSON→CSV
│   │       ├── json2csv.py
│   │       └── JSON2CSV.md
│   ├── README.md            # Documentación completa
│   ├── MODELOS.md           # Guía de modelos LLM
│   ├── EJEMPLOS_USO.md      # Ejemplos prácticos
│   └── CHANGELOG.md         # Historial de cambios
└── MIGRACION.md             # Historia de migración React → Python
```

## 🔗 Documentación

- **[README Principal](python-cli/README.md)** - Instalación y uso del scraper
- **[Guía de Modelos](python-cli/MODELOS.md)** - Comparación de modelos LLM (costos, calidad)
- **[Ejemplos de Uso](python-cli/EJEMPLOS_USO.md)** - Casos prácticos y comandos
- **[JSON to CSV](python-cli/boletines/csv/JSON2CSV.md)** - Conversión de datos a CSV
- **[Historia de Migración](MIGRACION.md)** - Migración de React a Python

## 🎯 Características

- ✅ Extracción automatizada de boletines municipales usando LLM (OpenRouter)
- ✅ Soporte para múltiples modelos (Gemini, Grok, GLM) con opción **GRATIS**
- ✅ Procesamiento paralelo de múltiples boletines
- ✅ Sistema de 3 niveles: Listado → Enlaces → Texto completo
- ✅ Conversión a CSV para análisis de datos
- ✅ Índice markdown automático con tracking de estado
- ✅ Modo automático con `--skip-existing`

## 💰 Modelo Gratuito Disponible

```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free
```

**100% gratis, sin límites**, sin necesidad de créditos en OpenRouter.

## 📊 Exportar a CSV

```bash
cd python-cli/boletines/csv
python3 json2csv.py *.json
# Genera: boletines_YY-MM-DD_HH-MM-SS.csv
```

## 🤝 Contribuciones

Este es un proyecto educativo para demostrar el uso de LLMs en extracción de datos estructurados desde HTML.

## 📄 Licencia

Proyecto de código abierto. Ver carpeta `python-cli/` para más detalles.
