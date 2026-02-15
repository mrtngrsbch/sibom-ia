# Sistema de Versionado - SIBOM IA

**Fecha de implementación:** 2026-02-14  
**Estrategia:** Semantic Versioning (SemVer) 2.0.0

---

## 📋 Resumen Ejecutivo

Este proyecto usa **Versionado Semántico** siguiendo el estándar [SemVer 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
```

- **MAJOR** (1.x.x): Cambios incompatibles (breaking changes)
- **MINOR** (x.1.x): Nuevas funcionalidades compatibles
- **PATCH** (x.x.1): Correcciones de bugs

**Versión actual:** `1.1.0` (definida en `chatbot/package.json`)

---

## 🎯 Filosofía: Vibe Coding + Orden Incremental

Este proyecto es mantenido por una sola persona con estilo **vibe coding** (desarrollo fluido y pragmático), pero necesita estructura para escalar. El sistema de versionado está diseñado para ser:

1. **Simple**: No requiere overhead administrativo excesivo
2. **Automático**: GitHub Actions maneja releases automáticamente
3. **Informativo**: El CHANGELOG documenta cada cambio importante
4. **Visible**: La versión se muestra en el chatbot

---

## 🔄 Workflow de Desarrollo

### Dos Opciones Disponibles

**🤖 Opción A: Automático (Recomendado)**
- Release Please gestiona todo automáticamente
- Solo haces commits y mergeas PRs
- Ver: [docs/AUTOMATED_RELEASES.md](docs/AUTOMATED_RELEASES.md)

**🛠️ Opción B: Manual (Más control)**
- Tú decides cuándo y cómo incrementar versiones
- Más trabajo pero más control
- Ver instrucciones abajo

---

### 1. Desarrollo Diario (Vibe Coding)

```bash
# 1. Trabaja en main o crea una branch
git checkout -b feature/nombre-descriptivo

# 2. Haz commits atómicos descriptivos
git commit -m "feat: agregar análisis satelital de anegamiento"
git commit -m "fix: corregir búsqueda BM25 con acentos"
git commit -m "docs: actualizar README con nuevos municipios"

# 3. Push cuando quieras
git push origin feature/nombre-descriptivo
```

### 2. Crear un Release (cuando sea necesario)

**Opción A: Automática (Recomendada)**

```bash
# 1. Decidir tipo de cambio
git tag v1.2.0  # MINOR: nueva funcionalidad
git tag v1.1.1  # PATCH: bug fix
git tag v2.0.0  # MAJOR: breaking change

# 2. GitHub Actions crea el release automáticamente
git push origin v1.2.0
```

**Opción B: Manual (para más control)**

1. Actualizar versión en `chatbot/package.json`:
   ```json
   {
     "version": "1.2.0"
   }
   ```

2. Actualizar `CHANGELOG.md` con los cambios

3. Crear PR con título: `chore: release v1.2.0`

4. Después de merge, crear tag:
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

### 3. Estructura de Branches (simplificada)

```
main            ← Producción (siempre estable)
  ├─ feature/*  ← Nuevas funcionalidades
  ├─ fix/*      ← Correcciones de bugs
  ├─ refactor/* ← Refactorización/mejoras
  └─ docs/*     ← Documentación
```

**Reglas:**
- `main` siempre debe funcionar (no pushear código roto)
- Features grandes: usar branch + PR
- Fixes urgentes: commit directo a main (luego documentar)

---

## 📝 Convenciones de Commits (Conventional Commits)

Seguir el formato:

```
<tipo>(<scope>): <descripción corta>

[cuerpo opcional]

[footer opcional]
```

### Tipos válidos:

| Tipo | Descripción | Incrementa |
|------|-------------|------------|
| `feat` | Nueva funcionalidad | MINOR |
| `fix` | Corrección de bug | PATCH |
| `docs` | Cambios en documentación | - |
| `style` | Formato (sin cambios lógicos) | - |
| `refactor` | Refactorización | - |
| `perf` | Mejoras de performance | PATCH |
| `test` | Agregar/modificar tests | - |
| `chore` | Tareas de mantenimiento | - |
| `build` | Cambios en build/dependencias | - |
| `ci` | Cambios en CI/CD | - |

### Breaking Changes:

```
feat!: cambiar API de búsqueda RAG

BREAKING CHANGE: El método `search()` ahora requiere un objeto de filtros
en lugar de parámetros separados.
```

Esto incrementa **MAJOR** (ej: 1.x.x → 2.0.0)

---

## 🎯 Cuándo Incrementar Cada Versión

### MAJOR (x.0.0) - Breaking Changes

Ejemplos:
- Cambiar API pública del chatbot
- Modificar estructura de índices JSON (incompatible con versiones anteriores)
- Cambiar formato de respuestas
- Eliminar endpoints/funcionalidades

**Frecuencia esperada:** 1-2 veces al año

### MINOR (1.x.0) - Nuevas Funcionalidades

Ejemplos:
- Agregar análisis satelital
- Nuevo tipo de documento soportado (ej: presupuestos)
- Agregar filtros avanzados al chat
- Integrar nuevo municipio (si es un grupo grande)

**Frecuencia esperada:** 1-2 veces al mes

### PATCH (1.1.x) - Bug Fixes

Ejemplos:
- Corregir búsqueda con acentos
- Fix en formateo de fechas
- Mejorar manejo de errores
- Optimizar performance sin cambiar funcionalidad

**Frecuencia esperada:** Semanalmente (según necesidad)

---

## 🔧 Sincronización de Versiones

El proyecto es un monorepo con 3 componentes:

```
chatbot/          ← package.json (versión principal)
python-cli/       ← pyproject.toml (sin version, usa git tags)
sat-analysis/     ← No tiene versión (API interna)
```

**Regla:** La versión del chatbot (`package.json`) es la **versión oficial del proyecto**.

### Cómo sincronizar:

1. **Manual:**
   ```bash
   # Actualizar version en package.json
   nano chatbot/package.json  # Cambiar "version": "1.2.0"
   
   # Commit y tag
   git commit -am "chore: bump version to 1.2.0"
   git tag v1.2.0
   git push origin main --tags
   ```

2. **Automático (con script):**
   ```bash
   # Crear scripts/bump-version.sh
   ./scripts/bump-version.sh minor  # 1.1.0 → 1.2.0
   ./scripts/bump-version.sh patch  # 1.1.0 → 1.1.1
   ./scripts/bump-version.sh major  # 1.1.0 → 2.0.0
   ```

---

## 🤖 Automatización con GitHub Actions

### Release Automático

Cuando haces push de un tag `v*`, GitHub Actions:

1. Lee la versión del tag (ej: `v1.2.0`)
2. Extrae los cambios del CHANGELOG
3. Crea un GitHub Release con notas automáticas
4. (Opcional) Deploya a Vercel/producción

Ver: `.github/workflows/release.yml`

### Validación de PR

Cada PR corre:
- Tests del chatbot (Vitest)
- Linting (ESLint, Ruff)
- Type checking (TypeScript)
- Build exitoso

Ver: `.github/workflows/pr-validation.yml`

---

## 📊 Mostrar Versión en el Producto

La versión se muestra en el Sidebar del chatbot:

```tsx
// chatbot/src/components/layout/Sidebar.tsx
<div className="text-xs text-slate-400">
  v{packageJson.version} • {stats?.totalDocuments || 0} docs
</div>
```

Se lee dinámicamente desde `package.json` en build time.

---

## 🚀 Migración desde "Sin Sistema"

### Estado Actual (antes de esta guía)

- Commits directos a main sin estructura
- No hay tags/releases formales
- No hay CHANGELOG
- Versión `1.1.0` existente pero no documentada

### Plan de Migración

1. **Semana 1:** Documentación (este archivo) ✅
2. **Semana 2:** Implementar CHANGELOG + widget de versión
3. **Semana 3:** Configurar GitHub Actions
4. **Semana 4:** Crear primer release formal (ej: v1.2.0)

### Compatibilidad con Estilo Actual

Puedes seguir haciendo:
- Commits directos a main (para fixes rápidos)
- Desarrollo rápido sin burocracia
- Documentar después (CHANGELOG actualizado semanalmente)

Lo único nuevo:
- Al terminar una feature grande → Crear release
- Commits más descriptivos (beneficio: mejor historial)

---

## 📚 Recursos

- **SemVer spec:** https://semver.org/
- **Conventional Commits:** https://www.conventionalcommits.org/
- **Keep a Changelog:** https://keepachangelog.com/

---

## ✅ Checklist para Crear un Release

```markdown
- [ ] Todos los tests pasan localmente
- [ ] Decidir tipo de versión (MAJOR/MINOR/PATCH)
- [ ] Actualizar chatbot/package.json con nueva versión
- [ ] Actualizar CHANGELOG.md con cambios importantes
- [ ] Commit: `chore: release v1.X.X`
- [ ] Push a main
- [ ] Crear tag: `git tag v1.X.X`
- [ ] Push tag: `git push origin v1.X.X`
- [ ] Verificar GitHub Release automático
- [ ] (Opcional) Anunciar en redes/usuarios
```

---

**Ejemplos de Releases Esperados:**

- `v1.1.1` - Fix búsqueda con acentos (PATCH)
- `v1.2.0` - Agregar análisis satelital (MINOR)
- `v1.3.0` - Soporte para presupuestos municipales (MINOR)
- `v1.4.0` - Dashboard de analytics (MINOR)
- `v2.0.0` - Rediseño completo de API RAG (MAJOR)

---

**Última actualización:** 2026-02-14  
**Mantenido por:** @mrtn (solo dev)  
**Estado:** 🟢 Activo
