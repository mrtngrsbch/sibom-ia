# Guía de Extracción de PDFs con Vision API

**Última actualización:** 2026-02-02
**Versión:** 5.0

---

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Comando `scrape` (Simplificado)](#comando-scrape)
3. [Comando `transparency` (Avanzado)](#comando-transparency)
4. [Archivos Generados](#archivos-generados)
5. [Ejemplos Prácticos](#ejemplos-prácticos)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Resumen Ejecutivo

El scraper de PDFs extrae contenido de documentos financieros municipales:
- **PDFs originales** se guardan para auditoría manual
- **JSON estructurado** para ingesta a SQLite/chatbot
- **Reportes Markdown** para visualización rápida

### Estrategia de Extracción

| Nivel | Motor | Modelo | Costo | Columnas |
|-------|-------|--------|-------|----------|
| **1** | File API | Gemini 2.5 Flash Lite | **$0.00** | ⚠️ Puede alterar |
| **2** | Vision Chunks | Gemini 2.5 Flash Lite | ~$1-3 | ✅ Correctas |

**Comportamiento:** Intenta Nivel 1 → Si falla → Nivel 3

---

## 🚀 Comando `scrape` (Simplificado)

**Nuevo comando recomendado para uso diario.**

### Sintaxis

```bash
python cli.py scrape <municipio> <categoria> [opciones]
```

### Argumentos Posicionales

| Argumento | Descripción |
|-----------|-------------|
| `municipio` | Nombre del municipio (ej: "Carlos Tejedor") |
| `categoria` | Categoría (balances, presupuestos, etc.) |

### Opciones

| Opción | Default | Descripción |
|--------|---------|-------------|
| `--save-pdfs` | True | Guardar PDFs originales en `pdfs/` |
| `--no-save-pdfs` | - | No guardar PDFs (solo JSON) |
| `--resume` | - | Retomar donde se quedó (omite procesados) |
| `--test` | - | Modo prueba (guarda en `{municipio}_test/`) |
| `--limit N` | 0 (todos) | Procesar solo N PDFs |

### Ejemplos Rápidos

```bash
# Scraping normal (guarda PDFs + JSON)
python cli.py scrape "Carlos Tejedor" balances

# Retomar interrumpido
python cli.py scrape "Carlos Tejedor" balances --resume

# Modo prueba (no afecta producción)
python cli.py scrape "Carlos Tejedor" balances --test

# Probar solo 5 PDFs
python cli.py scrape "Carlos Tejedor" balances --limit 5

# Sin guardar PDFs (solo JSON)
python cli.py scrape "Carlos Tejedor" balances --no-save-pdfs
```

---

## 🔧 Comando `transparency` (Avanzado)

**Comando original con más opciones de configuración.**

### Sintaxis

```bash
python cli.py transparency --municipality <municipio> --category <categoria> [opciones]
```

### Opciones Principales

| Opción | Default | Descripción |
|--------|---------|-------------|
| `--municipality` | Requerido | Nombre del municipio |
| `--category` | Requerido | Categoría (balances, presupuestos, etc.) |
| `--pdf-engine` | auto | Motor (auto, free, vision-chunks) |
| `--url` | - | URL específica de PDF |
| `--test-dir` | - | Guardar en `test/` en lugar de `boletines/` |
| `--skip-large-pdfs` | - | Saltar PDFs grandes (>50 pág) |
| `--large-pdf-threshold` | 50 | Umbral de páginas para "grande" |
| `--keep-pdf` | - | Guardar PDF original |
| `--limit` | 0 | Límite de documentos (0 = todos) |

### Motores de Extracción (`--pdf-engine`)

| Valor | Comportamiento |
|-------|----------------|
| `auto` | Intenta GRATIS → fallback a vision si falla |
| `free` | Solo modelos GRATIS (nunca consume visión) |
| `vision-chunks` | Usa Vision directo (columnas correctas) |

### Ejemplo

```bash
python cli.py transparency \
    --municipality "Carlos Tejedor" \
    --category balances \
    --pdf-engine auto \
    --skip-large-pdfs \
    --keep-pdf
```

---

## 📁 Archivos Generados

```
boletines/
└── {MUNICIPIO}/
    ├── .{categoria}_state.json     ← Estado del scraping (tracker único)
    ├── _procesamiento.md            ← Tabla de estado legible
    ├── {municipio}_{categoria}_{timestamp}_{hash}.json  ← Datos extraídos
    └── pdfs/                        ← PDFs originales (si --save-pdfs)
        ├── Balance_2025-T1_abc123.pdf
        └── ...
```

### Estado del Scraping (`.categoria_state.json`)

```json
{
  "municipio": "Carlos Tejedor",
  "categoria": "balances",
  "updated_at": "2026-02-02T19:30:00",
  "stats": {
    "total": 102,
    "processed": 88,
    "pending": 0,
    "errors": 0,
    "skipped": 14
  },
  "files": {
    "abc123...": {
      "url": "https://...",
      "status": "processed",
      "pdf_path": "pdfs/Balance_2025-T1_abc123.pdf",
      "json_path": "Carlos_Tejedor_..._abc123.json",
      "processed_at": "2026-02-02T19:10:23"
    }
  }
}
```

### Tabla de Procesamiento (`_procesamiento.md`)

| Archivo | Estado | Fecha | PDF | JSON | Errores |
|---------|--------|-------|-----|------|---------|
| Balance_2025-T1.pdf | ✅ processed | 2026-02-02 19:10 | ✅ | ✅ | - |
| Balance_2024-T4.pdf | ⊘ skipped | - | ❌ | ❌ | PDF grande (180 pág) |

---

## 📝 Ejemplos Prácticos

### Escenario 1: Primer scraping de un municipio

```bash
python cli.py scrape "Carlos Tejedor" balances
```

**Resultado:**
- Descarga todos los PDFs de balances
- Guarda PDFs en `boletines/Carlos_Tejedor/pdfs/`
- Extrae contenido y crea JSONs
- Genera `_procesamiento.md`

### Escenario 2: Retomar scraping interrumpido

```bash
python cli.py scrape "Carlos Tejedor" balances --resume
```

**Resultado:**
- Lee `.balances_state.json`
- Salta PDFs ya procesados
- Continúa desde donde se quedó

### Escenario 3: Auditar manualmente los PDFs

```bash
python cli.py scrape "Carlos Tejedor" balances --save-pdfs
```

**Luego revisar:**
```bash
# Ver PDFs descargados
ls boletines/Carlos_Tejedor/pdfs/

# Ver tabla de procesamiento
cat boletines/Carlos_Tejedor/_procesamiento.md

# Ver JSON de algún PDF
cat boletines/Carlos_Tejedor/Carlos_Tejedor_balances_*.json | jq '.contenido'
```

### Escenario 4: Procesar PDFs grandes con columnas correctas

```bash
python cli.py transparency \
    --municipality "Carlos Tejedor" \
    --category balances \
    --pdf-engine vision-chunks \
    --keep-pdf
```

**Resultado:**
- Usa Vision API directamente (más costoso)
- Columnas se mantienen en orden correcto
- PDFs guardados para verificación

---

## 🔧 Troubleshooting

### Error: "CRÉDITOS AGOTADOS"

**Causa:** Se alcanzó el límite de créditos de OpenRouter

**Solución:**
1. Agrega créditos a tu cuenta de OpenRouter
2. El progreso se guardó automáticamente en `.categoria_state.json`
3. Vuelve a ejecutar con `--resume`

```bash
python cli.py scrape "Carlos Tejedor" balances --resume
```

### Error: "No se encontraron URLs"

**Causa:** El municipio/categoría no está en `sources_user.yaml`

**Solución:** Agrega las URLs al archivo `sources_user.yaml`:

```yaml
Carlos_Tejedor:
  balances:
    - https://carlostejedor.gob.ar/wp-content/uploads/simple-file-list/Balance-1o-2022.pdf
    - ...
```

### PDFs con columnas alteradas

**Causa:** El motor `pdf-text` puede alterar el orden de columnas

**Solución:** Procesar ese PDF específico con vision-chunks:

```bash
python cli.py transparency \
    --url "https://url-del-pdf.pdf" \
    --municipality "Carlos Tejedor" \
    --pdf-engine vision-chunks \
    --keep-pdf
```

### Ver estado del procesamiento

```bash
# Ver tabla de procesamiento
cat boletines/Carlos_Tejedor/_procesamiento.md

# Ver estado JSON
cat boletines/Carlos_Tejedor/.balances_state.json | jq '.stats'

# Usar comando status
python cli.py status --municipality "Carlos Tejedor"
```

---

## 🎯 Recomendaciones

| Situación | Comando |
|-----------|---------|
| **Uso normal** | `python cli.py scrape "Municipio" categoria` |
| **Retomar** | `python cli.py scrape ... --resume` |
| **Prueba** | `python cli.py scrape ... --test --limit 3` |
| **Columnas correctas** | `python cli.py transparency ... --pdf-engine vision-chunks` |
| **Ver estado** | `python cli.py status --municipality "Municipio"` |

---

## 📊 Comparativa de Comandos

| Característica | `scrape` | `transparency` |
|----------------|----------|----------------|
| **Simplicidad** | ✅ 2 argumentos | ⚠️ 2 argumentos requeridos + 10+ opciones |
| **Guarda PDFs** | ✅ Por defecto | ❌ Requiere `--keep-pdf` |
| **Resume** | ✅ `--resume` | ⚠️ Requiere leer código |
| **Modo test** | ✅ `--test` | ⚠️ Requiere `--test-dir` |
| **Control motor** | ❌ Fijo a auto | ✅ `--pdf-engine` |
| **URL individual** | ❌ No | ✅ `--url` |
| **Recomendado para** | Uso diario | Casos avanzados |

---

## 🆕 Novedades v5.0

- ✨ **Nuevo comando `scrape`** - Más simple e intuitivo
- ✨ **StateTracker unificado** - Un solo archivo de estado
- ✨ **Barras de progreso visibles** - Feedback en tiempo real
- ✨ **PDFs guardados por defecto** - Para auditoría manual
- ✨ **Modo resume automático** - Detecta ya procesados
