#!/bin/bash
# Script de inicio rápido para refactoring con GLM-4.7

echo "🚀 INICIANDO REFACTORING CON GLM-4.7"
echo "===================================================================="

# Verificar si .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  No se encontró archivo .env"
    echo "Creando .env desde .env.example..."
    cp .env.example .env
    echo "✅ Archivo .env creado"
    echo ""
    echo "IMPORTANTE: Edita .env con tu API key:"
    echo "  nano .env"
    echo ""
    echo "Luego ejecuta este script de nuevo."
    exit 1
fi

# Verificar si tiene API key configurada
if grep -q "reemplazar-con-tu-api-key" .env; then
    echo "❌ ERROR: Necesitas agregar tu API key a .env"
    echo ""
    echo "1. Ve a https://openrouter.ai/keys"
    echo "2. Copia tu clave"
    echo "3. Edita .env y reemplaza 'reemplazar-con-tu-api-key'"
    echo ""
    echo "Comando: nano .env"
    exit 1
fi

echo "✅ API key detectada"
echo "📄 Enviando prompt a GLM-4.7..."
echo ""

# Ejecutar el script Python
python EXECUTE_REFACTOR.py
