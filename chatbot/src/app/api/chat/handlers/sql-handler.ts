/**
 * sql-handler.ts — SQL Comparison bypass
 *
 * Responsabilidad única: detectar y ejecutar queries comparativas entre municipios.
 * Cuando la query es una comparación ("cuál municipio tiene más decretos"),
 * se resuelve directamente con SQL sin pasar por el LLM → ahorro de tokens.
 */

import {
  isComparisonQuery,
  handleComparisonQuery,
  type ComparisonResult,
} from '@/lib/rag/sql-retriever';

/**
 * Intenta resolver la query como comparación SQL.
 * @returns ComparisonResult si es comparación exitosa, null en caso contrario.
 */
export async function tryHandleSQLComparison(query: string): Promise<ComparisonResult | null> {
  if (!isComparisonQuery(query)) {
    return null;
  }

  console.log('[SQLHandler] 🗄️ Detectada query de comparación SQL');
  const result = await handleComparisonQuery(query);

  if (result.success) {
    console.log(`[SQLHandler] ✅ Comparación exitosa: ${result.answer}`);
    console.log(`[SQLHandler] 📊 ${result.data.length} municipios`);
    return result;
  }

  console.log('[SQLHandler] ❌ Comparación falló, se usará RAG');
  return null;
}

/**
 * Construye un Response de stream directo para comparaciones SQL (sin LLM)
 */
export function buildSQLDirectResponse(result: ComparisonResult): Response {
  const directResponse = result.answer + (result.markdown || '');
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const escaped = directResponse.replace(/"/g, '\\"').replace(/\n/g, '\\n');
      controller.enqueue(encoder.encode(`0:"${escaped}"\n`));
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'X-Vercel-AI-Data-Stream': 'v1',
    },
  });
}
