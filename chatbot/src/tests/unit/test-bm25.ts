/**
 * Test de BM25 con ejemplos reales
 */

import { BM25Index, tokenize } from '@/lib/rag/bm25';

// Documentos de ejemplo (simulando ordenanzas)
const documents = [
  {
    title: 'Ordenanza Fiscal N° 2929/2025 - Carlos Tejedor',
    content: 'La presente ordenanza establece el régimen fiscal para el ejercicio 2025. Define las tasas, derechos y contribuciones municipales. Título Primero: Disposiciones Generales. Artículo 1: El presente régimen regirá desde el 1 de enero de 2025.'
  },
  {
    title: 'Ordenanza N° 2850/2024 - Carlos Tejedor - Urbanismo',
    content: 'Esta ordenanza regula el código de urbanismo y edificación. Establece normas sobre construcción, ampliación y modificación de edificios. Aplica a todo el ejido municipal.'
  },
  {
    title: 'Resolución N° 45/2025 - Carlos Tejedor - Recursos Humanos',
    content: 'Aprueba el escalafón municipal para el personal de planta permanente. Establece categorías y sueldos básicos. Vigencia desde febrero 2025.'
  },
  {
    title: 'Ordenanza de Tránsito N° 2100/2023 - Carlos Tejedor',
    content: 'Regula el tránsito vehicular y peatonal en el municipio. Establece multas, sanciones y procedimientos. Incluye señalización vial y estacionamiento.'
  },
  {
    title: 'Ordenanza N° 2930/2025 - Carlos Tejedor - Ambiente',
    content: 'Ordenanza de protección ambiental. Regula residuos, arbolado público, áreas verdes y control de contaminación. Año 2025.'
  }
];

// Tokenizar documentos
const tokenizedDocs = documents.map(doc =>
  tokenize(`${doc.title} ${doc.content}`)
);

// Crear índice BM25
const bm25 = new BM25Index(tokenizedDocs);

// Test queries
const queries = [
  'lista de ordenanzas de carlos tejedor del año 2025',
  'ordenanza fiscal 2025',
  'resoluciones de recursos humanos',
  'tránsito y multas',
  'medio ambiente protección'
];

console.log('=== TEST BM25 ===\n');

for (const query of queries) {
  console.log(`Query: "${query}"`);
  console.log('Tokens:', tokenize(query));

  const results = bm25.search(query, 3);

  console.log(`\nTop 3 resultados:\n`);
  results.forEach((result, i) => {
    console.log(`${i + 1}. [Score: ${result.score.toFixed(2)}] ${documents[result.index].title}`);

    // Mostrar explicación del score
    const explanation = bm25.explainScore(query, result.index);
    console.log(`   Desglose:`);
    explanation.termScores
      .filter(t => t.contribution > 0)
      .sort((a, b) => b.contribution - a.contribution)
      .slice(0, 3)
      .forEach(term => {
        console.log(`   - "${term.term}": TF=${term.tf}, IDF=${term.idf.toFixed(2)}, contrib=${term.contribution.toFixed(2)}`);
      });
  });

  console.log('\n' + '='.repeat(80) + '\n');
}
