'use client';

import { useState } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';
import { format } from 'date-fns';
import { 
  ArrowUpDown, 
  FileText, 
  Building2, 
  Calendar
} from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { AnalyticsSnapshot } from '@/lib/data/analytics-loader';

interface DashboardProps {
  data: AnalyticsSnapshot;
}

export default function DashboardClientView({ data }: DashboardProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>({ key: 'normativas', direction: 'desc' });

  // Filter & Sort
  const filtered = data.municipalities.filter(m => 
    m.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sorted = [...filtered].sort((a, b) => {
    if (!sortConfig) return 0;
    
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let aVal: number | string = (a.stats as any)[sortConfig.key] || 0;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let bVal: number | string = (b.stats as any)[sortConfig.key] || 0;
    
    if (sortConfig.key === 'normativas') {
        aVal = a.stats.normativas;
        bVal = b.stats.normativas;
    }
    
    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const requestSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  // Aggregations for charts
  const topByVolume = [...data.municipalities]
    .sort((a, b) => b.stats.normativas - a.stats.normativas)
    .slice(0, 10)
    .map(m => ({ name: m.name, value: m.stats.normativas }));

  return (
    <div className="space-y-8">
      {/* KPI Header */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documentos Indexados</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.global.total_documents.toLocaleString('es-AR')}</div>
            <p className="text-xs text-muted-foreground">normativas procesadas</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Municipios Activos</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.global.total_municipalities}</div>
            <p className="text-xs text-muted-foreground">de 135 municipios</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Boletines Oficiales</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.global.total_bulletins.toLocaleString('es-AR')}</div>
            <p className="text-xs text-muted-foreground">archivos PDF fuente</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Top Municipios por Volumen</CardTitle>
             <CardDescription>Cantidad de normativas extraídas exitosamente</CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={topByVolume}>
                <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}`} />
                <Tooltip />
                <Bar dataKey="value" fill="#adfa1d" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Detalle por Municipio</CardTitle>
            <CardDescription>Explorador detallado de datos</CardDescription>
          </CardHeader>
          <CardContent>
             <div className="flex items-center py-4">
                <Input
                  placeholder="Buscar municipio..."
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  className="max-w-sm"
                />
              </div>
              <div className="rounded-md border h-[300px] overflow-auto">
                <table className="w-full text-sm">
                    <thead className="bg-muted/50 sticky top-0">
                        <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                            <th className="h-10 px-4 text-left font-medium cursor-pointer" onClick={() => requestSort('name')}>
                                Municipio <ArrowUpDown className="ml-2 h-4 w-4 inline" />
                            </th>
                            <th className="h-10 px-4 text-right font-medium cursor-pointer" onClick={() => requestSort('normativas')}>
                                Docs <ArrowUpDown className="ml-2 h-4 w-4 inline" />
                            </th>
                            <th className="h-10 px-4 text-right font-medium">Últ. Act.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sorted.map((m) => (
                            <tr key={m.name} className="border-b transition-colors hover:bg-muted/50">
                                <td className="p-4 font-medium">{m.name}</td>
                                <td className="p-4 text-right font-mono">{m.stats.normativas}</td>
                                <td className="p-4 text-right text-muted-foreground">
                                    {m.stats.last_date ? format(new Date(m.stats.last_date), 'dd/MM/yy') : '-'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
              </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
