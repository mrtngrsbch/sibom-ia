#!/usr/bin/env python3
"""
balance_header.py

Extractor de cabeceras de balances contables.
Extrae datos de la primera página usando regex patterns.

@version 1.0.0
@created 2026-01-30
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


# ============================================================================
# DATA CLASS
# ============================================================================

@dataclass
class BalanceHeader:
    """Datos extraídos de la cabecera de un balance."""
    institucion: str = ""
    municipalidad: str = ""
    tipo_documento: str = ""
    ejercicio: str = ""
    periodo_inicio: str = ""
    periodo_fin: str = ""
    fecha_generacion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "institucion": self.institucion,
            "municipalidad": self.municipalidad,
            "tipo_documento": self.tipo_documento,
            "ejercicio": self.ejercicio,
            "periodo_inicio": self.periodo_inicio,
            "periodo_fin": self.periodo_fin,
            "fecha_generacion": self.fecha_generacion
        }

    @property
    def has_data(self) -> bool:
        """Retorna True si se extrajo algún dato."""
        return bool(
            self.institucion or self.tipo_documento or self.ejercicio or
            self.periodo_inicio or self.fecha_generacion
        )

    def get_periodo_code(self) -> Optional[str]:
        """
        Calcula el código de periodo (ej: "2020-T3", "2020-S1").

        Returns:
            Código de periodo o None si no se puede determinar
        """
        if not self.periodo_inicio or not self.ejercicio:
            return None

        try:
            fecha_inicio = datetime.strptime(self.periodo_inicio, "%d/%m/%Y")
            mes = fecha_inicio.month

            # Determinar si es trimestre o semestre
            trimestre = (mes - 1) // 3 + 1
            semestre = 1 if mes <= 6 else 2

            # Usar trimestre por defecto
            return f"{self.ejercicio}-T{trimestre}"
        except Exception:
            return None


# ============================================================================
# EXTRACTOR
# ============================================================================

class BalanceHeaderExtractor:
    """
    Extrae cabeceras de balances usando regex.

    Diseñado para patrones consistentes de documentos R.A.F.A.M.
    """

    # Patrones para R.A.F.A.M. (formato consistente)
    PATTERNS = {
        # Institución
        "institucion": re.compile(r'R\.?A\.?F\.?A\.?M\.?', re.IGNORECASE),

        # Ejercicio: "Ejercicio: 2020" o "Ejercicio 2020"
        "ejercicio": re.compile(r'Ejercicio\s*[:]\s*(\d{4})', re.IGNORECASE),

        # Periodo: "Desde el 02/01/2020 hasta el 30/06/2020"
        "periodo_desde": re.compile(r'Desde\s+el\s+(\d{2}/\d{2}/\d{4})', re.IGNORECASE),
        "periodo_hasta": re.compile(r'hasta\s+el\s+(\d{2}/\d{2}/\d{4})', re.IGNORECASE),

        # Alternativa: "Del 01/01/2020 al 31/12/2020"
        "periodo_del": re.compile(r'Del\s+(\d{2}/\d{2}/\d{4})', re.IGNORECASE),
        "periodo_al": re.compile(r'al\s+(\d{2}/\d{2}/\d{4})', re.IGNORECASE),

        # Fecha de generación: "20/07/2020 08:09" o "20/07/2020"
        "fecha_generacion": re.compile(r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})'),
        "fecha_sola": re.compile(r'^(\d{2}/\d{2}/\d{4})\s*$', re.MULTILINE),

        # Tipos de documento
        "tipo_balance_sumas": re.compile(r'BALANCE\s+DE\s+SUMAS\s+y\s+SALDOS', re.IGNORECASE),
        "tipo_balance_tesoreria": re.compile(r'BALANCE\s+DE\s+TESORER[IÍ]A', re.IGNORECASE),
        "tipo_ejecucion_presupuesto": re.compile(r'ESTADO\s+DE\s+EJECUCI[ÓO]N\s+DEL\s+PRESUPUESTO', re.IGNORECASE),
        "tipo_gastos_finalidad": re.compile(r'GASTOS\s+POR\s+FINALIDAD\s+y\s+FUNCI[ÓO]N', re.IGNORECASE),
    }

    def __init__(self, municipality: str = ""):
        """
        Args:
            municipality: Nombre del municipio (opcional)
        """
        self.municipality = municipality

    def extract(self, content: str, municipio: str = "") -> BalanceHeader:
        """
        Extrae datos de la cabecera del contenido extraído.

        Args:
            content: Contenido extraído por Vision API
            municipio: Nombre del municipio (sobrescribe self.municipality)

        Returns:
            BalanceHeader con los datos extraídos
        """
        header = BalanceHeader()

        # Usar municipio proporcionado o el de inicialización
        header.municipalidad = municipio or self.municipality

        # Solo analizar primeros 3000 caracteres (cabecera)
        # Esto evita falsos positivos del contenido del documento
        cabecera_text = content[:3000]

        # Extraer institución
        match = self.PATTERNS["institucion"].search(cabecera_text)
        if match:
            header.institucion = "R.A.F.A.M."

        # Extraer ejercicio
        match = self.PATTERNS["ejercicio"].search(cabecera_text)
        if match:
            header.ejercicio = match.group(1)

        # Extraer periodo (formato "Desde el ... hasta el ...")
        match = self.PATTERNS["periodo_desde"].search(cabecera_text)
        if match:
            header.periodo_inicio = match.group(1)
        else:
            # Intentar formato alternativo "Del ... al ..."
            match = self.PATTERNS["periodo_del"].search(cabecera_text)
            if match:
                header.periodo_inicio = match.group(1)

        match = self.PATTERNS["periodo_hasta"].search(cabecera_text)
        if match:
            header.periodo_fin = match.group(1)
        else:
            # Intentar formato alternativo "al ..."
            match = self.PATTERNS["periodo_al"].search(cabecera_text)
            if match:
                header.periodo_fin = match.group(1)

        # Extraer fecha de generación con hora
        match = self.PATTERNS["fecha_generacion"].search(cabecera_text)
        if match:
            header.fecha_generacion = f"{match.group(1)} {match.group(2)}"
        else:
            # Intentar fecha sola
            match = self.PATTERNS["fecha_sola"].search(cabecera_text)
            if match:
                header.fecha_generacion = match.group(1)

        # Extraer tipo de documento
        if self.PATTERNS["tipo_balance_sumas"].search(cabecera_text):
            header.tipo_documento = "BALANCE DE SUMAS Y SALDOS"
        elif self.PATTERNS["tipo_balance_tesoreria"].search(cabecera_text):
            header.tipo_documento = "BALANCE DE TESORERIA"
        elif self.PATTERNS["tipo_ejecucion_presupuesto"].search(cabecera_text):
            header.tipo_documento = "ESTADO DE EJECUCION DEL PRESUPUESTO"
        elif self.PATTERNS["tipo_gastos_finalidad"].search(cabecera_text):
            header.tipo_documento = "EJECUCION GASTOS POR FINALIDAD Y FUNCION"

        return header


# ============================================================================
# FUNCIÓN DE CONVENIENCIA
# ============================================================================

def extract_header_from_vision_content(
    content: str,
    municipio: str = ""
) -> Dict[str, Any]:
    """
    Extrae cabecera de contenido extraído por Vision API.

    Función de conveniencia para uso rápido.

    Args:
        content: Contenido extraído por Vision API
        municipio: Nombre del municipio

    Returns:
        Diccionario con los campos de la cabecera
    """
    extractor = BalanceHeaderExtractor(municipio)
    header = extractor.extract(content, municipio)
    return header.to_dict()


def extract_header_with_periodo_code(
    content: str,
    municipio: str = ""
) -> tuple[Dict[str, Any], Optional[str]]:
    """
    Extrae cabecera y calcula código de periodo.

    Args:
        content: Contenido extraído por Vision API
        municipio: Nombre del municipio

    Returns:
        Tuple (cabecera_dict, periodo_code)
    """
    extractor = BalanceHeaderExtractor(municipio)
    header = extractor.extract(content, municipio)
    return header.to_dict(), header.get_periodo_code()


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test con contenido típico de R.A.F.A.M.
    test_content = """
    R.A.F.A.M.
    Municipio de Carlos Tejedor

    Ejercicio: 2020
    Desde el 02/01/2020 hasta el 30/06/2020
    20/07/2020 08:09

    BALANCE DE SUMAS Y SALDOS

    | CUENTA | DESCRIPCION | ...
    """

    from rich.console import Console
    console = Console()

    console.print("[cyan]Test de extractor de cabeceras:[/cyan]\n")

    cabecera, periodo_code = extract_header_with_periodo_code(test_content, "Carlos Tejedor")

    console.print("[bold]Datos extraídos:[/bold]")
    for key, value in cabecera.items():
        console.print(f"  {key}: {value}")

    console.print(f"\n[bold]Periodo calculado:[/bold] {periodo_code}")

    # Test con Balance de Tesoreria
    test_content_2 = """
    R.A.F.A.M.
    Ejercicio 2021: Del 01/01/2021 al 31/03/2021
    15/04/2021

    BALANCE DE TESORERIA
    """

    console.print("\n[cyan]Test 2: Balance de Tesorería[/cyan]\n")
    cabecera2, periodo_code2 = extract_header_with_periodo_code(test_content_2, "Carlos Tejedor")

    for key, value in cabecera2.items():
        console.print(f"  {key}: {value}")
    console.print(f"\n[bold]Periodo calculado:[/bold] {periodo_code2}")
