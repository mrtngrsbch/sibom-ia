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
    const { messages, municipality } = body;

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

    // Obtener mensajes anteriores (excluir system)
    const recentMessages = messages.filter(
      (m: { role: string }) => m.role !== 'system'
    );

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


    const [retrievedContext, stats] = await Promise.all([
      retrieveContext(query, { municipality, limit: 5 }),
      getDatabaseStats()
    ]);

    // Cargar y construir prompt del sistema desde archivo externo
    const promptPath = path.join(process.cwd(), 'src', 'prompts', 'system.md');
    let systemPromptTemplate = '';
    try {
      systemPromptTemplate = await fs.readFile(promptPath, 'utf-8');
    } catch (err) {
      console.error('[ChatAPI] Error leyendo system prompt:', err);
      // Fallback básico si falla la lectura
      systemPromptTemplate = 'Eres un asistente legal municipal. Contexto: {{context}}';
    }

    const statsText = `MUNICIPIOS DISPONIBLES: ${stats.municipalityList.join(', ')}\nTOTAL: ${stats.totalDocuments} documentos.`;
    const sourcesText = retrievedContext.sources.length > 0
      ? retrievedContext.sources.map((s: any) => `- ${s.type.toUpperCase()} ${s.title} - ${s.municipality} [Estado: ${s.status}] (${s.url})`).join('\n')
      : 'Sin fuentes específicas.';

    const systemPrompt = systemPromptTemplate
      .replace('{{stats}}', statsText)
      .replace('{{context}}', retrievedContext.context || 'No se encontró información específica.')
      .replace('{{sources}}', sourcesText);

    // Log del prompt para depuración (solo los primeros 200 caracteres)
    console.log(`[ChatAPI] System Prompt construido (${systemPrompt.length} caracteres): ${systemPrompt.slice(0, 200)}...`);

    // Determinar modelo (usar Claude 3.5 Sonnet por defecto en OpenRouter)
    let modelId = process.env.ANTHROPIC_MODEL || 'anthropic/claude-3.5-sonnet';
    
    // Asegurar formato correcto para OpenRouter si viene de env var
    if (modelId.startsWith('claude-') && !modelId.includes('/')) {
      modelId = `anthropic/${modelId}`;
    }

    console.log(`[ChatAPI] Llamando a OpenRouter con modelo: ${modelId}`);

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
        maxTokens: 2000,
        onFinish: () => {
          const duration = Date.now() - startTime;
          console.log(`[ChatAPI] Respuesta completada en ${duration}ms`);
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
