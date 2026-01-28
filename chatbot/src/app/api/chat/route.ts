/**
 * route.ts (API Chat)
 *
 * Endpoint principal para el chat. Integra Vercel AI SDK con OpenRouter.
 * Procesa la consulta del usuario, recupera contexto mediante RAG y
 * genera una respuesta en streaming incluyendo metadatos de fuentes.
 *
 * @version 1.3.0
 * @created 2025-12-31
 * @modified 2025-12-31
 * @author Kilo Code
 *
 * @dependencies
 *   - ai: ^4.1.0
 *   - @ai-sdk/openai: ^1.0.0
 */

import { createOpenAI } from '@ai-sdk/openai';
import { streamText, convertToCoreMessages, StreamData, tool } from 'ai';
import { z } from 'zod';
import { retrieveContext, getDatabaseStats } from '@/lib/rag/retriever';
import { retrieveWithComputation, type ComputationalSearchResult } from '@/lib/rag/computational-retriever';
import {
  needsRAGSearch,
  calculateOptimalLimit,
  getOffTopicResponse,
  isFAQQuestion,
  isComputationalQuery,
  classifyQueryIntent,
  generateDirectResponse
} from '@/lib/query-classifier';
import { extractFiltersFromQuery } from '@/lib/query-filter-extractor';
import {
  isComparisonQuery,
  handleComparisonQuery,
  type ComparisonResult
} from '@/lib/rag/sql-retriever';
import { generateDataCatalog, generateConciseCatalog } from '@/lib/data-catalog';
import fs from 'fs/promises';
import path from 'path';

// Type guard para verificar si es un resultado computacional
function isComputationalResult(result: any): result is ComputationalSearchResult {
  return result && typeof result === 'object' && 'computationResult' in result;
}

export const maxDuration = 60;

/**
 * API Route para el chat
 * @route POST /api/chat
 */
export async function POST(req: Request) {
  console.log('[ChatAPI] Nueva petición recibida');
  const startTime = Date.now();

  try {
    const body = await req.json();
    console.log(`[ChatAPI] Body recibido: ${JSON.stringify(body).slice(0, 200)}...`);

    // Extraer mensajes y filtros
    const { messages, municipality, filters = {} } = body;

    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
      console.error('[ChatAPI] Error: OPENROUTER_API_KEY no encontrada');
      return new Response(JSON.stringify({ error: 'Configuración incompleta: Falta API Key' }), { status: 500 });
    }

    console.log(`[ChatAPI] API Key detectada (longitud: ${apiKey.length}, comienza con: ${apiKey.slice(0, 10)}...)`);

    // Configurar OpenRouter dentro de la petición para asegurar acceso a env vars
    const openrouter = createOpenAI({
      apiKey: apiKey,
      baseURL: 'https://openrouter.ai/api/v1',
      headers: {
        'HTTP-Referer': 'https://github.com/mrtngrsbch/sibom-ia',
        'X-Title': 'SIBOM Scraper Assistant',
      }
    });

    if (!messages || !Array.isArray(messages)) {
      return new Response('Mensajes inválidos', { status: 400 });
    }

    // Obtener mensajes anteriores (excluir system) - Limitar a 10 mensajes (5 intercambios)
    const recentMessages = messages
      .filter((m: { role: string }) => m.role !== 'system')
      .slice(-10);  // Solo últimos 10 mensajes para reducir tokens

    console.log(`[ChatAPI] Mensajes recientes: ${recentMessages.length}`);
    recentMessages.forEach((m: any, i: number) => {
      console.log(`  [${i}] ${m.role}: ${typeof m.content === 'string' ? m.content.slice(0, 30) : 'non-string content'}`);
    });

    // Recuperar contexto relevante usando RAG
    const lastUserMessage = recentMessages.findLast(
      (m: { role: string }) => m.role === 'user'
    );
    const query =
      typeof lastUserMessage?.content === 'string'
        ? lastUserMessage.content
        : '';

    console.log(`[ChatAPI] Consulta: "${query.slice(0, 50)}..."`);

    // Determinar si necesita búsqueda RAG
    // PRIORIDAD: 1. FAQ, 2. RAG normal
    const isFAQ = isFAQQuestion(query);
    const shouldSearch = !isFAQ && needsRAGSearch(query);
    console.log(`[ChatAPI] Necesita RAG: ${shouldSearch} (isFAQ: ${isFAQ})`);

    // Si es off-topic, marcar para debugging
    if (!shouldSearch && !isFAQ) {
      console.log(`[ChatAPI] Pregunta fuera de tema detectada: "${query.slice(0, 50)}..."`);
    }

    // Obtener estadísticas primero (necesitamos municipalityList para extracción)
    const stats = await getDatabaseStats();

    // Construir opciones de búsqueda con todos los filtros (UI + extraídos de query)
    const uiFilters = {
      municipality: filters.municipality || municipality, // Soportar ambos formatos
      type: filters.ordinanceType !== 'all' ? filters.ordinanceType : undefined,
      dateFrom: filters.dateFrom,
      dateTo: filters.dateTo
    };

    // Extraer filtros automáticamente de la query
    // Estrategia A: Auto-aplicar municipio/año/tipo detectado en la query
    const enhancedFilters = extractFiltersFromQuery(query, stats.municipalityList, uiFilters);

    const hasFilters = !!(enhancedFilters.municipality || enhancedFilters.type || enhancedFilters.dateFrom || enhancedFilters.dateTo);
    const optimalLimit = calculateOptimalLimit(query, hasFilters);

    // Determinar si el filtro de tipo es MANUAL (UI) o AUTOMÁTICO (detectado de query)
    // isManualTypeFilter = true solo cuando el usuario seleccionó explícitamente en el dropdown
    const isManualTypeFilter = uiFilters.type !== undefined && uiFilters.type === enhancedFilters.type;

    // Detectar si es query de listado masivo (muchos resultados esperados)
    const isMassiveListing = optimalLimit >= 100 && hasFilters;
    
    // Para listados masivos, NO limitar (recuperar todos los que coincidan)
    // El usuario quiere ver TODOS los resultados, no una muestra
    const adjustedLimit = isMassiveListing ? 10000 : optimalLimit; // Sin límite práctico para listados

    const searchOptions = {
      ...enhancedFilters,
      limit: adjustedLimit,
      isManualTypeFilter
    };

    console.log(`[ChatAPI] Filtros UI: ${JSON.stringify(uiFilters)}`);
    console.log(`[ChatAPI] Filtros extraídos de query: ${JSON.stringify(enhancedFilters)}`);
    console.log(`[ChatAPI] Tipo manual: ${isManualTypeFilter}`);
    console.log(`[ChatAPI] Límite dinámico: ${adjustedLimit} docs (filtros: ${hasFilters}, listado masivo: ${isMassiveListing})`);

    // Detectar si es query de comparación entre municipios (usar SQL)
    const isSQLComparison = isComparisonQuery(query);
    
    console.log(`[ChatAPI] Query de comparación SQL: ${isSQLComparison}`);
    
    // Si es comparación SQL, usar SQL retriever directamente
    let sqlComparisonResult: ComparisonResult | null = null;
    if (shouldSearch && isSQLComparison) {
      console.log('[ChatAPI] 🗄️ Usando SQL retriever para query comparativa');
      sqlComparisonResult = await handleComparisonQuery(query);
      
      if (sqlComparisonResult.success) {
        console.log(`[ChatAPI] ✅ SQL comparison exitosa: ${sqlComparisonResult.answer}`);
        console.log(`[ChatAPI] 📊 Datos: ${sqlComparisonResult.data.length} municipios`);
      } else {
        console.log(`[ChatAPI] ❌ SQL comparison falló, usando RAG normal`);
      }
    }

    // Recuperar contexto con los filtros mejorados
    let retrievedContext;
    if (shouldSearch && !isSQLComparison) {
      // Queries normales: usar RAG
      console.log('[ChatAPI] 📄 Usando retrieveContext normal');
      retrievedContext = await retrieveContext(query, searchOptions);
    } else if (shouldSearch && isSQLComparison && !sqlComparisonResult?.success) {
      // SQL falló: fallback a RAG
      console.log('[ChatAPI] 📄 Fallback a retrieveContext (SQL falló)');
      retrievedContext = await retrieveContext(query, searchOptions);
    } else {
      retrievedContext = { context: '', sources: [] };
    }

    // Log de fuentes recuperadas (después de inicializar retrievedContext)
    console.log(`[ChatAPI] 📊 Fuentes recuperadas: ${retrievedContext.sources?.length || 0}`);

    // ============================================================================
    // 🗄️ SQL COMPARISON - BYPASS COMPLETO DEL LLM (ÚNICO BYPASS PERMITIDO)
    // ============================================================================
    // Si es comparación SQL exitosa, generar respuesta directa sin LLM
    if (sqlComparisonResult?.success) {
      console.log(`[ChatAPI] 🗄️ SQL COMPARISON EXITOSA - Generando respuesta directa`);
      console.log(`[ChatAPI] 💰 Ahorro estimado: ~150,000 tokens (~$0.45)`);
      
      // Construir respuesta con markdown table
      const directResponse = sqlComparisonResult.answer + (sqlComparisonResult.markdown || '');
      
      // Crear StreamData para metadatos
      const data = new StreamData();
      
      // No hay sources individuales en comparaciones SQL
      data.append({
        type: 'sources',
        sources: []
      });
      
      data.append({
        type: 'usage',
        usage: {
          promptTokens: 0,
          completionTokens: 0,
          totalTokens: 0,
          model: 'sql-direct-response (comparison)'
        }
      });

      data.close();

      // Crear stream compatible con Vercel AI SDK manualmente
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        start(controller) {
          // Enviar el texto en formato de stream de Vercel AI
          controller.enqueue(encoder.encode(`0:"${directResponse.replace(/"/g, '\\"').replace(/\n/g, '\\n')}"\n`));
          
          // Enviar metadatos de sources
          controller.enqueue(encoder.encode(`2:[${JSON.stringify({type:'sources',sources:[]})}]\n`));
          
          // Enviar metadatos de usage
          controller.enqueue(encoder.encode(`2:[${JSON.stringify({type:'usage',usage:{promptTokens:0,completionTokens:0,totalTokens:0,model:'sql-direct-response (comparison)'}})}]\n`));
          
          controller.close();
        }
      });

      return new Response(stream, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'X-Vercel-AI-Data-Stream': 'v1'
        }
      });
    }

    // ============================================================================
    // 🤖 SIEMPRE USAR LLM PARA QUERIES DE NORMATIVAS
    // ============================================================================
    // El LLM es lo suficientemente inteligente para entender cualquier query:
    // - "sueldos de carlos tejedor 2025" → busca en contenido sobre salarios
    // - "decretos de carlos tejedor 2025" → lista todos los decretos
    // - "ordenanza 2947" → encuentra la ordenanza específica
    // - "cuántas ordenanzas hay" → cuenta y explica
    //
    // STOP TRYING TO BE CLEVER! Let the LLM do its job.
    console.log(`[ChatAPI] 🤖 Usando LLM para interpretar query y generar respuesta`);

    // Determinar tipo de respuesta según el contexto
    let systemPromptTemplate = '';

    if (!shouldSearch && isFAQQuestion(query)) {
      // Caso 2: Pregunta sugerida/FAQ - responder promoviendo NUESTRO CHAT
      const dataCatalog = generateConciseCatalog();
      
      systemPromptTemplate = `Eres un asistente para nuestro chatbot de legislación municipal.

CONTEXTO CRÍTICO DEL PROYECTO:
- Nuestro chat es la ALTERNATIVA SUPERIOR al buscador de SIBOM
- SIBOM tiene un buscador ineficiente y confuso
- Los usuarios vienen aquí porque somos MEJORES que SIBOM
- SIBOM es la FUENTE de datos (buena) pero su BUSCADOR es malo

REGLAS ABSOLUTAS:
1. ❌ NUNCA digas "ingresá a sibom.slyt.gba.gob.ar"
2. ❌ NUNCA recomiendes usar el buscador de SIBOM
3. ❌ NUNCA expliques cómo buscar EN SIBOM
4. ✅ SÍ explica cómo buscar en NUESTRO CHAT
5. ✅ SÍ menciona SIBOM como fuente oficial (solo en enlaces de verificación)
6. ✅ SÍ promociona nuestro chat como herramienta superior

CÓMO BUSCAR EN NUESTRO CHAT:
1. **Filtro de municipio** arriba (seleccionar municipio en el dropdown)
2. **Escribir en lenguaje natural** lo que buscas (ej: "ordenanzas de tránsito")
3. **Mencionar número** de norma si lo conocés (ej: "ordenanza 2833")
4. **Usar fechas** mencionándolas en la pregunta (ej: "decretos de 2024")

MUNICIPIOS CON DATOS DISPONIBLES (${stats.municipalities} de 135):
${stats.municipalityList.join(', ')}

TOTAL DE DOCUMENTOS DISPONIBLES: ${stats.totalDocuments}

${dataCatalog}

IMPORTANTE: Los municipios listados son los ÚNICOS con datos scrapeados.
El resto (${135 - stats.municipalities} municipios) NO tienen información aún.

Responde a la pregunta del usuario explicando cómo usar NUESTRO CHAT (no SIBOM).
Sé conciso, claro y promociona nuestras ventajas sobre el buscador de SIBOM.`;
    } else if (!shouldSearch && !isFAQQuestion(query)) {
      // Caso 3: Pregunta fuera de tema (NO es FAQ) - usar prompt off-topic
      const offTopicResponse = getOffTopicResponse(query);

      // ✅ FIX: En vez de devolver JSON plano (rompe el stream parser),
      // usar un systemPrompt simple con la respuesta off-topic
      systemPromptTemplate = `Responde EXACTAMENTE este mensaje al usuario (no agregues nada más):

${offTopicResponse || "Disculpá, pero mi especialidad son las ordenanzas y normativas municipales. ¿Tenés alguna consulta sobre ese tema? 📋"}`;
    } else {
      // Caso 4: Búsqueda normal - cargar prompt desde archivo
      const promptPath = path.join(process.cwd(), 'src', 'prompts', 'system.md');
      try {
        // Verificar que el archivo existe y es un archivo regular
        const stats = await fs.stat(promptPath);
        if (!stats.isFile()) {
          throw new Error(`${promptPath} no es un archivo regular`);
        }
        systemPromptTemplate = await fs.readFile(promptPath, 'utf-8');
        
        // Inyectar catálogo de datos en el prompt
        const dataCatalog = generateDataCatalog();
        systemPromptTemplate = systemPromptTemplate.replace('{{data_catalog}}', dataCatalog);
      } catch (err) {
        console.error('[ChatAPI] Error leyendo system prompt:', err instanceof Error ? err.message : err);
        // Fallback básico si falla la lectura
        systemPromptTemplate = 'Eres un asistente legal municipal. Contexto: {{context}}';
      }
    }

    // Construir system prompt final
    let systemPrompt = systemPromptTemplate;

    // Solo inyectar contexto RAG si es búsqueda normal (no off-topic)
    if (shouldSearch) {
      const needsStats = /municipios.*disponibles|cuántos municipios|qué municipios/i.test(query);
      const statsText = needsStats
        ? `IMPORTANTE: La Provincia de Buenos Aires tiene 135 municipios en total.

MUNICIPIOS CON DATOS SCRAPEADOS (${stats.municipalities} de 135):
${stats.municipalityList.join(', ')}

TOTAL DE DOCUMENTOS DISPONIBLES: ${stats.totalDocuments}

NOTA CRÍTICA: Los municipios listados arriba son los ÚNICOS que tienen información disponible en la base de datos. El resto de los municipios (${135 - stats.municipalities}) NO tienen datos scrapeados aún.`
        : '';

      // ✅ FIX: Para listados masivos (>50), NO enviar todas las sources al LLM
      // Solo enviar resumen agregado para ahorrar tokens
      const sourcesText = retrievedContext.sources.length > 0
        ? (retrievedContext.sources.length > 50
            ? `RESUMEN: ${retrievedContext.sources.length} normativas encontradas (listado completo disponible en UI)`
            : retrievedContext.sources.map((s: any) => {
                const typeLabel = s.documentTypes && s.documentTypes.length > 0
                  ? s.documentTypes.map((t: string) => t.toUpperCase()).join(', ')
                  : s.type.toUpperCase();
                return `- ${typeLabel} ${s.title} - ${s.municipality} [Estado: ${s.status}] (${s.url})`;
              }).join('\n')
          )
        : '';

      // Construir texto de filtros aplicados
      const filtersApplied = filters.municipality || filters.ordinanceType || filters.dateFrom || filters.dateTo
        ? `\n\nFILTROS APLICADOS EN ESTA BÚSQUEDA:\n${filters.municipality ? `- Municipio: ${filters.municipality}\n` : ''}${filters.ordinanceType && filters.ordinanceType !== 'all' ? `- Tipo de norma: ${filters.ordinanceType}\n` : ''}${filters.dateFrom ? `- Desde: ${filters.dateFrom}\n` : ''}${filters.dateTo ? `- Hasta: ${filters.dateTo}\n` : ''}`
        : '';

      // Para queries computacionales, agregar el resultado al contexto
      let contextToUse = retrievedContext.context || 'No se encontró información específica.';
      if (isComputationalResult(retrievedContext) && retrievedContext.computationResult?.success) {
        const compResult = retrievedContext.computationResult;
        let computationContext = `\n\n## 🔢 RESULTADO COMPUTACIONAL\n\n${compResult.answer}\n`;
        if (compResult.markdown) {
          computationContext += `\n${compResult.markdown}\n`;
        }
        contextToUse = contextToUse + computationContext;
        console.log('[ChatAPI] ✅ Resultado computacional agregado al contexto');
      }

      // Para listados masivos, agregar instrucción especial
      let massiveListingInstruction = '';
      if (isMassiveListing && retrievedContext.sources.length > 50) {
        massiveListingInstruction = `\n\n## ⚠️ INSTRUCCIÓN CRÍTICA - LISTADO MASIVO (${retrievedContext.sources.length} RESULTADOS)

**🚨 REGLAS ABSOLUTAS - NO NEGOCIABLES:**

1. ❌ **PROHIBIDO GENERAR LISTA** - NO escribas ninguna lista numerada o con viñetas
2. ❌ **PROHIBIDO CONTAR MANUALMENTE** - NO digas "Encontré X decretos:" seguido de lista
3. ❌ **PROHIBIDO DUPLICAR** - La lista ya se muestra automáticamente en "Fuentes Consultadas"

4. ✅ **SOLO PERMITIDO:** Resumen de 2-3 líneas máximo:
   - Línea 1: "Se encontraron ${retrievedContext.sources.length} ${enhancedFilters.type || 'normativas'} de ${enhancedFilters.municipality || 'este municipio'}${enhancedFilters.dateFrom ? ' del año ' + new Date(enhancedFilters.dateFrom).getFullYear() : ''}."
   - Línea 2 (opcional): Mencionar rango de números si es relevante
   - Línea 3: "La lista completa con enlaces está disponible en la sección 'Fuentes Consultadas' más abajo."

**EJEMPLO CORRECTO:**
"Se encontraron 1,249 decretos de Carlos Tejedor del año 2025. La lista completa con enlaces está disponible en la sección 'Fuentes Consultadas' más abajo."

**EJEMPLO INCORRECTO (NO HACER):**
"Encontré 100 decretos de Carlos Tejedor en 2025:
1. Decreto 1/25 - ...
2. Decreto 2/25 - ...
[...]"

**RECORDATORIO:** El usuario ya verá TODOS los ${retrievedContext.sources.length} resultados en "Fuentes Consultadas". Tu trabajo es SOLO resumir, NO listar.`;
      }

      systemPrompt = systemPromptTemplate
        .replace('{{stats}}', statsText)
        .replace('{{context}}', contextToUse)
        .replace('{{sources}}', sourcesText) + filtersApplied + massiveListingInstruction;
    }
    // Para off-topic, systemPrompt ya está completo (no necesita contexto RAG)

    // Log del prompt para depuración (solo los primeros 200 caracteres)
    console.log(`[ChatAPI] System Prompt construido (${systemPrompt.length} caracteres): ${systemPrompt.slice(0, 200)}...`);

    // Determinar modelo según tipo de query
    let modelId: string;

    if (isFAQ) {
      // Modelo económico para FAQ (configurable via env)
      modelId = process.env.LLM_MODEL_ECONOMIC || 'google/gemini-flash-1.5';
      console.log(`[ChatAPI] Usando modelo económico para FAQ: ${modelId}`);
    } else {
      // Modelo premium para búsquedas complejas (configurable via env)
      // Prioridad: LLM_MODEL_PRIMARY > ANTHROPIC_MODEL (legacy) > default
      modelId = process.env.LLM_MODEL_PRIMARY ||
                process.env.ANTHROPIC_MODEL ||
                'anthropic/claude-3.5-sonnet';

      // Asegurar formato correcto para OpenRouter si viene de env var
      if (modelId.startsWith('claude-') && !modelId.includes('/')) {
        modelId = `anthropic/${modelId}`;
      }

      console.log(`[ChatAPI] Usando modelo premium para búsqueda: ${modelId}`);
    }

    // Crear StreamData para enviar metadatos (fuentes) al frontend
    const data = new StreamData();

    // Enviar las fuentes como metadatos
    try {
      // Convertir Source[] a un formato compatible con StreamData
      const sourcesPlain = retrievedContext.sources.map(s => ({
        title: s.title,
        url: s.url,
        municipality: s.municipality,
        type: s.type,
        status: s.status,
        documentTypes: s.documentTypes
      }));
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data.append({
        type: 'sources',
        sources: sourcesPlain
      } as any);
    } catch (appendError) {
      console.error('[ChatAPI] Error al añadir fuentes a StreamData:', appendError);
    }

    // Generar respuesta con streaming
    try {
      console.log(`[ChatAPI] Iniciando streamText con modelo: ${modelId}`);
      
      const coreMessages = convertToCoreMessages(recentMessages);
      console.log(`[ChatAPI] Enviando ${coreMessages.length} mensajes al LLM`);

      const result = streamText({
        model: openrouter(modelId),
        system: systemPrompt,
        messages: coreMessages,
        temperature: 0.3,
        // Para listados masivos, reducir tokens para forzar respuesta breve
        maxTokens: isMassiveListing ? 500 : 4000,
        onFinish: (completion) => {
          const duration = Date.now() - startTime;
          console.log(`[ChatAPI] Respuesta completada en ${duration}ms`);

          // Enviar información de tokens y modelo al frontend
          if (completion.usage) {
            data.append({
              type: 'usage',
              usage: {
                promptTokens: completion.usage.promptTokens,
                completionTokens: completion.usage.completionTokens,
                totalTokens: completion.usage.totalTokens,
                model: modelId // Incluir el modelo usado
              }
            });
            console.log(`[ChatAPI] Tokens usados - Prompt: ${completion.usage.promptTokens}, Completion: ${completion.usage.completionTokens}, Total: ${completion.usage.totalTokens}, Model: ${modelId}`);
          }

          data.close();
        },
      });

      return result.toDataStreamResponse({
        data,
        getErrorMessage: (error: any) => {
          console.error('[ChatAPI] Error en el stream:', error);
          data.close();
          return error?.message || 'Error en el flujo de datos';
        }
      });
    } catch (streamError: any) {
      console.error('[ChatAPI] Error crítico al iniciar streamText:', streamError);
      data.close();
      
      return new Response(
        JSON.stringify({
          error: 'Error al conectar con el modelo de IA',
          details: streamError.message
        }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }
  } catch (error: any) {
    console.error('[ChatAPI] Error fatal:', error);
    
    // Si es un error de autenticación de OpenRouter/LLM
    const errorMessage = error?.message || 'Error interno del servidor';
    const statusCode = error?.status || 500;

    return new Response(
      JSON.stringify({
        error: errorMessage,
        details: error?.data || error?.cause || String(error)
      }),
      {
        status: statusCode,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}
