import { NextResponse } from 'next/server';
import { generateMunicipiosStats } from '@/lib/data/process-municipios';

/**
 * API Route para obtener estadísticas de municipios
 * GET /api/municipios-stats
 */
export async function GET() {
  try {
    const stats = generateMunicipiosStats();

    return NextResponse.json(stats, {
      headers: {
        'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      },
    });
  } catch (error) {
    console.error('Error generando estadísticas:', error);
    return NextResponse.json(
      { error: 'Error al generar estadísticas' },
      { status: 500 }
    );
  }
}
