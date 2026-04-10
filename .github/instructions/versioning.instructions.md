---
description: "Use when implementing new features, enhancements, bug fixes, or any functional change to mangrullo. Enforces version bump in .release-please-manifest.json and chatbot/package.json so the current version shows correctly in the Sidebar frontpage."
---

# Versionado de Mangrullo

Cada vez que se implementen cambios funcionales, se deben actualizar la versión del proyecto. La versión canónica vive en `.release-please-manifest.json` y se refleja en la UI del Sidebar a través de `chatbot/package.json`.

## Cuándo aplicar

- Nueva funcionalidad o característica (`feat`)
- Mejora observable de una funcionalidad existente
- Corrección de bug que afecte al usuario final (`fix`)
- Cambio de comportamiento en cualquier componente

No aplica para: refactoring interno sin cambio de comportamiento, correcciones de tipos/linting, actualizaciones de dependencias menores, cambios de docs.

## Reglas de Versionado Semántico

| Tipo de cambio | Bump | Ejemplo |
|---|---|---|
| Nueva funcionalidad | **minor** | `1.1.0` → `1.2.0` |
| Corrección de bug | **patch** | `1.1.0` → `1.1.1` |
| Cambio incompatible (breaking) | **major** | `1.1.0` → `2.0.0` |

## Archivos a actualizar siempre (en este orden)

### 1. `.release-please-manifest.json` — versión canónica

```json
{
  ".": "1.2.0"
}
```

### 2. `chatbot/package.json` — debe coincidir exactamente

```json
{
  "version": "1.2.0"
}
```

> Ambos archivos deben tener el mismo número de versión. El Sidebar lee `chatbot/package.json` para mostrar `v1.2.0` en el frontpage.

### 3. `CHANGELOG.md` — registrar el cambio bajo `[Unreleased]`

```markdown
## [Unreleased]

### Agregado
- Descripción concisa de la nueva funcionalidad

### Corregido
- Descripción del bug corregido (si aplica)
```

## Formato de Commit (Conventional Commits)

El mensaje de commit DEBE usar el prefijo correcto:

| Prefijo | Efecto en versión |
|---|---|
| `feat:` | bump minor |
| `fix:` | bump patch |
| `feat!:` o `BREAKING CHANGE:` en cuerpo | bump major |
| `perf:` | bump patch |
| `refactor:`, `docs:`, `chore:` | sin bump |

## Flujo obligatorio al implementar cambios funcionales

1. Implementar el cambio de código
2. Determinar el tipo de bump (minor / patch / major)
3. Actualizar `.release-please-manifest.json` → campo `"."`
4. Actualizar `chatbot/package.json` → campo `"version"` (mismo valor)
5. Actualizar `CHANGELOG.md` → sección `[Unreleased]`
6. Hacer commit con el prefijo correcto
