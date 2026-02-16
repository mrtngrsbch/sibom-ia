/**
 * Integration de Balance Retriever con Qdrant
 *
 * Detecta queries sobre balances y utiliza Qdrant Cloud para retrieval.
 * Mantiene compatibilidad con sistema RAG SQL existente para otras queries.
 *
 * @author Sistema de RAG Híbrido (Qdrant + SQLite)
 */

import {
	retrieveFromQdrant,
	retrieveBalanceTotals,
	formatChunksForLLM,
	extractNumbers,
	type RetrievedChunk,
} from "./qdrant-retriever";

/**
 * Detecta si una query es sobre balances de tesorería.
 */
export function isBalanceQuery(query: string): boolean {
	const keywords = [
		"balance",
		"tesorería",
		"recursos",
		"gastos",
		"gastos",
		"saldo",
		"disponibilidad",
		"ingresos",
		"egresos",
		"presupuesto",
		"total",
		"números",
		"montos",
		"dinero",
	];

	const lowerQuery = query.toLowerCase();
	const matchedKeywords = keywords.filter((kw) => lowerQuery.includes(kw));

	// Si coincide con 2+ keywords, es balance query
	return (
		matchedKeywords.length >= 2 ||
		(matchedKeywords.length === 1 && lowerQuery.includes("tesor"))
	);
}

/**
 * Verifica si el balance retriever puede usarse (Qdrant + OpenAI configurados).
 */
export function isBalanceRetrieverAvailable(): boolean {
	return Boolean(
		process.env.QDRANT_URL &&
		process.env.QDRANT_API_KEY &&
		process.env.OPENAI_API_KEY,
	);
}

/**
 * Extrae nombre del municipio de una query sobre balance.
 * Ejemplo: "¿Qué balance tiene Carlos Tejedor?" → "Carlos Tejedor"
 */
export function extractMunicipalityFromQuery(
	query: string,
): string | undefined {
	// Municipios conocidos (expandir según necesidad)
	const municipalities = ["Carlos Tejedor", "Azul", "Balcarce", "Bragado"];

	for (const mun of municipalities) {
		if (query.toLowerCase().includes(mun.toLowerCase())) {
			return mun;
		}
	}

	// Intentar extraer nombre propio después de "de", "en", "para"
	const patterns = [
		/(?:de|en|para|municipio|ciudad)\s+([A-Z][a-záé]+(?:\s+[A-Z][a-záé]+)?)/,
	];

	for (const pattern of patterns) {
		const match = query.match(pattern);
		if (match) {
			return match[1];
		}
	}

	return undefined;
}

/**
 * Extrae período de una query (e.g., "2024-T1", "primer trimestre 2024").
 */
export function extractPeriodFromQuery(query: string): string | undefined {
	// Patrones de período
	const yearPattern = /\d{4}/;
	const trimesterPattern = /[tT]([1-4])/;

	const yearMatch = query.match(yearPattern);
	const trimesterMatch = query.match(trimesterPattern);

	if (yearMatch && trimesterMatch) {
		return `${yearMatch[0]}-T${trimesterMatch[1]}`;
	}

	return undefined;
}

/**
 * Recupera contexto de balance usando Qdrant.
 * Interfaz compatible con el sistema RAG existente.
 */
export async function retrieveBalanceContext(
	query: string,
	municipio?: string,
	periodo?: string,
): Promise<{
	context: string;
	sources: Array<{ title: string; file: string; relevance: number }>;
}> {
	try {
		const chunks = municipio
			? await retrieveBalanceTotals(municipio, periodo)
			: await retrieveFromQdrant(query, { periodo }, 10);

		if (chunks.length === 0) {
			return {
				context: "No se encontraron balances de tesorería en la base de datos.",
				sources: [],
			};
		}

		// Formatear para LLM
		const context = formatChunksForLLM(chunks);

		// Extraer números para validación anti-alucinación
		const numbers = extractNumbers(chunks);

		// Construir fuentes
		const sources = chunks.map((chunk: RetrievedChunk) => ({
			title: `${chunk.metadata.municipio} - ${chunk.metadata.periodo}`,
			file: `balances/${chunk.metadata.municipio}`,
			relevance: Math.round((chunk.score || 0) * 100),
		}));

		// Log de extracción de números (para debugging)
		if (numbers.size > 0) {
			console.log(
				`[BalanceRetriever] Números detectados: ${Array.from(numbers).join(", ")}`,
			);
		}

		return {
			context,
			sources,
		};
	} catch (error) {
		console.error("[BalanceRetriever] Error:", error);
		return {
			context: "Error al recuperar información de balances.",
			sources: [],
		};
	}
}

/**
 * Prompt especializado para prevenir alucinaciones financieras.
 */
export const BALANCE_ANTI_HALLUCINATION_SYSTEM_PROMPT = `Eres un asistente especializado en información municipal de balances de tesorería.

REGLAS CRÍTICAS:
1. **DATOS VERIFICABLES**: Solo responde con números que están explícitamente en los documentos proporcionados.
2. **NO INVENTAR NÚMEROS**: Si no encuentras un número específico, dilo claramente: "No tengo el dato de...".
3. **CITAR FUENTES**: Siempre indica de qué documento y período proviene cada número.
4. **CLARIDAD DE PERÍODOS**: Especifica claramente: "En el período 2024-T1 (primer trimestre de 2024)...".
5. **EXACTITUD FINANCIERA**: Los números en balances son críticos. Mejor no responder que dar un número incorrecto.

FORMATO DE RESPUESTA:
- Total de Recursos: $X.XXX.XXX,XX (Período: Año-TN, Municipio: XXXX)
- Total de Gastos: $X.XXX.XXX,XX
- Saldo Final: $X.XXX.XXX,XX
- Fuente: [Nombre del documento oficial]

PROHIBIDO:
❌ Hacer cálculos aproximados si no estás seguro
❌ Asumir valores que no están en los documentos
❌ Redondear números sin indicarlo
❌ Confundir períodos o municipios`;

/**
 * Inyecta el prompt anti-alucinación en mensajes del sistema.
 */
export function buildBalanceSystemMessage(): {
	role: "system";
	content: string;
} {
	return {
		role: "system",
		content: BALANCE_ANTI_HALLUCINATION_SYSTEM_PROMPT,
	};
}
