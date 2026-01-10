# .agents/ - Arquitectura de Agentes AI

Esta carpeta contiene la arquitectura de proyecto agnóstica a herramientas.

## Estructura

```
.agents/
├── specs/           ← Referencias a .kiro/specs/ (READ-ONLY)
├── steering/        ← Reglas para agentes AI (EDITABLE)
├── hooks/           ← Scripts de sincronización
└── workflows/       ← Procedimientos multi-paso
```

## Fuentes de Verdad

- **`.kiro/`**: Documentación técnica completa (análisis de Kiro)
- **`.agents/`**: Reglas operativas para agentes AI

## Sincronización

```bash
# Después de que Kiro analice el proyecto
python .agents/hooks/sync_from_kiro.py

# Para agregar reglas específicas para agentes
# 1. Editar .agents/steering/
# 2. Ejecutar: python .agents/hooks/propagate_to_kiro.py
```

## Documentación

- **[Guía Completa](GUIA_COMPLETA.md)** - Manual completo del sistema
- **[Plan de Coexistencia](PLAN_COEXISTENCIA.md)** - Estrategia de arquitectura
- **[Análisis de Sincronización](ANALISIS_SINCRONIZACION.md)** - Detalles técnicos

---

**Última sincronización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
