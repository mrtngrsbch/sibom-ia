# 📦 Mangrullo Data - Boletines Oficiales Municipales

> Este es el README sugerido para tu repositorio `sibom-data` en GitHub

---

## 📋 Descripción

Este repositorio contiene los datos de **Boletines Oficiales Municipales** de la Provincia de Buenos Aires, Argentina, extraídos del [Sistema SIBOM](https://sibom.slyt.gba.gob.ar/).

Los datos se utilizan para alimentar un chatbot RAG (Retrieval Augmented Generation) que permite consultar legislación municipal de manera conversacional.

---

## 📊 Contenido

- **Total de documentos**: 3,210+ boletines
- **Municipios incluidos**: Campana, Carlos Tejedor, Baradero, Benito Juárez, y más
- **Tipos de normativa**: Ordenanzas, decretos, resoluciones
- **Tamaño**:
  - Sin comprimir: ~533 MB
  - Comprimido (gzip): ~100 MB (80% ahorro)

---

## 📁 Estructura

```
sibom-data/
├── boletines/                  # Archivos JSON individuales
│   ├── Carlos_Tejedor_57.json.gz
│   ├── Campana_123.json.gz
│   └── ... (3,210 archivos)
└── boletines_index.json.gz     # Índice de metadatos
```

### Índice (boletines_index.json)

Contiene metadatos de todos los boletines para búsqueda rápida:

```json
[
  {
    "id": "Carlos_Tejedor_57",
    "municipality": "Carlos Tejedor",
    "type": "ordenanza",
    "number": "57º",
    "title": "57º de Carlos Tejedor",
    "date": "10/08/2023",
    "url": "/bulletins/9210",
    "status": "vigente",
    "filename": "Carlos_Tejedor_57.json"
  }
]
```

### Archivos Individuales (boletines/*.json)

Cada archivo contiene el texto completo del boletín:

```json
{
  "number": "57º",
  "date": "10/08/2023",
  "description": "Ordenanza municipal...",
  "type": "ordenanza",
  "link": "/bulletins/9210",
  "fullText": "VISTO... CONSIDERANDO... ARTÍCULO 1º: ..."
}
```

---

## 🔗 Uso

Este repositorio está diseñado para ser accedido via **GitHub Raw** desde aplicaciones web deployadas en Vercel, Netlify, etc.

### Ejemplo de Acceso

**Índice**:
```
https://raw.githubusercontent.com/TU-USUARIO/sibom-data/main/boletines_index.json.gz
```

**Archivo individual**:
```
https://raw.githubusercontent.com/TU-USUARIO/sibom-data/main/boletines/Carlos_Tejedor_57.json.gz
```

### Descompresión (si usas archivos .gz)

**En Node.js/TypeScript**:
```typescript
import { gunzip } from 'zlib';
import { promisify } from 'util';

const gunzipAsync = promisify(gunzip);

const response = await fetch(url);
const arrayBuffer = await response.arrayBuffer();
const decompressed = await gunzipAsync(new Uint8Array(arrayBuffer));
const json = JSON.parse(decompressed.toString('utf-8'));
```

**En Python**:
```python
import gzip
import json
import requests

response = requests.get(url)
data = gzip.decompress(response.content)
boletines = json.loads(data.decode('utf-8'))
```

---

## 🔄 Actualización

Los datos se actualizan manualmente mediante scraping del SIBOM:

```bash
# En el proyecto principal sibom-scraper-assistant
cd python-cli
python sibom_scraper.py --limit 100
python indexar_boletines.py
python comprimir_boletines.py
```

Luego se suben a este repositorio:

```bash
git add boletines/*.json.gz boletines_index.json.gz
git commit -m "Update: Add XX new bulletins"
git push
```

---

## 📈 Estadísticas de Uso

### Bandwidth

Con archivos comprimidos (gzip):
- Descarga de índice: ~150 KB
- Descarga promedio por consulta: ~650 KB (índice + 5 archivos)
- **Estimado para 3,000 consultas/mes**: ~2 GB

✅ Bien dentro del límite gratuito de GitHub (100 GB/mes)

### Performance

- **Primera carga** (cache frío): ~500-800 ms
- **Cargas subsecuentes** (cache caliente): ~50-150 ms

---

## ⚖️ Licencia y Atribución

**Fuente de datos**: [Sistema de Boletines Oficiales Municipales (SIBOM)](https://sibom.slyt.gba.gob.ar/)
**Organismo**: Subsecretaría de Asuntos Municipales, Provincia de Buenos Aires, Argentina

Los datos de boletines oficiales son de dominio público según la legislación argentina. Este repositorio los recopila y formatea para facilitar su acceso programático.

**Uso**: Libre para fines educativos, investigación y desarrollo de aplicaciones cívicas.

**Atribución requerida**: Por favor, menciona la fuente original (SIBOM) en cualquier uso de estos datos.

---

## 🤝 Contribuciones

Este es un dataset en construcción. Contribuciones bienvenidas:

- 🐛 Reportar errores en datos
- ✨ Sugerir mejoras en el formato
- 📄 Agregar más municipios
- 🔄 Scripts de actualización automática

---

## 📧 Contacto

Para consultas sobre este dataset:
- **Issues**: [GitHub Issues](https://github.com/TU-USUARIO/sibom-data/issues)
- **Proyecto principal**: [sibom-ia](https://github.com/mrtngrsbch/sibom-ia)

---

## 🏷️ Tags

`open-data` `argentina` `buenos-aires` `legislation` `municipal-law` `civic-tech` `json` `sibom` `ordenanzas` `decretos`

---

**Última actualización**: 2026-01-01
**Total documentos**: 3,210
