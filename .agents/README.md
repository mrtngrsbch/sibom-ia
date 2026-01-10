# .agents/ - Arquitectura de Agentes AI

Esta carpeta contiene la arquitectura de proyecto agnóstica a herramientas.

## 📁 Estructura

```
.agents/
├── specs/           ← Referencias a .kiro/specs/ (AUTO-GENERADO)
├── steering/        ← Reglas para agentes AI (EDITABLE)
├── hooks/           ← Scripts de sincronización
└── workflows/       ← Procedimientos multi-paso
```

## 🎯 Fuentes de Verdad

### `.agents/` es fuente de verdad para:
- ✅ **Reglas obligatorias para agentes AI** (`.agents/steering/`)
- ✅ **Workflows y procedimientos** (`.agents/workflows/`)
- ✅ **Hooks de automatización** (`.agents/hooks/`)

### `.kiro/` es fuente de verdad para:
- ✅ **Análisis técnico profundo** (`.kiro/specs/`)
- ✅ **Patrones técnicos base** (`.kiro/steering/`)
- ✅ **Plan de implementación** (`.kiro/specs/tasks.md`)

### Sincronización:
- `.kiro/specs/` → `.agents/specs/` (referencias concisas)
- `.agents/steering/` → `.kiro/steering/` (propagación de reglas)

## 🔄 Sincronización

```bash
# Después de que Kiro analice el proyecto
python .agents/hooks/sync_from_kiro.py

# Para agregar reglas específicas para agentes
# 1. Editar .agents/steering/
# 2. Ejecutar: python .agents/hooks/propagate_to_kiro.py

# Sincronización completa (ambas direcciones)
python .agents/hooks/sync_all.py
```

## 🤖 Configuración de Herramientas

### Claude Code
Ver `.claude/CLAUDE.md` para instrucciones específicas.

**Resumen:**
1. LEER: `.agents/specs/` para entender arquitectura
2. RESPETAR: `.agents/steering/` como reglas OBLIGATORIAS
3. CONSULTAR: `.kiro/specs/` solo si necesitas detalles

### Droid (Factory)
Ver `.factory/config.yml` para configuración.

**Resumen:**
- Lee `.agents/` primero
- Consulta `.kiro/` para detalles técnicos
- Respeta restricciones en `.agents/steering/`

## 📚 Documentación

- **[Análisis de Integridad](ANALISIS_INTEGRIDAD.md)** - Confirmación de arquitectura
- **[Guía Completa](GUIA_COMPLETA.md)** - Manual completo del sistema
- **[Plan de Coexistencia](PLAN_COEXISTENCIA.md)** - Estrategia de arquitectura
- **[Análisis de Sincronización](ANALISIS_SINCRONIZACION.md)** - Detalles técnicos

## 🚀 Inicio Rápido

### Para Agentes AI

1. **Leer primero:** `.agents/specs/` (arquitectura concisa)
2. **Respetar siempre:** `.agents/steering/` (reglas obligatorias)
3. **Consultar si necesario:** `.kiro/specs/` (análisis técnico profundo)

### Para Desarrolladores Humanos

1. **Estudiar:** `.kiro/specs/` (análisis técnico completo)
2. **Editar:** `.agents/steering/` (agregar reglas para agentes)
3. **Sincronizar:** `python .agents/hooks/sync_all.py`

---

**Última actualización:** 2026-01-09  
**Estado:** Arquitectura confirmada y funcional
