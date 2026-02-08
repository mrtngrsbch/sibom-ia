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
    // Intentar usar SQLite primero si está disponible
    let stats;
    try {
      // Importación dinámica para evitar errores si better-sqlite3 no está instalado
      const sqliteModule = await import('@/lib/rag/sqlite-retriever');
      if (sqliteModule.isSQLiteAvailable()) {
        console.log('[/api/stats] 🗄️ Usando SQLite para estadísticas');
        stats = await sqliteModule.getSQLiteStats();
      } else {
        throw new Error('SQLite no disponible');
      }
    } catch (sqliteError) {
      console.log('[/api/stats] 📄 SQLite no disponible, usando JSON fallback:', sqliteError);
      // Fallback a JSON
      stats = await getDatabaseStats();
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
