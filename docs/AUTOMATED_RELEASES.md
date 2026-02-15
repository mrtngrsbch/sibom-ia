# 🤖 Sistema de Releases Automáticos

**Release Please** automatiza completamente el proceso de versionado y releases.

---

## ✨ Cómo Funciona

### 1. Haces commits normales

```bash
git commit -m "feat: agregar análisis de anegamiento"
git commit -m "fix: corregir búsqueda con acentos"
git commit -m "docs: actualizar README"
git push origin main
```

### 2. Release Please analiza automáticamente

Cada push a `main` ejecuta GitHub Actions que:
- **Lee todos los commits** desde el último release
- **Detecta el tipo de bump** necesario:
  - `feat:` → MINOR bump (1.1.0 → 1.2.0)
  - `fix:` → PATCH bump (1.1.0 → 1.1.1)
  - `feat!:` o `BREAKING CHANGE:` → MAJOR bump (1.1.0 → 2.0.0)
- **Genera CHANGELOG** automáticamente
- **Crea/actualiza un PR** llamado "chore(main): release X.X.X"

### 3. El PR contiene:

- ✅ Version bump en `chatbot/package.json`
- ✅ CHANGELOG.md actualizado con todos los cambios
- ✅ Commits agrupados por tipo
- ✅ Links a commits y issues

**El PR se actualiza automáticamente** cada vez que pusheas nuevos commits a main.

### 4. Cuando estés listo para release:

```bash
# Opción A: Merge desde GitHub UI
# Click en "Merge pull request" en el PR de release

# Opción B: Merge desde CLI
gh pr merge --auto --squash
```

### 5. Al mergear el PR:

**Release Please automáticamente:**
- ✅ Crea un GitHub Release
- ✅ Crea un tag git (ej: v1.2.0)
- ✅ Adjunta las notas del CHANGELOG
- ✅ Notifica (si configuraste Discord/Slack)

---

## 🎯 Workflow Completo (Sin Intervención)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Desarrollo Normal                                            │
│                                                                 │
│  • Haces commits con conventional commits                      │
│  • Pusheas a main cuando quieras                               │
│  • NO necesitas pensar en versiones manualmente                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. GitHub Actions (Automático)                                 │
│                                                                 │
│  • Cada push ejecuta Release Please                            │
│  • Analiza commits (feat/fix/breaking)                         │
│  • Calcula próxima versión                                     │
│  • Crea/actualiza PR de release                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. PR de Release (Automático)                                  │
│                                                                 │
│  Título: "chore(main): release 1.2.0"                          │
│                                                                 │
│  Contenido:                                                     │
│  • chatbot/package.json: "version": "1.2.0"                    │
│  • CHANGELOG.md actualizado                                     │
│  • Commits agrupados:                                           │
│    ✨ Nuevas Funcionalidades                                    │
│      - feat: análisis satelital                                 │
│      - feat: filtros avanzados                                  │
│    🐛 Correcciones                                              │
│      - fix: búsqueda con acentos                                │
│                                                                 │
│  Estado: ✅ Checks pasando (CI/CD)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. TÚ: Merge cuando quieras release                            │
│                                                                 │
│  • Revisas el PR (opcional)                                     │
│  • Click "Merge pull request"                                   │
│  • Listo! 🎉                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Release Creado (Automático)                                 │
│                                                                 │
│  • GitHub Release publicado: v1.2.0                             │
│  • Tag creado: v1.2.0                                           │
│  • CHANGELOG incluido en release notes                          │
│  • (Opcional) Deploy a producción                               │
│  • (Opcional) Notificación Discord/Slack                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Tipos de Commits y Versioning

Release Please determina automáticamente el bump:

| Commit | Bump | Ejemplo |
|--------|------|---------|
| `feat:` | MINOR | 1.1.0 → 1.2.0 |
| `fix:` | PATCH | 1.1.0 → 1.1.1 |
| `perf:` | PATCH | 1.1.0 → 1.1.1 |
| `refactor:` | PATCH | 1.1.0 → 1.1.1 |
| `feat!:` | MAJOR | 1.1.0 → 2.0.0 |
| `BREAKING CHANGE:` | MAJOR | 1.1.0 → 2.0.0 |
| `docs:`, `chore:`, etc | No bump | No crea release |

### Ejemplo de Breaking Change

```bash
git commit -m "feat!: cambiar API de búsqueda

BREAKING CHANGE: El método search() ahora requiere objeto de filtros.
Migración: Cambiar search(query, filters) por search({ query, ...filters })
"
```

Esto causará bump de 1.x.x → 2.0.0

---

## 🎨 Personalización

### Modificar Secciones del CHANGELOG

Edita `release-please-config.json`:

```json
{
  "changelog-sections": [
    {"type": "feat", "section": "✨ Lo Nuevo", "hidden": false},
    {"type": "fix", "section": "🔧 Arreglos", "hidden": false},
    {"type": "perf", "section": "🚀 Más Rápido", "hidden": false}
  ]
}
```

### Cambiar Comportamiento de Bump

```json
{
  "bump-minor-pre-major": true,     // 0.x.x permite MINOR
  "bump-patch-for-minor-pre-major": false,
  "draft": false,                   // Release público
  "prerelease": false               // No es pre-release
}
```

### Agregar Más Archivos para Actualizar

```json
{
  "extra-files": [
    "chatbot/package.json",
    "python-cli/version.py",  // Ejemplo
    "README.md"               // Actualizar version badge
  ]
}
```

---

## 🔔 Notificaciones Automáticas

### Discord

1. **Crear webhook en Discord:**
   - Server Settings → Integrations → Webhooks → New Webhook
   - Copiar URL

2. **Agregar a GitHub Secrets:**
   ```
   Settings → Secrets and variables → Actions
   → New repository secret
   Name: DISCORD_WEBHOOK_URL
   Value: https://discord.com/api/webhooks/...
   ```

3. **Listo!** Recibirás notificaciones automáticas de releases

### Slack (similar)

```yaml
- name: Notificar en Slack
  if: ${{ steps.release.outputs.release_created }}
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "🚀 Nueva versión: ${{ steps.release.outputs.version }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 🚀 Deploy Automático (Opcional)

### Deploy a Vercel al hacer release

Agrega a `.github/workflows/release-please.yml`:

```yaml
- name: Deploy a Vercel
  if: ${{ steps.release.outputs.release_created }}
  uses: amondnet/vercel-action@v25
  with:
    vercel-token: ${{ secrets.VERCEL_TOKEN }}
    vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
    vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
    vercel-args: '--prod'
    working-directory: ./chatbot
```

---

## 🔍 Ver Estado del Release

### En GitHub

```
Pull Requests → Buscar "chore(main): release"
```

Verás el PR con:
- ✅ Todos los cambios desde último release
- ✅ Version bump calculada
- ✅ CHANGELOG generado
- ✅ Checks de CI/CD

### Con GitHub CLI

```bash
# Ver PR de release actual
gh pr list --label "autorelease: pending"

# Ver contenido del PR
gh pr view <numero>

# Ver diff del CHANGELOG
gh pr diff <numero> -- CHANGELOG.md

# Merge cuando estés listo
gh pr merge <numero> --squash --auto
```

---

## 📊 Frecuencia de Releases

**Recomendaciones por tipo de proyecto:**

### Desarrollo Activo (actual)
- **PR de release:** Se actualiza en cada push
- **Release real:** Cada 1-2 semanas (cuando mergeas el PR)
- **Ventaja:** Acumulas varios cambios antes de release

### Continuous Deployment
- **Release:** Inmediatamente después de cada feature
- **Cómo:** Auto-merge el PR después de cada cambio importante
- **Ventaja:** Usuarios ven cambios más rápido

### Estable/Producción
- **Release:** Cada 1-2 meses
- **Acumular:** Muchos cambios entre releases
- **Ventaja:** Menos disrupciones

**Tu caso (vibe coding):** Recomiendo cada 1-2 semanas.

---

## 🛠️ Troubleshooting

### El PR de release no se crea

**Causas posibles:**
1. No hay commits con `feat:` o `fix:` desde último release
2. Commits solo tienen `docs:`, `chore:`, etc (no causan bump)
3. Ya existe un PR de release abierto

**Solución:**
```bash
# Ver último release
gh release view --json tagName

# Ver commits desde entonces
git log v1.1.0..HEAD --oneline

# Si solo hay docs/chore, hacer un feat o fix
git commit -m "feat: pequeña mejora para triggear release"
```

### El CHANGELOG no tiene mis cambios

**Causa:** Commits no siguen Conventional Commits

**Solución:**
```bash
# Mal
git commit -m "cambios en el chat"

# Bien
git commit -m "feat(chat): agregar nuevo filtro"
```

### Quiero cambiar el número de versión manualmente

```bash
# Editar .release-please-manifest.json
{
  ".": "2.0.0"  # Forzar próxima versión
}

# Commit y push
git add .release-please-manifest.json
git commit -m "chore: forzar versión a 2.0.0"
git push
```

---

## 💡 Tips Pro

### 1. Combinar Múltiples Features

```bash
# Trabajar en branch
git checkout -b feature/multiple-changes

# Hacer varios commits
git commit -m "feat: feature A"
git commit -m "feat: feature B"
git commit -m "fix: bug C"

# Merge a main con squash (un solo commit)
git checkout main
git merge --squash feature/multiple-changes
git commit -m "feat: agregar features A y B con fix C"
```

Release Please verá un solo commit y hará MINOR bump.

### 2. Release Candidates (Pre-releases)

```json
// release-please-config.json
{
  "prerelease": true,
  "prerelease-type": "beta"
}
```

Generará versiones: `1.2.0-beta.1`, `1.2.0-beta.2`, etc.

### 3. Changelog Solo con Highlights

Oculta commits menores:

```json
{
  "changelog-sections": [
    {"type": "feat", "section": "✨ Nuevas Funcionalidades", "hidden": false},
    {"type": "fix", "section": "🐛 Correcciones", "hidden": false},
    {"type": "perf", "section": "⚡ Performance", "hidden": false},
    {"type": "*", "hidden": true}  // Todo lo demás oculto
  ]
}
```

---

## ✅ Resumen

| Tarea | Antes (Manual) | Ahora (Automático) |
|-------|---------------|-------------------|
| Decidir versión | Tú calculas | Release Please calcula |
| Actualizar package.json | Editar manualmente | Automático en PR |
| Escribir CHANGELOG | Escribir manualmente | Generado automáticamente |
| Crear tag | `git tag v1.2.0` | Automático al merge |
| Crear release | GitHub Actions | Automático al merge |
| Deploy | Manual | Automático (opcional) |

**Tu única acción:** Merge el PR cuando quieras hacer release. ¡Eso es todo! 🎉

---

## 📚 Referencias

- [Release Please Docs](https://github.com/googleapis/release-please)
- [Conventional Commits Spec](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

**Última actualización:** 2026-02-15  
**Estado:** ✅ Configurado y listo para usar
