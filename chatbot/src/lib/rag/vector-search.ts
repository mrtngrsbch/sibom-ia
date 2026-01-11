/**
 * vector-search.ts
 *
 * Vector search using OpenAI embeddings + Qdrant vector database.
 * Provides semantic search capabilities for finding normativas by meaning,
 * not just keywords (solves synonym problem: "sueldo" → "remuneración").
 *
 * @version 1.0.0
 * @created 2026-01-10
 * @author Kiro AI (MIT Engineering Standards)
 *
 * @dependencies
 *   - openai: ^4.0.0
 *   - @qdrant/js-client-rest: ^1.0.0
 */

import { QdrantClient } from '@qdrant/js-client-rest';
import OpenAI from 'openai';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface VectorSearchResult {
  id: string;
  score: number;
  municipality: string;
  type: string;
  number: string;
  year: string;
  title: string;
  url: string;
  source_bulletin: string;
}

export interface VectorSearchOptions {
  municipality?: string;
  type?: string;
  year?: number;
  limit?: number;
}

// ============================================================================
// CLIENT INITIALIZATION
// ============================================================================

let qdrantClient: QdrantClient | null = null;
let openaiClient: OpenAI | null = null;

/**
 * Initializes Qdrant client (lazy initialization)
 */
function getQdrantClient(): QdrantClient {
  if (!qdrantClient) {
    const url = process.env.QDRANT_URL;
    const apiKey = process.env.QDRANT_API_KEY;

    if (!url || !apiKey) {
      throw new Error('QDRANT_URL and QDRANT_API_KEY must be set in environment variables');
    }

    qdrantClient = new QdrantClient({
      url,
      apiKey,
    });

    console.log('[VectorSearch] Qdrant client initialized');
  }

  return qdrantClient;
}

/**
 * Initializes OpenAI client (lazy initialization)
 */
function getOpenAIClient(): OpenAI {
  if (!openaiClient) {
    const apiKey = process.env.OPENAI_API_KEY;

    if (!apiKey) {
      throw new Error('OPENAI_API_KEY must be set in environment variables');
    }

    openaiClient = new OpenAI({
      apiKey,
    });

    console.log('[VectorSearch] OpenAI client initialized');
  }

  return openaiClient;
}

// ============================================================================
// VECTOR SEARCH
// ============================================================================

/**
 * Performs semantic vector search using OpenAI embeddings + Qdrant
 *
 * @param query - User query (e.g., "sueldos de carlos tejedor")
 * @param options - Search filters and limit
 * @returns Array of matching normativas with similarity scores
 *
 * @example
 * const results = await vectorSearch("sueldos municipales", {
 *   municipality: "Carlos Tejedor",
 *   year: 2025,
 *   limit: 10
 * });
 */
export async function vectorSearch(
  query: string,
  options: VectorSearchOptions = {}
): Promise<VectorSearchResult[]> {
  const startTime = Date.now();

  try {
    // 1. Generate query embedding
    console.log(`[VectorSearch] Generating embedding for query: "${query.slice(0, 50)}..."`);
    
    const openai = getOpenAIClient();
    const embeddingResponse = await openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: query,
      encoding_format: 'float',
    });

    const queryVector = embeddingResponse.data[0].embedding;
    console.log(`[VectorSearch] Embedding generated (${queryVector.length} dimensions)`);

    // 2. Build Qdrant filter
    const filter: any = { must: [] };

    if (options.municipality) {
      filter.must.push({
        key: 'municipality',
        match: { value: options.municipality }
      });
    }

    if (options.type) {
      filter.must.push({
        key: 'type',
        match: { value: options.type }
      });
    }

    if (options.year) {
      filter.must.push({
        key: 'year',
        match: { value: options.year.toString() }
      });
    }

    // 3. Search in Qdrant
    const qdrant = getQdrantClient();
    const limit = options.limit || 10;

    console.log(`[VectorSearch] Searching in Qdrant (limit: ${limit}, filters: ${JSON.stringify(options)})`);

    const searchResult = await qdrant.search('normativas', {
      vector: queryVector,
      filter: filter.must.length > 0 ? filter : undefined,
      limit,
      with_payload: true,
      score_threshold: 0.5, // Only return results with >50% similarity
    });

    // 4. Format results
    const results: VectorSearchResult[] = searchResult.map(point => ({
      id: point.id as string,
      score: point.score,
      municipality: point.payload?.municipality as string,
      type: point.payload?.type as string,
      number: point.payload?.number as string,
      year: point.payload?.year as string,
      title: point.payload?.title as string,
      url: point.payload?.url as string,
      source_bulletin: point.payload?.source_bulletin as string,
    }));

    const duration = Date.now() - startTime;
    console.log(`[VectorSearch] Found ${results.length} results in ${duration}ms`);
    console.log(`[VectorSearch] Top 3 scores:`, results.slice(0, 3).map(r => ({
      title: r.title.slice(0, 50),
      score: r.score.toFixed(3)
    })));

    return results;

  } catch (error) {
    console.error('[VectorSearch] Error:', error);
    throw error;
  }
}

/**
 * Checks if vector search is available (Qdrant configured)
 */
export function isVectorSearchAvailable(): boolean {
  return !!(process.env.QDRANT_URL && process.env.QDRANT_API_KEY && process.env.OPENAI_API_KEY);
}

/**
 * Gets vector search statistics
 */
export async function getVectorSearchStats() {
  try {
    const qdrant = getQdrantClient();
    const collectionInfo = await qdrant.getCollection('normativas');

    return {
      available: true,
      // Use indexed_vectors_count or fallback to points_count
      vectorCount: (collectionInfo as any).indexed_vectors_count || collectionInfo.points_count || 0,
      pointsCount: collectionInfo.points_count || 0,
      status: collectionInfo.status,
    };
  } catch (error) {
    console.error('[VectorSearch] Error getting stats:', error);
    return {
      available: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
