# Documentación SIBOM Scraper Assistant

Esta carpeta contiene toda la documentación organizada del proyecto SIBOM Scraper Assistant.

---

## 📂 Estructura

```
docs/
├── 01-architecture/         ← Arquitectura y diseño del sistema
├── 02-deployment/          ← Guías de deployment (Vercel, R2)
├── 03-features/            ← Features implementadas (Vector Search, SQL)
├── 04-changelogs/          ← Historial de cambios por fecha
├── 05-issues/             ← Bugs y fixes documentados
└── 06-reference/           ← Referencias (Factory, migraciones)
```

---

## 📚 Por Categoría

### 01-architecture/

Documentación sobre arquitectura del sistema, decisiones de diseño y análisis.

- **arquitectura-sistema.md** - Arquitectura con Function Calling
- **analisis-solucion.md** - Análisis crítico de soluciones
- **analisis-stack.md** - Análisis del stack tecnológico

### 02-deployment/

Guías completas para deployment en producción (Vercel, Cloudflare R2, GitHub Actions).

- **guia-completa.md** - Guía completa de deployment
- **quickstart.md** - Quickstart para deployment rápido
- **entornos.md** - Diferencias entre desarrollo y producción
- **troubleshooting.md** - Solución de problemas comunes

### 03-features/

Documentación de features implementadas en el sistema.

- **vector-search.md** - Búsqueda semántica con OpenAI + Qdrant
- **sql-retriever.md** - Base de datos SQLite para queries rápidas
- **data-catalog.md** - Catálogo de datos para el LLM
- **semantic-search.md** - Búsqueda semántica mejorada
- **embeddings-comparacion.md** - Comparación OpenAI vs Cohere

### 04-changelogs/

Historial de cambios organizado por fecha.

- **2026-01-optimizaciones.md** - Optimizaciones de tokens y performance
- **2026-01-refactor-filtros.md** - Refactor de filtros
- **2026-01-cleanup.md** - Limpieza de código obsoleto
- **session-2026-01-10.md** - Resumen de sesión
- **audit-complete.md** - Auditoría completa del código

### 05-issues/

Documentación de bugs y fixes implementados.

- **massive-listings.md** - Fix para listados >500 resultados
- **comparative-queries.md** - Fix para queries comparativas entre municipios
- **individual-urls.md** - Fix de URLs individuales
- **llm-strategy.md** - Estrategia de uso del LLM (simplificación)

### 06-reference/

Documentación de referencia y migraciones.

- **factory-implementation.md** - Implementación de droids/skills/hooks
- **migracion.md** - Migración de Gemini → OpenRouter + CLI Python

---

## 🎯 Cómo Navegar

### Nuevo al proyecto?

1. Lee **01-architecture/** para entender el sistema
2. Ve a **02-deployment/** para deployment en producción
3. Consulta **03-features/** para ver implementaciones

### Buscando solución a un bug?

1. Ve a **05-issues/** para ver fixes documentados
2. Busca por nombre del bug o feature
3. Revisa **04-changelogs/** para ver cuando se implementó

### Quieres entender el historial?

1. Ve a **04-changelogs/** para ver evolución temporal
2. Los archivos están nombrados con formato `YYYY-MM-titulo.md`
3. Cada changelog incluye métricas de impacto

---

## 🔗 Documentación Relacionada

- **README.md** - Documentación principal del proyecto
- **AGENTS.md** - Guía de agentes para AI assistants
- **chatbot/README.md** - Documentación del chatbot Next.js
- **python-cli/README.md** - Documentación del scraper CLI

---

## 📝 Convenciones

### Nombres de Archivos

- **kebab-case**: `arquitectura-sistema.md` (no `Arquitectura_Sistema.md`)
- **Inglés para código**: `vector-search.md`
- **Español para contenido**: Todo el contenido en español

### Estructura de Documentos

Cada documento debe seguir esta estructura:

```markdown
# Título del Documento

**Fecha:** YYYY-MM-DD
**Estado:** ✅ Completado / 🔄 En progreso / ⏸️ Pendiente

---

## 🎯 Resumen Ejecutivo

Breve descripción del problema y solución.

---

## 📋 Detalles

Documentación técnica completa.

---

## 🔧 Archivos Modificados

Lista de archivos afectados.

---

## 🧪 Testing

Casos de prueba y resultados esperados.
```

---

## 🚀 Actualización

Para agregar nueva documentación:

1. Crea el archivo en la carpeta apropiada
2. Sigue las convenciones de nombre y estructura
3. Agrega referencias cruzadas si es necesario
4. Actualiza este README con el nuevo documento

---

**Última actualización:** 2026-01-14
**Total de documentos:** ~15 archivos consolidados (de 35 originales)
