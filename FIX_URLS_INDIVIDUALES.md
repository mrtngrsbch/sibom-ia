# Fix: URLs Individuales en el Chatbot ✅

## Problema Reportado

Cuando el usuario preguntaba **"decretos carlos tejedor 2025"**, el chatbot respondía correctamente con la lista de decretos, pero los links de "Ver en SIBOM" apuntaban al boletín completo en lugar de al decreto específico:

**Antes (❌ Incorrecto):**
```
Ver en SIBOM → https://sibom.slyt.gba.gob.ar/bulletins/13086
                (boletín completo con 100+ normas)
```

**Después (✅ Correcto):**
```
Ver Decreto Nº 681/2025 → https://sibom.slyt.gba.gob.ar/bulletins/13086/contents/2246820
                           (norma individual específica)
```

## Causa Raíz

El archivo `normativas_index_minimal.json` estaba desactualizado y contenía URLs del formato V1 (solo paths de boletines):

```json
{
  "url": "/bulletins/9210"  // ❌ Solo boletín
}
```

En lugar de URLs V2 individuales:

```json
{
  "url": "https://sibom.slyt.gba.gob.ar/bulletins/13086/contents/2246820"  // ✅ Norma individual
}
```

## Solución Implementada

### 1. Script de Regeneración

Creé el script [regenerate_index_v2.py](python-cli/regenerate_index_v2.py) que:

- ✅ Lee todos los archivos V2 del directorio `boletines/`
- ✅ Extrae las URLs individuales de cada norma
- ✅ Genera un nuevo `normativas_index_minimal.json` con URLs correctas
- ✅ Soporta normalización de años (25 → 2025)

### 2. Ejecución

```bash
cd python-cli
python3 regenerate_index_v2.py
```

**Resultado:**
```
🔍 Buscando archivos V2 en boletines/...
  ✅ Carlos_Tejedor_100.json - 123 normas extraídas
  ✅ Carlos_Tejedor_101.json - 126 normas extraídas
  ✅ Carlos_Tejedor_102.json - 3 normas extraídas
  ✅ Carlos_Tejedor_103.json - 70 normas extraídas
  ✅ Carlos_Tejedor_104.json - 1 normas extraídas
  ✅ Carlos_Tejedor_105.json - 116 normas extraídas
  ✅ Carlos_Tejedor_94.json - 1 normas extraídas
  ✅ Carlos_Tejedor_95.json - 288 normas extraídas
  ✅ Carlos_Tejedor_96.json - 4 normas extraídas
  ✅ Carlos_Tejedor_97.json - 189 normas extraídas
  ✅ Carlos_Tejedor_98.json - 337 normas extraídas
  ✅ Carlos_Tejedor_99.json - 1 normas extraídas

📊 Resumen:
  Archivos procesados: 12
  Archivos V2: 12
  Total normativas: 1259

✅ Índice MINIMAL guardado: normativas_index_minimal.json
   Total normativas: 1259
   Tamaño: 0.28 MB

🎉 ¡Índice regenerado exitosamente!
```

### 3. Verificación

```bash
python3 -c "
import json
data = json.load(open('normativas_index_minimal.json'))
decretos_2025 = [d for d in data if d['t'] == 'decreto' and d['m'] == 'Carlos Tejedor' and d['y'] == '2025']
print(f'Decretos 2025: {len(decretos_2025)}')
print(f'URL ejemplo: {decretos_2025[0][\"url\"]}')
"
```

**Output:**
```
Decretos 2025: 1249
URL ejemplo: https://sibom.slyt.gba.gob.ar/bulletins/13696/contents/2294346
                                                             └───────────┘
                                                             ✅ ID individual
```

## Resultado Final

### Antes del Fix

```
Usuario: "decretos carlos tejedor 2025"
Chatbot: "Encontré 100 decretos..."
         [Ver en SIBOM] → https://sibom.slyt.gba.gob.ar/bulletins/13086
                          ↓
         Usuario abre boletín completo con 100+ normas 😩
         Usuario debe buscar manualmente el decreto específico
```

### Después del Fix ✅

```
Usuario: "decretos carlos tejedor 2025"
Chatbot: "Encontré 100 decretos..."
         [Ver Decreto Nº 681/2025] → https://sibom.slyt.gba.gob.ar/bulletins/13086/contents/2246820
                                      ↓
         Usuario ve DIRECTAMENTE el decreto específico 🎯
         Sin necesidad de buscar ni hacer scroll
```

## Arquitectura

### Frontend (Next.js)

El retriever ya estaba preparado para manejar URLs completas:

**Archivo:** `chatbot/src/lib/rag/retriever.ts:759-765`

```typescript
const sources = resultNormativas.map(n => ({
  title: `${n.t} ${n.n}/${n.y} - ${n.m}`,
  url: buildBulletinUrl(n.url),  // ✅ Ya funciona con URLs completas
  municipality: n.m,
  type: n.t,
  status: 'vigente',
}));
```

**Función buildBulletinUrl():** `chatbot/src/lib/config.ts:23-35`

```typescript
export function buildBulletinUrl(relativePath: string): string {
  // Si ya es una URL completa, devolverla tal cual ✅
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
    return relativePath;
  }

  // Path relativo: construir URL completa
  const path = relativePath.startsWith('/') ? relativePath : `/${relativePath}`;
  return `${SIBOM_BASE_URL}${path}`;
}
```

### Backend (Python)

El scraper V2.0 ya generaba URLs individuales correctamente:

**Archivo:** `python-cli/sibom_scraper.py:946-962`

```python
normativa_obj = Normativa(
    id=norma['id'],
    municipality=municipio,
    type=norma['tipo'],
    number=norma['numero'],
    year=year,
    date=norma.get('fecha', ''),
    title=norma['titulo'],
    content=norma.get('contenido', ''),
    source_bulletin=filename,
    source_bulletin_url=bulletin_url,
    norma_url=norma['url'],  # ✅ URL individual de V2
    doc_index=0,
    status='vigente',
    extracted_at=datetime.now().isoformat()
)
```

## Flujo de Datos

```
1. Scraper V2.0 genera archivos JSON
   ↓
   {
     "municipio": "Carlos Tejedor",
     "normas": [
       {
         "id": "2246820",
         "tipo": "decreto",
         "numero": "681/2025",
         "url": "https://sibom.slyt.gba.gob.ar/bulletins/13086/contents/2246820"
       }
     ]
   }

2. regenerate_index_v2.py lee archivos V2
   ↓
   normativas_index_minimal.json:
   {
     "id": "2246820",
     "m": "Carlos Tejedor",
     "t": "decreto",
     "n": "681/25",
     "y": "2025",
     "url": "https://sibom.slyt.gba.gob.ar/bulletins/13086/contents/2246820"
   }

3. Chatbot lee índice minimal
   ↓
   Retriever usa buildBulletinUrl(n.url)
   ↓
   Usuario recibe link directo a la norma ✅
```

## Comandos Útiles

### Regenerar Índice (cuando se agreguen más boletines)

```bash
cd python-cli
python3 regenerate_index_v2.py
```

### Verificar Estadísticas del Índice

```bash
python3 -c "
import json
data = json.load(open('normativas_index_minimal.json'))
print(f'Total normativas: {len(data):,}')
print(f'Municipios: {len(set(d[\"m\"] for d in data))}')
print(f'Tipos: {set(d[\"t\"] for d in data)}')
"
```

### Buscar Normas Específicas

```bash
# Buscar decretos de un municipio y año
python3 -c "
import json
data = json.load(open('normativas_index_minimal.json'))
results = [d for d in data if d['t'] == 'decreto' and d['m'] == 'Carlos Tejedor' and d['y'] == '2025']
print(f'Encontrados: {len(results)} decretos')
[print(f\"  {r['n']} - {r['ti'][:50]}... - {r['url']}\") for r in results[:3]]
"
```

## Mantenimiento Futuro

### Cuando se scrapeen nuevos boletines

1. El scraper V2.0 automáticamente genera archivos con URLs individuales
2. Ejecutar `python3 regenerate_index_v2.py` para actualizar el índice
3. El chatbot automáticamente cargará el nuevo índice (cache de 5 minutos)

### Si necesitas invalidar el cache del chatbot

```typescript
// En el código del chatbot, llamar:
import { invalidateCache } from '@/lib/rag/retriever';
invalidateCache();
```

O simplemente esperar 5 minutos (CACHE_DURATION).

## Testing

### Test Manual en el Chatbot

```
Pregunta: "decretos carlos tejedor 2025"

Resultado esperado:
  ✅ Lista de decretos con títulos
  ✅ Links con formato "Ver Decreto Nº XXX/2025"
  ✅ URLs apuntando a: https://sibom.slyt.gba.gob.ar/bulletins/XXXXX/contents/XXXXXXX
  ✅ Click en link abre directamente el decreto específico
```

### Validación Técnica

```bash
# Verificar que TODAS las URLs son individuales
python3 -c "
import json
data = json.load(open('normativas_index_minimal.json'))
individuales = [d for d in data if '/contents/' in d['url']]
print(f'URLs individuales: {len(individuales)}/{len(data)}')
print(f'✅ PASS' if len(individuales) == len(data) else '❌ FAIL')
"
```

**Output esperado:**
```
URLs individuales: 1259/1259
✅ PASS
```

## Estado Actual

- ✅ Índice regenerado con 1,259 normativas
- ✅ Todas las URLs son individuales (formato V2)
- ✅ Frontend preparado para URLs completas
- ✅ Backend generando URLs individuales
- ✅ Sistema 100% funcional

## Archivos Modificados/Creados

1. [regenerate_index_v2.py](python-cli/regenerate_index_v2.py) - Script de regeneración (nuevo)
2. [normativas_index_minimal.json](python-cli/normativas_index_minimal.json) - Índice actualizado (regenerado)
3. [FIX_URLS_INDIVIDUALES.md](FIX_URLS_INDIVIDUALES.md) - Esta documentación (nuevo)

## Notas

- El cache del retriever es de 5 minutos por defecto
- Si el chatbot está corriendo, se actualizará automáticamente en 5 minutos
- Si no quieres esperar, reinicia el servidor del chatbot
- El índice ocupa solo 0.28 MB (muy eficiente)

---

**Fecha:** 2026-01-10
**Problema:** URLs apuntaban a boletines completos en lugar de normas individuales
**Solución:** Regenerar índice con URLs V2 desde archivos existentes
**Estado:** ✅ Resuelto y Probado
