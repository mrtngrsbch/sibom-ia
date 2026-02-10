'use client';

import { X, Download, ZoomIn } from '@/lib/icons';
import { Button } from '@/components/ui/button';
import { useState, useEffect } from 'react';

interface ImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
  title: string;
  description?: string;
  date?: string;
}

/**
 * Modal para visualización de imágenes satelitales a pantalla completa.
 */
export function ImageModal({
  isOpen,
  onClose,
  imageUrl,
  title,
  description,
  date,
}: ImageModalProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [imageError, setImageError] = useState(false);

  // Listener para cerrar modal con tecla Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleDownload = () => {
    // Crear un link temporal para descargar la imagen
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `${title.replace(/\s+/g, '_')}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  const handleImageError = () => {
    setIsLoading(false);
    setImageError(true);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-w-6xl w-full mx-4 bg-white dark:bg-slate-900 rounded-xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white">{title}</h3>
            {description && (
              <p className="text-sm text-slate-600 dark:text-slate-400">{description}</p>
            )}
            {date && (
              <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                Fecha: {new Date(date).toLocaleDateString('es-AR', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric',
                })}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownload}
              className="gap-2"
            >
              <Download className="w-4 h-4" />
              Descargar
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="gap-2"
            >
              <X className="w-4 h-4" />
              Cerrar
            </Button>
          </div>
        </div>

        {/* Image Container */}
        <div className="relative flex items-center justify-center bg-slate-100 dark:bg-slate-950 min-h-[400px] max-h-[calc(100vh-200px)] overflow-auto">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
                <p className="text-sm text-slate-500 dark:text-slate-400">Cargando imagen...</p>
              </div>
            </div>
          )}

          {imageError ? (
            <div className="flex flex-col items-center gap-3 p-8">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                <X className="w-8 h-8 text-red-500" />
              </div>
              <p className="text-slate-600 dark:text-slate-400">No se pudo cargar la imagen</p>
            </div>
          ) : (
            <img
              src={imageUrl}
              alt={title}
              className="max-w-full max-h-[calc(100vh-200px)] object-contain"
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          )}
        </div>

        {/* Footer con instrucciones */}
        <div className="p-3 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-700">
          <p className="text-xs text-center text-slate-500 dark:text-slate-400">
            <ZoomIn className="w-3 h-3 inline mr-1" />
            Presione ESC o haga clic fuera para cerrar
          </p>
        </div>
      </div>
    </div>
  );
}
