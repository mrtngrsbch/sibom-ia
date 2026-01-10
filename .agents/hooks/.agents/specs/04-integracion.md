# 04 Integracion

## ⚠️ ARCHIVO AUTO-GENERADO

**Este archivo es una REFERENCIA a la documentación técnica completa.**

NO EDITAR ESTE ARCHIVO DIRECTAMENTE.

Para cambios, editar: `../../.kiro/specs/04-integracion.md`

Luego ejecutar: `python .agents/hooks/sync_from_kiro.py`

---

## 📋 Resumen

## Información General
**Proyecto:** SIBOM Scraper Assistant - Integración de Sistemas  
**Componentes:** Backend Python CLI + Frontend Next.js  
**Propósito:** Análisis de la comunicación, flujo de datos y arquitectura híbrida  
**Patrón:** Producer-Consumer con almacenamiento JSON intermedio  
## Arquitectura de Integración
### Modelo de Comunicación
```mermaid
graph TD
    A[Backend Python CLI] --> B[Archivos JSON]
    B --> C[Frontend Next.js]
    A1[Scraper SIBOM] --> A2[Extracción LLM]
    A2 --> A3[Generación JSON]
    A3 --> B1[boletines_index.json]
    A3 --> B2[boletines/*.json]


## 🔗 Documentación Técnica Completa

**Ver archivo completo:** `../../.kiro/specs/04-integracion.md`

**Ubicación:** `.kiro/specs/04-integracion.md`

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

**Generado:** 2026-01-09 13:38:22
**Fuente:** Análisis de Kiro
