"use client";

import { useEffect, useState } from "react";
import { Satellite, AlertCircle } from "@/lib/icons";
import { PartidaForm } from "@/components/satelite/PartidaForm";
import { ResultsPanel } from "@/components/satelite/ResultsPanel";
import {
	getSatAnalysisClient,
	type PartidoInfo,
	type AnalyzeRequest,
	type AnalyzeResponse,
} from "@/lib/sat-api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const SESSION_KEY_ANALYSIS = "sat_analysis_last";
const SESSION_KEY_TASK = "sat_analysis_taskId";

function loadPersistedAnalysis(): {
	analysis: AnalyzeResponse | null;
	taskId: string | null;
} {
	if (typeof window === "undefined") return { analysis: null, taskId: null };
	try {
		const raw = sessionStorage.getItem(SESSION_KEY_ANALYSIS);
		const taskId = sessionStorage.getItem(SESSION_KEY_TASK);
		return {
			analysis: raw ? (JSON.parse(raw) as AnalyzeResponse) : null,
			taskId: taskId ?? null,
		};
	} catch {
		return { analysis: null, taskId: null };
	}
}

/**
 * Página principal de análisis satelital
 */
export default function SatelitePage() {
	const [partidos, setPartidos] = useState<PartidoInfo[]>([]);
	const [loadingPartidos, setLoadingPartidos] = useState(true);
	const [partidosError, setPartidosError] = useState<string | null>(null);

	const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
	const [loading, setLoading] = useState(false);
	const [taskId, setTaskId] = useState<string | null>(null);

	const client = getSatAnalysisClient();

	// Restaurar último análisis al montar
	useEffect(() => {
		const { analysis: saved, taskId: savedTask } = loadPersistedAnalysis();
		if (saved) {
			setAnalysis(saved);
			// Si estaba en progreso al salir, reanudar polling
			if (
				savedTask &&
				saved.status !== "completed" &&
				saved.status !== "failed"
			) {
				setTaskId(savedTask);
				setLoading(true);
			}
		}
	}, []);

	const fetchPartidos = async () => {
		try {
			setLoadingPartidos(true);
			setPartidosError(null);
			const data = await client.getPartidos();
			setPartidos(data.partidos);
		} catch (error) {
			const msg =
				error instanceof Error
					? error.message
					: "No se pudo cargar la lista de partidos";
			setPartidosError(msg);
		} finally {
			setLoadingPartidos(false);
		}
	};

	// Cargar partidos al montar
	useEffect(() => {
		fetchPartidos();
	}, []);

	// Persistir análisis cuando cambia
	useEffect(() => {
		if (typeof window === "undefined") return;
		if (analysis) {
			try {
				sessionStorage.setItem(SESSION_KEY_ANALYSIS, JSON.stringify(analysis));
			} catch {
				// sessionStorage lleno o no disponible — ignorar silenciosamente
			}
		} else {
			sessionStorage.removeItem(SESSION_KEY_ANALYSIS);
		}
	}, [analysis]);

	// Persistir taskId cuando cambia
	useEffect(() => {
		if (typeof window === "undefined") return;
		if (taskId) {
			sessionStorage.setItem(SESSION_KEY_TASK, taskId);
		} else {
			sessionStorage.removeItem(SESSION_KEY_TASK);
		}
	}, [taskId]);

	// Polling para actualizar estado del análisis
	useEffect(() => {
		if (!taskId) return;

		const pollInterval = setInterval(async () => {
			try {
				const response = await client.getAnalysisStatus(taskId);
				setAnalysis(response);

				if (response.status === "completed" || response.status === "failed") {
					clearInterval(pollInterval);
					setLoading(false);
				}
			} catch (error) {
				console.error("Error en polling:", error);
				clearInterval(pollInterval);
				setLoading(false);
			}
		}, 2000);

		return () => clearInterval(pollInterval);
	}, [taskId]);

	const handleAnalyze = async (request: AnalyzeRequest) => {
		try {
			setLoading(true);
			setAnalysis(null);

			const response = await client.analyze(request);
			setTaskId(response.task_id);

			// Inicializar estado de análisis
			setAnalysis({
				task_id: response.task_id,
				partida: request.partida,
				status: response.status,
				progress: 0,
				message: "Análisis iniciado",
				total_images: 0,
			});
		} catch (error) {
			console.error("Error iniciando análisis:", error);
			setAnalysis({
				task_id: "",
				partida: request.partida,
				status: "failed",
				progress: 0,
				message: "Error al iniciar análisis",
				total_images: 0,
				error: error instanceof Error ? error.message : "Error desconocido",
			});
			setLoading(false);
		}
	};

	const handleReset = () => {
		setAnalysis(null);
		setTaskId(null);
	};

	return (
		<div className="container mx-auto p-6 max-w-6xl">
			{/* Header */}
			<div className="mb-8">
				<div className="flex items-center gap-3 mb-2">
					<div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
						<Satellite className="w-6 h-6 text-white" />
					</div>
					<div>
						<h1 className="text-3xl font-bold text-slate-900 dark:text-white">
							Análisis Satelital
						</h1>
						<p className="text-slate-600 dark:text-slate-400">
							Detección de anegamiento y salinización usando Sentinel-2,
							Sentinel-1 SAR y MODIS
						</p>
					</div>
				</div>

				{/* Resumen de capas */}
				<div className="mt-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-4">
					<p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400 mb-3">
						16 capas de análisis disponibles
					</p>
					<div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
						{/* Sentinel-2 */}
						<div className="space-y-1.5">
							<p className="font-semibold text-blue-700 dark:text-blue-400">
								🛰 Sentinel-2 — 8 capas
							</p>
							<ul className="space-y-0.5 text-slate-600 dark:text-slate-400">
								<li>RGB · Color real</li>
								<li>Clasificación · 4 categorías de uso de suelo</li>
								<li>NDWI · Índice de agua</li>
								<li>MNDWI · NDWI modificado (agua turbia)</li>
								<li>NDVI · Índice de vegetación</li>
								<li>NDMI · Índice de humedad</li>
								<li>NDSI · Índice de nieve/sal</li>
								<li>Salinidad · Ratio SWIR2 + NIR</li>
							</ul>
						</div>

						{/* Sentinel-1 */}
						<div className="space-y-1.5">
							<p className="font-semibold text-emerald-700 dark:text-emerald-400">
								📡 Sentinel-1 SAR — 4 capas
							</p>
							<ul className="space-y-0.5 text-slate-600 dark:text-slate-400">
								<li>SAR VV · Backscatter vertical</li>
								<li>SAR VH · Backscatter cruzado</li>
								<li>SAR RGB · Composición VV/VH/ratio</li>
								<li>SAR Agua · Máscara agua/humedad</li>
							</ul>
						</div>

						{/* MODIS */}
						<div className="space-y-1.5">
							<p className="font-semibold text-amber-700 dark:text-amber-400">
								🌍 MODIS — 4 capas
							</p>
							<ul className="space-y-0.5 text-slate-600 dark:text-slate-400">
								<li>RGB · Color real 500 m</li>
								<li>NDVI · Vegetación (compuesto 8 días)</li>
								<li>NDWI · Agua (compuesto 8 días)</li>
								<li>EVI · Vegetación mejorada</li>
							</ul>
						</div>
					</div>
				</div>
			</div>

			{/* Estado de error del servicio */}
			{partidosError && (
				<Card className="mb-6 border-red-200 dark:border-red-800">
					<CardContent className="pt-6">
						<div className="flex items-start gap-3">
							<AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
							<div className="flex-1">
								<p className="text-red-600 dark:text-red-400 font-medium">
									Servicio no disponible
								</p>
								<p className="text-red-500 dark:text-red-300 text-sm mt-1">
									{partidosError}
								</p>
								<Button
									variant="outline"
									size="sm"
									className="mt-3"
									onClick={fetchPartidos}
									disabled={loadingPartidos}
								>
									{loadingPartidos ? "Reintentando..." : "Reintentar conexión"}
								</Button>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Formulario */}
			{!analysis && (
				<PartidaForm
					partidos={partidos}
					onSubmit={handleAnalyze}
					loading={loading || loadingPartidos}
				/>
			)}

			{/* Resultados */}
			{analysis && (
				<div className="space-y-6">
					<ResultsPanel analysis={analysis} taskId={taskId} />

					{/* Botón para nuevo análisis */}
					{analysis.status === "completed" || analysis.status === "failed" ? (
						<div className="flex justify-center">
							<Button onClick={handleReset} variant="outline" size="lg">
								<Satellite className="w-4 h-4 mr-2" />
								Nuevo Análisis
							</Button>
						</div>
					) : null}
				</div>
			)}

			{/* Información */}
			<Card className="mt-8">
				<CardHeader>
					<CardTitle className="text-lg">Información</CardTitle>
				</CardHeader>
				<CardContent>
					<div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
						{/* Sentinel-2 */}
						<div className="space-y-3">
							<p className="font-semibold text-blue-700 dark:text-blue-400 border-b border-blue-200 dark:border-blue-800 pb-1">
								🛰 Sentinel-2 (óptico)
							</p>
							<div>
								<p className="font-medium">Resolución</p>
								<p className="text-slate-600 dark:text-slate-400">10 m/píxel</p>
							</div>
							<div>
								<p className="font-medium">Índices calculados</p>
								<p className="text-slate-600 dark:text-slate-400">
									NDWI · MNDWI · NDVI · NDMI · NDSI · Salinidad
								</p>
							</div>
							<div>
								<p className="font-medium">Clasificación</p>
								<p className="text-slate-600 dark:text-slate-400">
									4 categorías: Agua, Humedal, Vegetación, Otros
								</p>
							</div>
						</div>

						{/* Sentinel-1 */}
						<div className="space-y-3">
							<p className="font-semibold text-emerald-700 dark:text-emerald-400 border-b border-emerald-200 dark:border-emerald-800 pb-1">
								📡 Sentinel-1 (SAR radar)
							</p>
							<div>
								<p className="font-medium">Resolución</p>
								<p className="text-slate-600 dark:text-slate-400">10 m/píxel</p>
							</div>
							<div>
								<p className="font-medium">Imágenes generadas</p>
								<p className="text-slate-600 dark:text-slate-400">
									VV · VH · RGB SAR (VV/VH/ratio)
								</p>
							</div>
							<div>
								<p className="font-medium">Detección</p>
								<p className="text-slate-600 dark:text-slate-400">
									Agua y zonas húmedas por backscatter
								</p>
							</div>
						</div>

						{/* MODIS */}
						<div className="space-y-3">
							<p className="font-semibold text-amber-700 dark:text-amber-400 border-b border-amber-200 dark:border-amber-800 pb-1">
								🌍 MODIS (composición 8 días)
							</p>
							<div>
								<p className="font-medium">Resolución</p>
								<p className="text-slate-600 dark:text-slate-400">
									500 m/píxel
								</p>
							</div>
							<div>
								<p className="font-medium">Índices calculados</p>
								<p className="text-slate-600 dark:text-slate-400">
									NDVI · NDWI · EVI
								</p>
							</div>
							<div>
								<p className="font-medium">Uso recomendado</p>
								<p className="text-slate-600 dark:text-slate-400">
									Tendencias temporales y cobertura regional
								</p>
							</div>
						</div>
					</div>

					<p className="text-xs text-slate-400 dark:text-slate-500 mt-4 pt-3 border-t border-slate-200 dark:border-slate-700">
						Proveedor: Microsoft Planetary Computer (STAC) — Todos los sensores
					</p>
				</CardContent>
			</Card>
		</div>
	);
}
