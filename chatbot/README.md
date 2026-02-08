> ⚠️ NOTA (2026-02-07): Este doc puede tener refs desactualizadas. Stack actual: Gemini 3 Flash + GLM 4.7, Qdrant. Ver `.agents/README.md`

# Chatbot Legal Municipal

Chatbot especializado en responder consultas sobre legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires, Argentina. Incluye módulo de análisis satelital para monitoreo de humedales.

## 🚀 Características

### Chatbot Legal
- **Búsqueda inteligente**: Consulta normativa municipal usando IA
- **Fuentes oficiales**: Citas directas a documentos SIBOM
- **Respuestas claras**: Lenguaje accesible para ciudadanos
- **Chat en tiempo real**: Streaming de respuestas

### Análisis Satelital
- **Imágenes Sentinel-2**: Datos satelitales de alta resolución (10m)
- **Índices espectrales**: NDWI, MNDWI, NDVI, NDMI, NDSI, SWIR2+NIR
- **Clasificación de suelo**: Agua, Humedal, Vegetación, Otros
- **Galería visual**: Imágenes RGB, clasificación e índices espectrales
- **Descarga de imágenes**: Individual o en ZIP
- **Evolución temporal**: Gráficos y tablas de cambios históricos

## 📋 Requisitos

- **Bun 1.0+** (recomendado para desarrollo) - [Instalar Bun](https://bun.sh/install)
- Node.js 18+ (para producción/Vercel)
- API Key de OpenRouter (para el modelo LLM)

> **Nota:** Este proyecto usa Bun como runtime de desarrollo para mayor velocidad. El deployment a Vercel usa Node.js sin cambios necesarios.

## 🛠️ Instalación

### 1. Clonar e instalar dependencias

```bash
cd chatbot
bun install
```

> Si usas npm o yarn:
> ```bash
> npm install   # o: yarn install
> ```

### 2. Configurar variables de entorno

```bash
cp .env.example .env.local
```

Edita `.env.local` y agrega tu API key:

```env
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aqui
OPENROUTER_MODEL=google/gemini-3-flash-preview
```

Obtén tu API key en: [https://openrouter.ai/keys](https://openrouter.ai/keys)

### 3. Ejecutar en desarrollo

**Opción A: Desarrollo local con script (recomendado)**

El script `scripts/dev.sh` inicia tanto el backend sat-analysis como el frontend:

```bash
./scripts/dev.sh
```

Esto inicia:
- Backend FastAPI en `http://localhost:8001`
- Frontend Next.js en `http://localhost:3000`

**Opción B: Solo frontend (con backend Docker)**

```bash
bun run dev
```

Abre [http://localhost:3000](http://localhost:3000)

> **Nota:** Para usar el módulo satelital, el backend `sat-analysis` debe estar ejecutándose.

## 📁 Estructura del Proyecto

```
chatbot/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat/route.ts      # Endpoint del chat
│   │   │   └── stats/route.ts     # Endpoint de estadísticas
│   │   ├── globals.css            # Estilos globales
│   │   ├── layout.tsx             # Layout principal
│   │   ├── page.tsx               # Página principal (chatbot)
│   │   └── satelite/
│   │       └── page.tsx           # Página de análisis satelital
│   ├── components/
│   │   ├── chat/
│   │   │   └── ChatContainer.tsx  # Componente del chat
│   │   ├── satelite/              # Componentes de análisis satelital
│   │   │   ├── PartidaForm.tsx    # Formulario de partida
│   │   │   ├── ResultsPanel.tsx   # Panel de resultados (tabs)
│   │   │   ├── ImagesPanel.tsx    # Galería de imágenes
│   │   │   ├── ImageCard.tsx      # Card de imagen individual
│   │   │   ├── ImageModal.tsx     # Modal de zoom
│   │   │   └── ImageThumbnail.tsx # Miniatura para tabla
│   │   └── layout/
│   │       ├── Header.tsx         # Header de la app
│   │       └── Sidebar.tsx        # Panel lateral
│   └── lib/
│       ├── rag/
│       │   └── retriever.ts       # Motor RAG
│       ├── sat-api.ts             # Cliente API satelital
│       └── types.ts               # Tipos TypeScript
├── chatbot/                       # Carpeta con boletines (símbolo)
├── package.json
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## 🔧 Configuración

### Modelos LLM

El chatbot usa OpenRouter. Modelos recomendados:

| Modelo | Costo | Calidad |
|--------|-------|---------|
| `google/gemini-3-flash-preview` | Bajo | Muy buena |
| `google/gemini-2.5-flash-lite` | Muy bajo | Buena |
| `z-ai/glm-4.5-air:free` | Gratis | Buena |

### Base de Datos

Los documentos se leen desde la carpeta `../python-cli/boletines/`. Asegúrate de:
1. Ejecutar el scraper para obtener boletines
2. Los archivos JSON deben tener estructura compatible

## 📝 API

### POST /api/chat

Envía un mensaje al chatbot.

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      { "role": "user", "content": "¿Cómo consulto una ordenanza?" }
    ]
  }'
```

### GET /api/stats

Obtiene estadísticas de la base de datos.

```bash
curl http://localhost:3000/api/stats
```

## 🛰️ Endpoints Satelitales

El módulo de análisis satelital se comunica con el backend `sat-analysis` (FastAPI) en el puerto 8001.

### POST /api/analyze

Inicia un análisis de una partida catastral.

```bash
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "partida": "4606",
    "days_back": 365,
    "cloud_cover_max": 30
  }'
```

**Respuesta:**
```json
{
  "task_id": "d3b99a91-7ba7-4acf-bf14-832f196463eb",
  "status": "processing"
}
```

### GET /api/analyze/{task_id}

Consulta el estado de un análisis.

```bash
curl http://localhost:8001/api/analyze/d3b99a91-7ba7-4acf-bf14-832f196463eb
```

**Respuesta (completado):**
```json
{
  "task_id": "d3b99a91-7ba7-4acf-bf14-832f196463eb",
  "status": "completed",
  "partida": "4606",
  "results": [
    {
      "date": "2025-01-07",
      "water_ha": 12.5,
      "wetland_ha": 45.2,
      "vegetation_ha": 120.8,
      "other_ha": 85.3,
      "cloud_cover": 5,
      "images": {
        "rgb": "/images/rgb_4606_20250107.png",
        "clasificacion": "/images/clasificacion_4606_20250107.png",
        "ndwi": "/images/ndwi_4606_20250107.png",
        "ndvi": "/images/ndvi_4606_20250107.png",
        "ndmi": "/images/ndmi_4606_20250107.png",
        "mndwi": "/images/mndwi_4606_20250107.png",
        "ndsi": "/images/ndsi_4606_20250107.png",
        "swir2_nir": "/images/swir2-nir_4606_20250107.png"
      }
    }
  ]
}
```

### GET /api/analyze/{task_id}/zip

Descarga todas las imágenes del análisis en un ZIP.

```bash
curl http://localhost:8001/api/analyze/d3b99a91-7ba7-4acf-bf14-832f196463eb/zip \
  -o analisis_satelital.zip
```

### GET /images/{filename}

Accede a una imagen individual generada por el análisis.

```bash
curl http://localhost:8001/images/rgb_4606_20250107.png -o imagen.png
```

## 🧪 Desarrollo

### Desarrollo Local

**Opción A: Script de desarrollo completo**

El script `scripts/dev.sh` maneja tanto el backend como el frontend:

```bash
./scripts/dev.sh
```

**Opción B: Iniciar servicios manualmente**

```bash
# Terminal 1 - Backend sat-analysis
cd sat-analysis
source venv/bin/activate
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2 - Frontend chatbot
cd chatbot
bun run dev
```

### Comandos de Build

```bash
# Modo desarrollo (usa Bun runtime - muy rápido)
bun run dev

# Build para producción
bun run build

# Ver producción localmente
bun run start

# Linting
bun run lint

# Tests
bun run test
```

> Si usas npm o yarn, reemplaza `bun` con `npm` o `yarn`.

## 🚀 Deployment

### Vercel (Recomendado)

El proyecto está configurado para deployment en Vercel. El deployment usa Node.js runtime automáticamente - sin cambios necesarios.

1. Conecta tu repositorio a Vercel
2. Configura las variables de entorno
3. Deploy automático en cada push a `main`

### Self-hosted con Bun

Para usar Bun en producción:

```bash
bun run build
bun run start
```

## 📄 Licencia

MIT License

---

**Nota**: Este proyecto forma parte del ecosistema SIBOM Scraper Assistant.
