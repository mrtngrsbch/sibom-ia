import { getDatabaseStats } from '@/lib/rag/retriever';
import { readFile } from 'fs/promises';
import path from 'path';

/**
 * API Route para obtener estadísticas de la base de datos
 * @route GET /api/stats
 *
 * La lista de municipios se obtiene del archivo estático municipios.json
 * que contiene la lista oficial de 88 municipios disponibles en SIBOM.
 */
export async function GET() {
  try {
    // Obtener estadísticas de la base de datos
    const stats = await getDatabaseStats();

    // Sobrescribir municipalityList con la lista oficial de municipios
    // Esto asegura que siempre se muestren los 88 municipios disponibles
    // independientemente de cuántos hayan sido procesados en los índices
    try {
      const municipiosPath = path.join(process.cwd(), 'public', 'data', 'municipios.json');
      const municipiosData = JSON.parse(await readFile(municipiosPath, 'utf-8'));

      // Reemplazar con la lista oficial de municipios
      const responseStats = {
        ...stats,
        municipalityList: municipiosData.municipios,
        municipalities: municipiosData.municipios.length,
      };

      return new Response(
        JSON.stringify(responseStats),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    } catch (municipiosError) {
      console.warn('[/api/stats] No se pudo cargar municipios.json, usando fallback:', municipiosError);
      // Si falla, se mantiene la lista del índice (fallback)
      return new Response(
        JSON.stringify(stats),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  } catch (error) {
    console.error('Error en /api/stats:', error);
    return new Response(
      JSON.stringify({ error: 'Error obteniendo estadísticas' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
