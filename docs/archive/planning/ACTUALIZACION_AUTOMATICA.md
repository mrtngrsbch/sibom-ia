# Actualización Automática del Índice

## 📋 Resumen

El sistema tiene dos flujos de actualización dependiendo del entorno:

### En LOCAL (desarrollo)
Cuando haces clic en **"Actualizar datos"** en el Sidebar:
1. ✅ Ejecuta automáticamente `python3 indexar_boletines.py`
2. ✅ Regenera `boletines_index.json` con todos los archivos
3. ✅ Invalida el cache del retriever
4. ✅ Recarga las estadísticas

### En VERCEL (producción)
Cuando haces clic en **"Actualizar datos"** en el Sidebar:
1. ⏭️ Salta la reindexación (no hay Python disponible)
2. ✅ Invalida el cache del retriever
3. ✅ Recarga las estadísticas desde GitHub Raw

## 🔧 Configuración

### Detección automática de entorno

El endpoint `/api/reindex` detecta automáticamente si está en local:

```typescript
const isLocal = !process.env.VERCEL && !process.env.GITHUB_DATA_REPO;
```

- **Local**: Ambas variables están vacías → permite reindexación
- **Vercel**: `VERCEL=1` → bloquea reindexación (403)
- **GitHub Data**: `GITHUB_DATA_REPO` configurado → usa GitHub Raw

## 📝 Uso Manual

Si prefieres ejecutar la reindexación manualmente:

```bash
# Opción 1: Script bash (recomendado)
cd python-cli
./actualizar_index.sh

# Opción 2: Python directo
cd python-cli
python3 indexar_boletines.py
```

## 🔄 Flujo después de scrapear nuevos municipios

1. Ejecutar el scraper:
   ```bash
   python3 sibom_scraper.py
   ```

2. **AUTOMÁTICO**: Hacer clic en "Actualizar datos" en el Sidebar
   - El índice se regenera automáticamente
   - Los nuevos municipios aparecen inmediatamente

3. **MANUAL** (alternativa):
   ```bash
   ./actualizar_index.sh
   # Luego hacer clic en "Actualizar datos" en el Sidebar
   ```

## ⚙️ Archivos involucrados

- `python-cli/indexar_boletines.py` - Script de Python que genera el índice
- `python-cli/actualizar_index.sh` - Script bash wrapper
- `chatbot/src/app/api/reindex/route.ts` - Endpoint API para reindexación
- `chatbot/src/components/layout/Sidebar.tsx` - Botón "Actualizar datos"

## 🐛 Troubleshooting

### El botón no actualiza los municipios

1. Verifica que estés en local:
   ```bash
   # Debe mostrar "available": true
   curl http://localhost:3000/api/reindex
   ```

2. Verifica la consola del navegador:
   ```
   [Sidebar] Índice regenerado: { success: true, entries: 4864 }
   ```

3. Si ves "Reindexación no disponible", ejecuta manualmente:
   ```bash
   cd python-cli && python3 indexar_boletines.py
   ```

### Error al ejecutar Python

Verifica que Python 3 esté instalado:
```bash
python3 --version
# Debe mostrar Python 3.x.x
```

## 🚀 Despliegue en Vercel

En producción:
- El índice debe estar actualizado **antes** del deploy
- Vercel usa `boletines_index.json` tal como está en el repo
- El botón "Actualizar datos" solo invalida cache, no regenera índice
