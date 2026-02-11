# Ejemplos de Uso - Mangrullo Scraper

## 🎯 Modo Boletín Individual (NUEVO en v2.4)

### Procesar un boletín específico

```bash
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556
```

**Qué hace:**
- Procesa SOLO el boletín con ID 13556 (Boletín 98º de Carlos Tejedor)
- **Obtiene metadatos reales** (número, fecha, descripción) del boletín
- Extrae el contenido completo
- Guarda con el nombre correcto (ej: `boletines/Carlos_Tejedor_98.json`)

**Ejemplo de salida:**
```
╭─────────── 🚀 Iniciando ───────────╮
│ SIBOM Scraper                      │
│ Modo: 🎯 Boletín Individual        │
│ URL: .../bulletins/13556           │
│ Modelo: google/gemini-3-flash-...  │
╰────────────────────────────────────╯

🎯 Modo: Boletín Individual
Obteniendo metadatos del boletín 13556...
✓ Boletín: 98º - 98º de Carlos Tejedor

═══ NIVELES 2 y 3: PROCESANDO 1 BOLETINES ═══

📰 Procesando boletín: 98º
🔗 Nivel 2: Extrayendo enlaces de contenido...
```

### Procesar múltiples boletines específicos

```bash
# Procesar boletín 98º
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556

# Luego procesar boletín 105º
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/14046
```

### Con salida personalizada

```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --output boletin_98.json
```

---

## 📋 Modo Listado (Tradicional)

### Procesar desde listado de ciudad

```bash
# Procesar todos los boletines de Carlos Tejedor
python3 sibom_scraper.py

# Solo los primeros 5
python3 sibom_scraper.py --limit 5

# Con paralelismo
python3 sibom_scraper.py --limit 10 --parallel 3
```

### Otra ciudad

```bash
# Ciudad de Merlo
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/1

# Ciudad de La Plata
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/2
```

---

## 🔄 Re-procesamiento

### Re-procesar un boletín con error

Si un boletín falló (por ejemplo, el 98º):

```bash
# Opción 1: Borrar el archivo y re-procesar
rm boletines/Carlos_Tejedor_98.json
python3 sibom_scraper.py --limit 10

# Opción 2: Procesar solo ese boletín directamente
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556
```

### Re-procesar con sobreescritura

```bash
# Cuando te pregunte, elige opción 2 (Sobreescribir)
python3 sibom_scraper.py --limit 5
```

---

## 🤖 Modo Automático

### Para scripts y cron jobs

```bash
# Salta automáticamente archivos existentes
python3 sibom_scraper.py --limit 50 --skip-existing --parallel 3
```

**Útil para:**
- Scripts automatizados
- Cron jobs diarios
- Procesamiento incremental sin interacción

---

## 📊 Casos de Uso Reales

### Caso 1: Obtener un boletín urgente

```bash
# Encontraste un boletín importante en la web y quieres su texto completo
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/14046
```

### Caso 2: Actualización diaria

```bash
# En crontab (ejecutar todos los días a las 2am)
0 2 * * * cd /path/python-cli && source venv/bin/activate && \
  python3 sibom_scraper.py --limit 20 --skip-existing
```

### Caso 3: Procesar múltiples ciudades

```bash
# Script bash
for city_id in 1 2 3 15 22; do
  echo "Procesando ciudad $city_id"
  python3 sibom_scraper.py \
    --url https://sibom.slyt.gba.gob.ar/cities/$city_id \
    --limit 10 \
    --skip-existing \
    --output "ciudad_${city_id}.json"
done
```

### Caso 4: Recuperar boletines con error

```bash
# 1. Ver cuáles tienen error en boletines.md
cat boletines/boletines.md | grep "❌"

# 2. Re-procesar cada uno individualmente
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13556
python3 sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/13700
```

---

## 🔍 Debugging

### Ver qué retorna el LLM cuando falla

```bash
# Si un boletín falla con error JSON, el scraper ahora muestra:
⚠ Error parseando JSON del LLM: Extra data: line 2 column 1 (char 4674)
Respuesta recibida (primeros 500 chars):
{"links": ["/content/1"]}
{"otro": "objeto"}  ← Este es el problema
```

### Modo verbose (con debug logging)

El scraper ya incluye debug logging automático:
```
→ Procesando 1/8: 105º
→ Resultado agregado. Total acumulado: 1
→ Procesando 2/8: 104º
→ Resultado agregado. Total acumulado: 2
```

---

## 🤖 Modelos Alternativos

### Usar modelos más baratos o gratuitos

```bash
# Modelo gratuito: z-ai/glm-4.5-air:free
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free

# Modelo económico: google/gemini-2.5-flash-lite (75% más barato)
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model google/gemini-2.5-flash-lite

# Modelo premium: x-ai/grok-4.1-fast (más preciso pero más caro)
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model x-ai/grok-4.1-fast
```

### Comparación de modelos

| Modelo                                    | Costo (por 1M tokens) | Costo Boletín 98 | Velocidad  | Calidad   |
| ----------------------------------------- | --------------------- | ---------------- | ---------- | --------- |
| `z-ai/glm-4.5-air:free`                   | **GRATIS**            | **$0.00**        | Rápido     | Buena     |
| `google/gemini-2.5-flash-lite`            | $0.02                 | $0.06            | Muy rápido | Buena     |
| `google/gemini-3-flash-preview` (default) | $0.075                | $0.24            | Rápido     | Muy buena |
| `x-ai/grok-4.1-fast`                      | $0.20                 | $0.64            | Medio      | Excelente |

**Recomendación**: Para uso intensivo, prueba primero `z-ai/glm-4.5-air:free` y compara la calidad con el modelo por defecto.

---

## 💡 Tips

1. **Procesar boletines específicos**: Usa el modo individual cuando necesites un boletín concreto
2. **Incrementar límite gradualmente**: Empieza con `--limit 5`, luego aumenta
3. **Usar `--skip-existing`**: En scripts automatizados para evitar reprocesar
4. **Revisar `boletines.md`**: Es la mejor forma de ver el estado de todos los boletines
5. **Paralelismo moderado**: `--parallel 3` es un buen balance entre velocidad y rate limiting
6. **Modelos gratuitos**: Usa `--model z-ai/glm-4.5-air:free` para costo cero
7. **Comparar calidad**: Prueba un boletín con diferentes modelos para comparar

---

**Versión:** 2.5
**Fecha:** 2025-12-30
