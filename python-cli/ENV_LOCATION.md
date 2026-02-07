# 📍 DÓNDE COLOCAR EL ARCHIVO .ENV

## UBICACIÓN CORRECTA: 📂 `refactor/.env`

El archivo `.env` con tu API key **DEBE estar en la carpeta `refactor/`**, NO en la raíz del proyecto.

**Ruta completa**: `/Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/refactor/.env`

---

## ¿Por qué ahí?

El script `refactor/EXECUTE_REFACTOR.py` busca el archivo `.env` en este orden:

1. **Primero**: `refactor/.env` ← **PREFERIDO**
2. **Segundo**: Raíz del proyecto (`python-cli/.env`)
3. **Tercero**: Variable de entorno del sistema

Para evitar confusión, **colócalo directamente en la carpeta refactor/**.

---

## PASOS PARA CONFIGURAR (30 segundos)

### Opción A (Automática):

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/refactor

# Copia el archivo de ejemplo
cp .env.example .env

# Edita el archivo para poner tu API key
nano .env
# o code .env (VS Code)
# o open .env (macOS)
```

### Opción B (Manual):

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/refactor

echo "OPENROUTER_API_KEY=sk-or-v1-TU-CLAVE-AQUI" > .env
```

**Importante**: Reemplaza `sk-or-v1-TU-CLAVE-AQUI` con tu API key real.

---

## VERIFICAR QUE FUNCIONA

Después de crear `.env`, ejecuta:

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/refactor
python EXECUTE_REFACTOR.py
```

Si ves "✅ API key cargada", todo está correcto.

---

## ESTRUCTURA FINAL CORRECTA

```
python-cli/
└── refactor/
    ├── .env                      ← TU API KEY VA AQUÍ
    ├── .env.example              ← Plantilla (no tocar)
    ├── EXECUTE_REFACTOR.py       ← Script para ejecutar
    ├── GLM_REFACTOR_PROMPT.md    ← Prompt completo
    ├── PROMPT_SIMPLE.md          ← Prompt simple (alternativa)
    ├── REFACTOR_INSTRUCTIONS.md  ← Esta guía
    └── refactor_output.txt       ← (se crea al ejecutar)
```

---

## ⚠️ ERRORES COMUNES

**ERROR**: "No se encontró API key"

**Solución**: Estás en la carpeta incorrecta. Asegúrate de ejecutar desde `refactor/`:

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/refactor
python EXECUTE_REFACTOR.py
```

**ERROR**: "No se encuentra GLM_REFACTOR_PROMPT.md"

**Solución**: Verifica que estás ejecutando el script desde DENTRO de la carpeta refactor.

---

## 🎯 PRÓXIMO PASO

1. **Ve a la carpeta**: `cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/refactor`
2. **Crea .env**: Copia el ejemplo o créalo manualmente
3. **Ejecuta**: `python EXECUTE_REFACTOR.py`
4. **Aplica**: Copia el resultado a tu código

**¡Listo para empezar!**
