#!/usr/bin/env python3
"""
Table Extractor - Módulo de Extracción de Datos Tabulares
Extrae tablas HTML preservando estructura semántica para queries computacionales en RAG.

Fecha: 2026-01-08
Versión: 1.0.0
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup, Tag, NavigableString

# ============================================================================
# DATACLASSES - Estructuras de datos inmutables
# ============================================================================

@dataclass
class TableSchema:
    """Schema de una tabla con nombres de columnas y tipos inferidos."""
    columns: List[str]
    types: List[str]  # 'string', 'number', 'date'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TableStats:
    """Estadísticas calculadas para columnas numéricas."""
    row_count: int
    numeric_stats: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # Formato: {"columna": {"sum": X, "max": Y, "min": Z, "avg": W, "count": N}}
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredTable:
    """Representación estructurada completa de una tabla extraída."""
    id: str                          # "TABLA_1", "TABLA_2", etc.
    title: str                       # Título descriptivo generado
    context: str                     # Texto circundante (antes/después)
    description: str                 # Descripción en lenguaje natural
    position: int                    # Posición del placeholder en text_content
    schema: TableSchema              # Schema con columnas y tipos
    data: List[Dict[str, Any]]       # Array de filas como dicts
    stats: TableStats                # Estadísticas calculadas
    markdown: str                    # Representación Markdown
    extraction_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización JSON."""
        return {
            "id": self.id,
            "title": self.title,
            "context": self.context,
            "description": self.description,
            "position": self.position,
            "schema": self.schema.to_dict(),
            "data": self.data,
            "stats": self.stats.to_dict(),
            "markdown": self.markdown,
            "extraction_errors": self.extraction_errors
        }


# ============================================================================
# CLASE PRINCIPAL - TableExtractor
# ============================================================================

class TableExtractor:
    """
    Extrae y estructura tablas HTML preservando semántica columna-fila.
    
    Características:
    - Detecta tablas válidas (≥2 filas, ≥2 columnas)
    - Extrae contexto circundante para generar títulos
    - Parsea valores numéricos (formato argentino: 1.500,00)
    - Calcula estadísticas para columnas numéricas
    - Genera representación Markdown para visualización
    
    Uso:
        extractor = TableExtractor()
        text_content, tables = extractor.extract_tables(html)
    """
    
    # Configuración por defecto
    MIN_ROWS = 2
    MIN_COLS = 2
    DEFAULT_CONTEXT_CHARS = 500
    
    def __init__(self, context_chars: int = DEFAULT_CONTEXT_CHARS):
        """
        Inicializa el extractor de tablas.
        
        Args:
            context_chars: Máximo de caracteres a extraer antes/después de cada tabla
        """
        self.context_chars = context_chars
    
    # ========================================================================
    # MÉTODO PRINCIPAL
    # ========================================================================
    
    def extract_tables(self, html: str) -> Tuple[str, List[StructuredTable]]:
        """
        Extrae tablas del HTML y retorna texto con placeholders + tablas estructuradas.
        
        Args:
            html: Contenido HTML a procesar
            
        Returns:
            Tuple[str, List[StructuredTable]]: 
                - Texto con tablas reemplazadas por [TABLA_N]
                - Lista de tablas estructuradas
        """
        if not html or len(html) < 50:
            return html or "", []
        
        tables: List[StructuredTable] = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            table_elements = self._detect_tables(soup)
            
            if not table_elements:
                # Sin tablas válidas, retornar texto limpio
                text_content = self._extract_text_content(soup)
                return text_content, []
            
            # Procesar cada tabla
            for idx, table_elem in enumerate(table_elements):
                table_id = f"TABLA_{idx + 1}"
                
                try:
                    structured = self._process_single_table(table_elem, table_id, idx)
                    tables.append(structured)
                except Exception as e:
                    # Registrar error pero continuar con siguiente tabla
                    error_msg = f"Error procesando tabla {idx + 1}: {str(e)}"
                    error_table = self._create_error_table(table_id, error_msg)
                    tables.append(error_table)
            
            # Reemplazar tablas con placeholders y calcular posiciones
            text_content = self._replace_tables_with_placeholders(soup, table_elements, tables)
            
            return text_content, tables
            
        except Exception as e:
            # Fallback: retornar texto plano sin tablas
            try:
                soup = BeautifulSoup(html, 'lxml')
                text_content = self._extract_text_content(soup)
                return text_content, []
            except:
                return html, []
    
    # ========================================================================
    # DETECCIÓN DE TABLAS
    # ========================================================================
    
    def _detect_tables(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Detecta elementos <table> válidos (≥2 filas, ≥2 columnas).
        Maneja tablas anidadas procesando solo la más interna.
        
        Args:
            soup: BeautifulSoup parseado
            
        Returns:
            Lista de elementos Tag de tablas válidas
        """
        all_tables = soup.find_all('table')
        valid_tables: List[Tag] = []
        
        for table in all_tables:
            # Verificar si es tabla anidada (tiene tabla padre)
            parent_table = table.find_parent('table')
            if parent_table:
                # Es tabla anidada, la ignoramos (procesaremos la más interna)
                continue
            
            # Verificar dimensiones mínimas
            rows = table.find_all('tr')
            if len(rows) < self.MIN_ROWS:
                continue
            
            # Contar columnas en la primera fila con contenido
            max_cols = 0
            for row in rows:
                cells = row.find_all(['th', 'td'])
                col_count = sum(int(cell.get('colspan', 1)) for cell in cells)
                max_cols = max(max_cols, col_count)
            
            if max_cols < self.MIN_COLS:
                continue
            
            valid_tables.append(table)
        
        return valid_tables
    
    # ========================================================================
    # EXTRACCIÓN DE CONTEXTO
    # ========================================================================
    
    def _extract_context(self, table: Tag) -> str:
        """
        Extrae texto circundante (antes y después de la tabla).
        
        Args:
            table: Elemento Tag de la tabla
            
        Returns:
            Texto de contexto combinado
        """
        context_parts = []
        
        # Texto anterior
        prev_text = self._get_previous_text(table)
        if prev_text:
            context_parts.append(prev_text[-self.context_chars:])
        
        # Texto posterior
        next_text = self._get_next_text(table)
        if next_text:
            context_parts.append(next_text[:self.context_chars])
        
        return " ".join(context_parts).strip() or "Tabla sin contexto"
    
    def _get_previous_text(self, element: Tag) -> str:
        """Obtiene texto de elementos anteriores."""
        texts = []
        
        for sibling in element.previous_siblings:
            if isinstance(sibling, NavigableString):
                text = str(sibling).strip()
                if text:
                    texts.insert(0, text)
            elif isinstance(sibling, Tag):
                text = sibling.get_text(strip=True)
                if text:
                    texts.insert(0, text)
            
            # Limitar búsqueda
            if len(" ".join(texts)) > self.context_chars * 2:
                break
        
        return " ".join(texts)
    
    def _get_next_text(self, element: Tag) -> str:
        """Obtiene texto de elementos posteriores."""
        texts = []
        
        for sibling in element.next_siblings:
            if isinstance(sibling, NavigableString):
                text = str(sibling).strip()
                if text:
                    texts.append(text)
            elif isinstance(sibling, Tag):
                text = sibling.get_text(strip=True)
                if text:
                    texts.append(text)
            
            # Limitar búsqueda
            if len(" ".join(texts)) > self.context_chars * 2:
                break
        
        return " ".join(texts)
    
    # ========================================================================
    # EXTRACCIÓN DE HEADERS
    # ========================================================================
    
    def _extract_headers(self, table: Tag) -> List[str]:
        """
        Extrae y normaliza headers de la tabla.
        
        Args:
            table: Elemento Tag de la tabla
            
        Returns:
            Lista de headers normalizados a snake_case
        """
        headers = []
        
        # Buscar primera fila con <th>
        thead = table.find('thead')
        if thead:
            header_row = thead.find('tr')
        else:
            # Buscar primera fila con <th> o usar primera <tr>
            first_row_with_th = table.find('tr', recursive=True)
            if first_row_with_th:
                th_cells = first_row_with_th.find_all('th')
                if th_cells:
                    header_row = first_row_with_th
                else:
                    # Usar primera fila como headers
                    header_row = first_row_with_th
            else:
                header_row = None
        
        if header_row:
            cells = header_row.find_all(['th', 'td'])
            for cell in cells:
                header_text = cell.get_text(strip=True)
                normalized = self._normalize_header(header_text)
                
                # Evitar headers duplicados
                if normalized in headers:
                    counter = 2
                    while f"{normalized}_{counter}" in headers:
                        counter += 1
                    normalized = f"{normalized}_{counter}"
                
                headers.append(normalized)
        
        # Fallback: generar headers genéricos
        if not headers:
            rows = table.find_all('tr')
            if rows:
                first_row = rows[0]
                cells = first_row.find_all(['th', 'td'])
                headers = [f"columna_{i+1}" for i in range(len(cells))]
        
        return headers
    
    def _normalize_header(self, header: str) -> str:
        """
        Normaliza header a snake_case.
        
        Args:
            header: Texto del header original
            
        Returns:
            Header normalizado (snake_case, sin caracteres especiales)
        """
        if not header:
            return "sin_nombre"
        
        # Convertir a minúsculas
        normalized = header.lower()
        
        # Reemplazar caracteres especiales comunes
        replacements = {
            'nº': 'numero',
            'n°': 'numero',
            '#': 'numero',
            '$': 'pesos',
            '%': 'porcentaje',
            '€': 'euros',
            'ñ': 'n',
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Reemplazar espacios y caracteres no alfanuméricos por guión bajo
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized.strip())
        
        # Eliminar guiones bajos múltiples
        normalized = re.sub(r'_+', '_', normalized)
        
        # Eliminar guiones bajos al inicio/final
        normalized = normalized.strip('_')
        
        return normalized or "sin_nombre"

    
    # ========================================================================
    # PARSEO DE VALORES NUMÉRICOS
    # ========================================================================
    
    def _parse_numeric(self, value: str) -> Any:
        """
        Parsea valores numéricos, soportando formato argentino (1.500,00).
        
        Args:
            value: String a parsear
            
        Returns:
            int, float, o string original si no es número válido
        """
        # Manejar None y tipos no-string
        if value is None or not isinstance(value, str):
            return value
        
        # Limpiar espacios
        cleaned = value.strip()
        
        # String vacío o solo espacios
        if not cleaned:
            return None
        
        # Detectar si parece un número
        # Patrones válidos: "1500", "1.500", "1500,50", "1.500,50", "-1500", etc.
        numeric_pattern = r'^-?\d{1,3}(?:\.\d{3})*(?:,\d+)?$|^-?\d+(?:,\d+)?$|^-?\d+(?:\.\d+)?$'
        
        if not re.match(numeric_pattern, cleaned):
            return cleaned  # No es número, retornar string original
        
        try:
            # Detectar formato argentino (usa . como separador de miles y , como decimal)
            has_dot = '.' in cleaned
            has_comma = ',' in cleaned
            
            if has_comma and has_dot:
                # Formato argentino: 1.500,00 → 1500.00
                # Remover puntos de miles, reemplazar coma por punto
                cleaned = cleaned.replace('.', '').replace(',', '.')
            elif has_comma and not has_dot:
                # Solo coma: podría ser decimal argentino (1500,50) o miles (1,500)
                # Si hay exactamente 3 dígitos después de la coma, es separador de miles
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
                    # Es separador de miles: 1,500 → 1500
                    cleaned = cleaned.replace(',', '')
                else:
                    # Es decimal: 1500,50 → 1500.50
                    cleaned = cleaned.replace(',', '.')
            # Si solo tiene punto, asumimos formato internacional (1500.50)
            
            # Intentar convertir a número
            if '.' in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
                
        except (ValueError, TypeError):
            return value  # Retornar string original si falla conversión
    
    # ========================================================================
    # EXTRACCIÓN DE FILAS DE DATOS
    # ========================================================================
    
    def _extract_rows(self, table: Tag, headers: List[str]) -> List[Dict[str, Any]]:
        """
        Extrae filas de datos como array de dicts.
        
        Args:
            table: Elemento Tag de la tabla
            headers: Lista de headers normalizados
            
        Returns:
            Lista de diccionarios, cada uno representando una fila
        """
        rows_data: List[Dict[str, Any]] = []
        
        # Encontrar todas las filas
        all_rows = table.find_all('tr')
        
        # Determinar índice de inicio (saltar fila de headers)
        start_idx = 1  # Por defecto, saltar primera fila
        
        # Si hay thead, las filas de datos están en tbody o después del thead
        tbody = table.find('tbody')
        if tbody:
            data_rows = tbody.find_all('tr')
        else:
            # Saltar filas que son headers (contienen <th>)
            data_rows = []
            for row in all_rows:
                # Si la fila tiene <th>, es header
                if row.find('th'):
                    continue
                data_rows.append(row)
            
            # Si no encontramos filas sin <th>, usar todas excepto la primera
            if not data_rows and len(all_rows) > 1:
                data_rows = all_rows[1:]
        
        # Procesar cada fila de datos
        for row in data_rows:
            cells = row.find_all(['td', 'th'])
            
            if not cells:
                continue
            
            row_dict: Dict[str, Any] = {}
            
            for i, cell in enumerate(cells):
                # Obtener header correspondiente
                if i < len(headers):
                    header = headers[i]
                else:
                    header = f"columna_{i + 1}"
                
                # Extraer valor de la celda
                cell_text = cell.get_text(strip=True)
                
                # Parsear valor (intentar convertir a número)
                if cell_text:
                    parsed_value = self._parse_numeric(cell_text)
                else:
                    parsed_value = None
                
                row_dict[header] = parsed_value
            
            # Solo agregar filas con al menos un valor no nulo
            if any(v is not None for v in row_dict.values()):
                rows_data.append(row_dict)
        
        return rows_data
    
    # ========================================================================
    # INFERENCIA DE TIPOS
    # ========================================================================
    
    def _infer_types(self, headers: List[str], data: List[Dict[str, Any]]) -> List[str]:
        """
        Infiere tipos de columnas basado en los datos.
        
        Args:
            headers: Lista de headers
            data: Lista de filas de datos
            
        Returns:
            Lista de tipos ('string', 'number', 'date')
        """
        types = []
        
        for header in headers:
            # Recolectar valores no nulos de esta columna
            values = [row.get(header) for row in data if row.get(header) is not None]
            
            if not values:
                types.append('string')
                continue
            
            # Contar tipos
            numeric_count = sum(1 for v in values if isinstance(v, (int, float)))
            string_count = len(values) - numeric_count
            
            # Si mayoría son números, es columna numérica
            if numeric_count > string_count:
                types.append('number')
            else:
                # Verificar si parece fecha
                date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
                date_count = sum(1 for v in values if isinstance(v, str) and re.match(date_pattern, v))
                
                if date_count > len(values) / 2:
                    types.append('date')
                else:
                    types.append('string')
        
        return types
    
    # ========================================================================
    # CÁLCULO DE ESTADÍSTICAS
    # ========================================================================
    
    def _calculate_stats(self, headers: List[str], types: List[str], 
                         data: List[Dict[str, Any]]) -> TableStats:
        """
        Calcula estadísticas para columnas numéricas.
        
        Args:
            headers: Lista de headers
            types: Lista de tipos de columnas
            data: Lista de filas de datos
            
        Returns:
            TableStats con estadísticas calculadas
        """
        numeric_stats: Dict[str, Dict[str, float]] = {}
        
        for i, (header, col_type) in enumerate(zip(headers, types)):
            if col_type != 'number':
                continue
            
            # Recolectar valores numéricos de esta columna
            values = []
            for row in data:
                val = row.get(header)
                if isinstance(val, (int, float)):
                    values.append(float(val))
            
            if not values:
                continue
            
            # Calcular estadísticas
            numeric_stats[header] = {
                'sum': round(sum(values), 2),
                'max': round(max(values), 2),
                'min': round(min(values), 2),
                'avg': round(sum(values) / len(values), 2),
                'count': len(values)
            }
        
        return TableStats(
            row_count=len(data),
            numeric_stats=numeric_stats
        )
    
    # ========================================================================
    # GENERACIÓN DE MARKDOWN
    # ========================================================================
    
    def _generate_markdown(self, headers: List[str], data: List[Dict[str, Any]]) -> str:
        """
        Genera representación Markdown de la tabla.
        
        Args:
            headers: Lista de headers
            data: Lista de filas de datos
            
        Returns:
            String con tabla en formato Markdown
        """
        if not headers or not data:
            return ""
        
        lines = []
        
        # Header row
        header_line = "| " + " | ".join(headers) + " |"
        lines.append(header_line)
        
        # Separator row
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"
        lines.append(separator)
        
        # Data rows
        for row in data:
            values = []
            for header in headers:
                val = row.get(header, "")
                
                # Formatear números con separador de miles para legibilidad
                if isinstance(val, float):
                    if val == int(val):
                        formatted = f"{int(val):,}".replace(",", ".")
                    else:
                        formatted = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                elif isinstance(val, int):
                    formatted = f"{val:,}".replace(",", ".")
                elif val is None:
                    formatted = "-"
                else:
                    formatted = str(val)
                
                values.append(formatted)
            
            row_line = "| " + " | ".join(values) + " |"
            lines.append(row_line)
        
        return "\n".join(lines)

    
    # ========================================================================
    # GENERACIÓN DE TÍTULO Y DESCRIPCIÓN
    # ========================================================================
    
    def _generate_title(self, context: str, headers: List[str]) -> str:
        """
        Genera título descriptivo basado en contexto y headers.
        
        Args:
            context: Texto circundante de la tabla
            headers: Lista de headers
            
        Returns:
            Título descriptivo
        """
        # Intentar extraer título del contexto
        # Buscar patrones comunes: "Artículo X:", "Anexo X:", "Tabla X:", etc.
        title_patterns = [
            r'(?:Artículo|Art\.?)\s*\d+[°º]?\s*[-:.]?\s*([^.]+)',
            r'(?:Anexo|ANEXO)\s*[IVX\d]+\s*[-:.]?\s*([^.]+)',
            r'(?:Tabla|TABLA)\s*\d*\s*[-:.]?\s*([^.]+)',
            r'(?:Cuadro|CUADRO)\s*\d*\s*[-:.]?\s*([^.]+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                if len(title) > 10 and len(title) < 100:
                    return title[:100]
        
        # Fallback: generar título basado en headers
        if headers:
            # Usar primeros 3 headers significativos
            significant_headers = [h for h in headers[:3] if h != 'sin_nombre' and not h.startswith('columna_')]
            if significant_headers:
                return f"Tabla de {', '.join(significant_headers)}"
        
        return "Tabla de datos"
    
    def _generate_description(self, headers: List[str], types: List[str], 
                              row_count: int) -> str:
        """
        Genera descripción en lenguaje natural de la tabla.
        
        Args:
            headers: Lista de headers
            types: Lista de tipos de columnas
            row_count: Número de filas de datos
            
        Returns:
            Descripción de la tabla
        """
        # Contar columnas por tipo
        numeric_cols = sum(1 for t in types if t == 'number')
        string_cols = sum(1 for t in types if t == 'string')
        
        # Construir descripción
        parts = [f"Tabla con {row_count} filas y {len(headers)} columnas"]
        
        if numeric_cols > 0:
            parts.append(f"({numeric_cols} numéricas)")
        
        # Mencionar columnas principales
        main_headers = [h for h in headers[:3] if h != 'sin_nombre']
        if main_headers:
            parts.append(f"Columnas: {', '.join(main_headers)}")
        
        return ". ".join(parts) + "."
    
    # ========================================================================
    # PROCESAMIENTO DE TABLA INDIVIDUAL
    # ========================================================================
    
    def _process_single_table(self, table_elem: Tag, table_id: str, 
                               idx: int) -> StructuredTable:
        """
        Procesa una tabla individual y retorna estructura completa.
        
        Args:
            table_elem: Elemento Tag de la tabla
            table_id: ID de la tabla ("TABLA_1", etc.)
            idx: Índice de la tabla
            
        Returns:
            StructuredTable con todos los datos extraídos
        """
        errors: List[str] = []
        
        # 1. Extraer contexto
        try:
            context = self._extract_context(table_elem)
        except Exception as e:
            context = "Tabla sin contexto"
            errors.append(f"Error extrayendo contexto: {str(e)}")
        
        # 2. Extraer headers
        try:
            headers = self._extract_headers(table_elem)
        except Exception as e:
            headers = []
            errors.append(f"Error extrayendo headers: {str(e)}")
        
        if not headers:
            # Generar headers genéricos basados en primera fila
            first_row = table_elem.find('tr')
            if first_row:
                cells = first_row.find_all(['th', 'td'])
                headers = [f"columna_{i+1}" for i in range(len(cells))]
        
        # 3. Extraer filas de datos
        try:
            data = self._extract_rows(table_elem, headers)
        except Exception as e:
            data = []
            errors.append(f"Error extrayendo datos: {str(e)}")
        
        # 4. Inferir tipos
        try:
            types = self._infer_types(headers, data)
        except Exception as e:
            types = ['string'] * len(headers)
            errors.append(f"Error infiriendo tipos: {str(e)}")
        
        # 5. Calcular estadísticas
        try:
            stats = self._calculate_stats(headers, types, data)
        except Exception as e:
            stats = TableStats(row_count=len(data))
            errors.append(f"Error calculando estadísticas: {str(e)}")
        
        # 6. Generar Markdown
        try:
            markdown = self._generate_markdown(headers, data)
        except Exception as e:
            markdown = ""
            errors.append(f"Error generando Markdown: {str(e)}")
        
        # 7. Generar título y descripción
        try:
            title = self._generate_title(context, headers)
            description = self._generate_description(headers, types, len(data))
        except Exception as e:
            title = f"Tabla {idx + 1}"
            description = f"Tabla con {len(data)} filas"
            errors.append(f"Error generando título/descripción: {str(e)}")
        
        # 8. Crear schema
        schema = TableSchema(columns=headers, types=types)
        
        return StructuredTable(
            id=table_id,
            title=title,
            context=context,
            description=description,
            position=0,  # Se actualizará después
            schema=schema,
            data=data,
            stats=stats,
            markdown=markdown,
            extraction_errors=errors
        )
    
    def _create_error_table(self, table_id: str, error_msg: str) -> StructuredTable:
        """
        Crea una tabla con error para casos de fallo en extracción.
        
        Args:
            table_id: ID de la tabla
            error_msg: Mensaje de error
            
        Returns:
            StructuredTable con datos mínimos y error registrado
        """
        return StructuredTable(
            id=table_id,
            title="Tabla con error de extracción",
            context="",
            description="No se pudo extraer esta tabla correctamente",
            position=0,
            schema=TableSchema(columns=[], types=[]),
            data=[],
            stats=TableStats(row_count=0),
            markdown="",
            extraction_errors=[error_msg]
        )
    
    # ========================================================================
    # REEMPLAZO DE TABLAS POR PLACEHOLDERS
    # ========================================================================
    
    def _replace_tables_with_placeholders(self, soup: BeautifulSoup, 
                                          table_elements: List[Tag],
                                          tables: List[StructuredTable]) -> str:
        """
        Reemplaza tablas HTML con placeholders [TABLA_N] y calcula posiciones.
        
        Args:
            soup: BeautifulSoup parseado
            table_elements: Lista de elementos Tag de tablas
            tables: Lista de StructuredTable (se actualizan las posiciones)
            
        Returns:
            Texto con placeholders
        """
        # Reemplazar cada tabla con su placeholder
        for i, table_elem in enumerate(table_elements):
            placeholder = f"[TABLA_{i + 1}]"
            table_elem.replace_with(placeholder)
        
        # Extraer texto completo
        text_content = self._extract_text_content(soup)
        
        # Calcular posiciones de cada placeholder
        for i, table in enumerate(tables):
            placeholder = f"[TABLA_{i + 1}]"
            position = text_content.find(placeholder)
            # Actualizar posición en el objeto (dataclass es mutable en sus campos)
            object.__setattr__(table, 'position', position if position >= 0 else 0)
        
        return text_content
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extrae texto limpio del HTML.
        
        Args:
            soup: BeautifulSoup parseado
            
        Returns:
            Texto limpio
        """
        # Remover scripts y estilos
        for element in soup.find_all(['script', 'style', 'noscript']):
            element.decompose()
        
        # Extraer texto
        text = soup.get_text(separator='\n', strip=True)
        
        # Limpiar múltiples saltos de línea
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()


# ============================================================================
# FUNCIONES DE UTILIDAD PARA SERIALIZACIÓN
# ============================================================================

def tables_to_json(tables: List[StructuredTable]) -> str:
    """
    Serializa lista de tablas a JSON.
    
    Args:
        tables: Lista de StructuredTable
        
    Returns:
        String JSON
    """
    return json.dumps(
        [t.to_dict() for t in tables],
        ensure_ascii=False,
        indent=2
    )


def tables_from_json(json_str: str) -> List[StructuredTable]:
    """
    Deserializa JSON a lista de tablas.
    
    Args:
        json_str: String JSON
        
    Returns:
        Lista de StructuredTable
    """
    data = json.loads(json_str)
    tables = []
    
    for item in data:
        schema = TableSchema(
            columns=item['schema']['columns'],
            types=item['schema']['types']
        )
        stats = TableStats(
            row_count=item['stats']['row_count'],
            numeric_stats=item['stats'].get('numeric_stats', {})
        )
        table = StructuredTable(
            id=item['id'],
            title=item['title'],
            context=item['context'],
            description=item['description'],
            position=item['position'],
            schema=schema,
            data=item['data'],
            stats=stats,
            markdown=item['markdown'],
            extraction_errors=item.get('extraction_errors', [])
        )
        tables.append(table)
    
    return tables


# ============================================================================
# PUNTO DE ENTRADA PARA TESTING
# ============================================================================

if __name__ == '__main__':
    # Test básico
    test_html = """
    <html>
    <body>
    <p>Artículo 2: Las tasas se aplicarán según la siguiente escala:</p>
    <table>
        <tr><th>Categoría</th><th>Descripción</th><th>Monto ($)</th></tr>
        <tr><td>A</td><td>Comercio menor</td><td>1.500,00</td></tr>
        <tr><td>B</td><td>Comercio mayor</td><td>3.000,00</td></tr>
        <tr><td>C</td><td>Industria</td><td>5.500,50</td></tr>
    </table>
    <p>Artículo 3: Los montos se actualizarán anualmente.</p>
    </body>
    </html>
    """
    
    extractor = TableExtractor()
    text_content, tables = extractor.extract_tables(test_html)
    
    print("=" * 60)
    print("TEXTO CON PLACEHOLDERS:")
    print("=" * 60)
    print(text_content)
    print()
    
    if tables:
        print("=" * 60)
        print(f"TABLAS EXTRAÍDAS: {len(tables)}")
        print("=" * 60)
        
        for table in tables:
            print(f"\nID: {table.id}")
            print(f"Título: {table.title}")
            print(f"Descripción: {table.description}")
            print(f"Posición: {table.position}")
            print(f"Schema: {table.schema.columns} -> {table.schema.types}")
            print(f"Filas: {table.stats.row_count}")
            print(f"Stats: {table.stats.numeric_stats}")
            print(f"\nMarkdown:\n{table.markdown}")
            print(f"\nDatos: {table.data}")
            
            if table.extraction_errors:
                print(f"\nErrores: {table.extraction_errors}")
