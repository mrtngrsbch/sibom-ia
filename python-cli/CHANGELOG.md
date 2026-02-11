# Changelog - Mangrullo Scraper Python CLI

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [2.5] - 2025-12-30

### Agregado
- **Opción `--model`**: Permite cambiar el modelo LLM usado para extraer contenido
  - Ejemplo: `--model z-ai/glm-4.5-air:free` (modelo gratuito)
  - Ejemplo: `--model google/gemini-2.5-flash-lite` (75% más barato)
  - Soporte para cualquier modelo compatible con OpenRouter
- **Documentación de modelos alternativos**: Comparación de costos y calidad en EJEMPLOS_USO.md

### Mejorado
- Constructor de `SIBOMScraper` ahora acepta parámetro `model` opcional
- Panel inicial muestra el modelo que se está usando
- Mejor flexibilidad para optimizar costos según necesidades

## [2.4] - 2025-12-30

### Agregado
- **Modo boletín individual**: Ahora puedes procesar un boletín específico directamente con su URL
  - Ejemplo: `--url https://sibom.slyt.gba.gob.ar/bulletins/13556`
  - Detecta automáticamente si es URL de boletín o listado de ciudad
- **Manejo robusto de errores JSON**: Fallback inteligente cuando el LLM retorna JSON malformado
  - Intenta extraer el primer objeto JSON válido
  - Muestra la respuesta problemática para debugging
  - Continúa procesando en lugar de crashear

### Mejorado
- Debug logging más detallado para rastrear el flujo de procesamiento
- Mejor visualización del progreso con contadores (X/Y boletines)

## [2.3] - 2025-12-30

### Cambiado
- **Menú interactivo simplificado**: Reemplazado sistema de flechas (`inquirer`) por menú numérico (1-3)
- Eliminada dependencia de `inquirer` para mejor compatibilidad
- Interfaz más simple usando `input()` nativo de Python

### Mejorado
- Mejor compatibilidad con todos los tipos de terminales
- Eliminados problemas de interferencia visual entre inquirer y Rich
- Opción por defecto más clara (presionar Enter = opción 1)
- Proceso continúa correctamente sin confusión visual

### Corregido
- Problema donde el menú interactivo causaba confusión visual
- Clarificado que el proceso SÍ continúa correctamente al saltar boletines

## [2.2] - 2025-12-30

### Agregado
- Menú interactivo con flechas usando `inquirer` (reemplazado en v2.3)
- Tres opciones claras: Saltar, Sobreescribir, Cancelar

### Mejorado
- Mejor UX para manejo de archivos existentes

## [2.1] - 2025-12-30

### Agregado
- **Verificación de archivos existentes**: Pregunta antes de sobrescribir
- **Archivo `boletines.md`**: Índice markdown automático con tabla de boletines
- **Status con emojis**:
  - ✅ Completado (procesado exitosamente)
  - 🤖 Creado (ya existía, fue saltado)
  - ❌ Error (error real de scraping)
  - ⚠️ Sin contenido (sin enlaces)
- **Flag `--skip-existing`**: Modo automático para scripts/cron

### Mejorado
- URLs completas en `boletines.md` (con dominio incluido)
- Deduplicación en tabla markdown

## [2.0] - 2025-12-29

## 🎯 Archivos Individuales por Boletín

### ✨ Nuevas Características

**1. Generación de archivos individuales**
- Cada boletín se guarda en su propio archivo JSON
- Ubicación: carpeta `boletines/`
- Nomenclatura automática basada en la descripción del boletín

**2. Nomenclatura inteligente de archivos**
- Formato: `{Ciudad}_{Numero}.json`
- Ejemplo: `"105º de Carlos Tejedor"` → `Carlos_Tejedor_105.json`
- Caracteres especiales limpiados automáticamente
- Espacios convertidos a guiones bajos

**3. Estructura de carpetas**
```
python-cli/
├── sibom_scraper.py
├── boletines/              ← NUEVA carpeta
│   ├── Carlos_Tejedor_105.json
│   ├── Carlos_Tejedor_104.json
│   └── ...
├── sibom_results.json      ← Resumen consolidado
└── ...
```

### 🔄 Comportamiento

**Antes:**
- ❌ Todos los boletines en un solo archivo
- ❌ Difícil buscar un boletín específico
- ❌ El archivo se sobrescribía en cada ejecución

**Ahora:**
- ✅ Cada boletín en su propio archivo
- ✅ Nombres descriptivos y únicos
- ✅ Fácil organización y búsqueda
- ✅ Archivo resumen consolidado adicional

### 📝 Ejemplos

#### Procesando 1 boletín:
```bash
python sibom_scraper.py --limit 1
```

**Genera:**
- `boletines/Carlos_Tejedor_105.json` (archivo individual)
- `sibom_results.json` (resumen consolidado)

#### Procesando 5 boletines:
```bash
python sibom_scraper.py --limit 5 --output resumen_5.json
```

**Genera:**
- `boletines/Carlos_Tejedor_105.json`
- `boletines/Carlos_Tejedor_104.json`
- `boletines/Carlos_Tejedor_103.json`
- `boletines/Carlos_Tejedor_102.json`
- `boletines/Carlos_Tejedor_101.json`
- `resumen_5.json` (resumen consolidado)

### 🔧 Cambios Técnicos

#### Nuevo método: `_sanitize_filename()`
```python
def _sanitize_filename(self, description: str) -> str:
    """
    Convierte descripción en nombre de archivo válido.
    Ejemplo: "105º de Carlos Tejedor" -> "Carlos_Tejedor_105"
    """
    # Extrae número, limpia caracteres especiales, formatea
```

#### Modificación: `process_bulletin()`
```python
def process_bulletin(self, bulletin: Dict, base_url: str, output_dir: Path) -> Dict:
    """Procesa un boletín completo y guarda archivo individual"""
    # ... procesamiento ...

    # Guardar archivo individual
    filename = self._sanitize_filename(bulletin.get('description', bulletin['number']))
    filepath = output_dir / f"{filename}.json"

    with filepath.open('w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
```

#### Modificación: `scrape()`
```python
# Crear carpeta de salida
output_dir = Path("boletines")
output_dir.mkdir(exist_ok=True)
```

### 📊 Salida del Script

**Tabla de resumen actualizada:**
```
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Métrica             ┃ Valor      ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Total procesados    │ 5          │
│ Completados         │ 5          │
│ Errores             │ 0          │
│ Sin contenido       │ 0          │
│ Tiempo total        │ 245.3s     │
│ Tiempo por boletín  │ 49.1s      │
│ Carpeta boletines   │ boletines/ │  ← NUEVO
│ Resumen consolidado │ ...json    │  ← NUEVO
└─────────────────────┴────────────┘

✓ Boletines individuales guardados en: boletines/
✓ Resumen consolidado guardado en: sibom_results.json
```

### 🎯 Casos de Uso

**1. Análisis individual de boletines**
```bash
# Procesar y luego analizar archivos individuales
python sibom_scraper.py --limit 10

# Leer un boletín específico
cat boletines/Carlos_Tejedor_105.json | jq '.fullText'
```

**2. Procesamiento masivo organizado**
```bash
# Procesar todos los boletines de una ciudad
python sibom_scraper.py --parallel 3

# Los archivos quedan organizados por nombre
ls -lh boletines/
```

**3. Integración con otros scripts**
```bash
# Iterar sobre todos los boletines procesados
for file in boletines/*.json; do
  echo "Procesando: $file"
  # Tu lógica aquí
done
```

### ⚠️ Notas Importantes

1. **Carpeta `boletines/` se crea automáticamente**
   - No necesitas crearla manualmente
   - Se crea en el directorio actual donde ejecutas el script

2. **Archivos NO se sobrescriben entre ejecuciones**
   - Si procesas el mismo boletín dos veces, el archivo se sobrescribe
   - Útil para re-procesar boletines con errores

3. **Resumen consolidado sigue existiendo**
   - El archivo JSON con todos los resultados se mantiene
   - Útil para análisis agregados

### 🚀 Próximas Mejoras Sugeridas

- [ ] Opción para cambiar el nombre de la carpeta de salida
- [ ] Detección de duplicados antes de re-procesar
- [ ] Metadata adicional (timestamp, versión del script)
- [ ] Soporte para formatos adicionales (TXT, CSV)
- [ ] Compresión automática de archivos antiguos

---

**Versión:** 2.0
**Fecha:** 2025-12-30
**Modelo LLM:** google/gemini-3-flash-preview vía OpenRouter
