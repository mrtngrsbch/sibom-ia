# Documento de Diseño: Extracción de Datos Tabulares

## Resumen

Este diseño implementa la extracción estructurada de datos tabulares del scraper SIBOM. El objetivo es transformar tablas HTML en estructuras de datos computables que preserven la semántica columna-fila, permitiendo al sistema RAG responder queries que requieran cálculos, comparaciones y agregaciones.

### Problema Actual
El scraper actual (`parse_final_content`) extrae tablas como texto plano, perdiendo:
- Relación header-valor
- Tipos de datos numéricos
- Capacidad de cálculo (sumas, máximos, comparaciones)

### Solución Propuesta
Implementar un sistema híbrido donde:
1. **Texto narrativo** → Vector embeddings (búsqueda semántica)
2. **Tablas estructuradas** → JSON tipado (queries computacionales)

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         HTML Input                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Módulo Table_Extractor                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ detect_     │  │ extract_    │  │ generate_               │  │
│  │ tables()    │→ │ structure() │→ │ metadata()              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    JSON de Salida del Boletín                    │
│  {                                                               │
│    "text_content": "... [TABLA_1] ...",                         │
│    "tables": [{ datos_estructurados }],                         │
│    "metadata": { "has_tables": true }                           │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Sistema RAG                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │  Query_Router   │    │  Constructor de Contexto            │ │
│  │  - semántico    │ →  │  - chunks de texto (vector search)  │ │
│  │  - computacional│    │  - datos de tabla (lookup directo)  │ │
│  └─────────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes e Interfaces

### 1. Clase TableExtractor (Python)

```python
# python-cli/table_extractor.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
import re

@dataclass
class TableSchema:
    columns: List[str]
    types: List[str]  # 'string', 'number', 'date'

@dataclass
class TableStats:
    row_count: int
    numeric_stats: Dict[str, Dict[str, float]]  # columna -> {sum, max, min, avg}

@dataclass
class StructuredTable:
    id: str
    title: str
    context: str
    description: str
    position: int  # Posición del placeholder en text_content
    schema: TableSchema
    data: List[Dict[str, Any]]
    stats: TableStats
    markdown: str
    extraction_errors: List[str]

class TableExtractor:
    """Extrae y estructura tablas HTML"""
    
    def __init__(self, context_chars: int = 500):
        self.context_chars = context_chars
    
    def extract_tables(self, html: str) -> tuple[str, List[StructuredTable]]:
        """
        Extrae tablas del HTML y retorna texto con placeholders + tablas estructuradas
        """
        pass
    
    def _detect_tables(self, soup: BeautifulSoup) -> List[Tag]:
        """Detecta elementos <table> válidos (>= 2 filas y 2 columnas)"""
        pass
    
    def _extract_context(self, table: Tag) -> str:
        """Extrae texto circundante (max context_chars antes y después)"""
        pass
    
    def _extract_headers(self, table: Tag) -> List[str]:
        """Extrae y normaliza headers a snake_case"""
        pass
    
    def _extract_rows(self, table: Tag, headers: List[str]) -> List[Dict[str, Any]]:
        """Extrae filas como dicts con valores tipados"""
        pass
    
    def _parse_numeric(self, value: str) -> Any:
        """Parsea valores numéricos (soporta formato argentino 1.500,00)"""
        pass
    
    def _normalize_header(self, header: str) -> str:
        """Normaliza header a snake_case"""
        pass
    
    def _infer_types(self, data: List[Dict[str, Any]]) -> List[str]:
        """Infiere tipos de columnas basado en los datos"""
        pass
    
    def _calculate_stats(self, data: List[Dict[str, Any]], types: List[str]) -> TableStats:
        """Calcula estadísticas para columnas numéricas"""
        pass
    
    def _generate_markdown(self, headers: List[str], data: List[Dict[str, Any]]) -> str:
        """Genera representación Markdown de la tabla"""
        pass
    
    def _generate_title(self, context: str, headers: List[str]) -> str:
        """Genera título descriptivo basado en contexto y headers"""
        pass
```

### 2. Integración con SIBOMScraper

```python
# Modificación a python-cli/sibom_scraper.py

class SIBOMScraper:
    def __init__(self, ...):
        # ... código existente ...
        self.table_extractor = TableExtractor()
    
    def parse_final_content_structured(self, html: str) -> Dict[str, Any]:
        """
        Extrae contenido preservando estructura tabular
        """
        text_content, tables = self.table_extractor.extract_tables(html)
        
        return {
            "text_content": text_content,
            "tables": [self._table_to_dict(t) for t in tables],
            "metadata": {
                "has_tables": len(tables) > 0,
                "table_count": len(tables)
            }
        }
```

### 3. Query Router (TypeScript)

```typescript
// chatbot/src/lib/query-router.ts

export interface TableData {
  id: string;
  title: string;
  markdown: string;
  data: Record<string, any>[];
  stats: {
    row_count: number;
    numeric_stats: Record<string, { sum: number; max: number; min: number; avg: number }>;
  };
}

const COMPUTATIONAL_PATTERNS = [
  /cu[aá]l.*m[aá]s.*alto|mayor|m[aá]ximo/i,
  /cu[aá]l.*m[aá]s.*bajo|menor|m[ií]nimo/i,
  /suma|total|sumar/i,
  /promedio|media|average/i,
  /comparar|diferencia|vs|versus/i,
  /cu[aá]ntos|cantidad|n[uú]mero de/i,
];

export function isComputationalQuery(query: string): boolean {
  return COMPUTATIONAL_PATTERNS.some(pattern => pattern.test(query));
}
```

## Modelos de Datos

### Schema JSON del Boletín (Actualizado)

```json
{
  "number": "105º",
  "date": "08/01/2026",
  "description": "105º de Carlos Tejedor",
  "link": "/bulletins/12345",
  "status": "completed",
  
  "text_content": "El Concejo Deliberante... [TABLA_1] ...Artículo 3...",
  
  "tables": [
    {
      "id": "TABLA_1",
      "title": "Escala de Tasas Municipales 2026",
      "context": "Artículo 2: Las tasas se aplicarán según la siguiente escala:",
      "description": "Tabla de tasas municipales con montos por categoría",
      "position": 247,
      "schema": {
        "columns": ["categoria", "descripcion", "monto_pesos"],
        "types": ["string", "string", "number"]
      },
      "data": [
        {"categoria": "A", "descripcion": "Comercio menor", "monto_pesos": 1500},
        {"categoria": "B", "descripcion": "Comercio mayor", "monto_pesos": 3000}
      ],
      "stats": {
        "row_count": 2,
        "numeric_stats": {
          "monto_pesos": {"sum": 4500, "max": 3000, "min": 1500, "avg": 2250}
        }
      },
      "markdown": "| Categoría | Descripción | Monto ($) |\n|---|---|---|\n| A | Comercio menor | 1.500 |",
      "extraction_errors": []
    }
  ],
  
  "metadata": {
    "has_tables": true,
    "table_count": 1,
    "extracted_at": "2026-01-08T15:30:00Z"
  },
  
  "fullText": "..."
}
```

## Propiedades de Correctness

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas del sistema.*

### Propiedad 1: Completitud de Detección de Tablas
*Para cualquier* documento HTML con N tablas válidas (≥2 filas, ≥2 columnas), el Table_Extractor DEBE detectar exactamente N tablas.

**Valida: Requisitos 1.1, 1.3**

### Propiedad 2: Correctitud de Extracción de Estructura
*Para cualquier* tabla HTML válida con H headers y R filas de datos, los datos extraídos DEBEN ser un array de R objetos, cada uno con exactamente H keys correspondientes a los headers normalizados.

**Valida: Requisitos 2.1, 2.2, 2.6**

### Propiedad 3: Parseo Numérico (Formato Argentino)
*Para cualquier* string representando un número en formato argentino (ej: "1.500,00"), el parseo DEBE producir el valor numérico correcto (ej: 1500.00).

**Valida: Requisitos 2.3, 2.4**

### Propiedad 4: Correctitud de Estadísticas
*Para cualquier* array de valores numéricos, las estadísticas calculadas (sum, max, min, avg) DEBEN ser matemáticamente correctas.

**Valida: Requisitos 3.3**

### Propiedad 5: Validez de Markdown Generado
*Para cualquier* tabla extraída, el Markdown generado DEBE ser válido y contener todos los headers y valores de datos.

**Valida: Requisitos 3.4**

### Propiedad 6: Consistencia de Placeholders
*Para cualquier* documento con N tablas, el text_content DEBE contener exactamente N placeholders `[TABLA_1]` hasta `[TABLA_N]`, y la posición de cada tabla DEBE ser un índice válido dentro de text_content.

**Valida: Requisitos 4.2, 4.3**

### Propiedad 7: Integridad Round-Trip JSON
*Para cualquier* StructuredTable válida, serializar a JSON y deserializar DEBE producir un objeto equivalente con tipos preservados.

**Valida: Requisitos 5.1, 5.2, 5.3**

### Propiedad 8: Compatibilidad Hacia Atrás
*Para cualquier* JSON de boletín, los campos existentes (number, date, description, link, status) DEBEN permanecer sin cambios después de agregar extracción de tablas.

**Valida: Requisitos 4.5**

### Propiedad 9: Detección de Query Computacional
*Para cualquier* query conteniendo palabras clave computacionales (suma, máximo, comparar, cuántos), el Query_Router DEBE clasificarla como query computacional.

**Valida: Requisitos 6.1**

### Propiedad 10: Resiliencia a Errores
*Para cualquier* tabla malformada o error de parseo, la extracción DEBE continuar sin crashear y el error DEBE registrarse en extraction_errors.

**Valida: Requisitos 7.1, 7.2, 7.4**

## Manejo de Errores

```python
class TableExtractor:
    def extract_tables(self, html: str) -> tuple[str, List[StructuredTable]]:
        tables = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            table_elements = self._detect_tables(soup)
            
            for idx, table_elem in enumerate(table_elements):
                try:
                    structured = self._process_table(table_elem, idx)
                    tables.append(structured)
                except Exception as e:
                    # Registrar error pero continuar
                    error_msg = f"Error en tabla {idx}: {str(e)}"
                    tables.append(StructuredTable(
                        id=f"TABLA_{idx+1}",
                        title="Tabla con error de extracción",
                        extraction_errors=[error_msg],
                        # ... campos mínimos
                    ))
            
            text_content = self._replace_tables_with_placeholders(soup, table_elements)
            return text_content, tables
            
        except Exception as e:
            # Fallback: retornar texto plano sin tablas
            return html, []
```

## Estrategia de Testing

### Tests Unitarios (pytest)

```python
def test_detect_valid_table():
    """Detecta tabla con >= 2 filas y 2 columnas"""
    html = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    extractor = TableExtractor()
    text, tables = extractor.extract_tables(html)
    assert len(tables) == 1

def test_parse_argentine_number():
    """Parsea formato argentino correctamente"""
    extractor = TableExtractor()
    assert extractor._parse_numeric("1.500,00") == 1500.00
```

### Property-Based Tests (hypothesis)

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=1000000))
def test_argentine_format_roundtrip(number):
    """Property 3: Parseo numérico round-trip"""
    extractor = TableExtractor()
    formatted = f"{number:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    parsed = extractor._parse_numeric(formatted)
    assert parsed == number
```
