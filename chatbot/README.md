# Chatbot Legal Municipal

Chatbot especializado en responder consultas sobre legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires, Argentina.

## 🚀 Características

- **Búsqueda inteligente**: Consulta normativa municipal usando IA
- **Fuentes oficiales**: Citas directas a documentos SIBOM
- **Respuestas claras**: Lenguaje accesible para ciudadanos
- **Chat en tiempo real**: Streaming de respuestas

## 📋 Requisitos

- **Node.js 18+** (requerido)
- **pnpm** (recomendado) - [Instalar pnpm](https://pnpm.io/installation)
- API Key de OpenRouter (para el modelo LLM)

> **Nota:** Este proyecto usa pnpm como gestor de paquetes para mayor eficiencia y ahorro de espacio en disco.

## 🛠️ Instalación

### 1. Clonar e instalar dependencias

```bash
cd chatbot
pnpm install
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

```bash
pnpm run dev
```

> Si usas npm o yarn:
> ```bash
> npm run dev   # o: yarn dev
> ```

Abre [http://localhost:3000](http://localhost:3000)

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
│   │   └── page.tsx               # Página principal
│   ├── components/
│   │   ├── chat/
│   │   │   └── ChatContainer.tsx  # Componente del chat
│   │   └── layout/
│   │       ├── Header.tsx         # Header de la app
│   │       └── Sidebar.tsx        # Panel lateral
│   └── lib/
│       └── rag/
│           └── retriever.ts       # Motor RAG
├── chatbot/                       # Carpeta con boletines (símbolo)
├── package.json
├── next.config.js
├── tailwind.config.ts
└── tsconfig.json
```

## 🔧 Configuración

### Modelos LLM

El chatbot usa OpenRouter con **AI SDK v5**. Modelos recomendados:

| Modelo | Costo | Calidad |
|--------|-------|---------|
| `google/gemini-2.5-flash-lite-preview-09-2025` | Medio | Excelente |
| `zai/glm-4.7` | Bajo | Muy buena |
| `anthropic/claude-3.5-sonnet` | Medio | Excelente |

> **Nota:** AI SDK v5 soporta la especificación v2, lo que permite usar modelos de Google Gemini, Z.AI GLM, OpenAI y Anthropic.

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

## 🧪 Desarrollo

```bash
# Modo desarrollo
pnpm run dev

# Build para producción
pnpm run build

# Ver producción localmente
pnpm run start

# Linting
pnpm run lint

# Tests
pnpm run test
```

> Si usas npm o yarn, reemplaza `pnpm` con `npm` o `yarn`.

## 🚀 Deployment

### Vercel (Recomendado)

El proyecto está configurado para deployment en Vercel. El deployment se hace automáticamente en cada push a `main`.

1. Conecta tu repositorio a Vercel
2. Configura las variables de entorno
3. Deploy automático en cada push a `main`

### Self-hosted

Para hacer self-hosting en producción:

```bash
pnpm run build
pnpm run start
```

## 📄 Licencia

MIT License

---

**Nota**: Este proyecto forma parte del ecosistema SIBOM Scraper Assistant.
