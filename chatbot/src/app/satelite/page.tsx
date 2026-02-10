'use client';

import { useEffect, useState } from 'react';
import { Satellite, AlertCircle, HelpCircle, Menu } from '@/lib/icons';
import { PartidaForm } from '@/components/satelite/PartidaForm';
import { ResultsPanel } from '@/components/satelite/ResultsPanel';
import { getSatAnalysisClient, type PartidoInfo, type AnalyzeRequest, type AnalyzeResponse } from '@/lib/sat-api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileDrawer } from '@/components/layout/MobileDrawer';
import { SatelliteAnalysisProvider, useSatelliteAnalysis } from '@/contexts/SatelliteAnalysisContext';

/**
 * Página principal de análisis satelital
 */
export default function SatelitePage() {
  const [partidos, setPartidos] = useState<PartidoInfo[]>([]);
  const [loadingPartidos, setLoadingPartidos] = useState(true);
  const [partidosError, setPartidosError] = useState<string | null>(null);

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const { analysis, setAnalysis, resetAnalysis } = useSatelliteAnalysis();
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const client = getSatAnalysisClient();

  // Cargar partidos al montar
  useEffect(() => {
    const fetchPartidos = async () => {
      try {
        setLoadingPartidos(true);
        const data = await client.getPartidos();
        setPartidos(data.partidos);
      } catch (error) {
        console.error('Error cargando partidos:', error);
        setPartidosError('No se pudo cargar la lista de partidos');
      } finally {
        setLoadingPartidos(false);
      }
    };

    fetchPartidos();
  }, []);

  // Polling para actualizar estado del análisis
  useEffect(() => {
    if (!taskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await client.getAnalysisStatus(taskId);
        setAnalysis(response);

        if (response.status === 'completed' || response.status === 'failed') {
          clearInterval(pollInterval);
          setLoading(false);
        }
      } catch (error) {
        console.error('Error en polling:', error);
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
        message: 'Análisis iniciado',
        total_images: 0,
      });
    } catch (error) {
      console.error('Error iniciando análisis:', error);
      setAnalysis({
        task_id: '',
        partida: request.partida,
        status: 'failed',
        progress: 0,
        message: 'Error al iniciar análisis',
        total_images: 0,
        error: error instanceof Error ? error.message : 'Error desconocido',
      });
      setLoading(false);
    }
  };

  const handleReset = () => {
    // Usar el método resetAnalysis del Context que incluye confirmación
    resetAnalysis();
  };

  return (
    <SatelliteAnalysisProvider>
      <div className="flex h-screen overflow-hidden">
        {/* Contenido principal */}
        <main className="flex flex-1 flex-col min-w-0">
          {/* Header */}
          <header className="flex h-16 items-center justify-between border-b border-slate-200 dark:border-slate-800 px-4 bg-white dark:bg-slate-900">
            <Header onMenuClick={() => setIsMobileMenuOpen(true)} />
            <Button variant="outline" asChild>
              <Link href="/satelite/ayuda">
                <HelpCircle className="w-4 h-4 mr-2" />
                Ayuda
              </Link>
            </Button>
          </header>

        {/* Área de contenido */}
        <div className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-950">
          <div className="container mx-auto p-6 space-y-8">
            {/* Título */}
            <div className="space-y-2">
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                Análisis Satelital
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                Detección de anegamiento y salinización usando imágenes Sentinel-2
              </p>
            </div>

            {/* Estado de error del servicio */}
            {partidosError && (
              <Card className="border-red-200 dark:border-red-800">
                <CardContent className="pt-6">
                  <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
                    <AlertCircle className="w-5 h-5" />
                    <p>{partidosError}</p>
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
                <ResultsPanel analysis={analysis} />

                {/* Botón para nuevo análisis */}
                {analysis.status === 'completed' || analysis.status === 'failed' ? (
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
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Información</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="font-medium mb-2">Fuente de datos</p>
                    <p className="text-slate-600 dark:text-slate-400">
                      Sentinel-2 L2A (MSI) - Resolución 10m
                    </p>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Proveedor</p>
                    <p className="text-slate-600 dark:text-slate-400">
                      Microsoft Planetary Computer (STAC)
                    </p>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Índices calculados</p>
                    <p className="text-slate-600 dark:text-slate-400">
                      NDWI, MNDWI, NDVI, NDMI, NDSI, Salinity
                    </p>
                  </div>
                  <div>
                    <p className="font-medium mb-2">Clasificación</p>
                    <p className="text-slate-600 dark:text-slate-400">
                      4 categorías: Agua, Humedal, Vegetación, Otros
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
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
    </SatelliteAnalysisProvider>
  );
}
