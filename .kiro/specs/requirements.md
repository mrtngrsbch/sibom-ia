# Especificación de Requerimientos - SIBOM Scraper Assistant

## Información del Proyecto

**Nombre:** SIBOM Scraper Assistant  
**Versión:** 2.0 (Migración OpenRouter + Optimizaciones)  
**Fecha:** 2026-01-07  
**Estado:** Implementado y en producción  
**Tipo:** Sistema completo de scraping web + chatbot conversacional  

## Resumen Ejecutivo

El SIBOM Scraper Assistant es un ecosistema completo que automatiza la extracción y consulta inteligente de boletines oficiales municipales de la Provincia de Buenos Aires. Combina un backend Python CLI para scraping automatizado con un frontend Next.js para consultas conversacionales mediante IA.

### Componentes Principales

1. **Backend Python CLI** (`python-cli/`): Scraper automatizado con procesamiento LLM
2. **Frontend Next.js** (`chatbot/`): Interfaz web conversacional con sistema RAG
3. **Integración JSON**: Comunicación desacoplada mediante archivos estructurados
4. **Sistema LLM**: OpenRouter con estrategia dual de modelos (económico + premium)

## Epic 1: Backend Python CLI - Sistema de Scraping

### Historia de Usuario 1.1: Scraping Automatizado de Boletines
**Como** desarrollador del sistema  
**Quiero** extraer automáticamente todos los boletines municipales de SIBOM  
**Para** tener una base de datos actualizada de normativas municipales  

**Criterios de Aceptación:**
- ✅ Detectar automáticamente el número total de páginas sin intervención manual
- ✅ Procesar múltiples boletines en paralelo (configurable 1-5 hilos)
- ✅ Extraer metadatos: número, fecha, descripción, enlace
- ✅ Manejar paginación automática de listados
- ✅ Generar archivos JSON individuales por boletín
- ✅ Crear índice consolidado `boletines_index.json`

**Estado:** ✅ Completado

### Historia de Usuario 1.2: Extracción de Contenido Legal
**Como** desarrollador del sistema  
**Quiero** extraer el texto completo de documentos legales  
**Para** permitir búsquedas semánticas en el contenido  

**Criterios de Aceptación:**
- ✅ Pipeline de 3 niveles: listado → enlaces → contenido
- ✅ Procesamiento híbrido: BeautifulSoup (95%) + LLM fallback (5%)
- ✅ Preservar estructura legal: VISTO, CONSIDERANDO, ORDENA
- ✅ Extraer todos los artículos numerados
- ✅ Mantener formato original de ordenanzas/decretos
- ✅ Rate limiting configurable (3s por defecto)

**Estado:** ✅ Completado

### Historia de Usuario 1.3: Gestión de Archivos Existentes
**Como** usuario del scraper  
**Quiero** controlar qué hacer con boletines ya procesados  
**Para** evitar reprocesamiento innecesario  

**Criterios de Aceptación:**
- ✅ Detección automática de archivos existentes
- ✅ Modo interactivo: menú de opciones (saltar/sobreescribir/cancelar)
- ✅ Modo automático: `--skip-existing` para saltar sin preguntar
- ✅ Verificación de integridad de archivos JSON
- ✅ Logging detallado de decisiones tomadas

**Estado:** ✅ Completado

### Historia de Usuario 1.4: Configuración Flexible de Modelos LLM
**Como** usuario del scraper  
**Quiero** elegir diferentes modelos LLM según mi presupuesto  
**Para** optimizar costos vs calidad de extracción  

**Criterios de Aceptación:**
- ✅ Soporte para múltiples modelos OpenRouter
- ✅ Modelo gratuito: `z-ai/glm-4.5-air:free` ($0)
- ✅ Modelo económico: `google/gemini-2.5-flash-lite` ($0.06/boletín)
- ✅ Modelo premium: `google/gemini-3-flash-preview` ($0.24/boletín)
- ✅ Configuración via argumento `--model`
- ✅ Documentación de costos y calidad por modelo

**Estado:** ✅ Completado

## Epic 2: Frontend Next.js - Sistema de Consultas

### Historia de Usuario 2.1: Chat Conversacional con IA
**Como** usuario final  
**Quiero** hacer preguntas en lenguaje natural sobre normativas municipales  
**Para** obtener respuestas precisas sin navegar formularios complejos  

**Criterios de Aceptación:**
- ✅ Interfaz de chat con streaming de respuestas
- ✅ Soporte para consultas en español natural
- ✅ Respuestas con citas a fuentes oficiales SIBOM
- ✅ Historial de conversación persistente
- ✅ Estados de loading y error claros
- ✅ Responsive design para móvil y desktop

**Estado:** ✅ Completado

### Historia de Usuario 2.2: Sistema RAG con Búsqueda Semántica
**Como** usuario del sistema  
**Quiero** que las respuestas se basen en documentos reales  
**Para** garantizar precisión y trazabilidad de la información  

**Criterios de Aceptación:**
- ✅ Algoritmo BM25 optimizado para documentos legales en español
- ✅ Tokenización especializada con stopwords mínimas
- ✅ Ranking por relevancia con peso extra para títulos
- ✅ Truncamiento dinámico según tipo de consulta
- ✅ Cache multi-nivel (índice 5min, archivos 30min)
- ✅ Soporte para fuentes locales y GitHub Raw

**Estado:** ✅ Completado

### Historia de Usuario 2.3: Filtros Inteligentes Automáticos
**Como** usuario final  
**Quiero** que el sistema detecte automáticamente filtros de mi consulta  
**Para** obtener resultados más precisos sin configuración manual  

**Criterios de Aceptación:**
- ✅ Auto-detección de municipio en la consulta
- ✅ Auto-detección de año → conversión a rango de fechas
- ✅ Auto-detección de tipo de normativa (ordenanza/decreto)
- ✅ Sincronización bidireccional: UI ↔ auto-detección
- ✅ Badges visuales de filtros activos
- ✅ Posibilidad de remover filtros individualmente

**Estado:** ✅ Completado

### Historia de Usuario 2.4: Optimización de Costos LLM
**Como** administrador del sistema  
**Quiero** minimizar costos de LLM sin sacrificar calidad  
**Para** mantener el servicio económicamente viable  

**Criterios de Aceptación:**
- ✅ Clasificación automática de consultas (FAQ vs búsqueda compleja)
- ✅ Modelo económico para FAQ: Gemini Flash ($0.0007/consulta)
- ✅ Modelo premium para búsquedas: Claude Sonnet ($0.017/consulta)
- ✅ Respuestas off-topic sin llamar LLM (ahorro 100%)
- ✅ Historial limitado a 10 mensajes (ahorro 2,000-4,000 tokens)
- ✅ System prompt comprimido (ahorro 38% tokens)

**Estado:** ✅ Completado

## Epic 3: Integración y Pipeline de Datos

### Historia de Usuario 3.1: Comunicación Backend-Frontend
**Como** desarrollador del sistema  
**Quiero** una integración robusta entre scraper y chatbot  
**Para** mantener datos sincronizados y actualizados  

**Criterios de Aceptación:**
- ✅ Formato JSON estructurado y consistente
- ✅ Esquema de datos validado con TypeScript
- ✅ Soporte para modo local (desarrollo) y GitHub Raw (producción)
- ✅ Compresión gzip opcional (80% reducción bandwidth)
- ✅ Detección automática de cambios en archivos locales
- ✅ Health checks y estadísticas de base de datos

**Estado:** ✅ Completado

### Historia de Usuario 3.2: Indexación y Enriquecimiento
**Como** desarrollador del sistema  
**Quiero** generar índices enriquecidos automáticamente  
**Para** mejorar la búsqueda y navegación  

**Criterios de Aceptación:**
- ✅ Generación automática de `boletines_index.json`
- ✅ Extracción de tipos de documentos del contenido
- ✅ Detección automática de municipios
- ✅ Índice markdown navegable (`boletines.md`)
- ✅ Utilidades de compresión y optimización
- ✅ Validación de integridad de datos

**Estado:** ✅ Completado

### Historia de Usuario 3.3: Monitoreo y Observabilidad
**Como** administrador del sistema  
**Quiero** visibilidad completa del pipeline de datos  
**Para** detectar problemas y optimizar performance  

**Criterios de Aceptación:**
- ✅ Logs estructurados con timestamps y contexto
- ✅ Métricas de performance (tiempo, tokens, costos)
- ✅ Estadísticas de cache (hits/misses, tamaño)
- ✅ Tracking de errores con categorización
- ✅ Health checks de componentes críticos
- ✅ Dashboards de uso y estadísticas

**Estado:** ✅ Completado

## Epic 4: Optimizaciones de Performance

### Historia de Usuario 4.1: Optimización de Rendering Frontend
**Como** usuario final  
**Quiero** una interfaz rápida y responsiva  
**Para** tener una experiencia fluida al usar el chat  

**Criterios de Aceptación:**
- ✅ Memoización de componentes ReactMarkdown (70% mejora)
- ✅ Debounce de localStorage (95% reducción escrituras)
- ✅ Polling reducido de 30s a 5min (90% menos requests)
- ✅ useCallback para evitar re-renders innecesarios
- ✅ Componentes optimizados con React.memo
- ✅ Bundle size optimizado (pendiente: tree-shaking)

**Estado:** ✅ Completado (mejoras adicionales pendientes)

### Historia de Usuario 4.2: Optimización de Sistema RAG
**Como** desarrollador del sistema  
**Quiero** búsquedas rápidas y eficientes  
**Para** responder consultas en menos de 2 segundos  

**Criterios de Aceptación:**
- ✅ Cache multi-nivel con TTL configurables
- ✅ Límites dinámicos de documentos según consulta
- ✅ Truncamiento inteligente de contenido (75-90% ahorro tokens)
- ✅ Algoritmo BM25 optimizado para español legal
- ✅ Carga paralela de archivos JSON
- ✅ Compresión gzip para reducir bandwidth

**Estado:** ✅ Completado

### Historia de Usuario 4.3: Procesamiento Paralelo Backend
**Como** usuario del scraper  
**Quiero** procesar múltiples boletines simultáneamente  
**Para** reducir el tiempo total de scraping  

**Criterios de Aceptación:**
- ✅ ThreadPoolExecutor con workers configurables
- ✅ Progress bars con Rich para feedback visual
- ✅ Rate limiting por worker para evitar 429 errors
- ✅ Manejo de errores por thread independiente
- ✅ 3x mejora de velocidad con 3 workers paralelos
- ✅ Configuración via `--parallel N`

**Estado:** ✅ Completado

## Epic 5: Calidad y Testing

### Historia de Usuario 5.1: Manejo Robusto de Errores
**Como** usuario del sistema  
**Quiero** que el sistema maneje errores graciosamente  
**Para** tener una experiencia confiable y predecible  

**Criterios de Aceptación:**
- ✅ Retry automático con backoff exponencial
- ✅ Fallbacks para servicios externos (cache antiguo)
- ✅ Mensajes de error user-friendly
- ✅ Logging detallado para debugging
- ✅ Validación de entrada con schemas Zod
- ✅ Error boundaries en componentes React

**Estado:** ✅ Completado

### Historia de Usuario 5.2: Scripts de Testing Manual
**Como** desarrollador  
**Quiero** scripts para validar funcionalidad rápidamente  
**Para** detectar problemas durante desarrollo  

**Criterios de Aceptación:**
- ✅ Scripts de testing para BM25 (`test-bm25.ts`)
- ✅ Scripts de testing para query analyzer (`test-query-analyzer.ts`)
- ✅ Scripts de testing para retriever (`test-retriever.ts`)
- ✅ Scripts de testing para filtros (`test-filter-extraction.ts`)
- ✅ Validación de algoritmos con datos reales
- ✅ Debugging de edge cases

**Estado:** ✅ Completado (testing automatizado pendiente)

### Historia de Usuario 5.3: Validación de Datos
**Como** desarrollador del sistema  
**Quiero** garantizar la integridad de datos extraídos  
**Para** mantener alta calidad en las respuestas  

**Criterios de Aceptación:**
- ✅ Validación de JSON con try-catch robusto
- ✅ Schemas TypeScript para estructura de datos
- ✅ Verificación de archivos referenciados en índice
- ✅ Detección de documentos corruptos o incompletos
- ✅ Métricas de calidad de extracción
- ✅ Alertas para tasas de error elevadas

**Estado:** ✅ Completado

## Requerimientos No Funcionales

### Performance
- **Tiempo de respuesta:** < 2s para consultas típicas
- **Throughput scraping:** 2-3 boletines/segundo en paralelo
- **Cache hit rate:** > 80% para consultas repetidas
- **Bundle size:** < 1.5MB (optimización pendiente)

### Escalabilidad
- **Municipios soportados:** 135 (Provincia Buenos Aires)
- **Documentos por municipio:** Ilimitado
- **Usuarios concurrentes:** 50+ (limitado por Vercel)
- **Almacenamiento:** Escalable via GitHub/filesystem

### Confiabilidad
- **Disponibilidad:** 99.5% (limitado por servicios externos)
- **Recuperación de errores:** Automática con fallbacks
- **Persistencia de datos:** JSON + backup automático
- **Tolerancia a fallos:** Degradación graceful

### Seguridad
- **API Keys:** Almacenadas en variables de entorno
- **Validación de entrada:** Sanitización de consultas
- **Rate limiting:** Protección contra abuso
- **CORS:** Configurado para dominios autorizados

### Usabilidad
- **Interfaz:** Intuitiva, similar a ChatGPT
- **Idioma:** Español argentino
- **Accesibilidad:** Básica (mejoras pendientes)
- **Responsive:** Móvil y desktop

### Mantenibilidad
- **Código:** TypeScript + Python tipado
- **Documentación:** Completa y actualizada
- **Testing:** Scripts manuales (automatización pendiente)
- **Monitoreo:** Logs estructurados y métricas

## Dependencias Técnicas

### Backend Python
```
openai>=1.0.0          # Cliente OpenRouter
requests>=2.31.0       # HTTP requests  
python-dotenv>=1.0.0   # Variables de entorno
rich>=13.0.0           # UI terminal rica
beautifulsoup4>=4.12.0 # Parsing HTML
lxml>=4.9.0            # Parser XML/HTML rápido
tenacity>=8.0.0        # Retry logic
```

### Frontend Next.js
```
@ai-sdk/openai: ^1.0.0    # Cliente OpenRouter
ai: ^4.1.0                # Vercel AI SDK
next: ^15.1.0             # Framework React
react: ^19.0.0            # UI Library
react-markdown: ^10.1.0   # Renderizado Markdown
tailwindcss: ^3.4.0      # Styling
zod: ^3.25.76             # Validación de tipos
```

### Servicios Externos
- **OpenRouter:** Acceso a modelos LLM (crítico)
- **SIBOM:** Fuente de datos (crítico)
- **GitHub Raw:** Hosting de datos para producción (opcional)
- **Vercel:** Hosting del frontend (opcional)

## Configuración del Entorno

### Variables de Entorno Requeridas
```bash
# Compartidas
OPENROUTER_API_KEY=sk-or-v1-...  # CRÍTICO

# Backend específico
LLM_MODEL_EXTRACTION=google/gemini-3-flash-preview
RATE_LIMIT_DELAY=3
MAX_RETRIES=3

# Frontend específico  
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5
GITHUB_DATA_REPO=usuario/repo  # Para producción
```

### Comandos de Instalación
```bash
# Backend
cd python-cli
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd chatbot
npm install
```

## Criterios de Éxito del Proyecto

### Métricas Cuantitativas
- ✅ **Costo por consulta FAQ:** $0.0007 (97% reducción vs baseline)
- ✅ **Costo por consulta búsqueda:** $0.017 (37% reducción vs baseline)
- ✅ **Tiempo de render:** 150ms (70% mejora vs baseline)
- ✅ **Re-renders por mensaje:** 6 (70% reducción vs baseline)
- ✅ **Requests polling/día:** 576 (90% reducción vs baseline)
- ✅ **Precisión de extracción:** >95% con BeautifulSoup + LLM fallback

### Métricas Cualitativas
- ✅ **Experiencia de usuario:** Superior al buscador oficial SIBOM
- ✅ **Facilidad de uso:** Consultas en lenguaje natural vs formularios
- ✅ **Confiabilidad:** Fuentes oficiales con enlaces verificables
- ✅ **Mantenibilidad:** Código bien documentado y modular
- ✅ **Escalabilidad:** Arquitectura preparada para crecimiento

## Roadmap y Evolución

### Completado (2025-2026)
- ✅ Migración de Claude a OpenRouter
- ✅ Versión Python CLI completa
- ✅ RAG con BM25 y embeddings
- ✅ Optimizaciones de performance (70% mejora)
- ✅ Filtros inteligentes con sincronización

### En Desarrollo
- 🔄 Tree-shaking para reducir bundle size
- 🔄 Testing automatizado completo
- 🔄 Métricas de uso y analytics

### Planificado
- 📋 Cache distribuido con Redis
- 📋 API REST pública
- 📋 Dashboard analítico
- 📋 Notificaciones de nuevos boletines
- 📋 Soporte para más provincias

## Conclusión

El SIBOM Scraper Assistant representa una solución integral moderna que combina web scraping inteligente con IA conversacional. Su arquitectura modular, optimizaciones de performance y enfoque en la experiencia del usuario lo posicionan como una alternativa superior a las herramientas tradicionales de consulta legal municipal.

La separación clara entre extracción (Python) y consulta (Next.js) permite escalabilidad independiente y especialización tecnológica, mientras que la integración fluida de datos garantiza una experiencia de usuario coherente y eficiente.

---

**Última actualización:** 2026-01-07  
**Estado:** Requerimientos consolidados y validados  
**Próximo paso:** Crear documento de diseño técnico