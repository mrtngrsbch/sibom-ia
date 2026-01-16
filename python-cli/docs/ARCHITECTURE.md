# Arquitectura del Índice de Normativas

## Problema Original

El índice actual (`boletines_index.json`) solo contiene **boletines**, no normativas individuales:
- 1 boletín = 1 entrada en el índice
- Pero 1 boletín contiene 10-500 normativas mezcladas en `fullText`
- El chat debe parsear megabytes de texto para encontrar un decreto

## Nueva Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                     ÍNDICES (python-cli/)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  boletines_index.json          normativas_index.json            │
│  ┌──────────────────┐          ┌────────────────────────┐       │
│  │ id: boletin_98   │          │ id: decreto_1607       │       │
│  │ municipality     │ ◄──────► │ municipality           │       │
│  │ type: "boletin"  │          │ type: "decreto"        │       │
│  │ documentTypes[]  │          │ source_bulletin        │       │
│  │ filename         │          │ content (2-5KB)        │       │
│  └──────────────────┘          │ ...                    │       │
│        │                       └────────────────────────┘       │
│        ▼                                                        │
│  boletines/                                                     │
│  └── Carlos_Tejedor_98.json   (fullText completo, backup)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Schema: Normativa Individual

```json
{
  "id": "Carlos_Tejedor_decreto_1607_2025",
  "municipality": "Carlos Tejedor",
  "type": "decreto",
  "number": "1607",
  "year": "2025",
  "date": "01/07/2025",
  "title": "Designación de personal en Servicios Urbanos",
  "content": "VISTO: La necesidad de afectar al agente... [2-5KB]",
  "source_bulletin": "Carlos_Tejedor_98",
  "source_bulletin_url": "/bulletins/13556",
  "doc_index": 1,
  "status": "vigente",
  "extracted_at": "2026-01-09T15:30:00Z"
}
```

## Tipos de Normativas Soportados

| Tipo | Patrón de Detección | Frecuencia |
|------|---------------------|------------|
| `decreto` | `Decreto N[º°] \d+` | ~60% |
| `ordenanza` | `Ordenanza N[º°] \d+` | ~20% |
| `resolucion` | `Resolución N[º°] \d+` | ~10% |
| `convenio` | `Convenio N[º°]? \d*` | ~5% |
| `licitacion` | `Licitación Pública N[º°] \d+` | ~3% |
| `disposicion` | `Disposición N[º°] \d+` | ~1% |
| `comunicacion` | `Comunicación N[º°] \d+` | <1% |
| `acta` | `Acta N[º°] \d+` | <1% |

## Estimación de Escala

| Métrica | Valor |
|---------|-------|
| Municipios | 100-150 |
| Boletines por municipio | ~100 |
| Normativas por boletín | ~50 promedio |
| **Total normativas** | **500,000 - 750,000** |
| Tamaño promedio | 2.5 KB |
| **Tamaño total datos** | **1.5 - 2 GB** |
| **Tamaño índice JSON** | **~200 MB** |

## Flujos de Procesamiento

### 1. Post-procesamiento (datos existentes)
```bash
python extract_normativas.py --input boletines/ --output normativas_index.json
```

### 2. Tiempo real (durante scraping)
```python
# En sibom_scraper.py, después de guardar el boletín:
normativas = extract_normativas_from_bulletin(bulletin_data)
append_to_index(normativas, 'normativas_index.json')
```

## Beneficios

| Antes | Después |
|-------|---------|
| Enviar 775KB al LLM | Enviar 2.5KB al LLM |
| ~200,000 tokens/query | ~1,000 tokens/query |
| BM25 indexa 50KB (truncado) | BM25 indexa 100% del contenido |
| No puede listar decretos | Lista exacta de normativas |
| $0.20 por query | $0.001 por query |

## Compatibilidad

- `boletines_index.json`: Se mantiene sin cambios (backup, compatibilidad)
- `boletines/*.json`: Se mantienen sin cambios (fullText completo)
- Nuevo: `normativas_index.json` es la fuente principal para el chat
