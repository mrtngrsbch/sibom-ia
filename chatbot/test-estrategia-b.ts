/**
 * Test de la Estrategia B: Pedir confirmación antes de aplicar filtros detectados
 *
 * Escenario:
 * 1. Usuario pregunta "cuantas ordenanzas tuvo carlos tejedor en el 2025?"
 * 2. Usuario NO tiene filtro de municipio seleccionado
 * 3. Sistema detecta "Carlos Tejedor" en la query
 * 4. Sistema PREGUNTA al usuario si quiere filtrar por ese municipio
 * 5. Usuario confirma seleccionando el filtro
 * 6. Sistema busca y responde correctamente
 */

import { analyzeQuery } from './src/lib/query-analyzer';

async function testEstrategiaB() {
  console.log('=== TEST ESTRATEGIA B ===\n');

  const query = "cuantas ordenanzas tuvo carlos tejedor en el 2025?";
  const currentFilters = {
    municipality: null  // Usuario NO seleccionó municipio
  };
  const municipalities = ['Carlos Tejedor', 'Salto', 'General Lavalle', 'Pergamino'];

  console.log(`Query: "${query}"`);
  console.log(`Filtros actuales: ${JSON.stringify(currentFilters)}`);
  console.log(`Municipios disponibles: ${municipalities.join(', ')}\n`);

  // Analizar la query
  const analysis = analyzeQuery(query, currentFilters, municipalities);

  console.log('=== RESULTADO DEL ANÁLISIS ===\n');
  console.log(`¿Necesita clarificación? ${analysis.needsClarification ? '✅ SÍ' : '❌ NO'}`);

  if (analysis.needsClarification) {
    console.log(`\nTipo de clarificación: ${analysis.clarification?.type}`);
    console.log(`Mensaje: ${analysis.clarification?.message}`);
    console.log(`Sugerencias: ${analysis.clarification?.suggestions.join(', ')}`);
  }

  if (analysis.extractedFilters) {
    console.log(`\nFiltros extraídos (para aplicar DESPUÉS de confirmar):`);
    console.log(`  Municipio: ${analysis.extractedFilters.municipality || 'N/A'}`);
  }

  // Validación
  console.log('\n=== VALIDACIÓN ===');

  const expectedBehavior = {
    needsClarification: true,
    clarificationType: 'municipality',
    detectedMunicipality: 'Carlos Tejedor'
  };

  const isCorrect = analysis.needsClarification === expectedBehavior.needsClarification &&
                     analysis.clarification?.type === expectedBehavior.clarificationType &&
                     analysis.extractedFilters?.municipality === expectedBehavior.detectedMunicipality;

  if (isCorrect) {
    console.log('✅ ESTRATEGIA B FUNCIONANDO CORRECTAMENTE');
    console.log('   El sistema detectó "Carlos Tejedor" pero NO buscó automáticamente.');
    console.log('   Pedirá confirmación al usuario antes de aplicar el filtro.');
  } else {
    console.log('❌ ERROR EN ESTRATEGIA B');
    console.log('   Esperado:', expectedBehavior);
    console.log('   Obtenido:', {
      needsClarification: analysis.needsClarification,
      clarificationType: analysis.clarification?.type,
      detectedMunicipality: analysis.extractedFilters?.municipality
    });
  }

  // Test casos adicionales
  console.log('\n=== CASOS ADICIONALES ===\n');

  const testCases = [
    {
      name: 'Con municipio seleccionado en filtro',
      query: 'cuantas ordenanzas tuvo carlos tejedor en el 2025?',
      filters: { municipality: 'Carlos Tejedor' },
      expectedClarification: false
    },
    {
      name: 'Sin municipio mencionado ni seleccionado',
      query: 'cuantas ordenanzas hay en 2025?',
      filters: { municipality: null },
      expectedClarification: true
    },
    {
      name: 'Municipio mencionado sin filtro',
      query: 'decretos de Salto en 2024',
      filters: { municipality: null },
      expectedClarification: true
    },
    {
      name: 'Búsqueda en todos los municipios explícita',
      query: 'ordenanzas en todos los municipios de 2025',
      filters: { municipality: null },
      expectedClarification: false
    }
  ];

  for (const testCase of testCases) {
    const result = analyzeQuery(testCase.query, testCase.filters, municipalities);
    const passed = result.needsClarification === testCase.expectedClarification;

    console.log(`${passed ? '✅' : '❌'} ${testCase.name}`);
    console.log(`   Query: "${testCase.query}"`);
    console.log(`   Necesita clarificación: ${result.needsClarification} (esperado: ${testCase.expectedClarification})`);
    if (result.extractedFilters?.municipality) {
      console.log(`   Municipio detectado: ${result.extractedFilters.municipality}`);
    }
    console.log();
  }
}

testEstrategiaB().catch(console.error);
