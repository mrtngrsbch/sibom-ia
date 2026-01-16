# Commit Workflow - Guía de Uso Paso a Paso

## 🚀 MANUAL DE USO - COMMIT AGENT

### ¿Qué es?
El commit-agent es un asistente que te ayuda a hacer commits más pequeños y descriptivos.

### ¿Qué hace?
- Analiza tus cambios de código
- Te avisa cuando hay muchos cambios (>5 archivos)
- Genera 3 sugerencias de mensajes de commit
- Te alerta cada 30 minutos si hay cambios pendientes

### ¿Cómo funciona?
Funciona con OpenCode y Claude Code. Las alertas aparecen en el chat.

---

## 📋 FLUJO 1: COMMIT NORMAL

### Paso 1: Hacé cambios
```bash
# Editá archivos
vim chatbot/src/lib/rag/retriever.ts
vim chatbot/src/lib/types.ts
```

### Paso 2: Analizá cambios
```bash
commit-agent analyze
```

**Output:**
```
ℹ️  Cambios detectados:
  M chatbot/src/lib/rag/retriever.ts    (+45, -12)
  M chatbot/src/lib/types.ts            (+15, -5)

📊 Estadísticas:
  Archivos: 2
  Líneas: +45, -12
  Tiempo desde último commit: 1h 23m

✅ Commit sugerido (opcional):
  feat(rag): improve vector search relevance

¿Querés generar un mensaje de commit? (y/n) _
```

### Paso 3: Generá sugerencias
```bash
commit-agent suggest
```

**Output:**
```
📋 Opciones de mensajes de commit:

1. feat(rag): improve vector search relevance scoring
   - Adjust similarity threshold from 0.7 to 0.75
   - Add type narrowing for better matching
   - Update types to reflect new scoring logic

2. fix(rag): fix vector search type mismatch errors
   - Fix TypeScript errors in retriever.ts
   - Update types.ts with new interfaces

3. refactor(rag): optimize vector search matching logic
   - Simplify similarity calculation
   - Improve type safety in retriever

Seleccioná una opción (1-3) o 'n' para cancelar: _
```

### Paso 4: Commiteá
```bash
commit-agent commit --option 1
```

**Output:**
```
✅ Preparing commit...
📝 Commit message:
  feat(rag): improve vector search relevance scoring

  - Adjust similarity threshold from 0.7 to 0.75
  - Add type narrowing for better matching
  - Update types to reflect new scoring logic

¿Confirmar commit? (y/n) y
✅ Commit creado: abc1234
```

---

## 📋 FLUJO 2: COMMIT GRANDE

### Paso 1: Hacés muchos cambios
```bash
# Editás varios archivos
vim chatbot/src/lib/rag/*.ts
vim chatbot/src/lib/api/*.ts
vim chatbot/components/*.tsx
```

### Paso 2: Analizá cambios
```bash
commit-agent analyze
```

**Output:**
```
⚠️  ALERTA: Muchos cambios detectados
=====================================
📊 Estadísticas:
  Archivos: 12
  Líneas: +650, -180
  Directories: chatbot/src/lib/rag, chatbot/src/lib/api, chatbot/components
  Tiempo desde último commit: 5h 45m

🎯 Análisis por módulo:
  • chatbot/src/lib/rag/      (6 archivos, +420 líneas)
  • chatbot/src/lib/api/      (3 archivos, +150 líneas)
  • chatbot/components/       (3 archivos, +80 líneas)

💡 Recomendación: Considerá dividir en 2-3 commits más pequeños

📋 Opciones de mensajes de commit:

1. feat(chatbot): implement vector search and API endpoints
   - Add vector search using Qdrant in rag/
   - Implement API endpoints in api/
   - Add search components in components/

2. feat(rag): add vector search with relevance scoring
   - Implement Qdrant client in rag/
   - Add embedding generation
   - Implement similarity search with threshold 0.75

3. feat(api): add chatbot API for bulletin queries
   - Implement /api/query endpoint
   - Add /api/validate endpoint
   - Integrate with vector search

Seleccioná una opción (1-3) o 'd' para dividir en múltiples commits: _
```

### Paso 3: Opciones

**Opción A: Commitear todo**
```bash
commit-agent commit --option 1
```

**Opción B: Dividir en múltiples commits**
```bash
# Elegí 'd' para dividir
```

---

## 📋 FLUJO 3: DIVIDIR COMMITS GRANDES

### Paso 1: Elegís dividir
```bash
commit-agent analyze
# Seleccioná: d
```

**Output:**
```
🔄 Modo de división activado
=====================================

Commit 1: Módulo RAG
Archivos:
  M chatbot/src/lib/rag/retriever.ts
  M chatbot/src/lib/rag/vector_search.ts
  M chatbot/src/lib/rag/types.ts

Mensaje sugerido:
  feat(rag): add vector search with relevance scoring

¿Commitear estos archivos? (y/n) y

✅ Commit 1 creado: abc1234

=====================================

Commit 2: Módulo API
Archivos:
  M chatbot/src/lib/api/chat.ts
  M chatbot/src/lib/api/query.ts
  M chatbot/src/lib/api/types.ts

Mensaje sugerido:
  feat(api): add chatbot API for bulletin queries

¿Commitear estos archivos? (y/n) y

✅ Commit 2 creado: def5678

=====================================

Commit 3: Módulo Components
Archivos:
  M chatbot/components/SearchBar.tsx
  M chatbot/components/ResultsList.tsx
  M chatbot/components/ChatInput.tsx

Mensaje sugerido:
  feat(chatbot): add search components for bulletin queries

¿Commitear estos archivos? (y/n) y

✅ Commit 3 creado: ghi9012

🎉 3 commits creados exitosamente
=====================================
```

---

## 📋 FLUJO 4: MONITOR EN BACKGROUND

### Paso 1: Iniciá el monitor
```bash
commit-agent monitor --interval 30
```

**Output:**
```
🔍 Iniciando monitor de commits...
✅ Monitor corriendo en background (PID: 12345)
✅ Intervalo: 30 minutos
✅ Logs: .agents/logs/commit-monitor.log

Usá 'commit-agent monitor --stop' para detener

📊 Estado actual:
  Cambios pendientes: 0
  Último commit: hace 1h 23m
  Próxima verificación: en 30 minutos (14:45)
```

### Paso 2: Seguí trabajando
```bash
# Trabajá en otros archivos
vim python-cli/sibom_scraper.py
vim .agents/steering/python-patterns.md
```

### Paso 3: Después de 30 min, alerta

**Notificación en el chat (OpenCode/Claude Code):**
```
🔔 Commit Agent: Alerta

Tienes 8 archivos modificados desde hace 4h 15m

Archivos:
  • python-cli/sibom_scraper.py        (+180, -45)
  • python-cli/scripts/validate.py      (+120, -30)
  • python-cli/scripts/generate.py      (+90, -15)
  • python-cli/docs/scraper.md          (+60, -10)
  • .agents/steering/python-patterns.md  (+40, -5)
  • .agents/agents/scraper.yaml         (+30, -0)
  • .agents/prompts/system-prompts.md   (+25, -0)
  • .agents/workflows/scraper.md        (+20, -0)

Sugerencia: Considerá hacer un commit

Ejecutá: commit-agent analyze
        o
        commit-agent commit --option 1
```

### Paso 4: Detené el monitor
```bash
commit-agent monitor --stop
```

**Output:**
```
✅ Monitor detenido (PID: 12345)
📊 Estado final:
  Tiempo de ejecución: 2h 34m
  Verificaciones realizadas: 5
  Alertas generadas: 2
```

---

## 📋 FLUJO 5: VER ALERTAS

### Paso 1: Ver alertas recientes
```bash
commit-agent alerts
```

**Output:**
```
📋 Alertas recientes
=====================================

[2025-01-16 14:30] ⚠️  WARNING - 8 archivos modificados
  Tiempo desde último commit: 4h 15m
  Líneas: +565, -105
  Directories: python-cli, .agents

[2025-01-16 15:00] 🔴 CRITICAL - 12 archivos modificados
  Tiempo desde último commit: 5h 45m
  Líneas: +650, -180
  Directories: python-cli, .agents, chatbot

[2025-01-16 15:30] 🟢 OK - Sin cambios pendientes
  Último commit: hace 5 min

=====================================

Acciones disponibles:
- commit-agent analyze      → Analizar cambios actuales
- commit-agent commit --option 1 → Commitear con opción 1
- commit-agent monitor --stop   → Detener monitor
```

---

## 📋 FLUJO 6: VER ESTADÍSTICAS

### Paso 1: Ver tus estadísticas
```bash
commit-agent stats
```

**Output:**
```
📊 Estadísticas de Commits
=====================================

📈 Últimos 7 días:
  Commits totales: 15
  Promedio por día: 2.1
  Promedio tiempo entre commits: 3h 23m

📏 Tamaño promedio de commits:
  Archivos por commit: 6.3
  Líneas añadidas por commit: 245
  Líneas eliminadas por commit: 78

🏷️  Tipos de commits (últimos 30 días):
  feat: 45% (7 commits)
  fix: 25% (4 commits)
  docs: 15% (2 commits)
  refactor: 10% (2 commits)
  chore: 5% (1 commits)

📁 Distribución por módulo:
  python-cli/: 40% (6 commits)
  chatbot/: 35% (5 commits)
  .agents/: 25% (4 commits)

⏱️  Último commit:
  abc1234 | feat(chatbot): add vector search
  Hace: 23 minutos

=====================================

💡 Recomendaciones:
- ✅ Buen ritmo de commits (2.1 por día)
- ⚠️  Considerá hacer commits más pequeños (promedio 6.3 archivos)
- ✅ Buen uso de tipos (feat/fix dominan)

Acciones:
- commit-agent analyze → Ver cambios actuales
- commit-agent monitor --start → Iniciar monitor
```

---

## 🔧 COMANDOS AVANZADOS

### Personalizar umbrales

```bash
# Editar configuración
vim .agents/steering/git-workflow.md

# Buscar sección "Umbrales de Alerta"
# Ajustar valores según necesites
```

### Ver logs del monitor

```bash
# Ver logs en tiempo real
tail -f .agents/logs/commit-monitor.log

# Ver últimos 50 líneas
tail -50 .agents/logs/commit-monitor.log

# Ver logs de alertas
tail -f .agents/logs/commit-alerts.log
```

### Debug mode

```bash
# Ejecutar con debug
commit-agent analyze --debug

# Output con detalles técnicos:
# [DEBUG] Executing: git status --short
# [DEBUG] Parsing git output...
# [DEBUG] Detected 2 modified files
# [DEBUG] Calculating statistics...
# [DEBUG] Total lines: +45, -12
# [DEBUG] Checking thresholds...
# [DEBUG] Threshold: INFO (2 files < 5)
```

---

## 🆘 TROUBLESHOOTING

### Problema: "commit-agent: command not found"

**Solución:**
```bash
# Aseguráte de que el script sea ejecutable
chmod +x .agents/scripts/commit_agent.py

# Agregá alias a .gitconfig
git config alias.ca '!python3 $(git rev-parse --show-toplevel)/.agents/scripts/commit_agent.py analyze'
git config alias.cs '!python3 $(git rev-parse --show-toplevel)/.agents/scripts/commit_agent.py suggest'
git config alias.cc '!python3 $(git rev-parse --show-toplevel)/.agents/scripts/commit_agent.py commit'
```

### Problema: "No se detectan cambios"

**Solución:**
```bash
# Verificá que estás en el directorio correcto
cd /ruta/al/proyecto
pwd

# Ejecutá git status manualmente
git status --short

# Compará con output del agente
commit-agent analyze --debug
```

### Problema: "Monitor no envía alertas"

**Solución:**
```bash
# Verificá que el monitor está corriendo
ps aux | grep commit_agent

# Verificá logs
cat .agents/logs/commit-monitor.log

# Reiniciá monitor
commit-agent monitor --stop
commit-agent monitor --interval 30
```

### Problema: "Alertas no aparecen en el chat"

**Solución:**
Las alertas se guardan en `.agents/logs/commit-alerts.log`. Para verlas:

```bash
# Opción 1: Preguntá en el chat
"¿Hay alertas de commits pendientes?"

# Opción 2: Leé el archivo
cat .agents/logs/commit-alerts.log

# Opción 3: Usá notificaciones nativas
commit-agent monitor --notify native
```

---

## 📚 REFERENCIAS

- [`.agents/steering/git-workflow.md`](../steering/git-workflow.md) - Reglas de commits
- [`.agents/agents/commit-agent.yaml`](agents/commit-agent.yaml) - Definición del agente
- [`.agents/scripts/commit_agent.py`](scripts/commit_agent.py) - Implementación
- [`.agents/README.md`](../README.md) - Arquitectura de agentes
- [`.husky/pre-commit`](../../.husky/pre-commit) - Hook de validación
