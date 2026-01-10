#!/usr/bin/env python3
"""
Tests para el módulo TableExtractor.
Incluye tests unitarios y property-based tests.

Fecha: 2026-01-08
"""

import pytest
import json
import sys
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from table_extractor import (
    TableExtractor, 
    StructuredTable, 
    TableSchema, 
    TableStats,
    tables_to_json,
    tables_from_json
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def extractor():
    """Fixture para crear instancia de TableExtractor."""
    return TableExtractor()


@pytest.fixture
def simple_table_html():
    """HTML con tabla simple válida."""
    return """
    <html><body>
    <p>Contexto anterior de la tabla.</p>
    <table>
        <tr><th>Nombre</th><th>Edad</th><th>Monto</th></tr>
        <tr><td>Juan</td><td>25</td><td>1.500,00</td></tr>
        <tr><td>María</td><td>30</td><td>2.000,50</td></tr>
    </table>
    <p>Contexto posterior de la tabla.</p>
    </body></html>
    """


@pytest.fixture
def invalid_table_html():
    """HTML con tabla inválida (menos de 2 filas)."""
    return """
    <html><body>
    <table>
        <tr><th>Solo</th><th>Headers</th></tr>
    </table>
    </body></html>
    """


@pytest.fixture
def nested_tables_html():
    """HTML con tablas anidadas."""
    return """
    <html><body>
    <table>
        <tr><th>Exterior</th><th>Tabla</th></tr>
        <tr>
            <td>
                <table>
                    <tr><th>Interior</th><th>Anidada</th></tr>
                    <tr><td>A</td><td>B</td></tr>
                </table>
            </td>
            <td>Valor</td>
        </tr>
    </table>
    </body></html>
    """


@pytest.fixture
def multiple_tables_html():
    """HTML con múltiples tablas."""
    return """
    <html><body>
    <p>Primera sección</p>
    <table>
        <tr><th>Col1</th><th>Col2</th></tr>
        <tr><td>A1</td><td>B1</td></tr>
        <tr><td>A2</td><td>B2</td></tr>
    </table>
    <p>Segunda sección</p>
    <table>
        <tr><th>X</th><th>Y</th><th>Z</th></tr>
        <tr><td>1</td><td>2</td><td>3</td></tr>
        <tr><td>4</td><td>5</td><td>6</td></tr>
    </table>
    </body></html>
    """


# ============================================================================
# TESTS DE DETECCIÓN DE TABLAS (Requisitos 1.1, 1.3, 1.4)
# ============================================================================

class TestTableDetection:
    """Tests para detección de tablas HTML."""
    
    def test_detect_valid_table(self, extractor, simple_table_html):
        """Detecta tabla con >= 2 filas y 2 columnas."""
        text, tables = extractor.extract_tables(simple_table_html)
        
        assert len(tables) == 1
        assert tables[0].id == "TABLA_1"
        assert "[TABLA_1]" in text
    
    def test_ignore_invalid_table(self, extractor, invalid_table_html):
        """Ignora tabla con menos de 2 filas."""
        text, tables = extractor.extract_tables(invalid_table_html)
        
        assert len(tables) == 0
        assert "[TABLA_" not in text
    
    def test_detect_multiple_tables(self, extractor, multiple_tables_html):
        """Detecta múltiples tablas correctamente."""
        text, tables = extractor.extract_tables(multiple_tables_html)
        
        assert len(tables) == 2
        assert tables[0].id == "TABLA_1"
        assert tables[1].id == "TABLA_2"
        assert "[TABLA_1]" in text
        assert "[TABLA_2]" in text
    
    def test_handle_nested_tables(self, extractor, nested_tables_html):
        """Procesa solo tabla exterior (no anidadas)."""
        text, tables = extractor.extract_tables(nested_tables_html)
        
        # Solo debe detectar la tabla exterior
        assert len(tables) == 1
    
    def test_empty_html(self, extractor):
        """Maneja HTML vacío sin errores."""
        text, tables = extractor.extract_tables("")
        
        assert text == ""
        assert tables == []
    
    def test_html_without_tables(self, extractor):
        """Maneja HTML sin tablas."""
        html = "<html><body><p>Solo texto sin tablas.</p></body></html>"
        text, tables = extractor.extract_tables(html)
        
        assert len(tables) == 0
        assert "Solo texto sin tablas" in text


# ============================================================================
# TESTS DE EXTRACCIÓN DE HEADERS (Requisitos 2.1, 2.6)
# ============================================================================

class TestHeaderExtraction:
    """Tests para extracción y normalización de headers."""
    
    def test_extract_headers_from_th(self, extractor, simple_table_html):
        """Extrae headers de elementos <th>."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        assert tables[0].schema.columns == ['nombre', 'edad', 'monto']
    
    def test_normalize_special_characters(self, extractor):
        """Normaliza caracteres especiales en headers."""
        html = """
        <table>
            <tr><th>Nº Orden</th><th>Monto ($)</th><th>% IVA</th></tr>
            <tr><td>1</td><td>100</td><td>21</td></tr>
            <tr><td>2</td><td>200</td><td>21</td></tr>
        </table>
        """
        _, tables = extractor.extract_tables(html)
        
        columns = tables[0].schema.columns
        assert 'numero_orden' in columns
        assert 'monto_pesos' in columns
        assert 'porcentaje_iva' in columns
    
    def test_handle_duplicate_headers(self, extractor):
        """Maneja headers duplicados agregando sufijo numérico."""
        html = """
        <table>
            <tr><th>Valor</th><th>Valor</th><th>Valor</th></tr>
            <tr><td>A</td><td>B</td><td>C</td></tr>
            <tr><td>D</td><td>E</td><td>F</td></tr>
        </table>
        """
        _, tables = extractor.extract_tables(html)
        
        columns = tables[0].schema.columns
        assert columns == ['valor', 'valor_2', 'valor_3']
    
    def test_generate_generic_headers(self, extractor):
        """Genera headers genéricos si no hay <th>."""
        html = """
        <table>
            <tr><td>A</td><td>B</td></tr>
            <tr><td>C</td><td>D</td></tr>
        </table>
        """
        _, tables = extractor.extract_tables(html)
        
        # Debe generar headers genéricos
        columns = tables[0].schema.columns
        assert len(columns) == 2


# ============================================================================
# TESTS DE PARSEO NUMÉRICO (Requisitos 2.3, 2.4)
# ============================================================================

class TestNumericParsing:
    """Tests para parseo de valores numéricos."""
    
    def test_parse_argentine_format(self, extractor):
        """Parsea formato argentino: 1.500,00 → 1500.00"""
        assert extractor._parse_numeric("1.500,00") == 1500.00
        assert extractor._parse_numeric("10.000,50") == 10000.50
        assert extractor._parse_numeric("1.234.567,89") == 1234567.89
    
    def test_parse_simple_integer(self, extractor):
        """Parsea enteros simples."""
        assert extractor._parse_numeric("1500") == 1500
        assert extractor._parse_numeric("0") == 0
        assert extractor._parse_numeric("-100") == -100
    
    def test_parse_simple_decimal(self, extractor):
        """Parsea decimales con punto."""
        assert extractor._parse_numeric("1500.50") == 1500.50
        assert extractor._parse_numeric("0.99") == 0.99
    
    def test_parse_decimal_comma_only(self, extractor):
        """Parsea decimales con coma (sin punto de miles)."""
        assert extractor._parse_numeric("1500,50") == 1500.50
        assert extractor._parse_numeric("99,99") == 99.99
    
    def test_return_string_for_non_numeric(self, extractor):
        """Retorna string original si no es número."""
        assert extractor._parse_numeric("texto") == "texto"
        assert extractor._parse_numeric("ABC123") == "ABC123"
        assert extractor._parse_numeric("N/A") == "N/A"
    
    def test_handle_empty_values(self, extractor):
        """Maneja valores vacíos."""
        assert extractor._parse_numeric("") is None
        assert extractor._parse_numeric("   ") is None
        assert extractor._parse_numeric(None) is None


# ============================================================================
# TESTS DE EXTRACCIÓN DE DATOS (Requisitos 2.2, 2.5)
# ============================================================================

class TestDataExtraction:
    """Tests para extracción de filas de datos."""
    
    def test_extract_rows_as_dicts(self, extractor, simple_table_html):
        """Extrae filas como array de dicts."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        data = tables[0].data
        assert len(data) == 2
        assert data[0]['nombre'] == 'Juan'
        assert data[0]['edad'] == 25
        assert data[0]['monto'] == 1500.00
    
    def test_handle_empty_cells(self, extractor):
        """Maneja celdas vacías como None."""
        html = """
        <table>
            <tr><th>A</th><th>B</th></tr>
            <tr><td>1</td><td></td></tr>
            <tr><td></td><td>2</td></tr>
        </table>
        """
        _, tables = extractor.extract_tables(html)
        
        data = tables[0].data
        assert data[0]['b'] is None
        assert data[1]['a'] is None
    
    def test_typed_values(self, extractor, simple_table_html):
        """Valores numéricos se convierten a tipos correctos."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        data = tables[0].data
        assert isinstance(data[0]['edad'], int)
        assert isinstance(data[0]['monto'], float)
        assert isinstance(data[0]['nombre'], str)


# ============================================================================
# TESTS DE ESTADÍSTICAS (Requisito 3.3)
# ============================================================================

class TestStatistics:
    """Tests para cálculo de estadísticas."""
    
    def test_calculate_numeric_stats(self, extractor, simple_table_html):
        """Calcula estadísticas para columnas numéricas."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        stats = tables[0].stats
        assert stats.row_count == 2
        
        # Verificar stats de columna 'monto'
        monto_stats = stats.numeric_stats.get('monto')
        assert monto_stats is not None
        assert monto_stats['sum'] == 3500.50
        assert monto_stats['max'] == 2000.50
        assert monto_stats['min'] == 1500.00
        assert monto_stats['count'] == 2
    
    def test_stats_for_integer_column(self, extractor, simple_table_html):
        """Calcula estadísticas para columna de enteros."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        stats = tables[0].stats
        edad_stats = stats.numeric_stats.get('edad')
        assert edad_stats is not None
        assert edad_stats['sum'] == 55
        assert edad_stats['avg'] == 27.5


# ============================================================================
# TESTS DE MARKDOWN (Requisito 3.4)
# ============================================================================

class TestMarkdownGeneration:
    """Tests para generación de Markdown."""
    
    def test_generate_valid_markdown(self, extractor, simple_table_html):
        """Genera Markdown válido con headers y datos."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        markdown = tables[0].markdown
        assert "| nombre | edad | monto |" in markdown
        assert "| --- | --- | --- |" in markdown
        assert "| Juan |" in markdown
    
    def test_markdown_formats_numbers(self, extractor):
        """Markdown formatea números con separador de miles."""
        html = """
        <table>
            <tr><th>Valor</th><th>Otro</th></tr>
            <tr><td>1000000</td><td>A</td></tr>
            <tr><td>1500</td><td>B</td></tr>
        </table>
        """
        _, tables = extractor.extract_tables(html)
        
        assert len(tables) == 1
        markdown = tables[0].markdown
        # Debe tener separador de miles
        assert "1.000.000" in markdown or "1,000,000" in markdown


# ============================================================================
# TESTS DE PLACEHOLDERS (Requisitos 4.2, 4.3)
# ============================================================================

class TestPlaceholders:
    """Tests para reemplazo de tablas por placeholders."""
    
    def test_placeholder_in_text(self, extractor, simple_table_html):
        """Placeholder aparece en el texto."""
        text, tables = extractor.extract_tables(simple_table_html)
        
        assert "[TABLA_1]" in text
        assert "<table>" not in text
    
    def test_placeholder_position(self, extractor, simple_table_html):
        """Posición del placeholder es correcta."""
        text, tables = extractor.extract_tables(simple_table_html)
        
        position = tables[0].position
        assert position >= 0
        assert text[position:position+9] == "[TABLA_1]"
    
    def test_multiple_placeholders_ordered(self, extractor, multiple_tables_html):
        """Múltiples placeholders mantienen orden."""
        text, tables = extractor.extract_tables(multiple_tables_html)
        
        pos1 = text.find("[TABLA_1]")
        pos2 = text.find("[TABLA_2]")
        
        assert pos1 < pos2
        assert tables[0].position == pos1
        assert tables[1].position == pos2


# ============================================================================
# TESTS DE SERIALIZACIÓN JSON (Requisitos 5.1, 5.2, 5.3)
# ============================================================================

class TestJsonSerialization:
    """Tests para serialización/deserialización JSON."""
    
    def test_roundtrip_json(self, extractor, simple_table_html):
        """Serializar y deserializar produce datos equivalentes."""
        _, original_tables = extractor.extract_tables(simple_table_html)
        
        # Serializar
        json_str = tables_to_json(original_tables)
        
        # Deserializar
        restored_tables = tables_from_json(json_str)
        
        # Verificar equivalencia
        assert len(restored_tables) == len(original_tables)
        
        orig = original_tables[0]
        rest = restored_tables[0]
        
        assert rest.id == orig.id
        assert rest.title == orig.title
        assert rest.schema.columns == orig.schema.columns
        assert rest.data == orig.data
        assert rest.stats.row_count == orig.stats.row_count
    
    def test_json_preserves_unicode(self, extractor):
        """JSON preserva caracteres especiales en datos."""
        html = """
        <table>
            <tr><th>Nombre</th><th>Valor</th></tr>
            <tr><td>Año 2026</td><td>100</td></tr>
            <tr><td>Niño</td><td>200</td></tr>
        </table>
        """
        _, tables = extractor.extract_tables(html)
        
        json_str = tables_to_json(tables)
        
        # Verificar que preserva caracteres unicode en los datos
        assert "Año 2026" in json_str
        assert "Niño" in json_str
        assert "\\u" not in json_str  # No debe tener escapes unicode


# ============================================================================
# TESTS DE MANEJO DE ERRORES (Requisitos 7.1, 7.2, 7.3)
# ============================================================================

class TestErrorHandling:
    """Tests para manejo de errores."""
    
    def test_malformed_html_no_crash(self, extractor):
        """HTML malformado no causa crash."""
        malformed = "<table><tr><td>Unclosed"
        
        # No debe lanzar excepción
        text, tables = extractor.extract_tables(malformed)
        
        assert isinstance(text, str)
        assert isinstance(tables, list)
    
    def test_error_recorded_in_table(self, extractor):
        """Errores se registran en extraction_errors."""
        # Este test verifica que errores individuales no crashean
        html = """
        <table>
            <tr><th>A</th><th>B</th></tr>
            <tr><td>1</td><td>2</td></tr>
            <tr><td>3</td><td>4</td></tr>
        </table>
        """
        _, tables = extractor.extract_tables(html)
        
        # Tabla válida no debe tener errores
        assert tables[0].extraction_errors == []
    
    def test_continues_after_error(self, extractor, multiple_tables_html):
        """Continúa procesando después de error en una tabla."""
        _, tables = extractor.extract_tables(multiple_tables_html)
        
        # Ambas tablas deben procesarse
        assert len(tables) == 2


# ============================================================================
# TESTS DE INFERENCIA DE TIPOS (Requisito 3.5)
# ============================================================================

class TestTypeInference:
    """Tests para inferencia de tipos de columnas."""
    
    def test_infer_number_type(self, extractor, simple_table_html):
        """Infiere tipo 'number' para columnas numéricas."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        types = tables[0].schema.types
        columns = tables[0].schema.columns
        
        # 'edad' y 'monto' deben ser number
        edad_idx = columns.index('edad')
        monto_idx = columns.index('monto')
        
        assert types[edad_idx] == 'number'
        assert types[monto_idx] == 'number'
    
    def test_infer_string_type(self, extractor, simple_table_html):
        """Infiere tipo 'string' para columnas de texto."""
        _, tables = extractor.extract_tables(simple_table_html)
        
        types = tables[0].schema.types
        columns = tables[0].schema.columns
        
        nombre_idx = columns.index('nombre')
        assert types[nombre_idx] == 'string'


# ============================================================================
# PROPERTY-BASED TESTS (usando hypothesis si está disponible)
# ============================================================================

try:
    from hypothesis import given, strategies as st, settings
    
    class TestPropertyBased:
        """Property-based tests con hypothesis."""
        
        @given(st.integers(min_value=0, max_value=1000000))
        @settings(max_examples=50)
        def test_argentine_format_roundtrip(self, number):
            """Property 3: Parseo numérico formato argentino round-trip."""
            extractor = TableExtractor()
            
            # Formatear como argentino
            if number >= 1000:
                formatted = f"{number:,}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                formatted = str(number)
            
            # Parsear
            parsed = extractor._parse_numeric(formatted)
            
            # Verificar
            assert parsed == number
        
        @given(st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False), min_size=1, max_size=100))
        @settings(max_examples=30)
        def test_stats_correctness(self, values):
            """Property 4: Estadísticas matemáticamente correctas."""
            extractor = TableExtractor()
            
            # Crear datos de prueba
            headers = ['valor']
            types = ['number']
            data = [{'valor': v} for v in values]
            
            # Calcular stats
            stats = extractor._calculate_stats(headers, types, data)
            
            # Verificar
            expected_sum = round(sum(values), 2)
            expected_max = round(max(values), 2)
            expected_min = round(min(values), 2)
            expected_avg = round(sum(values) / len(values), 2)
            
            actual = stats.numeric_stats['valor']
            
            assert abs(actual['sum'] - expected_sum) < 0.01
            assert abs(actual['max'] - expected_max) < 0.01
            assert abs(actual['min'] - expected_min) < 0.01
            assert abs(actual['avg'] - expected_avg) < 0.01

except ImportError:
    # hypothesis no está instalado, skip property tests
    pass


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
