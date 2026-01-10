/**
 * Simulación de la petición API real del frontend
 * Para entender por qué no funciona en producción
 */

import { extractFiltersFromQuery } from './src/lib/query-filter-extractor';
import { retrieveContext, getDatabaseStats, type SearchOptions } from './src/lib/rag/retriever';
import { needsRAGSearch, calculateOptimalLimit } from './src/lib/query-classifier';

async function simulateAPIRequest() {
  console.log('=== SIMULACIÓN DE PETICIÓN API ===\n');

  // Simular la consulta del usuario (sin filtro de municipio en UI)
  const query = "cuantas ordenanzas tuvo carlos tejedor en el 2025?";
  const filters = {
    municipality: null,  // Usuario NO seleccionó municipio
    ordinanceType: 'all',
    dateFrom: null,
    dateTo: null
  };

  console.log(`Query: "${query}"`);
  console.log(`Filtros UI: ${JSON.stringify(filters)}\n`);

  // 1. Verificar si necesita RAG
  const shouldSearch = needsRAGSearch(query);
  console.log(`[1] ¿Necesita búsqueda RAG? ${shouldSearch ? '✅ SÍ' : '❌ NO'}`);

  if (!shouldSearch) {
    console.log('❌ ERROR: La query NO fue clasificada como búsqueda RAG');
    return;
  }

  // 2. Obtener estadísticas (necesario para extractFiltersFromQuery)
  const stats = await getDatabaseStats();
  console.log(`\n[2] Estadísticas cargadas: ${stats.municipalities} municipios, ${stats.totalDocuments} docs`);

  // 3. Construir filtros UI
  const uiFilters: Partial<SearchOptions> = {
    municipality: filters.municipality || undefined,
    type: filters.ordinanceType !== 'all' ? filters.ordinanceType : undefined,
    dateFrom: filters.dateFrom || undefined,
    dateTo: filters.dateTo || undefined
  };

  console.log(`\n[3] Filtros UI preparados: ${JSON.stringify(uiFilters)}`);

  // 4. Extraer filtros de la query (LO QUE DEBERÍA PASAR)
  const enhancedFilters = extractFiltersFromQuery(
    query,
    stats.municipalityList,
    uiFilters
  );

  console.log(`\n[4] Filtros extraídos automáticamente:`);
  console.log(`   ${JSON.stringify(enhancedFilters, null, 2)}`);

  // 5. Calcular límite óptimo
  const hasFilters = !!(enhancedFilters.municipality || enhancedFilters.type || enhancedFilters.dateFrom || enhancedFilters.dateTo);
  const optimalLimit = calculateOptimalLimit(query, hasFilters);

  console.log(`\n[5] ¿Tiene filtros? ${hasFilters ? '✅ SÍ' : '❌ NO'}`);
  console.log(`   Límite óptimo: ${optimalLimit} documentos`);

  // 6. Construir searchOptions
  const searchOptions = {
    ...enhancedFilters,
    limit: optimalLimit
  };

  console.log(`\n[6] SearchOptions finales: ${JSON.stringify(searchOptions, null, 2)}`);

  // 7. Recuperar contexto
  console.log(`\n[7] Ejecutando búsqueda RAG...`);
  const result = await retrieveContext(query, searchOptions);

  console.log(`   Documentos recuperados: ${result.sources.length}`);

  // Analizar los documentos recuperados
  const ordenanzas2025 = result.sources.filter(s => {
    // Verificar si es de 2025
    const date = s.title.match(/(\d{2})\/(\d{2})\/(\d{4})/);
    if (date) {
      const year = date[3];
      return year === '2025' && s.type === 'ordenanza';
    }
    return false;
  });

  console.log(`   - Ordenanzas de 2025: ${ordenanzas2025.length}`);
  console.log(`   - Total fuentes: ${result.sources.length}`);

  if (result.sources.length > 0) {
    console.log(`\n   Primeras 5 fuentes:`);
    result.sources.slice(0, 5).forEach((s, i) => {
      console.log(`   ${i + 1}. ${s.title} (${s.type})`);
    });
  }

  // 8. Validación final
  console.log(`\n=== RESULTADO FINAL ===`);

  if (ordenanzas2025.length === 24) {
    console.log(`✅ ÉXITO: Se recuperaron las 24 ordenanzas de 2025`);
  } else if (ordenanzas2025.length > 0) {
    console.log(`⚠️  PARCIAL: Se recuperaron ${ordenanzas2025.length}/24 ordenanzas de 2025`);
    console.log(`   Posible causa: límite de documentos (${optimalLimit})`);
  } else {
    console.log(`❌ ERROR: No se recuperaron ordenanzas de 2025`);
    console.log(`   Posibles causas:`);
    console.log(`   1. Los filtros no se aplicaron correctamente`);
    console.log(`   2. El año no se extrajo de la query`);
    console.log(`   3. El scoring priorizó documentos de otros años`);
  }

  // Analizar el contexto que recibiría el LLM
  console.log(`\n=== CONTEXTO ENVIADO AL LLM ===`);
  console.log(`Longitud: ${result.context.length} caracteres`);
  console.log(`Primeros 500 caracteres:\n${result.context.slice(0, 500)}...`);
}

simulateAPIRequest().catch(console.error);
