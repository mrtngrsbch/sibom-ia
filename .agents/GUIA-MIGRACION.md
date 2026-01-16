# Guía de Migración - Actualización a v2.0

**Fecha:** 2025-01-16  
**De:** v1.0 → v2.0  
**Tiempo estimado:** 10 minutos

---

## 🎯 ¿Qué Cambió?

La arquitectura de `.agents/` fue reorganizada completamente para ser portable y agnóstica de herramientas.

### Cambio Principal

**ANTES (v1.0):**
```
.agents/ y .kiro/ competían como fuentes de verdad
```

**AHORA (v2.0):**
```
.agents/ define → .opencode/ ejecuta → .kiro/ referencia
```

---

## 📋 Checklist de Migración

### Paso 1: Leer Nueva Documentación (5 min)

```bash
# Leer manual completo
cat .agents/README.md

# Leer resumen de cambios
cat .agents/CHANGELOG.md

# Leer quickstart
cat .agents/QUICKSTART.md
```

**¿Qué buscar?**
- Nueva estructura de carpetas
- Jerarquía de dependencias
- Flujos de trabajo actualizados

### Paso 2: Actualizar Referencias (2 min)

**Cambios en tus scripts/código:**

| ANTES (v1.0) | AHORA (v2.0) |
|--------------|--------------|
| Leer `.agents/specs/*.md` | Leer `.agents/README.md` |
| Leer `.agents/COORDINACION.md` | Leer `.agents/README.md` |
| Leer `.agents/docs/` | Leer `.agents/README.md` |
| Consultar `.agents/` para detalles | Consultar `.kiro/specs/` para detalles |

**Ejemplo de actualización:**

```bash
# ANTES
cat .agents/specs/01-proyecto-overview.md

# AHORA
cat .agents/README.md  # Para overview general
cat .kiro/specs/01-proyecto-overview.md  # Para detalles técnicos
```

### Paso 3: Verificar Sincronización (1 min)

```bash
# Verificar estado
python .agents/hooks/sync_status.py

# Sincronizar si es necesario
python .agents/hooks/sync_all.py
```

### Paso 4: Actualizar Workflows (2 min)

**Workflow antiguo:**
```bash
# ANTES: Leer múltiples archivos
cat .agents/specs/02-backend-architecture.md
cat .agents/specs/03-frontend-architecture.md
cat .agents/COORDINACION.md
```

**Workflow nuevo:**
```bash
# AHORA: Leer un solo archivo
cat .agents/README.md

# Consultar detalles solo si es necesario
cat .kiro/specs/02-backend-architecture.md
```

---

## 🔄 Mapeo de Archivos

### Archivos Eliminados → Nuevas Ubicaciones

| Archivo Eliminado | Nueva Ubicación | Notas |
|-------------------|-----------------|-------|
| `.agents/specs/01-proyecto-overview.md` | `.agents/README.md` + `.kiro/specs/` | Consolidado |
| `.agents/specs/02-backend-architecture.md` | `.kiro/specs/02-backend-architecture.md` | Movido a referencia |
| `.agents/specs/03-frontend-architecture.md` | `.kiro/specs/03-frontend-architecture.md` | Movido a referencia |
| `.agents/specs/04-integracion.md` | `.kiro/specs/04-integracion.md` | Movido a referencia |
| `.agents/specs/05-data-pipeline.md` | `.kiro/specs/05-data-pipeline.md` | Movido a referencia |
| `.agents/specs/06-llm-integration.md` | `.kiro/specs/06-llm-integration.md` | Movido a referencia |
| `.agents/COORDINACION.md` | `.agents/README.md` | Fusionado |
| `.agents/docs/*` (19 archivos) | `.agents/README.md` | Consolidado |

### Archivos Nuevos

| Archivo Nuevo | Propósito |
|---------------|-----------|
| `.agents/README.md` | Manual completo (500+ líneas) |
| `.agents/QUICKSTART.md` | Guía rápida |
| `.agents/CHANGELOG.md` | Historial de cambios |
| `.agents/agents/README.md` | Guía de creación de agentes |
| `.agents/agents/rag-indexer.yaml` | Ejemplo de agente |
| `.agents/prompts/system-prompts.md` | Prompts de sistema |
| `.agents/prompts/task-prompts.md` | Prompts de tareas |
| `.agents/specs/README.md` | Pointer a .kiro/ |
| `.agents/hooks/sync_to_opencode.py` | Sincronización con OpenCode |
| `.opencode/agents.json` | Registro de agentes |
| `.opencode/rules.md` | Reglas del proyecto |

---

## 🚨 Breaking Changes

### 1. `.agents/specs/` Ya No Contiene Especificaciones

**ANTES:**
```bash
cat .agents/specs/01-proyecto-overview.md  # ✅ Funcionaba
```

**AHORA:**
```bash
cat .agents/specs/01-proyecto-overview.md  # ❌ No existe
cat .agents/README.md                      # ✅ Usar esto
cat .kiro/specs/01-proyecto-overview.md    # ✅ O esto para detalles
```

**Solución:**
- Para overview general: Leer `.agents/README.md`
- Para detalles técnicos: Leer `.kiro/specs/`

### 2. `.agents/COORDINACION.md` Eliminado

**ANTES:**
```bash
cat .agents/COORDINACION.md  # ✅ Funcionaba
```

**AHORA:**
```bash
cat .agents/COORDINACION.md  # ❌ No existe
cat .agents/README.md        # ✅ Usar esto (contiene todo)
```

**Solución:**
- Todo el contenido está en `.agents/README.md`

### 3. `.agents/docs/` Eliminado

**ANTES:**
```bash
ls .agents/docs/  # ✅ 19 archivos
```

**AHORA:**
```bash
ls .agents/docs/  # ❌ No existe
cat .agents/README.md  # ✅ Usar esto
```

**Solución:**
- Toda la documentación está consolidada en `.agents/README.md`

---

## 🔧 Actualizar Scripts Personalizados

### Ejemplo 1: Script que Lee Specs

**ANTES:**
```bash
#!/bin/bash
# mi-script.sh

# Leer specs
for spec in .agents/specs/*.md; do
    echo "Procesando $spec"
    cat "$spec"
done
```

**AHORA:**
```bash
#!/bin/bash
# mi-script.sh

# Leer manual principal
echo "Leyendo manual principal"
cat .agents/README.md

# Leer specs de referencia (opcional)
for spec in .kiro/specs/*.md; do
    echo "Procesando $spec"
    cat "$spec"
done
```

### Ejemplo 2: Script que Busca Documentación

**ANTES:**
```bash
#!/bin/bash
# buscar-docs.sh

grep -r "arquitectura" .agents/specs/
grep -r "arquitectura" .agents/docs/
```

**AHORA:**
```bash
#!/bin/bash
# buscar-docs.sh

# Buscar en manual principal
grep -r "arquitectura" .agents/README.md

# Buscar en referencia (opcional)
grep -r "arquitectura" .kiro/specs/
```

### Ejemplo 3: Script de Onboarding

**ANTES:**
```bash
#!/bin/bash
# onboarding.sh

echo "Leyendo documentación..."
cat .agents/COORDINACION.md
cat .agents/specs/01-proyecto-overview.md
ls .agents/docs/
```

**AHORA:**
```bash
#!/bin/bash
# onboarding.sh

echo "Leyendo documentación..."
cat .agents/QUICKSTART.md  # Guía rápida
cat .agents/README.md      # Manual completo
```

---

## 📝 Actualizar Documentación Interna

### README.md del Proyecto

**ANTES:**
```markdown
## Documentación

Ver `.agents/specs/` para especificaciones detalladas.
Ver `.agents/COORDINACION.md` para coordinación de agentes.
```

**AHORA:**
```markdown
## Documentación

Ver `.agents/README.md` para el manual completo del sistema.
Ver `.agents/QUICKSTART.md` para una guía rápida.
Ver `.kiro/specs/` para análisis técnico profundo (opcional).
```

### Wiki/Confluence

**Actualizar enlaces:**
- `.agents/specs/` → `.agents/README.md`
- `.agents/COORDINACION.md` → `.agents/README.md`
- `.agents/docs/` → `.agents/README.md`

---

## 🎓 Nuevos Conceptos

### 1. Jerarquía de Dependencias

```
.agents/ define → .opencode/ ejecuta → .kiro/ referencia
```

**Regla de oro:** `.agents/` NUNCA depende de runtimes

### 2. Portabilidad

`.agents/` es agnóstico de herramientas:
- Funciona con OpenCode
- Funciona con Claude Code
- Funciona con Factory/Droids
- Funciona con cualquier runtime futuro

### 3. Single Source of Truth

**Un solo entry point:** `.agents/README.md`

No más múltiples archivos para entender el sistema.

### 4. Sincronización Automática

OpenCode lee `.agents/` automáticamente en cada ejecución.

No necesitas sincronizar manualmente (pero puedes si quieres).

---

## ✅ Validación Post-Migración

### Checklist de Validación

```bash
# 1. Verificar que puedes leer el manual
cat .agents/README.md
# ✅ Debe mostrar 500+ líneas

# 2. Verificar sincronización
python .agents/hooks/sync_status.py
# ✅ Debe mostrar estado OK

# 3. Verificar que OpenCode detecta agentes
cat .opencode/agents.json
# ✅ Debe mostrar agentes registrados

# 4. Verificar que .kiro/ existe (referencia)
ls .kiro/specs/
# ✅ Debe mostrar archivos de specs

# 5. Verificar que archivos antiguos no existen
ls .agents/docs/
# ❌ Debe dar error (no existe)

ls .agents/COORDINACION.md
# ❌ Debe dar error (no existe)
```

### Tests de Integración

```bash
# Test 1: Crear nuevo agente
vim .agents/agents/test-agent.yaml
git add .agents/agents/test-agent.yaml
git commit -m "test: agregar agente de prueba"
# ✅ Debe funcionar sin errores

# Test 2: Actualizar prompt
vim .agents/prompts/task-prompts.md
git commit -am "test: actualizar prompt"
# ✅ Debe funcionar sin errores

# Test 3: Sincronización completa
python .agents/hooks/sync_all.py
# ✅ Debe completar sin errores
```

---

## 🆘 Troubleshooting

### Problema 1: "No encuentro las specs"

**Síntoma:**
```bash
cat .agents/specs/01-proyecto-overview.md
# Error: No such file or directory
```

**Solución:**
```bash
# Leer manual principal
cat .agents/README.md

# O consultar referencia
cat .kiro/specs/01-proyecto-overview.md
```

### Problema 2: "Mi script no funciona"

**Síntoma:**
```bash
./mi-script.sh
# Error: .agents/COORDINACION.md not found
```

**Solución:**
```bash
# Actualizar script para usar nuevo archivo
sed -i 's/.agents\/COORDINACION.md/.agents\/README.md/g' mi-script.sh
```

### Problema 3: "OpenCode no detecta agentes"

**Síntoma:**
```bash
opencode list
# No agents found
```

**Solución:**
```bash
# Sincronizar manualmente
python .agents/hooks/sync_to_opencode.py

# Verificar
cat .opencode/agents.json
```

### Problema 4: "Olvidé cómo funciona todo"

**Solución:**
```bash
# Leer quickstart
cat .agents/QUICKSTART.md

# Leer manual completo
cat .agents/README.md

# Leer resumen de cambios
cat .agents/CHANGELOG.md
```

---

## 📞 Soporte

### Recursos Disponibles

| Recurso | Ubicación | Cuándo Usar |
|---------|-----------|-------------|
| Manual completo | `.agents/README.md` | Siempre |
| Guía rápida | `.agents/QUICKSTART.md` | Inicio rápido |
| Historial de cambios | `.agents/CHANGELOG.md` | Ver qué cambió |
| Guía de migración | `.agents/GUIA-MIGRACION.md` | Este archivo |
| Resumen final | `.agents/RESUMEN-FINAL.md` | Overview completo |

### Comandos Útiles

```bash
# Ver estado de sincronización
python .agents/hooks/sync_status.py

# Sincronizar todo
python .agents/hooks/sync_all.py

# Leer manual
cat .agents/README.md

# Buscar en documentación
grep -r "mi-busqueda" .agents/README.md
```

---

## 🎯 Resumen de Migración

### Cambios Clave

1. **Un solo entry point:** `.agents/README.md` (500+ líneas)
2. **Specs movidos:** `.agents/specs/` → `.kiro/specs/`
3. **Docs consolidados:** `.agents/docs/` → `.agents/README.md`
4. **Coordinación fusionada:** `.agents/COORDINACION.md` → `.agents/README.md`

### Nuevos Archivos

- `.agents/README.md` - Manual completo
- `.agents/QUICKSTART.md` - Guía rápida
- `.agents/agents/` - Definiciones de agentes
- `.agents/prompts/` - Sistema de prompts
- `.opencode/` - Configuración OpenCode

### Archivos Eliminados

- `.agents/specs/*.md` (6 archivos)
- `.agents/COORDINACION.md`
- `.agents/docs/` (19 archivos)

### Tiempo de Migración

- **Lectura:** 5 minutos
- **Actualización:** 2 minutos
- **Verificación:** 1 minuto
- **Actualización de scripts:** 2 minutos
- **Total:** ~10 minutos

---

## ✅ Checklist Final

- [ ] Leí `.agents/README.md`
- [ ] Leí `.agents/CHANGELOG.md`
- [ ] Actualicé mis scripts personalizados
- [ ] Actualicé referencias en documentación
- [ ] Verifiqué sincronización
- [ ] Probé crear un agente nuevo
- [ ] Validé que todo funciona
- [ ] Entendí la nueva arquitectura

---

**¡Migración completada! 🚀**

Ahora tienes una arquitectura portable, limpia y escalable.

---

**Última actualización:** 2025-01-16  
**Versión:** 2.0  
**Autor:** mrtn
