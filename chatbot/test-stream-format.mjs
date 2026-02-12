import { streamText } from 'ai';
import { createOpenRouter } from '@openrouter/ai-sdk-provider';

const openrouter = createOpenRouter({
  apiKey: 'test-key'
});

// Crear un stream de prueba
const result = streamText({
  model: openrouter('google/gemini-flash-1.5'),
  prompt: 'Hello',
});

// Verificar qué métodos existen en el resultado
console.log('Métodos disponibles en streamText result:');
console.log(Object.getOwnPropertyNames(Object.getPrototypeOf(result)).filter(m => m.includes('Stream') || m.includes('Response')));

// Verificar qué retorna toUIMessageStreamResponse
const response = result.toUIMessageStreamResponse();
console.log('\n📤 Tipo de respuesta:', response.constructor.name);
console.log('📤 Headers:', response.headers);
console.log('📤 Body type:', response.body?.constructor.name);
