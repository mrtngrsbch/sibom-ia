#!/bin/bash

# Script de instalación rápida para SIBOM Scraper CLI con uv

echo "🚀 Instalando SIBOM Scraper CLI..."
echo ""

# Verificar que uv esté instalado
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv no está instalado"
    echo "Instala uv primero:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ uv detectado: $(uv --version)"

# Crear entorno virtual con uv
echo ""
echo "📦 Creando entorno virtual..."
uv venv .venv

# Instalar dependencias
echo "📚 Instalando dependencias..."
uv pip install -r requirements.txt

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "Para activar el entorno:"
echo "  source .venv/bin/activate  # macOS/Linux"
echo "  .venv\\Scripts\\activate     # Windows"

# Verificar .env
echo ""
if [ ! -f .env ]; then
    echo "⚠️  No se encontró archivo .env"
    echo "📝 Creando .env desde .env.example..."
    cp .env.example .env
    echo ""
    echo "⚙️  IMPORTANTE: Edita el archivo .env y agrega tu OPENROUTER_API_KEY"
    echo "    Obtén tu API key en: https://openrouter.ai/keys"
else
    echo "✓ Archivo .env encontrado"
fi

# Hacer ejecutable el script
chmod +x cli.py

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "📖 Próximos pasos:"
echo "   1. Edita .env y agrega tu OPENROUTER_API_KEY (si no lo hiciste)"
echo "   2. Activa el entorno virtual: source .venv/bin/activate"
echo "   3. Ejecuta: python cli.py sibom --limit 5"
echo ""
echo "💡 Ver ayuda: python cli.py --help"
