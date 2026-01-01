/**
 * Generador de FAQs Dinámicos
 * Actualiza automáticamente el contenido de los FAQs basado en datos reales
 */

import { getDatabaseStats } from '@/lib/rag/retriever';
import { CachedFAQ } from './cached-faqs';

/**
 * Genera el contenido del FAQ de municipios disponibles dinámicamente
 */
export async function generateMunicipalitiesFAQ(): Promise<string> {
  try {
    const stats = await getDatabaseStats();
    
    if (stats.municipalityList.length === 0) {
      return `## Municipios Disponibles

⚠️ **Sistema en actualización** - No hay municipios disponibles actualmente.

### Próximamente
El sistema está configurado para agregar municipios de la Provincia de Buenos Aires progresivamente.

---
¿Te interesa información de algún municipio específico?`;
    }

    // Generar lista de municipios con formato dinámico
    const municipalityList = stats.municipalityList
      .map(municipality => `**${municipality}** - [Ver boletines](/chat?q=boletines+${encodeURIComponent(municipality)})`)
      .join('\n');

    const lastUpdatedText = stats.lastUpdated 
      ? `Última actualización: ${new Date(stats.lastUpdated).toLocaleDateString('es-AR')}`
      : 'Fecha de actualización no disponible';

    return `## Municipios Disponibles

Nuestro sistema actualmente cuenta con información de **${stats.municipalityList.length} municipio${stats.municipalityList.length > 1 ? 's' : ''}**:

${municipalityList}

### Estadísticas Actuales
- **Total de documentos:** ${stats.totalDocuments}
- **Municipios disponibles:** ${stats.municipalityList.length}
- **${lastUpdatedText}**

### Información en Tiempo Real
- [Ver estadísticas completas](/api/stats)
- [Ver todos los municipios](/api/stats)

### Expansión del Sistema
El sistema está en constante crecimiento. Se agregan nuevos municipios de la Provincia de Buenos Aires conforme se procesan sus boletines oficiales del SIBOM.

### ¿Tu municipio no aparece?
Si buscas información de un municipio específico que no está en la lista, el sistema podría agregarlo próximamente. Los datos se actualizan automáticamente.

---
¿Necesitas información de alguno de estos municipios?`;

  } catch (error) {
    console.error('[Dynamic FAQ] Error generando FAQ de municipios:', error);
    
    // Fallback en caso de error
    return `## Municipios Disponibles

❌ **Error temporal** - No se puede obtener la lista actualizada de municipios.

### Alternativas
- Intenta preguntarme directamente sobre el municipio que te interesa
- [Ver estadísticas del sistema](/api/stats)

### Sistema en Funcionamiento
El sistema sigue operativo para consultas generales sobre legislación municipal.

---
¿Puedo ayudarte con alguna consulta específica?`;
  }
}

/**
 * Actualiza un FAQ específico con contenido dinámico
 */
export async function updateFAQWithDynamicContent(faqId: string): Promise<CachedFAQ | null> {
  switch (faqId) {
    case 'faq-002':
      const dynamicAnswer = await generateMunicipalitiesFAQ();
      return {
        id: 'faq-002',
        question: 'Que municipios estan disponibles',
        keywords: ['municipios', 'disponibles', 'ciudades', 'localidades', 'lista', 'cuantos', 'cuales'],
        category: 'general',
        answer: dynamicAnswer
      };
    
    default:
      return null;
  }
}

/**
 * Obtiene la lista de FAQs que requieren contenido dinámico
 */
export function getDynamicFAQIds(): string[] {
  return ['faq-002'];
}

/**
 * Verifica si un FAQ requiere actualización dinámica
 */
export function isDynamicFAQ(faqId: string): boolean {
  return getDynamicFAQIds().includes(faqId);
}