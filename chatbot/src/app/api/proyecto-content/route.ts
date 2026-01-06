import { readFileSync } from 'fs';
import { join } from 'path';

/**
 * API Route para servir el contenido de proyecto.md
 * @route GET /api/proyecto-content
 */
export async function GET() {
  try {
    const filePath = join(process.cwd(), 'src', 'content', 'proyecto.md');
    const content = readFileSync(filePath, 'utf-8');

    return new Response(content, {
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
      },
    });
  } catch (error) {
    console.error('Error leyendo proyecto.md:', error);
    return new Response('Error cargando contenido', { status: 500 });
  }
}
