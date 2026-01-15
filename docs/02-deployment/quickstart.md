# 🚀 Quickstart: Deployment a Producción

## ¿Por qué GitHub → Vercel?

**El error que viste (`vercel --prod`)** ocurre porque Vercel CLI intenta deploy directo sin un build completo. El flujo profesional es:

```
❌ INCORRECTO: vercel --prod (deploy directo, errores de build)
✅ CORRECTO:   GitHub → Vercel (CI/CD automático, build completo)
```

**Ventajas del flujo GitHub:**
- ✅ Deploy automático en cada `git push`
- ✅ Build completo con todas las dependencias
- ✅ Preview deployments para testing
- ✅ Rollback fácil a commits anteriores
- ✅ Logs completos de build y runtime

---

## 🎯 Setup en 5 Minutos

### 1. Preparar Código

```bash
# Verificar que datos NO estén en Git
./prepare_for_github.sh

# Push a GitHub
git add .
git commit -m "feat: Deployment con arquitectura R2"
git push origin main
```

### 2. Conectar Vercel

1. Ir a https://vercel.com/new
2. Click **"Import Git Repository"**
3. Seleccionar `sibom-scraper-assistant`
4. Configurar:
   - **Framework**: Next.js
   - **Root Directory**: `chatbot`
5. Click **"Deploy"** (fallará - falta configuración)

### 3. Configurar Variables

Vercel Dashboard → Settings → Environment Variables:

```env
OPENROUTER_API_KEY       = sk-or-v1-xxxxx
LLM_MODEL_PRIMARY        = anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC       = google/gemini-flash-1.5
GITHUB_DATA_REPO         = pub-xxxxx.r2.dev/sibom-data
GITHUB_DATA_BRANCH       = (vacío)
GITHUB_USE_GZIP          = true
USE_NORMATIVAS_INDEX     = true
INDEX_CACHE_DURATION     = 3600000
```

**⚠️ IMPORTANTE:** `GITHUB_DATA_REPO` es la URL de tu bucket R2 (sin `https://`)

### 4. Redeploy

```bash
# Opción A: Desde GitHub
git commit --allow-empty -m "chore: Trigger deployment"
git push

# Opción B: Desde Vercel Dashboard
# Deployments → Latest → Redeploy
```

### 5. Verificar

Abrir: `https://tu-proyecto.vercel.app`

Test query: **"decretos de Carlos Tejedor"**

---

## 📦 ¿Y los Datos?

**Los datos NO van a GitHub** (son 3 GB sin comprimir).

Los datos van a **Cloudflare R2**:

```bash
cd python-cli

# 1. Comprimir
python compress_for_r2.py

# 2. Subir a R2
npm install -g wrangler
wrangler login
./upload_to_r2.sh
```

**Estructura final:**

```
GitHub (código)           Cloudflare R2 (datos)      Vercel (app)
├── chatbot/       ←────  ├── normativas_index.gz   ───▶ Build & Deploy
├── python-cli/           └── boletines/*.gz
└── README.md
```

---

## 🔄 Workflow Continuo

Cada vez que hagas cambios:

```bash
# Código
git add .
git commit -m "feat: Nueva funcionalidad"
git push
# Vercel detecta el push y deploya automáticamente ✅
```

Cuando scrapees más datos:

```bash
# Datos
cd python-cli
python sibom_scraper.py --municipality "Nuevo"
python normativas_extractor.py
python compress_for_r2.py
./upload_to_r2.sh
# NO necesitas git push - datos van a R2 directamente ✅
```

---

## ❓ FAQ

### ¿Por qué falló `vercel --prod`?

Vercel CLI necesita que ejecutes `npm run build` localmente primero, pero tu app Next.js requiere variables de entorno de producción que solo están en Vercel. El flujo GitHub → Vercel resuelve esto automáticamente.

### ¿Cuánto cuesta?

- **Cloudflare R2**: $0 (10 GB gratis)
- **Vercel**: $0 (100 GB bandwidth gratis)
- **OpenRouter**: Variable según uso (~$0.003/query con Claude)

### ¿Puedo usar otro hosting?

Sí, pero Vercel es el más fácil para Next.js:
- **Vercel**: Zero-config, recomendado ⭐
- **Netlify**: Requiere configuración extra
- **Docker**: Requiere Dockerfile custom
- **Cloudflare Pages**: Posible, más complejo

### ¿Cómo hago rollback?

Vercel Dashboard → Deployments → Deployment anterior → "Promote to Production"

O:
```bash
git revert HEAD
git push
```

---

## 📚 Documentación Completa

- **[DEPLOYMENT_GITHUB.md](DEPLOYMENT_GITHUB.md)** - Guía completa paso a paso
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Checklist detallado
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detalles técnicos de R2 y Vercel

---

**¿Listo?** Sigue [DEPLOYMENT_GITHUB.md](DEPLOYMENT_GITHUB.md) para el flujo completo.
