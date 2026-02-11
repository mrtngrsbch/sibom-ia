# Guía de Despliegue en Docker - Chatbot SIBOM

**Fecha:** 2026-02-05  
**Versión:** 1.0.0  
**Estado:** 📋 Guía para VPS

---

## 📋 Tabla de Contenidos

1. [Tecnologías del Frontend](#tecnologías-del-frontend)
2. [Requisitos del Sistema](#requisitos-del-sistema)
3. [Configuración de Docker](#configuración-de-docker)
4. [Despliegue en VPS](#despliegue-en-vps)
5. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
6. [Optimización para Producción](#optimización-para-producción)
7. [Troubleshooting](#troubleshooting)

---

## 1. Tecnologías del Frontend

### 1.1 Stack Tecnológico

| Tecnología         | Versión | Propósito                                  |
| ------------------ | ------- | ------------------------------------------ |
| **Next.js**        | 16.1.1  | Framework React para aplicaciones web      |
| **React**          | 19.0.0  | Biblioteca de UI para construir interfaces |
| **TypeScript**     | 5.0.0   | Superset tipado de JavaScript              |
| **Node.js**        | 18+     | Runtime de JavaScript para el servidor     |
| **Vercel AI SDK**  | 4.1.0   | SDK para integración con LLMs y streaming  |
| **OpenAI SDK**     | 6.16.0  | Cliente para OpenAI/OpenRouter             |
| **Tailwind CSS**   | 3.4.0   | Framework de CSS utilitario                |
| **Zustand**        | 5.0.10  | Gestión de estado ligero                   |
| **date-fns**       | 4.1.0   | Manipulación de fechas                     |
| **React Markdown** | 10.1.0  | Renderizado de Markdown en React           |
| **sql.js**         | 1.13.0  | SQLite compilado a WebAssembly             |

### 1.2 Dependencias de Desarrollo

| Tecnología                 | Versión     | Propósito                    |
| -------------------------- | ----------- | ---------------------------- |
| **Vitest**                 | 1.6.1       | Framework de testing         |
| **@testing-library/react** | 16.1.0      | Testing de componentes React |
| **TypeScript**             | 5.0.0       | Compilador de TypeScript     |
| **ESLint**                 | Configurado | Linting de código            |
| **Prettier**               | Configurado | Formateo de código           |
| **Husky**                  | 9.1.7       | Git hooks                    |

### 1.3 Arquitectura de la Aplicación

```
chatbot/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── api/
│   │   │   └── chat/route.ts  # API principal (Serverless)
│   │   ├── layout.tsx          # Layout raíz
│   │   └── page.tsx            # Página principal
│   ├── components/
│   │   ├── chat/               # Componentes del chat
│   │   └── layout/             # Componentes de layout
│   └── lib/
│       ├── rag/                # Motor RAG
│       ├── computation/         # Motor de cómputo
│       └── query-classifier.ts # Clasificador de queries
├── public/                     # Assets estáticos
├── package.json                # Dependencias
├── tsconfig.json               # Configuración TypeScript
├── next.config.js              # Configuración Next.js
├── tailwind.config.ts          # Configuración Tailwind
└── Dockerfile                  # Configuración Docker
```

---

## 2. Requisitos del Sistema

### 2.1 Requisitos Mínimos del Servidor

| Recurso               | Mínimo        | Recomendado      |
| --------------------- | ------------- | ---------------- |
| **CPU**               | 2 vCPUs       | 4 vCPUs          |
| **RAM**               | 2 GB          | 4 GB             |
| **Almacenamiento**    | 10 GB         | 20 GB SSD        |
| **Sistema Operativo** | Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| **Node.js**           | 18.x          | 20.x LTS         |
| **Docker**            | 20.10+        | 24.x+            |
| **Docker Compose**    | 2.0+          | 2.20+            |

### 2.2 Software Requerido

```bash
# Verificar versiones
node --version    # Debe ser 18.x o superior
docker --version   # Debe ser 20.x o superior
docker-compose --version  # Debe ser 2.x o superior
```

---

## 3. Configuración de Docker

### 3.1 Dockerfile para Next.js

Crear archivo `chatbot/Dockerfile`:

```dockerfile
# ============================================================================
# Multi-stage build para Next.js en producción
# ============================================================================

# Stage 1: Dependencias
FROM node:20-alpine AS deps

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package.json package-lock.json* ./

# Instalar dependencias
RUN npm ci --only=production && \
    npm cache clean --force

# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar dependencias desde stage deps
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Establecer variables de entorno para build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Construir la aplicación
RUN npm run build

# Stage 3: Runner (Producción)
FROM node:20-alpine AS runner

WORKDIR /app

# Crear usuario no-root para seguridad
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Establecer variables de entorno
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Copiar archivos necesarios desde builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Crear directorio para cache
RUN mkdir .next/cache && \
    chown -R nextjs:nodejs /app

# Cambiar a usuario no-root
USER nextjs

# Exponer puerto
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Iniciar aplicación
CMD ["node", "server.js"]
```

### 3.2 Configuración de Next.js para Standalone

Modificar `chatbot/next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Configuración para Docker standalone
  output: 'standalone',
  
  // Optimizaciones de imágenes
  images: {
    domains: ['pub-*.r2.dev'], // Cloudflare R2
    unoptimized: false,
  },
  
  // Configuración de headers para CORS y caching
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          }
        ]
      }
    ];
  },
  
  // Configuración de rewrites para datos externos
  async rewrites() {
    return [
      {
        source: '/data/:path*',
        destination: 'https://pub-*.r2.dev/sibom-data/:path*'
      }
    ];
  },
  
  // Configuración experimental
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },
};

module.exports = nextConfig;
```

### 3.3 Docker Compose

Crear archivo `chatbot/docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Chatbot Next.js
  chatbot:
    build:
      context: .
      dockerfile: Dockerfile
      target: runner
    container_name: sibom-chatbot
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - PORT=3000
      # Variables de entorno (usar .env file)
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_MODEL=${OPENROUTER_MODEL:-google/gemini-3-flash-preview}
      - LLM_MODEL_PRIMARY=${LLM_MODEL_PRIMARY:-anthropic/claude-3.5-sonnet}
      - LLM_MODEL_ECONOMIC=${LLM_MODEL_ECONOMIC:-google/gemini-flash-1.5}
      # Configuración de datos
      - GITHUB_DATA_REPO=${GITHUB_DATA_REPO}
      - GITHUB_DATA_BRANCH=${GITHUB_DATA_BRANCH:-main}
      - GITHUB_USE_GZIP=${GITHUB_USE_GZIP:-true}
      - USE_NORMATIVAS_INDEX=${USE_NORMATIVAS_INDEX:-true}
      - USE_SQLITE=${USE_SQLITE:-false}
      # Configuración de cache
      - INDEX_CACHE_DURATION=${INDEX_CACHE_DURATION:-3600000}
    env_file:
      - .env.production
    volumes:
      # Montar logs para persistencia
      - ./logs:/app/logs
      # Cache de Next.js
      - nextjs_cache:/app/.next/cache
    networks:
      - sibom-network
    healthcheck:
      test: ["CMD", "node", "-e", "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Nginx Reverse Proxy (Opcional pero recomendado)
  nginx:
    image: nginx:alpine
    container_name: sibom-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - nginx_cache:/var/cache/nginx
    depends_on:
      - chatbot
    networks:
      - sibom-network

volumes:
  nextjs_cache:
  nginx_cache:

networks:
  sibom-network:
    driver: bridge
```

### 3.4 Configuración de Nginx

Crear archivo `chatbot/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # Cache
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=nextjs_cache:10m max_size=1g inactive=60m;

    # Upstream
    upstream nextjs_upstream {
        server chatbot:3000;
        keepalive 64;
    }

    # HTTP Server
    server {
        listen 80;
        server_name your-domain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security Headers
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "origin-when-cross-origin" always;

        # Proxy to Next.js
        location / {
            proxy_pass http://nextjs_upstream;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Static files caching
        location /_next/static {
            proxy_pass http://nextjs_upstream;
            proxy_cache_valid 200 365d;
            add_header Cache-Control "public, immutable";
        }

        # Health check endpoint
        location /api/health {
            proxy_pass http://nextjs_upstream;
            access_log off;
        }
    }
}
```

---

## 4. Despliegue en VPS

### 4.1 Preparación del Servidor

```bash
# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 3. Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Verificar instalación
docker --version
docker-compose --version

# 5. Crear usuario para la aplicación (opcional pero recomendado)
sudo useradd -m -s /bin/bash sibom
sudo usermod -aG docker sibom

# 6. Crear directorio de la aplicación
sudo mkdir -p /opt/sibom-chatbot
sudo chown sibom:sibom /opt/sibom-chatbot

# 7. Cambiar al usuario de la aplicación
sudo su - sibom
cd /opt/sibom-chatbot
```

### 4.2 Clonar y Configurar Repositorio

```bash
# 1. Clonar repositorio
git clone https://github.com/mrtngrsbch/sibom-ia.git .
# O usar tu fork
# git clone https://github.com/tu-usuario/sibom-ia.git .

# 2. Navegar al directorio del chatbot
cd chatbot

# 3. Crear archivo de entorno
cp .env.production.example .env.production

# 4. Editar variables de entorno
nano .env.production
```

### 4.3 Configurar Variables de Entorno

Editar `.env.production`:

```env
# ============================================================================
# Variables de Entorno - Producción
# ============================================================================

# LLM Configuration
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aqui
OPENROUTER_MODEL=google/gemini-3-flash-preview
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5

# Data Configuration
GITHUB_DATA_REPO=pub-xxxxx.r2.dev/sibom-data
GITHUB_DATA_BRANCH=
GITHUB_USE_GZIP=true

# Index Configuration
USE_NORMATIVAS_INDEX=true
USE_SQLITE=false
INDEX_CACHE_DURATION=3600000

# Application Configuration
NODE_ENV=production
PORT=3000
NEXT_TELEMETRY_DISABLED=1

# Security (opcional)
ALLOWED_ORIGINS=https://tu-dominio.com
```

### 4.4 Construir y Ejecutar

```bash
# 1. Construir imagen Docker
docker-compose build

# 2. Iniciar servicios
docker-compose up -d

# 3. Ver logs
docker-compose logs -f chatbot

# 4. Verificar que el contenedor está corriendo
docker-compose ps

# 5. Verificar health check
curl http://localhost:3000/api/health
```

### 4.5 Configurar SSL con Let's Encrypt

```bash
# 1. Instalar Certbot
sudo apt install certbot -y

# 2. Obtener certificado
sudo certbot certonly --standalone -d tu-dominio.com

# 3. Crear directorio para SSL
mkdir -p ssl

# 4. Copiar certificados
sudo cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem ssl/

# 5. Configurar renovación automática
sudo crontab -e

# Agregar esta línea (renueva certificados cada mes)
0 0 1 * * certbot renew --quiet && docker-compose restart nginx
```

---

## 5. Configuración de Variables de Entorno

### 5.1 Variables Obligatorias

| Variable             | Descripción           | Ejemplo                         |
| -------------------- | --------------------- | ------------------------------- |
| `OPENROUTER_API_KEY` | API key de OpenRouter | `sk-or-v1-xxxxx`                |
| `OPENROUTER_MODEL`   | Modelo LLM principal  | `google/gemini-3-flash-preview` |

### 5.2 Variables Opcionales

| Variable               | Descripción                   | Default                       |
| ---------------------- | ----------------------------- | ----------------------------- |
| `LLM_MODEL_PRIMARY`    | Modelo para queries complejas | `anthropic/claude-3.5-sonnet` |
| `LLM_MODEL_ECONOMIC`   | Modelo para FAQs simples      | `google/gemini-flash-1.5`     |
| `GITHUB_DATA_REPO`     | URL de datos externos         | `pub-xxxxx.r2.dev/sibom-data` |
| `GITHUB_DATA_BRANCH`   | Rama de GitHub                | `main`                        |
| `GITHUB_USE_GZIP`      | Usar compresión gzip          | `true`                        |
| `USE_NORMATIVAS_INDEX` | Usar nuevo índice             | `true`                        |
| `USE_SQLITE`           | Usar SQLite                   | `false`                       |
| `INDEX_CACHE_DURATION` | Duración del cache (ms)       | `3600000`                     |
| `PORT`                 | Puerto de la aplicación       | `3000`                        |

### 5.3 Variables de Seguridad

```env
# CORS Configuration
ALLOWED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# Rate Limiting (si implementas rate limiting)
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=900000

# Session Configuration
SESSION_SECRET=your-secret-key-here
SESSION_MAX_AGE=86400000
```

---

## 6. Optimización para Producción

### 6.1 Optimización de Build

```javascript
// next.config.js - Optimizaciones adicionales
const nextConfig = {
  output: 'standalone',
  
  // Optimizaciones de imágenes
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // Optimizaciones de bundle
  swcMinify: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Optimizaciones experimentales
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
    optimizeCss: true,
  },
};
```

### 6.2 Optimización de Docker

```dockerfile
# Optimizaciones adicionales en Dockerfile

# Usar multi-stage build para reducir tamaño
# Ya implementado en el Dockerfile anterior

# Usar Alpine Linux para reducir tamaño base
FROM node:20-alpine

# Limpiar caches después de instalar
RUN npm ci --only=production && \
    npm cache clean --force && \
    rm -rf /tmp/*

# Usar .dockerignore para excluir archivos innecesarios
```

Crear `.dockerignore`:

```
# Dependencies
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage
.nyc_output

# Next.js
.next/
out/

# Production
build
dist

# Misc
.DS_Store
*.pem
.env.local
.env.development.local
.env.test.local
.env.production.local

# Debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Git
.git
.gitignore

# CI/CD
.github
.gitlab-ci.yml

# Documentation
README.md
*.md
```

### 6.3 Optimización de Nginx

```nginx
# Optimizaciones adicionales en nginx.conf

# Worker processes (ajustar según CPU)
worker_processes auto;

# Conexiones por worker
events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

# Optimizaciones de HTTP
http {
    # Buffer sizes
    client_body_buffer_size 128k;
    client_max_body_size 20m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;
    
    # Timeouts
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # Optimizaciones de cache
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=nextjs_cache:10m max_size=1g inactive=60m use_temp_path=off;
    
    # Optimizaciones de compresión
    gzip_comp_level 6;
    gzip_min_length 256;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;
}
```

---

## 7. Troubleshooting

### 7.1 Problemas Comunes

#### Problema: Contenedor no inicia

```bash
# Ver logs del contenedor
docker-compose logs chatbot

# Verificar variables de entorno
docker-compose config

# Reconstruir imagen
docker-compose build --no-cache
docker-compose up -d
```

#### Problema: Error de memoria

```bash
# Verificar uso de memoria
docker stats

# Aumentar límite de memoria en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

#### Problema: Conexión rechazada

```bash
# Verificar que el puerto esté abierto
sudo netstat -tulpn | grep 3000

# Verificar firewall
sudo ufw status
sudo ufw allow 3000/tcp
```

#### Problema: Error de API de OpenRouter

```bash
# Verificar que la API key sea correcta
docker-compose exec chatbot env | grep OPENROUTER_API_KEY

# Verificar logs para más detalles
docker-compose logs -f chatbot | grep OPENROUTER
```

### 7.2 Monitoreo

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f chatbot

# Ver estadísticas de contenedores
docker stats

# Verificar health checks
docker inspect --format='{{json .State.Health}}' sibom-chatbot
```

### 7.3 Backup y Restore

```bash
# Backup de volúmenes
docker run --rm -v nextjs_cache:/data -v $(pwd):/backup alpine tar czf /backup/nextjs_cache.tar.gz /data

# Restore de volúmenes
docker run --rm -v nextjs_cache:/data -v $(pwd):/backup alpine tar xzf /backup/nextjs_cache.tar.gz -C /

# Backup de configuración
tar czf backup_$(date +%Y%m%d).tar.gz .env.production docker-compose.yml nginx.conf ssl/
```

### 7.4 Actualización

```bash
# 1. Hacer backup
tar czf backup_$(date +%Y%m%d).tar.gz .env.production docker-compose.yml nginx.conf ssl/

# 2. Pull de cambios
git pull origin main

# 3. Reconstruir imagen
docker-compose build

# 4. Reiniciar servicios
docker-compose down
docker-compose up -d

# 5. Verificar
docker-compose ps
docker-compose logs -f
```

---

## 8. Recursos Adicionales

### 8.1 Documentación Oficial

- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/docs/)

### 8.2 Scripts Útiles

#### Script de Monitoreo

```bash
#!/bin/bash
# monitor.sh - Script de monitoreo básico

echo "=== SIBOM Chatbot Monitor ==="
echo "Fecha: $(date)"
echo ""

# Estado de contenedores
echo "=== Estado de Contenedores ==="
docker-compose ps
echo ""

# Uso de recursos
echo "=== Uso de Recursos ==="
docker stats --no-stream
echo ""

# Logs recientes
echo "=== Logs Recientes (últimas 20 líneas) ==="
docker-compose logs --tail=20 chatbot
echo ""

# Health check
echo "=== Health Check ==="
curl -s http://localhost:3000/api/health && echo "✅ OK" || echo "❌ FAILED"
```

#### Script de Backup Automático

```bash
#!/bin/bash
# backup.sh - Script de backup automático

BACKUP_DIR="/opt/backups/sibom-chatbot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup de configuración
tar czf $BACKUP_DIR/config_$DATE.tar.gz .env.production docker-compose.yml nginx.conf

# Backup de volúmenes
docker run --rm -v nextjs_cache:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/cache_$DATE.tar.gz /data

# Limpiar backups antiguos (mantener últimos 7 días)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completado: $DATE"
```

---

**Fin del Documento**
