"use client";

import { useState } from "react";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { ImageIcon, Package, Satellite } from "@/lib/icons";
import { ImageCard } from "./ImageCard";
import { ImageModal } from "./ImageModal";
import { getSatAnalysisClient, getSatAssetUrl } from "@/lib/sat-api";
import type { SatelliteImageResult, SensorType } from "@/lib/types";

interface ImagesPanelProps {
	results: SatelliteImageResult[];
	partida: string;
	taskId?: string | null;
	sensor?: SensorType;
}

// ── Definición de tipos de imagen por sensor ──────────────────────────────────

type ImageKey = string;

interface ImageTypeDef {
	key: ImageKey;
	title: string;
	description: string;
	priority: number;
	group: "s2" | "s1" | "modis";
}

const ALL_IMAGE_TYPES: ImageTypeDef[] = [
	// Sentinel-2
	{
		key: "rgb",
		title: "RGB",
		description: "Color real - Sentinel-2",
		priority: 1,
		group: "s2",
	},
	{
		key: "clasificacion",
		title: "Clasificación",
		description: "Mapa de uso de suelo (4 categorías)",
		priority: 2,
		group: "s2",
	},
	{
		key: "ndwi",
		title: "NDWI",
		description: "Normalized Difference Water Index",
		priority: 3,
		group: "s2",
	},
	{
		key: "ndvi",
		title: "NDVI",
		description: "Normalized Difference Vegetation Index",
		priority: 4,
		group: "s2",
	},
	{
		key: "ndmi",
		title: "NDMI",
		description: "Normalized Difference Moisture Index",
		priority: 5,
		group: "s2",
	},
	{
		key: "mndwi",
		title: "MNDWI",
		description: "Modified NDWI (agua turbia)",
		priority: 6,
		group: "s2",
	},
	{
		key: "swir2_nir",
		title: "Salinidad",
		description: "SWIR2 + NIR Index",
		priority: 7,
		group: "s2",
	},
	{
		key: "ndsi",
		title: "NDSI",
		description: "Normalized Difference Snow Index",
		priority: 8,
		group: "s2",
	},
	// Sentinel-1 SAR
	{
		key: "sar_rgb",
		title: "SAR RGB",
		description: "Composición SAR (VV/VH/ratio)",
		priority: 10,
		group: "s1",
	},
	{
		key: "sar_water",
		title: "SAR Agua",
		description: "Máscara agua/humedad SAR",
		priority: 11,
		group: "s1",
	},
	{
		key: "sar_vv",
		title: "SAR VV",
		description: "Backscatter VV (polarización vertical)",
		priority: 12,
		group: "s1",
	},
	{
		key: "sar_vh",
		title: "SAR VH",
		description: "Backscatter VH (polarización cruzada)",
		priority: 13,
		group: "s1",
	},
	// MODIS
	{
		key: "modis_rgb",
		title: "MODIS RGB",
		description: "Color real MODIS 500 m",
		priority: 20,
		group: "modis",
	},
	{
		key: "modis_ndvi",
		title: "MODIS NDVI",
		description: "NDVI MODIS 500 m (8 días)",
		priority: 21,
		group: "modis",
	},
	{
		key: "modis_ndwi",
		title: "MODIS NDWI",
		description: "NDWI MODIS 500 m (8 días)",
		priority: 22,
		group: "modis",
	},
	{
		key: "modis_evi",
		title: "MODIS EVI",
		description: "EVI MODIS 500 m (8 días)",
		priority: 23,
		group: "modis",
	},
];

const SENSOR_LABELS: Record<string, string> = {
	"sentinel-2": "Sentinel-2",
	"sentinel-1": "Sentinel-1 SAR",
	modis: "MODIS 500 m",
};

const SENSOR_COLORS: Record<string, string> = {
	"sentinel-2": "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
	"sentinel-1":
		"bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
	modis: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
};

/**
 * Panel de visualización de imágenes satelitales.
 * Soporta Sentinel-2, Sentinel-1 SAR y MODIS.
 */
export function ImagesPanel({
	results,
	partida,
	taskId,
	sensor = "sentinel-2",
}: ImagesPanelProps) {
	const [selectedDate, setSelectedDate] = useState(
		results.length > 0 ? results[results.length - 1].date : "",
	);
	const [modalOpen, setModalOpen] = useState(false);
	const [modalImage, setModalImage] = useState<{
		url: string;
		title: string;
		description: string;
	} | null>(null);

	const selectedResult = results.find((r) => r.date === selectedDate);
	const images = selectedResult?.images;

	// Filtrar qué imágenes están disponibles en la respuesta
	const availableTypes = images
		? ALL_IMAGE_TYPES.filter(
				(t) =>
					images[t.key as keyof typeof images] !== undefined &&
					images[t.key as keyof typeof images] !== null,
			).sort((a, b) => a.priority - b.priority)
		: [];

	const openModal = (url: string, title: string, description: string) => {
		setModalImage({ url, title, description });
		setModalOpen(true);
	};

	const handleDownloadAll = async () => {
		if (!taskId) {
			alert("No se puede descargar: ID de tarea no disponible");
			return;
		}
		try {
			const client = getSatAnalysisClient();
			await client.downloadImagesZipDirect(
				taskId,
				`analisis_satelital_${partida}.zip`,
			);
		} catch (error) {
			console.error("Error descargando ZIP:", error);
			alert("Error al descargar el archivo ZIP. Por favor intenta nuevamente.");
		}
	};

	const formatDate = (dateStr: string) =>
		new Date(dateStr).toLocaleDateString("es-AR", {
			day: "2-digit",
			month: "long",
			year: "numeric",
		});

	const getFullImageUrl = (relativePath: string) =>
		getSatAssetUrl(relativePath);

	if (!results || results.length === 0) {
		return (
			<Card>
				<CardHeader>
					<CardTitle className="flex items-center gap-2">
						<ImageIcon className="w-5 h-5" />
						Imágenes Satelitales
					</CardTitle>
				</CardHeader>
				<CardContent>
					<p className="text-slate-600 dark:text-slate-400">
						No hay imágenes disponibles para mostrar.
					</p>
				</CardContent>
			</Card>
		);
	}

	const selectedAffectedPercent = selectedResult
		? Math.round(
				((selectedResult.water_ha + selectedResult.wetland_ha) /
					Math.max(
						selectedResult.water_ha +
							selectedResult.wetland_ha +
							selectedResult.vegetation_ha +
							selectedResult.other_ha,
						0.001,
					)) *
					100,
			)
		: null;

	const sensorLabel = SENSOR_LABELS[sensor] ?? sensor;
	const sensorColor = SENSOR_COLORS[sensor] ?? "";

	return (
		<div className="space-y-6">
			{/* Header con selector y sensor badge */}
			<Card>
				<CardHeader>
					<div className="flex items-start justify-between gap-2">
						<div>
							<CardTitle className="flex items-center gap-2">
								<Satellite className="w-5 h-5" />
								Imágenes Satelitales
							</CardTitle>
							<CardDescription>
								Partida: {partida} · {availableTypes.length} imágenes
								disponibles
							</CardDescription>
						</div>
						<Badge className={`shrink-0 ${sensorColor}`}>{sensorLabel}</Badge>
					</div>
				</CardHeader>
				<CardContent>
					<div className="flex flex-col sm:flex-row sm:items-end gap-3">
						<div className="flex-1 space-y-1.5">
							<Label htmlFor="fecha-imagen">Fecha de imagen</Label>
							<Select value={selectedDate} onValueChange={setSelectedDate}>
								<SelectTrigger id="fecha-imagen" className="w-full">
									<SelectValue placeholder="Seleccionar una fecha..." />
								</SelectTrigger>
								<SelectContent>
									{results.map((result) => {
										const total =
											result.water_ha +
											result.wetland_ha +
											result.vegetation_ha +
											result.other_ha;
										const affectedPercent =
											total > 0
												? Math.round(
														((result.water_ha + result.wetland_ha) / total) *
															100,
													)
												: 0;
										return (
											<SelectItem key={result.date} value={result.date}>
												{formatDate(result.date)}
												{"  ·  "}
												{affectedPercent}% afectado
											</SelectItem>
										);
									})}
								</SelectContent>
							</Select>
						</div>

						{selectedAffectedPercent !== null && (
							<Badge
								variant={
									selectedAffectedPercent > 30
										? "destructive"
										: selectedAffectedPercent > 10
											? "secondary"
											: "outline"
								}
								className="h-10 px-4 text-sm self-end shrink-0"
							>
								{selectedAffectedPercent}% afectado
							</Badge>
						)}

						<Button
							variant="outline"
							onClick={handleDownloadAll}
							className="gap-2 self-end shrink-0"
						>
							<Package className="w-4 h-4" />
							<span className="hidden sm:inline">Descargar Todas</span>
							<span className="sm:hidden">ZIP</span>
						</Button>
					</div>
				</CardContent>
			</Card>

			{/* Galería de imágenes */}
			{availableTypes.length > 0 && images ? (
				<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
					{availableTypes.map((type) => {
						const imageUrl = images[type.key as keyof typeof images];
						if (!imageUrl) return null;
						return (
							<ImageCard
								key={type.key}
								title={type.title}
								description={type.description}
								imageUrl={getFullImageUrl(imageUrl)}
								onZoom={() =>
									openModal(
										getFullImageUrl(imageUrl),
										type.title,
										type.description,
									)
								}
								type={
									type.key === "rgb" ||
									type.key === "sar_rgb" ||
									type.key === "modis_rgb"
										? "rgb"
										: type.key === "clasificacion" || type.key === "sar_water"
											? "clasificacion"
											: "indice"
								}
							/>
						);
					})}
				</div>
			) : (
				<Card>
					<CardContent className="py-12">
						<div className="flex flex-col items-center justify-center text-center gap-4">
							<div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
								<ImageIcon className="w-8 h-8 text-slate-400" />
							</div>
							<div>
								<h3 className="font-semibold text-slate-900 dark:text-white mb-1">
									Imágenes no disponibles
								</h3>
								<p className="text-sm text-slate-600 dark:text-slate-400 max-w-md">
									Las imágenes satelitales para esta fecha no están disponibles.
								</p>
							</div>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Leyenda dinámica según sensor */}
			<Card>
				<CardHeader>
					<CardTitle className="text-base">Leyenda</CardTitle>
				</CardHeader>
				<CardContent>
					{sensor === "sentinel-1" ? (
						<div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#2196F3]" />
								<div>
									<p className="font-medium text-sm">Agua SAR</p>
									<p className="text-xs text-slate-500">VV &lt; 0.05 lineal</p>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#8BC34A]" />
								<div>
									<p className="font-medium text-sm">Suelo Húmedo</p>
									<p className="text-xs text-slate-500">VV 0.05–0.15</p>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#BDBDBD]" />
								<div>
									<p className="font-medium text-sm">Seco/Vegetación</p>
									<p className="text-xs text-slate-500">VV &gt; 0.15</p>
								</div>
							</div>
						</div>
					) : sensor === "modis" ? (
						<div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#2196F3]" />
								<div>
									<p className="font-medium text-sm">Agua</p>
									<p className="text-xs text-slate-500">NDWI &gt; 0.1</p>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#4CAF50]" />
								<div>
									<p className="font-medium text-sm">Vegetación</p>
									<p className="text-xs text-slate-500">NDVI &gt; 0.3</p>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#9E9E9E]" />
								<div>
									<p className="font-medium text-sm">Otros</p>
									<p className="text-xs text-slate-500">500 m / 8 días</p>
								</div>
							</div>
						</div>
					) : (
						<div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#2196F3]" />
								<div>
									<p className="font-medium text-sm">Agua</p>
									<p className="text-xs text-slate-500">NDWI alto</p>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#2E7D32]" />
								<div>
									<p className="font-medium text-sm">Humedal</p>
									<p className="text-xs text-slate-500">NDVI medio</p>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#8BC34A]" />
								<div>
									<p className="font-medium text-sm">Vegetación</p>
									<p className="text-xs text-slate-500">NDVI alto</p>
								</div>
							</div>
							<div className="flex items-center gap-3">
								<div className="w-6 h-6 rounded bg-[#9E9E9E]" />
								<div>
									<p className="font-medium text-sm">Otros</p>
									<p className="text-xs text-slate-500">Suelo desnudo</p>
								</div>
							</div>
						</div>
					)}
				</CardContent>
			</Card>

			{modalImage && (
				<ImageModal
					isOpen={modalOpen}
					onClose={() => setModalOpen(false)}
					imageUrl={modalImage.url}
					title={modalImage.title}
					description={modalImage.description}
					date={selectedDate}
				/>
			)}
		</div>
	);
}
