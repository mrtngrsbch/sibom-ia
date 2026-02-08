'use client';

import { useEffect, useState } from 'react';
import { Satellite, AlertCircle } from '@/lib/icons';
import { PartidaForm } from '@/components/satelite/PartidaForm';
import { ResultsPanel } from '@/components/satelite/ResultsPanel';
import { getSatAnalysisClient, type PartidoInfo, type AnalyzeRequest, type AnalyzeResponse } from '@/lib/sat-api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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

  // Cargar partidos al montar
  useEffect(() => {
    const fetchPartidos = async () => {
      try {
        console.log('[DEBUG] SatelitePage - Iniciando fetchPartidos()');
        console.log('[DEBUG] SatelitePage - client baseUrl:', (client as any).baseUrl);
        setLoadingPartidos(true);
        const data = await client.getPartidos();
        console.log('[DEBUG] SatelitePage - Partidos cargados:', data.partidos.length);
        setPartidos(data.partidos);
      } catch (error) {
        console.error('[DEBUG] SatelitePage - Error cargando partidos:', error);
        console.error('[DEBUG] SatelitePage - Error name:', error instanceof Error ? error.name : 'unknown');
        console.error('[DEBUG] SatelitePage - Error message:', error instanceof Error ? error.message : 'unknown');
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
              Detección de anegamiento y salinización usando imágenes Sentinel-2
            </p>
          </div>
        </div>
      </div>

      {/* Estado de error del servicio */}
      {partidosError && (
        <Card className="mb-6 border-red-200 dark:border-red-800">
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
          <ResultsPanel analysis={analysis} taskId={taskId} />

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
      <Card className="mt-8">
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
  );
}
