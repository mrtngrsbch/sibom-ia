import { getDatabaseStats } from '@/lib/rag/retriever';
import { readFile } from 'fs/promises';
import path from 'path';

/**
 * API Route para obtener estadísticas de la base de datos
 * @route GET /api/stats
 *
 * Prioridad: SQLite > JSON > municipios.json estático
 */
export async function GET() {
  try {
    // Nota: sqlite-retriever.ts fue deprecado y eliminado en Sprint 4
    // Usamos directamente getDatabaseStats() que tiene el fallback necesario
    let stats;
    try {
      stats = await getDatabaseStats();
    } catch (dbError) {
      console.error('[/api/stats] Error obteniendo estadísticas:', dbError);
      throw dbError;
    }

    // Sobrescribir municipalityList con la lista oficial de municipios
    // Esto asegura que siempre se muestren los municipios disponibles
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
      console.warn('[/api/stats] No se pudo cargar municipios.json, usando stats de DB:', municipiosError);
      // Si falla, se mantiene la lista de la BD (fallback)
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
