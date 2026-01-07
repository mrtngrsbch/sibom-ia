# Análisis: Sincronización .agents/ → .kiro/

## Fecha: 2026-01-07

## La pregunta fundamental

**¿Debe ser .kiro/ una vista sincronizada de .agents/?**

O dicho de otra forma:
**¿Quién es la fuente de verdad?**

---

## Opción A: .agents/ como fuente de verdad

```
.agents/ (fuente) → sincronizar → .kiro/ (vista)
```

### Ventajas:
- ✅ `.agents/` es agnóstica a herramientas
- ✅ Un solo lugar para mantener specs/steering
- ✅ Control total sobre el contenido

### Desventajas:
- ❌ Kiro podría sobrescribir cambios en `.kiro/`
- ❌ Formatos incompatibles (`.agents/` es conciso, `.kiro/` es detallado)
- ❌ Perderíamos el análisis profundo de Kiro
- ❌ Conflicto de direccionalidad (¿quién manda?)

### Problema técnico CRÍTICO:

```python
# Script de sincronización .agents/ → .kiro/

def sync_agents_to_kiro():
    """
    Problema: .agents/ es CONCISO, .kiro/ es DETALLADO

    ¿Cómo convertimos 150 líneas → 600 líneas?
    - No podemos "inventar" el detalle faltante
    - Kiro ya generó su análisis detallado
    - Perderíamos TODO el trabajo de Kiro
    """
    # Esto NO funciona
    short_content = Path('.agents/specs/01-proyecto-overview.md').read_text()
    # ¿Cómo expandimos a 600 líneas con código real?
    # IMPOSIBLE sin perder el trabajo de Kiro
```

---

## Opción B: .kiro/ como fuente de verdad

```
.kiro/ (fuente) → extraer esencial → .agents/ (vista)
```

### Ventajas:
- ✅ Preservamos TODO el análisis profundo de Kiro
- ✅ `.agents/` es verdaderamente una "vista simplificada"
- ✅ Kiro sigue funcionando normalmente
- ✅ No perdemos NINGÚN trabajo de Kiro

### Desventajas:
- ❌ Si editás `.agents/`, se pierde al sincronizar
- ❌ Kiro no sabe de `.agents/` (no es bidireccional)

### Solución: .agents/ es READ-ONLY (excepto steering/hooks)

```bash
# Estructura
.kiro/               ← Fuente de verdad (READ-ONLY después de generado)
  ↓
  ↓ extraer esencial (script)
  ↓
.agents/             ← Vista agnóstica (EDITABLE solo steering/hooks)
├── specs/           ← READ-ONLY (generado desde .kiro/)
├── steering/        ← EDITABLE (reglas específicas para agentes)
└── hooks/           ← EDITABLE (automatizaciones)
```

---

## Opción C: Dos fuentes de verdad independientes

```
.agents/             ← Para agentes AI (vos mantenés)
.kiro/              ← Para Kiro (Kiro mantiene)
docs/technical/     ← Para ingenieros humanos (copia de .kiro/)
```

### Ventajas:
- ✅ Cada herramienta tiene su territorio
- ✅ Sin conflictos de sincronización
- ✅ Máxima flexibilidad

### Desventajas:
- ❌ Posible duplicación de esfuerzo
- ❌ Riesgo de desincronización

---

## Mi recomendación: Opción HÍBRIDA

```bash
# Estructura final

.kiro/               ← Fuente de verdad técnica (READ-ONLY)
├── specs/           ← Análisis profundo de Kiro
├── steering/        ← Patrones técnicos detallados
└── ANALYSIS_SUMMARY.md

.agents/             ← Reglas para agentes (MIXTO)
├── specs/           ← READ-ONLY (referencias a .kiro/)
│   └── 01-proyecto-overview.md
│       "Ver análisis completo: .kiro/specs/01-proyecto-overview.md"
│
├── steering/        ← EDITABLE (reglas específicas para AI)
│   ├── claude-code-patterns.md      ← Específico para Claude
│   ├── droid-patterns.md            ← Específico para Droid
│   └── testing-requirements.md      ← Reqs de testing
│
└── hooks/           ← EDITABLE (automatizaciones)
    └── sync_from_kiro.py            ← Script que SÍ actualiza .kiro/

docs/technical/     ← Para humanos (copia de .kiro/)
└── (todo el contenido de .kiro/)
```

---

## Cómo funciona la sincronización en este modelo

### Flujo 1: .kiro/ → .agents/ (automático)

```python
# Script: .agents/hooks/sync_from_kiro.py

def sync_specs_from_kiro():
    """
    Genera .agents/specs/ como referencias a .kiro/
    """
    for kiro_spec in Path('.kiro/specs/').glob('*.md'):
        # No copiamos contenido
        # Solo creamos archivos con referencias
        agents_spec = Path('.agents/specs/') / kiro_spec.name

        agents_spec.write_text(f"""
# {kiro_spec.stem}

## Resumen

Este archivo es una referencia al análisis técnico completo.

## Documentación técnica

Ver: `.kiro/specs/{kiro_spec.name}`

## Para agentes AI

Cuando trabajéis en este proyecto:
1. LEER el archivo .kiro/ correspondiente
2. ENTENDER la arquitectura descrita
3. APLICAR patrones de .agents/steering/

NO modificar este archivo - es una referencia.
""")
```

### Flujo 2: .agents/ → .kiro/ (cuando agregas reglas para agentes)

```python
# Script: .agents/hooks/propagate_to_kiro.py

def propagate_steering_to_kiro():
    """
    Propaga cambios de .agents/steering/ hacia .kiro/steering/

    Útil cuando agregás reglas específicas para agentes AI
    """
    for agents_steering in Path('.agents/steering/').glob('*.md'):
        if 'claude-code' in agents_steering.name or 'droid' in agents_steering.name:
            # Estas son REGLAS PARA AGENTES, no patrones técnicos
            # No van a .kiro/ porque .kiro/ es técnica general

            continue

        # Para steering general (python-patterns, etc)
        kiro_steering = Path('.kiro/steering/') / agents_steering.name

        # Agregar sección de "Agent AI Requirements" al archivo de Kiro
        if kiro_steering.exists():
            content = kiro_steering.read_text()
            if '## Agent AI Requirements' not in content:
                content += f"""

## Agent AI Requirements

Based on `.agents/steering/{agents_steering.name}`:

{agents_steering.read_text()}
"""
                kiro_steering.write_text(content)
```

---

## ¿Cuándo usar cada flujo?

### Flujo 1 (.kiro/ → .agents/):
- **Trigger:** Automático después de que Kiro genera análisis
- **Propósito:** Crear referencias en `.agents/`
- **Resultado:** `.agents/specs/` con links a `.kiro/`

### Flujo 2 (.agents/ → .kiro/):
- **Trigger:** Manual, cuando editás `.agents/steering/`
- **Propósito:** Agregar reglas de agentes al análisis técnico
- **Resultado:** `.kiro/steering/` actualizado con "Agent AI Requirements"

---

## Respuesta a tu pregunta original

### "Si actualizo .agents/, debe enterarse también .kiro/"

**Respuesta:** DEPENDE de qué actualices:

| Si actualizás... | ¿Propagar a .kiro/? | ¿Por qué? |
|-----------------|---------------------|----------|
| `.agents/specs/` | ❌ NO | Son REFERENCIAS a .kiro/ |
| `.agents/steering/claude-code-patterns.md` | ❌ NO | Específico de herramienta |
| `.agents/steering/python-patterns.md` | ✅ SÍ | Regla general, útil para .kiro/ |
| `.agents/hooks/` | ❌ NO | Específico de automatización |

### "¿Acaso Kiro reconoce .agents/?"

**Respuesta:** NO, pero PUEDE reconocer referencias:

```yaml
# En .kiro/, podemos agregar:

## Agent AI Integration

Este proyecto usa `.agents/` como arquitectura de agentes AI-agnostic.

Para agents trabajando en este proyecto:
- LEER: `.agents/steering/python-patterns.md`
- RESPETAR: `.agents/steering/` como reglas obligatorias
- CONSULTAR: Este documento para detalles técnicos
```

---

## Conclusión y Recomendación Final

### Estructura óptima:

```bash
.kiro/                      ← Análisis técnico de Kiro (READ-ONLY)
├── specs/                  ← Fuente de verdad técnica
└── steering/               ← Patrones técnicos generales
    └── (con referencias a .agents/)

.agents/                    ← Reglas para agentes (EDITABLE)
├── specs/                  ← REFERENCIAS a .kiro/ (auto-generado)
├── steering/               ← REGLAS para agentes
│   ├── python-patterns.md       ← Copia + "Agent AI Requirements"
│   ├── typescript-patterns.md   ← Copia + "Agent AI Requirements"
│   └── claude-specific.md        ← Específico de Claude (NO va a .kiro/)
└── hooks/                   ← Automatizaciones
    ├── sync_from_kiro.py        ← Actualiza .agents/ desde .kiro/
    └── propagate_to_kiro.py      ← Propaga reglas a .kiro/

docs/technical/             ← Para humanos (copia de .kiro/)
└── (contenido idéntico a .kiro/)
```

### Workflow:

1. **Kiro genera análisis** → `.kiro/` creado
2. **Ejecutas sync script** → `.agents/specs/` creado con referencias
3. **Editás `.agents/steering/`** → Agregas reglas específicas para agentes
4. **Ejecutas propagate script** → `.kiro/` actualizado con "Agent AI Requirements"
5. **Ingenieros leen** → `docs/technical/` (copia de `.kiro/`)

### ¿Se entiende .kiro/ y .agents/?

- **`.kiro/`** entiende su propio contenido + referencias a `.agents/`
- **`.agents/`** entiende referencias a `.kiro/` + reglas propias
- **Herramientas (Claude, Droid)** entienden `.agents/` + referencias a `.kiro/`

---

## Próximo paso

¿Implementamos esta estructura híbrida?

1. Crear script de sincronización BIDIRECCIONAL
2. Definir qué es READ-ONLY vs EDITABLE
3. Establecer workflow de actualización

¡Tengo el código listo para implementar! 🚀
