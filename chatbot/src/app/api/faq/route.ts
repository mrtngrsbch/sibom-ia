/**
 * API Route para obtener FAQs con contenido dinámico actualizado
 * @route GET /api/faq
 * @route GET /api/faq?id=faq-002
 */

import { getFAQById, findMatchingFAQs } from '@/lib/faq/cached-faqs';
import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const faqId = searchParams.get('id');
    const query = searchParams.get('q');

    // Si se solicita un FAQ específico por ID
    if (faqId) {
      const faq = await getFAQById(faqId);
      
      if (!faq) {
        return new Response(
          JSON.stringify({ error: 'FAQ no encontrado' }),
          { status: 404, headers: { 'Content-Type': 'application/json' } }
        );
      }

      return new Response(
        JSON.stringify(faq),
        { 
          status: 200, 
          headers: { 'Content-Type': 'application/json' } 
        }
      );
    }

    // Si se solicita búsqueda por consulta
    if (query) {
      const matchingFAQs = await findMatchingFAQs(query);
      
      return new Response(
        JSON.stringify({ 
          query,
          results: matchingFAQs,
          count: matchingFAQs.length
        }),
        { 
          status: 200, 
          headers: { 'Content-Type': 'application/json' } 
        }
      );
    }

    // Si no hay parámetros específicos, devolver error
    return new Response(
      JSON.stringify({ 
        error: 'Parámetro requerido: id o q',
        examples: [
          '/api/faq?id=faq-002',
          '/api/faq?q=municipios+disponibles'
        ]
      }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error en /api/faq:', error);
    return new Response(
      JSON.stringify({ error: 'Error interno del servidor' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

/**
 * POST endpoint para forzar actualización de FAQs dinámicos
 * @route POST /api/faq
 */
export async function POST() {
  try {
    // Forzar actualización del FAQ de municipios
    const municipiosFAQ = await getFAQById('faq-002');
    
    if (!municipiosFAQ) {
      return new Response(
        JSON.stringify({ error: 'FAQ de municipios no encontrado' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({ 
        message: 'FAQs dinámicos actualizados correctamente',
        updated: ['faq-002'],
        timestamp: new Date().toISOString()
      }),
      { 
        status: 200, 
        headers: { 'Content-Type': 'application/json' } 
      }
    );

  } catch (error) {
    console.error('Error actualizando FAQs:', error);
    return new Response(
      JSON.stringify({ error: 'Error actualizando FAQs' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}