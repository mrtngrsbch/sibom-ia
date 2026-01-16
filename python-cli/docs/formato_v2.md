# Scraper V2.0 - Normas Individuales

## 🎯 Cambios Principales

### Versión Anterior (V1)
- **1 request por boletín**
- Texto concatenado sin estructura
- URLs solo del boletín completo
- Tablas y montos mezclados

### Versión Nueva (V2)
- **N+1 requests por boletín** (1 del boletín + 1 por cada norma)
- Normas individuales con URLs específicas
- Tablas y montos por norma
- Metadatos ricos por norma

---

## 📊 Nuevo Formato JSON

```json
{
  "municipio": "Alberti",
  "numero_boletin": "1º",
  "fecha_boletin": "30/11/2018",
  "boletin_url": "https://sibom.slyt.gba.gob.ar/bulletins/1636",
  "status": "completed",
  "total_normas": 178,

  "normas": [
    {
      "id": "1270278",
      "tipo": "ordenanza",
      "numero": "2319",
      "titulo": "Ordenanza Nº 2319",
      "fecha": "Alberti, 08/10/2018",
      "municipio": "Alberti",
      "url": "https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278",

      "contenido": "VISTO: El Decreto...",

      "tablas": [
        {
          "id": "TABLA_1",
          "titulo": "Detalle de Deuda Municipal",
          "headers": ["Concepto", "Mes", "Importe"],
          "data": [
            {"Concepto": "Electricidad", "Mes": "Enero", "Importe": 15000.50}
          ],
          "stats": {
            "row_count": 1,
            "numeric_stats": {
              "Importe": {"sum": 15000.50, "max": 15000.50, "min": 15000.50, "avg": 15000.50}
            }
          }
        }
      ],

      "montos_extraidos": [
        {
          "municipio": "Alberti",
          "boletin": "1º",
          "fecha": "Alberti, 08/10/2018",
          "norma_tipo": "Ordenanza",
          "norma_numero": "2319",
          "articulo": "1",
          "concepto": "deuda municipal con Cooperativa",
          "monto": 59110.95,
          "moneda": "ARS",
          "texto_completo": "Boletín 1º | Alberti | Ordenanza Nº2319...",
          "fuente_url": "https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278"
        }
      ],

      "metadata": {
        "longitud_caracteres": 1234,
        "tiene_tablas": true,
        "total_tablas": 1,
        "total_montos": 1
      }
    }
  ],

  "metadata_boletin": {
    "total_caracteres": 425000,
    "total_tablas": 45,
    "total_montos": 178,
    "fecha_scraping": "2026-01-10T15:30:00Z",
    "version_scraper": "2.0"
  }
}
```

---

## 🚀 Nuevas Características

### 1. **User-Agent Real**
```python
self.headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
    'Accept': 'text/html,application/xhtml+xml...',
    # ... más headers de navegador real
}
```

**Beneficio:** Simula navegador real, reduce riesgo de detección como bot.

---

### 2. **Jitter Aleatorio**
```python
jitter = random.uniform(-self.jitter_range, self.jitter_range)
actual_delay = max(1.0, self.rate_limit_delay + jitter)
```

**Beneficio:** Delays variables (2-4 segundos) evitan patrón detecta.

**Ejemplo:**
- Request 1: espera 2.3 segundos
- Request 2: espera 3.7 segundos
- Request 3: espera 2.9 segundos

---

### 3. **Modo Resume**
```python
# Guarda progreso después de cada norma
self._save_progress(bulletin_id, output_dir, normas_procesadas, normas_pendientes)

# Retoma desde última norma si se interrumpe
progress_data = self._load_progress(bulletin_id, output_dir)
```

**Archivos de progreso:**
```
boletines/.progress_1636.json
{
  "bulletin_id": "1636",
  "timestamp": 1736531400.123,
  "normas_procesadas": ["1270278", "1270283", "1270287"],
  "normas_pendientes": ["1270290", "1270295", ...],
  "total": 178,
  "completed": 3
}
```

**Beneficio:** Si falla scraping (conexión, KeyboardInterrupt), retoma desde última norma.

---

### 4. **URLs Individuales**

**Antes (V1):**
```
Chatbot: "Ver en SIBOM" → https://sibom.slyt.gba.gob.ar/bulletins/1636
```

**Ahora (V2):**
```
Chatbot: "Ver Ordenanza Nº 2319" → https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278
```

**Beneficio:** UX mucho mejor, lleva directo a la norma específica.

---

## 📈 Impacto en Performance

### Tiempo de Scraping

| Tamaño Boletín | V1 (requests) | V2 (requests) | Tiempo V1 | Tiempo V2 |
|----------------|---------------|---------------|-----------|-----------|
| Pequeño (10 normas) | 1 | 11 | ~3 seg | ~45 seg |
| Mediano (50 normas) | 1 | 51 | ~3 seg | ~4 min |
| Grande (178 normas) | 1 | 179 | ~3 seg | ~9 min |

**Fórmula:** `Tiempo ≈ (N_normas + 1) * delay_promedio`

Con jitter: `delay_promedio = 3 ± 1 segundos = 2-4 segundos`

---

## 🎯 Beneficios para el Chatbot

### 1. **Búsqueda Precisa**
```
Usuario: "¿Cuál es el salario del intendente de Alberti?"

RAG:
1. Busca en todas las normas de Alberti
2. Filtra por "salario" + "intendente"
3. Encuentra Ordenanza Nº 2320
4. Extrae tabla o monto específico
5. Responde: "$500,000 mensuales (Ordenanza 2320 - Ver aquí)"
```

### 2. **Queries Cross-Municipio**
```
Usuario: "Comparar tasas de servicios en toda la provincia"

RAG:
1. Busca tablas con tag "tasas"
2. Agrupa por municipio
3. Genera tabla comparativa:

| Municipio | Tasa Básica | Tasa Adicional |
|-----------|-------------|----------------|
| Alberti   | $1,500      | $500           |
| Merlo     | $1,800      | $450           |
| ...       | ...         | ...            |
```

### 3. **Análisis Estadístico**
```
Usuario: "¿Qué municipio tiene más ordenanzas sobre presupuesto?"

RAG:
1. Cuenta normas WHERE tipo="ordenanza" AND contenido CONTAINS "presupuesto"
2. Agrupa por municipio
3. Responde: "Merlo tiene 23 ordenanzas, Alberti tiene 15..."
```

---

## 🛡️ Medidas Anti-Ban

### Implementadas (V2.0)
✅ User-Agent real
✅ Jitter aleatorio
✅ Modo resume

### Disponibles si hay problemas
⏸️ Delays más largos (configurar `rate_limit_delay = 5-10`)
⏸️ Pausas cada N normas
⏸️ Scraping nocturno (crontask)
⏸️ Modo batch (10 normas → pausa 5 min)

---

## 🔧 Uso

### Test Rápido
```bash
python test_new_scraper.py
```

### Scraping Normal
```bash
python sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/1636 --limit 1
```

### Scraping con Skip Existing
```bash
python sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22 --skip-existing
```

### Resume Automático
Si el scraping se interrumpe, simplemente vuelve a ejecutar el mismo comando:
```bash
python sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/1636
# → Detecta progreso previo
# → Retoma desde última norma procesada
```

---

## 📦 Archivos Generados

### Por boletín:
```
boletines/Alberti_1.json      (formato V2 con normas individuales)
boletines/.progress_1636.json (progreso temporal, se elimina al completar)
```

### Índices globales:
```
montos_index.json              (todos los montos agregados)
normativas_index.json          (todas las normativas completas)
normativas_index_compact.json  (sin contenido, solo metadatos)
normativas_index_minimal.json  (mínimo para frontend)
boletines.md                   (índice Markdown)
```

---

## 🔍 Migración desde V1

Los JSONs antiguos (V1) tienen este formato:
```json
{
  "number": "1º",
  "date": "30/11/2018",
  "link": "/bulletins/1636",
  "text_content": "TODO EL TEXTO...",
  "status": "completed"
}
```

Los nuevos (V2) tienen:
```json
{
  "municipio": "Alberti",
  "numero_boletin": "1º",
  "fecha_boletin": "30/11/2018",
  "boletin_url": "https://...",
  "normas": [...],
  "status": "completed"
}
```

**No son compatibles**. Si quieres regenerar todos los boletines con V2:

```bash
rm boletines/*.json
python sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/cities/22
```

---

## ⚠️ Notas Importantes

1. **Tiempo de scraping:** Boletines grandes (100+ normas) pueden tardar 5-10 minutos
2. **Modo resume:** Si se interrumpe, retoma automáticamente
3. **Rate limiting:** Respeta delay de 3±1 segundos entre requests
4. **Progreso visible:** Barra de progreso muestra normas procesadas en tiempo real
5. **Archivos .progress_*:** Se eliminan automáticamente al completar boletín

---

## 🎓 Para más información

Ver `.agents/specs/` para arquitectura completa del sistema.
