import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

/**
 * API Route para obtener el contenido del FAQ en markdown
 * @route GET /api/faq-content
 */
export async function GET() {
  try {
    const faqPath = path.join(process.cwd(), 'src', 'content', 'faq.md');
    const content = await fs.readFile(faqPath, 'utf-8');

    return new NextResponse(content, {
      status: 200,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
      },
    });
  } catch (error) {
    console.error('Error leyendo faq.md:', error);
    return NextResponse.json(
      { error: 'Error cargando el contenido del FAQ' },
      { status: 500 }
    );
  }
}
