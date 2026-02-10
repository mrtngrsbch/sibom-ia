'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { AnalyzeResponse } from '@/lib/sat-api';

interface SatelliteAnalysisContextType {
  analysis: AnalyzeResponse | null;
  setAnalysis: (analysis: AnalyzeResponse | null) => void;
  resetAnalysis: () => void;
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

  // Cargar análisis guardado al montar
  useEffect(() => {
    const savedAnalysis = localStorage.getItem('satellite-analysis');
    if (savedAnalysis) {
      try {
        const parsed = JSON.parse(savedAnalysis);
        // Solo cargar si no hay un análisis activo
        if (parsed && (parsed.status === 'completed' || parsed.status === 'failed')) {
          setAnalysis(parsed);
          console.log('[SatelliteAnalysisContext] Análisis restaurado desde localStorage:', parsed.partida);
          // Limpiar localStorage después de cargar para evitar duplicados
          localStorage.removeItem('satellite-analysis');
        }
      } catch (error) {
        console.error('[SatelliteAnalysisContext] Error al cargar análisis guardado:', error);
      }
    }
  }, []);

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
      localStorage.removeItem('satellite-analysis');
    }
  };

  return (
    <SatelliteAnalysisContext.Provider value={{ analysis, setAnalysis, resetAnalysis }}>
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
