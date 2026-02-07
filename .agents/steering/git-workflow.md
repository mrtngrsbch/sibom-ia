# Git Workflow — Manual de Uso
<!-- Creado: 2025-01-16 | Modificado: 2026-02-06 -->

## QUICKSTART

### ¿Qué hace este archivo?
Define las reglas de commits para tu proyecto.

### Formato de commits (Conventional Commits)
```
type(scope): subject
```

**Ejemplos:**
- `feat(chatbot): add vector search`
- `fix(scraper): handle rate limit`
- `docs(agents): add commit-agent`

### Comandos rápidos
```bash
# Analizar cambios
commit-agent analyze

# Ver sugerencias de mensajes
commit-agent suggest

# Commit con opción 1
commit-agent commit --option 1

# Ver estadísticas
commit-agent stats

# Iniciar monitor (cada 30 min)
commit-agent monitor --interval 30
```

### Umbrales de alerta
- **>5 archivos**: Alerta
- **>300 líneas**: Alerta
- **>4 horas desde último commit**: Sugerir commit

---

## 📋 FORMATO CONVENTIONAL COMMITS

### Tipos (Types)

| Tipo | Cuándo usar | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(chatbot): add vector search` |
| `fix` | Corrección de bug | `fix(scraper): handle rate limit` |
| `docs` | Documentación | `docs(agents): add commit-agent` |
| `refactor` | Refactorización | `refactor(rag): improve performance` |
| `test` | Tests | `test(api): add integration tests` |
| `chore` | Mantenimiento | `chore(deps): upgrade dependencies` |

### Scopes

| Scope | Directorio | Ejemplo |
|-------|-----------|---------|
| `chatbot` | `chatbot/` | `feat(chatbot): ...` |
| `scraper` | `python-cli/` | `fix(scraper): ...` |
| `agents` | `.agents/` | `docs(agents): ...` |
| `docs` | `*.md`, `.docs/` | `docs(docs): ...` |
| `ci` | `.github/`, `.husky/` | `chore(ci): ...` |
| `(ninguno)` | Múltiples | `feat: ...` |

### Formato del subject
- **Largo:** 50-72 caracteres
- **Mayúsculas:** Primera letra minúscula
- **Punto:** NO al final

**✅ Correcto:**
```
feat(chatbot): add vector search
fix(scraper): handle rate limit errors
```

**❌ Incorrecto:**
```
Add vector search
feat(chatbot): Add vector search.
feat(chatbot): Add vector search for bulletin queries that improves relevance
```

---

## ⚠️ UMBRALES DE ALERTA

### Niveles de alerta

| Nivel | Archivos | Líneas | Tiempo | Acción |
|-------|----------|--------|--------|--------|
| INFO | 3-5 | 100-300 | 1-2h | Mostrar stats |
| WARNING | 5-10 | 300-500 | 2-4h | Sugerir commit |
| CRITICAL | 10-20 | 500-1000 | 4-8h | Generar mensaje |
| EMERGENCY | >20 | >1000 | >8h | Alertar fuerte |

### Comportamiento

- **<3 archivos:** Sin alerta
- **3-5 archivos:** Stats en `git status`
- **>5 archivos:** Alerta + sugerencias
- **>10 archivos:** 3 opciones de mensajes
- **>20 archivos:** Recomendar dividir

---

## 🌳 BRANCH NAMING

### Formato
```
type/short-description
```

### Ejemplos
- `feature/vector-search`
- `fix/rate-limit-error`
- `docs/commit-workflow`
- `refactor/rag-indexer`

---

## 🔄 PR WORKFLOW

### 1. Crear branch
```bash
git checkout -b feature/vector-search
```

### 2. Hacer commits
```bash
# Hacer cambios
vim chatbot/src/lib/api.ts

# Analizar
commit-agent analyze

# Commit
commit-agent commit --option 1
```

### 3. Push y crear PR
```bash
git push -u origin feature/vector-search

gh pr create \
  --title "feat(chatbot): add vector search" \
  --body "## Summary
- Add vector search using Qdrant
- Implement relevance scoring

## Changes
- chatbot/src/lib/api.ts (new)
- chatbot/src/lib/types.ts (modified)"
```

### 4. Auto-review
En el PR, agregá:
```
@droid please review
```

---

## 📚 EJEMPLOS REALES

### ✅ Commits Correctos

```
feat(chatbot): add vector search for bulletin queries

- Implement vector search using Qdrant
- Add relevance scoring with threshold 0.75
- Fallback to keyword search if no results

fix(scraper): handle rate limit errors gracefully

- Implement retry logic with exponential backoff
- Add rate limit detection from headers
- Improve error logging

docs(agents): add commit-agent to architecture

- Create commit-agent.yaml definition
- Add git-workflow.md steering rules
- Document commit workflow

refactor(rag): improve embedding batch processing

- Optimize batch size from 50 to 100
- Reduce API calls by 50%
- Improve memory usage

test(api): add integration tests for chat endpoint

- Test vector search queries
- Test keyword search fallback
- Test error handling

chore(deps): upgrade Next.js to 16.1.1

- Update next from 16.0.0 to 16.1.1
- Update peer dependencies
```

### ❌ Commits Incorrectos (NO usar)

```
reparo docs
basura
fix error
update files
WIP
commit message
arreglo
```

---

## 🔧 COMANDOS DEL AGENTE

### Comandos principales

```bash
# Analizar cambios actuales
commit-agent analyze

# Generar 3 opciones de mensajes
commit-agent suggest

# Commit con opción específica
commit-agent commit --option 1

# Ver alertas recientes
commit-agent alerts

# Ver estadísticas
commit-agent stats

# Iniciar monitor en background
commit-agent monitor --interval 30

# Detener monitor
commit-agent monitor --stop

# Ver versión
commit-agent --version

# Ver ayuda
commit-agent --help
```

### Git Aliases

```bash
git ca      # commit-agent analyze
git cs      # commit-agent suggest
git cc      # commit-agent commit
git calerts # commit-agent alerts
git cstats  # commit-agent stats
```

---

## ✅ VALIDACIÓN AUTOMÁTICA

### Pre-commit Hook

El hook `.husky/pre-commit` valida automáticamente:
- ✅ Formato Conventional Commits
- ✅ Tipo permitido (feat/fix/docs/refactor/test/chore)
- ✅ Scope válido (chatbot/scraper/agents/docs/ci)
- ✅ Subject dentro del límite de caracteres

**Si el mensaje no cumple:**
```
❌ ERROR: Invalid commit message format

Expected: type(scope): subject

Examples:
  feat(chatbot): add vector search
  fix(scraper): handle rate limit
  docs(agents): add commit-agent

Use --no-verify to bypass (not recommended)
```

---

## 📖 REFERENCIAS

- [Conventional Commits](https://www.conventionalcommits.org/)
- [`.agents/README.md`](../README.md) - Arquitectura de agentes
- [`.agents/agents/commit-agent.yaml`](agents/commit-agent.yaml) - Definición del agente
- [`.agents/workflows/commit-workflow.md`](workflows/commit-workflow.md) - Cómo usar el agente
