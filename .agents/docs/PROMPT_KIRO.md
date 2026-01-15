# Prompt para Kiro - Análisis Completo del Proyecto

## Copiar y pegar este prompt en Kiro (Spec Mode)

---

```
Analiza este proyecto completo de forma integral y profunda.

## CONTEXTO
Este es un ecosistema de DOS partes integradas:

1. **Backend Python** (`python-cli/`): Scraper de boletines municipales de SIBOM
   - Extrae boletines usando LLMs
   - Genera JSON estructurados
   - Exporta a CSV

2. **Frontend Next.js** (`chatbot/`): Chatbot con RAG
   - Consulta los boletines extraídos
   - Usa búsqueda semántica (BM25/embeddings)
   - Responde preguntas sobre legislación municipal

AMBAS partes son IGUALMENTE importantes.

## LO QUE NECESITO QUE ANALICES

### 1. Arquitectura y Componentes (Spec)

**Backend Python:**
- ¿Cuál es el flujo principal del scraper?
- ¿Cómo funciona la extracción con LLMs?
- ¿Cómo se estructura y almacena los datos (JSON, CSV)?

**Frontend Next.js:**
- ¿Cómo está estructurada la app Next.js?
- ¿Cómo funciona el chatbot RAG?
- ¿Cómo se integra con los datos del backend?

**Integración:**
- ¿Cómo se comunican ambas partes?
- ¿Qué datos comparten?
- ¿Cuál es el flujo completo: scraping → consulta?

### 2. Convenciones y Estilo (Vibe)
- ¿Qué patrones de código se usan consistently?
- ¿Qué estilo de documentación tienen los archivos?
- ¿Cómo se manejan errores y logging?
- ¿Qué preferencias técnicas son evidentes?
- ¿Qué decisiones de diseño reflejan los CHANGELOGs?

### 3. Configuración y Entorno
- ¿Cómo se configura el proyecto (env, requirements)?
- ¿Qué dependencias clave tiene?
- ¿Cómo se ejecutan los diferentes comandos?

## RESTRICCIONES IMPORTANTES

🚫 **NO MODIFICAR NINGÚN CÓDIGO**
🚫 **NO CREAR NUEVOS ARCHIVOS DE CÓDIGO**
🚫 **SOLO GENERAR DOCUMENTACIÓN DE ANÁLISIS**

## OUTPUT ESPERADO

Genera una estructura .kiro/ completa con:

```
.kiro/
├── specs/
│   ├── 01-proyecto-overview.md          # Ecosistema completo (backend + frontend)
│   ├── 02-backend-scraper.md            # Arquitectura del scraper Python
│   ├── 03-frontend-chatbot.md           # Arquitectura del chatbot Next.js
│   ├── 04-integracion.md                # Cómo se comunican ambas partes
│   ├── 05-data-pipeline.md              # Flujo: scraping → JSON → consulta RAG
│   └── 06-llm-integration.md            # Uso de OpenRouter en ambas partes
├── steering/
│   ├── python-style.md                  # Patrones y convenciones Python
│   ├── typescript-react-style.md        # Patrones y convenciones TypeScript/React
│   ├── error-handling.md                # Cómo se manejan errores
│   ├── llm-usage.md                     # Uso de modelos y costos
│   └── documentation-style.md           # Estilo de documentación
└── hooks/
    ├── testing.md                       # Automatización de tests (ambas partes)
    ├── deployment.md                    # Deploy y distribución
    └── data-processing.md               # Procesamiento de datos
```

Para cada archivo incluye:
- Descripción detallada basada en el código real
- Ejemplos concretos del proyecto (no genéricos)
- Referencias a archivos específicos (rutas reales)
- Patrones que observes en el código existente

## ENFOQUE

Sé específico y pragmático:
- ✅ "El scraper usa python-cli/sibom_scraper.py:45-78 para extracción"
- ✅ "El chatbot hace RAG en chatbot/src/lib/rag/retriever.ts"
- ❌ "El scraper tiene funciones de extracción"

Cita rutas de archivos reales, nombres de funciones, y patrones que observes.
Lee:
- README.md (raíz)
- python-cli/README.md
- python-cli/CHANGELOG*.md
- chatbot/README.md
- Código fuente en python-cli/ y chatbot/src/

---

**Tu objetivo es crear un análisis tan completo que pueda usarse
como documentación técnica del proyecto para futuros desarrolladores.**
```

---

## Instrucciones de uso

1. **Abrir Kiro** en este proyecto
2. **Seleccionar "Spec Mode"**
3. **Copiar y pegar** el prompt anterior
4. **Esperar análisis completo**
5. **Revisar** la carpeta `.kiro/` generada
6. **Volver aquí** y compartimos resultados

## Lo que buscaré en los resultados

- ✅ ¿Entendió que es un scraper SIBOM con LLM?
- ✅ ¿Capturó los 3 niveles (listado → enlaces → texto)?
- ✅ ¿Mencionó el modelo gratuito GLM-4.5-air?
- ✅ ¿Identificó el chatbot en `/chatbot`?
- ✅ ¿Entendió la estructura Python CLI?
- ✅ ¿Capturó las convenciones de tus CHANGELOGs?

## After action

Una vez que Kiro genere los archivos:
1. Copiá acá algunos ejemplos de lo que generó
2. Identificamos qué está bueno y qué falta
3. Extraemos lo mejor a `.agents/`
4. Diseñamos el sincronizador
