'use client';

import { useEffect, useState } from 'react';
import {
  MessageSquare,
  Scale
} from 'lucide-react';

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

/**
 * Sidebar de navegación
 * @description Panel lateral simplificado con info del sistema
 */
export function Sidebar() {
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch('/api/stats');
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

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
              SIBOM IA
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Asistente Municipal
            </p>
          </div>
        </div>
      </div>

      {/* Navegación - Solo Chat */}
      <nav className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-1">
          <li>
            <a
              href="/"
              className="flex items-center gap-3 px-3 py-2 text-sm text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 rounded-lg"
            >
              <MessageSquare className="w-5 h-5" />
              <span>Chat Legal</span>
              <span className="ml-auto px-2 py-0.5 text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded-full">
                Activo
              </span>
            </a>
          </li>
        </ul>

        {/* Info de municipios disponibles - Todos */}
        {stats && stats.municipalityList.length > 0 && (
          <div className="mt-6 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
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
        <div className="px-3 py-2 text-sm text-slate-500 dark:text-slate-400 space-y-1">
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
        </div>
      </div>
    </div>
  );
}
