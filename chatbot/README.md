# Chatbot Legal Municipal

Chatbot especializado en responder consultas sobre legislación, ordenanzas y decretos de municipios de la Provincia de Buenos Aires, Argentina.

## 🚀 Características

- **Búsqueda inteligente**: Consulta normativa municipal usando IA
- **Fuentes oficiales**: Citas directas a documentos SIBOM
- **Respuestas claras**: Lenguaje accesible para ciudadanos
- **Chat en tiempo real**: Streaming de respuestas

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

```bash
bun run dev
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

## 🧪 Desarrollo

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
