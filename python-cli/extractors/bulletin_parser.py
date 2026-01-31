#!/usr/bin/env python3
"""
bulletin_parser.py

Extractor de boletines municipales usando pdftotext.
Divide un boletín en normativas individuales (ordenanzas, decretos, etc.).

@version 1.0.0
@created 2026-01-29
"""

import asyncio
import re
import subprocess
import tempfile
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from rich.console import Console

console = Console()


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class ParsedNormativa:
    """Una normativa extraída de un boletín"""
    tipo: str  # "ordenanza", "decreto", "resolucion", "disposicion"
    numero: str  # Número de la normativa
    anio: str  # Año (extraído del número o contexto)
    titulo: str  # Título descriptivo
    contenido: str  # Contenido completo
    fecha: str = ""  # Fecha de sanción (si se detecta)
    indice: int = 0  # Índice dentro del boletín

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# BOLETIN PARSER
# =============================================================================

class BulletinParser:
    """
    Parser de boletines municipales que:
    1. Extrae texto usando pdftotext (mejor que pdfplumber)
    2. Divide en normativas individuales
    3. Extrae metadata (tipo, número, año, fecha)
    """

    # Patrones para detectar inicio de normativa
    NORMATIVA_PATTERNS = [
        r'ORDENANZA\s+N?º?\s*([\d/]+)',
        r'DECRETO\s+N?º?\s*([\d/]+)',
        r'RESOLUCI[ÓO]N\s+N?º?\s*([\d/]+)',
        r'DISPOSICI[ÓO]N\s+N?º?\s*([\d/]+)',
        r'ORD\.?\s+N?º?\s*([\d/]+)',  # Abreviatura
        r'DEC\.?\s+N?º?\s*([\d/]+)',
        r'RES\.?\s+N?º?\s*([\d/]+)',
    ]

    # Mapeo de patrones a tipos
    PATTERNS_TO_TYPE = {
        'ORDENANZA': 'ordenanza',
        'ORD': 'ordenanza',
        'DECRETO': 'decreto',
        'DEC': 'decreto',
        'RESOLUCION': 'resolucion',
        'RESOLUCIÓN': 'resolucion',
        'RES': 'resolucion',
        'DISPOSICION': 'disposicion',
        'DISPOSICIÓN': 'disposicion',
        'DISP': 'disposicion',
    }

    # Patrones para detectar fecha de sanción
    DATE_PATTERNS = [
        r'DADA EN LA SALA[^.]*\d{1,2}\s+DE\s+([A-ZÑÁÉÍÓÚ]+)\s+DE\s+(\d{4})',
        r'FECHA DE SANCION[:\s]*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
        r'(\d{1,2})\s+DE\s+([A-ZÑÁÉÍÓÚ]+)\s+DE\s+(\d{4})',
    ]

    MESES_ES = {
        'ENERO': '01', 'FEBRERO': '02', 'MARZO': '03', 'ABRIL': '04',
        'MAYO': '05', 'JUNIO': '06', 'JULIO': '07', 'AGOSTO': '08',
        'SEPTIEMBRE': '09', 'OCTUBRE': '10', 'NOVIEMBRE': '11', 'DICIEMBRE': '12'
    }

    def __init__(self, quality_threshold: float = 0.5):
        """
        Args:
            quality_threshold: Confianza mínima para aceptar una normativa (0.0-1.0)
        """
        self.quality_threshold = quality_threshold

    async def parse_pdf_file(
        self,
        pdf_path: str | Path,
        municipio: str = "Desconocido"
    ) -> Tuple[List[ParsedNormativa], Dict[str, Any]]:
        """
        Parsea un archivo PDF de boletín y extrae las normativas.

        Args:
            pdf_path: Ruta al PDF
            municipio: Nombre del municipio

        Returns:
            (normativas, metadata) - Lista de normativas y metadata del boletín
        """
        pdf_path = Path(pdf_path)

        # 1. Extraer texto con pdftotext
        text = await self._extract_text_with_pdftotext(pdf_path)

        if not text:
            return [], {"error": "No se pudo extraer texto del PDF"}

        # 2. Validar calidad básica del texto
        quality = self._assess_text_quality(text)
        console.print(f"[dim]  Calidad del texto: {quality['confidence']:.1%} ({quality['quality']})[/dim]")

        if quality['confidence'] < self.quality_threshold:
            console.print(f"[yellow]⚠️ Texto de baja calidad, intentando mejorar...[/yellow]")
            # Intentar limpieza adicional
            text = self._clean_text(text)

        # 3. Dividir en normativas
        normativas = self._split_into_normativas(text, municipio)

        # 4. Metadata del boletín
        metadata = {
            "municipio": municipio,
            "total_paginas": self._get_page_count(pdf_path),
            "total_normas": len(normativas),
            "text_quality": quality['quality'],
            "confidence": quality['confidence'],
            "raw_text_length": len(text),
        }

        return normativas, metadata

    async def _extract_text_with_pdftotext(self, pdf_path: Path) -> str:
        """Extrae texto usando pdftotext (poppler-utils)"""
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', '-enc', 'UTF-8', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return result.stdout
            else:
                console.print(f"[red]Error pdftotext: {result.stderr}[/red]")
                return ""

        except FileNotFoundError:
            console.print("[yellow]⚠️ pdftotext no encontrado. Instalar: brew install poppler[/yellow]")
            return ""
        except Exception as e:
            console.print(f"[red]Error extrayendo texto: {e}[/red]")
            return ""

    def _get_page_count(self, pdf_path: Path) -> int:
        """Obtiene el número de páginas del PDF"""
        try:
            result = subprocess.run(
                ['pdfinfo', str(pdf_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if 'Pages:' in line:
                    return int(line.split(':')[1].strip())
        except:
            pass
        return 0

    def _assess_text_quality(self, text: str) -> Dict[str, Any]:
        """
        Evalúa la calidad del texto extraído.
        Retorna dict con confidence, quality, y warnings.
        """
        if not text:
            return {"confidence": 0.0, "quality": "failed", "warnings": ["texto_vacio"]}

        warnings = []
        score = 1.0

        # 1. Longitud
        if len(text) < 500:
            score -= 0.5
            warnings.append("texto_corto")

        # 2. Caracteres corruptos específicos
        corrupt_indicators = [
            (r"´[aeiouAEIOU]", "acentos_rotos"),  # ´a, ´e en lugar de á, é
            (r"[A-Z]\s[A-Z]\s[A-Z]", "mayusculas_separadas"),
            (r"H[º°]\s*S[º°]", "honorarios_corruptos"),
        ]

        for pattern, name in corrupt_indicators:
            matches = len(re.findall(pattern, text))
            if matches > 5:
                score -= 0.2
                warnings.append(f"{name}:{matches}")

        # 3. Presencia de palabras clave legales
        legal_words = ['articulo', 'ordinanza', 'decreto', 'resolucion', 'sancion',
                       'comuniquese', 'departamento', 'ejecutivo']
        legal_count = sum(1 for word in legal_words if word.lower() in text.lower())

        if legal_count < 2:
            score -= 0.3
            warnings.append("sin_palabras_legales")

        # Determinar nivel
        if score >= 0.8:
            quality = "excellent"
        elif score >= 0.6:
            quality = "good"
        elif score >= 0.4:
            quality = "fair"
        elif score >= 0.2:
            quality = "poor"
        else:
            quality = "failed"

        return {
            "confidence": max(0, score),
            "quality": quality,
            "warnings": warnings[:5]
        }

    def _clean_text(self, text: str) -> str:
        """
        Limpia el texto aplicando correcciones comunes.

        El problema principal de pdftotext con -layout es que mantiene
        los saltos de línea del PDF, rompiendo palabras en mitad.
        """
        lines = text.split('\n')
        cleaned_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Si la línea es muy corta y no termina en punto, podría ser continuación
            if i + 1 < len(lines) and line:
                next_line = lines[i + 1].strip()

                # Unir si:
                # - La línea actual no termina en puntuación fuerte
                # - La siguiente empieza con minúscula o número
                # - La línea es muy corta (< 60 chars)
                should_join = (
                    len(line) < 60 and
                    not line.endswith(('.', ':', ';', '!')) and
                    not next_line[0:1].isupper() if next_line else False
                )

                if should_join:
                    # Unir líneas
                    line = line + ' ' + next_line
                    i += 2
                    cleaned_lines.append(line)
                    continue

            cleaned_lines.append(line)
            i += 1

        text = '\n'.join(cleaned_lines)

        # Espacios múltiples
        text = re.sub(r' +', ' ', text)

        # Guiones al final de línea (palabras divididas)
        text = re.sub(r'-\n\s*', '', text)

        # Saltos de línea excesivos
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _split_into_normativas(self, text: str, municipio: str) -> List[ParsedNormativa]:
        """
        Divide el texto del boletín en normativas individuales.

        Busca patrones como:
        - ORDENANZA 3793/16
        - DECRETO 123/2024
        - RESOLUCIÓN 456/2024
        """
        normativas = []

        # Compilar todos los patrones
        all_patterns = []
        for pattern_str in self.NORMATIVA_PATTERNS:
            all_patterns.append(re.compile(pattern_str, re.IGNORECASE))

        # Encontrar todas las posiciones donde empieza una normativa
        matches = []
        for pattern in all_patterns:
            for match in pattern.finditer(text):
                tipo_match = match.group(0).split()[0].upper()
                tipo = self.PATTERNS_TO_TYPE.get(
                    tipo_match,
                    tipo_match.lower()
                )
                numero = match.group(1)

                matches.append({
                    'pos': match.start(),
                    'tipo': tipo,
                    'numero': numero,
                    'full_match': match.group(0)
                })

        # Ordenar por posición
        matches.sort(key=lambda x: x['pos'])

        if not matches:
            console.print("[yellow]⚠️ No se detectaron normativas en el texto[/yellow]")
            # Retornar el texto completo como una sola normativa
            return [ParsedNormativa(
                tipo="desconocido",
                numero="0",
                anio="",
                titulo=text[:100],
                contenido=text[:50000],
                indice=0
            )]

        console.print(f"[green]✓ Detectadas {len(matches)} normativas[/green]")

        # Extraer cada normativa
        for i, match in enumerate(matches):
            # Determinar rango: desde esta normativa hasta la siguiente
            start_pos = match['pos']
            end_pos = matches[i + 1]['pos'] if i + 1 < len(matches) else len(text)

            # Extraer contenido
            contenido = text[start_pos:end_pos].strip()

            # Limitar longitud (evitar normativas gigantes)
            if len(contenido) > 50000:
                contenido = contenido[:50000] + "\n\n[... contenido truncado ...]"

            # Extraer año del número (ej: 3793/16 -> 2016)
            numero = match['numero']
            anio = self._extract_year(numero, contenido)

            # Extraer título (primeras líneas)
            titulo = self._extract_title(contenido, match['tipo'], numero)

            # Extraer fecha
            fecha = self._extract_date(contenido)

            normativa = ParsedNormativa(
                tipo=match['tipo'],
                numero=numero,
                anio=anio,
                titulo=titulo,
                contenido=contenido,
                fecha=fecha,
                indice=i
            )

            normativas.append(normativa)

        return normativas

    def _extract_year(self, numero: str, contenido: str) -> str:
        """Extrae el año de una normativa"""
        # Primero intentar del número (ej: 3793/16)
        if '/' in numero:
            year_part = numero.split('/')[-1]
            if len(year_part) == 2:
                return f"20{year_part}"
            elif len(year_part) == 4:
                return year_part

        # Buscar en el contenido
        year_match = re.search(r'(?:DE\s+)?(\d{4})', contenido[:500])
        if year_match:
            return year_match.group(1)

        return ""

    def _extract_title(self, contenido: str, tipo: str, numero: str) -> str:
        """Extrae un título descriptivo del contenido"""
        # Tomar las primeras 3 líneas o 200 caracteres
        lineas = contenido.split('\n')[:5]
        titulo = ' '.join(lineas[:3])

        # Limpiar
        titulo = re.sub(r'\s+', ' ', titulo).strip()

        # Limitar longitud
        if len(titulo) > 200:
            titulo = titulo[:200]

        # Si está vacío, usar genérico
        if not titulo or len(titulo) < 10:
            titulo = f"{tipo.upper()} {numero}"

        return titulo

    def _extract_date(self, contenido: str) -> str:
        """Extrae la fecha de sanción del contenido"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, contenido)
            if match:
                groups = match.groups()
                # Formato: DÍA MES AÑO
                if len(groups) == 2 and groups[0] in self.MESES_ES:
                    dia = "01"  # Default si no tiene día explícito
                    mes = self.MESES_ES[groups[0]]
                    anio = groups[1]
                    return f"{dia}/{mes}/{anio}"
                # Formato: DÍA MES AÑO con día
                elif len(groups) == 3:
                    return f"{groups[0]}/{groups[1]}/{groups[2]}"

        return ""


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def parse_bulletin_pdf(
    pdf_path: str | Path,
    municipio: str = "Desconocido"
) -> Tuple[List[ParsedNormativa], Dict[str, Any]]:
    """
    Función de conveniencia para parsear un PDF de boletín.

    Args:
        pdf_path: Ruta al PDF
        municipio: Nombre del municipio

    Returns:
        (normativas, metadata)
    """
    parser = BulletinParser()
    return await parser.parse_pdf_file(pdf_path, municipio)


def save_bulletin_json(
    normativas: List[ParsedNormativa],
    metadata: Dict[str, Any],
    output_path: str | Path
) -> None:
    """Guarda el resultado del parsing en JSON"""
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    data = {
        "metadata": metadata,
        "normativas": [n.to_dict() for n in normativas]
    }

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    console.print(f"[green]✓ JSON guardado: {output_path}[/green]")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Parser de boletines municipales"
    )
    parser.add_argument("pdf", help="Ruta al PDF del boletín")
    parser.add_argument("--municipio", default="Desconocido", help="Nombre del municipio")
    parser.add_argument("-o", "--output", help="Archivo JSON de salida")

    args = parser.parse_args()

    async def main():
        console.print(f"[cyan]🔍 Parseando: {args.pdf}[/cyan]")

        normativas, metadata = await parse_bulletin_pdf(args.pdf, args.municipio)

        console.print(f"\n[bold]Resultados:[/bold]")
        console.print(f"  Normativas: {len(normativas)}")
        console.print(f"  Calidad: {metadata.get('text_quality', 'unknown')}")

        if normativas:
            table = []
            for n in normativas:
                table.append({
                    "Tipo": n.tipo,
                    "Número": n.numero,
                    "Año": n.anio,
                    "Longitud": f"{len(n.contenido):,}",
                })
            from rich.table import Table as RichTable
            from rich import table as rich_table

            t = RichTable(title="Normativas Detectadas")
            t.add_column("Tipo")
            t.add_column("Número")
            t.add_column("Año")
            t.add_column("Longitud")

            for n in normativas:
                t.add_row(n.tipo, n.numero, n.anio, f"{len(n.contenido):,}")

            console.print(t)

        # Guardar si se especificó output
        if args.output:
            save_bulletin_json(normativas, metadata, args.output)
        else:
            # Default: guardar junto al PDF
            pdf_path = Path(args.pdf)
            default_output = pdf_path.parent / f"{pdf_path.stem}_parsed.json"
            save_bulletin_json(normativas, metadata, default_output)

    import asyncio
    asyncio.run(main())
