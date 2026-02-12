/**
 * route.ts (DEBUG: Chat Stream Format)
 * 
 * Endpoint para diagnosticar exactamente qué formato está generando streamText
 * y compararlo con lo que espera parseDataStreamPart
 */

import { streamText } from 'ai';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

export async function POST(_req: Request) {
  try {
    // await _req.json();  // No necesitamos parsear nada


    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'No API key' }), { status: 500 });
    }

    const openrouter = createOpenRouter({ apiKey });

    // Test stream de prueba muy simple
    const result = streamText({
      model: openrouter('google/gemini-flash-1.5'),
      system: 'Responde en UNA sola línea.',
      messages: [{ role: 'user', content: 'Hola' }],
      temperature: 0.3,
      maxOutputTokens: 100,
    });

    console.log('[CHAT-DEBUG] Métodos disponibles en result:', 
      Object.getOwnPropertyNames(Object.getPrototypeOf(result))
        .filter(m => m.includes('Stream') || m.includes('Response') || m.includes('Pipe')));

    // Probar toUIMessageStreamResponse
    console.log('[CHAT-DEBUG] Probando toUIMessageStreamResponse()...');
    const uiResponse = result.toUIMessageStreamResponse();
    console.log('[CHAT-DEBUG] Headers de UI response:', Object.fromEntries(uiResponse.headers));
    console.log('[CHAT-DEBUG] Body type:', uiResponse.body?.constructor.name);

    // Leer primeros bytes del stream
    if (uiResponse.body) {
      const reader = uiResponse.body.getReader();
      const { value } = await reader.read();
      if (value) {
        const chunk = new TextDecoder().decode(value);
        console.log('[CHAT-DEBUG] Formato de primeros bytes del stream:');
        console.log('[CHAT-DEBUG] Raw:', JSON.stringify(chunk.slice(0, 200)));
        console.log('[CHAT-DEBUG] Starts with:', chunk.slice(0, 20));
        console.log('[CHAT-DEBUG] Full first chunk:', chunk);
      }
      reader.releaseLock();
    }

    // Retornar el stream real
    return result.toUIMessageStreamResponse();

  } catch (error: unknown) {
    console.error('[CHAT-DEBUG] Error:', error);
    const msg = error instanceof Error ? error.message : String(error);
    return new Response(JSON.stringify({ error: msg }), { status: 500 });
  }
}
