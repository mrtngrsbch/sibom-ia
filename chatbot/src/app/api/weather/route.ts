/**
 * weather/route.ts
 *
 * API Route para obtener datos del clima de un municipio usando Open-Meteo.
 * Utiliza coordenadas pre-almacenadas para evitar ambigüedades en geocoding.
 *
 * @version 1.0.0
 * @created 2026-01-03
 * @author Kilo Code
 *
 * @dependencies
 *   - Open-Meteo API (libre, sin API key)
 */

import { getMunicipalityCoords, getAllMunicipalityNames } from '@/lib/data/municipalities-coords';

/**
 * Cache de clima (30 minutos de TTL)
 */
interface WeatherCacheEntry {
  data: any;
  timestamp: number;
}

const weatherCache = new Map<string, WeatherCacheEntry>();
const CACHE_TTL = 30 * 60 * 1000; // 30 minutos

/**
 * Mapeo de códigos de clima Open-Meteo a descripciones en español
 */
function getWeatherDescription(weatherCode: number): string {
  const weatherCodes: Record<number, string> = {
    0: 'Despejado',
    1: 'Mayormente despejado',
    2: 'Parcialmente nublado',
    3: 'Nublado',
    45: 'Niebla',
    48: 'Niebla con escarcha',
    51: 'Llovizna ligera',
    53: 'Llovizna moderada',
    55: 'Llovizna intensa',
    56: 'Llovizna helada ligera',
    57: 'Llovizna helada intensa',
    61: 'Lluvia ligera',
    63: 'Lluvia moderada',
    65: 'Lluvia intensa',
    66: 'Lluvia helada ligera',
    67: 'Lluvia helada intensa',
    71: 'Nevada ligera',
    73: 'Nevada moderada',
    75: 'Nevada intensa',
    77: 'Nieve granulada',
    80: 'Chubascos ligeros',
    81: 'Chubascos moderados',
    82: 'Chubascos intensos',
    85: 'Chubascos de nieve ligeros',
    86: 'Chubascos de nieve intensos',
    95: 'Tormenta',
    96: 'Tormenta con granizo ligero',
    99: 'Tormenta con granizo intenso'
  };

  return weatherCodes[weatherCode] || 'Desconocido';
}

/**
 * Obtiene emoji representativo según el código de clima y si es de día/noche
 */
function getWeatherEmoji(weatherCode: number, isDay: boolean): string {
  // Despejado
  if (weatherCode === 0 || weatherCode === 1) {
    return isDay ? '☀️' : '🌙';  // Sol de día, luna de noche
  }

  // Parcialmente nublado
  if (weatherCode === 2 || weatherCode === 3) {
    return isDay ? '⛅' : '☁️';  // Nube con sol de día, solo nube de noche
  }

  // Niebla
  if (weatherCode >= 45 && weatherCode <= 48) return '🌫️';

  // Lluvia
  if (weatherCode >= 51 && weatherCode <= 67) return '🌧️';

  // Nieve
  if (weatherCode >= 71 && weatherCode <= 77) return '❄️';

  // Chubascos
  if (weatherCode >= 80 && weatherCode <= 82) return '🌦️';

  // Chubascos de nieve
  if (weatherCode >= 85 && weatherCode <= 86) return '🌨️';

  // Tormenta
  if (weatherCode >= 95) return '⛈️';

  return isDay ? '🌤️' : '☁️';
}

/**
 * API Route para clima
 * @route GET /api/weather?municipality=NombreMunicipio
 */
export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const municipalityName = searchParams.get('municipality');

    if (!municipalityName) {
      return new Response(
        JSON.stringify({ error: 'Falta parámetro: municipality' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verificar cache
    const cacheKey = municipalityName;
    const cached = weatherCache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp) < CACHE_TTL) {
      console.log(`[Weather] Cache hit para ${municipalityName}`);
      return new Response(
        JSON.stringify({ ...cached.data, cached: true }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Normalizar el nombre del municipio (case-insensitive, sin tildes)
    const normalizeName = (name: string) => {
      return name.toLowerCase()
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // Eliminar tildes
        .trim();
    };

    // Obtener coordenadas desde tabla local (evitar geocoding)
    let coords = getMunicipalityCoords(municipalityName);

    // Si no encuentra, intentar coincidencia fuzzy (case-insensitive, sin tildes)
    if (!coords) {
      const allNames = getAllMunicipalityNames();
      const normalizedInput = normalizeName(municipalityName);

      for (const name of allNames) {
        if (normalizeName(name) === normalizedInput) {
          console.log(`[Weather] Coincidencia fuzzy: "${municipalityName}" → "${name}"`);
          coords = getMunicipalityCoords(name);
          break;
        }
      }
    }

    if (!coords) {
      console.log(`[Weather] Municipio NO encontrado: "${municipalityName}"`);
      return new Response(
        JSON.stringify({
          error: 'Municipio no encontrado en la base de datos',
          municipality: municipalityName
        }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    console.log(`[Weather] Consultando clima para ${municipalityName} (${coords.latitude}, ${coords.longitude})`);

    // Llamar a Open-Meteo API (incluyendo is_day, sunrise, sunset)
    const weatherRes = await fetch(
      `https://api.open-meteo.com/v1/forecast?` +
      `latitude=${coords.latitude}&` +
      `longitude=${coords.longitude}&` +
      `current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,is_day&` +
      `daily=sunrise,sunset&` +
      `timezone=America/Argentina/Buenos_Aires&` +
      `forecast_days=1`,
      {
        headers: {
          'User-Agent': 'SIBOM-Assistant/1.0 (Education)'
        }
      }
    );

    if (!weatherRes.ok) {
      throw new Error(`Open-Meteo API error: ${weatherRes.status}`);
    }

    const weatherData = await weatherRes.json();
    const current = weatherData.current;
    const daily = weatherData.daily;

    // Construir respuesta
    const isDay = current.is_day === 1;
    const response = {
      municipality: municipalityName,
      temperature: Math.round(current.temperature_2m),
      feelsLike: Math.round(current.apparent_temperature),
      humidity: current.relative_humidity_2m,
      windSpeed: Math.round(current.wind_speed_10m),
      precipitation: current.precipitation || 0,
      weatherCode: current.weather_code,
      description: getWeatherDescription(current.weather_code),
      emoji: getWeatherEmoji(current.weather_code, isDay),
      isDay,
      sunrise: daily?.sunrise?.[0],
      sunset: daily?.sunset?.[0],
      timestamp: new Date().toISOString(),
      cached: false
    };

    // Guardar en cache
    weatherCache.set(cacheKey, {
      data: response,
      timestamp: Date.now()
    });

    console.log(`[Weather] Clima obtenido para ${municipalityName}: ${response.temperature}°C - ${response.description}`);

    return new Response(
      JSON.stringify(response),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );

  } catch (error: any) {
    console.error('[Weather] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Error obteniendo datos del clima',
        details: error.message
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
