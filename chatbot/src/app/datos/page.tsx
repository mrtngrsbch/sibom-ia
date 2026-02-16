'use client';

import { StatsCards } from '@/components/datos/StatsCards';
import { MunicipiosTable } from '@/components/datos/MunicipiosTable';
import { useEffect, useState } from 'react';
import { Loader2 } from '@/lib/icons';

interface MunicipioStats {
  municipio: string;
  url: string;
  cityId: number;
  tieneDatos: boolean;
  cantidadBoletines: number;
  primeraPublicacion: string | null;
  ultimaPublicacion: string | null;
}

interface GlobalStats {
  totalMunicipios: number;
  municipiosConDatos: number;
  municipiosSinDatos: number;
  totalBoletines: number;
  totalNormativas: number;
  municipios: MunicipioStats[];
}

/**
 * Página de datos y estadísticas de la plataforma
 * @description Muestra métricas, estadísticas y tabla detallada de municipios
 */
export default function DatosPage() {
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch('/api/municipios-stats');
        if (!response.ok) {
          throw new Error('Error al cargar estadísticas');
        }
        const data = await response.json();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
          Datos de la Plataforma
        </h1>
        <p className="text-slate-600 dark:text-slate-400">
          Estadísticas y métricas del Observatorio de Transparencia Municipal de Buenos Aires
        </p>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          <span className="ml-3 text-slate-600 dark:text-slate-400">
            Cargando datos...
          </span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">
            Error: {error}
          </p>
        </div>
      )}

      {stats && !loading && !error && (
        <>
          <StatsCards stats={stats} />
          <MunicipiosTable municipios={stats.municipios} />
        </>
      )}
    </div>
  );
}
