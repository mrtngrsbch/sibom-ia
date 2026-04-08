/**
 * Cliente API para comunicación con el backend sat-analysis FastAPI.
 *
 * Maneja la comunicación asíncrona con el servicio de análisis satelital.
 */

const SAT_API_URL = "/api/sat";

export function getSatAssetUrl(relativePath: string): string {
	if (/^https?:\/\//.test(relativePath)) {
		return relativePath;
	}

	return `${SAT_API_URL}${relativePath.startsWith("/") ? relativePath : `/${relativePath}`}`;
}

/**
 * Estados posibles de una tarea de análisis
 */
export type TaskStatus = "pending" | "processing" | "completed" | "failed";

/**
 * URLs de imágenes generadas para una fecha específica.
 */
export interface ImageUrls {
	clasificacion?: string;
	ndwi?: string;
	mndwi?: string;
	ndvi?: string;
	ndmi?: string;
	ndsi?: string;
	swir2_nir?: string;
	rgb?: string;
}

/**
 * Resultado de análisis de una imagen individual
 */
export interface SatelliteImageResult {
	date: string;
	water_ha: number;
	wetland_ha: number;
	vegetation_ha: number;
	other_ha: number;
	cloud_cover?: number;
	images?: ImageUrls;
}

/**
 * Resumen estadístico del análisis
 */
export interface AnalysisSummary {
	partida: string;
	total_area_ha?: number;
	date_range: string;
	images_analyzed: number;
	max_water_ha: number;
	max_wetland_ha: number;
	avg_water_ha: number;
	avg_wetland_ha: number;
	max_affected_date: string;
	max_affected_area_ha: number;
	trend_water: "up" | "down" | "stable";
	trend_wetland: "up" | "down" | "stable";
}

/**
 * Respuesta del endpoint de análisis
 */
export interface AnalyzeResponse {
	task_id: string;
	partida: string;
	status: TaskStatus;
	sensor?: "sentinel-2" | "sentinel-1" | "modis";
	progress: number;
	message: string;
	total_images: number;
	results?: SatelliteImageResult[];
	summary?: AnalysisSummary;
	error?: string;
}

/**
 * Request para iniciar análisis
 */
export interface AnalyzeRequest {
	partida: string;
	years: number;
	samples_per_year: number;
	max_clouds: number;
	sensor?: "sentinel-2" | "sentinel-1" | "modis";
}

/**
 * Información de un partido ARBA
 */
export interface PartidoInfo {
	codigo: string;
	nombre: string;
}

/**
 * Respuesta del endpoint de partidos
 */
export interface PartidosResponse {
	partidos: PartidoInfo[];
}

/**
 * Cliente API para sat-analysis
 */
export class SatAnalysisClient {
	private baseUrl: string;

	constructor(baseUrl?: string) {
		this.baseUrl = baseUrl || SAT_API_URL;
	}

	/**
	 * Health check del servicio
	 */
	async health(): Promise<{
		status: string;
		service: string;
		version: string;
	}> {
		const response = await fetch(`${this.baseUrl}/api/health`);
		if (!response.ok) {
			throw new Error(`Health check failed: ${response.statusText}`);
		}
		return response.json();
	}

	/**
	 * Obtiene la lista de partidos ARBA disponibles
	 */
	async getPartidos(): Promise<PartidosResponse> {
		const response = await fetch(`${this.baseUrl}/api/partidos`);
		if (!response.ok) {
			if (response.status === 503) {
				throw new Error("El servicio de análisis satelital no está disponible");
			}
			throw new Error(`Error cargando partidos (${response.status})`);
		}
		return response.json();
	}

	/**
	 * Inicia un análisis de parcela
	 * @returns task_id para hacer polling
	 */
	async analyze(
		request: AnalyzeRequest,
	): Promise<{ task_id: string; status: TaskStatus; message: string }> {
		const response = await fetch(`${this.baseUrl}/api/analyze`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(request),
		});

		if (!response.ok) {
			const error = await response
				.json()
				.catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || "Error al iniciar análisis");
		}

		return response.json();
	}

	/**
	 * Consulta el estado de un análisis por task_id
	 */
	async getAnalysisStatus(taskId: string): Promise<AnalyzeResponse> {
		const response = await fetch(`${this.baseUrl}/api/analyze/${taskId}`);
		if (!response.ok) {
			throw new Error(`Error fetching status: ${response.statusText}`);
		}
		return response.json();
	}

	/**
	 * Realiza polling hasta que el análisis se complete
	 * @param taskId ID de la tarea
	 * @param onUpdate Callback con progreso
	 * @param intervalMs Intervalo de polling (default: 2000ms)
	 */
	async pollAnalysis(
		taskId: string,
		onUpdate?: (response: AnalyzeResponse) => void,
		intervalMs: number = 2000,
	): Promise<AnalyzeResponse> {
		return new Promise((resolve, reject) => {
			const poll = async () => {
				try {
					const response = await this.getAnalysisStatus(taskId);
					onUpdate?.(response);

					if (response.status === "completed") {
						resolve(response);
					} else if (response.status === "failed") {
						reject(new Error(response.error || "Análisis falló"));
					} else {
						// Continuar polling
						setTimeout(poll, intervalMs);
					}
				} catch (error) {
					reject(error);
				}
			};

			poll();
		});
	}

	/**
	 * Descarga un ZIP con todas las imágenes del análisis
	 * @param taskId ID de la tarea completada
	 * @returns URL del blob para descargar
	 */
	async downloadImagesZip(taskId: string): Promise<string> {
		const response = await fetch(`${this.baseUrl}/api/analyze/${taskId}/zip`);
		if (!response.ok) {
			throw new Error(`Error descargando ZIP: ${response.statusText}`);
		}
		const blob = await response.blob();
		return URL.createObjectURL(blob);
	}

	/**
	 * Descarga un ZIP con todas las imágenes del análisis (dispara descarga directa)
	 * @param taskId ID de la tarea completada
	 * @param filename Nombre del archivo (opcional)
	 */
	async downloadImagesZipDirect(
		taskId: string,
		filename?: string,
	): Promise<void> {
		const url = await this.downloadImagesZip(taskId);
		const link = document.createElement("a");
		link.href = url;
		link.download = filename || `analisis_satelital_${taskId}.zip`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	}
}

// Instancia singleton
let clientInstance: SatAnalysisClient | null = null;

export function getSatAnalysisClient(): SatAnalysisClient {
	if (!clientInstance) {
		clientInstance = new SatAnalysisClient();
	}
	return clientInstance;
}
