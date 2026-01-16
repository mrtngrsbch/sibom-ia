# Commit Agent - Implementación Completa

## ✅ LO QUE SE HA IMPLEMENTADO

### Archivos Creados (6 archivos)

1. **`.agents/agents/commit-agent.yaml`**
   - Definición del agente siguiendo el estándar de `.agents/`
   - Umbrales conservadores: WARNING (>5 archivos), CRITICAL (>10 archivos)
   - Integración con prompts del sistema

2. **`.agents/steering/git-workflow.md`**
   - Reglas de Conventional Commits
   - Formato: `type(scope): subject`
   - Tipos: feat, fix, docs, refactor, test, chore
   - Scopes: chatbot, scraper, agents, docs, ci
   - Ejemplos reales del proyecto

3. **`.agents/workflows/commit-workflow.md`**
   - Guía paso a paso de uso
   - 6 flujos completos:
     1. Commit Normal
     2. Commit Grande
     3. Dividir Commits
     4. Monitor en Background
     5. Ver Alertas
     6. Ver Estadísticas
   - Troubleshooting común

4. **`.agents/scripts/commit_agent.py`**
   - Implementación Python del agente
   - Funcionalidades:
     * Análisis de cambios
     * Categorización por módulo
     * Verificación de umbrales
     * Generación de 3 opciones de mensajes
     * Monitor en background (cada 30 min)
     * Notificaciones nativas de macOS
     * Logs en `.agents/logs/`
   - Comandos: analyze, suggest, commit, alerts, stats, monitor

5. **`.agents/prompts/system-prompts.md`** (MODIFICADO)
   - Agregada sección `commit-agent`
   - Define personalidad y contexto del agente
   - Restricciones y estilo de trabajo

6. **`.agents/prompts/task-prompts.md`** (MODIFICADO)
   - Agregada sección `generate-commit`
   - Pasos detallados para generar mensajes de commit
   - Validaciones y ejemplos

### Directorio Creado

- **`.agents/logs/`** - Para alertas y logs del monitor

---

## 🚀 CÓMO USAR EL AGENTE

### Comandos Básicos

```bash
# Ver versión
python3 .agents/scripts/commit_agent.py --version

# Analizar cambios actuales
python3 .agents/scripts/commit_agent.py analyze

# Ver sugerencias de mensajes
python3 .agents/scripts/commit_agent.py suggest

# Iniciar monitor (cada 30 minutos)
python3 .agents/scripts/commit_agent.py monitor --interval 30

# Ver alertas recientes
python3 .agents/scripts/commit_agent.py alerts

# Ver ayuda
python3 .agents/scripts/commit_agent.py --help
```

### Flujo Típico

```bash
# 1. Hacé cambios
vim chatbot/src/lib/api.ts

# 2. Analizá
python3 .agents/scripts/commit_agent.py analyze

# Output:
# ⚠️  WARNING: Considerá hacer un commit
# 
# 📊 Estadísticas:
#   Archivos: 2
#   Líneas: +45, -12
#   Tiempo desde último commit: 1h 23m
#
# 💡 Sugerencia: Ejecutá 'commit-agent suggest' para ver opciones

# 3. Ver sugerencias
python3 .agents/scripts/commit_agent.py suggest

# Output:
# 📋 Opciones de mensajes de commit:
#
# 1. feat(chatbot): improve vector search
#    - Adjust similarity threshold
#    - Add type narrowing
#
# 2. fix(chatbot): fix search type errors
#    - Fix TypeScript errors
#    - Update interfaces
#
# 3. refactor(chatbot): optimize search logic
#    - Simplify calculation
#    - Improve type safety

# 4. Commiteá con el mensaje que te guste
git commit -m "feat(chatbot): improve vector search
- Adjust similarity threshold from 0.7 to 0.75
- Add type narrowing for better matching"
```

---

## 🔔 NOTIFICACIONES

### En el Chat (OpenCode / Claude Code)

Las alertas se guardan en `.agents/logs/commit-alerts.log`. Para verlas:

```bash
# En el chat, preguntá:
"¿Hay alertas de commits pendientes?"

# O leé el archivo directamente:
cat .agents/logs/commit-alerts.log
```

### Notificaciones Nativas de macOS

El agente puede enviar notificaciones nativas cuando hay WARNING o superior:

```
🔔 Commit Agent: Alerta

⚠️  WARNING: Considerá hacer un commit

Files: 6
Time: 2h 15m

Sugerencia: Ejecutá commit-agent analyze
```

---

## ⚙️ CONFIGURACIÓN

### Umbrales de Alerta (Conservadores)

| Nivel | Archivos | Líneas | Tiempo | Acción |
|-------|----------|--------|--------|--------|
| **INFO** | 3-5 | 100-300 | 1-2h | Mostrar stats |
| **WARNING** | >5 | >300 | >4h | Sugerir commit |
| **CRITICAL** | >10 | >500 | >8h | Generar mensaje |
| **EMERGENCY** | >20 | >1000 | >24h | Alertar fuerte |

### Personalizar Umbrales

Edita `.agents/steering/git-workflow.md` y busca la sección "Umbrales de Alerta".

---

## 📊 FORMATO CONVENTIONAL COMMITS

### Tipo (Type)

| Tipo | Cuándo usar | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(chatbot): add vector search` |
| `fix` | Corrección de bug | `fix(scraper): handle rate limit` |
| `docs` | Documentación | `docs(agents): add commit-agent` |
| `refactor` | Refactorización | `refactor(rag): improve performance` |
| `test` | Tests | `test(api): add integration tests` |
| `chore` | Mantenimiento | `chore(deps): upgrade dependencies` |

### Scope

| Scope | Directorio | Ejemplo |
|-------|-----------|---------|
| `chatbot` | `chatbot/` | `feat(chatbot): ...` |
| `scraper` | `python-cli/` | `fix(scraper): ...` |
| `agents` | `.agents/` | `docs(agents): ...` |
| `docs` | `*.md`, `.docs/` | `docs(docs): ...` |
| `ci` | `.github/`, `.husky/` | `chore(ci): ...` |

### Formato

```
<type>(<scope>): <subject>

<body>
```

**Ejemplo correcto:**
```
feat(chatbot): add vector search for bulletin queries

- Implement vector search using Qdrant
- Add relevance scoring with threshold 0.75
- Fallback to keyword search if no results
```

---

## 🔧 INTEGRACIÓN CON OPENCODE

### ¿Cómo lo usa OpenCode?

1. **Automático**: OpenCode lee `.agents/agents/` al iniciar
2. **Manual**: Puedes preguntar en el chat:
   - "¿Hay alertas de commits pendientes?"
   - "Analiza mis cambios actuales"
   - "Genera un mensaje de commit"

### Compatibilidad

- ✅ OpenCode
- ✅ Claude Code
- ✅ Cualquier runtime compatible con `.agents/`

---

## 📝 COMMITS CREADOS

### Commit Inicial

```
feat(agents): add commit-agent for automated commit messages

- Add commit-agent.yaml definition with Conventional Commits
- Add git-workflow.md steering rules for commit conventions
- Add commit-workflow.md with step-by-step usage guide
- Add commit_agent.py script for analyzing changes and generating messages
- Add commit-agent section to system-prompts.md
- Add generate-commit section to task-prompts.md
- Create .agents/logs/ directory for alert logs
- Implement thresholds: WARNING (>5 files), CRITICAL (>10 files)
- Support monitor in background (every 30 minutes)
- Compatible with OpenCode and Claude Code
```

---

## 🎯 BENEFICIOS

### Después de Usar el Agente

✅ **Menos commits grandes** (>20 archivos)
✅ **Mensajes más descriptivos** (Conventional Commits)
✅ **Historial más limpio** de git
✅ **Deshacer cambios más fácil**
✅ **Alertas proactivas** (cada 30 min)
✅ **Integrado con tu arquitectura** (`.agents/`)
✅ **Sin nuevas carpetas** (usa estructura existente)

### Commits que NO vas a tener

❌ "reparo docs"
❌ "basura"
❌ "fix error"
❌ "update files"

### Commits que SÍ vas a tener

✅ "feat(chatbot): add vector search for bulletin queries"
✅ "fix(scraper): handle rate limit errors gracefully"
✅ "docs(agents): add commit-agent documentation"
✅ "refactor(rag): improve embedding batch processing"

---

## 📚 DOCUMENTACIÓN

### Archivos Principales

1. **[`.agents/agents/commit-agent.yaml`](agents/commit-agent.yaml)** - Definición del agente
2. **[`.agents/steering/git-workflow.md`](steering/git-workflow.md)** - Reglas de commits (START AQUÍ)
3. **[`.agents/workflows/commit-workflow.md`](workflows/commit-workflow.md)** - Guía paso a paso
4. **[`.agents/README.md`](README.md)** - Arquitectura de agentes (actualizado)

### Prompts

5. **[`.agents/prompts/system-prompts.md`](prompts/system-prompts.md)** - Sección `commit-agent`
6. **[`.agents/prompts/task-prompts.md`](prompts/task-prompts.md)** - Sección `generate-commit`

---

## 🆘 TROUBLESHOOTING

### Problema: "commit-agent: command not found"

**Solución:**
```bash
# Usá el path completo
python3 .agents/scripts/commit_agent.py analyze

# O agregá un alias a tu shell
echo "alias commit-agent='python3 $(pwd)/.agents/scripts/commit_agent.py'" >> ~/.zshrc
source ~/.zshrc
```

### Problema: "No se detectan cambios"

**Solución:**
```bash
# Verificá que estás en el directorio correcto
cd /ruta/al/proyecto
pwd

# Ejecutá git status manualmente
git status --short

# Compará con el agente
python3 .agents/scripts/commit_agent.py analyze --debug
```

### Problema: "Monitor no envía alertas"

**Solución:**
```bash
# Verificá que el monitor está corriendo
ps aux | grep commit_agent

# Verificá logs
tail -50 .agents/logs/commit-monitor.log

# Reiniciá monitor
python3 .agents/scripts/commit_agent.py monitor --stop
python3 .agents/scripts/commit_agent.py monitor --interval 30
```

### Problema: "Alertas no aparecen en el chat"

**Solución:**
Las alertas se guardan en `.agents/logs/commit-alerts.log`:

```bash
# Preguntá en el chat
"¿Hay alertas de commits pendientes?"

# O leé el archivo
cat .agents/logs/commit-alerts.log
```

---

## 📈 PRÓXIMOS PASOS (OPCIONALES)

### Mejoras Futuras

1. **Integración con Husky pre-commit**
   - Validar formato de mensajes automáticamente
   - Rechazar commits que no sigan Conventional Commits

2. **GitHub Actions**
   - Validar commits en PRs
   - Bloquear merge si commits son muy grandes

3. **Generación con LLM**
   - Usar OpenRouter para generar mensajes más inteligentes
   - Mejorar detección de tipo y scope

4. **Git Aliases**
   - Agregar aliases para acceso rápido
   - `git ca` → commit-agent analyze
   - `git cs` → commit-agent suggest

5. **Dashboard Web**
   - Visualizar estadísticas de commits
   - Gráficos de frecuencia y tamaño

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [x] Crear `.agents/agents/commit-agent.yaml`
- [x] Crear `.agents/steering/git-workflow.md`
- [x] Crear `.agents/workflows/commit-workflow.md`
- [x] Crear `.agents/scripts/commit_agent.py`
- [x] Modificar `.agents/prompts/system-prompts.md`
- [x] Modificar `.agents/prompts/task-prompts.md`
- [x] Crear directorio `.agents/logs/`
- [x] Implementar análisis de cambios
- [x] Implementar categorización por módulo
- [x] Implementar verificación de umbrales
- [x] Implementar generación de 3 opciones de mensajes
- [x] Implementar monitor en background
- [x] Implementar notificaciones macOS
- [x] Actualizar `.agents/README.md`
- [x] Crear commit inicial
- [x] Documentación completa en español
- [x] Integración con OpenCode/Claude Code

---

## 🎉 ¡LISTO!

El **Commit Agent** está completamente implementado y listo para usar.

### Para empezar

```bash
# Analiza tus cambios actuales
python3 .agents/scripts/commit_agent.py analyze

# O inicia el monitor para alertas proactivas
python3 .agents/scripts/commit_agent.py monitor --interval 30
```

### Preguntas

- **¿Cómo lo uso con OpenCode?** Preguntá en el chat: "¿Hay alertas de commits pendientes?"
- **¿Dónde están las alertas?** En `.agents/logs/commit-alerts.log`
- **¿Cómo personalizo los umbrales?** Edita `.agents/steering/git-workflow.md`
- **¿Es compatible con otros runtimes?** Sí, funciona con cualquier runtime compatible con `.agents/`

---

**Implementado por:** mrtn
**Fecha:** 2025-01-16
**Versión:** 1.0.0
**Estado:** ✅ PRODUCCIÓN
