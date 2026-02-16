/**
 * Qdrant Vector Search Retriever
 *
 * Búsqueda híbrida en Qdrant Cloud:
 * 1. Query + Vector search usando OpenAI embeddings
 * 2. Filtrado por municipio, periodo, tipo
 * 3. Ranking: Executive summaries primero
 * 4. Retorno: Top chunks con metadata para trazabilidad
 */

import { QdrantClient } from "@qdrant/js-client-rest";
import { OpenAI } from "openai";

export interface RetrievalFilters {
	municipio?: string;
	tipo_documento?: string;
	periodo?: string;
	is_executive_summary?: boolean;
}

export interface RetrievedChunk {
	id: string;
	content: string;
	metadata: {
		municipio: string;
		tipo_documento: string;
		tipo_detalle: string;
		periodo: string;
		is_executive_summary: boolean;
		contains_key_numbers: boolean;
		source: string;
	};
	score: number;
}

let qdrantClientInstance: QdrantClient | null = null;
let openaiInstance: OpenAI | null = null;

function getQdrantClient(): QdrantClient {
	if (!qdrantClientInstance) {
		const url = process.env.QDRANT_URL;
		const apiKey = process.env.QDRANT_API_KEY;

		if (!url || !apiKey) {
			throw new Error("Faltan QDRANT_URL o QDRANT_API_KEY");
		}

		qdrantClientInstance = new QdrantClient({ url, apiKey });
	}
	return qdrantClientInstance;
}

function getOpenAIClient(): OpenAI {
	if (!openaiInstance) {
		const apiKey = process.env.OPENAI_API_KEY;
		if (!apiKey) {
			throw new Error("Falta OPENAI_API_KEY");
		}
		openaiInstance = new OpenAI({ apiKey });
	}
	return openaiInstance;
}

/**
 * Realiza búsqueda vectorial híbrida en Qdrant.
 */
export async function retrieveFromQdrant(
	query: string,
	filters?: RetrievalFilters,
	maxResults: number = 10,
): Promise<RetrievedChunk[]> {
	try {
		const openai = getOpenAIClient();

		// 1. Generar embedding de la query
		const embeddingResponse = await openai.embeddings.create({
			input: query,
			model: "text-embedding-3-small",
		});

		const queryVector = embeddingResponse.data[0].embedding;
		console.log(
			`[Retriever] Query embedding generado (${queryVector.length} dims)`,
		);

		// 2. Construir filtros
		const qdrantFilters = buildQdrantFilters(filters);

		// 3. Búsqueda en Qdrant
		const qdrant = getQdrantClient();
		const searchResults = await qdrant.search("normativas", {
			vector: queryVector,
			limit: maxResults * 2,
			filter: qdrantFilters,
			with_payload: true,
			with_vector: false,
		});

		console.log(
			`[Retriever] Búsqueda Qdrant: ${searchResults.length} resultados`,
		);

		// 4. Convertir a formato estándar
		const chunks: RetrievedChunk[] = searchResults.map((result) => {
			const payload = (result.payload || {}) as Record<string, unknown>;
			return {
				id: String(result.id),
				content: String(payload.content || ""),
				metadata: {
					municipio: String(payload.municipio || "Unknown"),
					tipo_documento: String(payload.tipo_documento || ""),
					tipo_detalle: String(payload.tipo_detalle || ""),
					periodo: String(payload.periodo || ""),
					is_executive_summary: Boolean(payload.is_executive_summary),
					contains_key_numbers: Boolean(payload.contains_key_numbers),
					source: String(payload.source || ""),
				},
				score: (result.score || 0) as number,
			};
		});

		// 5. Ranking: Executive summaries con números primero
		const ranked = rankChunks(chunks);

		// 6. Retornar top maxResults
		return ranked.slice(0, maxResults);
	} catch (error) {
		console.error("[Retriever] Error en búsqueda:", error);
		throw error;
	}
}

/**
 * Búsqueda especializada para totales financieros.
 */
export async function retrieveBalanceTotals(
	municipio: string,
	periodo?: string,
): Promise<RetrievedChunk[]> {
	const query =
		"totales de balance de tesorería recursos gastos saldo disponibilidades";

	const filters: RetrievalFilters = {
		municipio,
		tipo_documento: "balances",
		is_executive_summary: true,
		periodo,
	};

	try {
		const results = await retrieveFromQdrant(query, filters, 5);

		if (results.length === 0) {
			console.warn(
				`[Retriever] No se encontraron totales para ${municipio} ${periodo || ""}`,
			);
		}

		return results;
	} catch (error) {
		console.error("[Retriever] Error al recuperar totales:", error);
		return [];
	}
}

/**
 * Construye filtro Qdrant para payload filtration.
 */
function buildQdrantFilters(
	filters?: RetrievalFilters,
): Record<string, (Record<string, unknown> | Record<string, string>)[]> {
	const must: Record<string, unknown>[] = [
		{
			key: "source",
			match: { value: "balance_migration_v1" },
		},
	];

	if (filters?.municipio) {
		must.push({
			key: "municipio",
			match: { value: filters.municipio },
		});
	}

	if (filters?.tipo_documento) {
		must.push({
			key: "tipo_documento",
			match: { value: filters.tipo_documento },
		});
	}

	if (filters?.periodo) {
		must.push({
			key: "periodo",
			match: { value: filters.periodo },
		});
	}

	if (filters?.is_executive_summary === true) {
		must.push({
			key: "is_executive_summary",
			match: { value: "true" },
		});
	}

	return { must };
}

/**
 * Ranking: Executive summaries con números primero.
 */
function rankChunks(chunks: RetrievedChunk[]): RetrievedChunk[] {
	return chunks.sort((a, b) => {
		// Prioridad 1: Executive summaries con números
		const aHasTotals =
			a.metadata.is_executive_summary && a.metadata.contains_key_numbers;
		const bHasTotals =
			b.metadata.is_executive_summary && b.metadata.contains_key_numbers;

		if (aHasTotals && !bHasTotals) return -1;
		if (!aHasTotals && bHasTotals) return 1;

		// Prioridad 2: Por score
		return (b.score || 0) - (a.score || 0);
	});
}

/**
 * Formatea chunks para contexto LLM con trazabilidad.
 */
export function formatChunksForLLM(chunks: RetrievedChunk[]): string {
	if (chunks.length === 0) {
		return "No se encontraron documentos relevantes en la base de datos.";
	}

	const formatted = chunks
		.map((chunk, idx) => {
			const badge = chunk.metadata.is_executive_summary
				? "📊 RESUMEN"
				: "📄 DETALLE";
			const relevance = Math.round((chunk.score || 0) * 100);

			return `[Fuente ${idx + 1}] ${badge}
Municipio: ${chunk.metadata.municipio}
Período: ${chunk.metadata.periodo}
Tipo: ${chunk.metadata.tipo_detalle}
Relevancia: ${relevance}%
─────────
${chunk.content.substring(0, 800)}${chunk.content.length > 800 ? "..." : ""}
─────────`;
		})
		.join("\n\n");

	return formatted;
}

/**
 * Extrae números para validación (anti-alucinación).
 */
export function extractNumbers(chunks: RetrievedChunk[]): Set<string> {
	const numbers = new Set<string>();
	const pattern = /\$?\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d{1,2}\/\d{1,2}\/\d{4}/g;

	chunks.forEach((chunk) => {
		const matches = chunk.content.match(pattern);
		if (matches) {
			for (const num of matches) {
				numbers.add(num);
			}
		}
	});

	return numbers;
}
