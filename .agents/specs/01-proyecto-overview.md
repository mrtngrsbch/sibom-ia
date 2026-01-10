# 01 Proyecto Overview

## ⚠️ ARCHIVO AUTO-GENERADO

**Este archivo es una REFERENCIA a la documentación técnica completa.**

NO EDITAR ESTE ARCHIVO DIRECTAMENTE.

Para cambios, editar: `.kiro/specs/01-proyecto-overview.md`

Luego ejecutar: `python .agents/hooks/sync_from_kiro.py`

---

## 📋 Resumen

## Introducción
El **SIBOM Scraper Assistant** es un ecosistema completo de dos partes integradas para la extracción y consulta inteligente de boletines oficiales municipales de la Provincia de Buenos Aires, Argentina. El proyecto demuestra una arquitectura moderna que combina web scraping automatizado con IA conversacional.
## Arquitectura del Ecosistema
### Visión General
```mermaid
graph TB
    A[SIBOM Web Portal] --> B[Backend Python CLI]
    B --> C[JSON Estructurados]
    C --> D[Frontend Next.js Chatbot]
    D --> E[Usuario Final]
    B --> F[CSV Export]
    B --> G[Markdown Index]
    subgraph "Backend: Extracción"
        B
        H[OpenRouter LLM]


## 🔗 Documentación Técnica Completa

**Ver archivo completo:** `.kiro/specs/01-proyecto-overview.md`

**Ubicación:** `.kiro/specs/01-proyecto-overview.md`

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
