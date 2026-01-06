'use client';

import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';
import { StatsCards } from '@/components/datos/StatsCards';
import { MunicipiosTable } from '@/components/datos/MunicipiosTable';
import { useEffect, useState } from 'react';
import { Loader2 } from '@/lib/icons';

interface GlobalStats {
  totalMunicipios: number;
  municipiosConDatos: number;
  municipiosSinDatos: number;
  totalDocumentos: number;
  municipios: any[];
}

/**
 * Página de datos y estadísticas de la plataforma
 * @description Muestra métricas, estadísticas y tabla detallada de municipios
 */
export default function DatosPage() {
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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
    <div className="flex h-screen overflow-hidden">
      {/* Contenido principal */}
      <main className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 bg-white dark:bg-slate-900">
          <Header onMenuClick={() => setIsMobileMenuOpen(true)} />
        </header>

        {/* Área de contenido */}
        <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950">
          <div className="container mx-auto p-6 space-y-8">
            {/* Título */}
            <div className="space-y-2">
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                Datos de la Plataforma
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                Estadísticas y métricas del Observatorio de Transparencia Municipal de Buenos Aires
              </p>
            </div>

            {/* Estado de carga */}
            {loading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
                <span className="ml-3 text-slate-600 dark:text-slate-400">
                  Cargando datos...
                </span>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="text-red-800 dark:text-red-200">
                  Error: {error}
                </p>
              </div>
            )}

            {/* Datos */}
            {stats && !loading && !error && (
              <>
                {/* Tarjetas de estadísticas */}
                <StatsCards stats={stats} />

                {/* Tabla de municipios */}
                <MunicipiosTable municipios={stats.municipios} />
              </>
            )}
          </div>
        </div>
      </main>

      {/* Panel lateral - Desktop (a la derecha) */}
      <aside className="hidden lg:flex w-72 flex-col border-l border-slate-200 dark:border-slate-800">
        <Sidebar />
      </aside>

      {/* Panel lateral - Mobile (Drawer desde la derecha) */}
      <MobileDrawer isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)}>
        <Sidebar />
      </MobileDrawer>
    </div>
  );
}
