'use client';

import { useState } from 'react';
import { Satellite, Search } from '@/lib/icons';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import type { PartidoInfo, AnalyzeRequest } from '@/lib/types';

interface PartidaFormProps {
  partidos: PartidoInfo[];
  onSubmit: (request: AnalyzeRequest) => void;
  loading?: boolean;
}

/**
 * Formulario para análisis de parcela catastral
 */
export function PartidaForm({ partidos, onSubmit, loading = false }: PartidaFormProps) {
  const [partido, setPartido] = useState<string>('002');
  const [partida, setPartida] = useState<string>('4606');
  const [years, setYears] = useState<number>(2);
  const [samplesPerYear, setSamplesPerYear] = useState<number>(4);
  const [maxClouds, setMaxClouds] = useState<number>(20);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validar
    if (!partida || !partida.trim()) {
      return;
    }

    // Construir request con código de partido + partida
    const partidaCompleta = `${partido}${partida.padStart(6, '0')}`;

    onSubmit({
      partida: partidaCompleta,
      years,
      samples_per_year: samplesPerYear,
      max_clouds: maxClouds,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Satellite className="w-5 h-5" />
          Parámetros de Búsqueda
        </CardTitle>
        <CardDescription>
          Ingresa la partida catastral ARBA para analizar anegamiento y salinización
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Partido y Partida */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="partido">Partido / Municipio</Label>
              <Select value={partido} onValueChange={setPartido}>
                <SelectTrigger id="partido">
                  <SelectValue placeholder="Seleccionar partido" />
                </SelectTrigger>
                <SelectContent>
                  {partidos.map((p) => (
                    <SelectItem key={p.codigo} value={p.codigo}>
                      {p.codigo} - {p.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="partida">Número de Partida</Label>
              <Input
                id="partida"
                type="text"
                value={partida}
                onChange={(e) => setPartida(e.target.value)}
                placeholder="Ej: 4606"
                pattern="[0-9]*"
                inputMode="numeric"
              />
              <p className="text-xs text-slate-500">
                Formato final: <strong>{partido}-{partida.padStart(6, '0')}</strong>
              </p>
            </div>
          </div>

          {/* Años de histórico */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="years">Años de histórico</Label>
              <span className="text-sm text-slate-500">{years} años</span>
            </div>
            <Slider
              id="years"
              min={1}
              max={10}
              step={1}
              value={[years]}
              onValueChange={(v) => setYears(v[0])}
              className="w-full"
            />
            <p className="text-xs text-slate-500">
              Período a analizar (1-10 años) desde el año actual
            </p>
          </div>

          {/* Imágenes por año */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="samples">Imágenes por año</Label>
              <span className="text-sm text-slate-500">
                {samplesPerYear === 1 ? 'Anual' :
                 samplesPerYear === 2 ? 'Semestral' :
                 samplesPerYear === 4 ? 'Trimestral' :
                 samplesPerYear === 6 ? 'Bimestral' :
                 samplesPerYear === 12 ? 'Mensual' : `${samplesPerYear}/año`}
              </span>
            </div>
            <Slider
              id="samples"
              min={1}
              max={12}
              step={1}
              value={[samplesPerYear]}
              onValueChange={(v) => setSamplesPerYear(v[0])}
              className="w-full"
            />
            <p className="text-xs text-slate-500">
              Total de imágenes: <strong>{years * samplesPerYear}</strong>
            </p>
          </div>

          {/* Máximo % de nubes */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label htmlFor="clouds">Máximo % de nubes</Label>
              <span className="text-sm text-slate-500">{maxClouds}%</span>
            </div>
            <Slider
              id="clouds"
              min={0}
              max={100}
              step={5}
              value={[maxClouds]}
              onValueChange={(v) => setMaxClouds(v[0])}
              className="w-full"
            />
            <p className="text-xs text-slate-500">
              Menor = más restrictivo (mayor calidad de imagen)
            </p>
          </div>

          {/* Botón de análisis */}
          <Button
            type="submit"
            disabled={loading || !partida}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Search className="w-4 h-4 mr-2 animate-spin" />
                Analizando...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Analizar Parcela
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
