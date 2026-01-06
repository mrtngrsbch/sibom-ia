/**
 * Test del bug de búsqueda Carlos Tejedor 2025
 *
 * BUG REPORTADO:
 * Query: "cuantas ordenanzas tuvo carlos tejedor en el 2025?"
 * Respuesta del chatbot: "no se registran ordenanzas para Carlos Tejedor en 2025"
 *
 * REALIDAD:
 * Existen 24 ordenanzas de Carlos Tejedor en 2025 (confirmado en índice)
 */

import { retrieveContext } from './src/lib/rag/retriever';
import { needsRAGSearch } from './src/lib/query-classifier';

async function testBug() {
  const query = "cuantas ordenanzas tuvo carlos tejedor en el 2025?";

  console.log('=== TEST DEL BUG ===');
  console.log(`Query: "${query}"\n`);

  // 1. Verificar si se detecta como búsqueda RAG
  const needsSearch = needsRAGSearch(query);
  console.log(`[1] ¿Necesita búsqueda RAG? ${needsSearch ? '✅ SÍ' : '❌ NO'}`);

  if (!needsSearch) {
    console.log('❌ ERROR: El query classifier NO detectó esta como búsqueda RAG');
    console.log('   Esto significa que el chatbot respondería sin buscar en la base de datos\n');
  }

  // 2. Probar búsqueda con filtro de municipio
  console.log('\n[2] Probando búsqueda con filtro de municipio: "Carlos Tejedor"');
  const result1 = await retrieveContext(query, {
    municipality: 'Carlos Tejedor',
    limit: 10
  });

  console.log(`   Documentos recuperados: ${result1.sources.length}`);
  console.log('   Fuentes encontradas:');
  result1.sources.forEach((s, i) => {
    console.log(`   ${i + 1}. ${s.title} (${s.type})`);
  });

  // 3. Probar búsqueda con filtro de municipio + año
  console.log('\n[3] Probando búsqueda con filtro de municipio + fechas de 2025');
  const result2 = await retrieveContext(query, {
    municipality: 'Carlos Tejedor',
    dateFrom: '2025-01-01',
    dateTo: '2025-12-31',
    limit: 10
  });

  console.log(`   Documentos recuperados: ${result2.sources.length}`);
  console.log('   Fuentes encontradas:');
  result2.sources.forEach((s, i) => {
    console.log(`   ${i + 1}. ${s.title} (${s.type})`);
  });

  // 4. Probar búsqueda SIN filtros (como lo haría el usuario)
  console.log('\n[4] Probando búsqueda SIN filtros (municipio mencionado en query)');
  const result3 = await retrieveContext(query, {
    limit: 10
  });

  console.log(`   Documentos recuperados: ${result3.sources.length}`);
  console.log('   Fuentes encontradas:');
  result3.sources.forEach((s, i) => {
    console.log(`   ${i + 1}. ${s.title} (${s.type})`);
  });

  // 5. Análisis del problema
  console.log('\n=== ANÁLISIS DEL BUG ===');

  if (result1.sources.length === 0 && result2.sources.length === 0 && result3.sources.length === 0) {
    console.log('❌ PROBLEMA CRÍTICO: No se recuperan documentos en NINGÚN caso');
    console.log('   Posibles causas:');
    console.log('   1. El filtro de fecha no funciona correctamente');
    console.log('   2. El filtro de municipio no funciona');
    console.log('   3. El scoring de relevancia es muy bajo');
    console.log('   4. Hay un problema con el formato de fechas');
  } else if (result1.sources.length > 0 || result2.sources.length > 0) {
    console.log('✅ Con filtros SÍ funciona');
    console.log('❌ Sin filtros NO funciona (problema de extracción de municipio desde query)');
  } else {
    console.log('🤔 Comportamiento mixto - necesita investigación más profunda');
  }
}

testBug().catch(console.error);
