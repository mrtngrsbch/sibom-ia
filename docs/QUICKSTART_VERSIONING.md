# 🚀 Quickstart: Sistema de Versionado y GitHub

Guía rápida para empezar a usar el nuevo sistema de versionado profesional.

---

## ✅ Lo que ya está listo

- ✅ Versionado semántico configurado (v1.1.0)
- ✅ Widget de versión en el chatbot (Sidebar)
- ✅ CHANGELOG.md para documentar cambios
- ✅ GitHub Actions para releases automáticos
- ✅ Templates de Issues y PRs
- ✅ Script automatizado para bump de versión
- ✅ Documentación completa

---

## 🎯 Workflows Principales

### 1. Desarrollo Diario (Vibe Coding)

**Sigue trabajando como siempre, solo mejora los commits:**

```bash
# Antes (está bien, pero podría ser mejor)
git commit -m "cambios en el chat"

# Ahora (más descriptivo, mejor historial)
git commit -m "feat(chat): agregar filtro por rango de fechas"
git commit -m "fix(scraper): corregir parsing de tablas"
git commit -m "docs: actualizar README"
```

**Tipos de commit:**
- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Documentación
- `refactor:` - Refactorización
- `perf:` - Mejora de performance
- `chore:` - Tareas de mantenimiento

### 2. Crear un Release

**🤖 OPCIÓN A: AUTOMÁTICO (Recomendado) - Sin Intervención**

**Release Please** hace todo por ti:

```bash
# 1. Haces commits normales
git commit -m "feat: nueva funcionalidad"
git commit -m "fix: corregir bug"
git push origin main

# 2. GitHub Actions crea/actualiza un PR automático
#    Título: "chore(main): release 1.2.0"
#    Contenido: package.json + CHANGELOG actualizados

# 3. Cuando quieras hacer release, merge el PR:
#    - Desde GitHub UI: Click en "Merge pull request"
#    - O desde CLI: gh pr merge --squash

# 4. ¡Listo! GitHub crea el release automáticamente 🎉
```

**Ver más:** [docs/AUTOMATED_RELEASES.md](docs/AUTOMATED_RELEASES.md)

---

**🛠️ OPCIÓN B: MANUAL (para más control) - Con Intervención**

Si prefieres controlar todo manualmente:

**Opción A: Script Automático (Recomendado)**

```bash
# Decide qué tipo de versión
./scripts/bump-version.sh minor   # 1.1.0 → 1.2.0 (nueva funcionalidad)
./scripts/bump-version.sh patch   # 1.1.0 → 1.1.1 (bug fix)
./scripts/bump-version.sh major   # 1.1.0 → 2.0.0 (breaking change)

# El script:
# 1. Actualiza package.json
# 2. Actualiza CHANGELOG.md (con TODOs)
# 3. Crea commit
# 4. Crea tag

# Luego edita el CHANGELOG para completar los cambios reales:
nano CHANGELOG.md

# Push todo
git push origin main --tags
```

**Opción B: Manual**

```bash
# 1. Editar chatbot/package.json
nano chatbot/package.json  # Cambiar "version": "1.2.0"

# 2. Editar CHANGELOG.md
nano CHANGELOG.md  # Agregar sección [1.2.0]

# 3. Commit
git commit -am "chore: release v1.2.0"

# 4. Tag
git tag v1.2.0

# 5. Push
git push origin main --tags
```

### 3. GitHub Actions Automático

**Cuando haces push del tag, GitHub Actions:**
1. Extrae los cambios del CHANGELOG
2. Crea un GitHub Release
3. Genera notas de release automáticas

**Ver releases:**
```
https://github.com/TU-USUARIO/sibom-scraper-assistant/releases
```

---

## 🏷️ Cuándo Incrementar Cada Versión

| Tipo | Cuándo | Ejemplo |
|------|--------|---------|
| **MAJOR** (2.0.0) | Cambios que rompen compatibilidad | Cambiar API de búsqueda |
| **MINOR** (1.X.0) | Nueva funcionalidad compatible | Agregar análisis satelital |
| **PATCH** (1.1.X) | Bug fixes | Corregir búsqueda con acentos |

**Frecuencia esperada:**
- MAJOR: 1-2 veces al año
- MINOR: 1-2 veces al mes
- PATCH: Semanalmente (según necesidad)

---

## 📝 Usar GitHub Issues

### Crear un Issue

```bash
# Ir a GitHub
# → Issues → New Issue
# → Seleccionar template:
#   - 🐛 Bug Report
#   - ✨ Feature Request
#   - 📄 Municipio Faltante
#   - 📚 Documentación
```

### Listar Issues (CLI)

```bash
# Instalar GitHub CLI si no lo tienes
brew install gh
gh auth login

# Ver issues abiertos
gh issue list

# Ver issues por label
gh issue list --label bug
gh issue list --label "good first issue"

# Crear issue desde CLI
gh issue create --title "Bug en búsqueda" --body "Descripción..."
```

---

## 🔀 Usar Pull Requests

### Workflow Básico

```bash
# 1. Crear branch
git checkout -b feature/nombre-descriptivo

# 2. Hacer cambios
# ...editar archivos...

# 3. Commit
git commit -m "feat: agregar nueva funcionalidad"

# 4. Push
git push origin feature/nombre-descriptivo

# 5. Crear PR en GitHub
# → Pull Requests → New PR
# → Completar template
```

### PR desde CLI

```bash
gh pr create --title "feat: agregar X" --body "Descripción..."
gh pr list
gh pr view 123
gh pr merge 123
```

---

## 🔍 Verificar Estado del Proyecto

### Ver versión actual

```bash
# En código
cat chatbot/package.json | grep version

# En el chatbot (Sidebar)
# La versión se muestra automáticamente: v1.1.0
```

### Ver historial de cambios

```bash
cat CHANGELOG.md
```

### Ver releases

```bash
gh release list
gh release view v1.1.0
```

---

## 🎨 Configurar GitHub (Primera Vez)

### 1. Labels

```bash
# Opción A: Crear manualmente en GitHub
# Settings → Issues → Labels → New label

# Opción B: Con GitHub CLI
gh label create "bug" --color "d73a4a" --description "Algo no funciona"
gh label create "enhancement" --color "a2eeef" --description "Nueva funcionalidad"
gh label create "chatbot" --color "fb8500" --description "Frontend Next.js"
# ...etc (ver docs/GITHUB_SETUP.md para lista completa)
```

### 2. Branch Protection (main)

```
Settings → Branches → Add rule
Branch name pattern: main
✅ Require a pull request before merging
✅ Require status checks to pass
✅ Require conversation resolution
```

### 3. Secrets (para GitHub Actions)

```
Settings → Secrets and variables → Actions → New repository secret
```

**Secrets necesarios:**
- `OPENROUTER_API_KEY` - Para builds del chatbot
- `DISCORD_WEBHOOK_URL` - (Opcional) Para notificaciones

---

## 📚 Documentación Completa

| Archivo | Descripción |
|---------|-------------|
| [docs/VERSIONING.md](docs/VERSIONING.md) | Sistema de versionado completo |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guía de contribución |
| [docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md) | Configuración de GitHub |

---

## 🛠️ Comandos Útiles

### Desarrollo

```bash
# Ver cambios desde último tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Ver estadísticas de commits
git shortlog -sn HEAD

# Ver tamaño del proyecto
cloc . --exclude-dir=node_modules,.next,venv
```

### Versioning

```bash
# Ver versión actual
cat chatbot/package.json | jq .version

# Listar tags
git tag -l

# Ver cambios entre versiones
git diff v1.0.0..v1.1.0
```

### GitHub

```bash
# Ver issues abiertos de alta prioridad
gh issue list --label priority-high --state open

# Ver PRs pendientes
gh pr list --state open

# Ver estadísticas del repo
gh api repos/:owner/:repo --jq '.stargazers_count, .forks_count, .open_issues_count'
```

---

## ❓ FAQ Rápido

**¿Tengo que usar branches para todo?**
No. Para fixes rápidos puedes seguir commiteando a main. Usa branches para features grandes.

**¿Tengo que crear release cada cambio?**
No. Crea releases cuando tengas varios cambios acumulados (cada 1-2 semanas).

**¿Qué pasa si se me olvida un cambio en el CHANGELOG?**
Puedes editarlo después y hacer push de un commit: `chore: update changelog`

**¿Puedo seguir con mi estilo de desarrollo?**
Sí. Este sistema agrega orden gradual sin cambiar tu workflow drásticamente.

**¿GitHub Actions es gratis?**
Sí, para repos públicos. Para privados tienes 2000 minutos/mes gratis.

---

## 🎯 Próximos Pasos Sugeridos

1. [ ] Prueba el script de bump: `./scripts/bump-version.sh patch`
2. [ ] Edita CHANGELOG.md con cambios reales
3. [ ] Push tag: `git push origin --tags`
4. [ ] Verifica que GitHub Actions creó el release
5. [ ] Configura labels en GitHub (ver GITHUB_SETUP.md)
6. [ ] Crea tu primer issue como prueba
7. [ ] Comparte el link del proyecto

---

## 🌟 Resultado Final

**Antes:**
- Commits sin estructura
- No hay releases formales
- Versión oculta
- Difícil trackear cambios

**Ahora:**
- ✅ Commits descriptivos (Conventional Commits)
- ✅ Releases automáticos con CHANGELOG
- ✅ Versión visible en el chatbot
- ✅ Issues y PRs organizados
- ✅ GitHub Actions para CI/CD
- ✅ Documentación completa

---

**¿Necesitas ayuda?**
- Lee [CONTRIBUTING.md](CONTRIBUTING.md)
- Crea un issue con label "question"
- Contacta: [tu-email]

---

**Última actualización:** 2026-02-14  
**Versión:** 1.0
