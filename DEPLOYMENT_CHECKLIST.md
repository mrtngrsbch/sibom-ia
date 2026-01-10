# ✅ Checklist de Deployment - SIBOM Chatbot

Sigue estos pasos en orden. Marca ✅ cuando completes cada uno.

---

## 📋 PRE-REQUISITOS

- [ ] Cuenta de Cloudflare creada (gratis)
- [ ] Cuenta de Vercel creada (gratis)
- [ ] OpenRouter API Key obtenida de https://openrouter.ai/keys
- [ ] Node.js y npm instalados
- [ ] Datos comprimidos en `python-cli/dist/`

---

## ☁️ PASO 1: CLOUDFLARE R2

### 1.1 Crear Bucket

- [ ] Ir a https://dash.cloudflare.com → **R2 Object Storage**
- [ ] Click **"Create bucket"**
- [ ] Nombre: `sibom-data`
- [ ] Click **"Create bucket"**

### 1.2 Habilitar Acceso Público

- [ ] Dentro del bucket → **Settings**
- [ ] Sección "Public access" → **"Allow Access"**
- [ ] **Anotar URL pública**: `pub-xxxxx.r2.dev` ⚠️ IMPORTANTE

### 1.3 Subir Archivos

**Opción A: Dashboard (fácil)**
- [ ] Subir `normativas_index_minimal.json.gz` a raíz
- [ ] Crear carpeta `boletines`
- [ ] Subir todos los `.gz` de `python-cli/dist/boletines/`

**Opción B: Wrangler CLI (rápido)**
```bash
npm install -g wrangler
wrangler login
cd python-cli
./upload_to_r2.sh
```

- [ ] Archivos subidos correctamente
- [ ] Verificar en R2 Dashboard que aparecen los archivos

---

## 🚀 PASO 2: VERCEL

### 2.1 Deploy Inicial

```bash
cd chatbot
npm install -g vercel
vercel
```

- [ ] Proyecto creado en Vercel
- [ ] Deploy inicial exitoso
- [ ] **Anotar URL del proyecto**: `https://tu-proyecto.vercel.app`

### 2.2 Configurar Variables de Entorno

**Opción A: Dashboard (recomendado)**

Ir a: https://vercel.com/dashboard → Tu proyecto → **Settings** → **Environment Variables**

Agregar estas variables:

| Variable | Valor | Environments |
|----------|-------|--------------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | Production, Preview, Development |
| `LLM_MODEL_PRIMARY` | `anthropic/claude-3.5-sonnet` | Production, Preview, Development |
| `LLM_MODEL_ECONOMIC` | `google/gemini-flash-1.5` | Production, Preview, Development |
| `GITHUB_DATA_REPO` | `pub-xxxxx.r2.dev/sibom-data` | Production, Preview |
| `GITHUB_DATA_BRANCH` | _(vacío)_ | Production, Preview |
| `GITHUB_USE_GZIP` | `true` | Production, Preview, Development |
| `USE_NORMATIVAS_INDEX` | `true` | Production, Preview, Development |
| `INDEX_CACHE_DURATION` | `3600000` | Production, Preview, Development |

**Opción B: CLI (automático)**

```bash
cd chatbot
./setup_vercel_env.sh
```

- [ ] 8 variables configuradas correctamente
- [ ] Screenshot guardado como backup (recomendado)

### 2.3 Redeploy con Variables

```bash
cd chatbot
vercel --prod
```

- [ ] Deploy completado
- [ ] URL de producción funcionando

---

## 🧪 PASO 3: VERIFICACIÓN

### 3.1 Test de R2

```bash
# Verificar que los archivos son accesibles
curl -I "https://pub-xxxxx.r2.dev/sibom-data/normativas_index_minimal.json.gz"
# Debe retornar: HTTP/2 200
```

- [ ] Índice accesible (200 OK)
- [ ] Boletín de prueba accesible (200 OK)

### 3.2 Test del Chatbot

Abrir: `https://tu-proyecto.vercel.app`

**Tests básicos:**

- [ ] Página carga correctamente
- [ ] Query: "decretos de Carlos Tejedor en 2025"
  - [ ] Retorna resultados (no "not found")
  - [ ] URLs de "Ver en SIBOM" funcionan
  - [ ] Enlaces apuntan a diferentes boletines (no duplicados)

- [ ] Query: "ordenanza 2833"
  - [ ] Encuentra la ordenanza específica
  - [ ] Muestra contenido relevante

- [ ] Query: "cuántos decretos hay"
  - [ ] Retorna estadísticas

**Verificar en logs de Vercel:**

```
✅ Índice de normativas cargado: 216,506 normativas (fuente: GitHub)
🔍 INICIO - Índice de normativas: 216506 registros
✅ Query completada en XXXms
```

- [ ] Logs muestran "fuente: GitHub" (no "local")
- [ ] Sin errores 404 en los logs

### 3.3 Test de Performance

- [ ] Primera query tarda <5 segundos
- [ ] Queries subsiguientes tardan <2 segundos
- [ ] Streaming funciona (respuesta aparece progresivamente)

---

## 🎯 PASO 4: MONITOREO

### 4.1 Configurar Alertas (opcional)

Vercel Dashboard → Monitoring → Alerts

- [ ] Alerta de error rate > 5%
- [ ] Alerta de latencia > 10s

### 4.2 Revisar Costos

**Cloudflare R2:**
- [ ] Verificar en Dashboard → R2 → Usage
- [ ] Free tier: 10 GB storage, 10M requests/mes

**Vercel:**
- [ ] Verificar en Dashboard → Usage
- [ ] Free tier: 100 GB bandwidth/mes

**OpenRouter:**
- [ ] Verificar en https://openrouter.ai/activity
- [ ] Monitorear costos diarios

---

## 🔄 PASO 5: ACTUALIZACIÓN INCREMENTAL (FUTURO)

Cuando scrapees más municipios:

```bash
# 1. Scrapear nuevos datos
cd python-cli
python sibom_scraper.py --municipality "Nuevo Municipio"

# 2. Re-generar índice
python normativas_extractor.py

# 3. Comprimir
python compress_for_r2.py

# 4. Subir a R2
./upload_to_r2.sh

# 5. Invalidar cache en Vercel
cd ../chatbot
vercel --prod --force
```

- [ ] Workflow de actualización probado

---

## 🚨 TROUBLESHOOTING

### Error: "CORS policy"
- Verificar que R2 bucket tenga "Public access" habilitado

### Error: "404 Not Found"
- Verificar `GITHUB_DATA_REPO` en Vercel
- Confirmar archivos en R2 con nombres correctos

### Error: "Índice vacío"
- Verificar `GITHUB_USE_GZIP=true` en Vercel
- Confirmar que archivo `.gz` existe en R2

### Respuestas lentas
- Aumentar `INDEX_CACHE_DURATION` a 3600000
- Verificar que `USE_NORMATIVAS_INDEX=true`

### Error: "Not found" en queries válidos
- Verificar logs de Vercel
- Confirmar que índice tiene datos: logs deben mostrar "216,506 normativas"

---

## ✨ DEPLOYMENT COMPLETADO

Si marcaste ✅ todos los items:

🎉 **Tu chatbot está en producción**

- Frontend: `https://tu-proyecto.vercel.app`
- Backend datos: Cloudflare R2
- LLM: OpenRouter

**Próximos pasos (Fase 2):**
- Implementar sql.js para exploración client-side
- Agregar listas y tablas de normativas
- Modo offline con Service Worker

---

**Última actualización:** 2026-01-09
**Versión del sistema:** 1.0.0
