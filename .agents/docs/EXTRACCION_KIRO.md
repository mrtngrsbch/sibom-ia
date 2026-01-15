# Análisis de la Documentación de Kiro - Plan de Extracción

## Fecha: 2026-01-07

## Veredicto Global

🎯 **Nivel de análisis: 9.5/10**

Kiro generó documentación técnica a nivel **profesional/experto**. No es boilerplate, es análisis real del código con ejemplos específicos, rutas de archivos, patrones observados y métricas medidas.

---

## LO QUE DEBEMOS EXTRAER A `.agents/`

### ✅ ARCHIVOS A CREAR (Prioridad Alta)

#### 1. `.agents/specs/01-proyecto-overview.md`
**Extraer de:** `.kiro/specs/01-proyecto-overview.md`

**Qué mantener:**
- Visión general del ecosistema (backend + frontend)
- Flujo de datos completo
- Casos de uso principales
- Tecnologías clave

**Qué eliminar:**
- Detalles excesivos de implementación
- Métricas específicas (ir a `docs/`)

---

#### 2. `.agents/specs/02-backend-architecture.md`
**Extraer de:** `.kiro/specs/02-backend-scraper.md`

**Qué mantener:**
- Pipeline de 3 niveles (conceptual)
- Estrategia híbrida (BeautifulSoup + LLM)
- Características principales (paralelización, rate limiting)

**Qué eliminar:**
- snippets de código específicos
- nombres de métodos internos
- líneas de código exactas

---

#### 3. `.agents/specs/03-frontend-architecture.md`
**Extraer de:** `.kiro/specs/03-frontend-chatbot.md`

**Qué mantener:**
- Arquitectura Next.js 15 + React 19
- Sistema RAG con BM25
- Flujo de consulta
- Integración con backend

**Qué eliminar:**
- Detalles de implementación de BM25
- Configuraciones específicas
- Código de componentes

---

#### 4. `.agents/specs/04-integracion-backend-frontend.md`
**Extraer de:** `.kiro/specs/04-integracion.md`

**Qué mantener:**
- Cómo se comunican ambas partes
- Formato de datos compartidos (JSON schema)
- Sincronización de datos

**Qué eliminar:**
- Ejemplos de código específicos
- Configuraciones de entorno

---

#### 5. `.agents/steering/python-patterns.md`
**Extraer de:** `.kiro/steering/python-patterns.md`

**Qué mantener:**
- Principios de diseño (SOLID, DRY)
- Patrones de error handling
- Estrategias de LLM integration
- Testing patterns

**Qué eliminar:**
- Snippets de código
- Ejemplos de implementación específicos

---

#### 6. `.agents/steering/typescript-react-patterns.md`
**Extraer de:** `.kiro/steering/typescript-patterns.md`

**Qué mantener:**
- Type system architecture
- React component patterns
- State management patterns
- Performance optimization patterns

**Qué eliminar:**
- Implementaciones específicas
- Código de ejemplo detallado

---

#### 7. `.agents/hooks/testing-automation.md`
**Extraer de:** `.kiro/hooks/test-validation.md`

**Qué mantener:**
- Estrategia de testing general
- Cuándo ejecutar tests
- Tipos de tests requeridos

**Qué eliminar:**
- Scripts específicos de package.json
- Configuraciones de pytest/vitest
- Ejemplos de tests específicos

---

## LO QUE NO DEBEMOS EXTRAER (Crear en `docs/` en su lugar)

### 📁 MOVER A `docs/technical/`

1. **Detalles de implementación de BM25**
   - Archivo: `docs/technical/bm25-implementation.md`
   - Contenido: Algoritmo, parámetros, optimizaciones

2. **Métricas de performance**
   - Archivo: `docs/technical/performance-metrics.md`
   - Contenido: Benchmarks, optimizaciones, mejoras

3. **Configuraciones específicas**
   - Archivo: `docs/technical/configuration-reference.md`
   - Contenido: Variables de entorno, scripts, settings

4. **Ejemplos de código detallados**
   - Archivo: `docs/technical/code-examples.md`
   - Contenido: Snippets, patrones de implementación

---

## ESTRATEGIA DE EXTRACCIÓN

### Fase 1: Extracción Manual Crítica

**Archivos prioritarios (crear hoy):**
1. `.agents/specs/01-proyecto-overview.md`
2. `.agents/specs/02-backend-architecture.md`
3. `.agents/specs/03-frontend-architecture.md`
4. `.agents/steering/python-patterns.md`
5. `.agents/steering/typescript-react-patterns.md`

**Método:**
- Leer archivo de `.kiro/`
- Identificar secciones clave (arquitectura, patrones, decisiones)
- Reescribir en formato CONCISO (50% del tamaño)
- Eliminar detalles de implementación
- Enfocarse en QUÉ y POR QUÉ, no CÓMO

---

### Fase 2: Crear Sincronizador

**Script:** `.agents/hooks/sync_from_kiro.py`

**Funcionalidad:**
```python
# Estrategia de sincronización .kiro/ → .agents/

def sync_kiro_to_agents(kiro_file, agents_file, extraction_rules):
    """
    Extrae contenido esencial de .kiro/ a .agents/

    - Lee archivo .kiro/
    - Aplica reglas de extracción (QUÉ mantener vs QUÉ eliminar)
    - Escribe versión simplificada en .agents/
    - Mantiene detalles técnicos en docs/technical/
    """
    pass
```

**Reglas de extracción:**
- Mantener: Arquitectura, patrones, decisiones, principios
- Eliminar: Snippets de código, configuraciones específicas, rutas exactas
- Mover a docs/: Detalles de implementación, métricas, ejemplos

---

### Fase 3: Integración con Claude Code

**Actualizar:** `.claude/CLAUDE.md`

```markdown
# Instrucciones para Claude Code

Este proyecto usa la arquitectura `.agents/` como fuente de verdad.

## Antes de modificar código:

1. LEER: `.agents/specs/` para entender arquitectura
2. RESPETAR: `.agents/steering/` como restricciones obligatorias
3. CONSULTAR: `docs/technical/` para detalles de implementación

## Para cambios arquitectónicos:

1. Proponer cambio en `.agents/specs/` PRIMERO
2. Esperar aprobación
3. Luego implementar en código
```

---

## DIFERENCIAS CLAVE: `.kiro/` vs `.agents/`

| Aspecto | `.kiro/` | `.agents/` |
|---------|----------|-----------|
| **Propósito** | Análisis técnico profundo | Arquitectura del proyecto |
| **Audiencia** | Ingenieros especialistas | Todos los agentes AI |
| **Nivel** | Implementación específica | Conceptual y patterns |
| **Código** | Snippets detallados | Pseudo-código o ninguno |
| **Rutas** | `python-cli/sibom_scraper.py:32-848` | "Backend scraper principal" |
| **Métricas** | Exactas con decimales | Generales/sin datos |
| **Longitud** | 400-600 líneas por archivo | 100-150 líneas por archivo |

---

## PRÓXIMOS PASOS

### Inmediato (hoy)

1. ✅ **Analizar documentación de Kiro** - COMPLETADO
2. ⏳ **Crear 5 archivos críticos en `.agents/`**
3. ⏳ **Actualizar `.claude/CLAUDE.md`**
4. ⏳ **Probar que Claude Code lea `.agents/`**

### Corto plazo (esta semana)

5. ⏳ **Crear script de sincronización `.kiro/` → `.agents/`**
6. ⏳ **Mover detalles técnicos a `docs/technical/`**
7. ⏳ **Documentar workflow de actualización**

### Medio plazo (próximo mes)

8. ⏳ **Automatizar sincronización con hooks**
9. ⏳ **Integrar otras herramientas (Droid, etc.)**
10. ⏳ **Refinar `.agents/` basado en uso real**

---

## CONCLUSIÓN

🎯 **Kiro hizo un trabajo EXCEPCIONAL.**

La documentación que generó es de **nivel profesional senior**, con:
- ✅ Análisis profundo del código real
- ✅ Patrones observados (no inventados)
- ✅ Métricas medidas (no asumidas)
- ✅ Ejemplos específicos del proyecto

**Pero es DEMASIADO detallada para ser una "fuente de verdad" para agentes.**

Nuestro trabajo ahora es:
1. **Extraer lo esencial** → `.agents/`
2. **Mover lo técnico** → `docs/technical/`
3. **Mantener `.kiro/` como "experto técnico"** para referencia

Esto nos da:
- **`.agents/`**: Arquitectura clara para cualquier agente
- **`docs/technical/`**: Detalles para desarrolladores humanos
- **`.kiro/`**: Análisis profundo para consultas técnicas

---

**¡Vamos a extraer lo mejor de cada mundo!** 🚀
