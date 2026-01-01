import { invalidateCache } from '@/lib/rag/retriever';
import { NextResponse } from 'next/server';

/**
 * API Route para refrescar el cache del índice de documentos
 * @route POST /api/refresh
 * @description Invalida el cache del retriever para forzar recarga del índice
 */
export async function POST() {
  try {
    // Invalidar el cache del retriever
    invalidateCache();
    
    return NextResponse.json({ 
      success: true, 
      message: 'Cache invalidado correctamente',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('[RefreshAPI] Error:', error);
    return NextResponse.json(
      { success: false, error: 'Error al invalidar cache' },
      { status: 500 }
    );
  }
}

/**
 * API Route para verificar si hay actualizaciones disponibles
 * @route GET /api/refresh
 * @description Devuelve información sobre la última actualización del índice
 */
export async function GET() {
  try {
    const { getDatabaseStats } = await import('@/lib/rag/retriever');
    const stats = await getDatabaseStats();
    
    return NextResponse.json({
      lastUpdated: stats.lastUpdated,
      totalDocuments: stats.totalDocuments,
      municipalities: stats.municipalities
    });
  } catch (error) {
    console.error('[RefreshAPI] Error:', error);
    return NextResponse.json(
      { error: 'Error al obtener información de actualización' },
      { status: 500 }
    );
  }
}
