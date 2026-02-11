#!/usr/bin/env python3
"""
extractors/glm_table_parser.py

Parser del formato específico de GLM-OCR para tablas financieras.

GLM-OCR devuelve tablas en formato propietario con guiones (-) como separadores,
no en formato Markdown estándar. Este parser convierte ese formato a CSV y Markdown.

El formato de GLM-OCR:
- CUENTA DESCRIPCION SALDO INICIAL MOVIMIENTOS SALDO FINAL VARIACIONES
- DEBE HABER DEBE HABER DEBE HABER DEBE HABER
- 111100000 Caja 4.292.802.582,81 4.288.152.432,33 4.650.150,48 4.650.150,48

@version 1.0.0
@created 2026-02-03
"""

import csv
import io
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class TableRow:
    """Fila de tabla parseada de GLM-OCR."""
    cuenta: str
    descripcion: str
    saldo_inicial_debe: str = ""
    saldo_inicial_haber: str = ""
    movimientos_debe: str = ""
    movimientos_haber: str = ""
    saldo_final_debe: str = ""
    saldo_final_haber: str = ""
    variaciones_debe: str = ""
    variaciones_haber: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convierte la fila a diccionario."""
        return {
            "CUENTA": self.cuenta,
            "DESCRIPCION": self.descripcion,
            "SALDO_INICIAL_DEBE": self.saldo_inicial_debe,
            "SALDO_INICIAL_HABER": self.saldo_inicial_haber,
            "MOVIMIENTOS_DEBE": self.movimientos_debe,
            "MOVIMIENTOS_HABER": self.movimientos_haber,
            "SALDO_FINAL_DEBE": self.saldo_final_debe,
            "SALDO_FINAL_HABER": self.saldo_final_haber,
            "VARIACIONES_DEBE": self.variaciones_debe,
            "VARIACIONES_HABER": self.variaciones_haber,
        }

    def has_variations(self) -> bool:
        """Verifica si la fila tiene datos de variaciones."""
        return bool(self.variaciones_debe or self.variaciones_haber)


@dataclass
class ParseResult:
    """Resultado del parsing de una tabla GLM-OCR."""
    rows: List[TableRow] = field(default_factory=list)
    total_rows: int = 0
    rows_with_variations: int = 0
    headers_detected: bool = False
    parse_errors: List[str] = field(default_factory=list)

    def add_row(self, row: TableRow) -> None:
        """Agrega una fila al resultado."""
        self.rows.append(row)
        self.total_rows += 1
        if row.has_variations():
            self.rows_with_variations += 1


class GLMTableParser:
    """
    Parser del formato específico de GLM-OCR.

    El formato usa guiones (-) como separadores y espacios para delimitar columnas.
    Las columnas son separadas por múltiples espacios, no por comas o pipes.

    IMPORTANTE: GLM-OCR usa un formato "sparse" donde los valores vacíos se OMITEN.
    Esto significa que una fila puede tener entre 2 y 10 valores dependiendo de
    cuántas columnas tienen datos.

    Columnas esperadas (10):
    1. CUENTA (código de 9 dígitos)
    2. DESCRIPCION
    3. SALDO INICIAL DEBE
    4. SALDO INICIAL HABER
    5. MOVIMIENTOS DEBE
    6. MOVIMIENTOS HABER
    7. SALDO FINAL DEBE
    8. SALDO FINAL HABER
    9. VARIACIONES DEBE
    10. VARIACIONES HABER
    """

    # Encabezados que indican el inicio de una tabla
    HEADER_PATTERNS = [
        re.compile(r'CUENTA.*DESCRIPCION.*SALDO INICIAL.*MOVIMIENTOS.*SALDO FINAL.*VARIACIONES', re.IGNORECASE),
        re.compile(r'CUENTA.*DESCRIPCION.*SALDO.*INICIAL.*MOVIMIENTOS.*SALDO.*FINAL.*VARIACIONES', re.IGNORECASE),
    ]

    # Sub-encabezados con DEBE/HABER
    SUBHEADER_PATTERN = re.compile(r'^-?\s*DEBE\s+HABER\s+DEBE\s+HABER\s+DEBE\s+HABER\s+DEBE\s+HABER\s*$', re.IGNORECASE)

    # Patrón para detectar líneas de datos GLM-OCR (enfoque flexible)
    # Formato: - [CUENTA] [DESCRIPCION] [valores numéricos...]
    # Los valores numéricos pueden ser de 0 a 8, dependiendo de cuántos están presentes
    DATA_PATTERN_FLEX = re.compile(
        r'^-\s+'                         # Guión inicial
        r'(\d{6,9}|TOTALES)\s+'          # 1. CUENTA (6-9 dígitos) o TOTALES
        r'(.+?)$'                       # 2. El resto de la línea (DESCRIPCION + valores)
    )

    # Patrón para extraer todos los valores numéricos de una línea
    NUMERIC_PATTERN = re.compile(r'[\d\.,]+')

    # Palabras clave que indican fin de tabla
    TABLE_END_MARKERS = [
        '---',
        '====',
    ]

    def __init__(self, strict: bool = False):
        """
        Args:
            strict: Si True, solo parsea líneas que coinciden exactamente con el patrón
        """
        self.strict = strict
        self._in_table = False
        self._current_headers = []

    def parse(self, content: str) -> ParseResult:
        """
        Parsea contenido GLM-OCR y retorna lista de filas.

        Args:
            content: Contenido raw de GLM-OCR

        Returns:
            ParseResult con las filas parseadas y metadata
        """
        result = ParseResult()
        self._in_table = False

        for line in content.split('\n'):
            line = line.strip()

            # Detectar encabezado
            if self._is_header(line):
                self._in_table = True
                result.headers_detected = True
                continue

            # Detectar sub-encabezado DEBE/HABER
            if self.SUBHEADER_PATTERN.match(line):
                continue

            # Detectar fin de tabla
            if self._is_table_end(line):
                self._in_table = False
                continue

            # Parsear línea de datos
            if self._in_table or (not self._in_table and self._looks_like_data(line)):
                row = self._parse_line(line)
                if row:
                    result.add_row(row)

        return result

    def _is_header(self, line: str) -> bool:
        """Verifica si la línea es un encabezado de tabla."""
        for pattern in self.HEADER_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def _is_table_end(self, line: str) -> bool:
        """
        Verifica si la línea marca el fin de una tabla.

        Nota: TOTALES ya NO marca el fin porque puede tener valores útiles.
        """
        return any(marker in line for marker in self.TABLE_END_MARKERS)

    def _looks_like_data(self, line: str) -> bool:
        """Verifica si la línea parece ser datos de tabla."""
        return line.startswith('- ') or bool(re.match(r'^\d{6,9}\s', line))

    def _parse_line(self, line: str) -> Optional[TableRow]:
        """
        Parsea una línea de datos y retorna un TableRow.

        El formato de GLM-OCR es "sparse": los valores vacíos se omiten.
        Esto significa que我们需要 inferir qué columna representa cada valor
        basándonos en la posición y el número de valores encontrados.

        Args:
            line: Línea de texto con datos

        Returns:
            TableRow o None si no se pudo parsear
        """
        match = self.DATA_PATTERN_FLEX.match(line)
        if not match:
            return None

        cuenta = match.group(1)
        rest = match.group(2).strip()

        # Extraer todos los valores numéricos de la línea
        numeric_values = self.NUMERIC_PATTERN.findall(rest)

        # Extraer la descripción (todo lo que no es numérico al inicio)
        # La descripción termina cuando encontramos el primer número
        desc_parts = []
        for part in rest.split():
            if self.NUMERIC_PATTERN.match(part):
                break
            desc_parts.append(part)

        descripcion = ' '.join(desc_parts).strip()

        # Asignar valores numéricos a columnas según el número de valores
        # El formato es: SI_DEBE, SI_HABER, MOV_DEBE, MOV_HABER, SF_DEBE, SF_HABER, VAR_DEBE, VAR_HABER
        # Si hay menos de 8 valores, algunos campos estarán vacíos

        defaults = {
            "saldo_inicial_debe": "",
            "saldo_inicial_haber": "",
            "movimientos_debe": "",
            "movimientos_haber": "",
            "saldo_final_debe": "",
            "saldo_final_haber": "",
            "variaciones_debe": "",
            "variaciones_haber": "",
        }

        if len(numeric_values) >= 8:
            # Todos los valores presentes
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber=numeric_values[1],
                movimientos_debe=numeric_values[2],
                movimientos_haber=numeric_values[3],
                saldo_final_debe=numeric_values[4],
                saldo_final_haber=numeric_values[5],
                variaciones_debe=numeric_values[6],
                variaciones_haber=numeric_values[7],
            )
        elif len(numeric_values) == 7:
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber=numeric_values[1],
                movimientos_debe=numeric_values[2],
                movimientos_haber=numeric_values[3],
                saldo_final_debe=numeric_values[4],
                saldo_final_haber=numeric_values[5],
                variaciones_debe=numeric_values[6],
                variaciones_haber="",
            )
        elif len(numeric_values) == 6:
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber=numeric_values[1],
                movimientos_debe=numeric_values[2],
                movimientos_haber=numeric_values[3],
                saldo_final_debe=numeric_values[4],
                saldo_final_haber=numeric_values[5],
                variaciones_debe="",
                variaciones_haber="",
            )
        elif len(numeric_values) == 5:
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber=numeric_values[1],
                movimientos_debe=numeric_values[2],
                movimientos_haber=numeric_values[3],
                saldo_final_debe=numeric_values[4],
                saldo_final_haber="",
                variaciones_debe="",
                variaciones_haber="",
            )
        elif len(numeric_values) == 4:
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber=numeric_values[1],
                movimientos_debe=numeric_values[2],
                movimientos_haber=numeric_values[3],
                saldo_final_debe="",
                saldo_final_haber="",
                variaciones_debe="",
                variaciones_haber="",
            )
        elif len(numeric_values) == 3:
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber=numeric_values[1],
                movimientos_debe=numeric_values[2],
                movimientos_haber="",
                saldo_final_debe="",
                saldo_final_haber="",
                variaciones_debe="",
                variaciones_haber="",
            )
        elif len(numeric_values) == 2:
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber=numeric_values[1],
                movimientos_debe="",
                movimientos_haber="",
                saldo_final_debe="",
                saldo_final_haber="",
                variaciones_debe="",
                variaciones_haber="",
            )
        elif len(numeric_values) == 1:
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
                saldo_inicial_debe=numeric_values[0],
                saldo_inicial_haber="",
                movimientos_debe="",
                movimientos_haber="",
                saldo_final_debe="",
                saldo_final_haber="",
                variaciones_debe="",
                variaciones_haber="",
            )
        else:
            # Sin valores numéricos, solo cuenta y descripción
            return TableRow(
                cuenta=cuenta,
                descripcion=descripcion,
            )

    def to_csv(self, rows: List[TableRow]) -> str:
        """
        Convierte filas parseadas a CSV.

        Args:
            rows: Lista de filas parseadas

        Returns:
            String en formato CSV
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "CUENTA", "DESCRIPCION",
            "SALDO_INICIAL_DEBE", "SALDO_INICIAL_HABER",
            "MOVIMIENTOS_DEBE", "MOVIMIENTOS_HABER",
            "SALDO_FINAL_DEBE", "SALDO_FINAL_HABER",
            "VARIACIONES_DEBE", "VARIACIONES_HABER"
        ])

        # Data
        for row in rows:
            writer.writerow([
                row.cuenta, row.descripcion,
                row.saldo_inicial_debe, row.saldo_inicial_haber,
                row.movimientos_debe, row.movimientos_haber,
                row.saldo_final_debe, row.saldo_final_haber,
                row.variaciones_debe, row.variaciones_haber,
            ])

        return output.getvalue()

    def to_markdown(self, rows: List[TableRow]) -> str:
        """
        Convierte filas parseadas a Markdown tabla.

        Args:
            rows: Lista de filas parseadas

        Returns:
            String en formato Markdown tabla
        """
        if not rows:
            return ""

        header = ("| CUENTA | DESCRIPCION | SALDO INICIAL DEBE | SALDO INICIAL HABER | "
                  "MOVIMIENTOS DEBE | MOVIMIENTOS HABER | SALDO FINAL DEBE | "
                  "SALDO FINAL HABER | VARIACIONES DEBE | VARIACIONES HABER |")

        separator = ("|--------|-------------|---------------------|----------------------|"
                     "------------------|-------------------|------------------|-------------------|"
                     "------------------|-------------------|")

        lines = [header, separator]

        for row in rows:
            line = (f"| {row.cuenta} | {row.descripcion} | {row.saldo_inicial_debe} | "
                   f"{row.saldo_inicial_haber} | {row.movimientos_debe} | {row.movimientos_haber} | "
                   f"{row.saldo_final_debe} | {row.saldo_final_haber} | {row.variaciones_debe} | "
                   f"{row.variaciones_haber} |")
            lines.append(line)

        return "\n".join(lines)

    def to_dict_list(self, rows: List[TableRow]) -> List[Dict[str, str]]:
        """
        Convierte filas parseadas a lista de diccionarios.

        Útil para exportar a JSON.
        """
        return [row.to_dict() for row in rows]


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def parse_glm_raw_to_csv(raw_content: str) -> str:
    """
    Convierte contenido RAW de GLM-OCR a CSV.

    Args:
        raw_content: Contenido raw devuelto por GLM-OCR

    Returns:
        String en formato CSV
    """
    parser = GLMTableParser()
    result = parser.parse(raw_content)
    return parser.to_csv(result.rows)


def parse_glm_raw_to_markdown(raw_content: str) -> str:
    """
    Convierte contenido RAW de GLM-OCR a Markdown.

    Args:
        raw_content: Contenido raw devuelto por GLM-OCR

    Returns:
        String en formato Markdown tabla
    """
    parser = GLMTableParser()
    result = parser.parse(raw_content)
    return parser.to_markdown(result.rows)


def parse_glm_raw(raw_content: str) -> ParseResult:
    """
    Parsea contenido RAW de GLM-OCR.

    Args:
        raw_content: Contenido raw devuelto por GLM-OCR

    Returns:
        ParseResult con filas y metadata
    """
    parser = GLMTableParser()
    return parser.parse(raw_content)


def has_variations_column(raw_content: str) -> bool:
    """
    Verifica si el contenido tiene la columna VARIACIONES.

    Útil para decidir si usar GLM-OCR o Gemini en el ensemble.
    """
    return "VARIACIONES" in raw_content.upper()


def count_columns_in_markdown(markdown_content: str) -> int:
    """
    Cuenta el número de columnas en una tabla Markdown.

    Útil para detectar columnas faltantes.
    """
    for line in markdown_content.split('\n'):
        if '|' in line and ('CUENTA' in line or 'DESCRIPCION' in line):
            return line.count('|') - 1
    return 0


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test con datos reales
    test_data = """
    - CUENTA DESCRIPCION SALDO INICIAL MOVIMIENTOS SALDO FINAL VARIACIONES
    - DEBE HABER DEBE HABER DEBE HABER DEBE HABER
    - 111100000 Caja 4.292.802.582,81 4.288.152.432,33 4.650.150,48 4.650.150,48
    - 111210103 Bco. Pcia. Bs.As. - Cta. Cte. N°10098/4-Hospital 9.897,40 251.024,89 76.000,00 184.922,29 175.024,89
    """

    print("=== GLM Table Parser Test ===\n")

    # Parsear
    result = parse_glm_raw(test_data)

    print(f"Filas parseadas: {result.total_rows}")
    print(f"Filas con VARIACIONES: {result.rows_with_variations}")
    print(f"Headers detectados: {result.headers_detected}")

    # Generar CSV
    print("\n=== CSV ===")
    csv_output = parse_glm_raw_to_csv(test_data)
    print(csv_output[:500])

    # Generar Markdown
    print("\n=== Markdown ===")
    md_output = parse_glm_raw_to_markdown(test_data)
    print(md_output[:500])

    # Verificar VARIACIONES
    print("\n=== Verificaciones ===")
    print(f"¿Tiene VARIACIONES? {has_variations_column(test_data)}")
    print(f"Columnas en MD: {count_columns_in_markdown(md_output)}")
