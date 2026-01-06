/**
 * Test del FIX para el bug de búsqueda Carlos Tejedor 2025
 *
 * BUG ORIGINAL:
 * Query: "cuantas ordenanzas tuvo carlos tejedor en el 2025?"
 * Problema: No se extraía el año 2025 de la query para filtrar
 *
 * FIX IMPLEMENTADO:
 * - Creado query-filter-extractor.ts
 * - Integrado en route.ts para extraer año, municipio y tipo automáticamente
 */

import { extractFiltersFromQuery, extractYear, extractMunicipality, extractOrdinanceType, yearToDateRange } from './src/lib/query-filter-extractor';
import { retrieveContext, getDatabaseStats } from './src/lib/rag/retriever';

async function testFix() {
  console.log('=== TEST DEL FIX ===\n');

  const query = "cuantas ordenanzas tuvo carlos tejedor en el 2025?";
  console.log(`Query: "${query}"\n`);

  // 1. Test de extracción de año
  console.log('[1] Extracción de año');
  const year = extractYear(query);
  console.log(`   Año detectado: ${year || 'NINGUNO'} ${year ? '✅' : '❌'}`);

  if (year) {
    const dateRange = yearToDateRange(year);
    console.log(`   Rango de fechas: ${dateRange.dateFrom} → ${dateRange.dateTo}`);
  }

  // 2. Test de extracción de municipio
  console.log('\n[2] Extracción de municipio');
  const stats = await getDatabaseStats();
  const municipality = extractMunicipality(query, stats.municipalityList);
  console.log(`   Municipio detectado: ${municipality || 'NINGUNO'} ${municipality ? '✅' : '❌'}`);

  // 3. Test de extracción de tipo
  console.log('\n[3] Extracción de tipo de normativa');
  const ordinanceType = extractOrdinanceType(query);
  console.log(`   Tipo detectado: ${ordinanceType || 'NINGUNO'} ${ordinanceType ? '✅' : '❌'}`);

  // 4. Test de extracción completa
  console.log('\n[4] Extracción completa de filtros');
  const extractedFilters = extractFiltersFromQuery(query, stats.municipalityList, {});
  console.log(`   Filtros extraídos:`);
  console.log(`   - Municipio: ${extractedFilters.municipality || 'N/A'}`);
  console.log(`   - Tipo: ${extractedFilters.type || 'N/A'}`);
  console.log(`   - Fecha desde: ${extractedFilters.dateFrom || 'N/A'}`);
  console.log(`   - Fecha hasta: ${extractedFilters.dateTo || 'N/A'}`);

  // 5. Test de búsqueda con filtros extraídos
  console.log('\n[5] Búsqueda con filtros extraídos');
  const result = await retrieveContext(query, {
    ...extractedFilters,
    limit: 25 // Aumentar límite para ver todas las ordenanzas de 2025
  });

  console.log(`   Documentos recuperados: ${result.sources.length}`);

  // Contar ordenanzas vs boletines
  const ordenanzasCount = result.sources.filter(s => s.type === 'ordenanza').length;
  const boletinesCount = result.sources.filter(s => s.type === 'boletin').length;

  console.log(`   - Ordenanzas: ${ordenanzasCount}`);
  console.log(`   - Boletines: ${boletinesCount}`);

  console.log('\n   Primeras 10 fuentes:');
  result.sources.slice(0, 10).forEach((s, i) => {
    console.log(`   ${i + 1}. ${s.title} (${s.type})`);
  });

  // 6. Validación final
  console.log('\n=== VALIDACIÓN FINAL ===');

  const expectedOrdenanzas = 24; // Verificado en el índice
  const success = ordenanzasCount === expectedOrdenanzas;

  if (success) {
    console.log(`✅ FIX EXITOSO: Se recuperaron ${ordenanzasCount}/${expectedOrdenanzas} ordenanzas de 2025`);
  } else {
    console.log(`❌ FIX PARCIAL: Se recuperaron ${ordenanzasCount}/${expectedOrdenanzas} ordenanzas de 2025`);
    if (ordenanzasCount > 0) {
      console.log(`   Nota: El fix funciona, pero el límite de recuperación es ${result.sources.length}`);
    }
  }

  // 7. Tests adicionales de edge cases
  console.log('\n=== EDGE CASES ===');

  const testCases = [
    'decretos de 2024 en salto',
    'ordenanza 2833',
    'en el año 2023',
    'carlos tejedor ordenanzas',
    'que normativas hay del 2022?'
  ];

  for (const testQuery of testCases) {
    const filters = extractFiltersFromQuery(testQuery, stats.municipalityList, {});
    const hasYear = !!(filters.dateFrom && filters.dateTo);
    const hasMunicipality = !!filters.municipality;
    const hasType = !!filters.type;

    console.log(`\nQuery: "${testQuery}"`);
    console.log(`  Año: ${hasYear ? '✅' : '❌'} | Municipio: ${hasMunicipality ? '✅' : '❌'} | Tipo: ${hasType ? '✅' : '❌'}`);
    if (filters.dateFrom) console.log(`  Rango: ${filters.dateFrom} → ${filters.dateTo}`);
    if (filters.municipality) console.log(`  Municipio: ${filters.municipality}`);
    if (filters.type) console.log(`  Tipo: ${filters.type}`);
  }
}

testFix().catch(console.error);
