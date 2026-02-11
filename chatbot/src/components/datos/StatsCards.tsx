'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Building2, CheckCircle2, XCircle } from '@/lib/icons';

interface GlobalStats {
  totalMunicipios: number;
  municipiosConDatos: number;
  municipiosSinDatos: number;
  totalDocumentos: number;
}

interface StatsCardsProps {
  stats: {
    totalMunicipios: number;
    municipiosConDatos: number;
    municipiosSinDatos: number;
    totalDocumentos: number;
  };
}

/**
 * Componente de tarjetas de estadísticas
 * @description Muestra métricas principales en tarjetas visuales
 */
export function StatsCards({ stats }: StatsCardsProps) {
  const porcentajeConDatos = Math.round(
    (stats.municipiosConDatos / stats.totalMunicipios) * 100
  );

  const cards = [
    {
      title: 'Total Municipios',
      value: stats.totalMunicipios,
      icon: Building2,
      description: 'Municipios registrados en la plataforma',
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
    },
    {
      title: 'Municipios con Datos',
      value: stats.municipiosConDatos,
      icon: CheckCircle2,
      description: `${porcentajeConDatos}% del total`,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
    },
    {
      title: 'Municipios sin Datos',
      value: stats.municipiosSinDatos,
      icon: XCircle,
      description: `${100 - porcentajeConDatos}% del total`,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
    },
    {
      title: 'Total Documentos',
      value: stats.totalDocumentos.toLocaleString('es-AR'),
      icon: FileText,
      description: 'Boletines oficiales recopilados',
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.title} className="overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                {card.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${card.bgColor}`}>
                <Icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                {card.value}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                {card.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
