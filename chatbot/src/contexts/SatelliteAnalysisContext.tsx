'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { AnalyzeResponse } from '@/lib/sat-api';

interface SatelliteAnalysisContextType {
  analysis: AnalyzeResponse | null;
  setAnalysis: (analysis: AnalyzeResponse | null) => void;
  resetAnalysis: () => void;
  taskId: string | null; // Agregar taskId al contexto
}

const SatelliteAnalysisContext = createContext<SatelliteAnalysisContextType | undefined>(undefined);

interface SatelliteAnalysisProviderProps {
  children: ReactNode;
}

/**
 * Provider para el contexto de análisis satelital
 * Gestiona el estado del análisis a nivel global para que persista durante toda la sesión
 */
export function SatelliteAnalysisProvider({ children }: SatelliteAnalysisProviderProps) {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null); // Agregar estado local de taskId

  // Cargar análisis guardado al montar
  useEffect(() => {
    const savedAnalysis = localStorage.getItem('satellite-analysis');
    if (savedAnalysis) {
      try {
        const parsed = JSON.parse(savedAnalysis);
        console.log('[SatelliteAnalysisContext] Cargando análisis guardado, taskId actual:', taskId);
        // Solo cargar si no hay un análisis activo (taskId es null)
        if (!taskId && parsed.status === 'completed' || parsed.status === 'failed') {
          setAnalysis(parsed);
          setTaskId(parsed.task_id); // Restaurar taskId también
          console.log('[SatelliteAnalysisContext] Análisis restaurado desde localStorage:', parsed.partida);
          // Limpiar localStorage después de cargar para evitar duplicados
          localStorage.removeItem('satellite-analysis');
        }
      } catch (error) {
        console.error('[SatelliteAnalysisContext] Error al cargar análisis guardado:', error);
      }
    }
  }, [taskId]); // Agregar taskId como dependencia

  // Guardar análisis en localStorage cuando se complete
  useEffect(() => {
    if (analysis && (analysis.status === 'completed' || analysis.status === 'failed')) {
      localStorage.setItem('satellite-analysis', JSON.stringify(analysis));
    }
  }, [analysis]);

  const resetAnalysis = () => {
    // Confirmar antes de limpiar el análisis
    if (window.confirm('¿Estás seguro de que quieres crear un nuevo análisis? El análisis anterior se perderá.')) {
      setAnalysis(null);
      setTaskId(null); // Limpiar taskId también
      localStorage.removeItem('satellite-analysis');
    }
  };

  return (
    <SatelliteAnalysisContext.Provider value={{ analysis, setAnalysis, resetAnalysis, taskId }}>
      {children}
    </SatelliteAnalysisContext.Provider>
  );
}

/**
 * Hook para usar el contexto de análisis satelital
 */
export function useSatelliteAnalysis() {
  const context = useContext(SatelliteAnalysisContext);
  if (!context) {
    throw new Error('useSatelliteAnalysis debe ser usado dentro de SatelliteAnalysisProvider');
  }
  return context;
}
