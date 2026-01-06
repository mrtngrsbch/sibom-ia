import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

/**
 * API Route para regenerar el índice de boletines (solo en desarrollo local)
 * @route POST /api/reindex
 * @description Ejecuta python3 indexar_boletines.py si estamos en local
 */
export async function POST() {
  // Solo permitir en desarrollo local
  const isLocal = !process.env.VERCEL && !process.env.GITHUB_DATA_REPO;

  if (!isLocal) {
    return NextResponse.json(
      {
        success: false,
        message: 'Reindexación solo disponible en desarrollo local',
        isProduction: true
      },
      { status: 403 }
    );
  }

  try {
    // Ruta al script de actualización automática
    const pythonCliPath = path.join(process.cwd(), '..', 'python-cli');
    const scriptPath = path.join(pythonCliPath, 'actualizar_index.sh');

    console.log('[Reindex] Ejecutando actualización automática en:', pythonCliPath);
    console.log('[Reindex] Script:', scriptPath);

    // Ejecutar el script bash que:
    // 1. Regenera el índice desde archivos JSON
    // 2. Enriquece con tipos de documentos
    // 3. Reemplaza el índice anterior
    const { stdout, stderr } = await execAsync(
      `cd "${pythonCliPath}" && bash actualizar_index.sh`,
      { timeout: 120000 } // Timeout de 2 minutos (más tiempo para enriquecimiento)
    );

    console.log('[Reindex] Output:', stdout);
    if (stderr) {
      console.warn('[Reindex] Stderr:', stderr);
    }

    // Parsear el output para obtener estadísticas
    const totalMatch = stdout.match(/Total documentos: ([\d,]+)/);
    const enrichedMatch = stdout.match(/Con tipos enriquecidos: ([\d,]+)/);

    const totalDocs = totalMatch ? parseInt(totalMatch[1].replace(/,/g, '')) : null;
    const enrichedDocs = enrichedMatch ? parseInt(enrichedMatch[1].replace(/,/g, '')) : null;

    return NextResponse.json({
      success: true,
      message: 'Índice regenerado y enriquecido correctamente',
      totalDocuments: totalDocs,
      enrichedDocuments: enrichedDocs,
      output: stdout.trim()
    });
  } catch (error) {
    console.error('[Reindex] Error:', error);

    return NextResponse.json(
      {
        success: false,
        error: 'Error al regenerar índice',
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}

/**
 * Verificar si la reindexación está disponible
 * @route GET /api/reindex
 */
export async function GET() {
  const isLocal = !process.env.VERCEL && !process.env.GITHUB_DATA_REPO;

  return NextResponse.json({
    available: isLocal,
    message: isLocal
      ? 'Reindexación disponible en este entorno'
      : 'Reindexación solo disponible en desarrollo local'
  });
}
