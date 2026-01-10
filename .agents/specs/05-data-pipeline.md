# 05 Data Pipeline

## ⚠️ ARCHIVO AUTO-GENERADO

**Este archivo es una REFERENCIA a la documentación técnica completa.**

NO EDITAR ESTE ARCHIVO DIRECTAMENTE.

Para cambios, editar: `.kiro/specs/05-data-pipeline.md`

Luego ejecutar: `python .agents/hooks/sync_from_kiro.py`

---

## 📋 Resumen

## Información General
**Proyecto:** SIBOM Scraper Assistant - Pipeline Completo de Datos  
**Flujo:** Web Scraping → Extracción LLM → JSON Storage → RAG Retrieval → Chat Response  
**Propósito:** Análisis del flujo completo desde la fuente hasta la respuesta al usuario  
**Tecnologías:** Python + OpenRouter + JSON + TypeScript + BM25  
## Arquitectura del Pipeline
### Vista General del Flujo
```mermaid
graph TD
    A[SIBOM Web Pages] --> B[Python Scraper]
    B --> C[OpenRouter LLM]
    C --> D[JSON Files]
    D --> E[Next.js RAG System]
    E --> F[BM25 Indexing]
    F --> G[OpenRouter LLM]


## 🔗 Documentación Técnica Completa

**Ver archivo completo:** `.kiro/specs/05-data-pipeline.md`

**Ubicación:** `.kiro/specs/05-data-pipeline.md`

**Contenido detallado:**
- Análisis técnico profundo
- Ejemplos de código real
- Diagramas y arquitectura
- Patrones y decisiones de diseño


## 🤖 Para Agentes AI

Cuando trabajéis en este proyecto:

1. **LEER** el archivo completo en `.kiro/` para entender el contexto
2. **APLICAR** patrones de `.agents/steering/`
3. **CONSULTAR** este archivo solo como referencia rápida

---

**Generado:** 2026-01-09 13:41:14
**Fuente:** Análisis de Kiro
