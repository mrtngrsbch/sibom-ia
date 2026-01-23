# Guía de Deployment: GitHub + Vercel (Opción Híbrida)

## 📋 Resumen

Esta guía explica cómo deployar el chatbot en Vercel usando GitHub Raw para hospedar los 533 MB de datos JSON de manera **100% gratuita**.

**Arquitectura**:
- **Frontend + Backend**: Vercel (gratis, <100 MB)
- **Datos (533 MB)**: GitHub público (gratis)
- **LLM**: OpenRouter con modelo económico (gemini-3-flash-preview)

**Ventajas**:
- ✅ Totalmente gratis
- ✅ Sin límites de storage (GitHub permite repos públicos de hasta 100 GB)
- ✅ Cache agresivo (1 hora índice, 30 min archivos)
- ✅ Opcionalmente con gzip (80% ahorro bandwidth)

---

## 🎯 Paso 1: Preparar Datos para GitHub

### 1.1. Comprimir Archivos (Opcional pero Recomendado)

Comprime los JSONs para ahorrar 80% de bandwidth:

```bash
cd python-cli
python comprimir_boletines.py
```

**Esto creará**:
- `boletines/*.json.gz` (archivos comprimidos)
- `boletines_index.json.gz` (índice comprimido)
- Ahorro: 533 MB → ~100 MB

**Alternativa sin compresión**:
Puedes saltar este paso y subir los .json directamente, pero consumirás más bandwidth.

### 1.2. Crear Repositorio de Datos en GitHub

1. Ve a [github.com](https://github.com) y crea un **nuevo repositorio público**
   - Nombre sugerido: `sibom-data`
   - Visibilidad: **Public** (importante para GitHub Raw)
   - No inicialices con README

2. Clona el repo local:
```bash
git clone https://github.com/TU-USUARIO/sibom-data.git
cd sibom-data
```

### 1.3. Subir Datos a GitHub

**Si comprimiste** (recomendado):
```bash
# Copiar archivos comprimidos
cp ../sibom-scraper-assistant/python-cli/boletines/*.json.gz ./boletines/
cp ../sibom-scraper-assistant/python-cli/boletines_index.json.gz ./

# Commit y push
git add .
git commit -m "Add compressed bulletins data (~100 MB)"
git push origin main
```

**Si NO comprimiste**:
```bash
# Copiar archivos originales
cp ../sibom-scraper-assistant/python-cli/boletines/*.json ./boletines/
cp ../sibom-scraper-assistant/python-cli/boletines_index.json ./

# Commit y push (puede tardar por el tamaño)
git add .
git commit -m "Add bulletins data (~533 MB)"
git push origin main
```

### 1.4. Verificar Acceso

Prueba que puedes acceder via GitHub Raw:

**Índice**:
```
https://raw.githubusercontent.com/TU-USUARIO/sibom-data/main/boletines_index.json
```

O si comprimiste:
```
https://raw.githubusercontent.com/TU-USUARIO/sibom-data/main/boletines_index.json.gz
```

Debe descargarse el archivo. Si ves JSON o se descarga, ¡funciona!

---

## 🚀 Paso 2: Configurar Proyecto para GitHub Raw

### 2.1. Actualizar Variables de Entorno Locales

Edita `/chatbot/.env.local`:

```bash
# OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aquí

# Modelo económico (gemini es 10x más barato que claude)
ANTHROPIC_MODEL=google/gemini-3-flash-preview

# Configuración GitHub
GITHUB_DATA_REPO=TU-USUARIO/sibom-data
GITHUB_DATA_BRANCH=main
GITHUB_USE_GZIP=true  # false si no comprimiste

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 2.2. Probar Localmente

```bash
cd chatbot
npm install
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000) y prueba una consulta.

**Logs esperados**:
```
[RAG] 📥 Descargando índice desde GitHub: https://raw.githubusercontent.com/...
[RAG] ✅ Índice descargado: 3210 documentos (gzip)
[RAG] Query "ordenanza presupuesto" completada en 450ms
[RAG] Recuperados 5 documentos relevantes
[RAG] Cache: 5 archivos en memoria
```

Si ves estos logs, ¡funciona! 🎉

---

## ☁️ Paso 3: Deploy a Vercel

### 3.1. Conectar Repositorio

1. Ve a [vercel.com](https://vercel.com) y haz login
2. Click en "Add New Project"
3. Importa tu repositorio `sibom-scraper-assistant`
4. Vercel detectará automáticamente Next.js

### 3.2. Configurar Build

**Root Directory**: `chatbot`

**Build Command** (default está bien):
```bash
npm run build
```

**Output Directory**: `.next`

### 3.3. Configurar Variables de Entorno

En "Environment Variables", agrega:

| Variable | Value | Environments |
|----------|-------|--------------|
| `OPENROUTER_API_KEY` | `sk-or-v1-tu-clave` | Production, Preview, Development |
| `ANTHROPIC_MODEL` | `google/gemini-3-flash-preview` | Production, Preview, Development |
| `GITHUB_DATA_REPO` | `TU-USUARIO/sibom-data` | Production, Preview, Development |
| `GITHUB_DATA_BRANCH` | `main` | Production, Preview, Development |
| `GITHUB_USE_GZIP` | `true` | Production, Preview, Development |
| `NEXT_PUBLIC_APP_URL` | `https://tu-app.vercel.app` | Production |
| `NODE_ENV` | `production` | Production |

**IMPORTANTE**: Reemplaza:
- `TU-USUARIO` con tu usuario de GitHub
- `tu-app` con el nombre de tu app en Vercel

### 3.4. Deploy

Click en "Deploy" y espera ~2-3 minutos.

Vercel te dará una URL como: `https://sibom-chatbot-abc123.vercel.app`

---

## 🧪 Paso 4: Verificar Deployment

### 4.1. Probar Chat

1. Abre la URL de Vercel
2. Escribe una consulta: "ordenanzas de presupuesto"
3. Debe responder con datos reales

### 4.2. Verificar Logs

En Vercel Dashboard → Functions → Logs, deberías ver:

```
[RAG] 📥 Descargando índice desde GitHub...
[RAG] ✅ Índice cargado: 3210 documentos (fuente: GitHub)
```

### 4.3. Monitorear Bandwidth

**GitHub**:
- Ve a Settings → Actions → Usage
- Bandwidth usado se muestra aquí
- Límite: 100 GB/mes (gratis)

**Vercel**:
- Dashboard → Analytics → Bandwidth
- Límite: 100 GB/mes (gratis)

---

## 📊 Análisis de Costos

### Sin Compresión

**Bandwidth por consulta**:
- Primera consulta: 772 KB (índice) + 2.5 MB (5 archivos) = **3.3 MB**
- Consultas siguientes (cache): **~0.5 MB** promedio

**100 consultas/día**:
- Mes: 100 × 30 = 3,000 consultas
- Bandwidth: ~1.5 GB/mes (bien dentro del límite gratuito)

### Con Compresión (Gzip)

**Bandwidth por consulta**:
- Primera consulta: 150 KB (índice gz) + 500 KB (5 archivos gz) = **650 KB**
- Consultas siguientes: **~100 KB** promedio

**100 consultas/día**:
- Mes: 3,000 consultas
- Bandwidth: ~300 MB/mes (**5x ahorro vs sin comprimir**)

### Costo de LLM

| Modelo | Input | Output | 100 consultas | 3,000/mes |
|--------|-------|--------|---------------|-----------|
| Claude 3.5 Sonnet | $3/1M | $15/1M | $0.05 | $1.50 |
| Gemini 3 Flash | $0.30/1M | $1.20/1M | $0.005 | $0.15 |
| GLM 4.5 Air (free) | $0 | $0 | $0 | $0 |

**Recomendación**: Usar Gemini 3 Flash para MVP (10x más barato, calidad excelente)

---

## 🔧 Troubleshooting

### Error: "GitHub respondió con status 404"

**Causa**: Repo privado o URL incorrecta

**Solución**:
1. Verifica que el repo sea **público**
2. Verifica la variable `GITHUB_DATA_REPO` (formato: `usuario/repo`)
3. Prueba la URL manual en el navegador

### Error: "Error descomprimiendo archivo"

**Causa**: Archivos no están comprimidos pero `GITHUB_USE_GZIP=true`

**Solución**:
- Cambia `GITHUB_USE_GZIP=false` en Vercel
- O comprime los archivos con `comprimir_boletines.py`

### Cache no funciona (descarga siempre)

**Causa**: Variables de cache de Next.js no respetadas

**Solución**:
```typescript
// En retriever.ts, ajustar:
const response = await fetch(url, {
  cache: 'force-cache',
  next: { revalidate: 3600 } // 1 hora
});
```

### Consultas lentas (>2 segundos)

**Causas posibles**:
1. GitHub rate limit alcanzado
2. Cache frío (primera consulta)
3. Red lenta

**Soluciones**:
1. Usar token de GitHub (aumenta límite a 5,000 req/hora)
2. Aumentar duración de cache a 2 horas
3. Pre-warm cache con script de healthcheck

---

## 🚀 Optimizaciones Avanzadas

### 1. Pre-warm Cache con Cron

Crea un endpoint `/api/healthcheck` que llame a `loadIndex()`:

```typescript
// chatbot/src/app/api/healthcheck/route.ts
import { loadIndex } from '@/lib/rag/retriever';

export async function GET() {
  await loadIndex(); // Pre-carga índice en cache
  return Response.json({ status: 'ok' });
}
```

Configura Vercel Cron (archivo `vercel.json`):

```json
{
  "crons": [{
    "path": "/api/healthcheck",
    "schedule": "0 * * * *"
  }]
}
```

Esto mantiene el cache caliente cada hora.

### 2. Token de GitHub (Aumentar Límites)

1. Genera token en: https://github.com/settings/tokens
2. Permisos: Solo `public_repo` (read)
3. Agrega a Vercel:

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

4. Úsalo en fetch:

```typescript
const response = await fetch(url, {
  headers: {
    'Authorization': `token ${process.env.GITHUB_TOKEN}`
  }
});
```

### 3. CDN de GitHub (jsDelivr)

Alternativa a GitHub Raw con mejor performance:

```typescript
// Reemplazar:
https://raw.githubusercontent.com/user/repo/main/file.json

// Por:
https://cdn.jsdelivr.net/gh/user/repo@main/file.json
```

jsDelivr tiene CDN global (más rápido) pero cache de 12 horas.

---

## 📚 Recursos

- [Vercel Docs](https://vercel.com/docs)
- [GitHub Raw](https://raw.githubusercontent.com/)
- [OpenRouter Pricing](https://openrouter.ai/models)
- [Next.js Caching](https://nextjs.org/docs/app/building-your-application/caching)

---

## ✅ Checklist de Deployment

- [ ] Datos comprimidos con `comprimir_boletines.py`
- [ ] Repo GitHub `sibom-data` creado (público)
- [ ] Archivos subidos a GitHub
- [ ] Acceso a GitHub Raw verificado
- [ ] `.env.local` configurado con GitHub
- [ ] Probado localmente (`npm run dev`)
- [ ] Proyecto importado en Vercel
- [ ] Variables de entorno configuradas en Vercel
- [ ] Deploy exitoso
- [ ] Chat funcional en producción
- [ ] Logs verificados (sin errores)
- [ ] Bandwidth monitoreado

---

¡Listo! Tu chatbot está desplegado 100% gratis y optimizado. 🎉
