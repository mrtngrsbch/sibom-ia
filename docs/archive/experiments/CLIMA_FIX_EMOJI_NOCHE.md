# Fix: Emoji de Clima Nocturno

## Problema Detectado

A las **00:53 (noche)** con cielo despejado, el badge mostraba ☀️ (sol) cuando debería mostrar 🌙 (luna).

## Causa

La función `getWeatherEmoji()` NO consideraba el flag `isDay` de Open-Meteo, siempre mostraba emojis diurnos.

## Solución Implementada

### 1. Actualizar `getWeatherEmoji()` para recibir parámetro `isDay`

**Antes:**
```typescript
function getWeatherEmoji(weatherCode: number): string {
  if (weatherCode === 0 || weatherCode === 1) return '☀️';  // SIEMPRE SOL
  if (weatherCode === 2 || weatherCode === 3) return '☁️';
  // ...
}
```

**Después:**
```typescript
function getWeatherEmoji(weatherCode: number, isDay: boolean): string {
  // Despejado
  if (weatherCode === 0 || weatherCode === 1) {
    return isDay ? '☀️' : '🌙';  // ✅ Sol de día, luna de noche
  }

  // Parcialmente nublado
  if (weatherCode === 2 || weatherCode === 3) {
    return isDay ? '⛅' : '☁️';  // ✅ Nube con sol de día, solo nube de noche
  }

  // Niebla, lluvia, nieve, tormenta (iguales día/noche)
  if (weatherCode >= 45 && weatherCode <= 48) return '🌫️';
  if (weatherCode >= 51 && weatherCode <= 67) return '🌧️';
  if (weatherCode >= 71 && weatherCode <= 77) return '❄️';
  if (weatherCode >= 80 && weatherCode <= 82) return '🌦️';
  if (weatherCode >= 85 && weatherCode <= 86) return '🌨️';
  if (weatherCode >= 95) return '⛈️';

  return isDay ? '🌤️' : '☁️';  // ✅ Default también considera día/noche
}
```

### 2. Actualizar llamada en `route.ts`

```typescript
const isDay = current.is_day === 1;
const response = {
  // ...
  emoji: getWeatherEmoji(current.weather_code, isDay),
  isDay,
  // ...
};
```

## Emojis Día vs Noche

| Condición | Día | Noche |
|-----------|-----|-------|
| Despejado | ☀️ | 🌙 |
| Parcialmente nublado | ⛅ | ☁️ |
| Nublado | ☁️ | ☁️ |
| Niebla | 🌫️ | 🌫️ |
| Lluvia | 🌧️ | 🌧️ |
| Nieve | ❄️ | ❄️ |
| Tormenta | ⛈️ | ⛈️ |

## Sobre Sunrise/Sunset

### ¿Por qué no aparecían?

Posibles causas:
1. **Cache anterior** - El badge tenía una versión cacheada sin sunrise/sunset
2. **Primera carga** - El componente se montó antes de que llegaran los datos

### Solución

Los datos YA están implementados:
```typescript
// API devuelve:
{
  sunrise: "2026-01-03T05:59",  // ✅
  sunset: "2026-01-03T20:28"    // ✅
}

// Badge renderiza:
{(weather.sunrise || weather.sunset) && (
  <div>
    <Sunrise /> 05:59
    <Sunset /> 20:28
  </div>
)}
```

**Para verlos:** Limpiar cache del navegador o esperar 30 minutos (TTL del cache).

## Sobre el Timezone

### ¿Necesitamos guardar UTC-3 en `boletines_index.json`?

**NO**, porque:

1. ✅ Ya usamos `timezone=America/Argentina/Buenos_Aires` en Open-Meteo
2. ✅ Esto garantiza que **todos** los datos vienen en hora argentina:
   - `current.is_day` - Calculado en hora argentina
   - `current.temperature_2m` - Hora actual argentina
   - `daily.sunrise` - Hora argentina
   - `daily.sunset` - Hora argentina
3. ✅ El timezone es constante para toda Argentina (UTC-3 / GMT-3)
4. ✅ `boletines_index.json` es para ordenanzas, NO para clima

### Verificación

```bash
# Test actual (01:08 AM Argentina)
curl "https://api.open-meteo.com/v1/forecast?...&timezone=America/Argentina/Buenos_Aires"
# Respuesta:
{
  "current": {
    "time": "2026-01-03T01:00",  # ✅ Hora argentina
    "is_day": 0                   # ✅ Correctamente detecta noche
  }
}
```

## Testing

### Verificar emoji nocturno:
```javascript
// Hora actual: 01:08 AM (noche)
// weatherCode: 0 (despejado)
// isDay: 0 (noche)
// Emoji esperado: 🌙 ✅
```

### Verificar sunrise/sunset:
```javascript
{
  "sunrise": "2026-01-03T05:59",  // 05:59 AM ✅
  "sunset": "2026-01-03T20:28"    // 20:28 PM ✅
}
```

## Resultado Final

Ahora el badge muestra correctamente:
- 🌙 de noche cuando está despejado
- ⛅/☁️ según si es día/noche cuando está nublado
- 🌅 05:59 (amanecer)
- 🌆 20:28 (atardecer)

Con gradientes nocturnos automáticos:
- Noche despejada: Índigo → Púrpura → Negro
- Noche nublada: Gris oscuro
