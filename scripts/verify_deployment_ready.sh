#!/bin/bash
# verify_deployment_ready.sh
# Verifica que todo esté listo para deployment

set -e

echo "🔍 VERIFICACIÓN PRE-DEPLOYMENT"
echo "================================"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contadores
checks_passed=0
checks_failed=0
warnings=0

# Función para check exitoso
check_ok() {
    echo -e "${GREEN}✅ $1${NC}"
    checks_passed=$((checks_passed + 1))
}

# Función para check fallido
check_fail() {
    echo -e "${RED}❌ $1${NC}"
    checks_failed=$((checks_failed + 1))
}

# Función para warning
check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    warnings=$((warnings + 1))
}

echo "📋 VERIFICANDO CÓDIGO"
echo "--------------------"

# 1. Verificar que estamos en la rama main
current_branch=$(git branch --show-current)
if [ "$current_branch" = "main" ]; then
    check_ok "Rama actual: main"
else
    check_warn "Rama actual: $current_branch (se recomienda main)"
fi

# 2. Verificar que no hay cambios sin commitear
if git diff-index --quiet HEAD --; then
    check_ok "No hay cambios sin commitear"
else
    check_fail "Hay cambios sin commitear"
    echo "   Ejecuta: git add . && git commit -m 'mensaje'"
fi

# 3. Verificar que está sincronizado con origin
if git diff origin/main..HEAD --quiet 2>/dev/null; then
    check_ok "Sincronizado con origin/main"
else
    check_warn "Hay commits locales sin pushear"
    echo "   Ejecuta: git push origin main"
fi

echo ""
echo "📦 VERIFICANDO DATOS"
echo "--------------------"

# 4. Verificar que existe dist/
if [ -d "python-cli/dist" ]; then
    check_ok "Directorio dist/ existe"
else
    check_fail "Directorio dist/ no existe"
    echo "   Ejecuta: cd python-cli && python3 compress_for_r2.py"
fi

# 5. Verificar índice comprimido
if [ -f "python-cli/dist/normativas_index_minimal.json.gz" ]; then
    size=$(du -h "python-cli/dist/normativas_index_minimal.json.gz" | cut -f1)
    check_ok "Índice comprimido existe ($size)"
else
    check_fail "Índice comprimido no existe"
    echo "   Ejecuta: cd python-cli && python3 compress_for_r2.py"
fi

# 6. Verificar boletines comprimidos
boletin_count=$(ls python-cli/dist/boletines/*.gz 2>/dev/null | wc -l | tr -d ' ')
if [ "$boletin_count" -gt 0 ]; then
    check_ok "Boletines comprimidos: $boletin_count archivos"
else
    check_fail "No hay boletines comprimidos"
    echo "   Ejecuta: cd python-cli && python3 compress_for_r2.py"
fi

echo ""
echo "🔧 VERIFICANDO CONFIGURACIÓN"
echo "----------------------------"

# 7. Verificar .env.example en chatbot
if [ -f "chatbot/.env.example" ]; then
    check_ok "chatbot/.env.example existe"
else
    check_warn "chatbot/.env.example no existe"
fi

# 8. Verificar package.json en chatbot
if [ -f "chatbot/package.json" ]; then
    check_ok "chatbot/package.json existe"
else
    check_fail "chatbot/package.json no existe"
fi

# 9. Verificar que node_modules existe
if [ -d "chatbot/node_modules" ]; then
    check_ok "chatbot/node_modules existe"
else
    check_warn "chatbot/node_modules no existe"
    echo "   Ejecuta: cd chatbot && pnpm install"
fi

# 10. Verificar .gitignore
if grep -q "normativas_index.json" .gitignore; then
    check_ok ".gitignore excluye archivos grandes"
else
    check_fail ".gitignore no excluye archivos grandes"
fi

echo ""
echo "📚 VERIFICANDO DOCUMENTACIÓN"
echo "----------------------------"

# 11. Verificar documentación de deployment
docs=("DEPLOYMENT_GITHUB.md" "DEPLOYMENT_CHECKLIST.md" "DEPLOYMENT_STATUS.md" "DEPLOYMENT_NEXT_STEPS.md")
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        check_ok "$doc existe"
    else
        check_warn "$doc no existe"
    fi
done

echo ""
echo "================================"
echo "📊 RESUMEN"
echo "================================"
echo ""
echo -e "${GREEN}✅ Checks exitosos: $checks_passed${NC}"
if [ $warnings -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warnings: $warnings${NC}"
fi
if [ $checks_failed -gt 0 ]; then
    echo -e "${RED}❌ Checks fallidos: $checks_failed${NC}"
fi
echo ""

# Determinar si está listo
if [ $checks_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 TODO LISTO PARA DEPLOYMENT${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. Subir datos a Cloudflare R2"
    echo "   cd python-cli && ./upload_to_r2.sh"
    echo ""
    echo "2. Deploy en Vercel"
    echo "   Ver: DEPLOYMENT_NEXT_STEPS.md"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  HAY PROBLEMAS QUE RESOLVER${NC}"
    echo ""
    echo "Revisa los checks fallidos arriba y corrígelos."
    echo ""
    exit 1
fi
