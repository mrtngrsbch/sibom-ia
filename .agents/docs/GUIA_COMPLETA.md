# Guía Completa: Sistema de Documentación SIBOM

## Fecha: 2026-01-07
## Última actualización: 2026-01-07

## Propósito

Esta guía explica TODO el sistema de documentación del proyecto para que puedas recordarlo sin tener que preguntar.

---

## 📚 Estructura de Documentación (Resumen Visual)

```
sibom-scraper-assistant/
│
├── .kiro/                    ← Análisis técnico de Kiro (READ-ONLY)
│   ├── specs/                ──────┐
│   ├── steering/             │     │ Referencia
│   ├── hooks/                │     │ Bidireccional
│   └── ANALYSIS_SUMMARY.md    │     │ (propagar reglas)
│                             │     │
├── .agents/                  ← Reglas para agentes AI (MIXTO) ◄────┘
│   ├── specs/                ← Referencias a .kiro/ (READ-ONLY)
│   ├── steering/             ← Reglas para agentes (EDITABLE)
│   ├── hooks/                ← Scripts de sincronización
│   ├── workflows/            ← Procedimientos multi-paso
│   └── README.md             ← "Qué es esta carpeta"
│
├── docs/                     ← Documentación para humanos
│   ├── technical/            ← Copia de .kiro/ (para ingenieros)
│   └── user/                 ← Tutoriales para usuarios (pendiente)
│
├── .claude/                  ← Configuración Claude Code
├── .factory/                 ← Configuración Droid
│
├── python-cli/               ← Backend Python
└── chatbot/                  ← Frontend Next.js
```

---

## 🔑 Conceptos Clave (Para no olvidar)

### 1. Fuentes de Verdad

| Carpeta | Es fuente de verdad de... | ¿Se edita? |
|---------|-------------------------|------------|
| `.kiro/specs/` | Análisis técnico completo | ❌ READ-ONLY (solo Kiro) |
| `.kiro/steering/` | Patrones técnicos detallados | ⚠️ Raramente (solo reglas de agentes) |
| `.agents/specs/` | Referencias a `.kiro/` | ❌ AUTO-GENERADO |
| `.agents/steering/` | Reglas para agentes AI | ✅ SÍ (vos editás) |
| `.agents/hooks/` | Scripts de automatización | ✅ SÍ (vos editás) |

### 2. Relación entre carpetas

```
.kiro/ (técnico)          ← REFERENCIA →
  ↓ copia                             ↑ propaga
docs/technical/    ← COPIA →          ↑ reglas
                                           ↓
                                         .agents/ (reglas AI)
```

### 3. Flujo de Trabajo Normal

```bash
# 1. Kiro analiza el proyecto
Abrir Kiro → Genera .kiro/ con análisis completo

# 2. Sincronizar .agents/ desde .kiro/
python3 .agents/hooks/sync_from_kiro.py

# 3. (Opcional) Editar .agents/steering/ para agregar reglas específicas
vim .agents/steering/claude-specific-rules.md

# 4. (Opcional) Propagar reglas a .kiro/
python3 .agents/hooks/propagate_to_kiro.py

# 5. Usar herramientas
Claude Code → Lee .agents/ → Respeta reglas → Consulta .kiro/ si necesita detalles
```

---

## 📖 Guías Rápidas

### Guía Rápida #1: ¿Qué archivo edito para X?

| Querés... | Editás este archivo | NO edites |
|-----------|-------------------|-----------|
| Agregar regla para Claude | `.agents/steering/claude-specific-rules.md` | `.kiro/` directamente |
| Cambiar arquitectura del sistema | `.kiro/specs/` primero (luego sync) | `.agents/specs/` directamente |
| Agregar automatización | `.agents/hooks/nuevo-hook.md` | - |
| Documentar para usuarios | `docs/user/tutorial.md` | `.kiro/` o `.agents/` |
| Actualizar documentación técnica | `.kiro/specs/` (luego sync) | `.agents/` directamente |

### Guía Rápida #2: ¿Dónde encuentro información sobre X?

| Querés saber sobre... | Leés este archivo | Profundidad |
|---------------------|------------------|------------|
| Arquitectura general | `.kiro/specs/01-proyecto-overview.md` | Muy detallada |
| Backend scraper | `.kiro/specs/02-backend-scraper.md` | Muy detallada |
| Frontend chatbot | `.kiro/specs/03-frontend-chatbot.md` | Muy detallada |
| Plan de implementación | `.kiro/specs/tasks.md` | Sprints detallados |
| Patrones Python | `.kiro/steering/python-patterns.md` | Código real incluido |
| Patrones TypeScript | `.kiro/steering/typescript-patterns.md` | Código real incluido |
| Reglas para Claude | `.agents/steering/claude-specific-rules.md` | Reglas concisas |
| Resumen rápido | `.agents/README.md` | 5 minutos |

### Guía Rápida #3: Comandos de Sincronización

```bash
# Sincronizar .agents/ desde .kiro/ (después de que Kiro analice)
python3 .agents/hooks/sync_from_kiro.py

# Propagar reglas de .agents/ hacia .kiro/ (después de editar steering)
python3 .agents/hooks/propagate_to_kiro.py

# Sincronización completa (ambas direcciones)
python3 .agents/hooks/sync_all.py

# Ver estado de sincronización
python3 .agents/hooks/sync_status.py
```

---

## 🎯 Escenarios Comunes

### Escenario 1: "Acabo de terminar que Kiro analice el proyecto"

```bash
# 1. Verificar que .kiro/ se creó
ls -la .kiro/

# 2. Sincronizar .agents/
python3 .agents/hooks/sync_from_kiro.py

# 3. Verificar que .agents/specs/ se creó
ls -la .agents/specs/

# 4. (Opcional) Copiar a docs/technical/
cp -r .kiro/ docs/technical/

# 5. Commit
git add .kiro/ .agents/ docs/technical/
git commit -m "docs: análisis completo de Kiro + estructura .agents/"
```

### Escenario 2: "Quiero agregar una regla para Claude Code"

```bash
# 1. Editar archivo de reglas
vim .agents/steering/claude-specific-rules.md

# Agregar por ejemplo:
# "Claude DEBE siempre usar type hints estrictos"
# "Claude DEBE leer .agents/specs/ antes de codear"

# 2. Propagar a .kiro/
python3 .agents/hooks/propagate_to_kiro.py

# 3. Verificar que se agregó a .kiro/steering/
grep -A 10 "Agent AI Requirements" .kiro/steering/python-patterns.md

# 4. Commit
git add .agents/ .kiro/
git commit -m "agents: agregar reglas específicas para Claude Code"
```

### Escenario 3: "Quiero actualizar la arquitectura del sistema"

```bash
# 1. NO editar .agents/ directamente
# 2. Editar .kiro/ primero (fuente de verdad técnica)
vim .kiro/specs/01-proyecto-overview.md

# 3. Sincronizar .agents/
python3 .agents/hooks/sync_from_kiro.py

# 4. Verificar que .agents/specs/ se actualizó
cat .agents/specs/01-proyecto-overview.md

# 5. Commit
git add .kiro/ .agents/
git commit -m "docs: actualizar arquitectura del sistema"
```

### Escenario 4: "Quiero usar Droid (Factory) en este proyecto"

```bash
# 1. Configurar Droid para usar .agents/
vim .factory/config.yml

# Agregar:
# agents_context:
#   read_first:
#     - .agents/specs/
#     - .agents/steering/
#   reference:
#     - .kiro/specs/
#   constraints:
#     hard:
#       - .agents/steering/droid-specific-rules.md

# 2. (Opcional) Crear reglas específicas para Droid
vim .agents/steering/droid-specific-rules.md

# "Droid DEBE ejecutar hooks antes de commit"
# "Droid DEBE respetar restricciones de .agents/steering/"

# 3. Sincronizar
python3 .agents/hooks/propagate_to_kiro.py

# 4. Commit
git add .agents/ .factory/
git commit -m "agents: configurar Droid con arquitectura .agents"
```

### Escenario 5: "Olvidé cómo funciona algo, ¿dónde reviso?"

```bash
# Para recordatorio rápido:
cat .agents/README.md

# Para guía completa:
cat .agents/GUIA_COMPLETA.md  # ← ESTE ARCHIVO

# Para ver estado de sincronización:
python3 .agents/hooks/sync_status.py

# Para entender relación entre carpetas:
cat .agents/PLAN_COEXISTENCIA.md
```

---

## ⚠️ Errores Comunes (y cómo evitarlos)

### Error #1: "Edité .agents/specs/ directamente y se perdieron los cambios"

**Problema:** `.agents/specs/` es AUTO-GENERADO desde `.kiro/`

**Solución:**
```bash
# NO editar .agents/specs/ directamente
# EN SU LUGAR:

# 1. Editar .kiro/specs/ (fuente de verdad)
vim .kiro/specs/archivo.md

# 2. Sincronizar
python3 .agents/hooks/sync_from_kiro.py

# 3. Los cambios se propagan a .agents/specs/
```

### Error #2: "Kiro sobrescribió mis cambios en .kiro/"

**Problema:** Kiro regenera `.kiro/` desde cero

**Solución:**
```bash
# MANTENER .kiro/ bajo control de versiones
git add .kiro/
git commit -m "docs: snapshot de análisis de Kiro"

# Si Kiro regenera, restaurar desde git
git checkout .kiro/

# O mejor: mantener .kiro/ en una rama separada
git checkout -b kiro-analysis
git mv .kiro/ docs/technical-from-kiro/
git commit -m "docs: preservar análisis de Kiro"
git checkout main  # Volver a rama principal
```

### Error #3: "No sé qué archivos son editables y cuáles no"

**Regla general:**
- ✅ EDITABLE: `.agents/steering/`, `.agents/hooks/`, `.agents/workflows/`
- ❌ READ-ONLY: `.agents/specs/` (auto-generado), `.kiro/` (Kiro lo maneja)
- ✅ EDITABLE (humano): `.kiro/specs/tasks.md`, `.kiro/specs/design.md`

**Para verificar:**
```bash
# Ver cabecera de archivo
head -5 .agents/specs/01-proyecto-overview.md

# Si dice: "AUTO-GENERADO desde .kiro/" → NO EDITAR
# Si dice: "Reglas para agentes AI" → PUEDES EDITAR
```

---

## 📋 Checklist de Mantenimiento

### Semanal (recomendado)

- [ ] Ejecutar `python3 .agents/hooks/sync_status.py`
- [ ] Verificar que `.agents/` esté sincronizado con `.kiro/`
- [ ] Revisar si hay nuevas reglas para agentes que agregar

### Mensual

- [ ] Actualizar `.kiro/` ejecutando Kiro nuevamente
- [ ] Revisar plan de implementación (`.kiro/specs/tasks.md`)
- [ ] Actualizar reglas de `.agents/steering/` si es necesario

### Trimestral

- [ ] Revisar toda la estructura de documentación
- [ ] Archivar versión antigua de `.kiro/` si es necesario
- [ ] Actualizar esta guía si hay cambios

---

## 🔗 Referencias Rápidas

### Archivos clave que siempre consultarás

| Archivo | Para qué sirve | Cuándo leerlo |
|---------|---------------|---------------|
| [`.agents/README.md`](.agents/README.md) | "Qué es esta carpeta" | Cuando te olvides la estructura |
| [`.agents/GUIA_COMPLETA.md`](.agents/GUIA_COMPLETA.md) | Esta guía | Cuando necesites recordarlo TODO |
| [`.kiro/ANALYSIS_SUMMARY.md`](.kiro/ANALYSIS_SUMMARY.md) | Resumen ejecutivo de Kiro | Cuando quieras un panorama rápido |
| [`.kiro/specs/tasks.md`](.kiro/specs/tasks.md) | Plan de implementación | Cuando planifiques sprints |
| [`.kiro/specs/design.md`](.kiro/specs/design.md) | Documento de diseño | Cuando estudies arquitectura |

### Scripts que siempre usarás

| Script | Qué hace | Cuándo ejecutarlo |
|--------|---------|------------------|
| `.agents/hooks/sync_from_kiro.py` | Sincroniza .agents/ ← .kiro/ | Después de que Kiro analice |
| `.agents/hooks/propagate_to_kiro.py` | Propaga .agents/ → .kiro/ | Después de editar steering |
| `.agents/hooks/sync_status.py` | Muestra estado de sync | Cuando quieras verificar |
| `.agents/hooks/sync_all.py` | Sincronización completa | Para actualizar todo |

---

## 🆘 Ayuda Rápida

### "Olvidé todo, ¿por dónde empiezo?"

```bash
# 1. Leer esta guía
cat .agents/GUIA_COMPLETA.md

# 2. Ver estado actual
python3 .agents/hooks/sync_status.py

# 3. Si necesita sincronización
python3 .agents/hooks/sync_all.py

# 4. Listo, ya podés trabajar
```

### "¿Qué carpeta abro en Kiro?"

```bash
# Abrir el proyecto desde la raíz
# Kiro creará .kiro/ automáticamente

# Si ya existe .kiro/, Kiro lo actualizará
# Si querés preservar la versión actual, haz backup primero:
cp -r .kiro/ .kiro-backup-$(date +%Y%m%d)/
```

### "¿Cómo configuro una nueva herramienta para usar .agents/?"

```bash
# 1. Crear archivo de reglas específicas
vim .agents/steering/nueva-herramienta-specific-rules.md

# Agregar:
# "Herramienta X DEBE leer .agents/specs/ antes de codear"
# "Herramienta X DEBE respetar .agents/steering/"

# 2. Propagar a .kiro/
python3 .agents/hooks/propagate_to_kiro.py

# 3. Configurar herramienta según su documentación
# (ver documentación de la herramienta específica)
```

---

## 📞 ¿Necesitas más ayuda?

### Si esta guía no cubre tu caso:

1. Revisa los otros archivos de `.agents/`:
   - [`.agents/PLAN_COEXISTENCIA.md`](.agents/PLAN_COEXISTENCIA.md) - Plan de coexistencia
   - [`.agents/ANALISIS_SINCRONIZACION.md`](.agents/ANALISIS_SINCRONIZACION.md) - Análisis de sincronización
   - [`.agents/EXTRACCION_KIRO.md`](.agents/EXTRACCION_KIRO.md) - Plan de extracción original

2. Revisa los documentos de planificación:
   - [`.agents/ESTRATEGIA_FINAL.md`](.agents/ESTRATEGIA_FINAL.md) - Estrategia de 3 niveles

3. Si aún así no encuentras respuesta:
   - La documentación de Kiro (`.kiro/`) tiene detalles técnicos profundos
   - Los READMEs de cada carpeta tienen información específica

---

## ✅ Resumen de 30 segundos

- **`.kiro/`** = Análisis técnico de Kiro (READ-ONLY, fuente de verdad)
- **`.agents/`** = Reglas para agentes AI (EDITABLE, specs auto-generados)
- **`docs/technical/`** = Copia de `.kiro/` para humanos
- **Sync scripts** en `.agents/hooks/` mantienen todo sincronizado
- **Esta guía** = Tu manual para no olvidar nada

---

**¡Guarda esta guía y consúltala cuando necesites!** 🚀

**Última actualización:** 2026-01-07
**Versión:** 1.0
**Estado:** Completo y funcional
