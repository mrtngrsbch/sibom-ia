# Especificaciones Técnicas

**Este directorio contiene REFERENCIAS a la documentación técnica completa.**

## 📚 Documentación Completa en `.kiro/`

Para análisis técnico profundo, consulta:

```
.kiro/specs/
├── 01-proyecto-overview.md      # Arquitectura general del proyecto
├── 02-backend-architecture.md   # Backend Python (scraper, procesamiento)
├── 03-frontend-architecture.md  # Frontend Next.js (chatbot, RAG)
├── 04-integracion.md            # Integración entre componentes
├── 05-data-pipeline.md          # Pipeline completo de datos
└── 06-llm-integration.md        # Integración con LLMs (OpenRouter)
```

## 🎯 Cuándo Consultar `.kiro/`

### Consulta `.kiro/specs/` cuando necesites:

- **Detalles técnicos profundos** sobre implementación
- **Ejemplos de código real** del proyecto
- **Diagramas de arquitectura** detallados
- **Decisiones de diseño** y sus justificaciones
- **Patrones específicos** usados en el código

### NO consultes `.kiro/specs/` para:

- **Definir nuevos agentes** → Usa `.agents/agents/`
- **Reglas de código** → Usa `.agents/steering/`
- **Prompts** → Usa `.agents/prompts/`
- **Coordinación** → Usa `.agents/README.md`

## 🔄 Sincronización

`.kiro/specs/` es generado por Kiro y se sincroniza a `.agents/specs/`:

```bash
# Después de que Kiro analice el proyecto
python .agents/hooks/sync_from_kiro.py

# Verifica sincronización
python .agents/hooks/sync_status.py
```

## 📖 Guía Rápida de Navegación

| Quiero saber sobre... | Leo este archivo |
|----------------------|------------------|
| Arquitectura general | `.kiro/specs/01-proyecto-overview.md` |
| Scraper Python | `.kiro/specs/02-backend-architecture.md` |
| Chatbot Next.js | `.kiro/specs/03-frontend-architecture.md` |
| Integración R2/Qdrant | `.kiro/specs/04-integracion.md` |
| Flujo de datos | `.kiro/specs/05-data-pipeline.md` |
| LLM/OpenRouter | `.kiro/specs/06-llm-integration.md` |

## 🚀 Workflow Recomendado

```bash
# 1. Leer .agents/README.md primero (contexto general)
cat .agents/README.md

# 2. Si necesitas detalles técnicos, consulta .kiro/
cat .kiro/specs/01-proyecto-overview.md

# 3. Para implementar, sigue .agents/steering/
cat .agents/steering/python-patterns.md
```

---

**Recuerda:** `.agents/` define QUÉ hacer, `.kiro/` explica CÓMO está hecho.
