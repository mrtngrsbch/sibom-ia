# Mangrullo

> *Observatorio independiente de la decepción municipal*

> **Estado Actual**: 🟢 Producción - 2026-02-10 (v3.1)

---

Ecosistema completo para extracción y consulta de boletines oficiales municipales de Mangrullo (Sistema Integrado de Boletines Oficiales Municipales de la Provincia de Buenos Aires).

## 🏗️ Arquitectura del Proyecto

Este es un ecosistema de **dos partes integradas**:

### 1. Backend Python 🐍
Scraper automatizado que extrae boletines usando LLMs
- **Ubicación**: [`python-cli/`](python-cli/)
- **Función**: Extrae, estructura y exporta boletines municipales
- **Tecnologías**: Python, OpenRouter, LLMs (Gemini, GLM, Grok)
- **Salida**: JSON estructurados + CSV para análisis

### 2. Frontend Next.js 💬
Chatbot con RAG para consultar los boletines extraídos
- **Ubicación**: [`chatbot/`](chatbot/)
- **Función**: Búsqueda semántica y consultas en lenguaje natural
- **Tecnologías**: Next.js 16, React 19, TypeScript, Tailwind, Vercel AI SDK, pnpm (package manager)
- **Características**: BM25, embeddings, streaming en tiempo real

## 🚀 Inicio Rápido

### Paso 1: Extraer Boletines (Backend)

```bash
cd python-cli
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edita .env y agrega tu OPENROUTER_API_KEY
python3 sibom_scraper.py --limit 5
```

### Paso 2: Consultar Boletines (Frontend)

```bash
cd chatbot
pnpm install              # O: npm install
cp .env.example .env.local
# Edita .env.local con tu OPENROUTER_API_KEY
pnpm run dev              # O: npm run dev
# Abre http://localhost:3000
```

> **Nota:** El proyecto usa **pnpm** como gestor de paquetes (más eficiente que npm).

**El chatbot leerá automáticamente los boletines extraídos** en `python-cli/boletines/`

## 📊 Estado Actual del Proyecto

**Fecha de Recomenzo**: 2026-01-14

### Datos Actuales
- **Archivos JSON**: 1,677 boletines individuales
- **Tamaño local**: 662MB (6.8M líneas de código)
- **DB SQLite**: 47MB (216K+ normativas indexadas)
- **Proyección producción**: ~4GB / ~3,000 archivos

### Arquitectura de Producción
```
┌─────────────────────────────────────────────────────────────┐
│                    PYTHON CLI (Backend)                      │
├─────────────────────────────────────────────────────────────┤
│  Scraper → Indices (6 tipos) → SQLite (agregaciones)       │
│  - BM25 (keyword search)                                      │
│  - Qdrant (vector search con embeddings)                     │
│  - SQLite (COUNT, SUM, AVG rápidos)                        │
│  - Cache multi-nivel (file, index, Vercel)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              CLOUDFLARE R2 (Storage + CDN)                    │
├─────────────────────────────────────────────────────────────┤
│  - Boletines JSON (gzip comprimido ~80% menos bandwidth)    │
│  - Índices JSON (minimal, compact, completo)                 │
│  - Caching agresivo (Vercel cache 3600s)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 NEXT.JS CHATBOT (Frontend)                    │
├─────────────────────────────────────────────────────────────┤
│  - BM25: Keywords exactas (números, nombres)                │
│  - Vector Search: Sinónimos ("sueldo" → "remuneración")      │
│  - SQL: Agregaciones rápidas (municipio con más normas)     │
│  - Streaming: Respuestas en tiempo real                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 VERCEL (Deployment)                          │
├─────────────────────────────────────────────────────────────┤
│  - Zero-downtime deployments                                  │
│  - Preview environments para testing                         │
│  - Logs y analytics completos                               │
└─────────────────────────────────────────────────────────────┘
```

### Motores de Búsqueda (Implementados)
1. **BM25 (Keyword Search)**: Para búsquedas exactas
   - Número de norma: "ordenanza 2947"
   - Listados por tipo: "decretos de Carlos Tejedor"
   - Filtrado por fechas y municipios

2. **Vector Search (Qdrant + OpenAI)**: Para búsqueda semántica
   - Sinónimos: "sueldos" encuentra "remuneración", "haberes"
   - Contexto: "tránsito", "salud", "impuestos"
   - Mejor para queries en lenguaje natural

3. **SQLite (sql.js)**: Para agregaciones numéricas
   - Comparaciones: "qué municipio tiene más decretos"
   - Conteos: "cuántas ordenanzas hay en total"
   - Rankings: "municipios con más normativa"

---

## 📂 Estructura del Proyecto

```
sibom-scraper-assistant/
├── python-cli/               # Backend: Scraper Python
│   ├── sibom_scraper.py     # Scraper base (un municipio)
│   ├── sibom_web_scraping.py # Orquestador (todos los municipios)
│   ├── boletines/           # Boletines extraídos (JSON)
│   │   └── normativas.db     # DB SQLite (agregaciones)
│   ├── data/
│   │   ├── indices/         # 6 tipos de índices
│   │   ├── estado/          # Estado del scraping
│   │   └── ejemplos/        # Ejemplos de datos
│   ├── docs/                # Documentación del backend
│   ├── scripts/             # Scripts utilitarios (R2, compresión)
│   ├── tests/               # Tests unitarios
│   └── tui/                 # UI opcional (React + Ink)
├── chatbot/                  # Frontend: Chatbot Next.js
│   ├── src/
│   │   ├── app/             # App Router Next.js 16
│   │   ├── components/      # UI components (Chat, Sidebar)
│   │   └── lib/
│   │       ├── rag/         # Motor RAG (BM25 + Vector + SQL)
│   │       ├── computation/  # Motor de cómputo tabular
│   │       └── data-catalog # Catálogo de datos para LLM
│   └── .env.example         # Variables de entorno
├── docs/                    # Documentación general
│   ├── archive/             # Documentación archivada (historial)
│   └── chatbot/             # Documentación del chatbot
├── .agents/                 # Arquitectura de agentes
└── README.md                # Este archivo
```

## 📂 Documentación

La documentación del proyecto está organizada en [`docs/`](docs/) con la siguiente estructura:

```
docs/
├── README.md                    # Índice de documentación
├── 01-architecture/             # Arquitectura y diseño del sistema
│   ├── arquitectura-sistema.md  # Arquitectura con Function Calling
│   ├── analisis-solucion.md    # Análisis crítico de soluciones
│   └── analisis-stack.md       # Análisis del stack tecnológico
├── 02-deployment/              # Guías de deployment (Vercel, R2)
│   ├── guia-completa.md        # Guía completa de deployment
│   ├── quickstart.md            # Quickstart para deployment rápido
│   ├── entornos.md             # Diferencias dev vs producción
│   └── troubleshooting.md      # Solución de problemas comunes
├── 03-features/               # Features implementadas
│   ├── vector-search.md         # Búsqueda semántica (OpenAI + Qdrant)
│   ├── sql-retriever.md         # Base de datos SQLite para queries rápidas
│   ├── data-catalog.md          # Catálogo de datos para el LLM
│   ├── semantic-search.md        # Búsqueda semántica mejorada
│   └── embeddings-comparacion.md  # Comparación OpenAI vs Cohere
├── 04-changelogs/             # Historial de cambios por fecha
│   ├── 2026-01-optimizaciones.md     # Optimizaciones de tokens y performance
│   ├── 2026-01-refactor-filtros.md    # Refactor de filtros
│   ├── 2026-01-cleanup.md             # Limpieza de código obsoleto
│   ├── session-2026-01-10.md          # Resumen de sesión
│   └── audit-complete.md                # Auditoría completa del código
├── 05-issues/                  # Bugs y fixes documentados
│   ├── massive-listings.md      # Fix para listados >500 resultados
│   ├── comparative-queries.md    # Fix para queries comparativas
│   ├── individual-urls.md       # Fix de URLs individuales
│   └── llm-strategy.md         # Estrategia de uso del LLM (simplificación)
└── 06-reference/               # Referencias y migraciones
    ├── factory-implementation.md # Implementación de droids/skills/hooks
    └── migracion.md            # Migración Gemini → OpenRouter + CLI Python
```

**Documentación relacionada:**
- **[AGENTS.md](AGENTS.md)** - Guía de agentes para AI assistants
- **[python-cli/README.md](python-cli/README.md)** - Documentación del scraper Python
- **[chatbot/README.md](chatbot/README.md)** - Documentación del chatbot Next.js

**Documentación relacionada:**
- **[docs/README.md](docs/README.md)** - Índice completo de documentación organizada
- **[AGENTS.md](AGENTS.md)** - Guía de agentes para AI assistants (arquitectura del proyecto)
- **[python-cli/README.md](python-cli/README.md)** - Documentación del scraper Python
- **[chatbot/README.md](chatbot/README.md)** - Documentación del chatbot Next.js

---

## 🎯 Características

### Backend (Scraper)
- ✅ Extracción automatizada usando LLM (OpenRouter)
- ✅ Soporte para múltiples modelos (Gemini, Grok, GLM) con opción **GRATIS**
- ✅ Procesamiento paralelo de múltiples boletines
- ✅ Sistema de 3 niveles: Listado → Enlaces → Texto completo
- ✅ Conversión a CSV para análisis de datos
- ✅ Índice markdown automático con tracking de estado
- ✅ Modo automático con `--skip-existing`

### Frontend (Chatbot)
- ✅ Búsqueda semántica con BM25 y embeddings
- ✅ Streaming de respuestas en tiempo real
- ✅ Soporte para múltiples municipios
- ✅ Fuentes citadas (referencias a boletines)
- ✅ Interfaz responsive con Tailwind CSS
- ✅ RAG (Retrieval Augmented Generation) para respuestas precisas

## 💰 Modelos Gratuitos Disponibles

### Para el Backend (Scraper)
```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free
```
**100% gratis, sin límites**, sin necesidad de créditos en OpenRouter.

### Para el Frontend (Chatbot)

En `chatbot/.env.local`:
```env
OPENROUTER_MODEL=z-ai/glm-4.5-air:free
```

Modelos gratuitos recomendados:
- `z-ai/glm-4.5-air:free` - Gratis, buena calidad
- `google/gemini-2.5-flash-lite` - Muy bajo costo, excelente calidad

## 🤝 Contribuciones

Este es un proyecto educativo para demostrar:
- Uso de LLMs en extracción de datos estructurados desde HTML
- Implementación de RAG para búsqueda semántica
- Integración backend Python con frontend Next.js
- Arquitectura de agentes AI-agnostic con `.agents/`

## 📄 Flujo de Trabajo Completo

```
1. Scraping (Backend)          → Boletines extraídos en JSON
2. Indexado (Automático)       → Boletines listos para consulta
3. Consulta (Frontend)         → Usuario pregunta en lenguaje natural
4. RAG (Chatbot)              → Búsqueda semántica + generación de respuesta
5. Respuesta (Streaming)      → Respuesta con fuentes citadas
```

## 🚀 Deployment a Producción

**Arquitectura en producción:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GitHub    │────▶│   Vercel    │────▶│ Cloudflare  │
│   (Código)  │ auto│   (App)     │     │   R2 (Data) │
└─────────────┘deploy└─────────────┘     └─────────────┘
```

**Guías de deployment:**

- **[DEPLOYMENT_GITHUB.md](DEPLOYMENT_GITHUB.md)** - ⭐ **Recomendado**: Deployment vía GitHub → Vercel
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Checklist completo paso a paso
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guía técnica detallada de R2 y Vercel

**Setup rápido:**
1. Push código a GitHub
2. Conectar Vercel con tu repo
3. Subir datos a Cloudflare R2
4. Configurar variables de entorno en Vercel
5. Deploy automático ✅

---

**¿Por dónde empezar?**
- Si querés extraer boletines → Ir a [python-cli/README.md](python-cli/README.md)
- Si querés consultar boletines → Ir a [chatbot/README.md](chatbot/README.md)
- Si querés deployar a producción → Ver [DEPLOYMENT_GITHUB.md](DEPLOYMENT_GITHUB.md)
- Si querés entender la arquitectura → Ver [`.agents/`](.agents/)

## 📄 Licencia

Proyecto de código abierto. Ver carpeta `python-cli/` para más detalles.
