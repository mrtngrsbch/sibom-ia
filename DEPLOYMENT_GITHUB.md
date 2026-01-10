# Deployment via GitHub → Vercel (Flujo Recomendado)

Este es el flujo **profesional y estándar** para deployment en producción.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Código    │────▶│   GitHub    │────▶│   Vercel    │────▶│ Producción  │
│   Local     │ git │   Repo      │ auto│   Build     │     │   Live      │
└─────────────┘push └─────────────┘deploy└─────────────┘     └─────────────┘
```

---

## ✅ PRE-REQUISITOS

- [x] Cuenta de GitHub
- [x] Cuenta de Vercel
- [x] Cuenta de Cloudflare con bucket R2 creado
- [x] Datos subidos a Cloudflare R2
- [x] Git instalado localmente

---

## 📦 PASO 1: Preparar el Repositorio

### 1.1 Verificar que datos NO estén en el repo

Los datos (boletines, índices) **NO van a GitHub** - van a Cloudflare R2.

```bash
# Verificar .gitignore
cat .gitignore | grep boletines
# Debe mostrar: python-cli/boletines/*.json

# Verificar que no haya archivos grandes
git status
# NO debe aparecer nada en python-cli/boletines/
```

### 1.2 Commit y Push del Código

```bash
# Ver cambios
git status

# Agregar archivos necesarios
git add chatbot/
git add python-cli/*.py
git add README.md
git add DEPLOYMENT_GITHUB.md
# NO agregues python-cli/boletines/ ni python-cli/dist/

# Commit
git commit -m "feat: Preparar deployment con arquitectura R2"

# Push a GitHub
git push origin main
```

---

## 🔗 PASO 2: Conectar Vercel con GitHub

### 2.1 Importar Proyecto en Vercel

1. Ir a https://vercel.com/new
2. Click **"Import Git Repository"**
3. Seleccionar tu repo: `sibom-scraper-assistant`
4. Configurar proyecto:

```
Framework Preset: Next.js
Root Directory: chatbot
Build Command: npm run build (default)
Output Directory: .next (default)
Install Command: npm install (default)
```

5. Click **"Deploy"** (fallará - es normal, faltan variables)

### 2.2 Configurar Variables de Entorno

En Vercel Dashboard → Settings → Environment Variables:

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

### 2.3 Redeploy

Después de configurar variables:

1. Vercel Dashboard → Deployments
2. Click en el último deployment (failed)
3. Click **"Redeploy"**

O desde GitHub:

```bash
# Trigger nuevo deploy con commit vacío
git commit --allow-empty -m "chore: Trigger Vercel deployment"
git push
```

---

## 🎯 PASO 3: Verificar Deployment

### 3.1 Ver Build Logs

Vercel Dashboard → Deployments → Latest → View Build Logs

**Buscar estas líneas:**
```
✓ Linting and checking validity of types
✓ Creating an optimized production build
✓ Compiled successfully
```

### 3.2 Test del Sitio

URL de producción: `https://sibom-chatbot.vercel.app`

**Tests:**
1. Query: "decretos de Carlos Tejedor"
2. Verificar que retorne resultados
3. Click en "Ver en SIBOM" - debe abrir SIBOM oficial

### 3.3 Verificar Logs

Vercel Dashboard → Deployments → Latest → Function Logs

**Buscar:**
```
[RAG] ✅ Índice de normativas cargado: 216,506 normativas (fuente: GitHub)
```

Si ves "fuente: local" → Variables mal configuradas

---

## 🔄 PASO 4: Workflow Continuo

### Deploy Automático

Cada vez que hagas `git push`:

1. Vercel detecta el push
2. Ejecuta build automáticamente
3. Deploy a producción si es branch `main`
4. Deploy preview si es otra branch

### Preview Deployments

```bash
# Crear branch para feature
git checkout -b feature/nueva-funcionalidad

# Hacer cambios
# ...

# Push
git push origin feature/nueva-funcionalidad
```

Vercel crea URL preview automática: `https://sibom-chatbot-git-feature-nueva-funcionalidad.vercel.app`

### Actualizar Datos (R2)

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

# NO NECESITAS hacer git push - Vercel ya tiene la configuración correcta
# El cambio en R2 es detectado automáticamente por el chatbot
```

**Opcional:** Si quieres forzar refresh del cache:

```bash
# Trigger redeploy
git commit --allow-empty -m "chore: Invalidate cache"
git push
```

---

## 📊 PASO 5: Monitoreo y Mantenimiento

### Monitoreo de Deployments

Vercel Dashboard → Analytics:
- Pageviews
- Response times
- Error rate
- Bandwidth usage

### Rollback si Hay Problemas

Si un deployment tiene bugs:

1. Vercel Dashboard → Deployments
2. Buscar deployment anterior que funcionaba
3. Click "..." → **"Promote to Production"**

O desde git:

```bash
git revert HEAD
git push
```

### Ver Logs en Tiempo Real

```bash
# CLI de Vercel (opcional)
npm install -g vercel
vercel logs --follow
```

---

## 🔧 TROUBLESHOOTING

### Error: "Build failed"

**Posible causa:** Configuración incorrecta de root directory

**Solución:**
1. Vercel Dashboard → Settings → General
2. Root Directory: `chatbot`
3. Redeploy

### Error: "Module not found"

**Posible causa:** `package-lock.json` desactualizado

**Solución:**
```bash
cd chatbot
rm -rf node_modules package-lock.json
npm install
git add package-lock.json
git commit -m "fix: Update dependencies"
git push
```

### Error: "Environment variable missing"

**Posible causa:** Variables no configuradas

**Solución:**
1. Vercel Dashboard → Settings → Environment Variables
2. Agregar variable faltante
3. Redeploy

### Sitio lento o errores 500

**Posible causa:** R2 no accesible o índice corrupto

**Verificar:**
```bash
curl -I "https://pub-xxxxx.r2.dev/sibom-data/normativas_index_minimal.json.gz"
# Debe retornar 200 OK
```

---

## ⚙️ CONFIGURACIONES AVANZADAS

### Custom Domain

1. Vercel Dashboard → Settings → Domains
2. Add domain: `chatbot.tu-dominio.com`
3. Configurar DNS según instrucciones

### Branch Protection

Vercel Dashboard → Settings → Git:
- Production Branch: `main`
- Preview Branches: All branches

### Build & Development Settings

```yaml
# vercel.json (opcional, en raíz de chatbot/)
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "outputDirectory": ".next"
}
```

---

## 📋 CHECKLIST COMPLETO

- [ ] Código pushed a GitHub
- [ ] Proyecto importado en Vercel desde GitHub
- [ ] Root directory configurado: `chatbot`
- [ ] 8 variables de entorno configuradas
- [ ] Deployment exitoso (verde en Vercel)
- [ ] URL de producción funciona
- [ ] Tests de queries exitosos
- [ ] Logs muestran "fuente: GitHub" (R2)
- [ ] Preview deployments configurados
- [ ] Monitoreo activo

---

## 🎉 DEPLOYMENT COMPLETADO

Si todos los checks están ✅:

**Tu aplicación está live y profesionalmente deployada:**

- 🌍 Producción: `https://sibom-chatbot.vercel.app`
- 🔄 CI/CD: Automático en cada push
- 📦 Datos: Cloudflare R2
- 🤖 LLM: OpenRouter

**Ventajas de este setup:**
- Zero-downtime deployments
- Rollback instantáneo
- Preview para testing
- Logs y analytics completos
- Escalable a millones de requests

---

**Última actualización:** 2026-01-09
**Flujo:** GitHub → Vercel (Recomendado)
