# Definiciones de Agentes

Esta carpeta contiene las **definiciones de agentes** en formato YAML/JSON.

## 📋 ¿Qué es un Agente?

Un agente es una **unidad de trabajo autónoma** que:
- Tiene un **objetivo claro** (goal)
- Recibe **entradas definidas** (inputs)
- Produce **salidas específicas** (outputs)
- Respeta **restricciones** (constraints)
- Usa **herramientas** (tools)

## 🎯 Template de Agente

```yaml
name: nombre-del-agente
version: 1.0.0
description: Descripción breve del agente

goal: |
  Descripción detallada del objetivo del agente.
  Qué problema resuelve y cómo lo hace.

inputs:
  - Fuente de datos 1
  - Fuente de datos 2

outputs:
  - Destino de salida 1
  - Logs/reportes

constraints:
  - Restricción 1 (ej: no modificar X)
  - Restricción 2 (ej: respetar rate limits)
  - Restricción 3 (ej: solo lectura)

tools:
  - herramienta-1
  - herramienta-2

runtime:
  language: python  # o typescript, bash, etc.
  version: "3.13"
  entrypoint: ruta/al/script.py

prompts:
  system: ../prompts/system-prompts.md#nombre-agente
  task: ../prompts/task-prompts.md#tarea-especifica

metadata:
  author: tu-nombre
  created: 2025-01-16
  tags: [tag1, tag2, tag3]
```

## 📝 Ejemplos

### Ejemplo 1: RAG Indexer

```yaml
name: rag-indexer
version: 1.0.0
description: Indexa documentos JSON desde R2 a Qdrant

goal: |
  Indexar todos los documentos JSON limpios desde Cloudflare R2
  al vector store Qdrant para búsqueda semántica.

inputs:
  - r2://sibom-cleaned-data/*.json
  - config/qdrant-settings.yaml

outputs:
  - qdrant://sibom-collection
  - logs/indexing-{timestamp}.log

constraints:
  - No scraping (solo lectura de R2)
  - No modificar frontend
  - Respetar rate limits de Qdrant (100 req/s)
  - Usar embeddings de OpenRouter

tools:
  - qdrant-client
  - boto3
  - openrouter-api

runtime:
  language: python
  version: "3.13"
  entrypoint: python-cli/rag_indexer.py

prompts:
  system: ../prompts/system-prompts.md#rag-indexer
  task: ../prompts/task-prompts.md#indexing

metadata:
  author: mrtn
  created: 2025-01-16
  tags: [rag, indexing, qdrant, r2]
```

### Ejemplo 2: Scraper Orchestrator

```yaml
name: scraper-orchestrator
version: 1.0.0
description: Orquesta el scraping de múltiples municipios

goal: |
  Coordinar el scraping paralelo de boletines oficiales
  de múltiples municipios, respetando rate limits y
  manejando errores gracefully.

inputs:
  - config/municipalities.yaml
  - .env (OPENROUTER_API_KEY)

outputs:
  - r2://sibom-raw-bulletins/{municipality}/*.json
  - logs/scraping-{timestamp}.log
  - reports/scraping-summary.csv

constraints:
  - Máximo 3 municipios en paralelo
  - Rate limit: 3 req/s por municipio
  - Timeout: 30s por request
  - Retry: 3 intentos con backoff exponencial

tools:
  - requests
  - beautifulsoup4
  - openrouter-api
  - boto3

runtime:
  language: python
  version: "3.13"
  entrypoint: python-cli/sibom_scraper.py

prompts:
  system: ../prompts/system-prompts.md#scraper-orchestrator
  task: ../prompts/task-prompts.md#scraping

metadata:
  author: mrtn
  created: 2025-01-16
  tags: [scraping, orchestration, parallel]
```

## 🚀 Crear un Nuevo Agente

```bash
# 1. Copiar template
cp .agents/agents/README.md .agents/agents/mi-agente.yaml

# 2. Editar definición
vim .agents/agents/mi-agente.yaml

# 3. Validar sintaxis YAML
python -c "import yaml; yaml.safe_load(open('.agents/agents/mi-agente.yaml'))"

# 4. Commit
git add .agents/agents/mi-agente.yaml
git commit -m "agents: agregar mi-agente"

# 5. OpenCode lo detecta automáticamente
```

## ✅ Checklist de Calidad

Antes de commitear un agente, verifica:

- [ ] Nombre en kebab-case (ej: `rag-indexer`, no `RAGIndexer`)
- [ ] Goal claro y específico
- [ ] Inputs y outputs bien definidos
- [ ] Constraints realistas y verificables
- [ ] Tools listadas correctamente
- [ ] Runtime especificado
- [ ] Prompts referenciados
- [ ] Metadata completa
- [ ] YAML válido (sin errores de sintaxis)

## 📚 Referencias

- [README principal](../README.md) - Manual completo
- [System Prompts](../prompts/system-prompts.md) - Prompts de sistema
- [Task Prompts](../prompts/task-prompts.md) - Prompts de tareas
