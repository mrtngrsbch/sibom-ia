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
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] useEffect de carga ejecutado');
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] taskId actual:', taskId);
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] analysis actual:', analysis);

    const savedAnalysis = localStorage.getItem('satellite-analysis');
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] localStorage.getItem("satellite-analysis"):', savedAnalysis);

    if (savedAnalysis) {
      try {
        const parsed = JSON.parse(savedAnalysis);
        console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Análisis guardado parseado:', parsed);
        console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] parsed.status:', parsed.status);
        console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] parsed.task_id:', parsed.task_id);
        console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] parsed.partida:', parsed.partida);

        // Solo cargar si no hay un análisis activo (taskId es null)
        if (!taskId && (parsed.status === 'completed' || parsed.status === 'failed')) {
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Condición cumplida: !taskId && (completed || failed)');
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Restaurando análisis...');
          setAnalysis(parsed);
          setTaskId(parsed.task_id); // Restaurar taskId también
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Análisis restaurado desde localStorage:', parsed.partida);
          // Limpiar localStorage después de cargar para evitar duplicados
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Eliminando análisis de localStorage...');
          localStorage.removeItem('satellite-analysis');
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] localStorage.removeItem ejecutado');
        } else {
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Condición NO cumplida');
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] !taskId:', !taskId);
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] parsed.status === "completed":', parsed.status === 'completed');
          console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] parsed.status === "failed":', parsed.status === 'failed');
        }
      } catch (error) {
        console.error('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Error al cargar análisis guardado:', error);
      }
    } else {
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] No hay análisis guardado en localStorage');
    }
  }, [taskId, analysis]); // Agregar taskId y analysis como dependencias

  // Guardar análisis en localStorage cuando se complete
  useEffect(() => {
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] useEffect de guardado ejecutado');
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] analysis:', analysis);

    if (analysis && (analysis.status === 'completed' || analysis.status === 'failed')) {
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Condición cumplida: analysis && (completed || failed)');
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Guardando análisis en localStorage...');
      localStorage.setItem('satellite-analysis', JSON.stringify(analysis));
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Análisis guardado en localStorage:', analysis.partida);
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] localStorage.setItem ejecutado');
    } else {
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Condición NO cumplida para guardar');
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] analysis:', analysis);
      if (analysis) {
        console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] analysis.status:', analysis.status);
      }
    }
  }, [analysis]);

  const resetAnalysis = () => {
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] resetAnalysis llamado');
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] analysis actual:', analysis);
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] taskId actual:', taskId);
    console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] localStorage.getItem("satellite-analysis"):', localStorage.getItem('satellite-analysis'));

    // Confirmar antes de limpiar el análisis
    if (window.confirm('¿Estás seguro de que quieres crear un nuevo análisis? El análisis anterior se perderá.')) {
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Usuario confirmó reset');
      setAnalysis(null);
      setTaskId(null); // Limpiar taskId también
      localStorage.removeItem('satellite-analysis');
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Análisis reseteado');
    } else {
      console.log('🔍 [SAT-DEBUG] [SatelliteAnalysisContext] Usuario canceló reset');
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
