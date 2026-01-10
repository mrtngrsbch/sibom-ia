# 06 Llm Integration

## ⚠️ ARCHIVO AUTO-GENERADO

**Este archivo es una REFERENCIA a la documentación técnica completa.**

NO EDITAR ESTE ARCHIVO DIRECTAMENTE.

Para cambios, editar: `.kiro/specs/06-llm-integration.md`

Luego ejecutar: `python .agents/hooks/sync_from_kiro.py`

---

## 📋 Resumen

## Información General
**Proyecto:** SIBOM Scraper Assistant - Integración LLM Unificada  
**Proveedor:** OpenRouter (https://openrouter.ai)  
**Modelos:** Google Gemini + Anthropic Claude  
**Propósito:** Análisis de la estrategia LLM unificada entre backend Python y frontend Next.js  
**Patrón:** Dual-model strategy (económico + premium)  
## Arquitectura LLM
### Vista General de Modelos
```mermaid
graph TD
    A[OpenRouter API] --> B[Backend Python]
    A --> C[Frontend Next.js]
    B --> B1[Gemini 3 Flash Preview]
    B1 --> B2[Data Extraction]
    B2 --> B3[JSON Generation]


## 🔗 Documentación Técnica Completa

**Ver archivo completo:** `.kiro/specs/06-llm-integration.md`

**Ubicación:** `.kiro/specs/06-llm-integration.md`

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
