'use client';

import { useEffect, useState } from 'react';
import { Cloud, Droplets, Wind, Loader2, CloudOff, Sunrise, Sunset } from '@/lib/icons';

interface WeatherData {
  municipality: string;
  temperature: number;
  feelsLike: number;
  humidity: number;
  windSpeed: number;
  precipitation: number;
  weatherCode: number;
  description: string;
  emoji: string;
  timestamp: string;
  cached: boolean;
  isDay: boolean;
  sunrise?: string;
  sunset?: string;
}

interface WeatherBadgeProps {
  municipality: string | null;
  className?: string;
}

/**
 * Determina el gradiente de fondo según hora del día y condición climática
 */
function getBackgroundGradient(weatherCode: number, isDay: boolean, currentHour: number): string {
  // Amanecer (5-7 AM)
  if (currentHour >= 5 && currentHour < 7) {
    return 'from-orange-300 via-pink-300 to-purple-400';
  }

  // Atardecer (18-20 PM)
  if (currentHour >= 18 && currentHour < 20) {
    return 'from-orange-400 via-red-400 to-purple-500';
  }

  // Noche (20-5)
  if (!isDay || currentHour >= 20 || currentHour < 5) {
    // Noche despejada
    if (weatherCode <= 1) return 'from-indigo-900 via-purple-900 to-slate-900';
    // Noche nublada
    if (weatherCode <= 3) return 'from-slate-800 via-slate-700 to-slate-900';
    // Noche con lluvia/tormenta
    if (weatherCode >= 51) return 'from-slate-900 via-gray-800 to-slate-950';
    return 'from-slate-800 via-slate-700 to-slate-900';
  }

  // Día despejado
  if (weatherCode <= 1) {
    return 'from-blue-400 via-cyan-300 to-blue-300';
  }

  // Día parcialmente nublado
  if (weatherCode <= 3) {
    return 'from-blue-300 via-slate-200 to-gray-300';
  }

  // Día con lluvia
  if (weatherCode >= 51 && weatherCode <= 67) {
    return 'from-gray-400 via-slate-400 to-blue-400';
  }

  // Día con nieve
  if (weatherCode >= 71 && weatherCode <= 77) {
    return 'from-slate-200 via-blue-200 to-white';
  }

  // Tormenta
  if (weatherCode >= 95) {
    return 'from-gray-600 via-slate-700 to-gray-800';
  }

  // Default: día nublado
  return 'from-gray-300 via-slate-300 to-blue-300';
}

/**
 * Genera partículas animadas según condición climática
 */
function WeatherAnimation({ weatherCode }: { weatherCode: number }) {
  // Lluvia
  if (weatherCode >= 51 && weatherCode <= 67) {
    return (
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 30 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-0.5 h-8 bg-blue-200/30 animate-rain"
            style={{
              left: `${Math.random() * 100}%`,
              top: `-${Math.random() * 20}%`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${0.5 + Math.random() * 0.5}s`
            }}
          />
        ))}
      </div>
    );
  }

  // Nieve
  if (weatherCode >= 71 && weatherCode <= 77) {
    return (
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-white rounded-full animate-snow"
            style={{
              left: `${Math.random() * 100}%`,
              top: `-${Math.random() * 20}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${2 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>
    );
  }

  return null;
}

/**
 * Badge de clima con diseño estilo Yahoo Weather
 * @description Muestra el clima actual con fondo dinámico, animaciones y datos completos
 */
export function WeatherBadge({ municipality, className = '' }: WeatherBadgeProps) {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!municipality) {
      setWeather(null);
      setError(null);
      return;
    }

    const fetchWeather = async () => {
      setLoading(true);
      setError(null);

      try {
        const res = await fetch(`/api/weather?municipality=${encodeURIComponent(municipality)}`);

        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.error || 'Error obteniendo clima');
        }

        const data = await res.json();
        setWeather(data);
      } catch (err: any) {
        console.error('[WeatherBadge] Error:', err);
        setError(err.message);
        setWeather(null);
      } finally {
        setLoading(false);
      }
    };

    fetchWeather();

    // Actualizar cada 30 minutos
    const interval = setInterval(fetchWeather, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [municipality]);

  // No mostrar nada si no hay municipio
  if (!municipality) return null;

  // Loading state
  if (loading) {
    return (
      <div className={`flex items-center gap-2 p-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl ${className}`}>
        <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        <span className="text-sm text-slate-600 dark:text-slate-400">
          Cargando clima de {municipality}...
        </span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`flex items-center gap-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl ${className}`}>
        <CloudOff className="w-5 h-5 text-red-600 dark:text-red-400" />
        <span className="text-sm text-red-600 dark:text-red-400">
          No se pudo obtener el clima
        </span>
      </div>
    );
  }

  if (!weather) return null;

  // Determinar hora actual para gradiente
  const currentHour = new Date().getHours();
  const gradient = getBackgroundGradient(weather.weatherCode, weather.isDay, currentHour);

  return (
    <div className={`relative overflow-hidden rounded-2xl ${className}`}>
      {/* Fondo con gradiente dinámico */}
      <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-90`} />

      {/* Animaciones de clima */}
      <WeatherAnimation weatherCode={weather.weatherCode} />

      {/* Contenido */}
      <div className="relative z-10 p-6 text-white">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold mb-1 drop-shadow-lg">
              {weather.municipality}
            </h3>
            <p className="text-sm opacity-90 drop-shadow">
              {weather.description}
            </p>
          </div>
          <span className="text-6xl drop-shadow-lg">
            {weather.emoji}
          </span>
        </div>

        {/* Temperatura principal */}
        <div className="mb-6">
          <div className="flex items-baseline gap-2">
            <span className="text-7xl font-bold drop-shadow-lg">
              {weather.temperature}°
            </span>
            <span className="text-2xl opacity-80">C</span>
          </div>
          <p className="text-sm opacity-90 mt-1 drop-shadow">
            Sensación térmica: {weather.feelsLike}°C
          </p>
        </div>

        {/* Grid de detalles */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          {/* Humedad */}
          <div className="flex flex-col items-center p-3 bg-white/10 backdrop-blur-sm rounded-lg">
            <Droplets className="w-5 h-5 mb-1 opacity-90" />
            <span className="text-lg font-semibold">{weather.humidity}%</span>
            <span className="text-xs opacity-80">Humedad</span>
          </div>

          {/* Viento */}
          <div className="flex flex-col items-center p-3 bg-white/10 backdrop-blur-sm rounded-lg">
            <Wind className="w-5 h-5 mb-1 opacity-90" />
            <span className="text-lg font-semibold">{weather.windSpeed}</span>
            <span className="text-xs opacity-80">km/h</span>
          </div>

          {/* Precipitación */}
          <div className="flex flex-col items-center p-3 bg-white/10 backdrop-blur-sm rounded-lg">
            <Cloud className="w-5 h-5 mb-1 opacity-90" />
            <span className="text-lg font-semibold">{weather.precipitation}</span>
            <span className="text-xs opacity-80">mm</span>
          </div>
        </div>

        {/* Sunrise/Sunset si está disponible */}
        {(weather.sunrise || weather.sunset) && (
          <div className="flex items-center justify-around py-3 border-t border-white/20">
            {weather.sunrise && (
              <div className="flex items-center gap-2">
                <Sunrise className="w-4 h-4 opacity-80" />
                <span className="text-sm opacity-90">
                  {new Date(weather.sunrise).toLocaleTimeString('es-AR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            )}
            {weather.sunset && (
              <div className="flex items-center gap-2">
                <Sunset className="w-4 h-4 opacity-80" />
                <span className="text-sm opacity-90">
                  {new Date(weather.sunset).toLocaleTimeString('es-AR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-white/20">
          <p className="text-xs opacity-70 text-center">
            Datos de{' '}
            <a
              href="https://open-meteo.com"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:opacity-100 transition-opacity"
            >
              Open-Meteo
            </a>
            {weather.cached && ' (en caché)'}
          </p>
        </div>
      </div>
    </div>
  );
}
