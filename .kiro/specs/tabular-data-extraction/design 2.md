# Design Document: Tabular Data Extraction

## Overview

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

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         HTML Input                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Table_Extractor Module                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ detect_     │  │ extract_    │  │ generate_               │  │
│  │ tables()    │→ │ structure() │→ │ metadata()              │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Bulletin JSON Output                          │
│  {                                                               │
│    "text_content": "... [TABLA_1] ...",                         │
│    "tables": [{ structured_data }],                             │
│    "metadata": { "has_tables": true }                           │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RAG System                                  │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │  Query_Router   │    │  Context Builder                    │ │
│  │  - semantic     │ →  │  - text chunks (vector search)      │ │
│  │  - computational│    │  - table data (structured lookup)   │ │
│  └─────────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. TableExtractor Class (Python)

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
    numeric_stats: Dict[str, Dict[str, float]]  # column -> {sum, max, min, avg}

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
        
        Args:
            html: Contenido HTML del documento
            
        Returns:
            tuple: (text_content con placeholders, lista de StructuredTable)
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
        
        Returns:
            {
                "text_content": str,  # Texto con placeholders [TABLA_N]
                "tables": List[dict], # Tablas estructuradas
                "metadata": {
                    "has_tables": bool,
                    "table_count": int
                }
            }
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
    
    def _table_to_dict(self, table: StructuredTable) -> dict:
        """Convierte StructuredTable a dict serializable"""
        return {
            "id": table.id,
            "title": table.title,
            "context": table.context,
            "description": table.description,
            "position": table.position,
            "schema": {
                "columns": table.schema.columns,
                "types": table.schema.types
            },
            "data": table.data,
            "stats": {
                "row_count": table.stats.row_count,
                "numeric_stats": table.stats.numeric_stats
            },
            "markdown": table.markdown,
            "extraction_errors": table.extraction_errors
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

export interface RetrievedContext {
  text: string;
  tables: TableData[];
  hasTables: boolean;
}

const COMPUTATIONAL_PATTERNS = [
  /cu[aá]l.*m[aá]s.*alto|mayor|m[aá]ximo/i,
  /cu[aá]l.*m[aá]s.*bajo|menor|m[ií]nimo/i,
  /suma|total|sumar/i,
  /promedio|media|average/i,
  /comparar|diferencia|vs|versus/i,
  /cu[aá]ntos|cantidad|n[uú]mero de/i,
  /ordenar|ranking|top/i,
  /porcentaje|%/i,
];

export function isComputationalQuery(query: string): boolean {
  return COMPUTATIONAL_PATTERNS.some(pattern => pattern.test(query));
}

export function formatTablesForLLM(tables: TableData[]): string {
  return tables.map(table => `
### ${table.title}

${table.markdown}

**Estadísticas pre-calculadas:**
- Filas: ${table.stats.row_count}
${Object.entries(table.stats.numeric_stats).map(([col, stats]) => 
  `- ${col}: suma=${stats.sum}, máx=${stats.max}, mín=${stats.min}, prom=${stats.avg.toFixed(2)}`
).join('\n')}
`).join('\n\n');
}
```

## Data Models

### Bulletin JSON Schema (Actualizado)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["number", "date", "description", "link", "status", "text_content", "tables", "metadata"],
  "properties": {
    "number": { "type": "string" },
    "date": { "type": "string" },
    "description": { "type": "string" },
    "link": { "type": "string" },
    "status": { "type": "string", "enum": ["completed", "error", "no_content", "skipped"] },
    
    "text_content": {
      "type": "string",
      "description": "Texto del documento con placeholders [TABLA_N] donde había tablas"
    },
    
    "tables": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "schema", "data", "markdown"],
        "properties": {
          "id": { "type": "string", "pattern": "^TABLA_[0-9]+$" },
          "title": { "type": "string" },
          "context": { "type": "string", "maxLength": 1000 },
          "description": { "type": "string" },
          "position": { "type": "integer", "minimum": 0 },
          "schema": {
            "type": "object",
            "properties": {
              "columns": { "type": "array", "items": { "type": "string" } },
              "types": { "type": "array", "items": { "type": "string", "enum": ["string", "number", "date"] } }
            }
          },
          "data": {
            "type": "array",
            "items": { "type": "object" }
          },
          "stats": {
            "type": "object",
            "properties": {
              "row_count": { "type": "integer" },
              "numeric_stats": { "type": "object" }
            }
          },
          "markdown": { "type": "string" },
          "extraction_errors": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    
    "metadata": {
      "type": "object",
      "properties": {
        "has_tables": { "type": "boolean" },
        "table_count": { "type": "integer" },
        "word_count": { "type": "integer" },
        "extracted_at": { "type": "string", "format": "date-time" }
      }
    },
    
    "fullText": {
      "type": "string",
      "description": "DEPRECATED: Usar text_content. Mantenido para compatibilidad."
    }
  }
}
```

### Ejemplo de Output

```json
{
  "number": "105º",
  "date": "08/01/2026",
  "description": "105º de Carlos Tejedor",
  "link": "/bulletins/12345",
  "status": "completed",
  
  "text_content": "El Concejo Deliberante de Carlos Tejedor, en sesión ordinaria del día 5 de enero de 2026, sanciona la siguiente Ordenanza:\n\nArtículo 1: Establécense las tasas municipales para el ejercicio 2026.\n\nArtículo 2: Las tasas se aplicarán según la siguiente escala:\n\n[TABLA_1]\n\nArtículo 3: Las presentes tasas entrarán en vigencia a partir del 1º de febrero de 2026.",
  
  "tables": [
    {
      "id": "TABLA_1",
      "title": "Escala de Tasas Municipales 2026",
      "context": "Artículo 2: Las tasas se aplicarán según la siguiente escala:",
      "description": "Tabla de tasas municipales que establece los montos en pesos para diferentes categorías comerciales",
      "position": 247,
      "schema": {
        "columns": ["categoria", "descripcion", "monto_pesos"],
        "types": ["string", "string", "number"]
      },
      "data": [
        {"categoria": "A", "descripcion": "Comercio menor", "monto_pesos": 1500},
        {"categoria": "B", "descripcion": "Comercio mayor", "monto_pesos": 3000},
        {"categoria": "C", "descripcion": "Industria", "monto_pesos": 5000}
      ],
      "stats": {
        "row_count": 3,
        "numeric_stats": {
          "monto_pesos": {"sum": 9500, "max": 5000, "min": 1500, "avg": 3166.67}
        }
      },
      "markdown": "| Categoría | Descripción | Monto ($) |\n|---|---|---|\n| A | Comercio menor | 1.500 |\n| B | Comercio mayor | 3.000 |\n| C | Industria | 5.000 |",
      "extraction_errors": []
    }
  ],
  
  "metadata": {
    "has_tables": true,
    "table_count": 1,
    "word_count": 89,
    "extracted_at": "2026-01-08T15:30:00Z"
  },
  
  "fullText": "El Concejo Deliberante de Carlos Tejedor..."
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Table Detection Completeness
*For any* HTML document containing N valid tables (≥2 rows, ≥2 columns), the Table_Extractor SHALL detect exactly N tables.

**Validates: Requirements 1.1, 1.3**

### Property 2: Structure Extraction Correctness
*For any* valid HTML table with H headers and R data rows, the extracted data SHALL be an array of R objects, each with exactly H keys corresponding to the normalized headers.

**Validates: Requirements 2.1, 2.2, 2.6**

### Property 3: Numeric Parsing (Argentine Format)
*For any* string representing a number in Argentine format (e.g., "1.500,00"), parsing SHALL produce the correct numeric value (e.g., 1500.00).

**Validates: Requirements 2.3, 2.4**

### Property 4: Statistics Correctness
*For any* array of numeric values, the calculated statistics (sum, max, min, avg) SHALL be mathematically correct.

**Validates: Requirements 3.3**

### Property 5: Markdown Generation Validity
*For any* extracted table, the generated Markdown SHALL be valid and contain all headers and data values.

**Validates: Requirements 3.4**

### Property 6: Placeholder Consistency
*For any* document with N tables, the text_content SHALL contain exactly N placeholders `[TABLA_1]` through `[TABLA_N]`, and each table's position SHALL be a valid index within text_content.

**Validates: Requirements 4.2, 4.3**

### Property 7: JSON Round-Trip Integrity
*For any* valid StructuredTable, serializing to JSON and deserializing SHALL produce an equivalent object with preserved types.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 8: Backward Compatibility
*For any* bulletin JSON, the existing fields (number, date, description, link, status) SHALL remain unchanged after adding table extraction.

**Validates: Requirements 4.5**

### Property 9: Computational Query Detection
*For any* query containing computational keywords (suma, máximo, comparar, cuántos), the Query_Router SHALL classify it as a computational query.

**Validates: Requirements 6.1**

### Property 10: Error Resilience
*For any* malformed table or parsing error, the extraction SHALL continue without crashing and the error SHALL be recorded in extraction_errors.

**Validates: Requirements 7.1, 7.2, 7.4**

## Error Handling

### Scraper (Python)

```python
class TableExtractionError(Exception):
    """Error durante extracción de tabla"""
    pass

class TableExtractor:
    def extract_tables(self, html: str) -> tuple[str, List[StructuredTable]]:
        tables = []
        errors = []
        
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
                    console.print(f"[yellow]⚠ {error_msg}[/yellow]")
                    errors.append(error_msg)
                    
                    # Crear tabla con error
                    tables.append(StructuredTable(
                        id=f"TABLA_{idx+1}",
                        title="Tabla con error de extracción",
                        extraction_errors=[error_msg],
                        # ... campos mínimos
                    ))
            
            text_content = self._replace_tables_with_placeholders(soup, table_elements)
            return text_content, tables
            
        except Exception as e:
            console.print(f"[red]Error fatal en extracción de tablas: {e}[/red]")
            # Fallback: retornar texto plano sin tablas
            return html, []
```

### RAG System (TypeScript)

```typescript
export async function retrieveContextWithTables(
  query: string, 
  filters: SearchFilters
): Promise<RetrievedContext> {
  try {
    const textResults = await searchTextContent(query, filters);
    
    let tables: TableData[] = [];
    if (isComputationalQuery(query)) {
      try {
        tables = await searchRelevantTables(query, filters);
      } catch (tableError) {
        console.error('[RAG] Error buscando tablas:', tableError);
        // Continuar sin tablas
      }
    }
    
    return {
      text: textResults,
      tables,
      hasTables: tables.length > 0
    };
  } catch (error) {
    console.error('[RAG] Error en retrieval:', error);
    return { text: '', tables: [], hasTables: false };
  }
}
```

## Testing Strategy

### Unit Tests (pytest)

```python
# python-cli/tests/test_table_extractor.py

import pytest
from table_extractor import TableExtractor, StructuredTable

class TestTableExtractor:
    
    def test_detect_valid_table(self):
        """Detecta tabla con >= 2 filas y 2 columnas"""
        html = """
        <table>
            <tr><th>A</th><th>B</th></tr>
            <tr><td>1</td><td>2</td></tr>
        </table>
        """
        extractor = TableExtractor()
        text, tables = extractor.extract_tables(html)
        assert len(tables) == 1
    
    def test_ignore_invalid_table(self):
        """Ignora tabla con < 2 filas"""
        html = "<table><tr><td>solo</td></tr></table>"
        extractor = TableExtractor()
        text, tables = extractor.extract_tables(html)
        assert len(tables) == 0
    
    def test_parse_argentine_number(self):
        """Parsea formato argentino correctamente"""
        extractor = TableExtractor()
        assert extractor._parse_numeric("1.500,00") == 1500.00
        assert extractor._parse_numeric("10.000") == 10000
        assert extractor._parse_numeric("3,14") == 3.14
    
    def test_normalize_header(self):
        """Normaliza headers a snake_case"""
        extractor = TableExtractor()
        assert extractor._normalize_header("Monto ($)") == "monto"
        assert extractor._normalize_header("Fecha de Vigencia") == "fecha_de_vigencia"
        assert extractor._normalize_header("Nº Ordenanza") == "n_ordenanza"
```

### Property-Based Tests (hypothesis)

```python
# python-cli/tests/test_table_properties.py

from hypothesis import given, strategies as st
import pytest
from table_extractor import TableExtractor

class TestTableProperties:
    
    @given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
    def test_stats_correctness(self, numbers):
        """
        Property 4: Statistics Correctness
        For any array of numbers, stats are mathematically correct
        
        **Feature: tabular-data-extraction, Property 4: Statistics Correctness**
        **Validates: Requirements 3.3**
        """
        extractor = TableExtractor()
        stats = extractor._calculate_numeric_stats(numbers)
        
        assert stats['sum'] == pytest.approx(sum(numbers))
        assert stats['max'] == max(numbers)
        assert stats['min'] == min(numbers)
        assert stats['avg'] == pytest.approx(sum(numbers) / len(numbers))
    
    @given(st.text(min_size=1, max_size=100))
    def test_header_normalization_produces_valid_key(self, header):
        """
        Property 2: Structure Extraction - header normalization
        For any header string, normalization produces valid snake_case
        
        **Feature: tabular-data-extraction, Property 2: Structure Extraction**
        **Validates: Requirements 2.6**
        """
        extractor = TableExtractor()
        normalized = extractor._normalize_header(header)
        
        # Debe ser snake_case válido (solo letras, números, guiones bajos)
        assert normalized == "" or normalized.replace("_", "").replace("0123456789", "").isalpha() or normalized.isalnum()
        # No debe empezar con número
        if normalized:
            assert not normalized[0].isdigit()
    
    @given(st.integers(min_value=0, max_value=1000000))
    def test_argentine_format_roundtrip(self, number):
        """
        Property 3: Numeric Parsing
        For any number, formatting as Argentine and parsing back gives same value
        
        **Feature: tabular-data-extraction, Property 3: Numeric Parsing**
        **Validates: Requirements 2.3, 2.4**
        """
        extractor = TableExtractor()
        
        # Formatear como argentino
        formatted = f"{number:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Parsear de vuelta
        parsed = extractor._parse_numeric(formatted)
        
        assert parsed == number
```

### Integration Tests

```python
# python-cli/tests/test_integration.py

def test_full_bulletin_extraction():
    """Test extracción completa de boletín con tablas"""
    html = load_test_html("bulletin_with_tables.html")
    
    scraper = SIBOMScraper(api_key="test")
    result = scraper.parse_final_content_structured(html)
    
    # Verificar estructura
    assert "text_content" in result
    assert "tables" in result
    assert "metadata" in result
    
    # Verificar placeholders
    table_count = result["metadata"]["table_count"]
    for i in range(1, table_count + 1):
        assert f"[TABLA_{i}]" in result["text_content"]
    
    # Verificar tablas
    for table in result["tables"]:
        assert "id" in table
        assert "data" in table
        assert "markdown" in table
        assert len(table["data"]) > 0
```
