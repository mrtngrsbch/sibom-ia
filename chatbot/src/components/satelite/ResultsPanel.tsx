"use client";

import { useState } from "react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
	BarChart,
	Bar,
	XAxis,
	YAxis,
	Tooltip,
	Legend,
	ResponsiveContainer,
	CartesianGrid,
} from "recharts";
import { Droplets, Cloud, TrendingUp, TrendingDown, Minus } from "@/lib/icons";
import { ImagesPanel } from "./ImagesPanel";
import { ImageThumbnail } from "./ImageThumbnail";
import { ImageModal } from "./ImageModal";
import type { AnalyzeResponse, SatelliteImageResult } from "@/lib/types";

interface ResultsPanelProps {
	analysis: AnalyzeResponse;
	taskId?: string | null;
}

/**
 * Colores para las categorías de clasificación
 */
const COLORS = {
	water: "#2196F3",
	wetland: "#2E7D32",
	vegetation: "#8BC34A",
	other: "#9E9E9E",
};

/**
 * Panel de resultados del análisis satelital
 */
export function ResultsPanel({ analysis, taskId }: ResultsPanelProps) {
	const { status, progress, message, summary, results, partida } = analysis;

	// State para el modal de imágenes
	const [modalOpen, setModalOpen] = useState(false);
	const [modalImageUrl, setModalImageUrl] = useState<string | null>(null);

	const openImageModal = (url: string) => {
		setModalImageUrl(url);
		setModalOpen(true);
	};

	const closeImageModal = () => {
		setModalOpen(false);
		setModalImageUrl(null);
	};

	// Estado de carga
	if (status === "pending" || status === "processing") {
		return (
			<Card>
				<CardHeader>
					<CardTitle>Procesando Análisis</CardTitle>
					<CardDescription>
						El análisis puede tardar varios minutos...
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="space-y-2">
						<div className="flex justify-between text-sm">
							<span>{message}</span>
							<span>{Math.round(progress * 100)}%</span>
						</div>
						<Progress value={progress * 100} className="h-2" />
					</div>

					{status === "processing" && (
						<div className="text-sm text-slate-500 dark:text-slate-400">
							<p>El análisis incluye:</p>
							<ul className="list-disc list-inside mt-2 space-y-1">
								<li>Consulta de geometría en ARBA</li>
								<li>Búsqueda de imágenes Sentinel-2</li>
								<li>Descarga y procesamiento de bandas</li>
								<li>Cálculo de índices espectrales</li>
								<li>Clasificación de píxeles</li>
							</ul>
						</div>
					)}
				</CardContent>
			</Card>
		);
	}

	// Estado de error
	if (status === "failed") {
		return (
			<Card className="border-red-200 dark:border-red-800">
				<CardHeader>
					<CardTitle className="text-red-600 dark:text-red-400">
						Error en el Análisis
					</CardTitle>
				</CardHeader>
				<CardContent>
					<p className="text-slate-600 dark:text-slate-400">
						{analysis.error ||
							"Ocurrió un error al procesar el análisis. Por favor intenta nuevamente."}
					</p>
				</CardContent>
			</Card>
		);
	}

	// Estado completado sin resultados
	if (status === "completed" && (!results || results.length === 0)) {
		return (
			<Card>
				<CardHeader>
					<CardTitle>Análisis Completado</CardTitle>
				</CardHeader>
				<CardContent>
					<p className="text-slate-600 dark:text-slate-400">
						El análisis se completó pero no se encontraron resultados.
					</p>
				</CardContent>
			</Card>
		);
	}

	// Preparar datos para el gráfico
	const chartData =
		results?.map((r) => ({
			date: new Date(r.date).toLocaleDateString("es-AR", {
				day: "2-digit",
				month: "2-digit",
				year: "2-digit",
			}),
			agua: r.water_ha,
			humedal: r.wetland_ha,
			vegetacion: r.vegetation_ha,
			otros: r.other_ha,
			total: r.water_ha + r.wetland_ha + r.vegetation_ha + r.other_ha,
		})) || [];

	// Info de color/etiqueta según nivel de riesgo (escala 0–100)
	const getRiskInfo = (score: number) => {
		if (score >= 75) return { label: "Bajo", className: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300" };
		if (score >= 50) return { label: "Moderado", className: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300" };
		if (score >= 30) return { label: "Elevado", className: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300" };
		return { label: "Alto", className: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300" };
	};
	const riskInfo = analysis.diagnostic ? getRiskInfo(analysis.diagnostic.overall_score) : null;

	return (
		<div className="space-y-6">
			{/* Resumen */}
			{summary && (
				<Card>
					<CardHeader>
						<CardTitle>Resumen del Análisis</CardTitle>
						<CardDescription>
							Partida: {summary.partida} | {summary.images_analyzed} imágenes
							procesadas
						</CardDescription>
					</CardHeader>
					<CardContent>
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
							{/* Área total */}
							{summary.total_area_ha && (
								<div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
									<p className="text-sm text-slate-500 dark:text-slate-400">
										Área Total
									</p>
									<p className="text-2xl font-bold">
										{summary.total_area_ha} ha
									</p>
								</div>
							)}

							{/* Máximo agua */}
							<div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
								<div className="flex items-center gap-2 mb-1">
									<Droplets className="w-4 h-4 text-blue-600" />
									<p className="text-sm text-slate-500 dark:text-slate-400">
										Máx. Agua
									</p>
								</div>
								<p className="text-2xl font-bold text-blue-600">
									{summary.max_water_ha} ha
								</p>
								<p className="text-xs text-slate-500">
									Promedio: {summary.avg_water_ha} ha
								</p>
							</div>

							{/* Máximo humedal */}
							<div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
								<div className="flex items-center gap-2 mb-1">
									<Droplets className="w-4 h-4 text-green-600" />
									<p className="text-sm text-slate-500 dark:text-slate-400">
										Máx. Humedal
									</p>
								</div>
								<p className="text-2xl font-bold text-green-600">
									{summary.max_wetland_ha} ha
								</p>
								<p className="text-xs text-slate-500">
									Promedio: {summary.avg_wetland_ha} ha
								</p>
							</div>

							{/* Pico de anegamiento */}
							<div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
								<p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
									Pico Anegamiento
								</p>
								<p className="text-lg font-bold text-purple-600">
									{summary.max_affected_area_ha} ha
								</p>
								<p className="text-xs text-slate-500">
									{summary.max_affected_date}
								</p>
							</div>
						</div>

						{/* Tendencias */}
						<div className="mt-4 flex gap-4">
							<div className="flex items-center gap-2">
								<span className="text-sm text-slate-500 dark:text-slate-400">
									Agua:
								</span>
								{summary.trend_water === "up" && (
									<TrendingUp className="w-4 h-4 text-red-500" />
								)}
								{summary.trend_water === "down" && (
									<TrendingDown className="w-4 h-4 text-green-500" />
								)}
								{summary.trend_water === "stable" && (
									<Minus className="w-4 h-4 text-slate-400" />
								)}
								<Badge
									variant={
										summary.trend_water === "up"
											? "destructive"
											: summary.trend_water === "down"
												? "default"
												: "secondary"
									}
								>
									{summary.trend_water === "up"
										? "Aumentando"
										: summary.trend_water === "down"
											? "Disminuyendo"
											: "Estable"}
								</Badge>
							</div>
							<div className="flex items-center gap-2">
								<span className="text-sm text-slate-500 dark:text-slate-400">
									Humedal:
								</span>
								{summary.trend_wetland === "up" && (
									<TrendingUp className="w-4 h-4 text-red-500" />
								)}
								{summary.trend_wetland === "down" && (
									<TrendingDown className="w-4 h-4 text-green-500" />
								)}
								{summary.trend_wetland === "stable" && (
									<Minus className="w-4 h-4 text-slate-400" />
								)}
								<Badge
									variant={
										summary.trend_wetland === "up"
											? "destructive"
											: summary.trend_wetland === "down"
												? "default"
												: "secondary"
									}
								>
									{summary.trend_wetland === "up"
										? "Aumentando"
										: summary.trend_wetland === "down"
											? "Disminuyendo"
											: "Estable"}
								</Badge>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Tabs con Diagnóstico, gráfico, tabla e imágenes */}
			<Tabs defaultValue="diagnostic" className="w-full">
				<TabsList className="flex flex-wrap h-auto gap-1 w-full justify-start bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
					<TabsTrigger value="diagnostic" className="text-xs sm:text-sm">
						Diagnóstico
					</TabsTrigger>
					<TabsTrigger value="chart" className="text-xs sm:text-sm">
						Gráfico de Evolución
					</TabsTrigger>
					<TabsTrigger value="table" className="text-xs sm:text-sm">
						Tabla de Datos
					</TabsTrigger>
					<TabsTrigger value="images" className="text-xs sm:text-sm">
						Imágenes
					</TabsTrigger>
				</TabsList>
				<TabsContent value="diagnostic" className="mt-4">
					<Card>
						<CardHeader>
							<CardTitle>Diagnóstico Profesional</CardTitle>
							<CardDescription>
								Evaluación automática del riesgo de anegamiento/salinización
							</CardDescription>
						</CardHeader>
						<CardContent>
							{analysis.diagnostic && riskInfo ? (
								<div className="space-y-5">
									{/* Score general + badge de riesgo */}
									<div className="flex items-center gap-6">
										<div className="text-center">
											<span className="text-5xl font-bold tabular-nums">
												{analysis.diagnostic.overall_score.toFixed(0)}
											</span>
											<p className="text-xs text-slate-500 mt-0.5">/ 100</p>
										</div>
										<div className="flex-1 space-y-2">
											<span
												className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${riskInfo.className}`}
											>
												Riesgo {analysis.diagnostic.risk_level ?? riskInfo.label}
											</span>
											<Progress
												value={analysis.diagnostic.overall_score}
												className="h-2"
											/>
										</div>
									</div>

									{/* Interpretación */}
									<div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200">
										{analysis.diagnostic.interpretation}
									</div>

									{/* Componentes del puntaje */}
									<div className="space-y-4">
										<p className="text-sm font-semibold text-slate-600 dark:text-slate-300">
											Detalle por componente
										</p>
										{analysis.diagnostic.scores.map((score) => (
											<div key={score.name} className="space-y-1.5">
												<div className="flex justify-between items-baseline text-sm">
													<span className="font-medium">{score.name}</span>
													<span className="text-slate-500 tabular-nums">
														{score.value.toFixed(2)}
														{score.label ? ` ${score.label}` : ""}
													</span>
												</div>
												{score.component_score !== undefined && (
													<Progress
														value={score.component_score}
														className="h-1.5"
													/>
												)}
												{score.interpretation && (
													<p className="text-xs text-slate-400">
														{score.interpretation}
													</p>
												)}
											</div>
										))}
									</div>
								</div>
							) : (
								<div className="space-y-3">
									<p className="text-amber-600 dark:text-amber-400 font-medium">
										Diagnóstico no disponible en este resultado.
									</p>
									<p className="text-slate-500 dark:text-slate-400 text-sm">
										<strong>Motivo:</strong> Este análisis fue generado con una
										versión anterior del sistema que no incluía el módulo de
										diagnóstico automático.
									</p>
									<p className="text-slate-500 dark:text-slate-400 text-sm">
										Vuelve a ejecutar el análisis para obtener la evaluación de
										riesgo de anegamiento/salinización.
									</p>
								</div>
							)}
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="chart" className="mt-4">
					<Card>
						<CardHeader>
							<CardTitle>Evolución Temporal</CardTitle>
							<CardDescription>
								Clasificación de uso de suelo a lo largo del tiempo
							</CardDescription>
						</CardHeader>
						<CardContent>
							<ResponsiveContainer width="100%" height={350}>
								<BarChart data={chartData}>
									<CartesianGrid
										strokeDasharray="3 3"
										className="stroke-slate-200 dark:stroke-slate-700"
									/>
									<XAxis
										dataKey="date"
										className="text-xs text-slate-500 dark:text-slate-400"
										tick={{ fill: "currentColor" }}
									/>
									<YAxis
										label={{
											value: "Hectáreas",
											angle: -90,
											position: "insideLeft",
										}}
										className="text-xs text-slate-500 dark:text-slate-400"
										tick={{ fill: "currentColor" }}
									/>
									<Tooltip
										contentStyle={{
											backgroundColor: "rgba(255, 255, 255, 0.95)",
											border: "1px solid #e2e8f0",
											borderRadius: "8px",
										}}
										formatter={(value: number, name: string) => {
											const labels: Record<string, string> = {
												agua: "Agua",
												humedal: "Humedal",
												vegetacion: "Vegetación",
												otros: "Otros",
											};
											return [`${value.toFixed(1)} ha`, labels[name] || name];
										}}
									/>
									<Legend />
									<Bar
										dataKey="otros"
										name="Otros"
										stackId="a"
										fill={COLORS.other}
									/>
									<Bar
										dataKey="vegetacion"
										name="Vegetación"
										stackId="a"
										fill={COLORS.vegetation}
									/>
									<Bar
										dataKey="humedal"
										name="Humedal"
										stackId="a"
										fill={COLORS.wetland}
									/>
									<Bar
										dataKey="agua"
										name="Agua"
										stackId="a"
										fill={COLORS.water}
									/>
								</BarChart>
							</ResponsiveContainer>
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="table" className="mt-4">
					<Card>
						<CardHeader>
							<CardTitle>Resultados por Imagen</CardTitle>
							<CardDescription>Detalle de cada fecha analizada</CardDescription>
						</CardHeader>
						<CardContent>
							<Table>
								<TableHeader>
									<TableRow>
										<TableHead className="w-20">Vista</TableHead>
										<TableHead>Fecha</TableHead>
										<TableHead className="text-right">Agua (ha)</TableHead>
										<TableHead className="text-right">Humedal (ha)</TableHead>
										<TableHead className="text-right">Veg (ha)</TableHead>
										<TableHead className="text-right">Otros (ha)</TableHead>
										<TableHead className="text-right">Nubes</TableHead>
										<TableHead className="text-right">Afectado</TableHead>
									</TableRow>
								</TableHeader>
								<TableBody>
									{results?.map((r) => {
										const total =
											r.water_ha + r.wetland_ha + r.vegetation_ha + r.other_ha;
										const afectado = (
											((r.water_ha + r.wetland_ha) / total) *
											100
										).toFixed(1);

										return (
											<TableRow key={r.date}>
												<TableCell>
													<ImageThumbnail
														images={r.images}
														date={r.date}
														water_ha={r.water_ha}
														wetland_ha={r.wetland_ha}
														total_ha={total}
														onOpenModal={openImageModal}
													/>
												</TableCell>
												<TableCell className="font-medium">
													{new Date(r.date).toLocaleDateString("es-AR")}
												</TableCell>
												<TableCell className="text-right text-blue-600">
													{r.water_ha.toFixed(1)}
												</TableCell>
												<TableCell className="text-right text-green-600">
													{r.wetland_ha.toFixed(1)}
												</TableCell>
												<TableCell className="text-right text-lime-600">
													{r.vegetation_ha.toFixed(1)}
												</TableCell>
												<TableCell className="text-right text-slate-500">
													{r.other_ha.toFixed(1)}
												</TableCell>
												<TableCell className="text-right">
													{r.cloud_cover !== undefined &&
													r.cloud_cover !== null ? (
														<span className="flex items-center justify-end gap-1">
															<Cloud className="w-3 h-3" />
															{r.cloud_cover.toFixed(0)}%
														</span>
													) : (
														"N/A"
													)}
												</TableCell>
												<TableCell className="text-right font-bold">
													{afectado}%
												</TableCell>
											</TableRow>
										);
									})}
								</TableBody>
							</Table>
						</CardContent>
					</Card>
				</TabsContent>

				{/* Tab de imágenes */}
				<TabsContent value="images" className="mt-4">
					<ImagesPanel
						results={results || []}
						partida={partida}
						taskId={taskId}
						sensor={analysis.sensor}
					/>
				</TabsContent>
			</Tabs>

			{/* Modal para visualización de imágenes */}
			{modalImageUrl && (
				<ImageModal
					isOpen={modalOpen}
					onClose={closeImageModal}
					imageUrl={modalImageUrl}
					title="Imagen Satelital"
					description="Clasificación de uso de suelo"
				/>
			)}
		</div>
	);
}
