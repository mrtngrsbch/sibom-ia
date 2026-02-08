'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ImageIcon, Download, Package, Satellite } from '@/lib/icons';
import { ImageCard } from './ImageCard';
import { ImageModal } from './ImageModal';
import { getSatAnalysisClient } from '@/lib/sat-api';
import type { SatelliteImageResult } from '@/lib/types';

interface ImagesPanelProps {
  results: SatelliteImageResult[];
  partida: string;
  taskId?: string | null;
}

/**
 * Panel de visualización de imágenes satelitales.
 *
 * Muestra un selector de fecha y una galería con todas las imágenes
 * (RGB, clasificación e índices espectrales) para la fecha seleccionada.
 */
export function ImagesPanel({ results, partida, taskId }: ImagesPanelProps) {
  // Fecha seleccionada (por defecto la más reciente)
  const [selectedDate, setSelectedDate] = useState(
    results.length > 0 ? results[results.length - 1].date : ''
  );

  // Log de diagnóstico
  console.log('[DEBUG] ImagesPanel - results:', results);
  console.log('[DEBUG] ImagesPanel - results.length:', results.length);
  console.log('[DEBUG] ImagesPanel - selectedDate:', selectedDate);
  console.log('[DEBUG] ImagesPanel - results dates:', results.map(r => r.date));

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalImage, setModalImage] = useState<{ url: string; title: string; description: string } | null>(null);

  // Obtener el resultado seleccionado
  const selectedResult = results.find((r) => r.date === selectedDate);

  // URLs de imágenes para el resultado seleccionado
  const images = selectedResult?.images;

  // Log de diagnóstico
  console.log('[DEBUG] ImagesPanel - selectedResult:', selectedResult);
  console.log('[DEBUG] ImagesPanel - images:', images);

  // Configuración de tipos de imágenes
  const imageTypes = [
    { key: 'rgb', title: 'RGB', description: 'Color real - Sentinel-2', priority: 1 },
    { key: 'clasificacion', title: 'Clasificación', description: 'Mapa de uso de suelo (4 categorías)', priority: 2 },
    { key: 'ndwi', title: 'NDWI', description: 'Normalized Difference Water Index', priority: 3 },
    { key: 'ndvi', title: 'NDVI', description: 'Normalized Difference Vegetation Index', priority: 4 },
    { key: 'ndmi', title: 'NDMI', description: 'Normalized Difference Moisture Index', priority: 5 },
    { key: 'mndwi', title: 'MNDWI', description: 'Modified NDWI (agua turbia)', priority: 6 },
    { key: 'swir2-nir', title: 'Salinidad', description: 'SWIR2 + NIR Index', priority: 7 },
    { key: 'ndsi', title: 'NDSI', description: 'Normalized Difference Snow Index', priority: 8 },
  ] as const;

  // Abrir modal con imagen
  const openModal = (url: string, title: string, description: string) => {
    setModalImage({ url, title, description });
    setModalOpen(true);
  };

  // Descargar todas las imágenes como ZIP
  const handleDownloadAll = async () => {
    if (!taskId) {
      alert('No se puede descargar: ID de tarea no disponible');
      return;
    }

    try {
      const client = getSatAnalysisClient();
      await client.downloadImagesZipDirect(taskId, `analisis_satelital_${partida}.zip`);
    } catch (error) {
      console.error('Error descargando ZIP:', error);
      alert('Error al descargar el archivo ZIP. Por favor intenta nuevamente.');
    }
  };

  // Formatear fecha para mostrar
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    });
  };

  // Obtener URL base para imágenes
  // En producción usa ruta relativa (nginx hace proxy), en desarrollo local usa URL completa
  const getFullImageUrl = (relativePath: string) => {
    // Si estamos en desarrollo local (no en Docker), usar URL directa del backend
    if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      return `http://localhost:8001${relativePath}`;
    }
    // En producción/Docker, usar ruta relativa (nginx hace proxy)
    return relativePath;
  };

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

  // Contar cuántas imágenes están disponibles
  const availableImages = images
    ? imageTypes.filter((type) => images[type.key as keyof typeof images]).length
    : 0;

  return (
    <div className="space-y-6">
      {/* Header con selector y acciones */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Satellite className="w-5 h-5" />
                Imágenes Satelitales
              </CardTitle>
              <CardDescription>
                Partida: {partida} • {availableImages} de 8 imágenes disponibles
              </CardDescription>
            </div>

            <div className="flex items-center gap-3">
              {/* Selector de fecha */}
              <Select value={selectedDate} onValueChange={setSelectedDate}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Seleccionar fecha" />
                </SelectTrigger>
                <SelectContent>
                  {results.map((result) => {
                    const dateFormatted = formatDate(result.date);
                    const affectedPercent = ((result.water_ha + result.wetland_ha) /
                      (result.water_ha + result.wetland_ha + result.vegetation_ha + result.other_ha) * 100).toFixed(0);

                    return (
                      <SelectItem key={result.date} value={result.date}>
                        <div className="flex items-center justify-between gap-2 w-full">
                          <span>{dateFormatted}</span>
                          <Badge variant="outline" className="ml-2">
                            {affectedPercent}% afectado
                          </Badge>
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>

              {/* Botón descargar todas */}
              <Button variant="outline" size="sm" onClick={handleDownloadAll} className="gap-2">
                <Package className="w-4 h-4" />
                <span className="hidden sm:inline">Descargar Todas</span>
                <span className="sm:hidden">ZIP</span>
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Galería de imágenes */}
      {images ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {(() => {
            const filteredTypes = imageTypes.filter((type) => images[type.key as keyof typeof images]);
            console.log('[DEBUG] ImagesPanel - filteredTypes:', filteredTypes);
            console.log('[DEBUG] ImagesPanel - available images count:', filteredTypes.length);
            return filteredTypes
              .sort((a, b) => a.priority - b.priority)
              .map((type) => {
                const imageUrl = images[type.key as keyof typeof images];
                if (!imageUrl) return null;

                console.log('[DEBUG] ImagesPanel - rendering image:', type.key, imageUrl);

                return (
                  <ImageCard
                    key={type.key}
                    title={type.title}
                    description={type.description}
                    imageUrl={getFullImageUrl(imageUrl)}
                    onZoom={() => openModal(getFullImageUrl(imageUrl), type.title, type.description)}
                    type={type.key === 'rgb' ? 'rgb' : type.key === 'clasificacion' ? 'clasificacion' : 'indice'}
                  />
                );
              });
          })()}
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
                  Esto puede deberse a que el análisis se ejecutó antes de que
                  se implementara esta funcionalidad.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Leyenda de clasificación */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Leyenda de Clasificación</CardTitle>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>

      {/* Modal de imagen */}
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
