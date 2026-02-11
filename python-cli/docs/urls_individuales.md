# URLs Individuales en Formato V2 ✅

## Resumen

El sistema ahora soporta URLs individuales para cada norma en formato V2, mejorando significativamente la UX del chatbot.

## Cambios Implementados

### 1. Backend Python

#### Clase Normativa Actualizada
**Archivo:** `normativas_extractor.py:64-80`

```python
@dataclass
class Normativa:
    # ... campos existentes ...
    norma_url: str  # ✨ NUEVO: URL individual de la norma (V2)
    # ... más campos ...
```

#### Función save_minimal_index() Actualizada
**Archivo:** `normativas_extractor.py:421-440`

```python
def save_minimal_index(normativas: List[Normativa], output_path: Path):
    data.append({
        # ... otros campos ...
        'url': n.norma_url if hasattr(n, 'norma_url') and n.norma_url else n.source_bulletin_url,
        # Usa URL individual si existe (V2), fallback a boletín completo (V1)
    })
```

**Beneficios:**
- ✅ Compatibilidad con V1 (URLs de boletín completo)
- ✅ Soporte para V2 (URLs individuales de normas)
- ✅ Fallback automático si falta norma_url

#### Scraper Principal Actualizado
**Archivo:** `sibom_scraper.py:935-962`

Ahora crea objetos `Normativa` con todos los parámetros correctos:

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
    norma_url=norma['url'],  # ✨ URL individual de V2
    doc_index=0,
    status='vigente',
    extracted_at=datetime.now().isoformat()
)
```

### 2. Frontend Next.js

#### buildBulletinUrl() Ya Preparado
**Archivo:** `chatbot/src/lib/config.ts:23-35`

```typescript
export function buildBulletinUrl(relativePath: string): string {
  if (!relativePath) return SIBOM_BASE_URL;

  // Si ya es una URL completa, devolverla tal cual ✅
  if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
    return relativePath;  // Maneja URLs V2 directamente
  }

  // Path relativo: construir URL completa (V1)
  const path = relativePath.startsWith('/') ? relativePath : `/${relativePath}`;
  return `${SIBOM_BASE_URL}${path}`;
}
```

**Beneficios:**
- ✅ Sin modificaciones necesarias en el frontend
- ✅ Soporte transparente para V1 y V2
- ✅ URLs clickeables apuntan directamente a la norma específica

#### Retriever Usa buildBulletinUrl()
**Archivo:** `chatbot/src/lib/rag/retriever.ts:759-765`

```typescript
const sources = resultNormativas.map(n => ({
  title: `${n.t} ${n.n}/${n.y} - ${n.m}`,
  url: buildBulletinUrl(n.url),  // ✅ Maneja ambos formatos automáticamente
  municipality: n.m,
  type: n.t,
  status: 'vigente',
}));
```

## Formato de URLs

### Formato V1 (Boletín Completo)
```
https://sibom.slyt.gba.gob.ar/bulletins/1636
```

### Formato V2 (Norma Individual) ✨
```
https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278
                                              └─ boletín ─┘ └─ norma ─┘
```

## Ejemplo de Índice Minimal

```json
{
  "id": "1270278",
  "m": "Alberti",
  "t": "ordenanza",
  "n": "2319",
  "y": "2018",
  "d": "Alberti, 08/10/2018",
  "ti": "Ordenanza Nº 2319",
  "sb": "Test_Quick",
  "url": "https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278"
         └─────────────────── URL individual de la norma ──────────────┘
}
```

## Flujo de Trabajo

### Scraping con Formato V2
```bash
# El scraper V2.0 genera archivos con array de normas
python sibom_scraper.py --url https://sibom.slyt.gba.gob.ar/bulletins/1636 --limit 1

# Resultado: boletines/Alberti_1.json
{
  "municipio": "Alberti",
  "numero_boletin": "1º",
  "normas": [
    {
      "id": "1270278",
      "tipo": "ordenanza",
      "numero": "2319",
      "url": "https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278",
      # ... más campos ...
    }
  ]
}
```

### Generación de Índice Minimal
```python
# Al finalizar el scraping, se genera automáticamente
# normativas_index_minimal.json con URLs individuales

from normativas_extractor import save_minimal_index

save_minimal_index(scraper.normativas_acumuladas, Path("normativas_index_minimal.json"))
```

### Uso en el Chatbot
```
Usuario: "Quiero ver la Ordenanza 2319 de Alberti"

RAG Sistema:
1. Busca en normativas_index_minimal.json
2. Encuentra: { "url": "https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278" }
3. buildBulletinUrl() detecta que ya es URL completa → devuelve tal cual
4. Chatbot muestra link: "Ver Ordenanza Nº 2319"
                          ↓ click
5. Usuario ve DIRECTAMENTE la norma específica (no todo el boletín) ✨
```

## Beneficios para el Usuario

### Antes (V1)
```
Chatbot: "Encontré Ordenanza 2319 en Boletín 1º"
          [Ver en Mangrullo] → https://sibom.slyt.gba.gob.ar/bulletins/1636
                          ↓
Usuario debe:
  1. Abrir página del boletín completo
  2. Buscar manualmente la Ordenanza 2319
  3. Scroll por 178 normas 😩
```

### Ahora (V2) ✨
```
Chatbot: "Encontré Ordenanza 2319 en Boletín 1º"
         [Ver Ordenanza Nº 2319] → https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278
                                    ↓
Usuario ve:
  DIRECTAMENTE la Ordenanza 2319 🎯
  Sin necesidad de buscar ni hacer scroll
```

## Compatibilidad

| Formato       | URLs                                          | Frontend    | Backend     | Estado   |
| ------------- | --------------------------------------------- | ----------- | ----------- | -------- |
| V1 (fullText) | `/bulletins/1636`                             | ✅ Soportado | ✅ Soportado | Legacy   |
| V2 (normas[]) | `https://.../bulletins/1636/contents/1270278` | ✅ Soportado | ✅ Soportado | Actual ✨ |

**Conclusión:** Sistema 100% compatible con ambos formatos sin romper funcionalidad existente.

## Testing

### Test Rápido
```bash
cd python-cli
python3 test_generate_index.py
```

**Verifica:**
- ✅ URLs individuales en índice minimal
- ✅ Formato correcto de URLs completas
- ✅ Estructura JSON compatible con frontend

### Output Esperado
```
✅ Índice MINIMAL guardado: normativas_index_minimal_test.json
   Total normativas: 10
   Tamaño: 0.00 MB

Primera norma (verificar URL individual):
  URL: https://sibom.slyt.gba.gob.ar/bulletins/1636/contents/1270278
```

## Próximos Pasos

1. **Re-scraping Opcional:**
   - Los boletines existentes (V1) seguirán funcionando con URLs de boletín completo
   - Nuevos scrapings usarán V2 automáticamente con URLs individuales
   - No es necesario re-scrapear todo, puede hacerse gradualmente

2. **Deployment:**
   - El frontend ya está listo (sin cambios necesarios)
   - Subir nuevo `normativas_index_minimal.json` cuando se genere con más boletines V2

3. **Monitoreo:**
   - Verificar que las URLs individuales funcionan correctamente en producción
   - Los enlaces en el chatbot deberían apuntar directamente a normas específicas

---

**Fecha:** 2026-01-10
**Versión Scraper:** 2.0
**Versión Frontend:** Compatible con V1 + V2
**Estado:** ✅ Implementado y Probado
