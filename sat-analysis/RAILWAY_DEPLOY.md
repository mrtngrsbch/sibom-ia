# 🚀 Despliegue en Railway

Guía para desplegar sat-analysis en Railway (https://railway.app/).

## Archivos de Configuración

- **[Dockerfile](Dockerfile)** - Multi-stage build optimizado para Python 3.13
- **[railway.json](railway.json)** - Configuración específica de Railway
- **[.dockerignore](.dockerignore)** - Exclusiones para optimizar el build

## Pasos para Desplegar

### Opción 1: Desde GitHub (Recomendado)

1. **Subir código a GitHub**
   ```bash
   git add sat-analysis/Dockerfile sat-analysis/railway.json sat-analysis/.dockerignore sat-analysis/app.py
   git commit -m "feat: add Railway deployment config"
   git push
   ```

2. **Crear proyecto en Railway**
   - Ve a https://railway.app/
   - Click en "New Project" → "Deploy from GitHub repo"
   - Selecciona tu repositorio
   - Railway detectará automáticamente el Dockerfile

3. **Configurar variables de entorno (opcional)**
   - En la pestaña "Variables" del proyecto:
   - `PORT=7860` (Railway asigna esto automáticamente)
   - `GRADIO_SERVER_NAME=0.0.0.0`

4. **Desplegar**
   - Click en "Deploy"
   - Railway construirá la imagen Docker (tarda ~5-10 minutos en el primer build)
   - Obtendrás una URL pública tipo `https://tu-app.railway.app`

### Opción 2: Desde CLI de Railway

1. **Instalar Railway CLI**
   ```bash
   pnpm add -g @railway/cli
   ```

2. **Login y deploy**
   ```bash
   railway login
   railway init  # desde el directorio sat-analysis/
   railway up
   ```

3. **Abrir la app desplegada**
   ```bash
   railway open
   ```

## Configuración del Servidor

Railway asigna automáticamente:
- **Puerto**: Variable de entorno `PORT` (usualmente 7860)
- **URL**: Pública con HTTPS
- **Recurso**: 512MB RAM / 1 CPU (plan gratuito)

Para análisis intensivos, considera:
- **Plan Hobby**: $5/mes - 1GB RAM
- **Plan Pro**: $20/mes - 2GB RAM + más CPU

## Recursos Necesarios

El procesamiento de imágenes satelitales es intensivo en recursos:

| Operación | RAM estimada | Tiempo |
|-----------|--------------|--------|
| Consulta ARBA WFS | ~50 MB | < 1s |
| Búsqueda STAC | ~100 MB | 2-5s |
| Descarga 1 imagen Sentinel-2 | ~200 MB | 5-10s |
| Clasificación 1 imagen | ~300 MB | 3-5s |
| Análisis completo (10 imágenes) | ~500 MB | 30-60s |

**Recomendación**: Mínimo 1GB RAM para producción.

## Limitaciones del Plan Gratuito

- **512MB RAM**: Puede ser insuficiente para procesar múltiples imágenes
- **Sleep**: La app se "duerme" después de 30 min de inactividad
- **Cold start**: Primer análisis tarda ~30 segundos adicionales
- **Timeout**: Requests tienen timeout de 60 segundos

Para uso en producción, considera el plan **Hobby ($5/mes)** con 1GB RAM.

## Monitoreo

En el dashboard de Railway puedes ver:
- **Logs**: Salida estándar del contenedor
- **Metrics**: CPU, RAM, disco
- **Deployments**: Historial de despliegues
- **Cron Jobs**: Para tareas programadas (si aplica)

## Troubleshooting

### Error: "Container failed to start"

Revisa los logs en Railway dashboard. Causas comunes:
- Build falló por dependencias faltantes
- Puerto incorrecto (debe usar variable `PORT`)
- Error al importar módulos de `sat_analysis`

### Error: "Out of memory"

El plan gratuito de 512MB puede ser insuficiente. Soluciones:
- Reducir `samples_per_year` en análisis
- Upgrade a plan con más RAM
- Optimizar el procesamiento de imágenes

### Error: "Timeout en análisis"

Railway tiene timeout de 60s por request. Soluciones:
- Reducir cantidad de imágenes a procesar
- Usar procesamiento asíncrono con background tasks

## Variables de Entorno Disponibles

```bash
# Asignadas automáticamente por Railway
PORT=7860
RAILWAY_ENVIRONMENT=production
RAILWAY_SERVICE_NAME=web

# Opcionales (configurables en dashboard)
GRADIO_SERVER_NAME=0.0.0.0
LOG_LEVEL=INFO
```

## Actualizar el Despliegue

Cada push a GitHub activa un nuevo deploy automáticamente:

```bash
git push
# Railway detecta cambios y reconstruye
```

## Costos Estimados

| Plan | RAM | CPU | Precio | Uso recomendado |
|------|-----|-----|--------|-----------------|
| Free | 512MB | 0.5 vCPU | $0 | Desarrollo/testing |
| Hobby | 1GB | 1 vCPU | $5/mes | Producción bajo volumen |
| Pro | 2GB | 2 vCPU | $20/mes | Producción alto volumen |

---

**Documentación**: [Railway Docs](https://docs.railway.app/)
