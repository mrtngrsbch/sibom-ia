#!/usr/bin/env python3
"""
utils/quality_validator.py

Validador de calidad para extracciones OCR.

Estrategias basadas en best practices de MIT/Stanford para validación
de documentos OCR con visión por computadora.
"""

import re
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Resultado de validación de calidad."""
    is_valid: bool
    confidence: float  # 0.0 - 1.0
    warnings: List[str]
    errors: List[str]
    score_breakdown: Dict[str, Any]

    def __str__(self) -> str:
        if self.is_valid:
            return f"✓ Válido (confianza: {self.confidence:.1%})"
        return f"✗ Inválido ({len(self.errors)} errores, {len(self.warnings)} warnings)"


class QualityValidator:
    """
    Validador de calidad para extracciones OCR.

    Implementa reglas específicas para detectar:
    - Confianza general del contenido
    - Problemas comunes de OCR (caracteres corruptos, tablas mal formadas)
    - Longitud y estructura del contenido
    - Indicadores específicos por tipo de documento
    """

    # Umbrales de validación
    MIN_CONFIDENCE = 0.5
    MIN_CONTENT_LENGTH = 200
    MAX_CORRUPT_CHARS_RATIO = 0.01  # 1% de caracteres corruptos máximo

    # Patrones de problemas comunes
    CORRUPT_PATTERNS = [
        "´Ó", "´A", "´E", "´I", "´O", "´U",  # Acentos rotos comunes
        "o.",  # Letra o con punto típico de OCR
    ]

    # Palabras clave financieras para detectar tipo de documento
    FINANCIAL_KEYWORDS = [
        "balance", "tesoreria", "presupuesto", "ejercicio",
        "activo", "pasivo", "patrimonio", "debe", "haber",
        "ingreso", "egreso", "gastos", "inversion", "fondo"
    ]

    # Columnas críticas para documentos financieros
    CRITICAL_COLUMNS = {
        "VARIACIONES": "Columna de variaciones mensuales/anuales",
        "SALDO FINAL": "Columna de saldo final debe/haber",
        "MOVIMIENTOS": "Columna de movimientos del período",
    }

    def __init__(self, strict: bool = False):
        """
        Args:
            strict: Si True, rechaza más casos (para producción)
        """
        self.strict = strict

    def validate(
        self,
        content: str,
        quality: dict = None,
        doc_type: str = "auto"
    ) -> ValidationResult:
        """
        Valida si la extracción es aceptable.

        Args:
            content: Contenido extraído del PDF
            quality: Metadata de calidad del extractor
            doc_type: Tipo de documento ("financial", "bulletin", "auto")

        Returns:
            ValidationResult con is_valid, confidence, warnings, errors
        """
        warnings = []
        errors = []
        score_breakdown = {}

        if not content:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                warnings=[],
                errors=["Contenido vacío"],
                score_breakdown={}
            )

        content_lower = content.lower()
        length = len(content)

        # ========================================
        # 1. VALIDACIÓN DE LONGITUD
        # ========================================
        length_score = self._validate_length(content, length)
        score_breakdown["length"] = length_score

        if length_score < 0.3:
            errors.append(f"Contenido muy corto: {length} caracteres")
        elif length_score < 0.7:
            warnings.append(f"Contenido corto: {length} caracteres")

        # ========================================
        # 2. VALIDACIÓN DE CARACTERES CORRUPTOS
        # ========================================
        corrupt_score = self._validate_corrupt_chars(content, length)
        score_breakdown["corrupt"] = corrupt_score

        corrupt_ratio = content.count("´") / max(length, 1)
        if corrupt_ratio > self.MAX_CORRUPT_CHARS_RATIO:
            errors.append(f"Muchos caracteres corruptos: {content.count('´')} ({corrupt_ratio:.1%})")
        elif corrupt_score < 0.7:
            warnings.append(f"Algunos caracteres corruptos detectados")

        # ========================================
        # 3. VALIDACIÓN DE TABLAS (según tipo)
        # ========================================
        table_score = self._validate_tables(content, content_lower, doc_type)
        score_breakdown["tables"] = table_score

        # Detectar tipo de documento automáticamente
        detected_type = self._detect_doc_type(content_lower)
        if doc_type == "auto":
            doc_type = detected_type

        # ========================================
        # 3.5. VALIDACIÓN DE COLUMNAS CRÍTICAS (nuevo)
        # ========================================
        critical_cols = self._validate_critical_columns(content, doc_type)
        score_breakdown["critical_columns"] = critical_cols["score"]

        # Aplicar reglas específicas por tipo
        if doc_type == "financial":
            if "|" not in content:
                errors.append("Documento financiero sin tablas Markdown")
            elif table_score < 0.5:
                warnings.append("Tablas posiblemente mal formadas")

            # Advertencias sobre columnas críticas faltantes
            if critical_cols["missing_critical"]:
                for missing in critical_cols["missing_critical"]:
                    warnings.append(f"Falta columna crítica: {missing}")

        # ========================================
        # 4. VALIDACIÓN DE ESTRUCTURA
        # ========================================
        structure_score = self._validate_structure(content)
        score_breakdown["structure"] = structure_score

        # ========================================
        # 5. CALCULAR CONFIDENCIA FINAL
        # ========================================
        # Promedio ponderado de scores (siempre suman 1.0)
        if doc_type == "financial":
            weights = {
                "length": 0.10,
                "corrupt": 0.15,
                "tables": 0.35,
                "structure": 0.10,
                "critical_columns": 0.30  # Columnas críticas son MUY importantes
            }
        else:
            weights = {
                "length": 0.15,
                "corrupt": 0.25,
                "tables": 0.35,
                "structure": 0.15,
                "critical_columns": 0.10
            }

        final_confidence = sum(
            score_breakdown[k] * weights[k]
            for k in weights
        )

        # Ajustar con calidad del extractor si existe
        if quality:
            extractor_confidence = quality.get("confidence", 0.5)
            # Promedio entre nuestra validación y el extractor
            final_confidence = (final_confidence + extractor_confidence) / 2

        # Determinar si es válido
        min_threshold = self.MIN_CONFIDENCE + (0.1 if self.strict else 0)

        is_valid = final_confidence >= min_threshold and len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            confidence=final_confidence,
            warnings=warnings,
            errors=errors,
            score_breakdown=score_breakdown
        )

    def _validate_length(self, content: str, length: int) -> float:
        """
        Valida longitud del contenido. Retorna score 0-1.

        CLAVE: Documentos financieros deben tener contenido sustancial.
        39 líneas (GLM-OCR) no es aceptable para un balance.
        """
        # Contar líneas (muy útil para detectar extracciones pobres)
        lines = [line for line in content.split('\n') if line.strip()]
        line_count = len(lines)

        # Si tiene muy pocas líneas, penalizar fuerte
        if line_count < 10:
            return 0.0  # GLM-OCR con 39 líneas pero solo ~10 útiles
        elif line_count < 20:
            return 0.3  # Muy corto

        # Para documentos financieros, requerir más longitud
        if length >= 3000:
            return 1.0
        elif length >= 1500:
            return 0.9
        elif length >= 800:
            return 0.7
        elif length >= 400:
            return 0.5
        elif length >= 200:
            return 0.3
        else:
            return 0.0

    def _validate_corrupt_chars(self, content: str, length: int) -> float:
        """Valida caracteres corruptos. Retorna score 0-1."""
        if length == 0:
            return 0.0

        corrupt_count = 0
        for pattern in self.CORRUPT_PATTERNS:
            corrupt_count += content.count(pattern)

        ratio = corrupt_count / length

        if ratio < 0.001:
            return 1.0
        elif ratio < 0.005:
            return 0.8
        elif ratio < 0.01:
            return 0.5
        elif ratio < 0.02:
            return 0.3
        else:
            return 0.0

    def _validate_tables(self, content: str, content_lower: str, doc_type: str) -> float:
        """
        Valida presencia y formato de tablas. Retorna score 0-1.

        CLAVE: Distingue entre HTML crudo (malo) y Markdown limpio (bueno).
        """
        # Detectar HTML crudo no convertido - PENALIZACIÓN FUERTE
        html_tags = ["<div", "<table", "<th>", "<td>", "<tr>", "<span", "<p>", "<br"]
        has_raw_html = any(tag in content for tag in html_tags)

        if has_raw_html:
            # Si hay HTML crudo, asume que NO se convirtió a Markdown
            return 0.1

        # Verificar si hay tablas Markdown
        has_tables = "|" in content

        # Detectar filas de tabla Markdown
        table_rows = [line for line in content.split('\n') if '|' in line]
        table_count = len(table_rows)

        # Verificar formato correcto de tablas Markdown (debe tener separadores)
        has_separator = any("---" in row for row in table_rows)
        has_proper_tables = has_tables and has_separator

        if doc_type == "financial":
            # Documentos financieros DEBEN tener tablas Markdown bien formadas
            if not has_proper_tables:
                return 0.1  # Muy malo: documento financiero sin tablas

            # Más filas de tabla = mejor
            if table_count >= 20:
                return 1.0
            elif table_count >= 10:
                return 0.9
            elif table_count >= 5:
                return 0.7
            elif table_count >= 2:
                return 0.5
            else:
                return 0.3

        # Para no financieros, tablas son opcionales pero buenos
        if table_count >= 5:
            return 1.0
        elif table_count >= 2:
            return 0.8
        elif has_proper_tables:
            return 0.7
        elif has_tables:
            return 0.5  # Tiene pipes pero no separadores
        else:
            return 0.6  # Neutral si no hay tablas (puede ser texto plano)

    def _validate_structure(self, content: str) -> float:
        """
        Valida estructura general del documento. Retorna score 0-1.

        CLAVE: Detecta HTML crudo no convertido y penaliza fuertemente.
        """
        lines = content.split('\n')
        non_empty = [line.strip() for line in lines if line.strip()]

        if len(non_empty) == 0:
            return 0.0

        # PENALIZACIÓN POR HTML CRUDO - lo más importante
        html_indicators = [
            "<div", "</div>", "<span", "</span>", "<table", "</table>",
            "<th>", "</th>", "<td>", "</td>", "<tr>", "</tr>",
            "<p>", "</p>", "<br>", "<br/>", "&nbsp;"
        ]
        html_count = sum(content.lower().count(tag) for tag in html_indicators)

        if html_count >= 5:
            return 0.1  # HTML crudo = muy malo
        elif html_count >= 2:
            return 0.3  # Algo de HTML = malo

        # Verificar que no sea todo una sola línea
        if len(lines) < 3:
            return 0.3

        # Verificar proporción de líneas no vacías
        density = len(non_empty) / len(lines)
        if density < 0.3:
            return 0.4
        elif density > 0.7:
            return 1.0
        else:
            return 0.8

    def _detect_doc_type(self, content_lower: str) -> str:
        """Detecta tipo de documento basado en contenido."""
        financial_count = sum(1 for kw in self.FINANCIAL_KEYWORDS if kw in content_lower)

        if financial_count >= 3:
            return "financial"
        elif "balance" in content_lower or "boletin" in content_lower:
            return "financial"
        else:
            return "general"

    def _validate_critical_columns(self, content: str, doc_type: str) -> Dict[str, Any]:
        """
        Valida presencia de columnas críticas en tablas financieras.

        Esta validación es ESPECIALMENTE importante para distinguir entre
        modelos que capturan todas las columnas vs modelos que omiten algunas.

        Por ejemplo:
        - GLM-OCR tiene VARIACIONES (10 columnas totales)
        - Gemini 3 a veces omite VARIACIONES (8 columnas totales)

        Args:
            content: Contenido extraído
            doc_type: Tipo de documento detectado

        Returns:
            Dict con:
                - has_variations: bool
                - has_saldo_final: bool
                - estimated_column_count: int
                - missing_critical: List[str]
                - score: float (0-1)
        """
        result = {
            "has_variations": False,
            "has_saldo_final": False,
            "has_movimientos": False,
            "estimated_column_count": 0,
            "missing_critical": [],
            "score": 1.0,
        }

        content_upper = content.upper()

        # Verificar columnas críticas por nombre (funciona para cualquier formato)
        result["has_variations"] = "VARIACIONES" in content_upper
        result["has_saldo_final"] = "SALDO FINAL" in content_upper
        result["has_movimientos"] = "MOVIMIENTOS" in content_upper

        # Detectar formato de la tabla
        has_markdown_tables = "|" in content
        # GLM-OCR tiene "VARIACIONES" y "- CUENTA" o "-CUENTA" con líneas de datos
        has_glm_format = (content_upper.count("VARIACIONES") > 0 and
                         (content.count("- CUENTA") > 0 or content.count("-CUENTA") > 0) and
                         content_upper.count("DEBE HABER") > 0)

        # Estimar número de columnas
        if has_markdown_tables:
            # Formato Markdown: contar pipes en la línea de encabezado
            max_columns = 0
            for line in content.split('\n'):
                if '|' in line and ('CUENTA' in line.upper() or 'DESCRIPCION' in line.upper()):
                    col_count = line.count('|') - 1  # -1 porque count incluye los bordes
                    if col_count > max_columns:
                        max_columns = col_count
            result["estimated_column_count"] = max_columns

        elif has_glm_format:
            # Formato GLM-OCR: el encabezado indica las columnas
            # "- CUENTA DESCRIPCION SALDO INICIAL MOVIMIENTOS SALDO FINAL VARIACIONES"
            # "- DEBE HABER DEBE HABER DEBE HABER DEBE HABER"
            # Contar las palabras clave DEBE en el encabezado (cada par DEBE/HABER = 2 columnas)
            column_estimate = 0
            for line in content.split('\n'):
                line_upper = line.upper()
                if "CUENTA" in line_upper and "DESCRIPCION" in line_upper:
                    # Cada "DEBE" representa una columna (SU FIJO o DEBE)
                    # Pero en el sub-encabezado, DEBE aparece 5 veces (para 5 pares de columnas)
                    debe_count = line_upper.count("DEBE")
                    # Contar CUENTA y DESCRIPCION como 1 columna cada uno + cada par DEBE/HABER
                    column_estimate = 2 + (debe_count if "DEBE" in line_upper and "HABER" in line_upper else 0)
                    result["estimated_column_count"] = column_estimate
                    break

            # Si no se pudo calcular, asumir 10 (formato completo GLM: 1 CUENTA + 1 DESC + 4 pares de DEBE/HABER)
            if result["estimated_column_count"] == 0:
                result["estimated_column_count"] = 10

        # Detectar columnas faltantes (solo si no es formato GLM que ya las validó)
        if not has_glm_format:
            if not result["has_variations"]:
                result["missing_critical"].append("VARIACIONES")

            if not result["has_saldo_final"]:
                result["missing_critical"].append("SALDO FINAL")

            if not result["has_movimientos"]:
                result["missing_critical"].append("MOVIMIENTOS")

        # Calcular score basado en columnas faltantes y conteo total
        # Para balances financieros completos, esperamos al menos 8 columnas
        min_expected_columns = 8 if doc_type == "financial" else 4

        if result["estimated_column_count"] < min_expected_columns and not has_glm_format:
            result["missing_critical"].append(f"Solo {result['estimated_column_count']} columnas (mínimo {min_expected_columns})")

        # Penalty score:
        # - Sin columnas críticas faltantes: 1.0
        # - 1 columna faltante: 0.7
        # - 2+ columnas faltantes: 0.4
        # - Menos columnas que el mínimo: 0.2

        missing_count = len(result["missing_critical"])

        if result["estimated_column_count"] < min_expected_columns and not has_glm_format:
            # Penalizar solo si no es formato GLM (que tiene columnas pero sin pipes)
            result["score"] = 0.2
        elif missing_count == 0:
            result["score"] = 1.0
        elif missing_count == 1:
            result["score"] = 0.7
        elif missing_count == 2:
            result["score"] = 0.5
        else:
            result["score"] = 0.3

        # Bonus especial para GLM-OCR con VARIACIONES
        if has_glm_format and result["has_variations"]:
            result["score"] = 1.0

        return result

    def compare_extractions(
        self,
        results: List[Dict[str, Any]]
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Compara múltiples extracciones y devuelve la mejor.

        Args:
            results: Lista de resultados de diferentes modelos
                     Cada dict debe tener: {model, content, metadata, ...}

        Returns:
            (index_mejor, resultado_mejor)
        """
        if not results:
            return -1, {}

        scored_results = []
        for i, result in enumerate(results):
            if not result.get("success", False):
                continue

            content = result.get("content", "")
            quality = result.get("quality", {})

            # Validar
            validation = self.validate(content, quality)
            scored_results.append({
                "index": i,
                "model": result.get("model", "unknown"),
                "confidence": validation.confidence,
                "is_valid": validation.is_valid,
                "warnings": validation.warnings,
                "errors": validation.errors,
                "content_length": len(content),
                "cost": result.get("cost", 1.0),
                "duration": result.get("duration", 0)
            })

        if not scored_results:
            return -1, {}

        # Ordenar por:
        # 1. Validez (válidos primero)
        # 2. Confianza (mayor primero)
        # 3. Longitud de contenido (más es mejor)
        # 4. Costo (menor es mejor)
        scored_results.sort(
            key=lambda x: (
                -int(x["is_valid"]),      # Válidos primero (negado para invertir)
                -x["confidence"],      # Mayor confianza primero (negado)
                -x["content_length"],  # Más largo (negado)
                x["cost"]               # Menor costo
            )
        )

        # Retornar el mejor
        best_idx = scored_results[0]["index"]
        return best_idx, results[best_idx]


# ============================================================================
# FUNCIÓN DE CONVENIENCIA
# ============================================================================

def validate_extraction(
    content: str,
    quality: dict = None,
    strict: bool = False
) -> Tuple[bool, float, List[str]]:
    """
    Función de conveniencia para validar una extracción.

    Args:
        content: Contenido extraído
        quality: Metadata de calidad del extractor
        strict: Si True, usa umbrales más estrictos

    Returns:
        (is_valid, confidence, warnings)
    """
    validator = QualityValidator(strict=strict)
    result = validator.validate(content, quality)
    return result.is_valid, result.confidence, result.warnings
