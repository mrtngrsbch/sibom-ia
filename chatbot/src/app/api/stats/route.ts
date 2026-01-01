import { getDatabaseStats } from '@/lib/rag/retriever';

/**
 * API Route para obtener estadísticas de la base de datos
 * @route GET /api/stats
 */
export async function GET() {
  try {
    const stats = await getDatabaseStats();
    
    return new Response(
      JSON.stringify(stats),
      { 
        status: 200, 
        headers: { 'Content-Type': 'application/json' } 
      }
    );
  } catch (error) {
    console.error('Error en /api/stats:', error);
    return new Response(
      JSON.stringify({ error: 'Error obteniendo estadísticas' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
