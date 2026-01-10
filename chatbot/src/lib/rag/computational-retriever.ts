/**
 * computational-retriever.ts
 *
 * Integración del motor de cómputo tabular con el sistema RAG.
 * Ejecuta operaciones computacionales sobre datos tabulares y genera respuestas.
 *
 * @version 1.0.0
 * @created 2026-01-09
 * @author Kilo Code
 */

import type { StructuredTable } from '@/lib/types';
import type { SearchOptions, SearchResult } from './retriever';
import { retrieveContext } from './retriever';
import { executeComputationalQuery } from '@/lib/computation';

/**
 * Resultado extendido que incluye cómputo tabular
 */
export interface ComputationalSearchResult extends SearchResult {
  isComputational: boolean;
  computationResult?: {
    success: boolean;
    answer: string;
    markdown?: string;
    metadata?: Record<string, any>;
  };
  tablesSummary?: string;
}

/**
 * Utilidad para leer un archivo JSON (local o GitHub)
 */
async function readJSONFile(filename: string): Promise<any> {
  // Modo GitHub
  if (process.env.GITHUB_DATA_REPO) {
    const branch = process.env.GITHUB_DATA_BRANCH || 'main';
    const useGzip = process.env.GITHUB_USE_GZIP === 'true';
    const url = `https://raw.githubusercontent.com/${process.env.GITHUB_DATA_REPO}/${branch}/boletines/${filename}${useGzip ? '.gz' : ''}`;

    const response = await fetch(url, {
      cache: 'force-cache',
      next: { revalidate: 1800 }
    });

    if (!response.ok) {
      throw new Error(`GitHub responded with status ${response.status}`);
    }

    // Si es gzip, descomprimir
    const arrayBuffer = await response.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);

    if (useGzip) {
      const { gunzip } = await import('zlib');
      const { promisify } = await import('util');
      const gunzipAsync = promisify(gunzip);
      const decompressed = await gunzipAsync(uint8Array);
      const decoder = new TextDecoder('utf-8');
      return JSON.parse(decoder.decode(decompressed));
    }

    const decoder = new TextDecoder('utf-8');
    const content = decoder.decode(uint8Array);
    return JSON.parse(content);
  }

  // Modo local
  const path = await import('path');
  const fs = await import('fs/promises');

  const dataPath = process.env.DATA_PATH || path.join(process.cwd(), '..', 'python-cli');
  const filePath = path.join(dataPath, 'boletines', filename);
  const content = await fs.readFile(filePath, 'utf-8');
  return JSON.parse(content);
}

/**
 * Lee el índice de boletines
 */
async function loadIndex(): Promise<any[]> {
  // Modo GitHub
  if (process.env.GITHUB_DATA_REPO) {
    const branch = process.env.GITHUB_DATA_BRANCH || 'main';
    const useGzip = process.env.GITHUB_USE_GZIP === 'true';
    const url = `https://raw.githubusercontent.com/${process.env.GITHUB_DATA_REPO}/${branch}/boletines_index.json${useGzip ? '.gz' : ''}`;

    const response = await fetch(url, {
      cache: 'force-cache',
      next: { revalidate: 3600 }
    });

    if (!response.ok) {
      throw new Error(`GitHub responded with status ${response.status}`);
    }

    const arrayBuffer = await response.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);

    if (useGzip) {
      const { gunzip } = await import('zlib');
      const { promisify } = await import('util');
      const gunzipAsync = promisify(gunzip);
      const decompressed = await gunzipAsync(uint8Array);
      const decoder = new TextDecoder('utf-8');
      return JSON.parse(decoder.decode(decompressed));
    }

    const decoder = new TextDecoder('utf-8');
    return JSON.parse(decoder.decode(uint8Array));
  }

  // Modo local
  const path = await import('path');
  const fs = await import('fs/promises');

  const dataPath = process.env.DATA_PATH || path.join(process.cwd(), '..', 'python-cli');
  const indexPath = path.join(dataPath, 'boletines_index.json');
  const content = await fs.readFile(indexPath, 'utf-8');
  return JSON.parse(content);
}

/**
 * Recupera contexto y ejecuta cómputos tabulares si es aplicable
 *
 * @param query - Query del usuario
 * @param options - Opciones de búsqueda (municipio, tipo, fecha, etc.)
 * @returns Resultado con contexto RAG + resultado computacional
 */
export async function retrieveWithComputation(
  query: string,
  options: SearchOptions = {}
): Promise<ComputationalSearchResult> {
  // 1. Obtener contexto RAG primero
  // NOTA: retrieveContext ya carga tablas en el contexto cuando detecta queries computacionales
  const ragResult = await retrieveContext(query, options);

  // 2. Detectar si es query computacional usando la función del módulo de cómputo
  const { isComputationalQuery } = await import('@/lib/computation');
  const isComputational = isComputationalQuery(query);

  if (!isComputational) {
    return {
      ...ragResult,
      isComputational: false
    };
  }

  console.log('[CompRetriever] 🧮 Query computacional detectada, cargando tablas...');

  // 3. Cargar índice y extraer tablas de documentos relevantes
  const index = await loadIndex();
  let filteredIndex = index;

  // Aplicar filtros
  if (options.municipality) {
    const mSearch = options.municipality.toLowerCase();
    filteredIndex = filteredIndex.filter((d: any) =>
      d.municipality.toLowerCase().includes(mSearch)
    );
  }

  if (options.type) {
    const typeFilter = options.type;
    filteredIndex = filteredIndex.filter((d: any) => {
      if (d.documentTypes && Array.isArray(d.documentTypes)) {
        return d.documentTypes.includes(typeFilter);
      }
      return d.type === typeFilter;
    });
  }

  // 4. Cargar tablas de documentos
  // OPTIMIZACIÓN: Limitar a los boletines más recientes por municipio
  // para no cargar todos los boletines históricos
  const maxBoletinesPerMunicipality = 3;
  const municipalityGroups = new Map<string, any[]>();
  for (const entry of filteredIndex) {
    const muni = entry.municipality;
    if (!municipalityGroups.has(muni)) {
      municipalityGroups.set(muni, []);
    }
    const group = municipalityGroups.get(muni)!;
    if (group.length < maxBoletinesPerMunicipality) {
      group.push(entry);
    }
  }

  const allTables: StructuredTable[] = [];
  const entriesToLoad = Array.from(municipalityGroups.values()).flat();

  console.log(`[CompRetriever] Cargando ${entriesToLoad.length} boletines (máx ${maxBoletinesPerMunicipality} por municipio)`);

  for (const entry of entriesToLoad) {
    try {
      const data = await readJSONFile(entry.filename);
      if (data.tables && Array.isArray(data.tables) && data.tables.length > 0) {
        allTables.push(...data.tables);
      }
    } catch (error) {
      // Silencioso - archivos corruptos o sin tablas
    }
  }

  console.log(`[CompRetriever] 📊 ${allTables.length} tablas cargadas`);

  if (allTables.length === 0) {
    return {
      ...ragResult,
      isComputational: true,
      computationResult: {
        success: false,
        answer: 'No se encontraron datos tabulares estructurados para realizar cómputos.'
      }
    };
  }

  // 5. Ejecutar query computacional
  const computationResult = executeComputationalQuery(query, allTables);

  // 6. Generar resumen de tablas
  const tablesSummary = generateTablesSummary(allTables);

  return {
    ...ragResult,
    isComputational: true,
    computationResult: {
      success: computationResult.success,
      answer: computationResult.answer,
      markdown: computationResult.markdown,
      metadata: computationResult.metadata
    },
    tablesSummary
  };
}

/**
 * Genera un resumen de las tablas disponibles
 */
function generateTablesSummary(tables: StructuredTable[]): string {
  if (tables.length === 0) return '';

  const lines: string[] = ['## 📊 Tablas Disponibles para Cómputo', ''];

  // Agrupar por título (evitar duplicados)
  const uniqueTables = new Map<string, StructuredTable>();
  for (const table of tables) {
    if (!uniqueTables.has(table.title)) {
      uniqueTables.set(table.title, table);
    }
  }

  for (const [title, table] of uniqueTables) {
    lines.push(`### ${title}`);
    if (table.description) {
      lines.push(`*${table.description}*`);
    }
    lines.push(`- **Filas:** ${table.stats.row_count}`);
    lines.push(`- **Columnas:** ${table.schema.columns.join(', ')}`);

    // Columnas numéricas con estadísticas
    const numericCols = Object.keys(table.stats.numeric_stats);
    if (numericCols.length > 0) {
      lines.push('- **Columnas numéricas:**');
      for (const col of numericCols) {
        const stats = table.stats.numeric_stats[col];
        lines.push(`  - **${col}:** suma=${formatArgentineNumber(stats.sum)}, ` +
                   `máx=${formatArgentineNumber(stats.max)}, ` +
                   `mín=${formatArgentineNumber(stats.min)}`);
      }
    }
    lines.push('');
  }

  return lines.join('\n');
}

/**
 * Formatea un número al formato argentino
 */
function formatArgentineNumber(num: number): string {
  const parts = num.toFixed(2).split('.');
  const integerPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  const decimalPart = parts[1];

  if (decimalPart === '00') return integerPart;
  return `${integerPart},${decimalPart}`;
}

/**
 * Construye el prompt del sistema con instrucciones de cómputo
 */
export function buildComputationalSystemPrompt(
  basePrompt: string,
  computationResult?: ComputationalSearchResult['computationResult']
): string {
  if (!computationResult || !computationResult.success) {
    return basePrompt;
  }

  const computationInstructions = `

## 🔢 DATOS COMPUTACIONLES

Se han ejecutado operaciones sobre datos tabulares estructurados.

**RESULTADO DEL CÓMPUTO:**
${computationResult.answer}

${computationResult.markdown ? `**TABLA DE RESULTADOS:**\n${computationResult.markdown}\n` : ''}

**IMPORTANTE:**
- Usa estos resultados computados para responder la pregunta del usuario.
- Los valores ya están calculados - NO intentes recalcularlos ni estimarlos.
- Si el usuario pide una comparación, usa los datos proporcionados directamente.
- Cita la fuente original de los datos (boletín municipal).
`;

  return basePrompt + computationInstructions;
}
