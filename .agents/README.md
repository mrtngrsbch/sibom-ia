# .agents/ — SIBOM Scraper Assistant

> **Versión:** 3.0 | **Fecha:** 2026-02-06 | **Autor:** Martín Grinberg

## ¿Qué es este proyecto?

Plataforma de transparencia legislativa para los **135 municipios** de la Provincia de Buenos Aires.
Permite buscar, analizar y comparar ordenanzas, decretos y resoluciones municipales mediante un chatbot RAG
y un módulo de análisis satelital de parcelas agrícolas.

**Problema:** Opacidad en el cobro de tasas municipales (caminos rurales, exenciones, lotes improductivos).
**Solución:** Chatbot legal + análisis satelital, modelo freemium SaaS.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| **Frontend** | Next.js 16.1, React 19, TypeScript, Tailwind CSS, Radix UI |
| **Backend** | Python 3.13, FastAPI (futuro), BeautifulSoup |
| **LLMs** | **Gemini 3 Flash** (principal), **GLM 4.7** (alternativo) |
| **Vector DB** | Qdrant |
| **Storage** | Cloudflare R2 |
| **Deploy** | Vercel (frontend), Dokploy/VPS (backend) |
| **Runtime** | pnpm + Node.js (frontend), Python 3.13 (backend) |

---

## Estructura de .agents/

```
.agents/
├── README.md              ← Este archivo (punto de entrada único)
├── QUICKSTART.md          ← Guía rápida de inicio
├── .gitignore             ← Ignora logs, cache, backups
├── agents/
│   ├── commit-agent.yaml  ← Agente de commits automáticos
│   └── rag-indexer.yaml   ← Agente de indexación RAG
├── prompts/
│   ├── system-prompts.md  ← Personalidad y contexto de cada agente
│   └── task-prompts.md    ← Tareas específicas con inputs/outputs
├── steering/
│   ├── python-patterns.md       ← Patrones Python del proyecto
│   ├── typescript-patterns.md   ← Patrones TypeScript/React
│   ├── error-handling.md        ← Estrategias de manejo de errores
│   ├── testing-patterns.md      ← Patrones de testing
│   ├── performance.md           ← Optimizaciones de rendimiento
│   └── git-workflow.md          ← Reglas de commits y branches
├── scripts/               ← Scripts de automatización
└── hooks/                 ← Git hooks
```

**Principio:** 1 archivo = 1 propósito. 0 redundancia.

---

## Componentes del proyecto

| Componente | Directorio | Estado | Descripción |
|-----------|-----------|--------|-------------|
| **Scraper** | `python-cli/` | ⭐⭐⭐⭐ Funcional | Extrae boletines de SIBOM |
| **Chatbot RAG** | `chatbot/` | ⭐⭐⭐ Con bugs | Búsqueda semántica de normativas |
| **Sat-Analysis** | `sat-analysis/` | ⭐⭐⭐⭐ MVP | Monitoreo satelital de parcelas |

---

## Convenciones

### LLMs
- **Modelo principal:** Gemini 3 Flash (data extraction, búsquedas)
- **Modelo alternativo:** GLM 4.7 (tareas complejas)
- **Embeddings:** text-embedding-3-small

### Idioma
- Código: inglés (variables, funciones, API endpoints)
- Documentación y comentarios: español
- Commits: formato Conventional Commits (inglés)

### Reglas de código
- **TypeScript:** NUNCA usar `any` — tipos explícitos siempre
- **Python:** Clases con dependency injection, retry con backoff exponencial
- **Next.js:** Server Components por defecto, API Routes para backend (NO Server Actions)
- **Logging:** structlog (Python), console con prefijos `[Módulo]` (TypeScript)

---

## Cómo usar esta carpeta

### Para agentes/LLMs
1. Leer este README como punto de entrada
2. Consultar `steering/` para patrones de código del lenguaje relevante
3. Consultar `prompts/` para personalidad y tareas de agentes

### Para desarrolladores
1. Seguir patrones en `steering/` al escribir código
2. Usar formato de commits definido en `steering/git-workflow.md`
3. Respetar modelos LLM configurados (Gemini 3 Flash / GLM 4.7)

---

## Links rápidos

- **Guía rápida:** [`QUICKSTART.md`](QUICKSTART.md)
- **Patrones Python:** [`steering/python-patterns.md`](steering/python-patterns.md)
- **Patrones TypeScript:** [`steering/typescript-patterns.md`](steering/typescript-patterns.md)
- **Git workflow:** [`steering/git-workflow.md`](steering/git-workflow.md)
- **System prompts:** [`prompts/system-prompts.md`](prompts/system-prompts.md)
