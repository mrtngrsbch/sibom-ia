import { retrieveContext, getDatabaseStats } from './src/lib/rag/retriever';

async function test() {
  console.log('--- Iniciando prueba de Retriever ---');
  
  try {
    const stats = await getDatabaseStats();
    console.log('Estadísticas:', stats);

    const query = 'ordenanza sobre presupuesto en Carlos Tejedor';
    console.log(`\nProbando consulta: "${query}"`);
    
    const result = await retrieveContext(query, {
      municipality: 'Carlos Tejedor',
      limit: 3
    });

    console.log('\nContexto recuperado (primeros 200 chars):');
    console.log(result.context.slice(0, 200) + '...');
    
    console.log('\nFuentes:');
    result.sources.forEach(s => console.log(`- ${s.title} (${s.url})`));

    if (result.sources.length > 0) {
      console.log('\n✅ Prueba exitosa');
    } else {
      console.log('\n⚠️ No se encontraron resultados');
    }
  } catch (error) {
    console.error('\n❌ Error en la prueba:', error);
  }
}

test();
