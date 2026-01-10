# 02 Backend Scraper

## ⚠️ ARCHIVO AUTO-GENERADO

**Este archivo es una REFERENCIA a la documentación técnica completa.**

NO EDITAR ESTE ARCHIVO DIRECTAMENTE.

Para cambios, editar: `../../.kiro/specs/02-backend-scraper.md`

Luego ejecutar: `python .agents/hooks/sync_from_kiro.py`

---

## 📋 Resumen

## Introducción
El backend del SIBOM Scraper es una herramienta CLI en Python que implementa un sistema de extracción de datos de 3 niveles con procesamiento híbrido. Ubicado en `python-cli/`, representa la parte de "extracción" del ecosistema.
## Arquitectura Principal
### Clase Central: SIBOMScraper
**Ubicación**: `python-cli/sibom_scraper.py:32-848`
```python
class SIBOMScraper:
    def __init__(self, api_key: str, model: str = "z-ai/glm-4.5-air:free"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self.rate_limit_delay = 3  # segundos entre llamadas
        self.last_call_time = 0


## 🔗 Documentación Técnica Completa

**Ver archivo completo:** `../../.kiro/specs/02-backend-scraper.md`

**Ubicación:** `.kiro/specs/02-backend-scraper.md`

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
