#!/bin/bash

# Script de instalación rápida para SIBOM Scraper CLI

echo "🚀 Instalando SIBOM Scraper CLI..."
echo ""

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "Por favor instala Python 3.8 o superior"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python detectado: $PYTHON_VERSION"

# Crear entorno virtual
echo ""
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

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
chmod +x sibom_scraper.py

echo ""
echo "✅ Instalación completada!"
echo ""
echo "📖 Próximos pasos:"
echo "   1. Edita .env y agrega tu OPENROUTER_API_KEY (si no lo hiciste)"
echo "   2. Activa el entorno virtual: source venv/bin/activate"
echo "   3. Ejecuta: python sibom_scraper.py --limit 5"
echo ""
echo "💡 Ver ayuda: python sibom_scraper.py --help"
