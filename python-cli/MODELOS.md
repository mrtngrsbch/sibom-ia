# Guía de Modelos LLM - SIBOM Scraper

Esta guía te ayuda a elegir el modelo LLM óptimo para tu caso de uso, considerando costo, velocidad y calidad.

## 🎯 TL;DR - Recomendaciones Rápidas

| Caso de Uso | Modelo Recomendado | Comando |
|-------------|-------------------|---------|
| **Pruebas y experimentación** | `z-ai/glm-4.5-air:free` | `--model z-ai/glm-4.5-air:free` |
| **Producción con presupuesto limitado** | `google/gemini-2.5-flash-lite` | `--model google/gemini-2.5-flash-lite` |
| **Balance calidad-precio** | `google/gemini-3-flash-preview` (default) | Sin parámetro |
| **Máxima calidad** | `x-ai/grok-4.1-fast` | `--model x-ai/grok-4.1-fast` |

---

## 📊 Comparación Detallada de Modelos

### Costos y Rendimiento

| Modelo | Input ($/1M) | Output ($/1M) | Costo Boletín 98* | Velocidad | Contexto |
|--------|--------------|---------------|-------------------|-----------|----------|
| **z-ai/glm-4.5-air:free** | **GRATIS** | **GRATIS** | **$0.00** | ⚡⚡⚡ Muy rápido | 128K |
| **google/gemini-2.5-flash-lite** | $0.02 | $0.10 | **$0.06** | ⚡⚡⚡ Muy rápido | 1M |
| **google/gemini-3-flash-preview** | $0.075 | $0.30 | **$0.24** | ⚡⚡ Rápido | 1M |
| **x-ai/grok-4.1-fast** | $0.20 | $0.50 | **$0.64** | ⚡ Medio | 2M |

*Boletín 98 = 126 documentos × 25K tokens/doc = ~3.2M tokens procesados

### Calidad de Extracción

| Modelo | Precisión | Formato | HTML Complejo | Textos Legales |
|--------|-----------|---------|---------------|----------------|
| **z-ai/glm-4.5-air:free** | ⭐⭐⭐ Buena | ✅ Bueno | ⚠️ Aceptable | ✅ Bueno |
| **google/gemini-2.5-flash-lite** | ⭐⭐⭐⭐ Muy buena | ✅ Muy bueno | ✅ Bueno | ✅ Muy bueno |
| **google/gemini-3-flash-preview** | ⭐⭐⭐⭐ Muy buena | ✅ Excelente | ✅ Muy bueno | ✅ Excelente |
| **x-ai/grok-4.1-fast** | ⭐⭐⭐⭐⭐ Excelente | ✅ Excelente | ✅ Excelente | ✅ Excelente |

---

## 🔬 Análisis por Modelo

### 1. z-ai/glm-4.5-air:free (GRATIS)

**✅ Ventajas:**
- Completamente gratuito
- Muy rápido
- Contexto de 128K tokens (suficiente para documentos legales)
- Ideal para pruebas y experimentación

**⚠️ Limitaciones:**
- Puede perder algunos detalles en HTML muy complejo
- Menor consistencia en formato
- Posibles limitaciones de rate limiting (por ser gratis)

**💡 Cuándo usarlo:**
- Pruebas iniciales del scraper
- Procesamiento de boletines para análisis exploratorio
- Cuando el presupuesto es $0
- Re-procesamiento de boletines con errores (para verificar si el error era del modelo)

**🧪 Comando de prueba:**
```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free
```

---

### 2. google/gemini-2.5-flash-lite (ECONÓMICO)

**✅ Ventajas:**
- 75% más barato que el modelo por defecto
- Muy rápido (flash architecture)
- Contexto masivo de 1M tokens
- Excelente balance costo-calidad

**⚠️ Limitaciones:**
- Ligeramente menos preciso que gemini-3-flash-preview
- Puede omitir algunos detalles menores

**💡 Cuándo usarlo:**
- Producción con presupuesto limitado
- Procesamiento masivo de boletines (100+)
- Cuando la calidad "muy buena" es suficiente
- Scripts automatizados diarios

**💵 Costo estimado:**
- 10 boletines: ~$0.60
- 100 boletines: ~$6.00
- 1000 boletines: ~$60.00

**🧪 Comando de prueba:**
```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model google/gemini-2.5-flash-lite
```

---

### 3. google/gemini-3-flash-preview (DEFAULT)

**✅ Ventajas:**
- Excelente calidad de extracción
- Muy buen manejo de HTML complejo
- Mantiene integridad de textos legales
- Contexto de 1M tokens
- Probado y validado en producción

**⚠️ Limitaciones:**
- Más caro que los modelos lite/free
- No es el más rápido

**💡 Cuándo usarlo:**
- Cuando necesitas alta calidad garantizada
- Boletines críticos o importantes
- Primera vez procesando una ciudad nueva
- Cuando el costo no es la prioridad principal

**💵 Costo estimado:**
- 10 boletines: ~$2.40
- 100 boletines: ~$24.00
- 1000 boletines: ~$240.00

**🧪 Comando (por defecto):**
```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556
```

---

### 4. x-ai/grok-4.1-fast (PREMIUM)

**✅ Ventajas:**
- Máxima calidad de extracción
- Excelente para HTML muy complejo
- Contexto masivo de 2M tokens
- Mejor manejo de edge cases
- Capacidades agentic avanzadas

**⚠️ Limitaciones:**
- 2.67x más caro que el default
- 10.6x más caro que gemini-lite
- Más lento que los modelos flash

**💡 Cuándo usarlo:**
- Boletines críticos que fallaron con otros modelos
- HTML extremadamente complejo
- Cuando necesitas la mejor calidad absoluta
- Debugging de boletines problemáticos

**💵 Costo estimado:**
- 10 boletines: ~$6.40
- 100 boletines: ~$64.00
- 1000 boletines: ~$640.00

**🧪 Comando de prueba:**
```bash
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model x-ai/grok-4.1-fast
```

---

## 🧪 Metodología de Prueba

### Comparar Modelos en un Solo Boletín

```bash
# 1. Probar con modelo gratuito
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free \
  --output test_free.json

# 2. Probar con modelo económico
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model google/gemini-2.5-flash-lite \
  --output test_lite.json

# 3. Probar con modelo default
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --output test_default.json

# 4. Comparar resultados
ls -lh test_*.json
cat test_free.json | jq '.fullText' | wc -w
cat test_lite.json | jq '.fullText' | wc -w
cat test_default.json | jq '.fullText' | wc -w
```

### Métricas de Comparación

1. **Completitud**: ¿Cuántas palabras extrajo cada modelo?
2. **Formato**: ¿Se mantienen los formatos markdown correctamente?
3. **Estructura Legal**: ¿Se preservan VISTO, CONSIDERANDO, DECRETA?
4. **Artículos**: ¿Se numeran correctamente todos los artículos?
5. **Detalles**: ¿Se mantienen nombres, fechas, números exactos?

---

## 💡 Estrategias de Optimización de Costos

### Estrategia 1: Modelo Híbrido (Recomendado)

```bash
# Primer pase: usar modelo gratuito para la mayoría
python3 sibom_scraper.py --limit 100 --model z-ai/glm-4.5-air:free

# Revisar boletines.md para identificar errores
cat boletines/boletines.md | grep "❌"

# Re-procesar errores con modelo premium
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/XXXXX \
  --model google/gemini-3-flash-preview
```

**Ahorro potencial**: 90-95%

---

### Estrategia 2: Procesamiento por Lotes

```bash
# Lote 1: Boletines recientes (críticos) con modelo default
python3 sibom_scraper.py --limit 10

# Lote 2: Boletines antiguos (archivo) con modelo gratuito
python3 sibom_scraper.py --limit 100 --model z-ai/glm-4.5-air:free
```

**Ahorro potencial**: 70-80%

---

### Estrategia 3: Prueba y Escala

```bash
# 1. Probar con 1 boletín usando modelo gratuito
python3 sibom_scraper.py \
  --url https://sibom.slyt.gba.gob.ar/bulletins/13556 \
  --model z-ai/glm-4.5-air:free

# 2. Verificar calidad manualmente
cat boletines/Carlos_Tejedor_98.json | jq '.fullText' | less

# 3. Si calidad es aceptable, escalar a todos
python3 sibom_scraper.py --limit 1000 --model z-ai/glm-4.5-air:free
```

**Ahorro potencial**: 100% (si modelo gratuito es suficiente)

---

## 🔧 Configuración por Defecto

Si quieres cambiar el modelo por defecto sin usar `--model` cada vez:

### Opción 1: Modificar el código

Edita [sibom_scraper.py](sibom_scraper.py#L37):

```python
# Línea 37
self.model = "z-ai/glm-4.5-air:free"  # Cambiar aquí
```

### Opción 2: Usar alias en bash

```bash
# Agregar a ~/.bashrc o ~/.zshrc
alias sibom-free='python3 sibom_scraper.py --model z-ai/glm-4.5-air:free'
alias sibom-lite='python3 sibom_scraper.py --model google/gemini-2.5-flash-lite'
alias sibom-premium='python3 sibom_scraper.py --model x-ai/grok-4.1-fast'

# Usar
sibom-free --url https://sibom.slyt.gba.gob.ar/bulletins/13556
```

---

## ⚠️ Notas Importantes

1. **Rate Limiting**: Los modelos gratuitos pueden tener límites más estrictos
2. **Disponibilidad**: Los modelos gratuitos pueden cambiar de precio sin aviso
3. **Calidad Variable**: La calidad puede variar entre diferentes tipos de documentos
4. **Testing Recomendado**: Siempre prueba con 1-2 boletines antes de procesamiento masivo

---

## 📞 Soporte de Modelos

Puedes usar **cualquier modelo disponible en OpenRouter**. Consulta la lista completa en:
- [OpenRouter Models](https://openrouter.ai/models)

### Otros Modelos Recomendados (no probados)

```bash
# Anthropic Claude (muy preciso pero más caro)
--model anthropic/claude-3.5-sonnet

# Meta Llama (código abierto)
--model meta-llama/llama-3.2-90b-vision-instruct

# Mistral (balance europeo)
--model mistralai/mistral-large-2
```

---

**Versión:** 2.5
**Fecha:** 2025-12-30
**Última actualización de precios:** 2025-12-30
