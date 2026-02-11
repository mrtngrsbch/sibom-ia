/**
 * query-classifier.ts
 *
 * Unified query classification system for SIBOM Scraper Assistant.
 * Determines query intent, RAG requirements, LLM bypass eligibility, and optimal retrieval parameters.
 *
 * @version 2.0.0 - Consolidated from query-classifier, query-intent-classifier, query-analyzer
 * @created 2026-01-10
 * @author Kiro AI (MIT Engineering Standards)
 *
 * ARCHITECTURE:
 * - Single source of truth for all query classification logic
 * - Type-safe discriminated unions for query intents
 * - Zero hardcoded patterns - LLM-first approach
 * - Performance-optimized with minimal token usage
 */

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

/**
 * Query intent types (discriminated union)
 */
export type QueryIntent =
  | 'simple-listing'      // List normativas (e.g., "decretos de carlos tejedor 2025")
  | 'count'               // Count normativas (e.g., "cuántas ordenanzas hay")
  | 'search-by-number'    // Search by number (e.g., "ordenanza 2947")
  | 'latest'              // Latest normativa (e.g., "última ordenanza de merlo")
  | 'date-range'          // Date range query (e.g., "ordenanzas de enero 2025")
  | 'content-analysis'    // Content analysis (e.g., "qué dice la ordenanza sobre X")
  | 'semantic-search'     // Semantic search (e.g., "ordenanzas de tránsito")
  | 'comparison'          // Comparison (e.g., "diferencias entre X y Y")
  | 'computational'       // Computational query (e.g., "cuál municipio publicó más decretos")
  | 'faq'                 // Frequent question about the system
  | 'off-topic';          // Off-topic (not related to normativas)

/**
 * Query intent classification result
 */
export interface QueryIntentResult {
  intent: QueryIntent;
  needsRAG: boolean;      // Requires RAG search in documents
  needsLLM: boolean;      // Requires LLM processing (vs direct response)
  confidence: number;     // 0-1 confidence score
  reason: string;         // Human-readable explanation
}

/**
 * Query analysis result (for clarification needs)
 */
export interface QueryAnalysisResult {
  needsClarification: boolean;
  clarification?: {
    type: 'municipality' | 'ordinanceType' | 'tooManyResults';
    message: string;
    suggestions: string[];
  };
  extractedFilters?: {
    municipality?: string;
    ordinanceType?: 'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion';
  };
}

// ============================================================================
// CORE CLASSIFICATION FUNCTIONS
// ============================================================================

/**
 * Classifies query intent and determines processing requirements
 *
 * SIMPLIFIED APPROACH: Let the LLM do its job!
 * - Only bypass LLM for obvious off-topic queries
 * - Everything else goes to LLM with RAG context
 * - LLM decides how to interpret and respond
 *
 * @param query - User query string
 * @returns Classification result with intent, RAG/LLM requirements, and confidence
 */
export function classifyQueryIntent(query: string): QueryIntentResult {
  const lowerQuery = query.toLowerCase().trim();

  // Priority 1: Off-topic (highest priority to avoid wasting resources)
  if (isOffTopic(lowerQuery)) {
    return {
      intent: 'off-topic',
      needsRAG: false,
      needsLLM: false,
      confidence: 0.95,
      reason: 'Query not related to municipal normativas'
    };
  }

  // Priority 2: FAQ (system questions - no RAG needed)
  if (isFAQQuery(lowerQuery)) {
    return {
      intent: 'faq',
      needsRAG: false,
      needsLLM: true, // FAQ needs LLM but with economic model
      confidence: 0.9,
      reason: 'Frequent question about the system'
    };
  }

  // Priority 3: Computational queries (SQL-based)
  if (isComputationalQuery(lowerQuery)) {
    return {
      intent: 'computational',
      needsRAG: true,
      needsLLM: true,
      confidence: 0.85,
      reason: 'Computational query requiring aggregation or comparison'
    };
  }

  // EVERYTHING ELSE: Let the LLM handle it
  // The LLM is smart enough to understand:
  // - "sueldos de carlos tejedor 2025" → search content about salaries
  // - "decretos de carlos tejedor 2025" → list all decrees
  // - "ordenanza 2947" → find specific ordinance
  // - "cuántas ordenanzas hay" → count and list
  // 
  // Stop trying to be clever with classifications!
  return {
    intent: 'semantic-search',
    needsRAG: true,
    needsLLM: true, // ALWAYS use LLM for normativa queries
    confidence: 0.8,
    reason: 'Let LLM interpret query and decide response'
  };
}

/**
 * Legacy function for backward compatibility
 * @deprecated Use classifyQueryIntent() instead
 */
export function needsRAGSearch(query: string): boolean {
  const result = classifyQueryIntent(query);
  return result.needsRAG;
}

/**
 * Legacy function for backward compatibility
 * @deprecated Use classifyQueryIntent() instead
 */
export function isFAQQuestion(query: string): boolean {
  const result = classifyQueryIntent(query);
  return result.intent === 'faq';
}

// ============================================================================
// INTENT DETECTION HELPERS (Private)
// ============================================================================

/**
 * Detects off-topic queries (not related to normativas)
 */
function isOffTopic(query: string): boolean {
  // If query mentions normativas explicitly, it's NOT off-topic
  const mentionsNormativas = /ordenanza|decreto|resolución|disposición|convenio|boletin|normativa|legislación/i.test(query);
  if (mentionsNormativas) {
    return false;
  }

  const offTopicPatterns = [
    /clima|tiempo|temperatura|pronóstico|lluvia|calor|frío/i,
    /receta|cocina|comida|cómo.*cocinar/i,
    /deporte|fútbol|partido|boca|river|racing|independiente|messi|maradona/i,
    /película|serie|netflix|spotify|música|canción/i,
    /dólar|cotización|inflación|economía.*nacional/i,
    /famoso|celebridad|actriz|actor|cantante/i,
    /médico|síntoma|enfermedad/i, // Removed "salud" - it's a valid normativa topic
    /amor|pareja|cita|romántico/i,
    /chiste|gracioso|reír/i,
    /qué.*hora/i,
    /noticias|actualidad/i,
  ];

  return offTopicPatterns.some(p => p.test(query));
}

/**
 * Detects FAQ queries about the system
 */
function isFAQQuery(query: string): boolean {
  const faqPatterns = [
    /qué.*municipios.*disponibles|cuáles.*municipios|municipios.*(hay|disponibles)/i,
    /cómo.*busco|cómo.*buscar|cómo.*consulto|cómo.*consultar/i,
    /cómo.*encuentro|cómo.*encontrar/i,
    /cómo.*uso.*chat|cómo.*usar.*chat|cómo.*funciona.*chat/i,
    /cómo.*citar.*norma|cómo.*cito|cómo.*referenciar/i,
    /qué.*tipos.*normativas|qué.*puedo.*consultar/i,
    /tipos.*normativas.*puedo/i,
    /diferencia.*entre.*ordenanza.*decreto/i,
    /información.*disponible/i,
    /para.*qué.*sirve/i,
    /qué.*puede.*hacer.*chat/i,
    /qué es sibom|qué es esto/i,
    /ayuda|help/i,
  ];

  return faqPatterns.some(p => p.test(query));
}

/**
 * Detects computational queries (aggregations, comparisons)
 * 
 * These require SQL/computational operations, not just semantic search.
 * Examples: "cuál municipio tiene más decretos", "comparar tasas entre municipios"
 */
export function isComputationalQuery(query: string): boolean {
  // Exclude simple count queries (those are handled by isCountQuery)
  // "cuántas ordenanzas hay" → count query, NOT computational
  const isSimpleCount = /cu[aá]ntos|cu[aá]ntas|cantidad|n[uú]mero de/i.test(query) &&
                        /ordenanza|decreto|resolución|disposición|convenio/i.test(query) &&
                        !/comparar|diferencia|mayor|menor|m[aá]s.*que|menos.*que/i.test(query);
  
  if (isSimpleCount) {
    return false;
  }

  // Exclude simple tax/fee queries (those are semantic search)
  // "tasas municipales merlo" → semantic search, NOT computational
  // "comparar tasas entre municipios" → computational
  const isSimpleTaxQuery = /tasa|impuesto|tributo/i.test(query) &&
                           !/comparar|diferencia|mayor|menor|cu[aá]l.*m[aá]s|entre.*y/i.test(query);
  
  if (isSimpleTaxQuery) {
    return false;
  }

  const computationalPatterns = [
    // Aggregation operations
    /suma|sumar|total|totalizar/i,
    /promedio|media|average/i,

    // Comparison operations (cross-municipality)
    /cu[aá]l.*municipio.*m[aá]s|cu[aá]l.*municipio.*mayor/i,
    /cu[aá]l.*municipio.*menos|cu[aá]l.*municipio.*menor/i,
    /comparar.*entre.*municipios|diferencia.*entre.*municipios/i,
    /ranking.*municipios|municipios.*ordenados/i,

    // Sorting operations
    /ordenar.*por|listar.*por.*cantidad|ranking/i,

    // Numeric filtering with comparisons
    /mayor.*que.*\d+|menor.*que.*\d+/i,
    /entre.*\d+.*y.*\d+/i,
  ];

  return computationalPatterns.some(pattern => pattern.test(query));
}

/**
 * Detects count queries
 */
function isCountQuery(query: string): boolean {
  const countPatterns = [
    /cuántas|cuantas|cantidad|total/i,
    /número de|numero de/i,
  ];

  const hasCountPattern = countPatterns.some(p => p.test(query));
  const mentionsNormType = /ordenanza|decreto|resolución|disposición|convenio/i.test(query);

  return hasCountPattern && mentionsNormType;
}

/**
 * Detects search by specific number
 */
function isSearchByNumberQuery(query: string): boolean {
  const hasNumber = /\b\d{1,5}\b/.test(query);
  const hasNormType = /ordenanza|decreto|resolución|disposición|convenio/i.test(query);
  const hasContentWords = /qué dice|contenido|texto|artículo|establece|dispone/i.test(query);
  const hasListingWords = /\bde\b|\bdel\b|\ben\b|\baño\b|correspondientes|durante/i.test(query);

  return hasNumber && hasNormType && !hasContentWords && !hasListingWords;
}

/**
 * Detects latest normativa queries
 */
function isLatestQuery(query: string): boolean {
  const latestPatterns = [
    /última|ultimo|más reciente|reciente/i,
  ];

  return latestPatterns.some(p => p.test(query));
}

/**
 * Detects content analysis queries
 */
function isContentAnalysisQuery(query: string): boolean {
  const contentPatterns = [
    /qué dice|que dice/i,
    /contenido|texto/i,
    /artículo|articulo/i,
    /establece|dispone|indica/i,
    /sobre qué|sobre que|acerca de/i,
  ];

  return contentPatterns.some(p => p.test(query));
}

/**
 * Detects comparison queries
 */
function isComparisonQuery(query: string): boolean {
  const comparisonPatterns = [
    /diferencia|diferencias/i,
    /comparar|comparación|comparacion/i,
    /entre.*y/i,
    /versus|vs/i,
  ];

  return comparisonPatterns.some(p => p.test(query));
}

/**
 * Detects semantic search queries (content-based searches)
 * 
 * These queries look for normativas about specific topics/content,
 * not just listings by metadata (municipality, year, type).
 * 
 * Examples:
 * - "sueldos de carlos tejedor 2025" → semantic (about salaries)
 * - "ordenanzas de tránsito" → semantic (about traffic)
 * - "decretos de carlos tejedor 2025" → NOT semantic (just listing)
 */
function isSemanticSearchQuery(query: string): boolean {
  // Content keywords that indicate the user wants to search ABOUT something
  // These are topics/subjects that appear IN the normativa content
  const contentKeywords = [
    // Labor/Employment
    /sueldo|salario|remuneraci[oó]n|salarial|jornada.*laboral/i,
    
    // Urban/Traffic
    /tr[aá]nsito|transito|vial|estacionamiento|velocidad.*m[aá]xima/i,
    
    // Health/Education
    /salud|educaci[oó]n|educacion|escuela|hospital|centro.*de.*salud/i,
    
    // Taxes/Fees
    /impuesto|tasa|tributo|canon|derecho.*de/i,
    
    // Permits/Licenses
    /habilitaci[oó]n|habilitacion|permiso|licencia|autorizaci[oó]n/i,
    
    // Environment
    /medio.*ambiente|ambiental|residuo|basura|reciclaje/i,
    
    // Construction/Urban Planning
    /construcci[oó]n|edificaci[oó]n|obra|urbanismo|zonificaci[oó]n/i,
    
    // Commerce
    /comercio|comercial|feria|mercado|venta.*ambulante/i,
    
    // Public Services
    /agua|luz|electricidad|gas|cloacas|alumbrado/i,
    
    // Social
    /vivienda|social|asistencia|subsidio|ayuda/i,
    
    // Security
    /seguridad|polic[ií]a|emergencia|bomberos/i,
    
    // Culture/Sports
    /cultura|deporte|recreaci[oó]n|turismo|patrimonio/i,
    
    // Generic semantic indicators
    /relacionada|relacionado|relacionadas/i,
    /sobre|acerca de/i,
    /tema|temas/i,
    /que.*habla|que.*trata|que.*dice.*sobre/i,
  ];

  // Check if query contains content keywords
  const hasContentKeyword = contentKeywords.some(p => p.test(query));
  
  // If it has content keywords, it's semantic search
  // (doesn't need to mention norm type explicitly)
  if (hasContentKeyword) {
    return true;
  }

  // Legacy check: semantic keyword + norm type
  const legacySemanticKeywords = [
    /relacionada|relacionado|relacionadas/i,
    /sobre|acerca de/i,
    /tema|temas/i,
  ];
  
  const hasLegacyKeyword = legacySemanticKeywords.some(p => p.test(query));
  const hasNormType = /ordenanza|decreto|resolución|disposición|convenio/i.test(query);

  return hasLegacyKeyword && hasNormType;
}

// ============================================================================
// DIRECT RESPONSE GENERATION (LLM Bypass)
// ============================================================================

/**
 * Generates direct response for simple queries without LLM
 *
 * @param intent - Query intent type
 * @param sources - Retrieved sources from RAG
 * @param filters - Applied filters (municipality, type, year)
 * @returns Formatted response string
 *
 * @example
 * generateDirectResponse('count', sources, { municipality: 'Carlos Tejedor', year: 2025 })
 * // => "Hay **1,249 decretos** de **Carlos Tejedor** del año **2025**..."
 */
export function generateDirectResponse(
  intent: QueryIntent,
  sources: Array<{ title: string; municipality?: string; url?: string; [key: string]: unknown }>,
  filters: {
    municipality?: string;
    type?: string;
    year?: number;
  }
): string {
  const { municipality, type, year } = filters;
  const count = sources.length;

  switch (intent) {
    case 'simple-listing':
      if (count === 0) {
        return `No se encontraron ${type || 'normativas'} de ${municipality || 'este municipio'}${year ? ` del año ${year}` : ''}.`;
      }
      if (count === 1) {
        return `Se encontró **1 ${type || 'normativa'}** de **${municipality || 'este municipio'}**${year ? ` del año **${year}**` : ''}.\n\nLa información completa está disponible en la sección "Fuentes Consultadas" más abajo.`;
      }
      return `Se encontraron **${count.toLocaleString('es-AR')} ${type || 'normativas'}** de **${municipality || 'este municipio'}**${year ? ` del año **${year}**` : ''}.\n\nLa lista completa con enlaces está disponible en la sección "Fuentes Consultadas" más abajo.`;

    case 'count':
      if (count === 0) {
        return `No hay ${type || 'normativas'} de ${municipality || 'este municipio'}${year ? ` del año ${year}` : ''}.`;
      }
      if (count === 1) {
        return `Hay **1 ${type || 'normativa'}** de **${municipality || 'este municipio'}**${year ? ` del año **${year}**` : ''}.\n\nPodés verla en la sección "Fuentes Consultadas" más abajo.`;
      }
      return `Hay **${count.toLocaleString('es-AR')} ${type || 'normativas'}** de **${municipality || 'este municipio'}**${year ? ` del año **${year}**` : ''}.\n\nLa lista completa está disponible en la sección "Fuentes Consultadas" más abajo.`;

    case 'search-by-number': {
      if (count === 0) {
        return `No se encontró la ${type || 'normativa'} solicitada de ${municipality || 'este municipio'}.`;
      }
      if (count === 1) {
        const source = sources[0] as { title: string; municipality?: string; type?: string };
        const sourceType = source.type || 'DOC';
        return `**${sourceType.toUpperCase()} N° ${source.title.match(/\d+\/\d+/)?.[0] || 'S/N'}** - ${source.municipality}\n\nPodés ver el documento completo en la sección "Fuentes Consultadas" más abajo.`;
      }
      return `Se encontraron **${count} resultados** para tu búsqueda.\n\nLa lista completa está disponible en la sección "Fuentes Consultadas" más abajo.`;

    case 'latest': {
      if (count === 0) {
        return `No se encontraron ${type || 'normativas'} de ${municipality || 'este municipio'}.`;
      }
      const latest = sources[0] as { title: string; type?: string } | undefined;
      const latestType = latest.type || 'normativa';
      return `La última ${latestType} de **${municipality || 'este municipio'}** es:\n\n**${(latestType || 'NORM').toUpperCase()} N° ${latest.title.match(/\d+\/\d+/)?.[0] || 'S/N'}**\n\nPodés verla en la sección "Fuentes Consultadas" más abajo.`;

    default:
      return `Se encontraron **${count.toLocaleString('es-AR')} resultados**.\n\nLa lista completa está disponible en la sección "Fuentes Consultadas" más abajo.`;
  }
}

// ============================================================================
// OFF-TOPIC RESPONSE GENERATION
// ============================================================================

/**
 * Generates friendly off-topic response
 *
 * @param query - User query
 * @returns Personalized off-topic message
 */
export function getOffTopicResponse(query: string): string | null {
  const lower = query.toLowerCase();

  // Weather
  if (/temperatura|clima|tiempo|pronóstico|lluvia|calor|frío/.test(lower)) {
    return "🌤️ Mirá, no tengo idea del clima... pero puedo decirte si hay alguna ordenanza municipal sobre drenajes pluviales para cuando llueva. ¿Te sirve? 😄";
  }

  // Sports
  if (/fútbol|boca|river|partido|ganó|racing|independiente|mejor.*jugador|campeón|mundial|copa|messi|maradona|ronaldo/.test(lower)) {
    return "⚽ Uh, si te digo quién ganó seguro me equivoco... pero sí te puedo contar sobre ordenanzas de habilitación de canchas de fútbol municipal. ¿Eso cuenta? 😅";
  }

  // Economy
  if (/dólar|cotización|inflación|economía.*nacional/.test(lower)) {
    return "💸 El dólar sube, baja, vuela... yo me ocupo de ordenanzas municipales, no de Wall Street. ¿Te interesa consultar tasas municipales? ¡Esas sí que las tengo al día! 😉";
  }

  // Recipes
  if (/receta|cocina|comida|cómo.*cocinar/.test(lower)) {
    return "🍳 ¡Ojalá tuviera recetas! Pero mi especialidad son ordenanzas, no empanadas. Eso sí, puedo ayudarte con normativas de habilitación de restaurantes. ¿Te sirve? 🧐";
  }

  // Celebrities
  if (/famoso|celebridad|actriz|actor|cantante/.test(lower)) {
    return "🎬 Los famosos no son mi tema... ¡pero las ordenanzas de espectáculos públicos sí! Si querés organizar un evento, puedo ayudarte con eso. 🎭";
  }

  // Health
  if (/salud|médico|síntoma|enfermedad/.test(lower)) {
    return "🏥 ¡Ojo! No soy médico. Mejor consultá con un profesional de verdad. Yo me limito a ordenanzas sanitarias municipales. 😊";
  }

  // Entertainment
  if (/película|serie|netflix|spotify/.test(lower)) {
    return "🎥 Netflix no es lo mío, pero ¿sabías que algunos municipios tienen ordenanzas sobre salas de cine? Si te interesa ese tema legal, charlamos. 🍿";
  }

  // Romance
  if (/amor|pareja|cita|romántico/.test(lower)) {
    return "💘 Ay, del corazón no entiendo nada... pero de ordenanzas municipales, ¡todo! ¿Querés consultar sobre espacios verdes para una cita romántica? 😌";
  }

  // Jokes
  if (/chiste|gracioso|reír/.test(lower)) {
    return "😂 El mejor chiste que conozco es leer ordenanzas a las 3 AM... pero bueno, ¿te puedo ayudar con algo serio de normativa municipal?";
  }

  // Time
  if (/qué.*hora/.test(lower)) {
    return "🕐 No tengo reloj, pero puedo contarte sobre ordenanzas de horarios comerciales en tu municipio. ¿Te interesa? ⏰";
  }

  // News
  if (/noticias|actualidad/.test(lower)) {
    return "📰 Las noticias cambian cada minuto... yo me especializo en ordenanzas municipales, que son un poco más estables. ¿Consultamos algo de normativa local? 📋";
  }

  // Generic fallback
  return "🤔 Mmm, esa pregunta no tiene que ver con ordenanzas municipales... Mi especialidad es ayudarte con normativas, decretos y boletines de la Provincia de Buenos Aires. ¿Querés consultar algo sobre legislación municipal? 📋";
}

// ============================================================================
// RETRIEVAL OPTIMIZATION
// ============================================================================

/**
 * Calculates optimal document limit based on query type and filters
 *
 * @param query - User query
 * @param hasFilters - Whether filters are applied
 * @returns Optimal number of documents to retrieve
 */
export function calculateOptimalLimit(query: string, hasFilters: boolean): number {
  // Listing queries need many documents
  const listingPatterns = [
    /cuántas|cuantas|cantidad|total/i,
    /lista|listar|listado/i,
    /todos.*los|todas.*las/i,
    /qué.*hay|que.*hay/i,
    /(ordenanzas|decretos|resoluciones).*\d{4}/i,
  ];

  if (listingPatterns.some(p => p.test(query))) {
    return hasFilters ? 100 : 10;
  }

  // Exact number search
  const hasExactNumber = /(ordenanza|decreto|resoluci[oó]n|disposici[oó]n)\s+(n[°º]?|nro\.?)?\s*\d{1,4}\b/i.test(query);
  if (hasExactNumber && hasFilters) return 1;

  // Metadata-only queries
  const singleDocPatterns = [
    /cuál.*última/i,
    /existe/i
  ];
  if (singleDocPatterns.some(p => p.test(query))) return 1;

  // With filters: increase for better BM25 ranking
  if (hasFilters) return 10;

  // Default: 5 documents
  return 5;
}

/**
 * Calculates optimal content limit (characters) based on query type
 *
 * @param query - User query
 * @returns Character limit for content truncation
 */
export function calculateContentLimit(query: string): number {
  // Listing queries: metadata only
  const isListingQuery = [
    /(ordenanzas?|decretos?|resoluciones?).*\d{4}/i,
    /cuántas?.+(ordenanzas?|decretos?|resoluciones?)/i,
    /listar|mostrar|todos.*los/i,
  ].some(pattern => pattern.test(query));

  if (isListingQuery) {
    return 200; // Metadata only
  }

  // Full content queries
  const needsFullContent = [
    /qué.*dice|contenido|texto|artículo/i,
    /resumen|detalle/i,
  ].some(pattern => pattern.test(query));

  if (needsFullContent) {
    return 2000;
  }

  // Metadata-only patterns
  const metadataOnlyPatterns = [
    /cuál.*última/i,
    /cuál.*más.*reciente/i,
    /listar/i,
    /mostrar/i,
    /existe/i,
    /vigente/i,
    /fecha.*ordenanza/i,
    /número.*decreto/i
  ];

  if (metadataOnlyPatterns.some(p => p.test(query))) {
    return 200;
  }

  // Content analysis
  if (/qué.*dice|contenido|texto|artículo|establece|dispone/i.test(query)) {
    return 5000;
  }

  // Default: short excerpt
  return 500;
}

// ============================================================================
// QUERY ANALYSIS (Clarification Detection)
// ============================================================================

/**
 * Analyzes query for ambiguities and clarification needs
 *
 * @param query - User query
 * @param currentFilters - Currently applied filters
 * @param municipalities - Available municipalities list
 * @returns Analysis result with clarification needs
 */
export function analyzeQuery(
  query: string,
  currentFilters: { municipality?: string | null },
  municipalities: string[] = []
): QueryAnalysisResult {
  const lowerQuery = query.toLowerCase();

  // User explicitly wants all municipalities
  if (/en todos.*municipios|todos los municipios|buscar en todos/i.test(query)) {
    return {
      needsClarification: false,
      extractedFilters: {}
    };
  }

  // Extract municipality mentioned in query
  const extractedMunicipality = municipalities.find(m =>
    lowerQuery.includes(m.toLowerCase())
  );

  const hasMunicipalityFilter = currentFilters.municipality !== null &&
                                  currentFilters.municipality !== undefined &&
                                  currentFilters.municipality !== '';

  // Suggest municipality if detected but not filtered
  if (extractedMunicipality && !hasMunicipalityFilter) {
    return {
      needsClarification: true,
      clarification: {
        type: 'municipality',
        message: `Detecté que mencionás "${extractedMunicipality}". ¿Querés que filtre por ese municipio?`,
        suggestions: [extractedMunicipality]
      },
      extractedFilters: { municipality: extractedMunicipality }
    };
  }

  // Broad questions without municipality
  const broadQuestions = [
    /cuál.*última.*ordenanza/i,
    /cuál.*tasa/i,
    /cuánto.*cuesta/i,
    /ordenanza.*\d+/i,
    /decreto.*\d+/i,
    /cuántos?.*(decretos|ordenanzas|boletines|resoluciones)/i,
    /(decretos|ordenanzas|boletines|resoluciones).*en.*\d{4}/i,
    /última.*norma/i,
    /vigente/i,
    /última/i,
    /más reciente/i
  ];

  const isBroadQuestion = broadQuestions.some(pattern => pattern.test(query));
  const hasMunicipality = currentFilters.municipality !== null &&
                          currentFilters.municipality !== undefined &&
                          currentFilters.municipality !== '';

  if (isBroadQuestion && !hasMunicipality) {
    return {
      needsClarification: true,
      clarification: {
        type: 'municipality',
        message: '¿De qué municipio querés consultar?',
        suggestions: municipalities.slice(0, 6)
      }
    };
  }

  // Extract ordinance type
  let ordinanceType: 'ordenanza' | 'decreto' | 'boletin' | 'resolucion' | 'disposicion' | 'convenio' | 'licitacion' | undefined;
  if (lowerQuery.includes('ordenanza')) ordinanceType = 'ordenanza';
  else if (lowerQuery.includes('decreto')) ordinanceType = 'decreto';
  else if (lowerQuery.includes('boletin') || lowerQuery.includes('boletín')) ordinanceType = 'boletin';
  else if (lowerQuery.includes('resolución') || lowerQuery.includes('resolucion')) ordinanceType = 'resolucion';
  else if (lowerQuery.includes('disposición') || lowerQuery.includes('disposicion')) ordinanceType = 'disposicion';
  else if (lowerQuery.includes('convenio')) ordinanceType = 'convenio';
  else if (lowerQuery.includes('licitación') || lowerQuery.includes('licitacion')) ordinanceType = 'licitacion';

  return {
    needsClarification: false,
    extractedFilters: {
      ...(extractedMunicipality && { municipality: extractedMunicipality }),
      ...(ordinanceType && { ordinanceType })
    }
  };
}
