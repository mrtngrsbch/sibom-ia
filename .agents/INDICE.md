# Índice de Documentación - .agents/

**Última actualización:** 2025-01-16  
**Versión:** 2.0

---

## 🎯 Navegación Rápida

### Para Nuevos Usuarios

1. **[QUICKSTART.md](QUICKSTART.md)** - Empieza aquí (5 minutos)
2. **[README.md](README.md)** - Manual completo (30 minutos)
3. **[agents/README.md](agents/README.md)** - Crear tu primer agente (10 minutos)

### Para Usuarios Existentes

1. **[CHANGELOG.md](CHANGELOG.md)** - ¿Qué cambió? (5 minutos)
2. **[GUIA-MIGRACION.md](GUIA-MIGRACION.md)** - Cómo migrar (10 minutos)
3. **[README.md](README.md)** - Nueva arquitectura (30 minutos)

### Para Mantenedores

1. **[RESUMEN-FINAL.md](RESUMEN-FINAL.md)** - Estado completo del proyecto (15 minutos)
2. **[ACTUALIZACION-COMPLETA.md](ACTUALIZACION-COMPLETA.md)** - Detalles Task 2 (10 minutos)
3. **[README.md](README.md)** - Arquitectura técnica (30 minutos)

---

## 📚 Documentos Principales

### 1. README.md (⭐ LEER PRIMERO)

**Tamaño:** 500+ líneas  
**Tiempo de lectura:** 30 minutos  
**Audiencia:** Todos

**Contenido:**
- Resumen ejecutivo (30 segundos)
- Estructura de carpetas
- Arquitectura del sistema
- Definición de agentes
- Sistema de prompts
- Reglas de código (steering)
- Sincronización con otras carpetas
- Workflows comunes
- Infraestructura (R2, GitHub)
- Reglas de oro
- Troubleshooting
- Métricas y monitoreo
- Referencias rápidas

**Cuándo leer:**
- ✅ Siempre primero
- ✅ Cuando olvides cómo funciona
- ✅ Antes de modificar código
- ✅ Para entender arquitectura completa

**Comando:**
```bash
cat .agents/README.md
```

---

### 2. QUICKSTART.md

**Tamaño:** ~100 líneas  
**Tiempo de lectura:** 5 minutos  
**Audiencia:** Nuevos usuarios

**Contenido:**
- Instalación rápida
- Primer agente en 5 minutos
- Comandos esenciales
- Próximos pasos

**Cuándo leer:**
- ✅ Primera vez usando el sistema
- ✅ Necesitas empezar rápido
- ✅ Quieres ver un ejemplo funcional

**Comando:**
```bash
cat .agents/QUICKSTART.md
```

---

### 3. CHANGELOG.md

**Tamaño:** ~300 líneas  
**Tiempo de lectura:** 5 minutos  
**Audiencia:** Todos

**Contenido:**
- Resumen de cambios v2.0
- Archivos creados (13)
- Archivos eliminados (27)
- Nueva estructura
- Principios arquitectónicos
- Flujos de sincronización
- Métricas de impacto
- Checklist de validación
- Próximos pasos
- Lecciones aprendidas

**Cuándo leer:**
- ✅ Después de actualizar
- ✅ Para entender qué cambió
- ✅ Para ver historial de evolución

**Comando:**
```bash
cat .agents/CHANGELOG.md
```

---

### 4. GUIA-MIGRACION.md

**Tamaño:** ~200 líneas  
**Tiempo de lectura:** 10 minutos  
**Audiencia:** Usuarios existentes

**Contenido:**
- Checklist de migración
- Mapeo de archivos
- Breaking changes
- Actualizar scripts personalizados
- Actualizar documentación interna
- Nuevos conceptos
- Validación post-migración
- Troubleshooting

**Cuándo leer:**
- ✅ Migrando de v1.0 a v2.0
- ✅ Scripts antiguos no funcionan
- ✅ Necesitas actualizar referencias

**Comando:**
```bash
cat .agents/GUIA-MIGRACION.md
```

---

### 5. RESUMEN-FINAL.md

**Tamaño:** ~400 líneas  
**Tiempo de lectura:** 15 minutos  
**Audiencia:** Mantenedores

**Contenido:**
- Objetivo general
- Tareas completadas
- Arquitectura final
- Métricas de impacto
- Estructura final de archivos
- Flujos de trabajo implementados
- Documentación creada
- Validación de consistencia
- Lecciones aprendidas
- Próximos pasos recomendados
- Guía de uso rápida
- Conclusión

**Cuándo leer:**
- ✅ Para entender estado completo
- ✅ Para ver métricas de impacto
- ✅ Para planificar próximos pasos

**Comando:**
```bash
cat .agents/RESUMEN-FINAL.md
```

---

### 6. ACTUALIZACION-COMPLETA.md

**Tamaño:** ~300 líneas  
**Tiempo de lectura:** 10 minutos  
**Audiencia:** Mantenedores

**Contenido:**
- Objetivo Task 2
- Archivos actualizados
- Arquitectura final
- Consistencia verificada
- Flujos de trabajo actualizados
- Cambios específicos por archivo
- Validación de consistencia
- Lecciones aprendidas

**Cuándo leer:**
- ✅ Para entender Task 2
- ✅ Para ver cambios en `.claude/` y `.factory/`
- ✅ Para validar consistencia

**Comando:**
```bash
cat .agents/ACTUALIZACION-COMPLETA.md
```

---

### 7. INDICE.md (Este Archivo)

**Tamaño:** ~200 líneas  
**Tiempo de lectura:** 5 minutos  
**Audiencia:** Todos

**Contenido:**
- Navegación rápida
- Documentos principales
- Documentos de subdirectorios
- Documentos de configuración
- Documentos de referencia
- Matriz de decisión
- Búsqueda rápida

**Cuándo leer:**
- ✅ No sabes qué documento leer
- ✅ Buscas algo específico
- ✅ Quieres overview de documentación

**Comando:**
```bash
cat .agents/INDICE.md
```

---

## 📁 Documentos de Subdirectorios

### agents/README.md

**Ubicación:** `.agents/agents/README.md`  
**Tamaño:** ~200 líneas  
**Audiencia:** Desarrolladores

**Contenido:**
- Qué es un agente
- Anatomía de un agente
- Template de agente
- Ejemplos
- Best practices
- Checklist de calidad

**Cuándo leer:**
- ✅ Vas a crear un agente
- ✅ Necesitas template
- ✅ Quieres ver ejemplos

**Comando:**
```bash
cat .agents/agents/README.md
```

---

### prompts/system-prompts.md

**Ubicación:** `.agents/prompts/system-prompts.md`  
**Tamaño:** ~150 líneas  
**Audiencia:** Desarrolladores

**Contenido:**
- Prompts de sistema
- Personalidad de agentes
- Contexto de agentes
- Ejemplos: rag-indexer, scraper-orchestrator

**Cuándo leer:**
- ✅ Vas a crear un agente
- ✅ Necesitas definir personalidad
- ✅ Quieres ver ejemplos de prompts

**Comando:**
```bash
cat .agents/prompts/system-prompts.md
```

---

### prompts/task-prompts.md

**Ubicación:** `.agents/prompts/task-prompts.md`  
**Tamaño:** ~150 líneas  
**Audiencia:** Desarrolladores

**Contenido:**
- Prompts de tareas
- Ejemplos: indexing, scraping, validation
- Input/output esperado
- Pasos de ejecución

**Cuándo leer:**
- ✅ Vas a crear un agente
- ✅ Necesitas definir tareas
- ✅ Quieres ver ejemplos de prompts

**Comando:**
```bash
cat .agents/prompts/task-prompts.md
```

---

### specs/README.md

**Ubicación:** `.agents/specs/README.md`  
**Tamaño:** ~50 líneas  
**Audiencia:** Todos

**Contenido:**
- Pointer a `.kiro/specs/`
- Cuándo consultar `.kiro/`
- Guía de navegación

**Cuándo leer:**
- ✅ Necesitas detalles técnicos profundos
- ✅ Quieres consultar análisis de Kiro

**Comando:**
```bash
cat .agents/specs/README.md
```

---

## 🎛️ Documentos de Steering

### steering/python-patterns.md

**Ubicación:** `.agents/steering/python-patterns.md`  
**Audiencia:** Desarrolladores Python

**Contenido:**
- Patrones de clases
- Error handling
- LLM integration
- Retry logic
- Logging estructurado

**Cuándo leer:**
- ✅ Vas a escribir código Python
- ✅ Necesitas seguir patrones obligatorios

**Comando:**
```bash
cat .agents/steering/python-patterns.md
```

---

### steering/typescript-patterns.md

**Ubicación:** `.agents/steering/typescript-patterns.md`  
**Audiencia:** Desarrolladores TypeScript

**Contenido:**
- Patrones de tipos
- React patterns
- API clients
- Error boundaries
- Performance optimization

**Cuándo leer:**
- ✅ Vas a escribir código TypeScript
- ✅ Necesitas seguir patrones obligatorios

**Comando:**
```bash
cat .agents/steering/typescript-patterns.md
```

---

### steering/error-handling.md

**Ubicación:** `.agents/steering/error-handling.md`  
**Audiencia:** Todos los desarrolladores

**Contenido:**
- Estrategias de error handling
- Frontend patterns
- Backend patterns
- Logging
- Graceful degradation

**Cuándo leer:**
- ✅ Vas a manejar errores
- ✅ Necesitas estrategias de resilience

**Comando:**
```bash
cat .agents/steering/error-handling.md
```

---

### steering/testing-patterns.md

**Ubicación:** `.agents/steering/testing-patterns.md`  
**Audiencia:** Todos los desarrolladores

**Contenido:**
- Unit testing
- Property-based testing
- Integration testing
- Testing scripts
- Coverage

**Cuándo leer:**
- ✅ Vas a escribir tests
- ✅ Necesitas estrategias de testing

**Comando:**
```bash
cat .agents/steering/testing-patterns.md
```

---

### steering/performance-optimization.md

**Ubicación:** `.agents/steering/performance-optimization.md`  
**Audiencia:** Todos los desarrolladores

**Contenido:**
- Frontend optimizations
- Backend optimizations
- Caching strategies
- Performance metrics

**Cuándo leer:**
- ✅ Vas a optimizar performance
- ✅ Necesitas estrategias de caching

**Comando:**
```bash
cat .agents/steering/performance-optimization.md
```

---

## ⚙️ Documentos de Configuración

### .opencode/rules.md

**Ubicación:** `.opencode/rules.md`  
**Audiencia:** Usuarios de OpenCode

**Contenido:**
- Reglas de oro
- Jerarquía de dependencias
- Reglas de código
- Restricciones
- Comandos comunes

**Cuándo leer:**
- ✅ Usas OpenCode
- ✅ Necesitas reglas específicas

**Comando:**
```bash
cat .opencode/rules.md
```

---

### .opencode/agents.json

**Ubicación:** `.opencode/agents.json`  
**Audiencia:** Usuarios de OpenCode

**Contenido:**
- Registro de agentes
- Referencias a `.agents/agents/*.yaml`
- Metadata de sincronización

**Cuándo leer:**
- ✅ Quieres ver agentes registrados
- ✅ Necesitas verificar sincronización

**Comando:**
```bash
cat .opencode/agents.json
```

---

### .claude/CLAUDE.md

**Ubicación:** `.claude/CLAUDE.md`  
**Audiencia:** Usuarios de Claude Code

**Contenido:**
- Configuración rápida
- Arquitectura
- Flujo de trabajo
- Reglas críticas
- Referencias rápidas

**Cuándo leer:**
- ✅ Usas Claude Code
- ✅ Necesitas configuración específica

**Comando:**
```bash
cat .claude/CLAUDE.md
```

---

### .factory/config.yml

**Ubicación:** `.factory/config.yml`  
**Audiencia:** Usuarios de Factory/Droids

**Contenido:**
- Contexto de agentes
- Comandos del proyecto
- Especialistas disponibles
- Flujo de trabajo
- Arquitectura

**Cuándo leer:**
- ✅ Usas Factory/Droids
- ✅ Necesitas configuración específica

**Comando:**
```bash
cat .factory/config.yml
```

---

## 📖 Documentos de Referencia

### .kiro/specs/

**Ubicación:** `.kiro/specs/`  
**Audiencia:** Todos (opcional)

**Contenido:**
- Análisis técnico profundo
- Detalles de implementación
- Arquitectura detallada

**Cuándo leer:**
- ✅ Necesitas detalles técnicos profundos
- ✅ Quieres entender implementación

**Comando:**
```bash
ls .kiro/specs/
cat .kiro/specs/01-proyecto-overview.md
```

---

### AGENTS.md (Raíz del proyecto)

**Ubicación:** `AGENTS.md`  
**Audiencia:** Todos

**Contenido:**
- Guía general del proyecto
- Comandos comunes
- Code style guidelines
- Testing policy

**Cuándo leer:**
- ✅ Primera vez en el proyecto
- ✅ Necesitas guía general

**Comando:**
```bash
cat AGENTS.md
```

---

## 🎯 Matriz de Decisión

### ¿Qué documento leer?

| Situación | Documento | Tiempo |
|-----------|-----------|--------|
| **Primera vez en el proyecto** | QUICKSTART.md | 5 min |
| **Quiero entender todo** | README.md | 30 min |
| **Acabo de actualizar** | CHANGELOG.md | 5 min |
| **Migrando de v1.0** | GUIA-MIGRACION.md | 10 min |
| **Voy a crear un agente** | agents/README.md | 10 min |
| **Voy a escribir Python** | steering/python-patterns.md | 15 min |
| **Voy a escribir TypeScript** | steering/typescript-patterns.md | 15 min |
| **Voy a escribir tests** | steering/testing-patterns.md | 15 min |
| **Necesito optimizar** | steering/performance-optimization.md | 15 min |
| **Uso OpenCode** | .opencode/rules.md | 10 min |
| **Uso Claude Code** | .claude/CLAUDE.md | 10 min |
| **Uso Factory/Droids** | .factory/config.yml | 5 min |
| **Necesito detalles técnicos** | .kiro/specs/ | Variable |
| **Soy mantenedor** | RESUMEN-FINAL.md | 15 min |
| **No sé qué leer** | INDICE.md (este archivo) | 5 min |

---

## 🔍 Búsqueda Rápida

### Por Tema

| Tema | Documentos |
|------|-----------|
| **Arquitectura** | README.md, RESUMEN-FINAL.md |
| **Agentes** | README.md, agents/README.md |
| **Prompts** | prompts/system-prompts.md, prompts/task-prompts.md |
| **Steering** | steering/*.md |
| **Sincronización** | README.md, hooks/*.py |
| **Migración** | GUIA-MIGRACION.md, CHANGELOG.md |
| **Troubleshooting** | README.md, GUIA-MIGRACION.md |
| **Configuración** | .opencode/, .claude/, .factory/ |

### Por Audiencia

| Audiencia | Documentos |
|-----------|-----------|
| **Nuevos usuarios** | QUICKSTART.md, README.md |
| **Usuarios existentes** | CHANGELOG.md, GUIA-MIGRACION.md |
| **Desarrolladores** | agents/README.md, steering/*.md |
| **Mantenedores** | RESUMEN-FINAL.md, ACTUALIZACION-COMPLETA.md |
| **Usuarios OpenCode** | .opencode/rules.md |
| **Usuarios Claude** | .claude/CLAUDE.md |
| **Usuarios Factory** | .factory/config.yml |

### Por Tiempo Disponible

| Tiempo | Documentos |
|--------|-----------|
| **5 minutos** | QUICKSTART.md, INDICE.md, CHANGELOG.md |
| **10 minutos** | GUIA-MIGRACION.md, agents/README.md |
| **15 minutos** | RESUMEN-FINAL.md, steering/*.md |
| **30 minutos** | README.md |

---

## 📞 Ayuda Rápida

### Comandos Útiles

```bash
# Leer manual completo
cat .agents/README.md

# Leer guía rápida
cat .agents/QUICKSTART.md

# Ver qué cambió
cat .agents/CHANGELOG.md

# Guía de migración
cat .agents/GUIA-MIGRACION.md

# Ver estado completo
cat .agents/RESUMEN-FINAL.md

# Este índice
cat .agents/INDICE.md

# Buscar en documentación
grep -r "mi-busqueda" .agents/

# Listar todos los documentos
find .agents/ -name "*.md"
```

### Estructura de Archivos

```
.agents/
├── README.md                    # ⭐ Manual completo
├── QUICKSTART.md                # Guía rápida
├── CHANGELOG.md                 # Historial de cambios
├── GUIA-MIGRACION.md            # Guía de migración
├── RESUMEN-FINAL.md             # Resumen completo
├── ACTUALIZACION-COMPLETA.md    # Detalles Task 2
├── INDICE.md                    # Este archivo
│
├── agents/
│   ├── README.md               # Guía de agentes
│   └── rag-indexer.yaml        # Ejemplo
│
├── prompts/
│   ├── system-prompts.md       # Prompts de sistema
│   └── task-prompts.md         # Prompts de tareas
│
├── steering/
│   ├── python-patterns.md
│   ├── typescript-patterns.md
│   ├── error-handling.md
│   ├── testing-patterns.md
│   └── performance-optimization.md
│
├── specs/
│   └── README.md               # Pointer a .kiro/
│
└── hooks/
    ├── sync_from_kiro.py
    ├── propagate_to_kiro.py
    ├── sync_all.py
    └── sync_to_opencode.py
```

---

## ✅ Checklist de Lectura

### Para Nuevos Usuarios

- [ ] Leí QUICKSTART.md
- [ ] Leí README.md
- [ ] Leí agents/README.md
- [ ] Entendí la arquitectura
- [ ] Creé mi primer agente

### Para Usuarios Existentes

- [ ] Leí CHANGELOG.md
- [ ] Leí GUIA-MIGRACION.md
- [ ] Actualicé mis scripts
- [ ] Verifiqué sincronización
- [ ] Entendí los cambios

### Para Mantenedores

- [ ] Leí RESUMEN-FINAL.md
- [ ] Leí ACTUALIZACION-COMPLETA.md
- [ ] Entendí métricas de impacto
- [ ] Validé consistencia
- [ ] Planeé próximos pasos

---

**Última actualización:** 2025-01-16  
**Versión:** 2.0  
**Autor:** mrtn

---

**¿No encuentras lo que buscas?**

Usa la búsqueda:
```bash
grep -r "tu-busqueda" .agents/
```

O lee el manual completo:
```bash
cat .agents/README.md
```
