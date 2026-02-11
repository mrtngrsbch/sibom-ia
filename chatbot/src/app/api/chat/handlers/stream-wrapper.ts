/**
 * stream-wrapper.ts — Inyección de fuentes en el stream
 *
 * Responsabilidad única: envolver el stream del LLM para inyectar
 * las fuentes consultadas al final como annotation oculta.
 */

import type { Source } from '@/lib/rag/retriever';

/**
 * Envuelve un Response stream para inyectar fuentes al final
 */
export function wrapStreamWithSources(
  response: Response,
  sources: Source[]
): Response {
  if (!sources || sources.length === 0) {
    return response;
  }

  const reader = response.body!.getReader();
  const encoder = new TextEncoder();

  const wrappedStream = new ReadableStream({
    async start(controller) {
      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            // Inyectar fuentes al final como annotation oculta
            const sourcesJson = JSON.stringify({ type: 'sources', sources });
            const annotation = `\n\n<!--SOURCES:${sourcesJson}-->`;
            controller.enqueue(encoder.encode(annotation));
            controller.close();
            break;
          }

          controller.enqueue(value);
        }
      } catch (err) {
        console.error('[StreamWrapper] Error en stream:', err);
        controller.error(err);
      }
    },
  });

  return new Response(wrappedStream, {
    headers: response.headers,
  });
}
