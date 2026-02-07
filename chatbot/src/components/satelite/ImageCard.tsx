'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, ZoomIn } from '@/lib/icons';
import { useState } from 'react';
import Image from 'next/image';

interface ImageCardProps {
  title: string;
  description: string;
  imageUrl: string;
  onZoom: () => void;
  type: 'rgb' | 'clasificacion' | 'indice';
}

const IMAGE_DESCRIPTIONS: Record<string, string> = {
  rgb: 'Imagen satelital en color real (Sentinel-2)',
  clasificacion: 'Mapa de clasificación de uso de suelo',
  ndwi: 'Normalized Difference Water Index - Detección de agua',
  mndwi: 'Modified NDWI - Detección de agua turbia',
  ndvi: 'Normalized Difference Vegetation Index - Vegetación',
  ndmi: 'Normalized Difference Moisture Index - Humedad',
  ndsi: 'Normalized Difference Snow Index - Nieve/Hielo',
  'swir2-nir': 'Índice de salinidad (SWIR2 + NIR)',
};

const IMAGE_COLORS: Record<string, string> = {
  rgb: 'from-blue-500 to-green-500',
  clasificacion: 'from-purple-500 to-pink-500',
  ndwi: 'from-blue-400 to-cyan-400',
  mndwi: 'from-cyan-400 to-blue-500',
  ndvi: 'from-green-400 to-emerald-500',
  ndmi: 'from-green-500 to-teal-500',
  ndsi: 'from-orange-400 to-red-400',
  'swir2-nir': 'from-amber-400 to-orange-500',
};

/**
 * Card individual para mostrar una imagen satelital con acciones.
 */
export function ImageCard({ title, description, imageUrl, onZoom, type }: ImageCardProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  const gradient = IMAGE_COLORS[title.toLowerCase()] || 'from-slate-400 to-slate-600';

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `${title.replace(/\s+/g, '_')}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Card className="group overflow-hidden hover:shadow-lg transition-shadow duration-300">
      <div className="relative aspect-video bg-slate-100 dark:bg-slate-950 overflow-hidden">
        {/* Loading skeleton */}
        {isLoading && (
          <div className="absolute inset-0 bg-slate-200 dark:bg-slate-800 animate-pulse">
            <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-20`} />
          </div>
        )}

        {/* Error state */}
        {imageError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-4 bg-slate-100 dark:bg-slate-950">
            <div className="w-12 h-12 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-2">
              <Download className="w-6 h-6 text-red-500" />
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 text-center">
              No disponible
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3 gap-2"
              onClick={handleDownload}
            >
              <Download className="w-4 h-4" />
              Descargar
            </Button>
          </div>
        ) : (
          <>
            <img
              src={imageUrl}
              alt={title}
              className="w-full h-full object-contain"
              onLoad={() => setIsLoading(false)}
              onError={() => {
                setIsLoading(false);
                setImageError(true);
              }}
            />

            {/* Overlay on hover */}
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={onZoom}
                className="gap-2"
              >
                <ZoomIn className="w-4 h-4" />
                Ampliar
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleDownload}
                className="gap-2"
              >
                <Download className="w-4 h-4" />
                Descargar
              </Button>
            </div>
          </>
        )}

        {/* Type badge */}
        <div className="absolute top-2 left-2">
          <span className={`px-2 py-1 text-xs font-medium text-white bg-gradient-to-r ${gradient} rounded-full shadow-sm`}>
            {title}
          </span>
        </div>
      </div>

      <CardContent className="p-4">
        <h4 className="font-semibold text-sm text-slate-900 dark:text-white mb-1">
          {IMAGE_DESCRIPTIONS[title.toLowerCase()] || description}
        </h4>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          {description}
        </p>
      </CardContent>
    </Card>
  );
}
