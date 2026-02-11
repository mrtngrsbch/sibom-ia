# Nuevas Características - Mangrullo Scraper CLI

## 🆕 Últimas Actualizaciones (2025-12-30)

### 1. Verificación de Archivos Existentes

El scraper ahora verifica si un boletín ya fue procesado antes de comenzar el scraping.

#### Comportamiento por Defecto (Modo Interactivo)

Si un archivo ya existe, el script pregunta al usuario:

```bash
python sibom_scraper.py --limit 5
```

```
⚠ El archivo Carlos_Tejedor_105.json ya existe
¿Deseas sobreescribir? (s/N):
```

**Opciones:**
- **`s`/`si`/`sí`**: Sobrescribe el archivo existente
- **`n`/`N`** (o Enter): Salta el boletín y continúa con el siguiente

#### Modo Automático con `--skip-existing`

Para automatización o scripts, usa el flag `--skip-existing`:

```bash
python sibom_scraper.py --limit 10 --skip-existing
```

**Comportamiento:**
- ⏭ Salta automáticamente boletines ya procesados
- ✅ No pregunta al usuario
- 🚀 Perfecto para ejecuciones en background o cron jobs

**Ejemplo de salida:**
```
⏭ Saltando boletín 105º (ya existe)
⏭ Saltando boletín 104º (ya existe)

📰 Procesando boletín: 103º
```

---

### 2. Archivo Índice `boletines.md`

El scraper genera automáticamente un archivo markdown con una tabla de todos los boletines procesados.

#### Ubicación
```
boletines/boletines.md
```

#### Formato

```markdown
# Boletines Procesados

| Number | Date       | Description            | Link                                                                                           | Status          |
| ------ | ---------- | ---------------------- | ---------------------------------------------------------------------------------------------- | --------------- |
| 105º   | 23/12/2025 | 105º de Carlos Tejedor | [https://sibom.slyt.gba.gob.ar/bulletins/14046](https://sibom.slyt.gba.gob.ar/bulletins/14046) | ✅ Completado    |
| 104º   | 11/12/2025 | 104º de Carlos Tejedor | [https://sibom.slyt.gba.gob.ar/bulletins/14045](https://sibom.slyt.gba.gob.ar/bulletins/14045) | ✅ Completado    |
| 103º   | 04/12/2025 | 103º de Carlos Tejedor | [https://sibom.slyt.gba.gob.ar/bulletins/14044](https://sibom.slyt.gba.gob.ar/bulletins/14044) | ⚠️ Sin contenido |
```

#### Características

- **Actualización automática**: Se actualiza con cada boletín procesado
- **URLs clickeables**: Enlaces completos a los boletines originales
- **Status visual**: Emojis para indicar el estado:
  - ✅ Completado - Boletín procesado exitosamente en esta ejecución
  - 🤖 Creado - Boletín ya existía, fue saltado
  - ❌ Error - Error real durante el scraping
  - ⚠️ Sin contenido - Boletín sin enlaces de contenido
  - ❓ Desconocido - Estado indeterminado
- **Formato estándar**: Tabla markdown compatible con GitHub, GitLab, etc.
- **Deduplicación**: Si un boletín se procesa dos veces, actualiza la entrada existente

#### Visualización

El archivo se ve así en GitHub/GitLab:

| Number | Date       | Description            | Link                                                                                           | Status       |
| ------ | ---------- | ---------------------- | ---------------------------------------------------------------------------------------------- | ------------ |
| 105º   | 23/12/2025 | 105º de Carlos Tejedor | [https://sibom.slyt.gba.gob.ar/bulletins/14046](https://sibom.slyt.gba.gob.ar/bulletins/14046) | ✅ Completado |
| 104º   | 11/12/2025 | 104º de Carlos Tejedor | [https://sibom.slyt.gba.gob.ar/bulletins/14045](https://sibom.slyt.gba.gob.ar/bulletins/14045) | ✅ Completado |

---

## 🔧 Casos de Uso

### Caso 1: Primera Ejecución

```bash
python sibom_scraper.py --limit 10
```

- Procesa 10 boletines
- Crea archivos JSON individuales en `boletines/`
- Genera `boletines.md` con las 10 entradas

### Caso 2: Re-ejecución Incremental

```bash
# Segunda ejecución con --skip-existing
python sibom_scraper.py --limit 20 --skip-existing
```

- Salta los primeros 10 ya procesados
- Procesa los nuevos 10 boletines
- Actualiza `boletines.md` con las 10 nuevas entradas

### Caso 3: Re-procesar un Boletín con Error

```bash
# Sin --skip-existing para preguntar
python sibom_scraper.py --limit 15
```

```
⚠ El archivo Carlos_Tejedor_105.json ya existe
¿Deseas sobreescribir? (s/N): s
♻️ Sobreescribiendo Carlos_Tejedor_105.json...
```

- Re-procesa el boletín con error
- Actualiza el archivo JSON
- Actualiza el status en `boletines.md`

### Caso 4: Automatización con Cron

```bash
# Crontab: Ejecutar diariamente
0 2 * * * cd /path/to/python-cli && source venv/bin/activate && python sibom_scraper.py --limit 100 --skip-existing --parallel 3
```

- Procesa solo boletines nuevos
- No requiere interacción
- Actualiza `boletines.md` automáticamente

---

## 📊 Estructura de Archivos

```
python-cli/
├── boletines/
│   ├── boletines.md                 ← NUEVO: Índice en markdown
│   ├── Carlos_Tejedor_105.json
│   ├── Carlos_Tejedor_104.json
│   └── Carlos_Tejedor_103.json
├── sibom_results.json               ← Resumen consolidado
└── sibom_scraper.py
```

---

## 🎯 Ventajas

### Verificación de Existentes

✅ **Ahorro de tiempo**: No re-procesa boletines ya descargados
✅ **Ahorro de costos**: No gasta tokens LLM en contenido ya procesado
✅ **Flexibilidad**: Modo interactivo o automático según necesidad
✅ **Control**: Opción de sobreescribir cuando se necesite

### Archivo `boletines.md`

✅ **Visualización rápida**: Ver todos los boletines en una tabla
✅ **Navegación fácil**: Links clickeables a boletines originales
✅ **Status claro**: Identificar rápidamente errores o faltantes
✅ **Documentación**: Historial de lo procesado
✅ **Compatible**: Funciona en GitHub, GitLab, editors markdown

---

## 🔍 Detalles Técnicos

### Algoritmo de Verificación

```python
1. Generar nombre de archivo desde descripción
2. Verificar si archivo existe en boletines/
3. Si existe:
   - Con --skip-existing: Leer archivo existente y retornar
   - Sin --skip-existing: Preguntar al usuario
4. Si no existe o usuario confirma: Procesar normalmente
```

### Actualización de `boletines.md`

```python
1. Crear archivo si no existe (con header y tabla)
2. Leer contenido actual
3. Buscar si ya existe entrada para este número de boletín
4. Si existe: Reemplazar línea existente
5. Si no existe: Agregar nueva línea al final
```

### URLs Completas

El script convierte automáticamente:
- **Entrada**: `/bulletins/14046`
- **Salida en MD**: `https://sibom.slyt.gba.gob.ar/bulletins/14046`

---

## 🚀 Próximas Mejoras Planificadas

- [ ] Opción `--overwrite-errors` para re-procesar solo boletines con errores
- [ ] Filtro por fecha en `boletines.md`
- [ ] Estadísticas en el encabezado del `boletines.md`
- [ ] Exportar `boletines.md` a CSV/Excel
- [ ] Opción para ordenar tabla por fecha, número o status

---

**Versión:** 2.3
**Fecha:** 2025-12-30

### Mejoras en v2.3 (2025-12-30)
- Reemplazado menú con flechas por menú numérico más compatible
- Eliminada dependencia de `inquirer`
- Mejor compatibilidad con todos los terminales
- Interfaz más simple y directa con opciones numéricas (1-3)
