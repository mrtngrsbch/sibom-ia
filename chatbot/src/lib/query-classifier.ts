/**
 * query-classifier.ts
 *
 * Clasifica queries para determinar si necesitan búsqueda RAG o pueden responderse directamente.
 * Optimiza tokens al evitar búsquedas innecesarias en documentos.
 * Incluye detección de queries computacionales que requieren datos tabulares estructurados.
 */

/**
 * Detecta si la query requiere operaciones computacionales sobre datos tabulares
 * @param query - Consulta del usuario
 * @returns true si necesita acceso a datos estructurados de tablas
 *
 * @example
 * isComputationalQuery("cuál es el monto máximo de tasas") // true
 * isComputationalQuery("suma de todas las tasas") // true
 * isComputationalQuery("qué dice la ordenanza de tránsito") // false
 *
 * NOTA: Esta función es un wrapper simple. Para análisis completo de queries
 * computacionales, usar el módulo @/lib/computation que incluye parsing
 * y ejecución de operaciones.
 */
export function isComputationalQuery(query: string): boolean {
  const computationalPatterns = [
    // Operaciones de agregación
    /suma|sumar|total|totalizar/i,
    /promedio|media|average/i,

    // Operaciones de comparación
    /cu[aá]l.*m[aá]s.*alto|mayor|m[aá]ximo/i,
    /cu[aá]l.*m[aá]s.*bajo|menor|m[ií]nimo/i,
    /comparar|diferencia|vs|versus/i,
    /entre.*y/i, // "diferencia entre X y Y"

    // Operaciones de conteo
    /cu[aá]ntos|cu[aá]ntas|cantidad|n[uú]mero de/i,

    // Búsqueda de valores específicos en tablas
    /monto|valor|precio|tasa|tarifa/i,
    /categor[ií]a|tipo.*de/i,

    // Operaciones de ordenamiento
    /ordenar|listar.*por|ranking/i,

    // Operaciones de filtrado sobre datos numéricos
    /mayor.*que|menor.*que|igual.*a/i,
    /entre.*\d+.*y.*\d+/i, // "entre 1000 y 5000"
  ];

  return computationalPatterns.some(pattern => pattern.test(query));
}

/**
 * Detecta si es una pregunta FAQ válida del sistema
 * @param query - Consulta del usuario
 * @returns true si es una FAQ sobre el sistema (no off-topic)
 */
export function isFAQQuestion(query: string): boolean {
  const faqPatterns = [
    // Municipios disponibles
    /qué.*municipios.*disponibles|cuáles.*municipios|municipios.*(hay|disponibles)/i,

    // Cómo buscar/consultar (FAQ clave que estaba fallando)
    /cómo.*busco|cómo.*buscar|cómo.*consulto|cómo.*consultar/i,
    /cómo.*encuentro|cómo.*encontrar/i,
    /cómo.*uso.*chat|cómo.*usar.*chat/i,

    // Cómo citar
    /cómo.*citar.*norma|cómo.*cito|cómo.*referenciar/i,

    // Tipos de normativas
    /qué.*tipos.*normativas|qué.*puedo.*consultar/i,
    /tipos.*normativas.*puedo/i,
    /diferencia.*entre.*ordenanza.*decreto/i,

    // Funcionamiento del sistema
    /cómo.*funciona.*búsqueda|cómo.*funciona.*chat/i,
    /información.*disponible/i,

    // Uso del chatbot
    /para.*qué.*sirve/i,
    /qué.*puede.*hacer.*chat/i
  ];

  return faqPatterns.some(p => p.test(query));
}

/**
 * Detecta si la query ES SOBRE ordenanzas/normativas municipales
 * @param query - Consulta del usuario
 * @returns true si necesita RAG (es sobre ordenanzas), false si es off-topic
 *
 * ESTRATEGIA: En vez de listar TODO lo que NO es ordenanza (imposible),
 * detectamos solo lo que SÍ ES sobre ordenanzas municipales.
 */
export function needsRAGSearch(query: string): boolean {
  const lowerQuery = query.toLowerCase();

  // 1. Saludos y conversación básica (NO necesita RAG)
  const greetingPatterns = [
    /^hola/i,
    /^buenos días/i,
    /^buenas tardes/i,
    /^buenas noches/i,
    /cómo estás|qué tal/i,
    /quién sos|qué sos|quién eres/i,
    /ayuda|help/i,
    /cómo.*funciona.*chat/i,
    /qué.*puede.*hacer/i,
    /para.*sirve/i,
  ];

  if (greetingPatterns.some(p => p.test(query))) {
    return false;
  }

  // 2. Queries FAQ sobre el sistema (NO necesitan RAG pero NO son off-topic)
  // Usar la misma función isFAQQuestion() para consistencia
  if (isFAQQuestion(query)) {
    return false; // NO buscar en RAG pero responder desde knowledge base
  }

  // 3. ✅ CAMBIO CLAVE: Detectar si menciona términos de ordenanzas/normativas
  const ordinanceKeywords = [
    /ordenanza/i,
    /decreto/i,
    // Patrones flexibles para "boletín" (incluyendo errores comunes de tipeo)
    /bolet[ií]n|botet[ií]n|boletin|botetin/i,
    /resolución/i,
    /normativa/i,
    /ley.*municipal/i,
    /reglamento/i,
    /disposición.*municipal/i,
    /tasa/i,
    /tributo/i,
    /impuesto.*municipal/i,
    /habilitación/i,
    /permiso.*municipal/i,
    /vigente/i,
    /derogad/i,
    /modificad/i,
    /código.*municipal/i,
    /sesión.*concejo/i,
    /concejal/i,
    /intendente/i,
    /municipal/i,
    // Términos relacionados con pagos y finanzas municipales
    /pago/i,
    /pagos/i,
    /finanzas/i,
    /presupuesto/i,
  ];

  // Si menciona términos de ordenanzas → SÍ necesita RAG
  if (ordinanceKeywords.some(p => p.test(query))) {
    return true;
  }

  // 4. Si NO menciona términos de ordenanzas → probablemente off-topic
  // (asumimos que es pregunta fuera de tema)
  return false;
}

/**
 * Genera una respuesta graciosa/educativa para preguntas fuera de tema
 * @param query - Consulta del usuario
 * @returns Mensaje personalizado o null si no aplica
 */
export function getOffTopicResponse(query: string): string | null {
  const lower = query.toLowerCase();

  // Clima/Temperatura
  if (/temperatura|clima|tiempo|pronóstico|lluvia|calor|frío/.test(lower)) {
    return "🌤️ Mirá, no tengo idea del clima... pero puedo decirte si hay alguna ordenanza municipal sobre drenajes pluviales para cuando llueva. ¿Te sirve? 😄";
  }

  // Fútbol/Deportes
  if (/fútbol|boca|river|partido|ganó|racing|independiente|mejor.*jugador|campeón|mundial|copa|messi|maradona|ronaldo/.test(lower)) {
    return "⚽ Uh, si te digo quién ganó seguro me equivoco... pero sí te puedo contar sobre ordenanzas de habilitación de canchas de fútbol municipal. ¿Eso cuenta? 😅";
  }

  // Economía/Dólar
  if (/dólar|cotización|inflación|economía.*nacional/.test(lower)) {
    return "💸 El dólar sube, baja, vuela... yo me ocupo de ordenanzas municipales, no de Wall Street. ¿Te interesa consultar tasas municipales? ¡Esas sí que las tengo al día! 😉";
  }

  // Recetas/Comida
  if (/receta|cocina|comida|cómo.*cocinar/.test(lower)) {
    return "🍳 ¡Ojalá tuviera recetas! Pero mi especialidad son ordenanzas, no empanadas. Eso sí, puedo ayudarte con normativas de habilitación de restaurantes. ¿Te sirve? 🧐";
  }

  // Famosos/Celebridades
  if (/famoso|celebridad|actriz|actor|cantante/.test(lower)) {
    return "🎬 Los famosos no son mi tema... ¡pero las ordenanzas de espectáculos públicos sí! Si querés organizar un evento, puedo ayudarte con eso. 🎭";
  }

  // Salud/Medicina
  if (/salud|médico|síntoma|enfermedad/.test(lower)) {
    return "🏥 ¡Ojo! No soy médico. Mejor consultá con un profesional de verdad. Yo me limito a ordenanzas sanitarias municipales. 😊";
  }

  // Películas/Series/Entretenimiento
  if (/película|serie|netflix|spotify/.test(lower)) {
    return "🎥 Netflix no es lo mío, pero ¿sabías que algunos municipios tienen ordenanzas sobre salas de cine? Si te interesa ese tema legal, charlamos. 🍿";
  }

  // Amor/Romántico
  if (/amor|pareja|cita|romántico/.test(lower)) {
    return "💘 Ay, del corazón no entiendo nada... pero de ordenanzas municipales, ¡todo! ¿Querés consultar sobre espacios verdes para una cita romántica? 😌";
  }

  // Chistes
  if (/chiste|gracioso|reír/.test(lower)) {
    return "😂 El mejor chiste que conozco es leer ordenanzas a las 3 AM... pero bueno, ¿te puedo ayudar con algo serio de normativa municipal?";
  }

  // Hora
  if (/qué.*hora/.test(lower)) {
    return "🕐 No tengo reloj, pero puedo contarte sobre ordenanzas de horarios comerciales en tu municipio. ¿Te interesa? ⏰";
  }

  // Noticias
  if (/noticias|actualidad/.test(lower)) {
    return "📰 Las noticias cambian cada minuto... yo me especializo en ordenanzas municipales, que son un poco más estables. ¿Consultamos algo de normativa local? 📋";
  }

  // 🎯 FALLBACK GENÉRICO para TODO lo demás (cualquier pregunta off-topic)
  return "🤔 Mmm, esa pregunta no tiene que ver con ordenanzas municipales... Mi especialidad es ayudarte con normativas, decretos y boletines de la Provincia de Buenos Aires. ¿Querés consultar algo sobre legislación municipal? 📋";
}

/**
 * Determina cuánto contenido incluir según el tipo de pregunta
 * @param query - Consulta del usuario
 * @returns Límite de caracteres para truncar contenido
 */
export function calculateContentLimit(query: string): number {
  // Preguntas de LISTADO/CONTEO → usar metadata-only (200 chars)
  // Estas queries necesitan CANTIDAD, no contenido completo
  const isListingQuery = [
    /(ordenanzas?|decretos?|resoluciones?).*\d{4}/i,  // "decretos 2025", "ordenanzas de 2024"
    /cuántas?.+(ordenanzas?|decretos?|resoluciones?)/i,  // "cuántos decretos"
    /listar|mostrar|todos.*los/i,  // "listar decretos", "todos los decretos"
  ].some(pattern => pattern.test(query));

  if (isListingQuery) {
    return 200;  // ✅ Metadata-only: permite devolver 100+ normativas sin explotar tokens
  }

  // Preguntas que piden CONTENIDO específico → aumentar límite
  const needsFullContent = [
    /qué.*dice|contenido|texto|artículo/i,  // "qué dice la ordenanza"
    /resumen|detalle/i,  // "detalle del decreto"
  ].some(pattern => pattern.test(query));

  if (needsFullContent) {
    return 2000;  // Contenido moderado para lectura específica
  }

  // Preguntas metadata-only (NO necesitan contenido completo)
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
    return 200;  // Solo título + fecha + número (90% ahorro)
  }

  // Preguntas específicas sobre contenido
  if (/qué.*dice|contenido|texto|artículo|establece|dispone/i.test(query)) {
    return 5000;  // Extracto mediano
  }

  // Default: extracto corto
  return 500;  // 75% ahorro vs 2000
}

/**
 * Calcula el límite óptimo de documentos a recuperar
 * @param query - Consulta del usuario
 * @param hasFilters - Si hay filtros aplicados (municipio, tipo, fecha)
 * @returns Número de documentos a recuperar
 */
export function calculateOptimalLimit(query: string, hasFilters: boolean): number {
  // 1. Queries de listado/conteo → necesitan recuperar MUCHOS documentos
  const listingPatterns = [
    /cuántas|cuantas|cantidad|total/i,  // Conteo
    /lista|listar|listado/i,             // Listado explícito
    /todos.*los|todas.*las/i,            // "todos los decretos"
    /qué.*hay|que.*hay/i,                 // "qué ordenanzas hay"
    // ✅ PATRÓN CRÍTICO: "ordenanzas [municipio] [año]" o "ordenanzas de [municipio] [año]"
    /(ordenanzas|decretos|resoluciones).*\d{4}/i  // "ordenanzas carlos tejedor 2025" o "decretos de X 2025"
  ];

  if (listingPatterns.some(p => p.test(query))) {
    // Si hay filtros específicos (municipio + año + tipo), recuperar hasta 100 docs
    return hasFilters ? 100 : 10;
  }

  // 2. Búsqueda exacta por número de normativa (NO años) → 1 doc
  // Detecta números de 1-4 dígitos precedidos por contexto de normativa
  // Ejemplos que SÍ detecta: "ordenanza 2833", "decreto N° 123", "resolución nro 45"
  // Ejemplos que NO detecta: "decretos 2025" (año en plural), "carlos tejedor 2025" (año solo)
  const hasExactNumber = /(ordenanza|decreto|resoluci[oó]n|disposici[oó]n)\s+(n[°º]?|nro\.?)?\s*\d{1,4}\b/i.test(query);
  if (hasExactNumber && hasFilters) return 1;

  // 3. Query metadata-only simple (última, existe) → 1 doc suficiente
  const singleDocPatterns = [
    /cuál.*última/i,
    /existe/i
  ];
  if (singleDocPatterns.some(p => p.test(query))) return 1;

  // 4. Con filtros aplicados → aumentar a 10 docs para mejor ranking BM25
  if (hasFilters) return 10;

  // 5. Sin filtros → 5 docs
  return 5;
}
