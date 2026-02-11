#!/bin/bash
# setup_vercel_env.sh
# Configura variables de entorno en Vercel vía CLI

set -e

echo "🔧 Configurador de Variables de Entorno para Vercel"
echo ""

# Verificar que vercel CLI esté instalado
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI no está instalado"
    echo "Instala con: npm install -g vercel"
    exit 1
fi

# Variables requeridas
echo "📝 Ingresa los valores (presiona Enter para valor por defecto):"
echo ""

read -p "OPENROUTER_API_KEY (requerido): " OPENROUTER_KEY
if [ -z "$OPENROUTER_KEY" ]; then
    echo "❌ Error: OPENROUTER_API_KEY es requerido"
    exit 1
fi

read -p "R2 Public URL (ej: pub-abc123.r2.dev/sibom-data): " R2_URL
if [ -z "$R2_URL" ]; then
    echo "❌ Error: R2 URL es requerida"
    exit 1
fi

read -p "LLM_MODEL_PRIMARY [anthropic/claude-3.5-sonnet]: " MODEL_PRIMARY
MODEL_PRIMARY=${MODEL_PRIMARY:-anthropic/claude-3.5-sonnet}

read -p "LLM_MODEL_ECONOMIC [google/gemini-flash-1.5]: " MODEL_ECONOMIC
MODEL_ECONOMIC=${MODEL_ECONOMIC:-google/gemini-flash-1.5}

echo ""
echo "⚙️ Configurando variables en Vercel..."
echo ""

# Configurar variables (production, preview, development)
vercel env add OPENROUTER_API_KEY production <<< "$OPENROUTER_KEY"
vercel env add OPENROUTER_API_KEY preview <<< "$OPENROUTER_KEY"
vercel env add OPENROUTER_API_KEY development <<< "$OPENROUTER_KEY"

vercel env add LLM_MODEL_PRIMARY production <<< "$MODEL_PRIMARY"
vercel env add LLM_MODEL_PRIMARY preview <<< "$MODEL_PRIMARY"
vercel env add LLM_MODEL_PRIMARY development <<< "$MODEL_PRIMARY"

vercel env add LLM_MODEL_ECONOMIC production <<< "$MODEL_ECONOMIC"
vercel env add LLM_MODEL_ECONOMIC preview <<< "$MODEL_ECONOMIC"
vercel env add LLM_MODEL_ECONOMIC development <<< "$MODEL_ECONOMIC"

vercel env add GITHUB_DATA_REPO production <<< "$R2_URL"
vercel env add GITHUB_DATA_REPO preview <<< "$R2_URL"

vercel env add GITHUB_DATA_BRANCH production <<< ""
vercel env add GITHUB_DATA_BRANCH preview <<< ""

vercel env add GITHUB_USE_GZIP production <<< "true"
vercel env add GITHUB_USE_GZIP preview <<< "true"
vercel env add GITHUB_USE_GZIP development <<< "true"

vercel env add USE_NORMATIVAS_INDEX production <<< "true"
vercel env add USE_NORMATIVAS_INDEX preview <<< "true"
vercel env add USE_NORMATIVAS_INDEX development <<< "true"

vercel env add INDEX_CACHE_DURATION production <<< "3600000"
vercel env add INDEX_CACHE_DURATION preview <<< "3600000"
vercel env add INDEX_CACHE_DURATION development <<< "3600000"

echo ""
echo "============================================"
echo "✅ CONFIGURACIÓN COMPLETADA"
echo "============================================"
echo ""
echo "Variables configuradas:"
echo "  ✓ OPENROUTER_API_KEY"
echo "  ✓ LLM_MODEL_PRIMARY = $MODEL_PRIMARY"
echo "  ✓ LLM_MODEL_ECONOMIC = $MODEL_ECONOMIC"
echo "  ✓ GITHUB_DATA_REPO = $R2_URL"
echo "  ✓ GITHUB_USE_GZIP = true"
echo "  ✓ USE_NORMATIVAS_INDEX = true"
echo ""
echo "Próximo paso: vercel --prod"
