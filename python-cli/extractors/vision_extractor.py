#!/usr/bin/env python3
"""
extractors/vision_extractor.py

Wrapper para Vision API de OpenRouter.
Extrae texto de PDFs con soporte especial para documentos con columnas.

@version 3.0.0
@created 202-01-29
"""

import asyncio
import base64
import tempfile
import os
from typing import Optional, Tuple
from pathlib import Path
from rich.console import Console

console = Console()


# ============================================================================
# EXCEPCIONES
# ============================================================================

class CreditExhaustedError(Exception):
    """Excepción lanzada cuando se detecta error de crédito/rate limit."""
    pass


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Modelos Vision API disponibles
VISION_MODEL_ID = "qwen/qwen3-vl-235b-a22b-instruct"  # Mejor OCR (paga)
# VISION_MODEL_ID = "nvidia/nemotron-nano-12b-v2-vl:free"  # Gratis


# ============================================================================
# VISION EXTRACTOR
# ============================================================================

class VisionExtractor:
    """
    Extractor de texto usando Vision API de OpenRouter.

    Optimizado para documentos con:
    - Columnas múltiples (boletines oficiales)
    - Tablas complejas (balances, presupuestos)
    - Layouts irregulares
    """

    def __init__(self, model_id: str = VISION_MODEL_ID):
        """
        Args:
            model_id: ID del modelo en OpenRouter
        """
        self.model_id = model_id
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")

    async def extract_pdf(
        self,
        pdf_content: bytes,
        url: str = "",
        municipio: str = "Desconocido",
        max_pages: Optional[int] = None,
        extract_tables: bool = False
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto completo de un PDF usando Vision API.

        Args:
            pdf_content: Contenido binario del PDF
            url: URL de origen (para logging)
            municipio: Nombre del municipio
            max_pages: Límite de páginas (None = todas)
            extract_tables: Si True, usa prompt optimizado para tablas financieras

        Returns:
            (title, content, quality) - Título extraído, contenido completo, metadata de calidad
        """
        from utils.vision_rate_limiter import get_rate_limiter
        from openai import AsyncOpenAI

        # Verificar rate limit
        limiter = get_rate_limiter()
        if not limiter.check_and_request():
            raise RuntimeError("Límite diario de Vision API alcanzado")

        # Convertir PDF a imágenes
        images = await self._pdf_to_images(pdf_content)
        if not images:
            return "", "", {"confidence": 0, "quality": "failed"}

        max_pages = max_pages or len(images)

        # Crear cliente
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        # Extraer texto de cada página
        full_text = []
        for i, image_base64 in enumerate(images[:max_pages]):
            console.print(f"[dim]  → Página {i + 1}/{len(images)}...[/dim]")

            text = await self._extract_page(image_base64, client, extract_tables=extract_tables)
            if text:
                full_text.append(text)

        await client.close()

        # Limpiar y unir
        content = "\n\n".join(full_text)

        # Extraer título de la primera página
        title = self._extract_title(content)

        # Evaluar calidad
        quality = self._assess_quality(content, len(images), max_pages)

        return title, content, quality

    async def _pdf_to_images(self, pdf_content: bytes) -> list[str]:
        """Convierte PDF a lista de imágenes base64."""
        try:
            import pdf2image
            from io import BytesIO
        except ImportError:
            console.print("[red]❌ Instala: pip install pdf2image[/red]")
            return []

        images = []
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_content)
                tmp_path = tmp.name

            pillow_images = pdf2image.convert_from_path(
                tmp_path,
                dpi=200,
                fmt='png'
            )

            for img in pillow_images:
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                images.append(base64.b64encode(buffer.getvalue()).decode('utf-8'))

            os.unlink(tmp_path)

        except Exception as e:
            console.print(f"[red]Error convirtiendo PDF: {e}[/red]")
            return []

        return images

    async def _extract_page(self, image_base64: str, client, extract_tables: bool = False) -> str:
        """Extrae texto de una página usando Vision API.

        Args:
            image_base64: Imagen codificada en base64
            client: Cliente OpenAI
            extract_tables: Si True, usa prompt optimizado para tablas financieras
        """

        # Prompt optimizado para tablas financieras (balances, presupuestos, etc.)
        if extract_tables:
            prompt = (
                "Eres un extractor de datos financieros experto. Extrae TODO el contenido de esta imagen:\n\n"
                "**PRIMERO: CABECERA DEL DOCUMENTO** (IMPORTANTE)\n"
                "- Extrae TODA la información de la cabecera ANTES de las tablas\n"
                "- Incluye: institución, municipio, ejercicio, periodo (Desde el... hasta el...), fecha de generación\n"
                "- Incluye el tipo de documento (BALANCE DE SUMAS Y SALDOS, BALANCE DE TESORERIA, etc.)\n"
                "- NO omitas la cabecera\n\n"
                "**SEGUNDO: TABLAS** (prioridad máxima)\n"
                "- Si hay tablas con datos contables/financieros, extráelas en formato Markdown\n"
                "- Usa el carácter | para separar columnas\n"
                "- Incluye fila de encabezado separadora con |---|---|---|\n"
                "- Ejemplo: | Cuenta | Debe | Haber |\\n|---|---|---|\\n| Caja | 1000 | 500 |\n\n"
                "**FORMATO DE COLUMNAS**:\n"
                "- Si el documento tiene 2 columnas de texto, lee IZQUIERDA completa primero, luego DERECHA\n\n"
                "**REGLAS**:\n"
                "- Mantén números, fechas y símbolos exactos (., $ %)\n"
                "- NO resumas ni interpretes\n"
                "- Devuelve TODO el contenido, PRIMERO la cabecera, LUEGO las tablas"
            )
        else:
            # Prompt para documentos legales con columnas
            prompt = (
                "Extrae TODO el texto de esta imagen de un documento legal. "
                "IMPORTANTE: Este documento puede tener DOS COLUMNAS. "
                "Debes leer la COLUMNA IZQUIERDA completa primero, luego la COLUMNA DERECHA completa. "
                "NO mezcles el texto entre columnas. "
                "Mantén el formato original con números, fechas y artículos. "
                "NO resumas, NO interpretes, SOLO extrae el texto literalmente."
            )

        try:
            response = await client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": f"data:image/png;base64,{image_base64}"
                            }
                        ]
                    }
                ],
                max_tokens=8192,
                temperature=0.0,
            )

            # Extraer y trackear uso de tokens
            content = response.choices[0].message.content or ""

            # Registrar en LLM tracker
            try:
                from utils.llm_tracker import extract_token_usage, record_llm_call
                input_tokens, output_tokens = extract_token_usage(response)

                if input_tokens > 0 or output_tokens > 0:
                    task = "vision_tables" if extract_tables else "vision"
                    record_llm_call(
                        model=self.model_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        task=task
                    )
            except Exception as track_err:
                # No fallar si el tracker falla
                pass

            return content

        except Exception as e:
            error_str = str(e).lower()
            error_msg = str(e)

            # Detectar errores de crédito/limite de OpenRouter
            credit_error_patterns = [
                "insufficient", "credit", "quota", "balance",
                "429", "rate limit", "limit", "exceeded"
            ]

            if any(p in error_str for p in credit_error_patterns):
                console.print("\n[bold red]⚠️⚠️⚠️ ERROR DE CRÉDITO/RATE LIMIT DETECTADO ⚠️⚠️⚠️[/bold red]\n")
                console.print(f"[red]Error: {error_msg}[/red]")

                # Emitir beep persistente (macOS/Linux)
                try:
                    import sys
                    if sys.platform == "darwin":
                        # macOS: afplay para beep continuo
                        import subprocess
                        for _ in range(5):
                            subprocess.run(["tput", "bel"])
                    else:
                        # Linux/Windows: print bell character
                        print('\a\a\a\a\a')
                except Exception:
                    print('\a\a\a\a\a')  # Fallback

                # Lanzar excepción específica para detener el scraper
                raise CreditExhaustedError(f"CRÉDITOS AGOTADOS: {error_msg}")

            console.print(f"[red]Error en página: {e}[/red]")
            return ""

    def _extract_title(self, content: str) -> str:
        """Extrae un título del contenido."""
        lines = content.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Limpiar caracteres corruptos comunes
                line = line.replace("´", "")
                return line[:100]

        return "Extraído con Vision API"

    def _assess_quality(self, content: str, total_pages: int, processed: int) -> dict:
        """Evalúa la calidad de la extracción."""
        if not content:
            return {"confidence": 0, "quality": "failed"}

        score = 1.0
        warnings = []

        # Longitud mínima
        if len(content) < 100:
            score -= 0.5
            warnings.append("texto_corto")

        # Caracteres corruptos
        corrupt_count = content.count("´")
        if corrupt_count > 10:
            score -= min(0.3, corrupt_count * 0.01)
            warnings.append(f"acentos_rotos:{corrupt_count}")

        # Palabras clave legales
        legal_words = ['articulo', 'ordinanza', 'decreto', 'resolucion', 'sancion',
                       'comuniquese', 'departamento', 'ejecutivo']
        legal_count = sum(1 for word in legal_words if word.lower() in content.lower())

        if legal_count < 2 and len(content) > 500:
            score -= 0.2
            warnings.append("sin_palabras_legales")

        # Determinar nivel
        if score >= 0.8:
            quality = "excellent"
        elif score >= 0.6:
            quality = "good"
        elif score >= 0.4:
            quality = "fair"
        else:
            quality = "poor"

        return {
            "confidence": max(0, score),
            "quality": quality,
            "warnings": warnings[:5],
            "extraction_method": "vision_api_bulletin",
            "pages_processed": processed,
            "total_pages": total_pages
        }


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

async def extract_bulletin_with_vision(
    content: bytes,
    url: str = "",
    municipio: str = "Desconocido",
    extract_tables: bool = False
) -> Optional[Tuple[str, str, dict]]:
    """
    Extrae un boletín usando Vision API con prompt especial para columnas.

    Wrapper para uso rápido. Procesa TODAS las páginas del PDF.

    Args:
        content: Contenido binario del PDF
        url: URL de origen
        municipio: Nombre del municipio
        extract_tables: Si True, usa prompt optimizado para tablas financieras

    Returns:
        (title, content, quality) o None si falla
    """
    extractor = VisionExtractor()

    try:
        return await extractor.extract_pdf(content, url, municipio, extract_tables=extract_tables)
    except Exception as e:
        console.print(f"[red]Error en extracción Vision: {e}[/red]")
        return None


def extract_tables_as_markdown(text: str) -> list[str]:
    """
    Detecta y extrae tablas del texto, convirtiéndolas a Markdown.

    Args:
        text: Texto que puede contener tablas

    Returns:
        Lista de tablas en formato Markdown
    """
    import re

    tables = []
    lines = text.split('\n')
    current_table = []
    in_table = False

    for line in lines:
        # Detectar inicio de tabla por separador |
        if '|' in line and line.strip():
            # Detectar si es un encabezado o fila de datos
            cols = line.count('|')
            if cols >= 3:  # Al menos 3 columnas
                in_table = True
                current_table.append(line)
            elif in_table:
                # Fin de la tabla
                in_table = False
                if current_table:
                    tables.append("\n".join(current_table))
                current_table = []
        elif in_table and line.strip() == "":
            # Fin de tabla por línea vacía
            in_table = False
            if current_table:
                tables.append("\n".join(current_table))
            current_table = []

    # Última tabla si quedó pendiente
    if current_table:
        tables.append("\n".join(current_table))

    return tables


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    import httpx

    async def test():
        url = "https://boletin.casares.gob.ar/archivos_boletin_oficial/boletin_oficial_31.pdf"

        console.print("[cyan]📥 Descargando PDF de prueba...[/cyan]")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                console.print(f"[red]❌ Error: {response.status_code}[/red]")
                return

            result = await extract_bulletin_with_vision(
                response.content,
                url,
                municipio="Casares"
            )

            if result:
                title, content, quality = result
                console.print(f"\n[bold green]✅ EXTRACCIÓN COMPLETADA[/bold green]")
                console.print(f"Título: {title[:80]}...")
                console.print(f"Longitud: {len(content):,} caracteres")
                console.print(f"Calidad: {quality['confidence']:.1%} ({quality['quality']})")
            else:
                console.print("[red]❌ Falló la extracción[/red]")

    asyncio.run(test())
