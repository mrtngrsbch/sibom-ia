# Setup Rápido: Embeddings con OpenAI + Qdrant

## 📋 Prerequisitos

Ya tenés las API keys en tu `.env`. Solo necesitás instalar las dependencias.

## 🚀 Instalación

```bash
cd python-cli

# Instalar dependencias
pip install -r requirements.txt
```

Esto instalará:
- `openai` - Para generar embeddings
- `qdrant-client` - Para subir vectores a Qdrant
- `tqdm` - Para progress bar
- `python-dotenv` - Para cargar .env (ya instalado)

## ⚙️ Configuración

Tu archivo `.env` debe tener:

```bash
OPENAI_API_KEY=sk-proj-xxxxx
QDRANT_URL=https://xxxxx.qdrant.io
QDRANT_API_KEY=xxxxx
```

## ▶️ Ejecutar

```bash
python3 generate_embeddings.py
```

## 📊 Output Esperado

```
======================================================================
OpenAI Embeddings Generator for Qdrant
======================================================================

🔌 Initializing clients...
✅ Clients initialized

📥 Loading normativas index from boletines/normativas_index_minimal.json...
✅ Loaded 216,000 normativas

🗄️ Setting up Qdrant collection 'normativas'...
📦 Creating collection with 1536 dimensions...
✅ Collection created

🚀 Processing 216,000 normativas in batches of 100...
⏱️ Estimated time: ~108 minutes
💰 Estimated cost: ~$0.22

Generating embeddings: 100%|████████████| 216000/216000 [30:00<00:00, 120.00it/s]

✅ Processing complete!
   Successful: 216,000
   Failed: 0

🔍 Verifying collection...
✅ Collection info:
   Points: 216,000
   Vectors: 216,000
   Status: green

✅ Done! Vector search is now available.
```

## ⏱️ Tiempo y Costo

- **Tiempo:** 30-60 minutos (depende de tu conexión)
- **Costo:** ~$0.22 (216K docs × 500 tokens × $0.02/1M tokens)
- **Frecuencia:** ONE-TIME (solo cuando agregues nuevos documentos)

## ✅ Verificación

Después de ejecutar, verificá en Qdrant dashboard:
1. Ir a https://cloud.qdrant.io
2. Abrir tu cluster
3. Ver colección "normativas"
4. Debería tener 216,000 points

## 🔄 Actualizar Embeddings

Si agregás nuevos documentos:

```bash
# 1. Regenerar índice
python3 build_normativas_index.py

# 2. Regenerar embeddings
python3 generate_embeddings.py
```

El script te preguntará si querés borrar la colección existente.

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not set"
- Verificá que `.env` existe en `python-cli/`
- Verificá que la key empieza con `sk-proj-`

### Error: "QDRANT_URL not set"
- Verificá que creaste el cluster en Qdrant
- La URL debe ser `https://xxxxx.qdrant.io`

### Error: "normativas_index_minimal.json not found"
```bash
python3 build_normativas_index.py
```

### Error: "Rate limit exceeded"
- Esperá 1 minuto
- El script tiene rate limiting automático (0.5s entre batches)

### Proceso muy lento
- Normal: 30-60 minutos para 216K docs
- Cada batch de 100 docs tarda ~3-5 segundos
- Total: ~2160 batches × 3s = ~108 minutos

## 📝 Próximo Paso

Una vez completado, agregá las mismas variables al chatbot:

```bash
# chatbot/.env.local
OPENAI_API_KEY=sk-proj-xxxxx
QDRANT_URL=https://xxxxx.qdrant.io
QDRANT_API_KEY=xxxxx
```

Y listo! El chatbot usará vector search automáticamente.
