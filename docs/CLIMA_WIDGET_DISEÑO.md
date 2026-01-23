# Weather Badge - Diseño Avanzado (Estilo Yahoo Weather)

## Cambios Implementados

### ✅ 1. Badge Pequeño Eliminado
- **Razón**: Duplicaba información ya mostrada en el chat
- El badge ahora solo se muestra en el cuerpo del chat cuando hay municipio seleccionado

### ✅ 2. Diseño Dinámico con Gradientes
Similar a Yahoo Weather, el fondo cambia según:
- **Hora del día** (amanecer, día, atardecer, noche)
- **Condición climática** (despejado, nublado, lluvia, nieve, tormenta)

#### Gradientes Implementados:

**Amanecer (5-7 AM)**
```css
from-orange-300 via-pink-300 to-purple-400
```
🌅 Colores cálidos naranjas/rosas/púrpuras

**Atardecer (18-20 PM)**
```css
from-orange-400 via-red-400 to-purple-500
```
🌇 Colores intensos naranjas/rojos/púrpuras

**Noche Despejada**
```css
from-indigo-900 via-purple-900 to-slate-900
```
🌌 Azul oscuro/púrpura profundo

**Noche Nublada**
```css
from-slate-800 via-slate-700 to-slate-900
```
☁️ Grises oscuros

**Día Despejado**
```css
from-blue-400 via-cyan-300 to-blue-300
```
☀️ Azul cielo brillante

**Día Nublado**
```css
from-blue-300 via-slate-200 to-gray-300
```
⛅ Grises claros con toques azules

**Día con Lluvia**
```css
from-gray-400 via-slate-400 to-blue-400
```
🌧️ Grises con azules apagados

**Día con Nieve**
```css
from-slate-200 via-blue-200 to-white
```
❄️ Blancos/celestes claros

**Tormenta**
```css
from-gray-600 via-slate-700 to-gray-800
```
⛈️ Grises muy oscuros

### ✅ 3. Animaciones Climáticas

#### Lluvia
- 30 partículas animadas cayendo
- Líneas verticales semi-transparentes
- Velocidad variable (0.5-1s)
- Efecto de caída continua

#### Nieve
- 20 copos de nieve circulares
- Movimiento diagonal (caída + deriva lateral)
- Velocidad lenta (2-4s)
- Efecto de nieve flotante

### ✅ 4. Datos Adicionales

**Sunrise/Sunset**
- Muestra hora de amanecer y atardecer
- Iconos de sol naciente/poniente
- Formato 24h (HH:MM)

**Flag isDay**
- Detecta si es de día o noche actualmente
- Usado para determinar gradientes nocturnos

### ✅ 5. Efectos Visuales

**Drop Shadow**
- Texto con sombra para mejor legibilidad sobre fondos dinámicos
- Aplicado a título, descripción, temperatura

**Backdrop Blur**
- Cards de detalles con fondo semi-transparente difuminado
- `bg-white/10 backdrop-blur-sm`
- Efecto glassmorphism moderno

**Opacidad Dinámica**
- Fondo con `opacity-90` para permitir sutiles variaciones
- Textos con opacidad variable (70-100%) según jerarquía

## Estructura del Badge

```tsx
<div className="relative overflow-hidden rounded-2xl">
  {/* Fondo gradiente dinámico */}
  <div className="absolute inset-0 bg-gradient-to-br {gradiente} opacity-90" />

  {/* Animaciones (lluvia/nieve) */}
  <WeatherAnimation weatherCode={weatherCode} />

  {/* Contenido */}
  <div className="relative z-10 p-6 text-white">
    {/* Header: Ciudad + Emoji grande */}
    <div className="flex items-start justify-between">
      <div>
        <h3>Dolores</h3>
        <p>Parcialmente nublado</p>
      </div>
      <span className="text-6xl">☁️</span>
    </div>

    {/* Temperatura principal 7xl */}
    <div className="text-7xl font-bold">15°C</div>
    <p>Sensación térmica: 12°C</p>

    {/* Grid 3 columnas: Humedad, Viento, Precipitación */}
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-white/10 backdrop-blur-sm rounded-lg">
        <Droplets />
        <span>67%</span>
        <span>Humedad</span>
      </div>
      {/* ... */}
    </div>

    {/* Sunrise/Sunset */}
    <div className="border-t border-white/20">
      <Sunrise /> 05:38
      <Sunset /> 20:11
    </div>

    {/* Footer */}
    <p>Datos de Open-Meteo</p>
  </div>
</div>
```

## Datos de Open-Meteo API

### Endpoint Actualizado
```
https://api.open-meteo.com/v1/forecast?
  latitude={lat}&
  longitude={lng}&
  current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,is_day&
  daily=sunrise,sunset&
  timezone=America/Argentina/Buenos_Aires&
  forecast_days=1
```

### Nuevos Campos Agregados:
- `current.is_day` - 1 si es de día, 0 si es de noche
- `daily.sunrise[0]` - Hora del amanecer (ISO 8601)
- `daily.sunset[0]` - Hora del atardecer (ISO 8601)

### Respuesta Actualizada del API:
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
  "isDay": true,
  "sunrise": "2026-01-03T05:38",
  "sunset": "2026-01-03T20:11",
  "timestamp": "2026-01-03T00:00:00.000Z",
  "cached": false
}
```

## Algoritmo de Gradientes

```typescript
function getBackgroundGradient(weatherCode: number, isDay: boolean, currentHour: number): string {
  // 1. Prioridad horarios especiales
  if (currentHour >= 5 && currentHour < 7) return gradienteAmanecer;
  if (currentHour >= 18 && currentHour < 20) return gradienteAtardecer;

  // 2. Noche
  if (!isDay || currentHour >= 20 || currentHour < 5) {
    if (weatherCode <= 1) return nocheDespejada;
    if (weatherCode <= 3) return nocheNublada;
    if (weatherCode >= 51) return nocheLluvia;
    return nocheDefault;
  }

  // 3. Día según condición
  if (weatherCode <= 1) return diaDespejado;
  if (weatherCode <= 3) return diaNublado;
  if (weatherCode >= 51 && weatherCode <= 67) return diaLluvia;
  if (weatherCode >= 71 && weatherCode <= 77) return diaNieve;
  if (weatherCode >= 95) return tormenta;

  return diaDefault;
}
```

## Jerarquía Visual

### Tamaños de Fuente:
- Temperatura: `text-7xl` (72px)
- Emoji: `text-6xl` (60px)
- Ciudad: `text-2xl` (24px)
- Detalles: `text-lg` (18px)
- Descripción: `text-sm` (14px)
- Footer: `text-xs` (12px)

### Espaciado:
- Padding principal: `p-6` (24px)
- Gap entre secciones: `mb-4` a `mb-6` (16-24px)
- Gap en grid: `gap-4` (16px)

### Bordes:
- Badge: `rounded-2xl` (16px)
- Cards internos: `rounded-lg` (8px)

## Comparación con Yahoo Weather

### ✅ Similitudes Implementadas:
1. **Gradientes dinámicos** según hora y clima
2. **Animaciones** de partículas (lluvia/nieve)
3. **Temperatura grande** como elemento principal
4. **Glassmorphism** en cards de detalles
5. **Sunrise/Sunset** integrados
6. **Colores de texto en blanco** sobre fondo dinámico

### ❌ No Implementado (futuras mejoras):
1. **Imágenes de fondo** (Yahoo usa fotos reales de paisajes)
2. **Gráficos de temperatura** por hora
3. **Pronóstico extendido** (3-7 días)
4. **Mapa de radar** de lluvia
5. **Alertas meteorológicas**

## Opciones de Customización Futuras

### Nivel 1: Fácil (CSS/Tailwind)
- Cambiar colores de gradientes
- Ajustar opacidades
- Modificar tamaños de fuente
- Cambiar bordes/sombras

### Nivel 2: Medio (React/TypeScript)
- Agregar más animaciones (relámpagos para tormenta)
- Mostrar/ocultar secciones
- Cambiar layout (horizontal vs vertical)
- Agregar transiciones entre estados

### Nivel 3: Avanzado (API/Backend)
- Pronóstico por hora (gráfico lineal)
- Pronóstico extendido (7 días)
- Alertas de clima extremo
- Comparación con otros municipios
- Histórico de temperatura

## Testing Visual

Para probar diferentes condiciones:

1. **Día despejado**: weatherCode = 0-1, isDay = true, hora = 12
2. **Noche nublada**: weatherCode = 2-3, isDay = false, hora = 22
3. **Día con lluvia**: weatherCode = 61, isDay = true, hora = 14
4. **Amanecer**: weatherCode = 0, isDay = true, hora = 6
5. **Atardecer**: weatherCode = 2, isDay = true, hora = 19
6. **Nieve**: weatherCode = 71, isDay = true, hora = 11
7. **Tormenta**: weatherCode = 95, isDay = false, hora = 21

## Performance

### Animaciones:
- CSS puro (sin JavaScript)
- GPU-accelerated (transform/opacity)
- No impacto en rendimiento

### Re-renders:
- Solo cuando cambia `municipality`
- Cache de 30 min → mínimos fetches
- useEffect con cleanup apropiado

### Bundle Size:
- ~3KB adicionales (componente + estilos)
- No librerías externas
- Solo iconos de Lucide (ya en uso)
