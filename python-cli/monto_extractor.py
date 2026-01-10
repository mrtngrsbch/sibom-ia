#!/usr/bin/env python3
"""
monto_extractor.py

Extrae montos monetarios del texto de boletines municipales.
Genera registros estructurados con citas textuales para cómputos comparativos.

@created 2025-01-09
@author Kilo Code
"""

import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class MontoRecord:
    """Registro estructurado de un monto extraído"""
    municipio: str
    boletin: str
    fecha: str
    norma_tipo: str  # Ordenanza, Decreto, Resolución, etc.
    norma_numero: str
    articulo: str
    concepto: str
    monto: float
    moneda: str
    texto_completo: str
    fuente_url: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MontoExtractor:
    """Extractor de montos monetarios de boletines"""

    # Patrones de moneda y número en formato argentino
    # Formatos: "$ 155.162,86", "$155.162,86", "PESOS ... ($ ...)"
    AMOUNT_PATTERN = re.compile(
        r'(?:PESOS\s+(?:CIENTO\s+)?[^$]+?)?'  # Prefijo "PESOS ..." opcional
        r'\$\s*'  # Símbolo de peso
        r'(\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+)(?:\s*,\s*\d+)?'  # Número argentino
        r'(?:\s*con\s+(\d+)\s+centavos)?',  # "con 50 centavos"
        re.IGNORECASE
    )

    # Patrones para identificar tipo de norma
    NORMA_PATTERNS = {
        'Ordenanza': re.compile(r'ORDENANZA\s+N[º°]\s*(\d+[^\s]*)', re.IGNORECASE),
        'Decreto': re.compile(r'DECRETO\s+N[º°]\s*(\d+[^\s]*)', re.IGNORECASE),
        'Resolución': re.compile(r'RESOLUCIÓN\s+N[º°]\s*(\d+[^\s]*)', re.IGNORECASE),
        'Resolucion': re.compile(r'RESOLUCION\s+N[º°]\s*(\d+[^\s]*)', re.IGNORECASE),
        'Disposición': re.compile(r'DISPOSICIÓN\s+N[º°]\s*(\d+[^\s]*)', re.IGNORECASE),
        'Disposicion': re.compile(r'DISPOSICION\s+N[º°]\s*(\d+[^\s]*)', re.IGNORECASE),
        'Edicto': re.compile(r'EDITO\s+N[º°]\s*(\d+[^\s]*)', re.IGNORECASE),
    }

    # Patrón para artículos
    ARTICULO_PATTERN = re.compile(
        r'ART[ÍI]CULO\s+N?[º°]?\s*(\d+[A-Za-z]?)',
        re.IGNORECASE
    )

    # Palabras clave que indican contexto relevante
    CONTEXT_KEYWORDS = [
        'sueldo', 'salario', 'honorarios', 'remuneración', 'remuneracion',
        'monto', 'importe', 'tasa', 'arancel', 'tributo', 'impuesto',
        'gasto', 'obra', 'contratación', 'contratacion', 'adquisición',
        'adquisicion', 'presupuesto', 'credito', 'credito',
        ' subsidio', 'subvención', 'subvencion', 'beca', 'beneficio'
    ]

    def __init__(self):
        self.stats = {
            'processed': 0,
            'amounts_found': 0,
            'records_created': 0
        }

    def _parse_argentine_number(self, num_str: str) -> Optional[float]:
        """
        Convierte número argentino a float.
        Formato: 1.234.567,89 -> 1234567.89
        """
        try:
            # Remover puntos de miles y reemplazar coma por punto
            cleaned = num_str.replace('.', '').replace(',', '.')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _extract_municipio(self, description: str) -> str:
        """
        Extrae nombre del municipio de la descripción.
        Formato: "6º de Nueve de Julio" -> "Nueve de Julio"
        """
        match = re.search(r'de\s+(.+?)(?:\s+\(|$)', description)
        if match:
            municipio = match.group(1).strip()
            # Limpiar sufijos comunes
            municipio = re.sub(r'\s*\([^)]*\)', '', municipio).strip()
            return municipio
        return "Desconocido"

    def _extract_boletin_number(self, description: str) -> str:
        """Extrae número de boletín de la descripción"""
        match = re.search(r'(\d+)[º°]', description)
        return match.group(1) if match else "0"

    def _extract_norma_info(self, text: str) -> tuple[str, str]:
        """
        Extrae tipo y número de norma del texto.
        Returns: (tipo, numero)
        """
        for tipo, pattern in self.NORMA_PATTERNS.items():
            match = pattern.search(text)
            if match:
                return tipo, match.group(1)
        return "Norma", "S/N"

    def _extract_articulo(self, text: str) -> str:
        """Extrae número de artículo del texto"""
        # Buscar en una ventana cercana al monto
        match = self.ARTICULO_PATTERN.search(text)
        return match.group(1) if match else "S/N"

    def _extract_context(self, text: str, monto_pos: int, window: int = 200) -> str:
        """
        Extrae contexto alrededor del monto para identificar el concepto.
        """
        start = max(0, monto_pos - window)
        end = min(len(text), monto_pos + window)
        context = text[start:end]

        # Buscar la oración completa que contiene el monto
        sentences = re.split(r'[.\n]+', context)
        for sentence in sentences:
            if '$' in sentence or 'PESOS' in sentence:
                # Limpiar y recortar
                cleaned = ' '.join(sentence.split())
                if len(cleaned) > 150:
                    # Truncar pero mantener palabras completas
                    cleaned = cleaned[:147].rsplit(' ', 1)[0] + '...'
                return cleaned
        return context[:100] + '...' if len(context) > 100 else context

    def _extract_concept(self, context: str, text: str) -> str:
        """
        Intenta extraer el concepto del gasto/tasa del contexto.
        """
        # Buscar palabras clave en el contexto
        for keyword in self.CONTEXT_KEYWORDS:
            if keyword.lower() in context.lower():
                # Extraer frase alrededor de la keyword
                pattern = re.compile(
                    rf'.{{0,50}}{re.escape(keyword)}.{{0,100}}',
                    re.IGNORECASE
                )
                match = pattern.search(context)
                if match:
                    concepto = match.group(0).strip()
                    # Limpiar
                    concepto = re.sub(r'\s+', ' ', concepto)
                    return concepto[:150]

        # Fallback: usar primeras palabras del contexto
        words = context.split()[:10]
        return ' '.join(words)

    def extract_from_boletin(self, boletin: Dict[str, Any]) -> List[MontoRecord]:
        """
        Extrae todos los montos de un boletín completo.

        Args:
            boletin: Diccionario con datos del boletín (leído de JSON)

        Returns:
            Lista de registros MontoRecord
        """
        self.stats['processed'] += 1

        # Obtener municipio y número de boletín
        municipio = self._extract_municipio(boletin.get('description', ''))
        boletin_num = self._extract_boletin_number(boletin.get('description', ''))
        fecha = boletin.get('date', '')
        fuente_url = boletin.get('link', '')

        # Usar text_content o fullText
        text = boletin.get('text_content') or boletin.get('fullText') or ''

        if not text:
            return []

        records = []
        doc_start = 0

        # Buscar todos los montos en el texto
        for match in self.AMOUNT_PATTERN.finditer(text):
            monto_str = match.group(1)
            centavos_str = match.group(2)

            # Parsear monto
            monto = self._parse_argentine_number(monto_str)
            if monto is None or monto < 1:  # Filtrar valores inválidos
                continue

            if centavos_str:
                monto += int(centavos_str) / 100

            # Posición del monto en el texto
            monto_pos = match.start()

            # Extraer contexto antes del monto (para obtener info de norma/artículo)
            context_window = text[max(0, monto_pos - 500):monto_pos + 200]

            # Extraer información de norma
            norma_tipo, norma_numero = self._extract_norma_info(context_window)

            # Extraer artículo
            # Buscar artículo cercano al monto
            articulo_match = self.ARTICULO_PATTERN.search(context_window)
            articulo = articulo_match.group(1) if articulo_match else "S/N"

            # Extraer concepto del contexto
            concepto = self._extract_concept(context_window, text)

            # Construir cita textual
            cita = self._build_cita(
                boletin_num, municipio, norma_tipo, norma_numero,
                articulo, monto, context_window
            )

            record = MontoRecord(
                municipio=municipio,
                boletin=boletin_num,
                fecha=fecha,
                norma_tipo=norma_tipo,
                norma_numero=norma_numero,
                articulo=articulo,
                concepto=concepto,
                monto=monto,
                moneda='ARS',
                texto_completo=cita,
                fuente_url=fuente_url
            )

            records.append(record)
            self.stats['amounts_found'] += 1

        self.stats['records_created'] += len(records)
        return records

    def _build_cita(self, boletin: str, municipio: str, tipo: str,
                    numero: str, articulo: str, monto: float,
                    context: str) -> str:
        """Construye cita textual con formato estándar"""
        monto_formatted = f"{monto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"Boletín {boletin}º | {municipio} | {tipo} Nº{numero} [ARTÍCULO {articulo}: ${monto_formatted}]"

    def process_directory(self, boletines_dir: Path,
                          output_file: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Procesa todos los JSONs en un directorio.

        Args:
            boletines_dir: Directorio con archivos JSON de boletines
            output_file: Archivo donde guardar el índice de montos

        Returns:
            Lista de todos los registros extraídos
        """
        all_records = []

        json_files = list(boletines_dir.glob('*.json'))
        print(f"📁 Procesando {len(json_files)} archivos en {boletines_dir}")

        for json_file in json_files:
            try:
                with json_file.open('r', encoding='utf-8') as f:
                    boletin = json.load(f)

                records = self.extract_from_boletin(boletin)
                if records:
                    all_records.extend([r.to_dict() for r in records])
                    print(f"  ✓ {json_file.name}: {len(records)} montos")
                else:
                    print(f"  - {json_file.name}: sin montos")

            except Exception as e:
                print(f"  ✗ {json_file.name}: error - {e}")

        # Guardar índice consolidado
        if output_file and all_records:
            self._save_index(all_records, output_file)
            print(f"\n💾 Índice guardado: {output_file}")

        self._print_stats()
        return all_records

    def _save_index(self, records: List[Dict[str, Any]], output_file: Path):
        """Guarda el índice de montos en formato JSON"""
        index = {
            'metadata': {
                'total_records': len(records),
                'municipios': len(set(r['municipio'] for r in records)),
                'generated_at': str(Path(__file__).stat().st_mtime)
            },
            'records': records
        }

        with output_file.open('w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _print_stats(self):
        """Imprime estadísticas de extracción"""
        print(f"\n📊 Estadísticas:")
        print(f"  Boletines procesados: {self.stats['processed']}")
        print(f"  Montos encontrados: {self.stats['amounts_found']}")
        print(f"  Registros creados: {self.stats['records_created']}")


def main():
    """CLI para extraer montos de boletines existentes"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extrae montos monetarios de boletines municipales'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='boletines',
        help='Directorio con JSONs de boletines (default: boletines)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='montos_index.json',
        help='Archivo de salida (default: montos_index.json)'
    )

    args = parser.parse_args()

    extractor = MontoExtractor()
    extractor.process_directory(
        Path(args.input),
        Path(args.output)
    )


if __name__ == '__main__':
    main()
