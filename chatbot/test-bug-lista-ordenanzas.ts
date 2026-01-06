/**
 * Test para reproducir bug: "lista de ordenanzas de carlos tejedor del año 2025"
 *
 * Problema reportado:
 * - LLM responde "Encontré 10 ordenanzas" cuando hay 21
 * - Fuentes Consultadas muestra 24 documentos (algunos son decretos)
 *
 * Hipótesis:
 * 1. BM25 está buscando texto "ordenanza" en vez de filtrar por documentTypes
 * 2. LLM está ignorando la instrucción de listar TODAS las ordenanzas
 */

import { retrieveContext } from './src/lib/rag/retriever';
import { extractFiltersFromQuery } from './src/lib/query-filter-extractor';

const query = "lista de ordenanzas de carlos tejedor del año 2025";
const municipalities = ['Carlos Tejedor', 'Salto', 'Alberti'];

async function testBug() {
  console.log('\n=== TEST BUG LISTA ORDENANZAS ===\n');
  console.log('Query:', query);
  console.log('\n--- Paso 1: Extracción de filtros ---');

  const filters = extractFiltersFromQuery(query, municipalities, {});
  console.log('Filtros extraídos:', JSON.stringify(filters, null, 2));

  console.log('\n--- Paso 2: Recuperación de contexto ---');

  const searchOptions = {
    ...filters,
    limit: 50 // Límite alto para asegurar que obtenemos todas
  };

  console.log('Opciones de búsqueda:', JSON.stringify(searchOptions, null, 2));

  const result = await retrieveContext(query, searchOptions);

  console.log('\n--- Paso 3: Análisis de resultados ---');
  console.log(`Total de fuentes recuperadas: ${result.sources.length}`);

  // Contar por tipo de documento
  const typeCount: Record<string, number> = {};
  result.sources.forEach(source => {
    const types = source.documentTypes || [source.type];
    types.forEach(t => {
      typeCount[t] = (typeCount[t] || 0) + 1;
    });
  });

  console.log('\nConteo por tipo:');
  Object.entries(typeCount).forEach(([type, count]) => {
    console.log(`  ${type}: ${count}`);
  });

  // Filtrar solo ordenanzas reales (con documentTypes)
  const realOrdenanzas = result.sources.filter(source =>
    source.documentTypes && source.documentTypes.includes('ordenanza')
  );

  console.log(`\n✅ Ordenanzas reales (con documentTypes): ${realOrdenanzas.length}`);

  // Mostrar primeras 5 ordenanzas
  console.log('\nPrimeras 5 ordenanzas:');
  realOrdenanzas.slice(0, 5).forEach((ord, i) => {
    console.log(`${i + 1}. ${ord.title}`);
    console.log(`   documentTypes: ${JSON.stringify(ord.documentTypes)}`);
    console.log(`   type: ${ord.type}`);
  });

  // Verificar si hay documentos que NO son ordenanzas
  const nonOrdenanzas = result.sources.filter(source =>
    !source.documentTypes || !source.documentTypes.includes('ordenanza')
  );

  if (nonOrdenanzas.length > 0) {
    console.log(`\n❌ ERROR: Se recuperaron ${nonOrdenanzas.length} documentos que NO son ordenanzas:`);
    nonOrdenanzas.slice(0, 3).forEach((doc, i) => {
      console.log(`${i + 1}. ${doc.title}`);
      console.log(`   documentTypes: ${JSON.stringify(doc.documentTypes)}`);
      console.log(`   type: ${doc.type}`);
    });
  }

  console.log('\n=== FIN TEST ===\n');
}

testBug().catch(console.error);
