/**
 * route.ts — API Chat endpoint
 *
 * Orquestador delgado: parsea request -> clasifica -> delega -> responde.
 * Toda la lógica pesada vive en handlers/.
 *
 * @version 2.1.0 — Migrated to AI SDK v5
 */
import { createOpenRouter } from '@openrouter/ai-sdk-provider';
import { streamText, type UIMessage } from 'ai';
import {
  needsRAGSearch,
  calculateOptimalLimit,
  isFAQQuestion,
} from '@/lib/query-classifier';
import { extractFiltersFromQuery, extractConversationContext } from '@/lib/query-filter-extractor';
import { getStats, retrieveAndRerank } from './handlers/rag-handler';
import { tryHandleSQLComparison, buildSQLDirectResponse } from './handlers/sql-handler';
import { buildFAQPrompt, buildOffTopicPrompt, buildRAGPrompt } from './handlers/prompt-builder';
import type { ChatMessageInput, EnhancedFilters } from './types';
import type { Source } from '@/lib/rag/retriever';

// Tipo de mensaje personalizado con metadata
export type ChatUIMessage = UIMessage<{
  sources?: Source[];
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
    model: string;
  };
}>;

export const maxDuration = 60;

// Crear proveedor OpenRouter
const openrouter = createOpenRouter({
  apiKey: process.env.OPENROUTER_API_KEY,
});

export async function POST(req: Request) {
  console.log('[ChatAPI] Nueva petición recibida');
  const startTime = Date.now();

  try {
    // 1. Parse & validate
    const { messages } = await req.json();
    if (!messages || !Array.isArray(messages)) {
      return new Response('Mensajes inválidos', { status: 400 });
    }

    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'Configuración incompleta: Falta API Key' }), { status: 500 });
    }

    // 2. Extract query from last user message
    const recentMessages: ChatMessageInput[] = messages
      .filter((m: ChatMessageInput) => m.role !== 'system')
      .slice(-10);

    const lastUserMessage = recentMessages.findLast((m) => m.role === 'user');
    const query = typeof lastUserMessage?.content === 'string' ? lastUserMessage.content : '';
    console.log(`[ChatAPI] Query: "${query.slice(0, 60)}..."`);

    // 3. Classify intent
    const isFAQ = isFAQQuestion(query);
    const shouldSearch = !isFAQ && needsRAGSearch(query);
    console.log(`[ChatAPI] RAG: ${shouldSearch}, FAQ: ${isFAQ}`);

    // 4. Get stats (needed for filters extraction and prompts)
    const stats = await getStats();

    // 5. Extract filters from conversation + query
    const conversationContext = extractConversationContext(recentMessages, stats.municipalityList);
    const enhancedFilters: EnhancedFilters = extractFiltersFromQuery(
      query, stats.municipalityList, {}, conversationContext
    );

    const hasFilters = !!(enhancedFilters.municipality || enhancedFilters.type || enhancedFilters.dateFrom || enhancedFilters.dateTo);
    const optimalLimit = calculateOptimalLimit(query, hasFilters);
    const isMassiveListing = optimalLimit >= 100 && hasFilters;

    // 6. SQL comparison bypass (no LLM needed)
    if (shouldSearch) {
      const sqlResult = await tryHandleSQLComparison(query);
      if (sqlResult) {
        console.log(`[ChatAPI] 🗄️ SQL bypass — ${Date.now() - startTime}ms`);
        return buildSQLDirectResponse(sqlResult);
      }
    }

    // 7. RAG retrieval + reranking
    let retrievedContext = { context: '', sources: [] as import('@/lib/rag/retriever').Source[] };

    if (shouldSearch) {
      const searchOptions = {
        ...enhancedFilters,
        limit: isMassiveListing ? 10000 : optimalLimit,
      };
      retrievedContext = await retrieveAndRerank(query, searchOptions);
    }

    // 8. Build system prompt
    let systemPrompt: string;
    if (isFAQ) {
      systemPrompt = buildFAQPrompt(stats);
    } else if (!shouldSearch) {
      systemPrompt = buildOffTopicPrompt(query);
    } else {
      systemPrompt = await buildRAGPrompt({
        query,
        stats,
        retrievedContext,
        enhancedFilters,
        conversationContext,
        isMassiveListing,
      });
    }

    // 9. Select model
    const modelId = isFAQ
      ? (process.env.LLM_MODEL_ECONOMIC || 'zai/glm-4.7')
      : (() => {
          let id = process.env.LLM_MODEL_PRIMARY || process.env.ANTHROPIC_MODEL || 'anthropic/claude-3.5-sonnet';
          if (id.startsWith('claude-') && !id.includes('/')) id = `anthropic/${id}`;
          return id;
        })();

    console.log(`[ChatAPI] Modelo: ${modelId} | Prompt: ${systemPrompt.length} chars`);

    // 10. Stream response using AI SDK v5 streamText
    const model = openrouter.chat(modelId);

    // Convertir mensajes al formato esperado por el SDK
    const coreMessages = recentMessages.map((msg) => ({
      role: msg.role as 'user' | 'assistant' | 'system',
      content: msg.content,
    }));

    const result = streamText({
      model,
      system: systemPrompt,
      messages: coreMessages,
      onFinish({ usage }) {
        const duration = Date.now() - startTime;
        console.log(`[ChatAPI] Completado en ${duration}ms | Tokens: ${usage?.totalTokens ?? 0}`);
      },
    });

    // Return UI message stream response con metadata para useChat hook
    return result.toUIMessageStreamResponse({
      messageMetadata({ part }) {
        // Adjuntar sources cuando termine la generación
        if (part.type === 'finish') {
          return {
            sources: retrievedContext.sources,
            usage: {
              promptTokens: part.totalUsage?.inputTokens ?? 0,
              completionTokens: part.totalUsage?.outputTokens ?? 0,
              totalTokens: part.totalUsage?.totalTokens ?? 0,
              model: modelId,
            },
          };
        }
        return undefined;
      },
    });

  } catch (error: unknown) {
    const err = error as { message?: string; status?: number; data?: unknown; cause?: unknown };
    console.error('[ChatAPI] Error fatal:', err);
    return new Response(
      JSON.stringify({
        error: err.message || 'Error interno del servidor',
        details: err.data || err.cause || String(error),
      }),
      {
        status: err.status || 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}
