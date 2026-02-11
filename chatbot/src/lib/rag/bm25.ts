/**
 * bm25.ts
 *
 * Implementación de BM25 (Best Matching 25) para ranking de documentos.
 * Optimizado para español y terminología legal municipal.
 *
 * @author Kilo Code
 * @created 2026-01-04
 */

/**
 * Diccionario de sinónimos para términos legales comunes
 */
const SYNONYMS: Record<string, string[]> = {
  // Términos laborales
  'sueldo': ['salario', 'remuneracion', 'haber', 'retribucion', 'paga'],
  'salario': ['sueldo', 'remuneracion', 'haber', 'retribucion'],
  'remuneracion': ['sueldo', 'salario', 'haber', 'retribucion'],
  
  // Términos de tránsito
  'transito': ['vial', 'circulacion', 'trafico'],
  'vial': ['transito', 'circulacion'],
  
  // Términos fiscales
  'impuesto': ['tasa', 'tributo', 'gravamen', 'canon'],
  'tasa': ['impuesto', 'tributo', 'canon'],
  'tributo': ['impuesto', 'tasa', 'gravamen'],
  
  // Términos de habilitación
  'habilitacion': ['permiso', 'licencia', 'autorizacion'],
  'permiso': ['habilitacion', 'licencia', 'autorizacion'],
  'licencia': ['habilitacion', 'permiso', 'autorizacion'],
};

/**
 * Expande un término con sus sinónimos
 */
function expandWithSynonyms(term: string): string[] {
  const normalized = term.toLowerCase();
  const synonyms = SYNONYMS[normalized] || [];
  return [normalized, ...synonyms];
}

/**
 * Tokeniza texto en español, eliminando stopwords y normalizando
 * Ahora con expansión de sinónimos para mejorar recall
 */
export function tokenize(text: string, expandSynonyms: boolean = false): string[] {
  // Stopwords comunes en español (mínimo para mantener contexto legal)
  const stopwords = new Set([
    'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'ser', 'se', 'no', 'haber',
    'por', 'con', 'su', 'para', 'como', 'estar', 'tener', 'le', 'lo', 'todo',
    'pero', 'más', 'hacer', 'o', 'poder', 'decir', 'este', 'ir', 'otro', 'ese',
    'la', 'si', 'me', 'ya', 'ver', 'porque', 'dar', 'cuando', 'él', 'muy',
    'sin', 'vez', 'mucho', 'saber', 'qué', 'sobre', 'mi', 'alguno', 'mismo',
    'yo', 'también', 'hasta', 'año', 'dos', 'querer', 'entre', 'así', 'primero',
    'desde', 'grande', 'eso', 'ni', 'nos', 'llegar', 'pasar', 'tiempo', 'ella',
    'sí', 'día', 'uno', 'bien', 'poco', 'deber', 'entonces', 'poner', 'cosa',
    'tanto', 'hombre', 'parecer', 'nuestro', 'tan', 'donde', 'ahora', 'parte',
    'después', 'vida', 'quedar', 'siempre', 'creer', 'hablar', 'llevar', 'dejar'
  ]);

  const tokens = text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // Eliminar acentos para normalización
    .replace(/[^\w\s]/g, ' ') // Eliminar puntuación
    .split(/\s+/)
    .filter(token => token.length > 2 && !stopwords.has(token));

  // Si se solicita expansión de sinónimos (solo para queries)
  if (expandSynonyms) {
    const expanded = new Set<string>();
    for (const token of tokens) {
      const synonyms = expandWithSynonyms(token);
      synonyms.forEach(syn => expanded.add(syn));
    }
    return Array.from(expanded);
  }

  return tokens;
}

/**
 * Calcula IDF (Inverse Document Frequency) para cada término
 */
export function calculateIDF(documents: string[][]): Map<string, number> {
  const N = documents.length;
  const df = new Map<string, number>(); // Document frequency

  // Contar en cuántos documentos aparece cada término
  for (const doc of documents) {
    const uniqueTerms = new Set(doc);
    for (const term of uniqueTerms) {
      df.set(term, (df.get(term) || 0) + 1);
    }
  }

  // Calcular IDF para cada término
  const idf = new Map<string, number>();
  for (const [term, docFreq] of df.entries()) {
    // IDF = log((N - df + 0.5) / (df + 0.5) + 1)
    // Fórmula BM25 estándar con smoothing
    idf.set(term, Math.log((N - docFreq + 0.5) / (docFreq + 0.5) + 1));
  }

  return idf;
}

/**
 * Calcula la longitud promedio de documentos
 */
export function calculateAvgDocLength(documents: string[][]): number {
  const totalLength = documents.reduce((sum, doc) => sum + doc.length, 0);
  return totalLength / documents.length;
}

/**
 * Índice BM25 precargado en memoria
 */
export class BM25Index {
  private documents: string[][];
  private idf: Map<string, number>;
  private avgDocLength: number;
  private k1: number; // Parámetro de saturación de término (típicamente 1.2-2.0)
  private b: number;  // Parámetro de normalización de longitud (típicamente 0.75)

  constructor(
    documents: string[][],
    k1: number = 1.5,  // Optimizado para documentos legales (más conservador)
    b: number = 0.75   // Normalización estándar
  ) {
    this.documents = documents;
    this.k1 = k1;
    this.b = b;
    this.idf = calculateIDF(documents);
    this.avgDocLength = calculateAvgDocLength(documents);
  }

  /**
   * Calcula score BM25 para un documento dado una query
   */
  public score(queryTokens: string[], docIndex: number): number {
    const doc = this.documents[docIndex];
    const docLength = doc.length;

    // Calcular frecuencia de términos en el documento
    const termFreq = new Map<string, number>();
    for (const term of doc) {
      termFreq.set(term, (termFreq.get(term) || 0) + 1);
    }

    let score = 0;

    for (const queryTerm of queryTokens) {
      const tf = termFreq.get(queryTerm) || 0;
      const idf = this.idf.get(queryTerm) || 0;

      if (tf === 0) continue;

      // BM25 formula
      // score += IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (docLength / avgDocLength)))
      const numerator = tf * (this.k1 + 1);
      const denominator = tf + this.k1 * (1 - this.b + this.b * (docLength / this.avgDocLength));

      score += idf * (numerator / denominator);
    }

    return score;
  }

  /**
   * Busca y rankea documentos por relevancia
   * Ahora con expansión de sinónimos para mejorar recall
   */
  public search(query: string, topK: number = 10): Array<{ index: number; score: number }> {
    // ✅ EXPANDIR QUERY CON SINÓNIMOS
    const queryTokens = tokenize(query, true); // true = expandir sinónimos

    if (queryTokens.length === 0) {
      return [];
    }

    const scores: Array<{ index: number; score: number }> = [];

    for (let i = 0; i < this.documents.length; i++) {
      const score = this.score(queryTokens, i);
      if (score > 0) {
        scores.push({ index: i, score });
      }
    }

    // Ordenar por score descendente
    scores.sort((a, b) => b.score - a.score);

    return scores.slice(0, topK);
  }

  /**
   * Explica el score de un documento (útil para debugging)
   */
  public explainScore(query: string, docIndex: number): {
    totalScore: number;
    termScores: Array<{ term: string; tf: number; idf: number; contribution: number }>;
  } {
    const queryTokens = tokenize(query);
    const doc = this.documents[docIndex];
    const docLength = doc.length;

    const termFreq = new Map<string, number>();
    for (const term of doc) {
      termFreq.set(term, (termFreq.get(term) || 0) + 1);
    }

    const termScores: Array<{ term: string; tf: number; idf: number; contribution: number }> = [];
    let totalScore = 0;

    for (const queryTerm of queryTokens) {
      const tf = termFreq.get(queryTerm) || 0;
      const idf = this.idf.get(queryTerm) || 0;

      if (tf === 0) {
        termScores.push({ term: queryTerm, tf: 0, idf, contribution: 0 });
        continue;
      }

      const numerator = tf * (this.k1 + 1);
      const denominator = tf + this.k1 * (1 - this.b + this.b * (docLength / this.avgDocLength));
      const contribution = idf * (numerator / denominator);

      termScores.push({ term: queryTerm, tf, idf, contribution });
      totalScore += contribution;
    }

    return { totalScore, termScores };
  }
}
