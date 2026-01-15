# 🔄 Entornos: Desarrollo vs Producción

**Fecha:** 2026-01-10  
**Proyecto:** SIBOM Chatbot

---

## 📊 Comparación de Entornos

| Aspecto | Desarrollo (Local) | Producción (Vercel) |
|---------|-------------------|---------------------|
| **Frontend** | `localhost:3000` | `sibom-ia.vercel.app` |
| **Datos** | `python-cli/boletines/*.json` (local) | Cloudflare R2 (CDN) |
| **LLM** | OpenRouter API | OpenRouter API |
| **Build** | `pnpm run dev` (hot reload) | `pnpm run build` (optimizado) |
| **Variables** | `.env.local` | Vercel Dashboard |
| **Cache** | 5 minutos (detección de cambios) | 1 hora (estable) |

---

## 🏠 Entorno de Desarrollo (Local)

### Configuración

**Archivo:** `chatbot/.env.local`

```bash
# API Keys
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Modelos LLM
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5

# Datos LOCALES (sin GITHUB_DATA_REPO)
# Si GITHUB_DATA_REPO está vacío o no existe, usa datos locales
# GITHUB_DATA_REPO=

# Configuración de índice
USE_NORMATIVAS_INDEX=true
INDEX_CACHE_DURATION=300000  # 5 minutos para detectar cambios rápido
```

### Cómo Funciona

**Detección automática en `chatbot/src/lib/rag/retriever.ts`:**

```typescript
/**
 * Determina si debe usar GitHub Raw o archivos locales
 */
function useGitHub(): boolean {
  const githubRepo = process.env.GITHUB_DATA_REPO;
  return !!(githubRepo && githubRepo.trim().length > 0);
}

/**
 * Obtiene la ruta base de datos según el entorno
 */
function getDataBasePath(): string {
  if (useGitHub()) {
    // Producción: Cloudflare R2
    return getGitHubRawBase();
  }
  
  // Desarrollo: Archivos locales
  return path.join(process.cwd(), '..', 'python-cli');
}
```

**Flujo en Desarrollo:**

1. Usuario hace query: "decretos de Carlos Tejedor"
2. Sistema detecta: `GITHUB_DATA_REPO` vacío → **modo local**
3. Lee índice: `python-cli/boletines_index.json`
4. Busca documentos con BM25
5. Carga contenido: `python-cli/boletines/carlos_tejedor_boletin_123.json`
6. Retorna resultados al LLM

### Comandos de Desarrollo

```bash
# 1. Instalar dependencias
cd chatbot
pnpm install

# 2. Configurar .env.local
cp .env.example .env.local
# Editar .env.local con tu OPENROUTER_API_KEY

# 3. Iniciar servidor de desarrollo
pnpm run dev

# 4. Abrir navegador
open http://localhost:3000
```

### Ventajas del Modo Local

- ✅ **Cambios instantáneos:** Editas JSON y se refleja en 5 minutos (cache)
- ✅ **Sin costos de bandwidth:** No consume Cloudflare R2
- ✅ **Debugging fácil:** Puedes ver los archivos directamente
- ✅ **Scrapear y probar:** Scrapeas nuevos municipios y los pruebas al instante

---

## 🌐 Entorno de Producción (Vercel)

### Configuración

**Ubicación:** Vercel Dashboard → Settings → Environment Variables

```bash
# API Keys
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Modelos LLM
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5

# Datos en CLOUDFLARE R2 (IMPORTANTE)
GITHUB_DATA_REPO=pub-xxxxx.r2.dev/sibom-data
GITHUB_DATA_BRANCH=  # Vacío (no aplica para R2)

# Configuración de índice
GITHUB_USE_GZIP=true
USE_NORMATIVAS_INDEX=true
INDEX_CACHE_DURATION=3600000  # 1 hora (estable)
```

### Cómo Funciona

**Flujo en Producción:**

1. Usuario hace query: "decretos de Carlos Tejedor"
2. Sistema detecta: `GITHUB_DATA_REPO` = `pub-xxxxx.r2.dev/sibom-data` → **modo GitHub/R2**
3. Descarga índice (con cache): `https://pub-xxxxx.r2.dev/sibom-data/normativas_index_minimal.json.gz`
4. Busca documentos con BM25
5. Descarga contenido (con cache): `https://pub-xxxxx.r2.dev/sibom-data/boletines/carlos_tejedor_boletin_123.json.gz`
6. Retorna resultados al LLM

**Optimizaciones en Producción:**

- **Gzip:** Archivos comprimidos (80% menos bandwidth)
- **CDN Global:** Cloudflare R2 sirve desde edge locations
- **Cache Agresivo:** 1 hora de cache (menos requests)
- **Next.js Cache:** `force-cache` + `revalidate: 3600`

### Ventajas del Modo Producción

- ✅ **Escalable:** Soporta millones de requests
- ✅ **Rápido:** CDN global con edge caching
- ✅ **Económico:** R2 es más barato que S3
- ✅ **Confiable:** 99.9% uptime garantizado

---

## 🧪 Cómo Probar Producción

### Opción 1: Probar Localmente con Datos de R2

Puedes probar el modo producción localmente configurando R2 en `.env.local`:

```bash
# chatbot/.env.local
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5

# Apuntar a R2 (igual que producción)
GITHUB_DATA_REPO=pub-xxxxx.r2.dev/sibom-data
GITHUB_USE_GZIP=true
USE_NORMATIVAS_INDEX=true
INDEX_CACHE_DURATION=3600000
```

Luego:

```bash
cd chatbot
pnpm run dev
# Ahora usa datos de R2, no locales
```

**Verificar en logs:**
```
[RAG] ✅ Índice de normativas cargado: 216,506 normativas (fuente: GitHub)
```

Si dice "fuente: GitHub" → está usando R2 ✅

---

### Opción 2: Probar en Vercel Preview

Vercel crea URLs preview automáticas para cada branch:

```bash
# 1. Crear branch de testing
git checkout -b test-production

# 2. Hacer un cambio mínimo
echo "# Test" >> README.md
git add README.md
git commit -m "test: Probar deployment preview"

# 3. Push
git push origin test-production
```

Vercel creará automáticamente:
- URL preview: `https://sibom-ia-git-test-production-tu-usuario.vercel.app`
- Usa las mismas variables de entorno que producción
- Puedes probar sin afectar producción

---

### Opción 3: Probar Producción Real

Una vez deployado en Vercel:

**URL:** `https://sibom-ia.vercel.app`

**Tests básicos:**

#### 1. Test de Conectividad con R2

```bash
# Verificar que el índice es accesible
curl -I "https://pub-xxxxx.r2.dev/sibom-data/normativas_index_minimal.json.gz"

# Debe retornar:
HTTP/2 200
content-type: application/gzip
content-length: 5604999
```

#### 2. Test de Query Simple

1. Abrir: `https://sibom-ia.vercel.app`
2. Escribir: "decretos de Carlos Tejedor"
3. **Verificar:**
   - ✅ Retorna resultados (no "not found")
   - ✅ Enlaces "Ver en SIBOM" funcionan
   - ✅ Respuesta en <5 segundos

#### 3. Test de Query Específica

1. Escribir: "ordenanza 2833"
2. **Verificar:**
   - ✅ Encuentra la ordenanza específica
   - ✅ Muestra contenido relevante
   - ✅ URL correcta del boletín

#### 4. Test de Estadísticas

1. Escribir: "cuántos decretos hay"
2. **Verificar:**
   - ✅ Retorna número total
   - ✅ Puede filtrar por municipio

#### 5. Verificar Logs en Vercel

Vercel Dashboard → Deployments → Latest → **Function Logs**

**Buscar estas líneas:**

```
[RAG] ✅ Índice de normativas cargado: 216,506 normativas (fuente: GitHub)
[RAG] 🔍 INICIO - Índice de normativas: 216506 registros
[RAG] ✅ Query completada en 1234ms
```

**Si ves errores:**

```
[RAG] ❌ Error descargando índice de GitHub: 404
```
→ Verificar `GITHUB_DATA_REPO` en Vercel

```
[RAG] ⚠️ Usando cache antiguo como fallback
```
→ R2 no accesible, verificar acceso público

---

## 🔍 Debugging de Entornos

### Verificar Qué Entorno Está Usando

**En desarrollo (localhost:3000):**

Abrir DevTools → Console → Buscar:

```
[RAG] Modo: local
[RAG] Ruta base: /Users/tu-usuario/sibom-scraper-assistant/python-cli
```

**En producción (Vercel):**

Vercel Dashboard → Function Logs → Buscar:

```
[RAG] Modo: GitHub
[RAG] URL base: https://pub-xxxxx.r2.dev/sibom-data
```

### Problemas Comunes

#### Problema: "No se encuentran documentos"

**Causa:** Índice vacío o no cargado

**Solución:**

1. Verificar logs: ¿Cuántos documentos cargó?
2. Si es 0 → Verificar `GITHUB_DATA_REPO` o archivos locales
3. Si es >0 pero no encuentra → Problema con BM25 o filtros

#### Problema: "404 Not Found" en R2

**Causa:** Archivos no subidos o URL incorrecta

**Solución:**

```bash
# Verificar URL de R2
curl -I "https://pub-xxxxx.r2.dev/sibom-data/normativas_index_minimal.json.gz"

# Si falla, verificar:
# 1. Bucket tiene acceso público
# 2. Archivos están subidos
# 3. URL es correcta en GITHUB_DATA_REPO
```

#### Problema: "Respuestas muy lentas"

**Causa:** Cache deshabilitado o límite muy bajo

**Solución:**

```bash
# Aumentar cache duration
INDEX_CACHE_DURATION=3600000  # 1 hora

# Verificar que gzip está habilitado
GITHUB_USE_GZIP=true
```

---

## 📋 Checklist de Verificación

### Desarrollo Local

- [ ] `.env.local` configurado con `OPENROUTER_API_KEY`
- [ ] `GITHUB_DATA_REPO` vacío o comentado
- [ ] Archivos en `python-cli/boletines/*.json` existen
- [ ] `pnpm run dev` inicia sin errores
- [ ] Queries retornan resultados
- [ ] Logs muestran "fuente: local"

### Producción Vercel

- [ ] 8 variables de entorno configuradas en Vercel
- [ ] `GITHUB_DATA_REPO` apunta a R2: `pub-xxxxx.r2.dev/sibom-data`
- [ ] Archivos subidos a R2 (índice + boletines)
- [ ] R2 bucket tiene acceso público
- [ ] Build exitoso en Vercel
- [ ] Queries retornan resultados
- [ ] Logs muestran "fuente: GitHub"
- [ ] URLs de "Ver en SIBOM" funcionan

---

## 🎯 Resumen Ejecutivo

**Desarrollo:**
- Usa archivos locales en `python-cli/`
- Rápido para iterar y probar
- No requiere R2

**Producción:**
- Usa Cloudflare R2 (CDN global)
- Optimizado con gzip y cache
- Escalable y económico

**Cómo Probar:**
1. Local con R2: Configurar `GITHUB_DATA_REPO` en `.env.local`
2. Preview: Push a branch → Vercel crea URL preview
3. Producción: Probar en `sibom-ia.vercel.app` + verificar logs

**Indicador clave:** Buscar en logs:
- `fuente: local` → Desarrollo
- `fuente: GitHub` → Producción (R2)

---

**Última actualización:** 2026-01-10  
**Versión:** 1.0.0
