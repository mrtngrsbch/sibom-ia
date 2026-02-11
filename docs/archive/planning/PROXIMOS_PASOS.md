# 🚀 Próximos Pasos - Mangrullo Scraper Assistant

## ✅ Lo que acabamos de implementar

He implementado exitosamente la **Opción Híbrida (GitHub + Vercel con cache agresivo y soporte gzip)**. Esto te permite:

1. ✅ **Retriever híbrido** (`chatbot/src/lib/rag/retriever.ts`)
   - Soporta datos locales O GitHub Raw
   - Cache multi-nivel (1 hora índice, 30 min archivos)
   - Soporte para archivos comprimidos con gzip
   - Ahorro de 80% bandwidth con compresión

2. ✅ **Script de compresión** (`python-cli/comprimir_boletines.py`)
   - Comprime 533 MB → ~100 MB
   - Interfaz interactiva con progreso
   - Opción de mantener originales

3. ✅ **Configuración actualizada** (`.env.example`)
   - Variables para GitHub Raw
   - Documentación inline
   - Opciones de compresión

4. ✅ **Documentación completa**
   - Guía de deployment paso a paso
   - README para repo de datos
   - Análisis de costos y bandwidth

---

## 📋 Para Deployar a Producción

### Paso 1: Comprimir Datos (5 minutos)

```bash
cd python-cli
python comprimir_boletines.py
```

**Resultado**: Archivos `.json.gz` listos para GitHub

---

### Paso 2: Crear Repo de Datos en GitHub (10 minutos)

1. **Crear repositorio público**:
   ```
   Nombre: sibom-data
   Visibilidad: Public
   No inicializar con README
   ```

2. **Subir datos**:
   ```bash
   git clone https://github.com/TU-USUARIO/sibom-data.git
   cd sibom-data

   # Copiar archivos comprimidos
   cp ../sibom-scraper-assistant/python-cli/boletines/*.json.gz ./boletines/
   cp ../sibom-scraper-assistant/python-cli/boletines_index.json.gz ./

   # Usar el README que creé
   cp ../sibom-scraper-assistant/docs/SIBOM_DATA_REPO_README.md ./README.md

   # Commit y push
   git add .
   git commit -m "Initial commit: Add compressed bulletins data"
   git push origin main
   ```

3. **Verificar acceso**:
   ```
   https://raw.githubusercontent.com/TU-USUARIO/sibom-data/main/boletines_index.json.gz
   ```

   Debe descargarse el archivo.

---

### Paso 3: Configurar Variables Locales (2 minutos)

Edita `chatbot/.env.local`:

```bash
# API de OpenRouter
OPENROUTER_API_KEY=sk-or-v1-tu-clave-aquí

# Modelo económico (10x más barato que Claude)
ANTHROPIC_MODEL=google/gemini-3-flash-preview

# GitHub Data
GITHUB_DATA_REPO=TU-USUARIO/sibom-data
GITHUB_DATA_BRANCH=main
GITHUB_USE_GZIP=true

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

### Paso 4: Probar Localmente (5 minutos)

```bash
cd chatbot
npm install
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000) y prueba:

```
Pregunta: "ordenanza de presupuesto en Carlos Tejedor"
```

**Logs esperados**:
```
[RAG] 📥 Descargando índice desde GitHub: https://raw.githubusercontent.com/...
[RAG] ✅ Índice descargado: 3210 documentos (gzip)
[RAG] Query completada en 450ms
[RAG] Recuperados 5 documentos relevantes
[RAG] Cache: 5 archivos en memoria
```

Si ves esto, ¡funciona! 🎉

---

### Paso 5: Deploy a Vercel (10 minutos)

1. **Ir a [vercel.com](https://vercel.com)**

2. **New Project** → Importar `sibom-scraper-assistant`

3. **Configurar Build**:
   - Root Directory: `chatbot`
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

4. **Environment Variables** (copiar de `.env.local`):

   | Variable              | Value                           |
   | --------------------- | ------------------------------- |
   | `OPENROUTER_API_KEY`  | `sk-or-v1-...`                  |
   | `ANTHROPIC_MODEL`     | `google/gemini-3-flash-preview` |
   | `GITHUB_DATA_REPO`    | `TU-USUARIO/sibom-data`         |
   | `GITHUB_DATA_BRANCH`  | `main`                          |
   | `GITHUB_USE_GZIP`     | `true`                          |
   | `NEXT_PUBLIC_APP_URL` | (Vercel te lo dará)             |
   | `NODE_ENV`            | `production`                    |

5. **Deploy**

6. **Actualizar `NEXT_PUBLIC_APP_URL`**:
   - Vercel te da una URL: `https://sibom-chatbot-abc123.vercel.app`
   - Actualiza la variable en Vercel Settings → Environment Variables
   - Redeploy (opcional)

---

## 📊 Monitoreo y Optimización

### Verificar Funcionamiento

1. **Abrir app en Vercel**: `https://tu-app.vercel.app`
2. **Hacer consulta de prueba**
3. **Ver logs** en Vercel → Functions → Logs

### Monitorear Bandwidth

**GitHub**:
- Settings → Insights → Traffic
- Límite: 100 GB/mes (gratis)

**Vercel**:
- Dashboard → Analytics → Bandwidth
- Límite: 100 GB/mes (gratis)

### Costos Estimados

**Con Gemini 3 Flash** (100 consultas/día):
- Bandwidth GitHub: ~300 MB/mes (con gzip)
- Bandwidth Vercel: ~300 MB/mes
- LLM: ~$0.15/mes

**Total: ~$0.15/mes** (prácticamente gratis)

---

## 🔧 Optimizaciones Futuras

### 1. Pre-warming de Cache (Opcional)

Crea `/chatbot/vercel.json`:

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

Si llegas a rate limits:
1. Genera token: https://github.com/settings/tokens
2. Permisos: `public_repo` (read)
3. Agrega a Vercel: `GITHUB_TOKEN=ghp_xxx...`

### 3. Cambiar a Modelo Gratuito

Si quieres 100% gratis:

```bash
ANTHROPIC_MODEL=zhipu/glm-4.5-air:free
```

(Con límites, pero suficiente para MVP)

---

## 📚 Documentación Completa

He creado estos archivos para ti:

1. **`docs/DEPLOYMENT_GITHUB_VERCEL.md`**
   - Guía completa de deployment
   - Troubleshooting
   - Optimizaciones avanzadas

2. **`docs/SIBOM_DATA_REPO_README.md`**
   - README para tu repo `sibom-data`
   - Descripción de estructura
   - Guía de uso

3. **`python-cli/comprimir_boletines.py`**
   - Script de compresión con interfaz
   - Estadísticas de ahorro

4. **`chatbot/.env.example`**
   - Todas las variables documentadas
   - Ejemplos de configuración

---

## ❓ Preguntas Respondidas

### 1. ¿Por qué tengo configs de Anthropic si solo uso OpenRouter?

**Respuesta**: Por compatibilidad histórica del SDK. El código usa `ANTHROPIC_BASE_URL=https://openrouter.ai/api/v1` para redirigir todo a OpenRouter.

**Dónde cambiar modelo**: Variable `ANTHROPIC_MODEL` en `.env.local`

### 2. ¿Qué tecnologías usa el RAG?

**Respuesta**: RAG sin embeddings (keyword-based):
- Índice JSON de metadatos (790 KB)
- Búsqueda por scoring heurístico
- Cache en memoria (1 hora índice, 30 min archivos)
- Lazy loading (solo lee 5 de 3,210 archivos)

### 3. ¿Variables de entorno para Vercel?

**Respuesta**:
```bash
OPENROUTER_API_KEY      # Requerida
ANTHROPIC_MODEL         # Opcional (default: claude-3.5-sonnet)
GITHUB_DATA_REPO        # Requerida para GitHub Raw
GITHUB_DATA_BRANCH      # Opcional (default: main)
GITHUB_USE_GZIP         # Opcional (default: false)
NEXT_PUBLIC_APP_URL     # URL de Vercel
```

### 4. ¿Dónde está la lógica del comportamiento del chat?

**Respuesta**:
- **System Prompt**: `/chatbot/src/prompts/system.md`
- **Parámetros LLM**: `/chatbot/src/app/api/chat/route.ts` (temperature: 0.3, maxTokens: 2000)
- **Recuperación RAG**: `/chatbot/src/lib/rag/retriever.ts` (limit: 5 docs)

---

## 🎯 Próximos Pasos Inmediatos

**Para deployar HOY**:

1. ⬜ Comprimir datos: `python comprimir_boletines.py`
2. ⬜ Crear repo GitHub `sibom-data` (público)
3. ⬜ Subir archivos .gz a GitHub
4. ⬜ Configurar `.env.local` con tu usuario GitHub
5. ⬜ Probar local: `npm run dev`
6. ⬜ Deploy a Vercel
7. ⬜ Configurar variables en Vercel
8. ⬜ Verificar funcionamiento

**Tiempo estimado**: ~30-45 minutos

---

## 🆘 Si Necesitas Ayuda

1. **Revisa** `docs/DEPLOYMENT_GITHUB_VERCEL.md` (troubleshooting completo)
2. **Verifica logs** en Vercel → Functions → Logs
3. **Prueba acceso** a GitHub Raw manualmente
4. **Verifica variables** en Vercel Settings

---

## ✨ Resultado Final

Tendrás un chatbot:
- ✅ Desplegado en Vercel (gratis)
- ✅ Datos en GitHub (gratis)
- ✅ LLM económico ($0.15/mes con Gemini)
- ✅ Cache optimizado (respuestas rápidas)
- ✅ 80% ahorro bandwidth (gzip)
- ✅ Escalable hasta 100 GB/mes

**Costo total mensual**: ~$0.15 USD

---

¡Éxito con el deployment! 🚀
