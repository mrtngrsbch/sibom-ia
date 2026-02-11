/**
 * prompt-builder.ts — Construcción del system prompt
 *
 * Responsabilidad única: construir el system prompt según el tipo de query.
 * NO decide qué tipo de query es — eso lo hace el classifier.
 */

import fs from 'fs/promises';
import path from 'path';
import { generateDataCatalog, generateConciseCatalog } from '@/lib/data-catalog';
import { getOffTopicResponse } from '@/lib/query-classifier';
import type { Source } from '@/lib/rag/retriever';
import type {
  StatsResult,
  EnhancedFilters,
  ConversationContext,
  RetrievedContext,
} from '../types';

// ============================================================================
// Builders por tipo de query
// ============================================================================

/**
 * Prompt para preguntas FAQ (sobre el sistema)
 */
export function buildFAQPrompt(stats: StatsResult): string {
  const dataCatalog = generateConciseCatalog();

  return `Eres un asistente para nuestro chatbot de legislación municipal.

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
}

/**
 * Prompt para preguntas fuera de tema
 */
export function buildOffTopicPrompt(query: string): string {
  const offTopicResponse = getOffTopicResponse(query);
  return `Responde EXACTAMENTE este mensaje al usuario (no agregues nada más):

${offTopicResponse || 'Disculpá, pero mi especialidad son las ordenanzas y normativas municipales. ¿Tenés alguna consulta sobre ese tema? 📋'}`;
}

/**
 * Prompt principal para búsquedas RAG
 */
export async function buildRAGPrompt(params: {
  query: string;
  stats: StatsResult;
  retrievedContext: RetrievedContext;
  enhancedFilters: EnhancedFilters;
  conversationContext: ConversationContext;
  isMassiveListing: boolean;
}): Promise<string> {
  const {
    query,
    stats,
    retrievedContext,
    enhancedFilters,
    conversationContext,
    isMassiveListing,
  } = params;

  // Cargar template desde archivo
  let template = await loadSystemPromptTemplate();

  // Inyectar catálogo de datos
  const dataCatalog = generateDataCatalog();
  template = template.replace('{{data_catalog}}', dataCatalog);

  // Stats block (solo si pregunta sobre municipios disponibles)
  const statsText = buildStatsBlock(query, stats);

  // Context y sources
  const totalResultsCount = retrievedContext.totalCount ?? retrievedContext.sources.length;
  const contextToUse = buildContextText(retrievedContext);
  const sourcesText = buildSourcesText(retrievedContext.sources, totalResultsCount);

  // Warning anti-alucinación si no hay fuentes
  const noSourcesWarning = buildNoSourcesWarning(
    query,
    retrievedContext.sources,
    enhancedFilters
  );

  // Filtros aplicados
  const filtersApplied = buildFiltersText(enhancedFilters);

  // Instrucción para listados masivos
  const massiveListingInstruction = isMassiveListing && totalResultsCount > 50
    ? buildMassiveListingInstruction(totalResultsCount, enhancedFilters)
    : '';

  // Contexto conversacional
  const conversationContextText = buildConversationContextText(conversationContext);

  // Ensamblar prompt final
  return template
    .replace('{{stats}}', statsText)
    .replace('{{context}}', contextToUse)
    .replace('{{sources}}', sourcesText)
    .replace('{{conversation_context}}', conversationContextText)
    + noSourcesWarning
    + filtersApplied
    + massiveListingInstruction;
}

// ============================================================================
// Helpers internos
// ============================================================================

async function loadSystemPromptTemplate(): Promise<string> {
  const promptPath = path.join(process.cwd(), 'src', 'prompts', 'system.md');
  try {
    const stat = await fs.stat(promptPath);
    if (!stat.isFile()) throw new Error(`${promptPath} no es un archivo regular`);
    return await fs.readFile(promptPath, 'utf-8');
  } catch (err) {
    console.error('[PromptBuilder] Error leyendo system prompt:', err instanceof Error ? err.message : err);
    return 'Sos Mangrullo, observatorio independiente de legislación municipal bonaerense. Contexto: {{context}}';
  }
}

function buildStatsBlock(query: string, stats: StatsResult): string {
  const needsStats = /municipios.*disponibles|cuántos municipios|qué municipios/i.test(query);
  if (!needsStats) return '';

  return `IMPORTANTE: La Provincia de Buenos Aires tiene 135 municipios en total.

MUNICIPIOS CON DATOS SCRAPEADOS (${stats.municipalities} de 135):
${stats.municipalityList.join(', ')}

TOTAL DE DOCUMENTOS DISPONIBLES: ${stats.totalDocuments}

NOTA CRÍTICA: Los municipios listados arriba son los ÚNICOS que tienen información disponible en la base de datos. El resto de los municipios (${135 - stats.municipalities}) NO tienen datos scrapeados aún.`;
}

function buildContextText(retrievedContext: RetrievedContext): string {
  let context = retrievedContext.context || 'No se encontró información específica.';

  // Agregar resultado computacional si existe
  if (retrievedContext.computationResult?.success) {
    const comp = retrievedContext.computationResult;
    context += `\n\n## 🔢 RESULTADO COMPUTACIONAL\n\n${comp.answer}\n`;
    if (comp.markdown) context += `\n${comp.markdown}\n`;
  }

  return context;
}

function buildSourcesText(sources: Source[], totalCount: number): string {
  if (sources.length === 0) return '';

  if (totalCount > 50) {
    return `RESUMEN: ${totalCount.toLocaleString()} normativas encontradas en total (listado completo disponible en UI)`;
  }

  return sources.map((s) => {
    const typeLabel = (s as { documentTypes?: string[] }).documentTypes?.length
      ? (s as { documentTypes: string[] }).documentTypes.map((t: string) => t.toUpperCase()).join(', ')
      : s.type.toUpperCase();
    return `- ${typeLabel} ${s.title} - ${s.municipality} [Estado: ${s.status || 'vigente'}] (${s.url})`;
  }).join('\n');
}

function buildNoSourcesWarning(
  query: string,
  sources: Source[],
  filters: EnhancedFilters
): string {
  if (sources.length > 0) return '';

  const isSpecific = /\d{2,5}\/\d{2,4}/.test(query) ||
    /ordenanza \d+|decreto \d+/i.test(query) ||
    /impositiva|tasa vial|sueldos|habilitación/i.test(query);

  if (!isSpecific) return '';

  console.log('[PromptBuilder] ⚠️ No hay fuentes para búsqueda específica — agregando warning anti-alucinación');

  let warning = `\n\n🚨🚨🚨 ADVERTENCIA CRÍTICA - NO SE ENCONTRARON FUENTES 🚨🚨🚨\n\n` +
    `La búsqueda "${query.slice(0, 50)}..." NO arrojó resultados en la base de datos.\n\n` +
    `REGLAS ABSOLUTAS:\n` +
    `1. ❌ NO INVENTAR normativas, números o fechas\n` +
    `2. ❌ NO MENCIONAR ordenanzas o decretos que no estén en {{sources}}\n` +
    `3. ✅ DECIR CLARAMENTE: "No encontré información específica sobre..."\n` +
    `4. ✅ OFRECER alternativas: buscarse por otros criterios\n\n`;

  if (filters.municipality) {
    warning += `Podés intentar:\n- Buscar sin filtrar por municipio\n- Usar otros términos de búsqueda\n- Verificar el número o año\n`;
  }

  return warning;
}

function buildFiltersText(filters: EnhancedFilters): string {
  const hasFilters = !!(filters.municipality || filters.type || filters.dateFrom || filters.dateTo);
  if (!hasFilters) return '';

  let text = '\n\nFILTROS APLICADOS EN ESTA BÚSQUEDA:\n';
  if (filters.municipality) text += `- Municipio: ${filters.municipality}\n`;
  if (filters.type) text += `- Tipo: ${filters.type}\n`;
  if (filters.dateFrom) text += `- Desde: ${filters.dateFrom}\n`;
  if (filters.dateTo) text += `- Hasta: ${filters.dateTo}\n`;
  return text;
}

function buildConversationContextText(ctx: ConversationContext): string {
  const parts: string[] = [];
  if (ctx.municipality) parts.push(`- **Municipio activo**: ${ctx.municipality}`);
  if (ctx.year) parts.push(`- **Año activo**: ${ctx.year}`);
  if (ctx.type) parts.push(`- **Tipo de normativa activo**: ${ctx.type}`);

  return parts.length > 0
    ? parts.join('\n')
    : 'No hay contexto previo (primera consulta de la conversación).';
}

function buildMassiveListingInstruction(totalCount: number, filters: EnhancedFilters): string {
  const typeLabel = filters.type || 'normativas';
  const munLabel = filters.municipality || 'este municipio';
  const yearLabel = filters.dateFrom ? ` del año ${new Date(filters.dateFrom).getFullYear()}` : '';

  return `\n\n## ⚠️ INSTRUCCIÓN CRÍTICA - LISTADO MASIVO (${totalCount.toLocaleString()} RESULTADOS)

**🚨 REGLAS ABSOLUTAS:**
1. ❌ **PROHIBIDO GENERAR LISTA** — NO escribas lista numerada ni con viñetas
2. ❌ **PROHIBIDO DUPLICAR** — La lista se muestra en "Fuentes Consultadas"
3. ✅ **SOLO PERMITIDO:** Resumen de 2-3 líneas máximo:
   - "Se encontraron ${totalCount.toLocaleString()} ${typeLabel} de ${munLabel}${yearLabel}."
   - "La lista completa con enlaces está disponible en 'Fuentes Consultadas' más abajo."

💡 **Tip:** Sugerí al usuario refinar la búsqueda con palabras clave como "sueldos", "licitaciones", etc.`;
}
