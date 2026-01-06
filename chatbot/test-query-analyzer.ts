/**
 * Test para query-analyzer
 */

import { analyzeQuery } from './src/lib/query-analyzer';

const municipalities = [
  'Carlos Tejedor',
  'Salto',
  'Alberti',
  'Bahía Blanca'
];

const filters = { municipality: null };

// Test 1: Primera pregunta del usuario
const query1 = "cuantas resoluciones tuvo carlos tejedor en el 2025?";
const result1 = analyzeQuery(query1, filters, municipalities);

console.log('\n=== TEST 1 ===');
console.log('Query:', query1);
console.log('needsClarification:', result1.needsClarification);
console.log('extractedFilters:', result1.extractedFilters);
console.log('clarification:', result1.clarification);

// Test 2: Segunda pregunta del usuario
const query2 = "resoluciones carlos tejedor en el 2025";
const result2 = analyzeQuery(query2, filters, municipalities);

console.log('\n=== TEST 2 ===');
console.log('Query:', query2);
console.log('needsClarification:', result2.needsClarification);
console.log('extractedFilters:', result2.extractedFilters);
console.log('clarification:', result2.clarification);

// Test 3: Verificar detección de municipio
const lowerQuery = query1.toLowerCase();
const found = municipalities.find(m => lowerQuery.includes(m.toLowerCase()));

console.log('\n=== DEBUG ===');
console.log('lowerQuery:', lowerQuery);
console.log('municipalities:', municipalities.map(m => m.toLowerCase()));
console.log('found:', found);
