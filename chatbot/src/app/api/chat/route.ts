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
import { streamText, convertToCoreMessages, StreamData } from 'ai';
import { retrieveContext, getDatabaseStats } from '@/lib/rag/retriever';
import { needsRAGSearch, calculateOptimalLimit, getOffTopicResponse, isFAQQuestion } from '@/lib/query-classifier';
import { extractFiltersFromQuery } from '@/lib/query-filter-extractor';
import fs from 'fs/promises';
import path from 'path';

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
        'HTTP-Referer': 'https://github.com/sibom-scraper-assistant',
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

    const searchOptions = {
      ...enhancedFilters,
      limit: optimalLimit
    };

    console.log(`[ChatAPI] Filtros UI: ${JSON.stringify(uiFilters)}`);
    console.log(`[ChatAPI] Filtros extraídos de query: ${JSON.stringify(enhancedFilters)}`);
    console.log(`[ChatAPI] Límite dinámico: ${optimalLimit} docs (filtros: ${hasFilters})`);

    // Recuperar contexto con los filtros mejorados
    const retrievedContext = shouldSearch
      ? await retrieveContext(query, searchOptions)
      : { context: '', sources: [] }; // ✅ 0 tokens si no necesita RAG

    // Determinar tipo de respuesta según el contexto
    let systemPromptTemplate = '';

    if (!shouldSearch && isFAQQuestion(query)) {
      // Caso 2: Pregunta sugerida/FAQ - responder promoviendo NUESTRO CHAT
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

      const sourcesText = retrievedContext.sources.length > 0
        ? retrievedContext.sources.map((s: any) => {
            // ✅ Mostrar documentTypes si existen (más específico que type)
            const typeLabel = s.documentTypes && s.documentTypes.length > 0
              ? s.documentTypes.map((t: string) => t.toUpperCase()).join(', ')
              : s.type.toUpperCase();
            return `- ${typeLabel} ${s.title} - ${s.municipality} [Estado: ${s.status}] (${s.url})`;
          }).join('\n')
        : '';

      // Construir texto de filtros aplicados
      const filtersApplied = filters.municipality || filters.ordinanceType || filters.dateFrom || filters.dateTo
        ? `\n\nFILTROS APLICADOS EN ESTA BÚSQUEDA:\n${filters.municipality ? `- Municipio: ${filters.municipality}\n` : ''}${filters.ordinanceType && filters.ordinanceType !== 'all' ? `- Tipo de norma: ${filters.ordinanceType}\n` : ''}${filters.dateFrom ? `- Desde: ${filters.dateFrom}\n` : ''}${filters.dateTo ? `- Hasta: ${filters.dateTo}\n` : ''}`
        : '';

      systemPrompt = systemPromptTemplate
        .replace('{{stats}}', statsText)
        .replace('{{context}}', retrievedContext.context || 'No se encontró información específica.')
        .replace('{{sources}}', sourcesText) + filtersApplied;
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
      data.append({
        type: 'sources',
        sources: retrievedContext.sources
      });
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
        maxTokens: 4000,  // Aumentado para listados largos (98+ ordenanzas)
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
