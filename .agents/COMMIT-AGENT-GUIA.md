# 🚀 Commit Agent - Guía Rápida

## ⚡ 2 Minutos para Empezar

### ¿Qué hace?
Analiza tus cambios de código y te ayuda a hacer commits más pequeños y descriptivos.

### ¿Cuándo alerta?
- **>3 archivos** modificados
- **>200 líneas** cambiadas
- **>2 horas** desde el último commit

---

## 🎯 3 Formas de Usar

### Forma 1: Auto-commit (la más fácil)

```bash
# Ver 3 opciones y commitear automáticamente
python3 .agents/scripts/commit_agent.py commit --option 1
```

**Ejemplo de salida:**
```
🚀 Ejecutando commit con opción 1...

📝 Mensaje de commit:
────────────────────────────────
feat(scraper): add new feature

- Update 2 file(s) in scraper
────────────────────────────────

✅ Commit creado exitosamente!
```

---

### Forma 2: Ver comandos (para copiar y pegar)

```bash
# Ver comandos listos para copiar
python3 .agents/scripts/commit_agent.py suggest --dry-run
```

**Ejemplo de salida:**
```
📋 Comandos git listos para copiar:

Opción 1:
git commit -m "feat(scraper): add new feature"
git commit -m "- Update 2 file(s) in scraper"

Opción 2:
git commit -m "feat(scraper): improve implementation"
git commit -m "- Update 2 file(s) in scraper"

Opción 3:
git commit -m "feat(scraper): enhance functionality"
git commit -m "- Update 2 file(s) in scraper"
```

---

### Forma 3: Ver opciones (para elegir manualmente)

```bash
# Ver las 3 opciones disponibles
python3 .agents/scripts/commit_agent.py suggest
```

**Luego commitea manualmente:**
```bash
git commit -m "feat(scraper): add new feature

- Update 2 file(s) in scraper"
```

---

## 🔔 Recibir Alertas

### En el Chat (OpenCode / Claude Code)

Las alertas se guardan en `.agents/logs/commit-alerts.log`. Para verlas:

```bash
# Preguntá en el chat
"¿Hay alertas de commits pendientes?"

# O leé el archivo
cat .agents/logs/commit-alerts.log
```

### En macOS (notificaciones nativas)

Cuando superas los umbrales, recibirás una notificación:

```
🔔 macOS Notification

Commit Agent
⚠️ ¡WARNING! Considerá hacer un commit (2 archivos, 1h 30m ago)
```

---

## 📝 Formato de Commits

### Estructura

```
<tipo>(<módulo>): <descripción corta>

<lista de cambios>
```

### Ejemplos Correctos

✅ **Ejemplo 1:**
```
feat(chatbot): add vector search

- Implement search using Qdrant
- Add relevance scoring
```

✅ **Ejemplo 2:**
```
fix(scraper): handle rate limit errors

- Add retry logic with exponential backoff
- Improve error logging
```

✅ **Ejemplo 3:**
```
docs(agents): add commit-agent documentation

- Add user guide
- Update installation instructions
```

### Ejemplos Incorrectos (NO usar)

❌ `reparo docs`
❌ `basura`
❌ `fix error`
❌ `update files`
❌ `Add feature`
❌ `Bug fix`

---

## 🎯 Tipos (Types)

| Tipo | Cuándo usar | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(chatbot): add search` |
| `fix` | Corrección de bug | `fix(scraper): handle errors` |
| `docs` | Documentación | `docs(agents): add guide` |
| `refactor` | Refactorización | `refactor(rag): improve code` |
| `test` | Tests | `test(api): add tests` |
| `chore` | Mantenimiento | `chore(deps): update deps` |

---

## 🎯 Módulos (Scopes)

| Módulo | Directorio | Ejemplo |
|--------|-----------|---------|
| `chatbot` | `chatbot/` | `feat(chatbot): ...` |
| `scraper` | `python-cli/` | `fix(scraper): ...` |
| `agents` | `.agents/` | `docs(agents): ...` |
| `docs` | Archivos `.md` | `docs(docs): ...` |
| `ci` | `.github/`, `.husky/` | `chore(ci): ...` |

---

## 🔍 Otros Comandos Útiles

### Ver estadísticas

```bash
python3 .agents/scripts/commit_agent.py stats
```

### Ver alertas recientes

```bash
python3 .agents/scripts/commit_agent.py alerts
```

### Iniciar monitor (alertas cada 30 min)

```bash
python3 .agents/scripts/commit_agent.py monitor --interval 30
```

### Detener monitor

```bash
python3 .agents/scripts/commit_agent.py monitor --stop
```

---

## 🎯 Umbrales de Alerta

| Nivel | Archivos | Líneas | Tiempo | Acción |
|-------|----------|--------|--------|--------|
| INFO | 3+ | 200+ | 2h+ | Mostrar info |
| WARNING | 10+ | 1000+ | 6h+ | Sugerir commit |
| CRITICAL | 20+ | 2000+ | 12h+ | Generar mensaje |
| EMERGENCY | 50+ | 5000+ | 24h+ | Alertar fuerte |

---

## ⚙️ Configuración

### Cambiar umbrales

Edita el archivo `.agents/scripts/commit_agent.py`:

```python
# Busca esta sección (línea ~25)
THRESHOLDS = {
    'info': {'files': 3, 'lines': 200, 'hours': 2},
    'warning': {'files': 10, 'lines': 1000, 'hours': 6},
    'critical': {'files': 20, 'lines': 2000, 'hours': 12},
    'emergency': {'files': 50, 'lines': 5000, 'hours': 24},
}
```

Cambia los valores según necesites.

---

## 🆘 Troubleshooting

### Problema: "El hook rechaza mi mensaje de commit"

**Solución:**
```bash
# Verifica el formato
git commit -m "feat(chatbot): descripción corta"

# Si estás seguro, puedes saltar la validación
git commit -m "tu mensaje" --no-verify
```

### Problema: "No quiero que me alerte tanto"

**Solución:**
Edita los umbrales en `.agents/scripts/commit_agent.py` y aumenta los valores.

### Problema: "Quiero desactivar el monitor"

**Solución:**
```bash
python3 .agents/scripts/commit_agent.py monitor --stop
```

### Problema: "Quiero desactivar notificaciones macOS"

**Solución:**
Edita `.agents/scripts/commit_agent.py` y comenta la función `send_notification()`.

---

## 📚 Archivos Principales

| Archivo | Propósito |
|---------|-----------|
| `.agents/agents/commit-agent.yaml` | Definición del agente |
| `.agents/scripts/commit_agent.py` | Implementación Python |
| `.agents/scripts/validate_commit_message.py` | Validación de mensajes |
| `.agents/steering/git-workflow.md` | Reglas de commits |
| `.agents/workflows/commit-workflow.md` | Guía paso a paso |
| `.agents/hooks/commit-msg.template` | Hook de git (template) |

---

## 🎯 Resumen en 3 Pasos

### 1. Recibes una alerta
```
🔔 Notification: Commit Agent
⚠️ ¡WARNING! Considerá hacer un commit (2 archivos, 1h 30m)
```

### 2. Ejecutas el comando
```bash
python3 .agents/scripts/commit_agent.py commit --option 1
```

### 3. Listo
```
✅ Commit creado exitosamente!
```

---

## 💡 Consejos

1. **Commiteá frecuente** - Cada 2-3 horas o cuando termines una tarea
2. **Usa el auto-commit** - Es la forma más fácil
3. **Lee las alertas** - Te avisan antes de que se acumule mucho
4. **Verifica el formato** - El hook lo valida automáticamente
5. **No uses mensajes genéricos** - "reparo docs", "basura" no sirven

---

## 🆘 Más Ayuda

### Ayuda rápida del agente

```bash
# Ver todos los comandos
python3 .agents/scripts/commit_agent.py --help

# Ver ayuda de un comando específico
python3 .agents/scripts/commit_agent.py suggest --help
```

### Documentación completa

- [`.agents/steering/git-workflow.md`](steering/git-workflow.md) - Reglas de commits
- [`.agents/workflows/commit-workflow.md`](workflows/commit-workflow.md) - Guía paso a paso
- [`.agents/COMMIT-AGENT-IMPLEMENTACION.md`](COMMIT-AGENT-IMPLEMENTACION.md) - Guía completa

---

**Versión:** 1.0.0  
**Fecha:** 2025-01-17  
**Autor:** mrtn

¡Listo para usar! 🚀
