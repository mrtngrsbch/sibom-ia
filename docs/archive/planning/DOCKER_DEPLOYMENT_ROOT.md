# Docker Deployment - SIBOM Scraper Assistant

Guía de despliegue para VPS con Docker.

## Requisitos Previos

- Docker y Docker Compose instalados en el VPS
- Dominio configurado apuntando a la IP del VPS (opcional, para SSL)
- Git para clonar el repositorio

## Estructura del Despliegue

```
┌─────────────────────────────────────────────────────────────┐
│                        VPS Hostinger                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Nginx (80/443)                                      │   │
│  │   / → chatbot:3000                                   │   │
│  │   /api/satelite/* → sat-analysis:8001                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                 │
│         ┌────────────────┴────────────────┐               │
│         ▼                                 ▼               │
│  ┌─────────────┐                ┌──────────────┐        │
│  │  chatbot    │                │ sat-analysis │        │
│  │  Next.js    │                │  FastAPI     │        │
│  │  :3000      │                │  :8001       │        │
│  └─────────────┘                └──────────────┘        │
│                                                             │
│  Volúmenes:                                                 │
│  - sat-data/ (resultados de análisis)                     │
│  - sat-cache/ (imágenes procesadas)                        │
└─────────────────────────────────────────────────────────────┘
```

## Pasos de Despliegue

### 1. Clonar el Repositorio

```bash
git clone <tu-repositorio>
cd sibom-scraper-assistant
```

### 2. Configurar Variables de Entorno

Crear archivo `.env` en la raíz:

```bash
# Chatbot
NODE_ENV=production
OPENROUTER_API_KEY=sk-or-xxx
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5
SAT_API_URL=http://sat-analysis:8001

# Sat-Analysis (opcional, valores por defecto)
SAT_ANALYSIS_STAC_URL=https://planetarycomputer.microsoft.com/api/stac/v1
SAT_ANALYSIS_ARBA_WFS_URL=https://geo.arba.gov.ar/geoserver/idera/wfs
```

### 3. Construir y Levantar Contenedores

```bash
# Build inicial
docker-compose build

# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 4. Verificar Funcionamiento

```bash
# Verificar que todos los containers estén running
docker ps

# Verificar health checks
curl http://localhost:3000/api/health  # Chatbot
curl http://localhost:8001/api/health  # Sat-Analysis
```

### 5. Configurar SSL con Let's Encrypt (Opcional)

#### Primero obtener certificado:

```bash
# Crear directorios
mkdir -p certbot/conf certbot/www

# Obtener certificado (reemplazar con tu dominio y email)
docker run --rm -p 80:80 \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot certonly \
  --email tu-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d tu-dominio.com \
  --standalone
```

#### Actualizar nginx.conf:

1. Descomentar la sección HTTPS en `nginx/nginx.conf`
2. Cambiar `tu-dominio.com` por tu dominio real
3. Comentar la redirección HTTP en la sección HTTP

#### Reiniciar nginx:

```bash
docker-compose restart nginx
```

## Comandos Útiles

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f chatbot
docker-compose logs -f sat-analysis

# Reiniciar un servicio
docker-compose restart chatbot

# Actualizar servicios después de cambios
docker-compose up -d --build

# Detener todos los servicios
docker-compose down

# Eliminar volumes (CUIDADO: borra datos)
docker-compose down -v
```

## URLs de Acceso

- **Frontend**: `http://tu-ip:3000` o `http://tu-dominio.com`
- **API Sat-Analysis**: `http://tu-ip:8001/api/docs` (documentación FastAPI)
- **Chat**: `http://tu-dominio.com/`
- **Análisis Satelital**: `http://tu-dominio.com/satelite`

## Troubleshooting

### El container de sat-analysis falla al iniciar

Verificar que las dependencias geoespaciales se instalaron correctamente:

```bash
docker logs sibom-sat-analysis
```

### El chatbot no se conecta a la API de satélite

Verificar que `SAT_API_URL` esté correctamente configurada y que el contenedor de sat-analysis esté funcionando.

### Error de "connection refused"

Verificar que los containers estén en la misma red Docker:

```bash
docker network inspect sibom-scraper-assistant_sibom-network
```

### Los datos se pierden al reiniciar

Los datos persistentes se guardan en los volumes Docker. Para hacer backup:

```bash
# Backup de sat-data
docker run --rm -v sibom-scraper-assistant_sat-data:/data -v $(pwd):/backup alpine tar czf /backup/sat-data-backup.tar.gz /data
```

## Actualización del Sistema

Para actualizar después de cambios en el código:

```bash
# Pull de cambios
git pull

# Reconstruir y reiniciar
docker-compose up -d --build
```

## Monitoreo

### Ver uso de recursos

```bash
docker stats
```

### Ver espacio en disco

```bash
docker system df
```

### Limpiar resources no usados

```bash
docker system prune -a
```
