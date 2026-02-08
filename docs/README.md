> ⚠️ NOTA (2026-02-06): Este doc puede tener refs desactualizadas. Stack actual: Gemini 3 Flash + GLM 4.7, Qdrant. Ver `.agents/README.md`

# Documentación SIBOM Scraper Assistant

> **Última actualización:** 2026-02-07
> **Stack:** Gemini 3 Flash + GLM 4.7 | Qdrant | Next.js 16.1 | Python 3.13

---

## 📂 Estructura

```
docs/
├── 01-architecture/         ← Arquitectura y diseño
├── 02-deployment/           ← Deployment (Vercel, R2, Docker)
├── 03-features/             ← Features implementadas (Vector, SQL, BM25, Satélite)
├── 04-changelogs/           ← Historial de cambios
├── 05-issues/               ← Bugs y fixes documentados
├── 06-reference/            ← Factory, migraciones
├── 07-deployment-sat/      ← Deployment satelital (Nginx, Docker, scripts)
├── archive/                 ← Docs históricos (specs originales, experiments)
│   ├── planning/            ← Propuestas y planes viejos
│   ├── specs-originales/    ← Specs v1 con contradicciones (ChromaDB, etc.)
│   ├── experiments/         ← Features experimentales (clima widget)
│   ├── auditorias/          ← Code reviews viejos
│   └── changelogs-root/     ← Changelogs que estaban en root
├── Municipios_contenidos.md ← Datos de municipios
└── README.md                ← Este archivo
```

---

## 📚 Contenido

### 01-architecture/
| Archivo | Contenido |
|---|---|
| `arquitectura-sistema.md` | Propuesta Function Calling (LLM + Tools) |
| `analisis-solucion.md` | Análisis crítico de soluciones |
| `analisis-stack.md` | Stack tecnológico actual |

### 02-deployment/
| Archivo | Contenido |
|---|---|
| `quickstart.md` | Setup rápido |
| `guia-completa.md` | Deployment completo (Vercel + R2) |
| `entornos.md` | Dev vs producción |
| `troubleshooting.md` | Problemas comunes |

### 03-features/
| Archivo | Contenido |
|---|---|
| `vector-search.md` | Qdrant + embeddings |
| `sql-retriever.md` | SQLite para queries |
| `semantic-search.md` | Búsqueda semántica mejorada |
| `embeddings-comparacion.md` | OpenAI vs Cohere |
| `satellite-analysis.md` | Análisis satelital completo |
| `image-gallery.md` | Galería de imágenes con miniaturas |

### 07-deployment-sat/
| Archivo | Contenido |
|---|---|
| `nginx-proxy.md` | Configuración Nginx para proxy /api/analyze y /images/ |
| `docker-compose.md` | Docker-compose con sat-analysis service |
| `dev-script.md` | Script de desarrollo local (scripts/dev.sh) |

### archive/
Documentos históricos movidos el 2026-02-06. Contienen información posiblemente desactualizada (referencias a ChromaDB, OpenRouter como LLM directo, pgvector). **Consultar `.agents/README.md` para el stack actual.**

---

## 🔗 Docs Relacionados

| Recurso | Path |
|---|---|
| **Punto de entrada AI/LLM** | `.agents/README.md` |
| **Roadmap** | `.agents/ROADMAP.md` |
| **Plans (análisis recientes)** | `plans/` |
| **Chatbot README** | `chatbot/README.md` |
| **Scraper CLI README** | `python-cli/README.md` |
| **Sat-Analysis README** | `sat-analysis/README.md` |

---

## ⚡ Stack Real (fuente: .agents/README.md)

| Componente | Tecnología |
|---|---|
| LLM principal | Gemini 3 Flash |
| LLM alternativo | GLM 4.7 |
| Vector DB | Qdrant |
| Embeddings | text-embedding-3-small |
| Frontend | Next.js 16.1 + React 19 |
| Backend | Python 3.13 + BeautifulSoup |
| Sat-Analysis | FastAPI + Sentinel-2 + STAC |
| Storage | Cloudflare R2 |
| Deploy | Vercel (frontend), Dokploy/VPS (backend) |
