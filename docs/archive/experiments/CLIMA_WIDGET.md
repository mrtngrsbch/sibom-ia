# Widget de Clima - Documentación

## Resumen

Sistema de badges de clima integrado en el chatbot que muestra información meteorológica en tiempo real de los municipios de la Provincia de Buenos Aires usando el API gratuito de Open-Meteo.

## Características

✅ **Dual Badge System**:
- Badge **pequeño** en el FilterBar (muestra solo temperatura y emoji)
- Badge **grande** en el cuerpo del chat (muestra datos completos: temperatura, sensación térmica, humedad, viento, precipitación)

✅ **Sin API Key requerida**: Usa Open-Meteo (100% gratuito, 10,000 requests/día)

✅ **Sin ambigüedades**: Tabla pre-configurada de 34 municipios con coordenadas GPS exactas

✅ **Cache inteligente**: 30 minutos de TTL para reducir llamadas al API

✅ **Actualización automática**: Se refresca cada 30 minutos mientras el usuario está en la página

## Archivos Creados

### 1. Tabla de Coordenadas
**Archivo**: `chatbot/src/lib/data/municipalities-coords.ts`

```typescript
// Tabla con los 34 municipios y sus coordenadas GPS
export const MUNICIPALITIES_COORDS: Record<string, MunicipalityCoords> = {
  "Dolores": {
    name: "Dolores",
    latitude: -36.3133,
    longitude: -57.6792,
    province: "Buenos Aires"
  },
  // ... 33 municipios más
};

// Funciones helper
export function getMunicipalityCoords(municipalityName: string): MunicipalityCoords | null;
export function municipalityExists(municipalityName: string): boolean;
export function getAllMunicipalityNames(): string[];
```

### 2. API Route
**Archivo**: `chatbot/src/app/api/weather/route.ts`

**Endpoint**: `GET /api/weather?municipality=NombreMunicipio`

**Respuesta**:
```json
{
  "municipality": "Dolores",
  "temperature": 15,
  "feelsLike": 12,
  "humidity": 67,
  "windSpeed": 18,
  "precipitation": 0,
  "weatherCode": 2,
  "description": "Parcialmente nublado",
  "emoji": "☁️",
  "timestamp": "2026-01-03T00:00:00.000Z",
  "cached": false
}
```

**Features**:
- Cache en memoria (30 min TTL)
- Mapeo de códigos WMO a descripciones en español
- Emojis automáticos según condición meteorológica
- Manejo de errores completo

### 3. Componente WeatherBadge
**Archivo**: `chatbot/src/components/chat/WeatherBadge.tsx`

**Props**:
```typescript
interface WeatherBadgeProps {
  municipality: string | null;  // Municipio a consultar
  variant?: 'small' | 'large';  // Tamaño del badge
  className?: string;           // Clases CSS adicionales
}
```

**Variantes**:

#### Small (FilterBar)
- Muestra solo emoji + temperatura
- Tooltip con sensación térmica
- No muestra errores (solo desaparece)

#### Large (Chat Body)
- Muestra todos los datos meteorológicos
- Grid con iconos para cada métrica
- Degradado de fondo azul/cian
- Link a Open-Meteo en el footer

### 4. Integración en Componentes Existentes

**FilterBar.tsx**:
```typescript
import { WeatherBadge } from './WeatherBadge';

// ...al final de los filtros
<WeatherBadge municipality={filters.municipality} variant="small" />
```

**ChatContainer.tsx**:
```typescript
import { WeatherBadge } from './WeatherBadge';

// ...después del mensaje de bienvenida
{filters.municipality && (
  <WeatherBadge municipality={filters.municipality} variant="large" />
)}
```

## Cómo Usar

1. **Usuario selecciona municipio** en el FilterBar
2. **Badge pequeño aparece automáticamente** al lado de los filtros
3. **Badge grande aparece** en el cuerpo del chat (solo si hay municipio seleccionado)
4. **Actualización automática** cada 30 minutos sin intervención del usuario

## API de Open-Meteo

### Endpoint Usado
```
https://api.open-meteo.com/v1/forecast?
  latitude={lat}&
  longitude={lng}&
  current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&
  timezone=America/Argentina/Buenos_Aires&
  forecast_days=1
```

### Códigos de Clima (WMO)
- `0-1`: Despejado
- `2-3`: Nublado
- `45-48`: Niebla
- `51-67`: Lluvia/llovizna
- `71-77`: Nieve
- `80-86`: Chubascos
- `95-99`: Tormenta

### Límites
- **10,000 requests/día** (sin API key)
- **Cache de 30 min** → ~48 requests/día por municipio
- **34 municipios** → máximo 1,632 requests/día (16% del límite)

## Ventajas del Diseño

1. **Sin Geocoding Ambiguo**:
   - No usa nombres de municipios para geocoding
   - Coordenadas pre-almacenadas evitan confusiones entre ciudades homónimas

2. **Zero Configuration**:
   - Sin API keys
   - Sin registro
   - Sin límites estrictos

3. **Offline Friendly**:
   - Tabla de coordenadas en código
   - No depende de servicio de geocoding externo

4. **Performance**:
   - Cache de 30 min reduce llamadas al API
   - Actualización automática en background

5. **UX Mejorada**:
   - Badge pequeño siempre visible cuando hay municipio
   - Badge grande contextual en el chat
   - Emojis y colores intuitivos

## Testing

### Verificar Tabla de Coordenadas
```bash
cd chatbot
npx tsx -e "import {getAllMunicipalityNames} from './src/lib/data/municipalities-coords'; console.log(getAllMunicipalityNames())"
```

### Probar API Manual
```bash
curl "http://localhost:3000/api/weather?municipality=Dolores" | jq
```

### Probar Open-Meteo Directo
```bash
curl "https://api.open-meteo.com/v1/forecast?latitude=-36.3133&longitude=-57.6792&current=temperature_2m,weather_code&timezone=America/Argentina/Buenos_Aires" | jq
```

## Futuras Mejoras

1. **Pronóstico extendido**: Agregar vista de 3-7 días
2. **Alertas meteorológicas**: Mostrar warnings si hay condiciones extremas
3. **Gráficos**: Temperatura/humedad en las últimas 24h
4. **Comparación**: Comparar clima entre municipios
5. **Persistencia**: Guardar preferencias de municipio favorito

## Troubleshooting

### Badge no aparece
- Verificar que hay municipio seleccionado: `filters.municipality !== null`
- Revisar console del browser para errores de API

### Error 404 del municipio
- Verificar que el nombre coincide exactamente con la tabla
- Ver lista completa: `getAllMunicipalityNames()`

### Clima desactualizado
- Cache es de 30 min, esperar o limpiar cache manualmente
- Verificar timestamp en respuesta del API

### Rate limit de Open-Meteo
- Verificar que cache está funcionando
- Reducir frecuencia de actualización si es necesario
