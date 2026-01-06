'use client';

import { useEffect, useState } from 'react';
import {
  MessageSquare,
  Scale,
  BarChart3,
  RefreshCw,
  Info,
  HelpCircle
} from '@/lib/icons';
import { WeatherBadge } from '@/components/chat/WeatherBadge';

/**
 * Tipos de estadísticas
 */
interface DatabaseStats {
  totalDocuments: number;
  municipalities: number;
  municipalityList: string[];
  lastUpdated: string | null;
}

/**
 * Formatea una fecha ISO a DD/MM/YYYY
 */
function formatDate(isoDate: string): string {
  const date = new Date(isoDate);
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

interface SidebarProps {
  showNavigation?: boolean;
  currentMunicipality?: string | null;
}

/**
 * Sidebar de navegación
 * @description Panel lateral simplificado con info del sistema
 */
export function Sidebar({ showNavigation = true, currentMunicipality = null }: SidebarProps) {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastKnownUpdate, setLastKnownUpdate] = useState<string | null>(null);

  // Función para obtener estadísticas
  const fetchStats = async (invalidateCache = false) => {
    try {
      if (invalidateCache) {
        setRefreshing(true);
      }

      // Si se solicita invalidar cache, llamar al endpoint de refresh primero
      if (invalidateCache) {
        await fetch('/api/refresh', { method: 'POST' });
        console.log('[Sidebar] Cache invalidado');
      }

      // Agregar timestamp para evitar cache del navegador cuando se invalida
      const url = invalidateCache
        ? `/api/stats?_=${Date.now()}`
        : '/api/stats';

      const response = await fetch(url, {
        cache: invalidateCache ? 'no-store' : 'default'
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);

        // Si hay nueva fecha de actualización, actualizar
        if (data.lastUpdated !== lastKnownUpdate) {
          setLastKnownUpdate(data.lastUpdated);
          console.log('[Sidebar] Datos actualizados:', {
            totalDocuments: data.totalDocuments,
            municipalities: data.municipalities,
            lastUpdated: data.lastUpdated
          });
        }
      }
    } catch (error) {
      console.error('[Sidebar] Error fetching stats:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Función para refrescar manualmente
  const handleManualRefresh = async () => {
    setRefreshing(true);

    try {
      // 1. Intentar regenerar índice si estamos en local
      const reindexResponse = await fetch('/api/reindex', { method: 'POST' });

      if (reindexResponse.ok) {
        const reindexData = await reindexResponse.json();
        console.log('[Sidebar] Índice regenerado:', reindexData);
      } else {
        // Si falla (ej: estamos en producción), no es crítico
        console.log('[Sidebar] Reindexación no disponible (probablemente en producción)');
      }
    } catch (error) {
      console.log('[Sidebar] No se pudo reindexar:', error);
    }

    // 2. Actualizar datos con cache invalidado
    await fetchStats(true);
  };

  // Cargar datos iniciales
  useEffect(() => {
    fetchStats();
  }, []);

  // Polling cada 5 minutos para detectar cambios
  // Reducción esperada: 90% en requests (5,760 → 576 req/día)
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        // Verificar si hay actualizaciones sin invalidar cache
        const response = await fetch('/api/refresh');
        if (response.ok) {
          const data = await response.json();

          // Si cambió la fecha de actualización, recargar datos invalidando cache
          if (data.lastUpdated && data.lastUpdated !== lastKnownUpdate) {
            console.log('[Sidebar] Detectado cambio en índice, recargando...');
            await fetchStats(true);
          }
        }
      } catch (error) {
        console.error('[Sidebar] Error en polling:', error);
      }
    }, 5 * 60 * 1000); // Cada 5 minutos (300000ms)

    return () => clearInterval(interval);
  }, [lastKnownUpdate]);

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900">
      {/* Logo */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center flex-shrink-0">
            <Scale className="w-5 h-5 text-white" />
          </div>
          <div className="min-w-0">
            <h2 className="font-semibold text-slate-900 dark:text-white truncate">
              SIBOM Chat
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Observatorio de transparencia municipal de la Provincia de Buenos Aires
            </p>
          </div>
        </div>
      </div>

      {/* Navegación */}
      <nav className="flex-1 overflow-y-auto p-4">
        {showNavigation && (
          <ul className="space-y-2 mb-6">
            <li>
              <a
                href="/"
                className="flex items-center gap-3 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <MessageSquare className="w-5 h-5" />
                <span>Chat Legal</span>
              </a>
            </li>
            <li>
              <a
                href="/datos"
                className="flex items-center gap-3 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <BarChart3 className="w-5 h-5" />
                <span>Datos</span>
              </a>
            </li>
            <li>
              <a
                href="/proyecto"
                className="flex items-center gap-3 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Info className="w-5 h-5" />
                <span>Proyecto</span>
              </a>
            </li>
            <li>
              <a
                href="/faq"
                className="flex items-center gap-3 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              >
                <HelpCircle className="w-5 h-5" />
                <span>FAQ</span>
              </a>
            </li>
          </ul>
        )}

        {/* WeatherBadge - Solo si hay municipio seleccionado */}
        {currentMunicipality && (
          <div className="mb-4">
            <WeatherBadge municipality={currentMunicipality} />
          </div>
        )}

        {/* Info de municipios disponibles - Todos */}
        {stats && stats.municipalityList.length > 0 && (
          <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">
              Municipios disponibles ({stats.municipalityList.length}):
            </p>
            <div className="flex flex-wrap gap-1 max-h-48 overflow-y-auto">
              {stats.municipalityList.map((m) => (
                <span
                  key={m}
                  className="text-xs px-2 py-0.5 bg-white dark:bg-slate-700 rounded text-slate-600 dark:text-slate-300"
                >
                  {m}
                </span>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800">
        <div className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400 space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>
              {loading ? 'Cargando...' : `${stats?.totalDocuments || 0} documentos`}
            </span>
          </div>
          {stats?.lastUpdated && (
            <p className="text-xs text-slate-400 dark:text-slate-500">
              Última actualización: {formatDate(stats.lastUpdated)}
            </p>
          )}
          {/* Botón de actualización manual */}
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 text-xs px-2 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed w-full justify-center"
            title="Forzar actualización de datos"
          >
            <RefreshCw className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Actualizando...' : 'Actualizar datos'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
