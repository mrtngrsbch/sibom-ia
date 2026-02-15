# 🛠️ Configuración de GitHub Issues y Projects

## 📋 Labels Recomendados

### Tipos de Issue
- `bug` (rojo, #d73a4a) - Algo no funciona
- `enhancement` (azul claro, #a2eeef) - Nueva funcionalidad
- `documentation` (azul, #0075ca) - Mejoras en docs
- `question` (rosa, #d876e3) - Más información necesaria
- `duplicate` (gris, #cfd3d7) - Issue duplicado
- `wontfix` (blanco, #ffffff) - No se trabajará en esto
- `help wanted` (verde, #008672) - Se busca ayuda externa
- `good first issue` (púrpura, #7057ff) - Bueno para principiantes

### Componentes
- `chatbot` (naranja, #fb8500) - Frontend Next.js
- `python-cli` (amarillo, #ffb703) - Scraper Python
- `sat-analysis` (cyan, #219ebc) - API satelital
- `data` (marrón, #8b5a00) - Índices/datos
- `infrastructure` (gris oscuro, #666666) - Docker/CI/CD

### Prioridad
- `priority-high` (rojo oscuro, #b60205) - Urgente
- `priority-medium` (naranja, #d93f0b) - Importante
- `priority-low` (verde, #0e8a16) - Puede esperar

### Estado
- `needs-triage` (amarillo, #fef2c0) - Por revisar
- `blocked` (rojo, #d73a4a) - Bloqueado por algo
- `in-progress` (azul, #0e8a16) - En desarrollo
- `needs-testing` (púrpura, #5319e7) - Listo para testing

### Municipios
- `municipio` (verde agua, #7bed9f) - Relacionado a municipios

---

## 🎯 Issue Templates Configurados

Ya están creados en `.github/ISSUE_TEMPLATE/`:

1. **bug_report.md** - Para reportar bugs
2. **feature_request.md** - Para sugerir features
3. **municipio_request.md** - Para solicitar nuevos municipios
4. **documentation.md** - Para issues de documentación

---

## 🔄 GitHub Projects (opcional)

### Configuración Recomendada

**Tablero Kanban simple:**

```
📋 Backlog    → 🔍 Triaged    → 🚧 In Progress    → ✅ Done
```

**Campos personalizados:**
- **Prioridad**: Alta/Media/Baja
- **Componente**: Chatbot/Python-CLI/Sat-Analysis/Data
- **Estimación**: S/M/L (Small/Medium/Large)
- **Versión objetivo**: v1.2.0, v1.3.0, etc.

### Automatización

GitHub Actions puede mover issues automáticamente:
- Issue cerrado → columna "Done"
- PR mergeado → columna "Done"
- Issue asignado → columna "In Progress"

---

## 📊 Milestones Sugeridos

Crear milestones para trackear releases:

1. **v1.2.0** (Febrero 2026)
   - Descripción: "Exportación y comparación de normativas"
   - Issues: #1, #2, #3

2. **v1.3.0** (Marzo 2026)
   - Descripción: "API pública y widgets embebibles"
   - Issues: #4, #5

3. **v2.0.0** (Q2 2026)
   - Descripción: "Rediseño de API RAG"
   - Issues: #10, #11

---

## 🤖 GitHub Actions Configuradas

Ya están creadas en `.github/workflows/`:

1. **release.yml** - Crear releases automáticamente al pushear tags
2. **pr-validation.yml** - Validar PRs (tests, linting, build)

---

## 📝 Branch Protection (Recomendado)

### Para `main`:

**Settings → Branches → Add rule:**

- [x] Require a pull request before merging
- [x] Require status checks to pass before merging
  - [x] validate-frontend
  - [x] validate-backend
- [x] Require conversation resolution before merging
- [ ] Require signed commits (opcional)
- [x] Include administrators (aplicar reglas a ti también)

**Permite commits directos solo para:**
- Hotfixes urgentes
- Cambios de documentación menores

---

## 🎨 Issue Templates Usage

### Para Usuarios

Al crear un issue, GitHub mostrará:

```
Choose an issue template:

🐛 Reporte de Bug
   Reportar un problema o comportamiento inesperado

✨ Feature Request
   Sugerir una nueva funcionalidad

📄 Municipio Faltante
   Solicitar agregar un nuevo municipio

📚 Documentación
   Reportar problemas en la documentación
```

Esto guía a los usuarios a proporcionar información completa.

---

## 🚀 Workflow Completo

### 1. Usuario reporta bug:
```
Usuario crea issue → Auto-label "needs-triage"
                   → Notificación a maintainer
                   → Maintainer revisa en 24-48h
                   → Asigna labels (bug, prioridad, componente)
                   → Asigna milestone (si aplica)
```

### 2. Contributor trabaja en feature:
```
Contributor crea issue → Discusión de diseño
                       → Aprobación del maintainer
                       → Contributor hace PR
                       → CI/CD valida automáticamente
                       → Code review
                       → Merge a main
                       → Auto-close issue
```

### 3. Mantenedor crea release:
```
Commits acumulados → Script bump-version.sh
                   → Actualiza package.json + CHANGELOG
                   → Commit + Tag push
                   → GitHub Actions crea release
                   → Notificación automática (opcional)
```

---

## 📈 Métricas para Trackear

### Issues
- Issues abiertos vs cerrados
- Tiempo promedio de respuesta
- Tiempo promedio de resolución
- Issues por label/componente

### Pull Requests
- PRs abiertos vs merged
- Tiempo promedio de review
- Tamaño promedio de PR (líneas cambiadas)
- PRs de colaboradores externos vs internos

### Releases
- Frecuencia de releases (por mes)
- Tiempo entre releases
- Número de issues cerrados por release

---

## 🔧 Scripts Útiles

### Crear un Release

```bash
# Automatizado
./scripts/bump-version.sh minor

# Manual
git tag v1.2.0
git push origin v1.2.0
```

### Listar Issues por Label

```bash
gh issue list --label bug --state open
gh issue list --label "good first issue"
```

### Ver Estadísticas

```bash
gh issue list --state all --json state,labels,createdAt | \
  jq 'group_by(.state) | map({state: .[0].state, count: length})'
```

---

## 📚 Referencias

- [GitHub Issues Docs](https://docs.github.com/en/issues)
- [GitHub Projects Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)

---

**Última actualización:** 2026-02-14  
**Mantenedor:** @mrtn
