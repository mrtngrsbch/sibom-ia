import { invalidateCache } from '@/lib/rag/retriever';
import { NextRequest, NextResponse } from 'next/server';
import crypto from 'crypto';

/**
 * Webhook de GitHub para invalidar cache cuando se actualiza el repo de datos
 * @route POST /api/webhook/github
 *
 * Configuración en GitHub:
 * 1. Ve a tu repo sibom-data → Settings → Webhooks → Add webhook
 * 2. Payload URL: https://tu-app.vercel.app/api/webhook/github
 * 3. Content type: application/json
 * 4. Secret: (genera un token aleatorio y agrégalo como GITHUB_WEBHOOK_SECRET en Vercel)
 * 5. Events: Just the push event
 */
export async function POST(request: NextRequest) {
  try {
    const signature = request.headers.get('x-hub-signature-256');
    const body = await request.text();

    // Verificar firma de GitHub (seguridad)
    if (process.env.GITHUB_WEBHOOK_SECRET) {
      if (!signature) {
        console.warn('[GitHubWebhook] Firma no proporcionada');
        return NextResponse.json(
          { error: 'Firma no proporcionada' },
          { status: 401 }
        );
      }

      const hmac = crypto.createHmac('sha256', process.env.GITHUB_WEBHOOK_SECRET);
      const expectedSignature = `sha256=${hmac.update(body).digest('hex')}`;

      if (signature !== expectedSignature) {
        console.warn('[GitHubWebhook] Firma inválida');
        return NextResponse.json(
          { error: 'Firma inválida' },
          { status: 401 }
        );
      }
    }

    const payload = JSON.parse(body);

    // Verificar que es un push event
    if (payload.ref === 'refs/heads/main' || payload.ref === 'refs/heads/master') {
      console.log('[GitHubWebhook] Push detectado en rama principal - Invalidando cache');

      // Invalidar cache del RAG
      invalidateCache();

      return NextResponse.json({
        success: true,
        message: 'Cache invalidado por webhook de GitHub',
        timestamp: new Date().toISOString(),
        commits: payload.commits?.length || 0
      });
    }

    return NextResponse.json({
      success: true,
      message: 'Evento recibido pero no es push a main',
      ref: payload.ref
    });

  } catch (error) {
    console.error('[GitHubWebhook] Error:', error);
    return NextResponse.json(
      { error: 'Error procesando webhook' },
      { status: 500 }
    );
  }
}

/**
 * Health check del endpoint
 */
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    endpoint: 'GitHub Webhook Handler',
    configured: !!process.env.GITHUB_WEBHOOK_SECRET
  });
}
