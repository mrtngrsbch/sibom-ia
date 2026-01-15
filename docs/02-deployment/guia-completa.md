# Deployment Guide - SIBOM Chatbot

## Arquitectura de Produccion

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Vercel        │────▶│   Next.js Server     │────▶│  Cloudflare R2  │
│   (Frontend)    │     │   (API Routes)       │     │  (Datos)        │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
                                  │
                                  ▼
                        ┌──────────────────────┐
                        │   OpenRouter API     │
                        │   (LLM)              │
                        └──────────────────────┘
```

## Fase 1: Preparar Datos para R2

### 1.1 Comprimir Datos

```bash
cd python-cli
python compress_for_r2.py
```

Resultado:
- `dist/normativas_index_minimal.json.gz` (5.3 MB)
- `dist/boletines/*.json.gz` (332 MB total)

### 1.2 Crear Bucket en R2

1. Ir a [Cloudflare Dashboard](https://dash.cloudflare.com) → R2
2. Crear bucket: `sibom-data`
3. Habilitar acceso público:
   - Settings → Public access → Allow Access
   - Anotar la URL pública: `https://pub-xxxxx.r2.dev`

### 1.3 Subir Datos a R2

**Opcion A: Dashboard (archivos pequeños)**
- Subir `dist/` directamente desde el navegador

**Opcion B: Wrangler CLI (recomendado)**
```bash
# Instalar wrangler
npm install -g wrangler

# Login
wrangler login

# Subir índice
wrangler r2 object put sibom-data/normativas_index_minimal.json.gz \
  --file dist/normativas_index_minimal.json.gz

# Subir boletines (puede tomar varios minutos)
for f in dist/boletines/*.gz; do
  wrangler r2 object put "sibom-data/boletines/$(basename $f)" --file "$f"
done
```

**Opcion C: rclone (para muchos archivos)**
```bash
# Configurar rclone con R2
rclone config
# Seguir wizard: tipo=s3, provider=Cloudflare, ...

# Subir todo
rclone copy dist/ r2:sibom-data/ --progress
```

## Fase 2: Configurar Vercel

### 2.1 Variables de Entorno

En Vercel Dashboard → Settings → Environment Variables:

```env
# LLM (requerido)
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Modelo primario (para respuestas detalladas)
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet

# Modelo económico (para FAQs simples)
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5

# Datos desde R2 (requerido para producción)
GITHUB_DATA_REPO=pub-xxxxx.r2.dev/sibom-data
GITHUB_DATA_BRANCH=  # Dejar vacío para R2
GITHUB_USE_GZIP=true

# Cache (opcional, ajustar según necesidad)
INDEX_CACHE_DURATION=3600000  # 1 hora

# Usar nuevo índice de normativas
USE_NORMATIVAS_INDEX=true
```

> **Nota**: Aunque la variable se llama `GITHUB_DATA_REPO`, funciona con cualquier URL pública (R2, S3, etc.)

### 2.2 Configurar URL Base para R2

El retriever construye URLs así:
```
https://raw.githubusercontent.com/${GITHUB_DATA_REPO}/${GITHUB_DATA_BRANCH}/...
```

Para R2, configurar:
```env
GITHUB_DATA_REPO=pub-xxxxx.r2.dev/sibom-data
GITHUB_DATA_BRANCH=
```

Esto genera:
```
https://pub-xxxxx.r2.dev/sibom-data/normativas_index_minimal.json.gz
https://pub-xxxxx.r2.dev/sibom-data/boletines/Carlos_Tejedor_57.json.gz
```

### 2.3 Deploy

```bash
cd chatbot
vercel --prod
```

## Fase 3: Verificar Deployment

### 3.1 Test del Índice

```bash
curl -I "https://pub-xxxxx.r2.dev/sibom-data/normativas_index_minimal.json.gz"
# Debe retornar 200 OK
```

### 3.2 Test de un Boletín

```bash
curl -I "https://pub-xxxxx.r2.dev/sibom-data/boletines/Carlos_Tejedor_57.json.gz"
# Debe retornar 200 OK
```

### 3.3 Test del Chatbot

1. Abrir `https://tu-app.vercel.app`
2. Probar query: "decretos de Carlos Tejedor en 2025"
3. Verificar que retorne resultados

## Actualizar Datos Incrementalmente

### Cuando scrapees más municipios:

```bash
# 1. Scrapear nuevos datos
cd python-cli
python sibom_scraper.py --municipality "Nuevo Municipio"

# 2. Re-generar índice (incluye todos los boletines)
python normativas_extractor.py

# 3. Comprimir nuevos archivos
python compress_for_r2.py

# 4. Subir a R2
# Solo los nuevos boletines + índice actualizado
wrangler r2 object put sibom-data/normativas_index_minimal.json.gz \
  --file dist/normativas_index_minimal.json.gz

# Nuevos boletines
for f in dist/boletines/Nuevo_Municipio_*.gz; do
  wrangler r2 object put "sibom-data/boletines/$(basename $f)" --file "$f"
done
```

### Invalidar Cache en Producción

Si actualizas datos y el chatbot no los detecta:

```bash
# Vercel redeploy fuerza refresh del cache
vercel --prod --force
```

## Costos Estimados

### Cloudflare R2 (Free Tier)
- 10 GB almacenamiento: **$0** ✅
- 10M requests/mes Class A: **$0** ✅
- 10M requests/mes Class B: **$0** ✅

### Vercel (Free Tier)
- 100 GB bandwidth/mes: **$0** ✅
- Serverless functions: **$0** ✅

### OpenRouter
- Depende del modelo y uso
- Claude 3.5 Sonnet: ~$0.003/query promedio
- Gemini Flash: ~$0.0001/query promedio

## Troubleshooting

### Error: "CORS policy"
- Verificar que R2 bucket tenga acceso público habilitado
- Configurar CORS en R2 si es necesario

### Error: "404 Not Found"
- Verificar URL del bucket R2
- Confirmar que los archivos se subieron correctamente

### Error: "Índice vacío"
- Verificar `GITHUB_USE_GZIP=true`
- Confirmar que el archivo .gz existe en R2

### Respuestas lentas
- Aumentar `INDEX_CACHE_DURATION`
- Verificar que `USE_NORMATIVAS_INDEX=true`

---

## Próximos Pasos (Fase 2)

Una vez estabilizado el deployment:

1. **sql.js para exploración client-side**
   - Búsqueda instantánea sin servidor
   - Filtros, tablas, ordenamiento
   - Funciona offline

2. **Service Worker para cache**
   - Cache del índice en browser
   - Experiencia offline completa

Ver [TODO] para tracking de estas mejoras.
