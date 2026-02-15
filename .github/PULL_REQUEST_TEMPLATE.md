---
name: Pull Request
about: Template para PRs
title: ''
assignees: ''
---

## 📋 Tipo de Cambio

- [ ] 🐛 Bug fix (no rompe funcionalidad existente)
- [ ] ✨ Nueva funcionalidad (no rompe funcionalidad existente)
- [ ] 💥 Breaking change (funcionalidad existente se ve afectada)
- [ ] 📚 Documentación
- [ ] 🔧 Refactoring (sin cambios funcionales)
- [ ] ⚡ Mejora de performance
- [ ] ✅ Agregar/actualizar tests

## 📝 Descripción

**¿Qué hace este PR?**

Una descripción clara de los cambios realizados.

**¿Por qué es necesario?**

Contexto o issue relacionado.

**Issue(s) relacionado(s):**
Fixes #(issue number)
Closes #(issue number)

## 🔬 Cómo se probó

Describe los tests que ejecutaste para verificar tus cambios:

- [ ] Tests unitarios (Vitest/pytest)
- [ ] Tests de integración
- [ ] Tests manuales
- [ ] Tests en múltiples navegadores (si aplica)
- [ ] Tests con diferentes municipios

**Detalles de testing:**
```
Describe los pasos seguidos para probar
```

## 📸 Screenshots (si aplica)

Agrega screenshots del antes/después si hay cambios visuales.

**Antes:**
[Screenshot]

**Después:**
[Screenshot]

## 🔄 Cambios en la Base de Datos/Índices

- [ ] Este PR modifica el formato de índices
- [ ] Este PR requiere re-scraping de datos
- [ ] Este PR requiere migración de datos
- [ ] No hay cambios en datos

**Si hay cambios, describe el plan de migración:**
```
...
```

## 📦 Dependencias

- [ ] Este PR agrega nuevas dependencias
- [ ] Este PR elimina dependencias
- [ ] No hay cambios en dependencias

**Si hay cambios, lista las dependencias:**
```json
{
  "nueva-libreria": "^1.0.0"
}
```

## ⚠️ Breaking Changes

- [ ] Este PR introduce breaking changes

**Si los introduce, describe:**
- Qué se rompe
- Cómo migrar código existente
- Si requiere actualizar versión MAJOR

## 🔐 Consideraciones de Seguridad

- [ ] Este PR maneja datos sensibles
- [ ] Este PR expone nuevos endpoints
- [ ] Este PR modifica autenticación/autorización
- [ ] No hay impacto de seguridad

## 📊 Impacto en Performance

- [ ] Mejora performance
- [ ] Sin impacto en performance
- [ ] Puede impactar performance negativamente

**Si hay impacto, describe:**
```
Benchmarks o mediciones
```

## ✅ Checklist de Desarrollo

### Código
- [ ] Mi código sigue las convenciones del proyecto
- [ ] He revisado mi propio código
- [ ] He comentado código complejo cuando es necesario
- [ ] Mis cambios no generan warnings nuevos
- [ ] He actualizado tipos TypeScript (si aplica)

### Tests
- [ ] He agregado tests que prueban mi cambio
- [ ] Todos los tests existentes pasan
- [ ] Tests unitarios cubren casos edge
- [ ] Tests de integración pasan

### Documentación
- [ ] He actualizado la documentación
- [ ] He actualizado el CHANGELOG.md
- [ ] He actualizado JSDoc/docstrings
- [ ] He actualizado README (si aplica)

### Build
- [ ] Build local pasa exitosamente
- [ ] No hay errores de TypeScript
- [ ] Linter pasa sin errores (ESLint/Ruff)
- [ ] Formateador aplicado (Prettier/Black)

### Deployment
- [ ] Cambios son compatibles con producción
- [ ] Variables de entorno documentadas (si hay nuevas)
- [ ] Instrucciones de deployment actualizadas (si aplica)

## 🎯 Versionado

**¿Este PR debería incrementar la versión?**
- [ ] MAJOR (v2.0.0) - Breaking changes
- [ ] MINOR (v1.X.0) - Nueva funcionalidad
- [ ] PATCH (v1.1.X) - Bug fix
- [ ] No incrementa versión (docs/refactor menor)

**Versión objetivo:** v___.___.___

## 📝 Notas para el Reviewer

Información adicional que el reviewer debería saber:
- Áreas específicas donde necesitas feedback
- Decisiones de diseño tomadas
- Trade-offs considerados
- Limitaciones conocidas

## 🚀 Plan de Rollout (si aplica)

**Para cambios grandes:**
- [ ] Feature flag implementado
- [ ] Rollout gradual planeado
- [ ] Plan de rollback definido
- [ ] Monitoreo configurado

## 📎 Referencias

Links a:
- Issues relacionados
- PRs relacionados
- Documentación externa
- Diseños en Figma/etc
- Tickets de proyecto

---

/cc @mrtn <!-- Opcional: mencionar reviewers -->
