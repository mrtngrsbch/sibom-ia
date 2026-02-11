'use client';

import { Badge } from '@/components/ui/badge';
import { ImageIcon } from '@/lib/icons';
import { useState } from 'react';
import Image from 'next/image';
import type { ImageUrls } from '@/lib/types';

interface ImageThumbnailProps {
  images?: ImageUrls;
  date: string;
  water_ha: number;
  wetland_ha: number;
  total_ha: number;
  onOpenModal: (url: string) => void;
}

/**
 * Miniatura clickeable de la imagen de clasificación.
 *
 * Muestra una preview pequeña y al hacer click abre el modal completo.
 */
export function ImageThumbnail({ images, date, water_ha, wetland_ha, total_ha, onOpenModal }: ImageThumbnailProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // Usar la imagen de clasificación por defecto, o RGB si no está disponible
  const thumbnailUrl = images?.clasificacion || images?.rgb;

  if (!thumbnailUrl) {
    return (
      <div className="w-16 h-12 bg-slate-100 dark:bg-slate-800 rounded flex items-center justify-center">
        <ImageIcon className="w-5 h-5 text-slate-400" />
      </div>
    );
  }

  // Calcular porcentaje afectado
  const affectedPercent = total_ha > 0
    ? ((water_ha + wetland_ha) / total_ha * 100)
    : 0;

  // Color del badge según severidad
  const getBadgeVariant = (percent: number) => {
    if (percent > 50) return 'destructive';
    if (percent > 25) return 'default';
    return 'secondary';
  };

  const apiBaseUrl = process.env.NEXT_PUBLIC_SAT_API_URL || 'http://localhost:8001';
  const fullUrl = `${apiBaseUrl}${thumbnailUrl}`;

  return (
    <button
      onClick={() => onOpenModal(fullUrl)}
      className="relative w-16 h-12 rounded overflow-hidden border border-slate-200 dark:border-slate-700 hover:border-primary-500 hover:ring-2 hover:ring-primary-500/20 transition-all group"
    >
      {isLoading && (
        <div className="absolute inset-0 bg-slate-200 dark:bg-slate-800 animate-pulse" />
      )}

      {hasError ? (
        <div className="absolute inset-0 bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
          <ImageIcon className="w-4 h-4 text-slate-400" />
        </div>
      ) : (
        <img
          src={fullUrl}
          alt={`Clasificación ${date}`}
          className="w-full h-full object-cover"
          onLoad={() => setIsLoading(false)}
          onError={() => {
            setIsLoading(false);
            setHasError(true);
          }}
        />
      )}

      {/* Badge de afectación */}
      <Badge
        variant={getBadgeVariant(affectedPercent)}
        className="absolute -bottom-1 -right-1 w-5 h-5 p-0 flex items-center justify-center text-[10px] font-bold"
      >
        {Math.round(affectedPercent)}%
      </Badge>

      {/* Icono de zoom al hover */}
      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <ImageIcon className="w-4 h-4 text-white" />
      </div>
    </button>
  );
}
