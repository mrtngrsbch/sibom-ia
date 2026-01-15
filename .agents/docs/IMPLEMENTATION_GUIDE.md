# Guía de Implementación - Arquitectura .agents/

## Para Proyectos Futuros

**Versión:** 1.0
**Fecha:** 2026-01-07
**Autoría:** Claude Code + Usuario
**Proyecto original:** SIBOM Scraper Assistant

---

## 📋 Índice

1. [Introducción](#introducción)
2. [Conceptos Clave](#conceptos-clave)
3. [Requisitos Previos](#requisitos-previos)
4. [Implementación Paso a Paso](#implementación-paso-a-paso)
5. [Personalización](#personalización)
6. [Mejores Prácticas](#mejores-prácticas)
7. [Troubleshooting](#troubleshooting)
8. [Ejemplos Reales](#ejemplos-reales)

---

## 🎯 Introducción

### ¿Qué es esta arquitectura?

Una estructura de carpeta `.agents/` que funciona como **capa de abstracción tool-agnostic** para proyectos que usan múltiples herramientas de AI (Kiro, Claude Code, Droid, etc.).

### Problema que Resuelve

```
❌ ANTES (Problema):
.proyecto/
├── .kiro/           # Configuración de Kiro
├── .claude/         # Configuración de Claude Code
├── .factory/        # Configuración de Droid
├── .cursor/         # Configuración de Cursor
└── .obsidian/       # Configuración de Otros
→ "Spaghetti" de configuraciones
→ Documentación duplicada
→ Difícil de mantener
```

```
✅ DESPUÉS (Solución):
.proyecto/
├── .agents/         # Fuente única de verdad
│   ├── specs/       # Arquitectura (para todos)
│   ├── steering/    # Reglas (para todos)
│   ├── hooks/       # Automatizaciones
│   └── workflows/   # Procedimientos
├── .kiro/           # Solo análisis técnico
├── .claude/         # Solo config de Claude
└── .factory/        # Solo config de Droid
→ Una fuente de verdad
→ Documentación unificada
→ Fácil de mantener
```

### Beneficios

- ✅ **Tool-agnostic**: Funciona con CUALQUIER herramienta de AI
- ✅ **Escalable**: Fácil agregar nuevas herramientas
- ✅ **Mantenible**: Un solo lugar para actualizar reglas
- ✅ **Profesional**: Organización clara y documentada
- ✅ **Flexible**: Se adapta a cualquier tipo de proyecto

---

## 🧠 Conceptos Clave

### 1. Tres Niveles de Documentación

```
┌─────────────────────────────────────────────────┐
│  Nivel 1: .agents/        (CONCISO)             │
│  - Audiencia: Agentes AI                        │
│  - Propósito: Reglas operativas                 │
│  - Tamaño: 100-200 líneas por archivo           │
└─────────────────────────────────────────────────┘
                      ↓ consulta
┌─────────────────────────────────────────────────┐
│  Nivel 2: .kiro/         (DETALLADO)            │
│  - Audiencia: Ingenieros humanos                │
│  - Propósito: Análisis técnico profundo         │
│  - Tamaño: 600+ líneas por archivo              │
└─────────────────────────────────────────────────┘
                      ↓ informa
┌─────────────────────────────────────────────────┐
│  Nivel 3: docs/user/     (AMIGABLE)             │
│  - Audiencia: Usuarios finales                  │
│  - Propósito: Tutoriales y guías                │
│  - Tamaño: Variable                             │
└─────────────────────────────────────────────────┘
```

### 2. Fuentes de Verdad

| Carpeta | Rol | Lectura | Escritura |
|---------|-----|---------|-----------|
| **`.agents/`** | Reglas operativas | Agentes AI | Ingeniero humano |
| **`.kiro/`** | Análisis técnico | Ingeniero humano | Kiro (automático) |
| **`docs/`** | Documentación usuario | Usuario final | Ingeniero humano |

### 3. Sincronización Bidireccional

```bash
# .kiro/ → .agents/ (referencias)
python .agents/hooks/sync_from_kiro.py

# .agents/ → .kiro/ (propagación de reglas)
python .agents/hooks/propagate_to_kiro.py

# Completa
python .agents/hooks/sync_all.py
```

---

## 📦 Requisitos Previos

### Opcionales pero Recomendados

1. **Kiro** (para análisis técnico automático)
   - Genera `.kiro/` con documentación detallada
   - URL: https://kiro.ai

2. **Python 3.8+** (para scripts de sincronización)
   - No requerido si no usas sync scripts

3. **Git** (para control de versiones)
   - Recomendado para cualquier proyecto

### Sin Kiro

Si NO usas Kiro, puedes crear `.agents/` manualmente:
- Ver sección [Implementación Manual](#implementación-manual-sin-kiro)

---

## 🚀 Implementación Paso a Paso

### Opción A: Con Kiro (Recomendado)

#### Paso 1: Instalar y Ejecutar Kiro

```bash
# Instalar Kiro (siguiendo su documentación)
# Ejecutar análisis del proyecto
kiro analyze ./tu-proyecto
```

Esto genera:
```
.tu-proyecto/
└── .kiro/
    ├── specs/           # Análisis técnico
    ├── steering/        # Patrones de código
    └── hooks/           # Definiciones de hooks
```

#### Paso 2: Crear Estructura .agents/

```bash
# Crear estructura base
mkdir -p .agents/{specs,steering,hooks,workflows}

# Copiar scripts de sincronización
# (Usar plantillas de la sección Plantillas)
cp ~/plantillas/sync_*.py .agents/hooks/
```

#### Paso 3: Ejecutar Sincronización Inicial

```bash
python .agents/hooks/sync_from_kiro.py
```

Esto genera:
```
.tu-proyecto/
├── .agents/
│   ├── specs/           # Referencias a .kiro/specs/
│   ├── steering/        # Copia editable de .kiro/steering/
│   └── hooks/           # Scripts de sincronización
└── .kiro/               # Análisis técnico original
```

#### Paso 4: Configurar Herramientas

**Claude Code** (`.claude/CLAUDE.md`):

```markdown
# CLAUDE.md

## Antes de trabajar

1. LEER: `.agents/specs/` para entender arquitectura
2. RESPETAR: `.agents/steering/` como reglas OBLIGATORIAS
3. CONSULTAR: `.kiro/` solo para detalles de implementación
```

**Droid** (`.factory/config.yml`):

```yaml
agents_context:
  read_first:
    - .agents/specs/
    - .agents/steering/
  reference_for_details:
    - .kiro/
  hard_constraints:
    - .agents/steering/
```

#### Paso 5: Personalizar para tu Proyecto

Editar archivos en `.agents/steering/` para agregar reglas específicas:

```bash
vim .agents/steering/claude-specific-rules.md
vim .agents/steering/droid-specific-rules.md
```

#### Paso 6: (Opcional) Configurar Pre-commit Hook

```bash
# Crear .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
if git diff --cached --name-only | grep -q "^\.agents/"; then
    echo "🔄 Cambios en .agents/ detectados, sincronizando..."
    python .agents/hooks/sync_all.py
fi
EOF

chmod +x .git/hooks/pre-commit
```

---

### Opción B: Implementación Manual (Sin Kiro)

#### Paso 1: Crear Estructura Base

```bash
mkdir -p .agents/{specs,steering,hooks,workflows}
```

#### Paso 2: Crear Archivos de Especificación

**`.agents/specs/01-project-overview.md`**:

```markdown
# [Nombre del Proyecto] - Overview

## ⚠️ ARCHIVO AUTO-GENERADO

Este archivo contiene la arquitectura del proyecto.

## Resumen Ejecutivo

Descripción breve del proyecto (2-3 párrafos).

## Arquitectura

### Stack Tecnológico

- **Backend:**
- **Frontend:**
- **Base de datos:**
- **Otros:**

### Estructura del Proyecto

```
project-name/
├── backend/
├── frontend/
└── shared/
```

## Funcionalidades Principales

1. **Feature 1**: Descripción
2. **Feature 2**: Descripción
3. **Feature 3**: Descripción

## Para Más Detalles

Ver documentación técnica en `docs/technical/` (si existe).
```

#### Paso 3: Crear Archivos de Steering

**`.agents/steering/coding-patterns.md`**:

```markdown
# Coding Patterns - [Nombre del Proyecto]

## ⚠️ BASE EDITABLE

Este archivo contiene reglas de codificación que los agentes AI DEBEN seguir.

## Principios Generales

1. **Principio 1**: Descripción
2. **Principio 2**: Descripción
3. **Principio 3**: Descripción

## Patrones de Código

### [Lenguaje 1] - Backend

- ✅ HACER: Lista de prácticas
- ❌ NO HACER: Lista de anti-patrones

### [Lenguaje 2] - Frontend

- ✅ HACER: Lista de prácticas
- ❌ NO HACER: Lista de anti-patrones

## Ejemplos

```python
# ✅ BUEN ejemplo
def good_example():
    pass

# ❌ MAL ejemplo
def bad_example():
    pass
```
```

#### Paso 4: Configurar Herramientas

(Same as Opción A, Paso 4)

---

## 🎨 Personalización

### Adaptar a Diferentes Tipos de Proyecto

#### Proyecto Backend-Only

```
.agents/
├── specs/
│   ├── 01-api-architecture.md
│   ├── 02-database-schema.md
│   └── 03-auth-flow.md
└── steering/
    ├── api-patterns.md
    └── database-patterns.md
```

#### Proyecto Frontend-Only

```
.agents/
├── specs/
│   ├── 01-component-architecture.md
│   ├── 02-state-management.md
│   └── 03-routing-strategy.md
└── steering/
    ├── react-patterns.md
    └── styling-patterns.md
```

#### Proyecto Full-Stack

```
.agents/
├── specs/
│   ├── 01-system-overview.md
│   ├── 02-backend-architecture.md
│   ├── 03-frontend-architecture.md
│   └── 04-integration.md
└── steering/
    ├── backend-patterns.md
    ├── frontend-patterns.md
    └── api-contracts.md
```

#### Proyecto Data Science/ML

```
.agents/
├── specs/
│   ├── 01-project-overview.md
│   ├── 02-data-pipeline.md
│   ├── 03-model-architecture.md
│   └── 04-deployment-strategy.md
└── steering/
    ├── data-patterns.md
    ├── model-patterns.md
    └── experiment-tracking.md
```

### Agregar Reglas Específicas por Herramienta

**`.agents/steering/claude-specific-rules.md`**:

```markdown
# Claude Code - Reglas Específicas

## Formato de Respuesta

- Siempre usar español
- Ser conciso pero completo
- Incluir ejemplos de código cuando sea relevante

## Estilo de Código

- Preferir funciones puras
- Usar type hints siempre
- Documentar con docstrings

## Errores Comunes a Evitar

- No omitir manejo de errores
- No usar globales para configuración
- No hardcodear valores
```

**`.agents/steering/droid-specific-rules.md`**:

```markdown
# Droid - Reglas Específicas

## Comportamiento Esperado

- Leer TODO el contexto antes de sugerir cambios
- Explicar el porqué de cada cambio
- Sugerir tests para nuevo código

## Preferencias de Framework

- [Tus preferencias específicas]
```

---

## 📚 Mejores Prácticas

### 1. Mantén .agents/ Actualizado

```bash
# Después de cambios arquitectónicos importantes
python .agents/hooks/sync_all.py

# Revisar cambios
git diff .agents/

# Commit
git add .agents/ && git commit -m "docs: actualizar .agents/"
```

### 2. Sea Granular con los Archivos

**❌ MAL**: Un archivo gigante

```markdown
# everything.md (2000 líneas)
- Backend patterns
- Frontend patterns
- DB patterns
- DevOps patterns
- Testing patterns
```

**✅ BIEN**: Múltiples archivos enfocados

```markdown
steering/
├── backend-patterns.md (200 líneas)
├── frontend-patterns.md (200 líneas)
├── database-patterns.md (150 líneas)
├── devops-patterns.md (150 líneas)
└── testing-patterns.md (150 líneas)
```

### 3. Usa Ejemplos de Código Reales

**❌ MAL**: Explicación vaga

```markdown
## Error Handling

Manejar errores apropiadamente.
```

**✅ BIEN**: Ejemplo específico

```markdown
## Error Handling

```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_data(url: str) -> dict:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise
    except requests.Timeout:
        logger.error(f"Timeout fetching {url}")
        raise
```
```

### 4. Documenta Decisiones Arquitectónicas

En `.agents/spec/`, incluye secciones "Rationale":

```markdown
## Architecture Decision: Why PostgreSQL over MongoDB?

### Context
Necesitamos almacenar datos transaccionales con relaciones complejas.

### Decision
PostgreSQL sobre MongoDB.

### Rationale
- ✅ ACID transactions
- ✅ Complex joins
- ✅ Mature ORM ecosystem (SQLAlchemy)
- ❌ No necesitamos schema flexibility
- ❌ No esperamos alta write throughput

### Consequences
- Trade-off 1: Schema migrations required
- Trade-off 2: Less flexible for rapid prototyping
```

### 5. Versiona .agents/ con Git

```bash
# .gitignore (para otros)
.kiro/

# PERO mantener .agents/ versionado
!.agents/

# Commit temprano y seguido
git add .agents/
git commit -m "docs: add .agents/ architecture"
```

---

## 🔧 Troubleshooting

### Problema: Los agentes no siguen las reglas

**Síntoma**: Claude Code ignora `.agents/steering/`

**Soluciones**:

1. **Verificar que `.claude/CLAUDE.md` existe**:
   ```bash
   cat .claude/CLAUDE.md
   # Debe mencionar .agents/
   ```

2. **Verificar que las reglas son claras**:
   - Usa formato "✅ HACER" / "❌ NO HACER"
   - Incluye ejemplos de código

3. **Ser explícito en prompts**:
   ```
   Antes de empezar, lee .agents/specs/ y .agents/steering/
   ```

### Problema: Sincronización no funciona

**Síntoma**: `sync_from_kiro.py` falla

**Soluciones**:

1. **Verificar que .kiro/ existe**:
   ```bash
   ls -la .kiro/
   ```

2. **Ejecutar con verbosidad**:
   ```bash
   python -v .agents/hooks/sync_from_kiro.py
   ```

3. **Verificar permisos**:
   ```bash
   chmod +x .agents/hooks/*.py
   ```

### Problema: Demasiada información en .agents/

**Síntema**: Los archivos son demasiado largos (500+ líneas)

**Solución**:

1. **Mover detalles a .kiro/**
2. **Mantener .agents/ conciso (100-200 líneas)**
3. **Usar referencias**:
   ```markdown
   ## Para detalles profundos
   Ver: `.kiro/specs/backend-architecture.md:Sección X`
   ```

---

## 📖 Ejemplos Reales

### Ejemplo 1: Proyecto SaaS B2B

**Stack**: Next.js + Python FastAPI + PostgreSQL + Redis

```
.saas-project/
├── .agents/
│   ├── specs/
│   │   ├── 01-product-overview.md
│   │   ├── 02-frontend-architecture.md
│   │   ├── 03-backend-api.md
│   │   ├── 04-database-schema.md
│   │   └── 05-auth-strategy.md
│   └── steering/
│       ├── react-patterns.md
│       ├── fastapi-patterns.md
│       ├── sql-patterns.md
│       └── auth-patterns.md
├── .kiro/
│   └── (análisis técnico automático)
└── .claude/
    └── CLAUDE.md
```

### Ejemplo 2: Proyecto Móvil (React Native)

**Stack**: React Native + Expo + Firebase

```
.mobile-app/
├── .agents/
│   ├── specs/
│   │   ├── 01-app-architecture.md
│   │   ├── 02-navigation-structure.md
│   │   ├── 03-state-management.md
│   │   └── 04-firebase-integration.md
│   └── steering/
│       ├── react-native-patterns.md
│       ├── navigation-patterns.md
│       └── firebase-patterns.md
└── .kiro/
    └── (opcional, si usas Kiro)
```

### Ejemplo 3: Proyecto Data Engineering

**Stack**: Python + Airflow + Snowflake + dbt

```
.data-pipeline/
├── .agents/
│   ├── specs/
│   │   ├── 01-pipeline-overview.md
│   │   ├── 02-data-sources.md
│   │   ├── 03-transformation-logic.md
│   │   └── 04-data-model.md
│   └── steering/
│       ├── airflow-patterns.md
│       ├── sql-patterns.md
│       └── dbt-patterns.md
└── .kiro/
    └── (análisis técnico)
```

---

## 🎓 Checklist de Implementación

Use este checklist para asegurar que la implementación está completa:

### Fase 1: Setup Inicial

- [ ] Instalar Kiro (opcional pero recomendado)
- [ ] Ejecutar análisis de Kiro
- [ ] Crear estructura `.agents/`
- [ ] Copiar scripts de sincronización

### Fase 2: Documentación

- [ ] Crear archivos en `.agents/specs/`
  - [ ] Overview del proyecto
  - [ ] Arquitectura de cada componente
  - [ ] Diagramas de flujo de datos
- [ ] Crear archivos en `.agents/steering/`
  - [ ] Patrones de código
  - [ ] Reglas de formato
  - [ ] Manejo de errores

### Fase 3: Configuración de Herramientas

- [ ] Configurar Claude Code (`.claude/CLAUDE.md`)
- [ ] Configurar Droid (`.factory/config.yml`)
- [ ] Configurar otras herramientas (si aplica)

### Fase 4: Testing

- [ ] Probar que agentes leen `.agents/specs/`
- [ ] Verificar que siguen `.agents/steering/`
- [ ] Confirmar que consultan `.kiro/` para detalles
- [ ] Ejecutar sincronización completa

### Fase 5: Mantenimiento

- [ ] Configurar pre-commit hook (opcional)
- [ ] Documentar proceso de actualización
- [ ] Crear guía para el equipo

---

## 📞 Recursos Adicionales

### Documentación Relacionada

- [GUIA_COMPLETA.md](GUIA_COMPLETA.md) - Manual detallado del sistema
- [PLAN_COEXISTENCIA.md](PLAN_COEXISTENCIA.md) - Estrategia de arquitectura
- [ANALISIS_SINCRONIZACION.md](ANALISIS_SINCRONIZACION.md) - Detalles técnicos

### Herramientas

- **Kiro**: https://kiro.ai - Análisis automático de código
- **Claude Code**: https://claude.ai/code - AI pair programmer
- **Factory/Droid**: https://factory.ai - AI agents

### Comunidades

- **AGENTS.md standard**: https://agents.md - Estandarización de config de agentes

---

## 📝 Changelog

### v1.0 (2026-01-07)

- ✅ Versión inicial
- ✅ Documentación completa
- ✅ Scripts de sincronización
- ✅ Probado en proyecto real

### Futuras mejoras

- ⏳ CLI tool para setup automático
- ⏳ Integración con más herramientas
- ⏳ Validación automática de archivos
- ⏳ Tests para verificar configuración

---

## 🤝 Contribución

Esta es una arquitectura abierta. Si encuentras mejoras:

1. Documenta lo que funcionó
2. Comparte con la comunidad
3. Contribuye a este documento

---

**¿Preguntas? Revisa la [GUIA_COMPLETA.md](GUIA_COMPLETA.md) o abre un issue.**

---

**Fin de la Guía de Implementación** 🎉
