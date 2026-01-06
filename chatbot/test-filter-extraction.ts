/**
 * Test de extracción de filtros
 */

import { extractFiltersFromQuery } from './src/lib/query-filter-extractor';

const municipalities = ['Carlos Tejedor', 'Salto', 'Alberti'];

const query = "lista de ordenanzas de carlos tejedor del año 2025";

const filters = extractFiltersFromQuery(query, municipalities, {});

console.log('\n=== TEST EXTRACCIÓN DE FILTROS ===');
console.log('Query:', query);
console.log('\nFiltros extraídos:');
console.log(JSON.stringify(filters, null, 2));

if (filters.type === 'ordenanza') {
  console.log('\n✅ ÉXITO: Tipo "ordenanza" extraído correctamente');
} else {
  console.log('\n❌ ERROR: Tipo NO extraído. Valor:', filters.type);
}

if (filters.municipality === 'Carlos Tejedor') {
  console.log('✅ ÉXITO: Municipio extraído correctamente');
} else {
  console.log('❌ ERROR: Municipio NO extraído');
}

if (filters.dateFrom === '2025-01-01' && filters.dateTo === '2025-12-31') {
  console.log('✅ ÉXITO: Año extraído correctamente');
} else {
  console.log('❌ ERROR: Año NO extraído');
}
