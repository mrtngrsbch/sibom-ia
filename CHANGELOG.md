# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

### Agregado
- Sistema de versionado semántico completo
- Widget de versión en Sidebar del chatbot
- Documentación de versionado en `docs/VERSIONING.md`
- Este archivo CHANGELOG.md

### Mejorado
- N/A

### Corregido
- N/A

---

## [1.1.0] - 2026-02-14

### Agregado
- Análisis satelital de anegamiento con Sentinel-2
- Dashboard de analytics con estadísticas por municipio
- Soporte para balances municipales en formato PDF
- Búsqueda semántica con Qdrant (opcional)
- Widget de clima en Sidebar
- Filtros avanzados por fecha, tipo de documento y municipio
- API de chat con streaming usando Vercel AI SDK
- Integración con OpenRouter para múltiples LLMs (Gemini 3 Flash, GLM 4.7)

### Mejorado
- Scraper de SIBOM ahora usa Vision API para tablas complejas
- Búsqueda BM25 optimizada para español (normalización de acentos)
- Reducción del 90% en requests al backend (polling cada 5 min)
- Performance de índices JSON con compresión
- UX del chat con mejor formateo de tablas markdown

### Corregido
- Búsqueda con acentos ahora funciona correctamente
- Formateo de fechas en formato argentino (DD/MM/YYYY)
- Manejo de errores en API de OpenRouter
- Cache de índices que no se invalidaba correctamente

### Modificado
- Migración de OpenAI SDK a Vercel AI SDK
- Estructura de índices optimizada (campos abreviados)
- Sistema de filtros simplificado en UI

---

## [1.0.0] - 2026-01-17

### Agregado
- Primera versión pública del chatbot
- Scraper Python para extraer boletines de SIBOM
- Indexación de normativas municipales (220K+ documentos)
- RAG con BM25 para búsqueda semántica
- Soporte para 80+ municipios de Buenos Aires
- API REST con FastAPI
- Frontend Next.js con React 19
- Docker Compose para desarrollo local

### Tecnologías Iniciales
- Python 3.13 (backend)
- Next.js 16 (frontend)
- OpenRouter API (LLMs)
- SQLite (índices)
- Vercel (deployment)

---

## Tipos de Cambios

- **Agregado** - Para nuevas funcionalidades
- **Mejorado** - Para mejoras en funcionalidades existentes
- **Deprecado** - Para funcionalidades que serán removidas
- **Eliminado** - Para funcionalidades removidas
- **Corregido** - Para corrección de bugs
- **Seguridad** - Para vulnerabilidades corregidas
- **Modificado** - Para cambios que no caen en otras categorías

---

## Notas de Migración

### Desde 1.0.0 a 1.1.0

**Cambios compatibles (no requieren acción):**
- Los índices anteriores siguen siendo válidos
- La API del chatbot mantiene compatibilidad

**Nuevas dependencias opcionales:**
- Qdrant (solo si se usa búsqueda vectorial)
- Poppler (solo para Vision API en Python CLI)

**Variables de entorno nuevas (opcionales):**
```env
QDRANT_URL=           # Para búsqueda vectorial
QDRANT_API_KEY=       # Para Qdrant Cloud
WEATHER_API_KEY=      # Para widget de clima
```

---

## Roadmap (Próximas Versiones)

### v1.2.0 (Febrero 2026) - Planeado
- [ ] Exportación de búsquedas a PDF/Excel
- [ ] Comparación de normativas entre municipios
- [ ] Sistema de alertas por email
- [ ] Soporte para decretos provinciales

### v1.3.0 (Marzo 2026) - Planeado
- [ ] Editor de consultas SQL visual
- [ ] API pública para desarrolladores
- [ ] Widget embebible para sitios externos
- [ ] Sistema de usuario y favoritos

### v2.0.0 (Q2 2026) - En discusión
- [ ] Rediseño completo de API RAG
- [ ] Migración a PostgreSQL + pgvector
- [ ] Sistema multi-tenant
- [ ] Autenticación y roles de usuario

---

## Contribuyendo

Este es un proyecto de desarrollo individual, pero se aceptan:
- Reportes de bugs vía GitHub Issues
- Sugerencias de funcionalidades vía GitHub Discussions
- Pull Requests (previo acuerdo por issue)

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

---

## Licencia

Este proyecto usa licencia [Especificar licencia].

Ver [LICENSE](LICENSE) para más información.

---

**Última actualización:** 2026-02-14  
**Mantenedor:** @mrtn  
**Versión actual:** v1.1.0
