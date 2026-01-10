# 🎯 Próximos Pasos para Completar el Deployment

**Estado actual:** Código en GitHub ✅ | Datos comprimidos ✅ | Falta: R2 + Vercel

---

## 📦 PASO 1: Subir Datos a Cloudflare R2 (15 minutos)

### Opción A: CLI con Wrangler (Recomendado - Automático)

```bash
# 1. Instalar Wrangler
npm install -g wrangler

# 2. Login en Cloudflare
wrangler login
# Se abrirá el navegador para autenticarte

# 3. Crear bucket (solo primera vez)
wrangler r2 bucket create sibom-data

# 4. Habilitar acceso público
# Ir a: https://dash.cloudflare.com → R2 → sibom-data → Settings
# En "Public access" → Click "Allow Access"
# ANOTAR la URL pública: pub-xxxxx.r2.dev

# 5. Subir archivos
cd python-cli
./upload_to_r2.sh
```

**Tiempo estimado:** 5-10 minutos (depende de tu conexión)

---

### Opción B: Dashboard de Cloudflare (Manual)

Si prefieres hacerlo manualmente:

1. **Crear bucket:**
   - Ir a https://dash.cloudflare.com → R2 Object Storage
   - Click "Create bucket"
   - Nombre: `sibom-data`
   - Click "Create bucket"

2. **Habilitar acceso público:**
   - Dentro del bucket → Settings
   - Sección "Public access" → "Allow Access"
   - **ANOTAR URL:** `pub-xxxxx.r2.dev` ⚠️ IMPORTANTE

3. **Subir archivos:**
   - En la raíz del bucket:
     - Subir: `python-cli/dist/normativas_index_minimal.json.gz`
   
   - Crear carpeta `boletines`:
     - Click "Create folder" → Nombre: `boletines`
     - Entrar a la carpeta
     - Subir todos los archivos de: `python-cli/dist/boletines/*.gz`
     - Son ~1,740 archivos (puede tomar 10-15 minutos)

**Tiempo estimado:** 15-20 minutos

---

## 🚀 PASO 2: Deploy en Vercel (10 minutos)

### 2.1 Importar Proyecto

1. Ir a https://vercel.com/new
2. Click **"Import Git Repository"**
3. Buscar y seleccionar: `mrtngrsbch/sibom-ia`
4. Configurar proyecto:

```
Framework Preset: Next.js
Root Directory: chatbot
Build Command: npm run build (default)
Output Directory: .next (default)
Install Command: npm install (default)
```

5. Click **"Deploy"**
   - El primer deploy fallará (es normal, faltan variables)

---

### 2.2 Configurar Variables de Entorno

En Vercel Dashboard → Tu proyecto → Settings → Environment Variables

**Agregar estas 8 variables:**

#### 1. OPENROUTER_API_KEY
- **Value:** Tu API key de OpenRouter (obtener en https://openrouter.ai/keys)
- **Environments:** Production, Preview, Development

#### 2. LLM_MODEL_PRIMARY
- **Value:** `anthropic/claude-3.5-sonnet`
- **Environments:** Production, Preview, Development

#### 3. LLM_MODEL_ECONOMIC
- **Value:** `google/gemini-flash-1.5`
- **Environments:** Production, Preview, Development

#### 4. GITHUB_DATA_REPO
- **Value:** `pub-xxxxx.r2.dev/sibom-data` ⚠️ Reemplazar con tu URL de R2
- **Environments:** Production, Preview

#### 5. GITHUB_DATA_BRANCH
- **Value:** _(dejar vacío)_
- **Environments:** Production, Preview

#### 6. GITHUB_USE_GZIP
- **Value:** `true`
- **Environments:** Production, Preview, Development

#### 7. USE_NORMATIVAS_INDEX
- **Value:** `true`
- **Environments:** Production, Preview, Development

#### 8. INDEX_CACHE_DURATION
- **Value:** `3600000`
- **Environments:** Production, Preview, Development

---

### 2.3 Redeploy

Después de configurar todas las variables:

1. Ir a: Vercel Dashboard → Deployments
2. Click en el último deployment (el que falló)
3. Click en los 3 puntos "..." → **"Redeploy"**
4. Esperar 2-3 minutos

---

## ✅ PASO 3: Verificar que Todo Funciona

### 3.1 Verificar Build

En Vercel Dashboard → Deployments → Latest

**Buscar en los logs:**
```
✓ Linting and checking validity of types
✓ Creating an optimized production build
✓ Compiled successfully
```

Si ves errores, revisar las variables de entorno.

---

### 3.2 Test del Sitio

Tu URL será algo como: `https://sibom-ia.vercel.app`

**Tests básicos:**

1. **Query simple:**
   - Escribir: "decretos de Carlos Tejedor"
   - Debe retornar resultados con enlaces a SIBOM

2. **Query específica:**
   - Escribir: "ordenanza 2833"
   - Debe encontrar la ordenanza específica

3. **Query de conteo:**
   - Escribir: "cuántos decretos hay"
   - Debe retornar estadísticas

4. **Verificar enlaces:**
   - Click en "Ver en SIBOM"
   - Debe abrir el boletín oficial en SIBOM

---

### 3.3 Verificar Logs

En Vercel Dashboard → Deployments → Latest → Function Logs

**Buscar esta línea:**
```
[RAG] ✅ Índice de normativas cargado: 216,506 normativas (fuente: GitHub)
```

**Si ves "fuente: local":**
- Variables mal configuradas
- Revisar `GITHUB_DATA_REPO` en Vercel

**Si ves errores 404:**
- Verificar que archivos estén en R2
- Verificar que R2 bucket tenga acceso público

---

## 🎉 DEPLOYMENT COMPLETADO

Si todos los tests pasan:

✅ **Tu aplicación está en producción:**
- Frontend: `https://sibom-ia.vercel.app`
- Datos: Cloudflare R2
- LLM: OpenRouter

---

## 🔄 Workflow Futuro

### Actualizar Código

```bash
# Hacer cambios en el código
git add .
git commit -m "feat: Nueva funcionalidad"
git push origin main

# Vercel detecta el push y hace deploy automático
```

### Actualizar Datos

```bash
# 1. Scrapear nuevos municipios
cd python-cli
python3 sibom_scraper.py --municipality "Nuevo Municipio"

# 2. Re-generar índice
python3 normativas_extractor.py

# 3. Comprimir
python3 compress_for_r2.py

# 4. Subir a R2
./upload_to_r2.sh

# El chatbot detectará los cambios automáticamente
```

---

## 🔧 Troubleshooting Rápido

### Error: "Build failed"
- Verificar Root Directory: `chatbot` en Vercel Settings

### Error: "Module not found"
```bash
cd chatbot
rm -rf node_modules package-lock.json
npm install
git add package-lock.json
git commit -m "fix: Update dependencies"
git push
```

### Error: "404 Not Found" en queries
- Verificar `GITHUB_DATA_REPO` en Vercel
- Confirmar archivos en R2
- Verificar acceso público en R2

### Sitio lento
- Verificar `INDEX_CACHE_DURATION=3600000`
- Verificar `USE_NORMATIVAS_INDEX=true`

---

## 📞 Soporte

- **Documentación completa:** `DEPLOYMENT_GITHUB.md`
- **Checklist detallado:** `DEPLOYMENT_CHECKLIST.md`
- **Estado actual:** `DEPLOYMENT_STATUS.md`

---

**Última actualización:** 2026-01-10  
**Tiempo estimado total:** 25-30 minutos  
**Dificultad:** Media (requiere cuentas en Cloudflare y Vercel)
