#!/usr/bin/env python3
"""
balance_extractor.py

Extractor de datos numéricos críticos de balances contables.
Extrae totales, saldos e ingresos/egresos de documentos Balance de Tesorería.

Diseñado para Layer 1 de arquitectura zero-hallucination:
Garantiza que cada documento Balance tiene campos de resumen ANTES de chunking.

@created 2026-02-15
@author SIBOM IA
"""

import re
import json
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class BalanceSummary:
    """Datos resumidos extraído de un balance contable"""
    # Totales obligatorios (TIER-1)
    saldo_inicial: Optional[float] = None
    total_ingresos_presupuestarios: Optional[float] = None
    total_egresos: Optional[float] = None
    saldo_final: Optional[float] = None

    # Recursos extrapresupuestarios
    total_ingresos_extrapresupuestarios: Optional[float] = None
    total_egresos_extrapresupuestarios: Optional[float] = None

    # Ajustes
    resultados_ejercicios_anteriores: Optional[float] = None

    # Metadatos
    municipio: str = ""
    periodo: str = ""
    tipo_detalle: str = ""
    fecha_extraccion: str = ""
    confianza_general: float = 0.0
    campos_extraidos: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON"""
        return asdict(self)

    def to_json_str(self) -> str:
        """Convierte a string JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @property
    def is_complete(self) -> bool:
        """Retorna True si tiene los datos mínimos obligatorios"""
        required_fields = [
            self.saldo_inicial,
            self.saldo_final,
            self.total_egresos
        ]
        return all(f is not None for f in required_fields)

    @property
    def completeness_score(self) -> float:
        """Score de completitud: 0.0 a 1.0"""
        fields_present = sum(1 for f in [
            self.saldo_inicial,
            self.total_ingresos_presupuestarios,
            self.total_egresos,
            self.saldo_final,
            self.total_ingresos_extrapresupuestarios,
            self.total_egresos_extrapresupuestarios,
            self.resultados_ejercicios_anteriores
        ] if f is not None)

        return fields_present / 7.0


class BalanceExtractor:
    """
    Extrae datos numéricos de balances contables.

    Estrategia:
    1. Buscar patrones específicos en el contenido markdown
    2. Extraer números argentinos (formato: 1.234.567,89)
    3. Retornar objeto BalanceSummary con todos los totales
    """

    # Patrones para encontrar los grandes totales
    PATTERNS = {
        'saldo_inicial': [
            # Patrón principal: "**Total Disponibilidades:** **469.581.055,31**"
            r'\*\*Total\s+Disponibilidades:\*\*\s*\*?\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?\*?',
            # Alternativa: números al final de línea con Total Disponibilidades
            r'Total\s+Disponibilidades[:\s]+\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
            # Alternativas para Saldo Inicial
            r'Saldo\s+Inicial[:\s]+\*?\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?\*?',
        ],

        'total_ingresos_presupuestarios': [
            # Patrón principal: "**Total de Recursos:** 2.035.900.495,32"
            r'\*\*Total\s+de\s+Recursos:\*\*[:\s]*\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
            # Alternativa sin negritas
            r'Total\s+de\s+Recursos:\s+\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
            # Total Recursos Presupuestarios
            r'Total(?:\s+de)?\s+Recursos\s+Presupuestarios?[:\s]+\*?([0-9.,]+)\*?',
        ],

        'total_egresos': [
            # Patrón principal: línea de tabla que termina con número grande sin descripción
            r'\|\s+\|[^\|]*\|\s*([2][0-9.]{1,15},[0-9]{2})\s*\|',
            # Patrón alternativo: línea de tabla estándar "Total de Gastos"
            r'Total(?:\s+de)?\s+(?:Gastos|Egresos)[:\s]+\|?\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
        ],

        'saldo_final': [
            # Patrón principal: "**502.347.349,06**" después de "Total Disponibilidades:" (segunda aparición)
            r'(?:Saldo|Total)\s+(?:Final|Disponibilidades)[\s:]+.*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?\*?(?=\n)',
            # Simple: "Saldo Final: **502.347.349,06**"
            r'Saldo\s+Final[:\s]+\*?\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?\*?',
        ],

        'total_ingresos_extrapresupuestarios': [
            r'(?:Recursos|Total)\s+Extrapres(?:upuestarios)?[:\s]+\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
            r'Recursos\s+Extrapresupuestarios?.*?\|\s*\*?\*?([0-9.,]+)\*?\*?',
        ],

        'total_egresos_extrapresupuestarios': [
            r'(?:Gastos|Total)\s+Extrapres(?:upuestarios)?[:\s]+\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
            r'Total de Gastos:.*?\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
        ],

        'resultados_ejercicios_anteriores': [
            r'Resultados?\s+(?:de\s+)?[Ee]jercicios?\s+[Aa]nteriores?[:\s]+\*?([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]+)?)\*?',
        ],
    }

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.extractor_stats = {
            'documents_processed': 0,
            'complete_extractions': 0,
            'partial_extractions': 0,
            'failed_extractions': 0,
        }

    def _normalize_number(self, num_str: str) -> float:
        """
        Convierte número argentino a float.
        Ejemplo: "469.581.055,31" -> 469581055.31
        """
        if not num_str:
            return None

        try:
            # Limpiar espacios
            num_str = num_str.strip()

            # Argentino: 1.234.567,89 -> float
            # Remover puntos (miles) y reemplazar coma (decimal) por punto
            cleaned = num_str.replace('.', '').replace(',', '.')
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _find_value(self, text: str, patterns: List[str],
                    region: Optional[str] = None) -> Optional[float]:
        """
        Busca un valor en el texto usando múltiples patrones.

        Args:
            text: Texto a buscar
            patterns: Lista de patrones regex a intentar
            region: Región opcional de texto donde buscar

        Returns:
            Número encontrado o None
        """
        search_text = region if region else text

        for pattern in patterns:
            try:
                match = re.search(pattern, search_text,
                                  re.IGNORECASE | re.DOTALL)
                if match:
                    num_str = match.group(1)
                    value = self._normalize_number(num_str)
                    if value:
                        return value
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠ Error en patrón {pattern[:30]}...: {e}")

        return None

    def _extract_from_demonstracion_saldos(self, contenido: str) -> Dict[str, Optional[float]]:
        """
        Extrae datos de la sección "Demostración de Saldos" (más confiable que búsqueda global).

        Formato esperado:
        | Saldo Inicial: | 469.581.055,31 |
        | Balance de Ingresos y Egresos: | 32.766.293,75 |
        | Saldo final: | 502.347.349,06 |
        """
        results = {}

        # Buscar la sección "Demostración de Saldos"
        demo_idx = contenido.find("Demostración de Saldos")
        if demo_idx == -1:
            return results

        # Extraer 1000 chars después de "Demostración" para la tabla
        demo_section = contenido[demo_idx:demo_idx+1000]

        # Patrones específicos para la tabla
        patterns_demo = {
            'saldo_inicial': r'\|\s*Saldo\s+Inicial[:\s]*\|\s*([0-9.,]+)',
            'balance_ingresos_egresos': r'\|\s*Balance[\s\w]+[:\s]*\|\s*([0-9.,]+)',
            'saldo_final': r'\|\s*Saldo\s+final[:\s]*\|\s*([0-9.,]+)',
        }

        for field, pattern in patterns_demo.items():
            match = re.search(pattern, demo_section, re.IGNORECASE | re.DOTALL)
            if match:
                num_str = match.group(1)
                value = self._normalize_number(num_str)
                if value:
                    results[field] = value

        return results

    def extract(self, document: Dict[str, Any]) -> BalanceSummary:
        """
        Extrae datos numéricos de un documento Balance.

        Estrategia (en orden de preferencia):
        1. Sección "Demostración de Saldos" (TIER-1 más confiable)
        2. Búsqueda global en contenido (TIER-2 fallback)

        Args:
            document: Dict con campos: municipio, contenido, periodo, tipo_detalle

        Returns:
            BalanceSummary con datos extraídos
        """
        self.extractor_stats['documents_processed'] += 1

        # Validar documento
        if not isinstance(document, dict):
            return BalanceSummary()

        contenido = document.get('contenido', '')
        if not contenido:
            return BalanceSummary()

        # Crear objeto resumen
        summary = BalanceSummary(
            municipio=document.get('municipio', 'Desconocido'),
            periodo=document.get('periodo', 'S/D'),
            tipo_detalle=document.get('tipo_detalle', 'Balance'),
            fecha_extraccion=datetime.now().isoformat(),
        )

        extracted_count = 0

        # PASO 1: Intentar extraer de "Demostración de Saldos" (TIER-1)
        demo_data = self._extract_from_demonstracion_saldos(contenido)
        if demo_data:
            if 'saldo_inicial' in demo_data:
                summary.saldo_inicial = demo_data['saldo_inicial']
                extracted_count += 1
                if self.verbose:
                    print(
                        f"  ✓ saldo_inicial: ${demo_data['saldo_inicial']:,.2f} (from Demostración)")

            if 'saldo_final' in demo_data:
                summary.saldo_final = demo_data['saldo_final']
                extracted_count += 1
                if self.verbose:
                    print(
                        f"  ✓ saldo_final: ${demo_data['saldo_final']:,.2f} (from Demostración)")

        # PASO 2: Buscar Total de Recursos / Ingresos (global search)
        total_ingresos = self._find_value(
            contenido, self.PATTERNS['total_ingresos_presupuestarios'])
        if total_ingresos:
            summary.total_ingresos_presupuestarios = total_ingresos
            extracted_count += 1
            if self.verbose:
                print(
                    f"  ✓ total_ingresos_presupuestarios: ${total_ingresos:,.2f}")

        # PASO 3: Buscar Total de Egresos (global search)
        total_egresos = self._find_value(
            contenido, self.PATTERNS['total_egresos'])
        if total_egresos:
            summary.total_egresos = total_egresos
            extracted_count += 1
            if self.verbose:
                print(f"  ✓ total_egresos: ${total_egresos:,.2f}")

        # PASO 4: Buscar otros campos
        for field_name in ['total_ingresos_extrapresupuestarios', 'resultados_ejercicios_anteriores']:
            value = self._find_value(contenido, self.PATTERNS[field_name])
            if value is not None:
                setattr(summary, field_name, value)
                extracted_count += 1
                if self.verbose:
                    print(f"  ✓ {field_name}: ${value:,.2f}")

        summary.campos_extraidos = extracted_count
        summary.confianza_general = summary.completeness_score

        # Registrar estadísticas
        if summary.is_complete:
            self.extractor_stats['complete_extractions'] += 1
        elif extracted_count > 0:
            self.extractor_stats['partial_extractions'] += 1
        else:
            self.extractor_stats['failed_extractions'] += 1

        if self.verbose:
            print(f"  📊 Completitud: {summary.completeness_score:.0%} "
                  f"({extracted_count}/7 campos)")

        return summary

    def extract_batch(self, documents: List[Dict[str, Any]]) -> List[BalanceSummary]:
        """
        Extrae datos de múltiples documentos.

        Args:
            documents: Lista de documentos

        Returns:
            Lista de BalanceSummary
        """
        results = []
        for doc in documents:
            result = self.extract(doc)
            results.append(result)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de extracciones"""
        total = self.extractor_stats['documents_processed']

        return {
            **self.extractor_stats,
            'success_rate': (
                (self.extractor_stats['complete_extractions'] / total * 100)
                if total > 0 else 0
            ),
        }


def test_extraction():
    """Test del extractor con un ejemplo real"""
    print("🧪 Testing BalanceExtractor...")

    # Ejemplo de documento
    test_doc = {
        'municipio': 'Carlos Tejedor',
        'periodo': '2024-T1',
        'tipo_detalle': 'BALANCE DE TESORERIA',
        'contenido': '''
        **Total Disponibilidades:** **469.581.055,31**
        
        **Total de Recursos:** 2.035.900.495,32
        
        **Total de Egresos:** 2.003.134.201,57
        
        **Saldo Final:** 502.347.349,06
        '''
    }

    extractor = BalanceExtractor(verbose=True)
    summary = extractor.extract(test_doc)

    print(f"\n✅ Extracción completada:")
    print(
        f"  Saldo Inicial: ${summary.saldo_inicial:,.2f}" if summary.saldo_inicial else "  Saldo Inicial: NO ENCONTRADO")
    print(f"  Completitud: {summary.completeness_score:.0%}")
    print(f"  Stats: {extractor.get_stats()}")


if __name__ == '__main__':
    test_extraction()
