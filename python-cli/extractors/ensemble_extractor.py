"""
extractors/ensemble_extractor.py

Extractor ensemble que combina múltiples modelos OCR con selección automática.

Estrategia Cascade (MIT/Stanford best practices):
1. GLM-OCR primero (60% de casos) → rápido, barato, especializado en tablas
2. Gemini 3 Flash fallback (30%) → mejor calidad, layouts complejos
3. Gemini 2.5 último recurso (10%) → más económico

@version 1.1.0
@created 2026-02-03
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from extractors.glm_ocr_extractor import GLMOCRExtractor
from extractors.vision_extractor import VisionExtractor
from extractors.glm_table_parser import GLMTableParser, has_variations_column, parse_glm_raw_to_markdown
from utils.quality_validator import QualityValidator, ValidationResult


@dataclass
class EnsembleResult:
    """Resultado de extracción ensemble."""
    model_used: str
    content: str
    title: str
    confidence: float
    is_valid: bool
    validation: ValidationResult
    all_results: List[Dict[str, Any]] = field(default_factory=list)
    cost: float = 0.0
    duration: float = 0.0

    def __str__(self) -> str:
        if self.is_valid:
            return f"✓ {self.model_used} (confianza: {self.confidence:.1%})"
        return f"⚠ {self.model_used} (confianza: {self.confidence:.1%}, bajo threshold)"


class EnsembleExtractor:
    """
    Extractor ensemble con estrategia cascade + quality scoring.

    Usa QualityValidator para evaluar resultados y seleccionar el mejor.

    Estrategia Cascade:
        1. Probar GLM-OCR (rápido, barato, especializado en tablas)
        2. Si confianza < threshold → probar Gemini 3 Flash
        3. Si aún baja → probar Gemini 2.5 (backup económico)
        4. Si todos fallan → devolver el mejor disponible
    """

    # Precios por millón de tokens (USD)
    PRICING = {
        "glm-ocr": {"input": 0.03, "output": 0.03},
        "gemini-3": {"input": 0.50, "output": 3.00},
        "gemini-2.5": {"input": 0.10, "output": 0.40},
    }

    def __init__(
        self,
        strategy: str = "cascade",
        min_confidence: float = 0.6,
        verbose: bool = True,
        chunk_size: int = 15
    ):
        """
        Args:
            strategy: "cascade" (uno tras otro) o "parallel" (todos a la vez)
            min_confidence: Confianza mínima para aceptar resultado sin probar más
            verbose: Mostrar logs de progreso
            chunk_size: Páginas por chunk para PDFs grandes
        """
        self.strategy = strategy
        self.min_confidence = min_confidence
        self.verbose = verbose
        self.chunk_size = chunk_size
        self.validator = QualityValidator()

        # Inicializar extractores
        self.glm_extractor = GLMOCRExtractor()

        # Crear extractores Gemini separados con diferentes modelos
        # Nota: Usamos Gemini 3 Flash Preview como principal (mejor calidad)
        self.gemini_3_extractor = VisionExtractor(
            model_id="google/gemini-3-flash-preview"
        )
        # Gemini 2.5 como backup (más económico pero menos preciso)
        self.gemini_25_extractor = VisionExtractor(
            model_id="google/gemini-2.5-flash-lite-preview-09-2025"
        )

    async def extract(
        self,
        pdf_path: Path,
        pdf_content: bytes = None
    ) -> EnsembleResult:
        """
        Extrae PDF usando estrategia ensemble.

        Args:
            pdf_path: Ruta al archivo PDF
            pdf_content: Contenido binario del PDF (si None, se lee del archivo)

        Returns:
            EnsembleResult con el mejor resultado encontrado
        """
        # Leer contenido si no se proporcionó
        if pdf_content is None:
            pdf_content = pdf_path.read_bytes()

        if self.strategy == "cascade":
            return await self._extract_cascade(pdf_path, pdf_content)
        else:
            return await self._extract_parallel(pdf_path, pdf_content)

    async def _extract_cascade(
        self,
        pdf_path: Path,
        pdf_content: bytes
    ) -> EnsembleResult:
        """
        Estrategia Cascade: probar modelos en orden hasta encontrar uno bueno.

        Orden: GLM-OCR → Gemini 3 Flash → Gemini 2.5

        Args:
            pdf_path: Ruta al PDF
            pdf_content: Contenido binario

        Returns:
            EnsembleResult con el mejor resultado
        """
        start_time = time.time()

        all_results = []
        models_to_try = [
            ("glm-ocr", self.glm_extractor),
            ("gemini-3", self.gemini_3_extractor),
            ("gemini-2.5", self.gemini_25_extractor),
        ]

        for model_name, extractor in models_to_try:
            if self.verbose:
                print(f"[Ensemble] 🔍 Probando {model_name}...")

            try:
                result = await self._try_extractor(
                    model_name, extractor, pdf_path, pdf_content, start_time
                )
                all_results.append(result)

                # Si falló completamente, continuar al siguiente
                if result.get("error"):
                    if self.verbose:
                        print(f"[Ensemble] ⚠️  {model_name} falló: {result['error']}")
                    continue

                # Validar calidad
                validation = result["validation"]

                if self.verbose:
                    status = "✅" if validation.is_valid else "⚠️"
                    print(f"[Ensemble] {status} {model_name}: confianza {validation.confidence:.1%}")

                # Si pasa el threshold, retornar inmediatamente
                if validation.is_valid and validation.confidence >= self.min_confidence:
                    if self.verbose:
                        print(f"[Ensemble] 🎯 {model_name} aceptado (confianza {validation.confidence:.1%} >= {self.min_confidence:.1%})")

                    return EnsembleResult(
                        model_used=model_name,
                        content=result["content"],
                        title=result["title"],
                        confidence=validation.confidence,
                        is_valid=True,
                        validation=validation,
                        all_results=all_results,
                        cost=self._calculate_cost(all_results),
                        duration=time.time() - start_time,
                    )

            except Exception as e:
                if self.verbose:
                    print(f"[Ensemble] ❌ {model_name} excepción: {e}")
                all_results.append({
                    "model": model_name,
                    "error": str(e),
                })

        # Nadie pasó el threshold, devolver el mejor válido
        valid_results = [
            r for r in all_results
            if "validation" in r and r["validation"].is_valid
        ]

        if valid_results:
            best = max(valid_results, key=lambda x: x["validation"].confidence)

            if self.verbose:
                print(f"[Ensemble] ⚠️  Nadie llegó al threshold, usando mejor fallback:")
                print(f"[Ensemble]    → {best['model']} (confianza: {best['validation'].confidence:.1%})")

            return EnsembleResult(
                model_used=best["model"],
                content=best["content"],
                title=best["title"],
                confidence=best["validation"].confidence,
                is_valid=False,  # No llegó al threshold
                validation=best["validation"],
                all_results=all_results,
                cost=self._calculate_cost(all_results),
                duration=time.time() - start_time,
            )

        # Todos fallaron
        if self.verbose:
            print(f"[Ensemble] ❌ Todos los modelos fallaron")

        return EnsembleResult(
            model_used="none",
            content="",
            title="",
            confidence=0.0,
            is_valid=False,
            validation=ValidationResult(
                is_valid=False,
                confidence=0.0,
                warnings=[],
                errors=["Todos los modelos fallaron"],
                score_breakdown={}
            ),
            all_results=all_results,
            cost=0.0,
            duration=time.time() - start_time,
        )

    async def _extract_parallel(
        self,
        pdf_path: Path,
        pdf_content: bytes
    ) -> EnsembleResult:
        """
        Estrategia Parallel: ejecutar todos y elegir el mejor.

        Args:
            pdf_path: Ruta al PDF
            pdf_content: Contenido binario

        Returns:
            EnsembleResult con el mejor resultado
        """
        import asyncio

        start_time = time.time()

        if self.verbose:
            print(f"[Ensemble] 🔄 Ejecutando todos los modelos en paralelo...")

        # Ejecutar todos en paralelo
        tasks = [
            self._try_extractor("glm-ocr", self.glm_extractor, pdf_path, pdf_content, start_time),
            self._try_extractor("gemini-3", self.gemini_3_extractor, pdf_path, pdf_content, start_time),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Procesar resultados
        all_results = []
        for r in results:
            if isinstance(r, Exception):
                continue
            all_results.append(r)

        # Seleccionar el mejor
        valid_results = [r for r in all_results if r.get("validation") and r["validation"].is_valid]

        if valid_results:
            best = max(valid_results, key=lambda x: x["validation"].confidence)

            if self.verbose:
                print(f"[Ensemble] 🏆 Mejor modelo: {best['model']} (confianza: {best['validation'].confidence:.1%})")

            return EnsembleResult(
                model_used=best["model"],
                content=best["content"],
                title=best["title"],
                confidence=best["validation"].confidence,
                is_valid=best["validation"].confidence >= self.min_confidence,
                validation=best["validation"],
                all_results=all_results,
                cost=self._calculate_cost(all_results),
                duration=time.time() - start_time,
            )

        # Fallback al mejor disponible
        if all_results:
            best = max(all_results, key=lambda x: x["validation"].confidence)
            return EnsembleResult(
                model_used=best["model"],
                content=best["content"],
                title=best["title"],
                confidence=best["validation"].confidence,
                is_valid=False,
                validation=best["validation"],
                all_results=all_results,
                cost=self._calculate_cost(all_results),
                duration=time.time() - start_time,
            )

        # Todos fallaron
        raise ValueError("Todos los modelos fallaron en el ensemble")

    async def _try_extractor(
        self,
        model_name: str,
        extractor,
        pdf_path: Path,
        pdf_content: bytes,
        start_time: float
    ) -> Dict[str, Any]:
        """
        Intenta extraer con un extractor específico.

        Args:
            model_name: Nombre del modelo ("glm-ocr", "gemini-2.5", "gemini-3")
            extractor: Instancia del extractor (GLMOCRExtractor o VisionExtractor)
            pdf_path: Ruta al PDF
            pdf_content: Contenido binario
            start_time: Tiempo de inicio

        Returns:
            Dict con: model, title, content, validation, duration, tokens
        """
        try:
            # Detectar tipo de extractor
            if isinstance(extractor, GLMOCRExtractor):
                # GLM-OCR es síncrono
                title, content, quality = extractor.extract_pdf(
                    pdf_content,
                    url=str(pdf_path),
                    municipio="Ensemble"
                )

                # Estimar tokens (GLM-OCR no reporta)
                tokens = len(content) // 4 if content else 0

                # ========================================
                # PROCESAR CONTENIDO GLM-OCR
                # ========================================
                # GLM-OCR devuelve un formato propietario con guiones.
                # Si tiene VARIACIONES pero no formato Markdown, convertirlo.
                if has_variations_column(content) and "|" not in content:
                    # Convertir formato GLM a Markdown
                    markdown_content = parse_glm_raw_to_markdown(content)

                    if self.verbose and markdown_content:
                        print(f"[Ensemble] 📊 GLM-OCR convertido a Markdown ({len(markdown_content)} chars)")

                    # Actualizar contenido con la versión Markdown
                    if markdown_content:
                        content = markdown_content
                        quality["glm_converted_to_md"] = True

            else:
                # VisionExtractor es asíncrono
                title, content, quality = await extractor.extract_pdf(
                    pdf_content,
                    url=str(pdf_path),
                    municipio="Ensemble",
                    extract_tables=True
                )

                # Extraer tokens de quality
                input_tokens = quality.get("input_tokens", 0)
                output_tokens = quality.get("output_tokens", 0)
                tokens = input_tokens + output_tokens

            if not content:
                return {
                    "model": model_name,
                    "error": "No se extrajo contenido",
                    "validation": ValidationResult(
                        is_valid=False,
                        confidence=0.0,
                        warnings=[],
                        errors=["No se extrajo contenido"],
                        score_breakdown={}
                    ),
                }

            validation = self.validator.validate(content, quality)

            return {
                "model": model_name,
                "title": title,
                "content": content,
                "quality": quality,
                "validation": validation,
                "duration": time.time() - start_time,
                "tokens": tokens,
            }

        except Exception as e:
            return {
                "model": model_name,
                "error": str(e),
                "validation": ValidationResult(
                    is_valid=False,
                    confidence=0.0,
                    warnings=[],
                    errors=[str(e)],
                    score_breakdown={}
                ),
            }

    def _calculate_cost(self, results: List[Dict]) -> float:
        """Calcula costo total de todos los intentos."""
        total_cost = 0.0

        for r in results:
            model = r["model"]
            tokens = r.get("tokens", 0)

            # GLM-OCR no reporta tokens, estimar
            if model == "glm-ocr":
                # Estimar basado en longitud de contenido
                content_len = len(r.get("content", ""))
                # GLM-OCR cobra $0.03/1M para input+output
                estimated_tokens = content_len / 4  # ~4 chars por token
                total_cost += (estimated_tokens / 1_000_000) * self.PRICING[model]["input"]
            else:
                # Gemini cobra separado input/output
                # Asumir 80% input, 20% output
                input_cost = (tokens * 0.8 / 1_000_000) * self.PRICING[model]["input"]
                output_cost = (tokens * 0.2 / 1_000_000) * self.PRICING[model]["output"]
                total_cost += input_cost + output_cost

        return total_cost

    def print_summary(self, result: EnsembleResult) -> None:
        """Imprime resumen del resultado ensemble."""
        print(f"\n{'='*60}")
        print("RESUMEN ENSEMBLE")
        print(f"{'='*60}")
        print(f"Modelo usado: {result.model_used}")
        print(f"Válido: {'Sí' if result.is_valid else 'No (bajo threshold)'}")
        print(f"Confianza: {result.confidence:.1%}")
        print(f"Duración: {result.duration:.2f}s")
        print(f"Costo estimado: ${result.cost:.6f}")

        if result.validation.warnings:
            print(f"Warnings: {', '.join(result.validation.warnings[:3])}")

        if result.validation.errors:
            print(f"Errores: {', '.join(result.validation.errors[:3])}")

        print(f"\nModelos probados: {len(result.all_results)}")
        for r in result.all_results:
            model = r["model"]
            if "validation" in r:
                conf = r["validation"].confidence
                valid = "✓" if r["validation"].is_valid else "✗"
                print(f"  {valid} {model}: {conf:.1%}")
            else:
                print(f"  ✗ {model}: Error")

        print(f"{'='*60}\n")

    def export_to_csv(
        self,
        result: EnsembleResult,
        output_path: Path = None
    ) -> Optional[str]:
        """
        Exporta el contenido a CSV si es posible.

        Intenta extraer tablas del contenido y exportarlas a CSV.
        Para GLM-OCR, usa el parser específico. Para Markdown estándar,
        intenta convertir tablas Markdown a CSV.

        Args:
            result: Resultado del ensemble
            output_path: Ruta donde guardar el CSV (si None, retorna el contenido)

        Returns:
            Contenido CSV si se pudo exportar, None si no hay tablas
        """
        from extractors.glm_table_parser import parse_glm_raw, GLMTableParser

        content = result.content
        if not content:
            return None

        # Si el contenido tiene formato GLM-OCR, usar el parser específico
        if has_variations_column(content) and content.count("- ") > 5:
            try:
                parse_result = parse_glm_raw(content)
                if parse_result.total_rows > 0:
                    parser = GLMTableParser()
                    csv_content = parser.to_csv(parse_result.rows)

                    if output_path:
                        output_path.write_text(csv_content, encoding='utf-8')
                        if self.verbose:
                            print(f"[Ensemble] 📄 CSV exportado a {output_path}")
                    else:
                        return csv_content
            except Exception as e:
                if self.verbose:
                    print(f"[Ensemble] ⚠️  Error exportando GLM a CSV: {e}")

        return None


# ============================================================================
# FUNCIÓN DE CONVENIENCIA
# ============================================================================

async def extract_with_ensemble(
    pdf_path: Path,
    strategy: str = "cascade",
    min_confidence: float = 0.6,
    verbose: bool = True
) -> EnsembleResult:
    """
    Extrae PDF usando ensemble de modelos.

    Args:
        pdf_path: Ruta al archivo PDF
        strategy: "cascade" o "parallel"
        min_confidence: Confianza mínima para aceptar resultado
        verbose: Mostrar logs

    Returns:
        EnsembleResult con el mejor resultado

    Example:
        >>> result = await extract_with_ensemble(Path("documento.pdf"))
        >>> if result.is_valid:
        ...     print(f"Extraído con {result.model_used}")
        ...     print(result.content[:500])
    """
    extractor = EnsembleExtractor(
        strategy=strategy,
        min_confidence=min_confidence,
        verbose=verbose
    )
    return await extractor.extract(pdf_path)
