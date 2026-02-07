# JSON to CSV Converter - SIBOM Boletines

Herramienta para convertir archivos JSON de boletines extraídos con el SIBOM Scraper a formato CSV.

## 🚀 Uso Rápido

### Opción 1: Convertir un archivo individual

```bash
python3 json2csv.py Carlos_Tejedor_81.json
```

**Resultado**: Genera `Carlos_Tejedor_81.csv` con el contenido del boletín.

### Opción 2: Convertir múltiples archivos

```bash
python3 json2csv.py *.json
```

**Resultado**: Genera `boletines_25-12-30_14-35-22.csv` (con timestamp) consolidando todos los boletines.

---

## 📋 Descripción Detallada

### Opción 1: Archivo Individual

Cuando pasas un archivo JSON específico:

```bash
python3 json2csv.py boletines/Carlos_Tejedor_81.json
```

**Comportamiento:**
- Lee el archivo JSON especificado
- Extrae los campos: `number`, `date`, `description`, `link`, `status`, `fullText`
- Crea un CSV con el mismo nombre que el JSON pero con extensión `.csv`
- Ejemplo: `Carlos_Tejedor_81.json` → `Carlos_Tejedor_81.csv`

**Ejemplo de salida CSV:**
```csv
number,date,description,link,status,fullText
81º,20/01/2025,81º de Carlos Tejedor,/bulletins/12106,completed,"[DOC 1]..."
```

---

### Opción 2: Múltiples Archivos (Consolidado)

Cuando usas wildcards (`*`):

```bash
# Convertir todos los JSON en la carpeta actual
python3 json2csv.py *.json

# Convertir todos los JSON de la carpeta boletines
python3 json2csv.py boletines/*.json
```

**Comportamiento:**
- Encuentra todos los archivos JSON que coinciden con el patrón
- Lee cada archivo JSON
- Consolida todos los boletines en un ÚNICO CSV
- El nombre del archivo usa timestamp: `boletines_YY-MM-DD_HH-MM-SS.csv`
- Formato del timestamp: Año-Mes-Día_Hora-Minuto-Segundo

**Ejemplo de salida:**
```
📂 Encontrados 25 archivos JSON
✅ CSV consolidado generado: boletines_25-12-30_14-35-22.csv
   Total de boletines: 25

🎉 Conversión completada exitosamente
```

**Contenido del CSV:**
```csv
number,date,description,link,status,fullText
105º,23/12/2025,105º de Carlos Tejedor,/bulletins/14046,completed,"[DOC 1]..."
104º,11/12/2025,104º de Carlos Tejedor,/bulletins/14045,completed,"[DOC 2]..."
103º,14/11/2025,103º de Carlos Tejedor,/bulletins/13865,completed,"[DOC 3]..."
...
```

---

## 📊 Estructura del CSV

El CSV generado tiene las siguientes columnas:

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| `number` | Número del boletín | `81º` |
| `date` | Fecha de publicación | `20/01/2025` |
| `description` | Descripción del boletín | `81º de Carlos Tejedor` |
| `link` | URL relativa del boletín | `/bulletins/12106` |
| `status` | Estado del procesamiento | `completed` |
| `fullText` | Contenido completo del boletín | `[DOC 1]\n**Ordenanza...` |

---

## 💡 Ejemplos Prácticos

### Caso 1: Convertir un boletín específico

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/boletines/csv
python3 json2csv.py Carlos_Tejedor_81.json
```

**Salida:**
```
✅ CSV generado: /Users/.../boletines/csv/Carlos_Tejedor_81.csv
🎉 Conversión completada exitosamente
```

### Caso 2: Convertir todos los boletines de la carpeta csv

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/boletines/csv
python3 json2csv.py *.json
```

**Salida:**
```
📂 Encontrados 3 archivos JSON
✅ CSV consolidado generado: /Users/.../boletines/csv/boletines_25-12-30_12-29-15.csv
   Total de boletines: 3
🎉 Conversión completada exitosamente
```

### Caso 3: Convertir todos los boletines desde la carpeta padre

```bash
cd /Users/mrtn/Documents/GitHub/sibom-scraper-assistant/python-cli/boletines
python3 csv/json2csv.py *.json
```

**Salida:**
```
📂 Encontrados 28 archivos JSON
✅ CSV consolidado generado: /Users/.../python-cli/boletines/boletines_25-12-30_12-30-45.csv
   Total de boletines: 28
🎉 Conversión completada exitosamente
```

---

## 🔧 Opciones Avanzadas

### Ordenar boletines por fecha

Si quieres que el CSV consolidado esté ordenado por fecha, puedes usar el siguiente comando:

```bash
# Convertir todos
python3 json2csv.py boletines/*.json

# Luego ordenar con herramientas de sistema
sort -t',' -k2 -r boletines_25-12-30_14-35-22.csv > boletines_ordenados.csv
```

### Filtrar solo boletines completados

```bash
# Primero convierte todos
python3 json2csv.py boletines/*.json

# Luego filtra los completados
grep ",completed," boletines_25-12-30_14-35-22.csv > boletines_completados.csv
```

### Extraer solo metadatos (sin texto completo)

Si solo necesitas los metadatos sin el texto completo:

```bash
# Convertir
python3 json2csv.py boletines/*.json

# Extraer solo columnas 1-5 (sin fullText)
cut -d',' -f1-5 boletines_25-12-30_14-35-22.csv > metadatos.csv
```

---

## ⚠️ Notas Importantes

1. **Encoding UTF-8**: Los CSV se generan con codificación UTF-8 para preservar caracteres especiales (ñ, tildes, etc.)

2. **Texto completo preservado**: La columna `fullText` contiene TODO el contenido extraído, incluyendo saltos de línea y caracteres especiales. Esto puede hacer que el archivo CSV sea muy grande.

3. **Compatibilidad Excel**:
   - Excel puede tener problemas con UTF-8.
   - Si necesitas abrir en Excel, usa "Importar datos" en lugar de doble clic.
   - O convierte a CSV con encoding Latin-1 usando herramientas adicionales.

4. **Archivos grandes**: Si tienes muchos boletines (100+), el CSV consolidado puede ser muy grande (varios MB).

---

## 🐛 Troubleshooting

### Error: "Archivo no encontrado"

```bash
❌ Archivo no encontrado: Carlos_Tejedor_81.json
```

**Solución**: Verifica que el archivo existe y que estás en el directorio correcto.

```bash
ls boletines/Carlos_Tejedor_81.json
```

### Error: "No se encontraron archivos"

```bash
❌ No se encontraron archivos que coincidan con: *.json
```

**Solución**: Verifica que hay archivos JSON en el directorio:

```bash
ls boletines/*.json
```

### Error al leer JSON

```bash
⚠ Error leyendo archivo.json: Expecting value: line 1 column 1 (char 0)
```

**Solución**: El archivo JSON está corrupto o vacío. Verifica su contenido:

```bash
cat archivo.json | head -10
```

---

## 📈 Casos de Uso

### Análisis de datos

Importa el CSV en herramientas como:
- **Excel**: Para análisis básico
- **Google Sheets**: Para colaboración
- **Python Pandas**: Para análisis avanzado
- **R**: Para estadísticas
- **Power BI / Tableau**: Para visualizaciones

### Ejemplo con Pandas

```python
import pandas as pd

# Leer CSV
df = pd.read_csv('boletines_25-12-30_14-35-22.csv')

# Ver primeros boletines
print(df.head())

# Contar por status
print(df['status'].value_counts())

# Filtrar por fecha
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
recent = df[df['date'] > '2025-01-01']

# Buscar texto específico
search = df[df['fullText'].str.contains('ORDENANZA', case=False)]
```

---

## 🔗 Integración con SIBOM Scraper

### Flujo completo

```bash
# 1. Extraer boletines con el scraper
python3 sibom_scraper.py --limit 10 --model z-ai/glm-4.5-air:free

# 2. Convertir a CSV
python3 json2csv.py boletines/*.json

# 3. El CSV ya está listo para análisis
```

### Script automatizado

```bash
#!/bin/bash
# extract_and_convert.sh

# Extraer boletines
echo "📥 Extrayendo boletines..."
python3 sibom_scraper.py --limit 50 --skip-existing

# Convertir a CSV
echo "📊 Convirtiendo a CSV..."
python3 json2csv.py boletines/*.json

echo "✅ Proceso completado"
```

---

## 📝 Changelog

### v1.2 - 2025-12-30
- ✨ **MEJORA**: Los archivos CSV se generan en el directorio actual de ejecución (no en la ubicación del script)
- 📍 Usa `Path.cwd()` para determinar la ubicación de salida
- 💡 Permite ejecutar el script desde cualquier carpeta: `python3 ../json2csv.py *.json`

### v1.1 - 2025-12-30
- 🐛 **FIX**: Detección correcta de múltiples archivos cuando el shell expande `*.json`
- ✨ Manejo robusto de argumentos: detecta múltiples archivos por cantidad de argumentos (`len(sys.argv) > 2`)
- ✨ Soporte para wildcards entre comillas: `python3 json2csv.py '*.json'`

### v1.0 - 2025-12-30
- ✨ Conversión individual de JSON a CSV
- ✨ Conversión consolidada de múltiples JSON
- ✨ Timestamp automático para archivos consolidados
- ✨ Soporte completo para UTF-8
- ✨ Manejo de errores robusto

---

**Autor**: SIBOM Scraper Team
**Fecha**: 2025-12-30
**Versión**: 1.0
