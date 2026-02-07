# 🚀 INSTRUCCIONES RÁPIDAS - REFACTORING CON GLM-4.7

## PASO 1: Configurar API Key (1 minuto)

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli

# Crear archivo .env
echo "OPENROUTER_API_KEY=sk-or-v1-xxx" > .env

# Instalar dependencia
pip install python-dotenv openai
```

**¿Dónde obtener API key?**
→ https://openrouter.ai/keys

## PASO 2: Ejecutar (1 minuto)

```bash
python EXECUTE_REFACTOR.py
```

Esto:
1. Lee el prompt de `GLM_REFACTOR_PROMPT.md`
2. Lo envía a GLM-4.7
3. Muestra la respuesta
4. Guarda en `refactor_output.txt`

## PASO 3: Aplicar cambios (30 segundos)

1. Abre `refactor_output.txt`
2. Copia el código refactoreado
3. Pégalo en tu archivo Python original
4. Guarda

---

## SIMPLEMENTE EJECUTA:

```bash
python EXECUTE_REFACTOR.py
```

Y sigue las instrucciones en pantalla.
