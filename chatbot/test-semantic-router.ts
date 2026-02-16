/**
 * test-semantic-router.ts
 *
 * Test suite para validar el funcionamiento del SemanticRouter (Layer 3).
 * Verifica que las queries se clasifiquen correctamente y se asignen a los tiers apropiados.
 *
 * @author AI Agent
 * @created 2026-02-15
 */

import { routeQuery, filterChunksByTier, explainRouting, needsExecutiveSummary } from './src/lib/rag/semantic-router';

// Mock chunks para testing
const mockChunks = [
  // TIER-1: Executive
  {
    chunk_id: 'exec_1',
    tier: 1,
    completeness_score: 1.0,
    embedding_text: 'Balance Carlos Tejedor 2024-T1: Saldo Inicial $469M, Total Ingresos $2B...',
  },
  // TIER-3: Details (varios)
  {
    chunk_id: 'detail_1',
    tier: 3,
    completeness_score: 0.2,
    embedding_text: 'Cuenta 111210108: Sueldos Personal Municipal...',
  },
  {
    chunk_id: 'detail_2',
    tier: 3,
    completeness_score: 0.2,
    embedding_text: 'Cuenta 111220305: Honorarios Profesionales...',
  },
  {
    chunk_id: 'detail_3',
    tier: 3,
    completeness_score: 0.2,
    embedding_text: 'Cuenta 111230402: Servicios Públicos...',
  },
];

// Test cases
const testCases = [
  {
    query: '¿Cuál es el saldo inicial de Carlos Tejedor en 2024-T1?',
    expectedType: 'executive_summary',
    expectedTiers: [1],
    expectedMaxResults: 1,
    description: 'Query directa sobre total → TIER-1 solo',
  },
  {
    query: '¿Cuánto es el total de ingresos del trimestre?',
    expectedType: 'executive_summary',
    expectedTiers: [1],
    expectedMaxResults: 1,
    description: 'Query sobre totalización → TIER-1 solo',
  },
  {
    query: '¿Cuál es la diferencia entre el saldo inicial y el saldo final?',
    expectedType: 'comparison',
    expectedTiers: [1, 2],
    expectedMaxResults: 10,
    description: 'Query de comparación → TIER-1 + TIER-2',
  },
  {
    query: '¿Qué cuenta tiene el número 111210108?',
    expectedType: 'detail',
    expectedTiers: [2, 3],
    expectedMaxResults: 20,
    description: 'Query específica de cuenta → TIER-2 + TIER-3',
  },
  {
    query: 'Mostrame los sueldos del personal municipal',
    expectedType: 'detail',
    expectedTiers: [2, 3],
    expectedMaxResults: 20,
    description: 'Query sobre partida específica → TIER-2 + TIER-3',
  },
  {
    query: '¿Cuánto gastaron en total en servicios?',
    expectedType: 'aggregation',
    expectedTiers: [1, 2],
    expectedMaxResults: 15,
    description: 'Query de agregación → TIER-1 + TIER-2',
  },
  {
    query: 'Ordenanza 123',
    expectedType: 'general',
    expectedTiers: [1, 2, 3],
    expectedMaxResults: 10,
    description: 'Query no-Balance → general search',
  },
];

console.log('='.repeat(80));
console.log('TEST: SemanticRouter (Layer 3)');
console.log('='.repeat(80));

let passedTests = 0;
let failedTests = 0;

for (let i = 0; i < testCases.length; i++) {
  const test = testCases[i];
  console.log(`\nTest ${i + 1}/${testCases.length}: ${test.description}`);
  console.log(`Query: "${test.query}"`);
  
  const result = routeQuery(test.query);
  
  console.log(`\nResult:`);
  console.log(explainRouting(result));
  
  // Validar tipo
  const typeMatch = result.queryType === test.expectedType;
  console.log(`\n✓ Type: ${result.queryType} ${typeMatch ? '✅' : `❌ (expected ${test.expectedType})`}`);
  
  // Validar tiers
  const tiersMatch = JSON.stringify(result.tiers) === JSON.stringify(test.expectedTiers);
  console.log(`✓ Tiers: ${result.tiers.join(', ')} ${tiersMatch ? '✅' : `❌ (expected ${test.expectedTiers.join(', ')})`}`);
  
  // Validar maxResults
  const maxResultsMatch = result.maxResults === test.expectedMaxResults;
  console.log(`✓ MaxResults: ${result.maxResults} ${maxResultsMatch ? '✅' : `❌ (expected ${test.expectedMaxResults})`}`);
  
  // Test de filtrado de chunks
  console.log(`\n--- Testing chunk filtering ---`);
  const filteredChunks = filterChunksByTier(mockChunks, result);
  console.log(`Original chunks: ${mockChunks.length}`);
  console.log(`Filtered chunks: ${filteredChunks.length}`);
  console.log(`Filtered tiers: ${filteredChunks.map((c: any) => c.tier).join(', ')}`);
  
  // Validar que solo incluye tiers esperados
  const allTiersValid = filteredChunks.every((chunk: any) =>
    test.expectedTiers.includes(chunk.tier || 3)
  );
  console.log(`Tier filtering: ${allTiersValid ? '✅' : '❌'}`);
  
  if (typeMatch && tiersMatch && maxResultsMatch && allTiersValid) {
    passedTests++;
    console.log(`\n✅ Test ${i + 1} PASSED`);
  } else {
    failedTests++;
    console.log(`\n❌ Test ${i + 1} FAILED`);
  }
  
  console.log('-'.repeat(80));
}

console.log('\n' + '='.repeat(80));
console.log('SUMMARY');
console.log('='.repeat(80));
console.log(`Total tests: ${testCases.length}`);
console.log(`Passed: ${passedTests} ✅`);
console.log(`Failed: ${failedTests} ${failedTests > 0 ? '❌' : ''}`);
console.log(`Success rate: ${((passedTests / testCases.length) * 100).toFixed(0)}%`);

// Test de needsExecutiveSummary utility
console.log('\n' + '-'.repeat(80));
console.log('UTILITY FUNCTIONS TEST');
console.log('-'.repeat(80));

const executiveQueries = [
  '¿Cuál es el saldo inicial?',
  '¿Cuánto es el saldo final del trimestre?',
];

const nonExecutiveQueries = [
  '¿Cuánto es el total de ingresos?',  // aggregation, not executive
  '¿Qué cuenta tiene el número 123?',
  'Mostrame los sueldos',
];

console.log('\nneedsExecutiveSummary() tests:');
for (const q of executiveQueries) {
  const needs = needsExecutiveSummary(q);
  console.log(`"${q}" → ${needs ? '✅ Executive' : '❌ Not executive'}`);
  if (!needs) failedTests++;
}

for (const q of nonExecutiveQueries) {
  const needs = needsExecutiveSummary(q);
  console.log(`"${q}" → ${!needs ? '✅ Not executive' : '❌ Executive (wrong)'}`);
  if (needs) failedTests++;
}

console.log('\n' + '='.repeat(80));

if (failedTests === 0) {
  console.log('🎯 ALL TESTS PASSED! Layer 3 (SemanticRouter) is working correctly ✅');
  process.exit(0);
} else {
  console.log(`⚠️ ${failedTests} test(s) failed. Please review the implementation.`);
  process.exit(1);
}
