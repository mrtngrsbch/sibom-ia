/**
 * FAQs Cacheadas para el Chatbot Legal
 * Respuestas predefinidas para preguntas frecuentes sobre legislación municipal
 */

export interface CachedFAQ {
  id: string;
  question: string;
  keywords: string[];
  answer: string;
  category: 'general' | 'consulta' | 'normativa' | 'acceso';
}

export const cachedFAQs: CachedFAQ[] = [
  {
    id: 'faq-001',
    question: 'Como puedo consultar una ordenanza',
    keywords: ['consultar', 'ordenanza', 'buscar', 'encontrar', 'ver'],
    category: 'consulta',
    answer: `## Como Consultar una Ordenanza

Para consultar ordenanzas municipales en nuestro sistema, tenes las siguientes opciones:

**1. Busqueda por Texto**
Escribi palabras clave relacionadas con el tema que te interesa (ej: "transito", "comercio", "medio ambiente") y el sistema buscara en todos los boletines disponibles.

**2. Busqueda por Municipio**
Podes filtrar por municipio especifico si deseas conocer las ordenanzas de una localidad en particular.

**3. Busqueda por Numero**
Si conhees el numero de la ordenanza (ej: "Ordenanza 123"), podes consultarla directamente.

### Fuentes Oficiales
Todas las respuestas incluyen enlaces a los boletines oficiales del SIBOM (Sistema de Boletines Municipales) de la Provincia de Buenos Aires.

---
Necesitas ayuda con algum tema especifico?`
  },
  {
    id: 'faq-002',
    question: 'Que municipios estan disponibles',
    keywords: ['municipios', 'disponibles', 'ciudades', 'localidades', 'lista'],
    category: 'general',
    answer: `## Municipios Disponibles

Nuestro sistema actualmente cuenta con informacion de los siguientes municipios:

**Carlos Tejedor** - Ver boletines
*(Mas municipios se agregaran progresivamente)*

### Actualizacion
Los boletines se actualizan regularmente conforme el sistema de scraping procesa nueva informacion del SIBOM.

### Estadisticas
- Total de documentos: [Ver estadisticas](/api/stats)
- Municipios disponibles: [Ver lista](/api/stats)

### Tu municipio no aparece?
El sistema esta en expansion. Proximamente se agregaran mas municipios de la Provincia de Buenos Aires.

---
Queres informacion de algun municipio especifico?`
  },
  {
    id: 'faq-003',
    question: 'Como accedo a los boletines oficiales',
    keywords: ['boletin', 'boletines', 'oficial', 'acceder', 'ver', 'descargar'],
    category: 'acceso',
    answer: `## Acceso a Boletines Oficiales

### Fuentes Oficiales

Los boletines oficiales de los municipios de Buenos Aires se publican en el SIBOM (Sistema de Boletines Municipales):

**Portal Oficial SIBOM:** https://sibom.slyt.gba.gob.ar

### Que Encontras en un Boletín?

Cada boletín municipal tipicamente contiene:

1. **Ordenanzas** - Normas aprobadas por el Honorable Consejo Deliberante
2. **Decretos** - Decisiones del Departamento Ejecutivo
3. **Resoluciones** - Disposiciones administrativas
4. **Edictos** - Comunicaciones oficiales

### Acceso desde nuestro Chatbot

Nuestro chatbot te permite:

- **Buscar** por tema, numero o fecha
- **Consultar** el contenido de ordenanzas y decretos
- **Obtener** enlaces directos a las fuentes oficiales

### Consultar Directamente

Si necesitas el texto completo de un boletín especifico, podes:
1. Usar el chat para buscarlo
2. O acceder directamente a: https://sibom.slyt.gba.gob.ar

---
En que puedo ayudarte hoy?`
  },
  {
    id: 'faq-004',
    question: 'Puedo buscar por fecha o numero',
    keywords: ['buscar', 'fecha', 'numero', 'filtro', 'especifico'],
    category: 'consulta',
    answer: `## Busqueda por Fecha o Numero

### Busqueda por Fecha

Si bien el sistema actualmente busca principalmente por contenido textual, podes:

1. **Mencionar la fecha** en tu consulta (ej: "ordenanzas de diciembre 2024")
2. El sistema intentara encontrar documentos cercanos a esa fecha

### Busqueda por Numero

Para buscar por numero de norma:

- **Ordenanzas:** Deci "Ordenanza 123" o "ordenanza numero 123"
- **Decretos:** Deci "Decreto 456" o "decreto ejecutivo 456"
- **Boletines:** Podes consultar el numero de boletín (ej: "boletin 105")

### Consejos de Busqueda

*Por tema:* "reglamento de transito"
*Por numero:* "ordenanza 150"
*Por fecha:* "normas de 2024"
*Por municipio:* "ordenanzas de [ciudad]"
*Combinada:* "ordenanza 150 de Carlos Tejedor"

### Mejoras Proximas
Estamos trabajando para agregar filtros mas precisos por fecha y tipo de documento.

---
Que norma estas buscando?`
  },
  {
    id: 'faq-005',
    question: 'El chatbot tiene costo',
    keywords: ['costo', 'gratis', 'gratuito', 'precio', 'pago', 'dinero'],
    category: 'general',
    answer: `## Informacion sobre Costos

### Servicio Gratuito

**Nuestro chatbot es completamente gratuito para usar.**

No cobramos por consultas ni por el acceso a la informacion de boletines oficiales.

### Sin Datos Personales

No requerimos:
- Registro de usuario
- Datos personales
- Pago de ningun tipo

### Acceso a Informacion Oficial

La informacion que proporcionamos (ordenanzas, decretos, boletines) es **informacion publica** del Estado Provincial y Municipal.

### Nota Importante

Aunque el uso del chatbot es gratuito, las respuestas son generadas por inteligencia artificial. Te recomendamos:

1. **Verificar** informacion critica en las fuentes oficiales
2. **Consultar** con profesionales para temas legales especificos
3. **Contactar** el municipio directamente para tramites oficiales

---
En que puedo ayudarte sin costo alguno?`
  },
  {
    id: 'faq-006',
    question: 'Las respuestas son confiables',
    keywords: ['confiable', 'confianza', 'exacto', 'correcto', 'verdadero', 'verificar', 'precision'],
    category: 'general',
    answer: `## Sobre la Confiabilidad de las Respuestas

### Fuentes y Origen de Datos

Nuestro chatbot extrae informacion de:

- **Boletines Oficiales** del SIBOM (Sistema de Boletines Municipales)
- **Normativas Vigentes** publicadas por los municipios
- **Documentos Originales** con texto integro de ordenanzas y decretos

### Limitaciones

Como toda herramienta de IA, es importante que tengas en cuenta:

1. **Verificacion Recomendada:** Para decisiones importantes, consulta la fuente oficial directamente
2. **Contexto Local:** Algunas normas pueden tener interpretaciones especificas segun el municipio
3. **Actualizacion:** Los boletines mas recientes pueden no estar disponibles inmediatamente

### Buenas Practicas

- **Para tramites legales:** Consultá un profesional
- **Para informacion general:** Verifica en la fuente oficial
- **Para decisiones importantes:** Contactá el municipio
- **Para interpretacion de normas:** Asesorate legalmente

### Fuentes Verificables

Todas nuestras respuestas incluyen enlaces a las fuentes oficiales para que puedas verificar la informacion.

---
Tenes alguna consulta especifica que quieras verificar?`
  },
  {
    id: 'faq-007',
    question: 'Puedo descargar los documentos',
    keywords: ['descargar', 'download', 'pdf', 'exportar', 'copia', 'guardar'],
    category: 'acceso',
    answer: `## Descarga de Documentos

### Formatos Disponibles

Nuestro chatbot proporciona **enlaces directos** a los documentos oficiales en el SIBOM.

### Como acceder?

1. Cada respuesta incluye un **enlace a la fuente oficial**
2. Podes hacer clic en el enlace para ver el documento completo
3. Desde el SIBOM podes:
   - Ver el documento en linea
   - Descargar en formato digital
   - Imprimir si lo necesitas

### Limitaciones Actualmente

Actualmente el chatbot **no descarga archivos directamente**, pero:

- Proporciona enlaces directos a boletines
- Resume el contenido relevante
- Destaca informacion importante

### Futuras Mejoras

Estamos trabajando para permitir:
- Descarga directa en PDF
- Exportacion de consultas
- Busqueda guardada

### Alternativa

Si necesitas un documento especifico:
1. Consulta en el chat para encontrarlo
2. Usa el enlace proporcionado para acceder al SIBOM
3. Descarga el documento desde la fuente oficial

---
Que documento necesitas consultar?`
  },
  {
    id: 'faq-008',
    question: 'Que tipos de normativas existen',
    keywords: ['tipos', 'normativa', 'normas', 'clases', 'categorias', 'ordenanza', 'decreto', 'resolucion'],
    category: 'normativa',
    answer: `## Tipos de Normativas Municipales

En la Provincia de Buenos Aires, los municipios dictan diferentes tipos de normas:

### 1. Ordenanzas
Son las normas de maxima jerarquia municipal. Son aprobadas por el Honorable Consejo Deliberante (Concejo) y regulan aspectos fundamentales de la vida local.
*Ejemplos:* codigo de transito, zonificacion, tasas

### 2. Decretos
Son dictados por el Departamento Ejecutivo (Intendente). Son normas de caracter operativo y administrativo que pueden reglamentar ordenanzas existentes.
*Ejemplos:* llamados a licitacion, nombramientos

### 3. Resoluciones
Son normas de menor jerarquia para asuntos internos de la administracion.
*Ejemplos:* circulares internas, procedimientos

### 4. Edictos
Son comunicados oficiales a la ciudadania, notificaciones de normas e informacion de interes publica.

### Jerarquia Normativa

Ordenanzas (maxima jerarquia local)
  +-- Decretos (aplicacion de ordenanzas)
       +-- Resoluciones (normas internas)

### Busqueda por Tipo

En el chatbot podes especificar el tipo de norma que buscas:
- "ordenanza sobre comercio"
- "decreto de pavimentacion"
- "edicto sobre tasas"

---
Te interesa algun tipo de normativa en particular?`
  }
];

/**
 * Resultado de busqueda con puntuacion
 */
interface ScoredFAQ {
  faq: CachedFAQ;
  score: number;
}

/**
 * Busca FAQs que coincidan con una consulta
 */
export function findMatchingFAQs(query: string): CachedFAQ[] {
  const queryLower = query.toLowerCase();
  const queryTerms = queryLower.split(/\s+/);
  
  const scoredFAQs: ScoredFAQ[] = cachedFAQs.map(faq => {
    let score = 0;
    
    // Coincidencia exacta en la pregunta
    if (queryLower === faq.question.toLowerCase()) {
      score += 100;
    }
    
    // Coincidencia en palabras clave
    for (const term of queryTerms) {
      if (faq.question.toLowerCase().includes(term)) {
        score += 20;
      }
      for (const keyword of faq.keywords) {
        if (keyword.includes(term) || term.includes(keyword)) {
          score += 15;
        }
      }
    }
    
    return { faq, score };
  });
  
  // Ordenar por puntuacion y filtrar solo las relevantes
  scoredFAQs.sort((a, b) => b.score - a.score);
  
  return scoredFAQs
    .filter(item => item.score > 0)
    .map(item => item.faq)
    .slice(0, 3);
}

/**
 * Verifica si una consulta es suficientemente especifica para FAQ
 */
export function isFaqQuery(query: string): boolean {
  const matching = findMatchingFAQs(query);
  return matching.length > 0;
}

/**
 * Obtiene una FAQ especifica por ID
 */
export function getFAQById(id: string): CachedFAQ | undefined {
  return cachedFAQs.find(faq => faq.id === id);
}

/**
 * Obtiene todas las FAQs por categoria
 */
export function getFAQsByCategory(category: CachedFAQ['category']): CachedFAQ[] {
  return cachedFAQs.filter(faq => faq.category === category);
}

/**
 * Lista de preguntas frecuentes para mostrar en UI
 */
export function getFaqQuestions(): string[] {
  return cachedFAQs.map(faq => faq.question);
}
