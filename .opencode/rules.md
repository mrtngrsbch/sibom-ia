# Reglas del Proyecto - SIBOM Scraper Assistant

**Última actualización:** 2025-01-16

---

## 🎯 Reglas de Oro

### 1. Jerarquía de Dependencias

```
.agents/ define → .opencode/ ejecuta → .kiro/ referencia
```

**NUNCA al revés**

- `.agents/` es la fuente de verdad de dominio
- `.opencode/` solo ejecuta lo que `.agents/` define
- `.kiro/` es referencia técnica opcional

### 2. Portabilidad

- `.agents/` es agnóstico de herramientas
- Puede vivir en cualquier IDE/runtime
- Si cambias de OpenCode a otra herramienta, `.agents/` no cambia

### 3. Fuentes de Verdad

| Aspecto | Fuente de Verdad | Editable |
|---------|------------------|----------|
| **Definición de agentes** | `.agents/agents/` | ✅ Sí |
| **Prompts** | `.agents/prompts/` | ✅ Sí |
| **Reglas de código** | `.agents/steering/` | ✅ Sí |
| **Ejecución** | `.opencode/` | ✅ Sí |
| **Análisis técnico** | `.kiro/specs/` | ❌ No |

### 4. Flujo de Trabajo

```bash
1. Diseñas agente en .agents/
2. Lo documentas
3. Lo versionas (git commit)
4. .opencode/ lo referencia (automático)
5. Ejecutas
6. Ajustas dominio
7. Commit
```

### 5. Sincronización

- **Automática**: OpenCode lee `.agents/` en cada ejecución
- **Manual (backup)**: `python .agents/hooks/sync_to_opencode.py`

---

## 📋 Reglas de Código

### Python

Seguir patrones de `.agents/steering/python-patterns.md`:

- ✅ Class-based design con dependency injection
- ✅ Retry logic con exponential backoff
- ✅ Structured logging con structlog
- ✅ Atomic file operations
- ✅ Type hints estrictos
- ✅ Immutable configuration

### TypeScript

Seguir patrones de `.agents/steering/typescript-patterns.md`:

- ✅ Explicit type definitions (no `any`)
- ✅ Discriminated unions para state
- ✅ React.memo y useMemo para performance
- ✅ Error boundaries para resilience
- ✅ Type-safe API clients

### Error Handling

Seguir estrategias de `.agents/steering/error-handling.md`:

- ✅ Try-catch en todos los async/await
- ✅ Retry logic para errores de red
- ✅ Fallbacks para servicios externos
- ✅ Mensajes user-friendly
- ✅ Logging estructurado

### Testing

Seguir patrones de `.agents/steering/testing-patterns.md`:

- ✅ Unit tests para lógica de negocio
- ✅ Property-based tests para robustez
- ✅ Integration tests para flujos completos
- ✅ Mock de dependencias externas

### Performance

Seguir optimizaciones de `.agents/steering/performance-optimization.md`:

- ✅ Memoización de componentes React
- ✅ Debounce de operaciones costosas
- ✅ Cache multi-nivel
- ✅ Lazy loading
- ✅ Batch processing

---

## 🚫 Restricciones

### NO hacer:

- ❌ Definir prompts largos dentro de `.opencode/agents.json`
- ❌ Copiar lógica de agente en múltiples archivos
- ❌ Hacer que `.agents/` dependa de `.opencode/`
- ❌ Guardar memoria viva en `.agents/`
- ❌ Usar `.agents/` como cache
- ❌ Editar `.kiro/` directamente (es auto-generado)
- ❌ Ignorar reglas de `.agents/steering/`

### SÍ hacer:

- ✅ Definir agentes en `.agents/agents/`
- ✅ Crear prompts en `.agents/prompts/`
- ✅ Seguir patrones de `.agents/steering/`
- ✅ Commit frecuente de `.agents/`
- ✅ Consultar `.kiro/` para detalles técnicos
- ✅ Sincronizar después de cambios

---

## 🔄 Comandos Comunes

```bash
# Ver estado de sincronización
python .agents/hooks/sync_status.py

# Sincronizar .agents/ → .opencode/ (backup)
python .agents/hooks/sync_to_opencode.py

# Sincronizar .kiro/ → .agents/
python .agents/hooks/sync_from_kiro.py

# Propagar .agents/ → .kiro/
python .agents/hooks/propagate_to_kiro.py

# Sincronización completa
python .agents/hooks/sync_all.py
```

---

## 📚 Documentación

- **[.agents/README.md](../.agents/README.md)** - Manual completo
- **[.agents/agents/README.md](../.agents/agents/README.md)** - Cómo crear agentes
- **[.kiro/specs/](../.kiro/specs/)** - Análisis técnico profundo
- **[AGENTS.md](../AGENTS.md)** - Guía general del proyecto

---

## ✅ Checklist Antes de Commit

- [ ] Código sigue patrones de `.agents/steering/`
- [ ] Tests pasan (si aplica)
- [ ] Documentación actualizada
- [ ] `.agents/` sincronizado con `.opencode/`
- [ ] No hay secretos en el código
- [ ] Commit message descriptivo

---

**Última actualización:** 2025-01-16  
**Versión:** 1.0
