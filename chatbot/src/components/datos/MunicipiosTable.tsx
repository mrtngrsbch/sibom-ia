'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ExternalLink } from '@/lib/icons';
import { useState } from 'react';

interface MunicipioStats {
  municipio: string;
  url: string;
  cityId: number;
  tieneDatos: boolean;
  cantidadBoletines: number;
  primeraPublicacion: string | null;
  ultimaPublicacion: string | null;
}

interface MunicipiosTableProps {
  municipios: MunicipioStats[];
}

/**
 * Componente de tabla de municipios
 * @description Muestra tabla detallada con estadísticas de cada municipio
 */
export function MunicipiosTable({ municipios }: MunicipiosTableProps) {
  const [filterStatus, setFilterStatus] = useState<'all' | 'with-data' | 'without-data'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Filtrar municipios
  const filteredMunicipios = municipios.filter((m) => {
    // Filtro por búsqueda
    const matchesSearch = m.municipio.toLowerCase().includes(searchTerm.toLowerCase());

    // Filtro por estado
    let matchesStatus = true;
    if (filterStatus === 'with-data') {
      matchesStatus = m.tieneDatos;
    } else if (filterStatus === 'without-data') {
      matchesStatus = !m.tieneDatos;
    }

    return matchesSearch && matchesStatus;
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Municipios de la Provincia de Buenos Aires</CardTitle>
        <CardDescription>
          Detalle completo de municipios con fechas de publicación y cantidad de documentos
        </CardDescription>

        {/* Filtros y búsqueda */}
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <input
            type="text"
            placeholder="Buscar municipio..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 px-4 py-2 border border-slate-200 dark:border-slate-800 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <div className="flex gap-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterStatus === 'all'
                  ? 'bg-primary-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              Todos
            </button>
            <button
              onClick={() => setFilterStatus('with-data')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterStatus === 'with-data'
                  ? 'bg-green-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              Con datos
            </button>
            <button
              onClick={() => setFilterStatus('without-data')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterStatus === 'without-data'
                  ? 'bg-orange-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              Sin datos
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="rounded-md border border-slate-200 dark:border-slate-800">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[300px]">Municipio</TableHead>
                <TableHead className="text-center">Estado</TableHead>
                <TableHead className="text-center">Documentos</TableHead>
                <TableHead className="text-center">Primera Publicación</TableHead>
                <TableHead className="text-center">Última Publicación</TableHead>
                <TableHead className="text-center">Enlace</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredMunicipios.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                    No se encontraron municipios con los filtros aplicados
                  </TableCell>
                </TableRow>
              ) : (
                filteredMunicipios.map((municipio) => (
                  <TableRow key={municipio.cityId}>
                    <TableCell className="font-medium">
                      {municipio.municipio}
                    </TableCell>
                    <TableCell className="text-center">
                      {municipio.tieneDatos ? (
                        <Badge variant="success">Con datos</Badge>
                      ) : (
                        <Badge variant="warning">Sin datos</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {municipio.tieneDatos ? (
                        <span className="font-semibold text-slate-900 dark:text-white">
                          {municipio.cantidadBoletines}
                        </span>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      {municipio.primeraPublicacion || (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center text-sm">
                      {municipio.ultimaPublicacion || (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <a
                        href={municipio.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Resumen de resultados */}
        <div className="mt-4 text-sm text-slate-500 dark:text-slate-400">
          Mostrando {filteredMunicipios.length} de {municipios.length} municipios
        </div>
      </CardContent>
    </Card>
  );
}
