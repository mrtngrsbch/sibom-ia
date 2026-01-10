# 🚀 Estado del Deployment - SIBOM Chatbot

**Fecha:** 2026-01-10  
**Repositorio:** https://github.com/mrtngrsbch/sibom-ia.git

---

## ✅ COMPLETADO

### 1. Preparación del Código
- [x] Código limpio y organizado
- [x] `.gitignore` actualizado (excluye archivos >100MB)
- [x] Documentación de deployment completa
- [x] Variables de entorno documentadas
- [x] Scripts de deployment preparados

### 2. GitHub
- [x] Código pushed a GitHub exitosamente
- [x] Repositorio: `mrtngrsbch/sibom-ia`
- [x] Branch: `main`
- [x] Commit: `a06511a1` - "fix: Resolver conflictos de dependencias para Vercel"

### 3. Dependencias Arregladas
- [x] Actualizado `@testing-library/react` a v16.3.1 (compatible con React 19)
- [x] Agregado `@testing-library/dom@^10.0.0`
- [x] Configurado `vercel.json` para usar pnpm
- [x] Build local exitoso: ✓ Compiled successfully

**⚠️ Nota:** GitHub detectó 2 vulnerabilidades de dependencias (1 moderada, 1 baja)
- Ver: https://github.com/mrtngrsbch/sibom-ia/security/dependabot
- Acción recomendada: Revisar y actualizar dependencias después del deployment

---

## 🔄 PRÓXIMOS PASOS

### PASO 1: Subir Datos a Cloudflare R2

Los archivos de datos NO están en GitHub (son muy grandes). Debes subirlos a Cloudflare R2:

```bash
cd python-cli

# 1. Comprimir datos (si no lo hiciste ya)
python3 compress_for_r2.py

# 2. Subir a R2
# Opción A: Dashboard de Cloudflare (manual)
# - Ir a https://dash.cloudflare.com → R2
# - Crear bucket "sibom-data"
# - Habilitar acceso público
# - Subir archivos de dist/

# Opción B: CLI de Wrangler (automático)
npm install -g wrangler
wrangler login
./upload_to_r2.sh
```

**Archivos a subir:**
- `normativas_index_minimal.json.gz` (raíz del bucket)
- `boletines/*.json.gz` (carpeta boletines/)

**Anotar:** URL pública del bucket R2 (ej: `pub-xxxxx.r2.dev`)

---

### PASO 2: Deploy en Vercel

#### 2.1 Importar Proyecto

1. Ir a https://vercel.com/new
2. Click **"Import Git Repository"**
3. Seleccionar: `mrtngrsbch/sibom-ia`
4. Configurar:
   - **Framework Preset:** Next.js
   - **Root Directory:** `chatbot`
   - **Build Command:** `pnpm run build` (default)
   - **Output Directory:** `.next` (default)
5. Click **"Deploy"** (ahora debería funcionar con las dependencias arregladas)

#### 2.2 Configurar Variables de Entorno

En Vercel Dashboard → Settings → Environment Variables, agregar:

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

**⚠️ IMPORTANTE:** Reemplazar `pub-xxxxx.r2.dev` con tu URL real de R2

#### 2.3 Redeploy

Después de configurar variables:
1. Vercel Dashboard → Deployments
2. Click en el último deployment (failed)
3. Click **"Redeploy"**

---

### PASO 3: Verificar Deployment

#### 3.1 Test Básico

URL de producción: `https://sibom-ia.vercel.app` (o similar)

**Tests:**
1. Query: "decretos de Carlos Tejedor"
2. Verificar que retorne resultados
3. Click en "Ver en SIBOM" - debe abrir SIBOM oficial

#### 3.2 Verificar Logs

Vercel Dashboard → Deployments → Latest → Function Logs

**Buscar:**
```
[RAG] ✅ Índice de normativas cargado: 216,506 normativas (fuente: GitHub)
```

Si ves "fuente: local" → Variables mal configuradas

---

## 📋 CHECKLIST COMPLETO

### GitHub
- [x] Código pushed exitosamente
- [x] `.gitignore` excluye archivos grandes
- [x] Documentación completa

### Cloudflare R2
- [ ] Bucket creado
- [ ] Acceso público habilitado
- [ ] Archivos comprimidos subidos
- [ ] URL pública anotada

### Vercel
- [ ] Proyecto importado desde GitHub
- [ ] Root directory: `chatbot`
- [ ] 8 variables de entorno configuradas
- [ ] Deployment exitoso (verde)
- [ ] URL de producción funciona
- [ ] Tests de queries exitosos
- [ ] Logs muestran "fuente: GitHub"

---

## 📚 DOCUMENTACIÓN DE REFERENCIA

- **Guía completa:** `DEPLOYMENT_GITHUB.md`
- **Checklist detallado:** `DEPLOYMENT_CHECKLIST.md`
- **Quickstart:** `QUICKSTART_DEPLOYMENT.md`
- **Variables de entorno:** `chatbot/.env.example`

---

## 🔧 TROUBLESHOOTING

### Error: "404 Not Found" en queries
- Verificar `GITHUB_DATA_REPO` en Vercel
- Confirmar archivos en R2 con nombres correctos
- Verificar que R2 bucket tenga acceso público

### Error: "Índice vacío"
- Verificar `GITHUB_USE_GZIP=true` en Vercel
- Confirmar que archivo `.gz` existe en R2

### Respuestas lentas
- Aumentar `INDEX_CACHE_DURATION` a 3600000
- Verificar que `USE_NORMATIVAS_INDEX=true`

---

## 🎯 SIGUIENTE ACCIÓN INMEDIATA

**Subir datos a Cloudflare R2:**

```bash
cd python-cli
python3 compress_for_r2.py
# Luego subir manualmente o con wrangler
```

Una vez que los datos estén en R2, continuar con Vercel.

---

**Última actualización:** 2026-01-10  
**Estado:** GitHub ✅ | R2 ⏳ | Vercel ⏳
