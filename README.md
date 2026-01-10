# SIBOM IA

Ecosistema completo para extracción y consulta de boletines oficiales municipales de SIBOM (Sistema Integrado de Boletines Oficiales Municipales de la Provincia de Buenos Aires).

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
- **Tecnologías**: Next.js 15, React 19, TypeScript, Tailwind, Vercel AI SDK
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
npm install
cp .env.example .env.local
# Edita .env.local con tu OPENROUTER_API_KEY
npm run dev
# Abre http://localhost:3000
```

**El chatbot leerá automáticamente los boletines extraídos** en `python-cli/boletines/`

## 📂 Estructura del Proyecto

```
sibom-scraper-assistant/
├── python-cli/               # Backend: Scraper Python
│   ├── sibom_scraper.py     # Script principal del scraper
│   ├── boletines/           # Boletines extraídos (JSON)
│   │   └── csv/             # Herramientas JSON→CSV
│   ├── README.md            # Documentación backend
│   ├── MODELOS.md           # Guía de modelos LLM
│   ├── EJEMPLOS_USO.md      # Ejemplos de uso
│   └── CHANGELOG.md         # Historial de cambios
├── chatbot/                  # Frontend: Chatbot Next.js
│   ├── src/
│   │   ├── app/             # App Router Next.js 15
│   │   ├── components/      # UI components (Chat, Sidebar)
│   │   └── lib/rag/         # Motor RAG (BM25 + embeddings)
│   ├── README.md            # Documentación frontend
│   └── package.json         # Dependencias React/Next
├── .agents/                  # Arquitectura de agentes (agnóstica)
└── README.md                 # Este archivo
```

## 🔗 Documentación

### Backend (Scraper)
- **[README Backend](python-cli/README.md)** - Instalación y uso del scraper
- **[Guía de Modelos](python-cli/MODELOS.md)** - Comparación de modelos LLM (costos, calidad)
- **[Ejemplos de Uso](python-cli/EJEMPLOS_USO.md)** - Casos prácticos y comandos
- **[JSON to CSV](python-cli/boletines/csv/JSON2CSV.md)** - Conversión de datos a CSV

### Frontend (Chatbot)
- **[README Chatbot](chatbot/README.md)** - Instalación y configuración del chatbot
- **[API Endpoints](chatbot/README.md#api)** - Documentación de la API REST

### General
- **[Historia de Migración](MIGRACION.md)** - Migración de React a Python
- **[.agents/](.agents/)** - Arquitectura de agentes del proyecto

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
