/**
 * Test para Estrategia A (auto-aplicar filtros)
 */

import { analyzeQuery } from './src/lib/query-analyzer';

const municipalities = [
  'Carlos Tejedor',
  'Salto',
  'Alberti',
  'Bahía Blanca'
];

const filters = { municipality: null };

// Test: Primera pregunta del usuario
const query = "cuantas resoluciones tuvo carlos tejedor en el 2025?";
const analysis = analyzeQuery(query, filters, municipalities);

console.log('\n=== ESTRATEGIA A: AUTO-APLICAR FILTROS ===');
console.log('Query:', query);
console.log('Municipio detectado:', analysis.extractedFilters?.municipality);
console.log('');

// Simular lo que hace el frontend ahora (líneas 189-194 de ChatContainer.tsx)
const finalFilters = {
  municipality: filters.municipality || analysis.extractedFilters?.municipality,
  ordinanceType: undefined,
  dateFrom: null,
  dateTo: null
};

console.log('Filtros finales que se envían al backend:');
console.log(JSON.stringify(finalFilters, null, 2));
console.log('');

if (finalFilters.municipality === 'Carlos Tejedor') {
  console.log('✅ ÉXITO: El municipio se auto-aplicó correctamente');
  console.log('✅ La búsqueda se hará directamente en Carlos Tejedor sin pedir confirmación');
} else {
  console.log('❌ ERROR: El municipio NO se auto-aplicó');
}
