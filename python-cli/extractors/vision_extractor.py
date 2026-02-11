#!/usr/bin/env python3
"""
extractors/vision_extractor.py

Wrapper para Vision API de OpenRouter.
Extrae texto de PDFs con soporte especial para documentos con columnas.

@version 4.0.0
@created 202-01-29
@updated 2026-02-02 - File API para procesar PDF completo en 1 llamada
"""

import asyncio
import base64
import hashlib
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


class LargePDFWarning(Warning):
    """Advertencia para PDFs grandes que pueden requerir procesamiento especial."""
    pass


# ============================================================================
# UTILIDADES
# ============================================================================

def get_pdf_page_count(pdf_content: bytes) -> int:
    """
    Retorna el número de páginas de un PDF sin procesarlo.

    Útil para detectar PDFs grandes antes de consumir tokens.

    Args:
        pdf_content: Contenido binario del PDF

    Returns:
        Número de páginas (0 si falla)
    """
    import io
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return 0

    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        return len(pdf_reader.pages)
    except Exception:
        return 0


def get_pdf_size_info(pdf_content: bytes) -> dict:
    """
    Retorna información sobre el tamaño de un PDF.

    Args:
        pdf_content: Contenido binario del PDF

    Returns:
        Dict con keys: size_bytes, size_mb, page_count, is_large
    """
    size_bytes = len(pdf_content)
    page_count = get_pdf_page_count(pdf_content)

    return {
        "size_bytes": size_bytes,
        "size_mb": size_bytes / (1024 * 1024),
        "page_count": page_count,
        "is_large": page_count > 50 or size_bytes > 2 * 1024 * 1024,  # >50 pág o >2MB
        "is_very_large": page_count > 100 or size_bytes > 4 * 1024 * 1024,  # >100 pág o >4MB
    }


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Modelos para extracción de PDFs
# Modelo GRATIS para extracción normal (File API + chunks)
# NOTA: google/gemini-2.0-flash-exp:free ya no existe en OpenRouter (404)
# Usamos un modelo económico como alternativa
FREE_VISION_MODEL = "google/gemini-2.5-flash-lite-preview-09-2025"

# Modelo PREMIUM para casos especiales (vision chunks - columnas correctas)
PREMIUM_VISION_MODEL = "google/gemini-2.5-flash-lite-preview-09-2025"

# Modelo Vision API por defecto - se lee desde config/models.yaml
def _get_default_vision_model() -> str:
    """Retorna el modelo Vision API por defecto desde models.yaml."""
    try:
        from utils.llm_tracker import get_default_model
        model = get_default_model("vision")
        return model or PREMIUM_VISION_MODEL
    except Exception:
        return PREMIUM_VISION_MODEL

VISION_MODEL_ID = _get_default_vision_model()

# Motor de procesamiento de PDFs
PDF_ENGINE = os.getenv("PDF_ENGINE", "auto")  # "auto", "free", "vision-chunks", "images", "glm-ocr"


# ============================================================================
# VISION EXTRACTOR
# ============================================================================

class VisionExtractor:
    """
    Extractor de texto usando Vision API de OpenRouter y GLM-OCR.

    Optimizado para documentos con:
    - Columnas múltiples (boletines oficiales)
    - Tablas complejas (balances, presupuestos)
    - Layouts irregulares

    Estrategia de 4 niveles:
    - Nivel 0: GLM-OCR (especializado en tablas financieras) -> PDF_ENGINE="glm-ocr"
    - Nivel 1: File API con modelo GRATIS (primer intento)
    - Nivel 2: Chunks con modelo GRATIS (error 413)
    - Nivel 3: Vision Chunks con modelo PREMIUM (casos especiales)
    """

    # Modelo GRATIS para extracción normal (File API + chunks)
    FREE_VISION_MODEL = FREE_VISION_MODEL

    # Modelo PREMIUM para casos especiales (vision chunks - columnas correctas)
    PREMIUM_VISION_MODEL = PREMIUM_VISION_MODEL

    def __init__(self, model_id: str = VISION_MODEL_ID, pdf_engine: str = None):
        """
        Args:
            model_id: ID del modelo en OpenRouter
            pdf_engine: Motor de procesamiento ("auto", "free", "vision-chunks", "images")
        """
        self.model_id = model_id
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.pdf_engine = pdf_engine or PDF_ENGINE

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")

    async def extract_pdf(
        self,
        pdf_content: bytes,
        url: str = "",
        municipio: str = "Desconocido",
        max_pages: Optional[int] = None,
        extract_tables: bool = False,
        pdf_engine: str = None
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto completo de un PDF usando Vision API o GLM-OCR.

        Estrategia de 4 niveles:
        - "glm-ocr": GLM-OCR API (especializado en tablas financieras)
        - "auto": Intenta Nivel 1 → Nivel 2 → Nivel 3 si falla
        - "free": Solo Nivel 1 y 2 (ambos GRATIS)
        - "vision-chunks": Nivel 3 directamente (casos especiales)
        - "images": Método legacy (página por página)

        Args:
            pdf_content: Contenido binario del PDF
            url: URL de origen (para logging)
            municipio: Nombre del municipio
            max_pages: Límite de páginas (None = todas)
            extract_tables: Si True, usa prompt optimizado para tablas financieras
            pdf_engine: Motor de procesamiento

        Returns:
            (title, content, quality) - Título extraído, contenido completo, metadata de calidad
        """
        from utils.vision_rate_limiter import get_rate_limiter

        # Verificar rate limit
        limiter = get_rate_limiter()
        if not limiter.check_and_request():
            raise RuntimeError("Límite diario de Vision API alcanzado")

        # Elegir motor de procesamiento
        engine = pdf_engine or self.pdf_engine or "auto"

        # NIVEL 4: GLM-OCR (especializado en tablas financieras)
        if engine == "glm-ocr":
            console.print("[cyan]🔍 Modo GLM-OCR (especializado en tablas)[/cyan]")
            return await self._extract_pdf_with_glm_ocr(
                pdf_content, url, municipio, extract_tables
            )

        # NIVEL 3: Casos especiales (solo cuando se solicita explícitamente)
        if engine == "vision-chunks":
            console.print("[yellow]⚠ Modo VISION CHUNKS (usa modelo PREMIUM)[/yellow]")
            return await self._extract_pdf_as_image_chunks(
                pdf_content, url, municipio, extract_tables
            )

        # NIVEL 1 y 2: Gratis con fallback automático
        if engine in ["auto", "free"]:
            try:
                console.print("[cyan]📄 Nivel 1: File API (modelo GRATIS)[/cyan]")
                return await self._extract_pdf_as_file(
                    pdf_content, url, municipio, extract_tables, use_free_model=True
                )
            except Exception as e:
                error_str = str(e).lower()

                # Error de crédito → repropagar
                if any(p in error_str for p in ["insufficient", "credit", "quota"]):
                    raise

                # Error de tamaño (413) → Nivel 2
                if any(p in error_str for p in ["413", "payload too large", "too large"]):
                    console.print("[yellow]→ PDF demasiado grande → Nivel 2[/yellow]")
                    return await self._extract_pdf_as_chunks(
                        pdf_content, url, municipio, extract_tables, use_free_model=True
                    )

                # Otro error → si es "auto", intentar Nivel 3
                if engine == "auto":
                    console.print(f"[yellow]File API falló: {e}[/yellow]")
                    console.print("[yellow]→ Intentando Nivel 3 (Vision Chunks)...[/yellow]")
                    return await self._extract_pdf_as_image_chunks(
                        pdf_content, url, municipio, extract_tables
                    )
                raise

        # Método legacy (imágenes página por página)
        return await self._extract_pdf_as_images(
            pdf_content, url, municipio, max_pages, extract_tables
        )

    async def _extract_pdf_as_file(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str,
        extract_tables: bool,
        use_free_model: bool = True
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto usando OpenRouter File API - UNA llamada para todo el PDF.

        Estrategia:
        1. PRIMERO intentar con URL (si es http/https) - sin límite de tamaño
        2. Si falla, intentar con base64
        3. Si falla con error 413, NO hacer fallback a imágenes (muy caro)

        Args:
            use_free_model: Si True, usa modelo GRATIS; si False, usa modelo actual

        Usa el motor 'pdf-text' que es GRATIS para PDFs con texto.
        """
        from openai import AsyncOpenAI

        # Elegir modelo según configuración
        model_id = self.FREE_VISION_MODEL if use_free_model else self.model_id

        pdf_filename = url.split('/')[-1] if url else "documento.pdf"

        # Construir prompt según tipo de extracción
        if extract_tables:
            prompt = self._get_tables_prompt()
        else:
            prompt = (
                "Extrae TODO el texto de este documento PDF. "
                "Si el documento tiene DOS COLUMNAS, lee la IZQUIERDA completa primero, luego la DERECHA completa. "
                "NO mezcles el texto entre columnas. "
                "Mantén el formato original con números, fechas y artículos. "
                "NO resumas, NO interpretes, SOLO extrae el texto literalmente."
            )

        # Estrategia 1: Intentar con URL si es una URL HTTP válida
        if url and url.startswith(('http://', 'https://')):
            console.print("[cyan]📄 Intentando con PDF por URL (sin límite de tamaño)...[/cyan]")
            try:
                result = await self._extract_pdf_from_url(url, prompt, extract_tables, pdf_filename, model_id)
                if result:
                    return result
                console.print("[yellow]  Método por URL falló, intentando con base64...[/yellow]")
            except Exception as e:
                error_str = str(e).lower()
                # Si es error de crédito, propagar
                credit_patterns = ["insufficient", "credit", "quota", "balance", "429", "rate limit"]
                if any(p in error_str for p in credit_patterns):
                    raise CreditExhaustedError(f"CRÉDITOS AGOTADOS: {e}")
                console.print(f"[yellow]  URL falló: {e}[/yellow]")

        # Estrategia 2: Intentar con base64
        console.print("[cyan]📄 Intentando con PDF en base64...[/cyan]")
        try:
            return await self._extract_pdf_base64(pdf_content, url, prompt, extract_tables, pdf_filename, model_id)
        except Exception as e:
            await self._close_client_if_exists()
            error_str = str(e).lower()

            # Detectar errores de crédito
            credit_patterns = ["insufficient", "credit", "quota", "balance", "429", "rate limit"]
            if any(p in error_str for p in credit_patterns):
                console.print("\n[bold red]⚠️⚠️⚠️ ERROR DE CRÉDITO/RATE LIMIT ⚠️⚠️⚠️[/bold red]\n")
                raise CreditExhaustedError(f"CRÉDITOS AGOTADOS: {e}")

            # Detectar error de tamaño (413) - usar chunks
            size_patterns = ["413", "request entity too large", "payload too large", "too large"]
            if any(p in error_str for p in size_patterns):
                console.print("\n[yellow]📦 PDF demasiado grande para File API (error 413)[/yellow]")
                console.print("[yellow]   Procesando por chunks de 15 páginas...[/yellow]")
                return await self._extract_pdf_as_chunks(pdf_content, url, municipio, extract_tables)

            # Otro error
            console.print(f"[red]Error desconocido: {e}[/red]")
            raise

    async def _extract_pdf_from_url(
        self,
        url: str,
        prompt: str,
        extract_tables: bool,
        pdf_filename: str,
        model_id: str = None
    ) -> Optional[Tuple[str, str, dict]]:
        """
        Intenta extraer PDF usando URL directa en lugar de base64.

        Args:
            model_id: ID del modelo a usar (si None, usa self.model_id)

        Ventaja: No hay límite de tamaño del request body.
        """
        from openai import AsyncOpenAI

        # Usar modelo proporcionado o default
        if model_id is None:
            model_id = self.model_id

        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        try:
            call_kwargs = {
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "file",
                                "file": {
                                    "filename": pdf_filename,
                                    "file_data": url  # URL directa en lugar de base64
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 16384,
                "temperature": 0.0,
                "extra_body": {
                    "plugins": [
                        {"id": "file-parser", "pdf": {"engine": "pdf-text"}}
                    ]
                }
            }

            response = await client.chat.completions.create(**call_kwargs)
            content = response.choices[0].message.content or ""

            # Registrar en LLM tracker
            try:
                from utils.llm_tracker import extract_token_usage, record_llm_call
                input_tokens, output_tokens = extract_token_usage(response)
                if input_tokens > 0 or output_tokens > 0:
                    task = "vision_tables_url" if extract_tables else "vision_url"
                    record_llm_call(
                        model=self.model_id,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        task=task,
                        metadata={"method": "file_url", "pdf_engine": "pdf-text"}
                    )
            except Exception:
                pass

            await client.close()

            # Extraer título y evaluar calidad
            title = self._extract_title(content)
            quality = self._assess_quality(content, 0, 0)
            quality["extraction_method"] = "file_url_pdf_text"

            console.print(f"[green]✓ Extraído {len(content):,} caracteres vía URL (1 llamada)[/green]")

            return title, content, quality

        except Exception as e:
            await client.close()
            # Propagar excepción para que el caller decida qué hacer
            raise

    async def _extract_pdf_base64(
        self,
        pdf_content: bytes,
        url: str,
        prompt: str,
        extract_tables: bool,
        pdf_filename: str,
        model_id: str = None
    ) -> Tuple[str, str, dict]:
        """
        Extrae PDF usando base64 (método original).

        Args:
            model_id: ID del modelo a usar (si None, usa self.model_id)
        """
        from openai import AsyncOpenAI

        # Usar modelo proporcionado o default
        if model_id is None:
            model_id = self.model_id

        # Codificar PDF en base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        call_kwargs = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "file",
                            "file": {
                                "filename": pdf_filename,
                                "file_data": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 16384,
            "temperature": 0.0,
            "extra_body": {
                "plugins": [
                    {"id": "file-parser", "pdf": {"engine": "pdf-text"}}
                ]
            }
        }

        response = await client.chat.completions.create(**call_kwargs)
        content = response.choices[0].message.content or ""

        # Registrar en LLM tracker
        try:
            from utils.llm_tracker import extract_token_usage, record_llm_call
            input_tokens, output_tokens = extract_token_usage(response)
            if input_tokens > 0 or output_tokens > 0:
                task = "vision_tables_base64" if extract_tables else "vision_base64"
                record_llm_call(
                    model=self.model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    task=task,
                    metadata={"method": "file_base64", "pdf_engine": "pdf-text"}
                )
        except Exception:
            pass

        await client.close()

        # Extraer título y evaluar calidad
        title = self._extract_title(content)
        quality = self._assess_quality(content, 0, 0)
        quality["extraction_method"] = "file_base64_pdf_text"

        console.print(f"[green]✓ Extraído {len(content):,} caracteres vía base64 (1 llamada)[/green]")

        return title, content, quality

    async def _close_client_if_exists(self):
        """Cierra el cliente si existe (para cleanup en errores)."""
        pass  # El cliente se cierra localmente en cada método

    def _split_pdf_into_chunks(self, pdf_content: bytes, chunk_size: int = 15) -> list[tuple[bytes, str]]:
        """
        Divide un PDF en chunks de N páginas cada uno.

        Args:
            pdf_content: Contenido binario del PDF
            chunk_size: Páginas por chunk (default: 15)

        Returns:
            Lista de (chunk_bytes, page_range) donde page_range = "1-15", "16-30", etc.
        """
        import io
        try:
            from PyPDF2 import PdfReader, PdfWriter
        except ImportError:
            console.print("[red]❌ Instala: pip install PyPDF2[/red]")
            raise ImportError("PyPDF2 es requerido para dividir PDFs grandes")

        chunks = []
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        total_pages = len(pdf_reader.pages)

        console.print(f"[dim]  Dividiendo PDF de {total_pages} páginas en chunks de {chunk_size}...[/dim]")

        for start_page in range(0, total_pages, chunk_size):
            end_page = min(start_page + chunk_size, total_pages)

            writer = PdfWriter()
            for page_num in range(start_page, end_page):
                writer.add_page(pdf_reader.pages[page_num])

            chunk_buffer = io.BytesIO()
            writer.write(chunk_buffer)
            chunk_bytes = chunk_buffer.getvalue()

            page_range = f"{start_page + 1}-{end_page}"
            chunks.append((chunk_bytes, page_range))

            console.print(f"[dim]    Chunk {len(chunks)}: páginas {page_range} ({end_page - start_page} pág)[/dim]")

        return chunks

    async def _extract_pdf_as_chunks(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str,
        extract_tables: bool,
        chunk_size: int = 15,
        use_free_model: bool = True
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto dividiendo el PDF en chunks y procesando cada uno.

        Usa File API con motor pdf-text para cada chunk.

        Args:
            use_free_model: Si True, usa modelo GRATIS; si False, usa modelo actual
        """
        from openai import AsyncOpenAI

        # Elegir modelo según configuración
        model_id = self.FREE_VISION_MODEL if use_free_model else self.model_id

        model_name = "GRATIS" if use_free_model else "PREMIUM"
        console.print(f"[cyan]📄 Procesando PDF por chunks de {chunk_size} páginas (modelo {model_name})...[/cyan]")

        # Dividir PDF en chunks
        chunks = self._split_pdf_into_chunks(pdf_content, chunk_size)
        total_chunks = len(chunks)

        if not chunks:
            return "", "", {"confidence": 0, "quality": "failed"}

        console.print(f"[cyan]  PDF dividido en {total_chunks} chunks[/cyan]")

        # Procesar cada chunk
        all_content = []
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        try:
            for i, (chunk_bytes, page_range) in enumerate(chunks, 1):
                console.print(f"[cyan]  [{i}/{total_chunks}] Procesando páginas {page_range}...[/cyan]")

                # Codificar chunk en base64
                chunk_base64 = base64.b64encode(chunk_bytes).decode('utf-8')
                chunk_filename = f"documento_paginas_{page_range}.pdf"

                # Prompt específico para chunk
                if extract_tables:
                    prompt = self._get_tables_prompt()
                    prompt = f"{prompt}\n\nESTE ES UN CHUNK DE PÁGINAS {page_range} DEL DOCUMENTO ORIGINAL."
                else:
                    prompt = (
                        f"Extrae TODO el texto de estas páginas ({page_range}) del documento. "
                        "Si hay DOS COLUMNAS, lee la IZQUIERDA completa primero, luego la DERECHA. "
                        "NO mezcles el texto entre columnas."
                    )

                try:
                    # Llamada API para este chunk
                    response = await client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "file",
                                        "file": {
                                            "filename": chunk_filename,
                                            "file_data": f"data:application/pdf;base64,{chunk_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=16384,
                        temperature=0.0,
                        extra_body={
                            "plugins": [
                                {"id": "file-parser", "pdf": {"engine": "pdf-text"}}
                            ]
                        }
                    )

                    content = response.choices[0].message.content or ""
                    all_content.append(f"=== PÁGINAS {page_range} ===\n{content}")

                    # Registrar token usage
                    try:
                        from utils.llm_tracker import extract_token_usage, record_llm_call
                        input_tokens, output_tokens = extract_token_usage(response)
                        if input_tokens > 0 or output_tokens > 0:
                            task = "vision_tables_chunk" if extract_tables else "vision_chunk"
                            record_llm_call(
                                model=self.model_id,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                task=task,
                                metadata={"method": "chunk_api", "pages": page_range}
                            )
                    except Exception:
                        pass

                    console.print(f"[green]    ✓ Chunk {i}/{total_chunks} completado ({len(content):,} caracteres)[/green]")

                except Exception as chunk_err:
                    error_str = str(chunk_err).lower()

                    # Detectar errores de crédito
                    if any(p in error_str for p in ["insufficient", "credit", "quota", "429", "rate limit"]):
                        await client.close()
                        console.print("\n[bold red]⛔ ERROR DE CRÉDITO/RATE LIMIT ⛔[/bold red]")
                        raise CreditExhaustedError(f"CRÉDITOS AGOTADOS: {chunk_err}")

                    console.print(f"[yellow]    ⚠ Chunk {i} falló: {chunk_err}[/yellow]")
                    all_content.append(f"=== PÁGINAS {page_range} ===\n[ERROR: No se pudo procesar]")

            await client.close()

            # Unir todo el contenido
            full_content = "\n\n".join(all_content)

            # Extraer título y evaluar calidad
            title = self._extract_title(full_content)
            quality = self._assess_quality(full_content, total_chunks, total_chunks)
            quality["extraction_method"] = "chunk_api_pdf_text"

            console.print(f"[green]✓ Extraído {len(full_content):,} caracteres en {total_chunks} chunks[/green]")

            return title, full_content, quality

        except CreditExhaustedError:
            raise
        except Exception as e:
            await client.close()
            raise

    async def _extract_pdf_as_image_chunks(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str,
        extract_tables: bool,
        chunk_size: int = 15
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto dividiendo el PDF en chunks y procesando cada chunk con VISION (imágenes).

        A diferencia de _extract_pdf_as_chunks() que usa pdf-text (altera columnas),
        este método convierte cada chunk a imágenes y usa Gemini Vision directamente.

        Ventaja: Mantiene el orden correcto de las columnas porque Gemini ve la imagen visualmente.
        """
        from openai import AsyncOpenAI
        import io
        try:
            import pdf2image
        except ImportError:
            console.print("[red]❌ Instala: pip install pdf2image[/red]")
            raise ImportError("pdf2image es requerido para procesar PDFs como imágenes")

        console.print(f"[cyan]📸 Procesando PDF por chunks de {chunk_size} páginas con Gemini Vision...[/cyan]")

        # 1. Dividir PDF en chunks (usando PyPDF2)
        chunks = self._split_pdf_into_chunks(pdf_content, chunk_size)
        total_chunks = len(chunks)

        if not chunks:
            return "", "", {"confidence": 0, "quality": "failed"}

        console.print(f"[cyan]  PDF dividido en {total_chunks} chunks[/cyan]")

        # 2. Procesar cada chunk con Vision
        all_content = []
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        try:
            for i, (chunk_bytes, page_range) in enumerate(chunks, 1):
                console.print(f"[cyan]  [{i}/{total_chunks}] Procesando páginas {page_range}...[/cyan]")

                # Convertir chunk PDF a imágenes
                try:
                    images = pdf2image.convert_from_bytes(
                        chunk_bytes,
                        dpi=200,  # Mejor calidad para OCR
                        fmt='jpeg'
                    )
                except Exception as e:
                    console.print(f"[yellow]    ⚠ Error convirtiendo chunk a imágenes: {e}[/yellow]")
                    all_content.append(f"=== PÁGINAS {page_range} ===\n[ERROR: No se pudo procesar chunk]")
                    continue

                console.print(f"[dim]    → {len(images)} imágenes generadas[/dim]")

                # 3. Procesar todas las imágenes del chunk en UNA SOLA llamada
                # Esto es MUCHO más eficiente y económico (12 llamadas en lugar de 176)
                content_list = []
                
                # Prompt inicial
                chunk_prompt = self._get_tables_prompt() if extract_tables else (
                    f"Extrae TODO el texto de estas páginas del documento ({page_range}).\n"
                    "Si hay DOS COLUMNAS, lee la IZQUIERDA completa primero, luego la DERECHA.\n"
                    "Mantén el formato original. NO resumas."
                )
                content_list.append({"type": "text", "text": chunk_prompt})

                # Agregar todas las imágenes como partes del contenido
                for img in images:
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='JPEG', quality=90) # Bajamos un poco quality para evitar 413
                    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                    content_list.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    })

                try:
                    # Llamada única para el chunk de 15 páginas
                    response = await client.chat.completions.create(
                        model=self.model_id,
                        messages=[{
                            "role": "user",
                            "content": content_list
                        }],
                        max_tokens=16384,
                        temperature=0.0,
                    )

                    chunk_md = response.choices[0].message.content or ""
                    
                    # Registrar token usage
                    try:
                        from utils.llm_tracker import extract_token_usage, record_llm_call
                        input_tokens, output_tokens = extract_token_usage(response)
                        if input_tokens > 0 or output_tokens > 0:
                            task = "vision_tables_chunk_batch" if extract_tables else "vision_chunk_batch"
                            record_llm_call(
                                model=self.model_id,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                task=task,
                                metadata={"method": "image_chunk_batch", "pages": page_range}
                            )
                    except Exception:
                        pass

                    all_content.append(f"=== PÁGINAS {page_range} ===\n{chunk_md}")
                    console.print(f"[green]    ✓ Chunk {i}/{total_chunks} completado ({len(chunk_md):,} caracteres)[/green]")

                except Exception as chunk_err:
                    error_str = str(chunk_err).lower()
                    if any(p in error_str for p in ["insufficient", "credit", "quota", "429", "rate limit"]):
                        await client.close()
                        console.print("\n[bold red]⛔ ERROR DE CRÉDITO/RATE LIMIT ⛔[/bold red]")
                        from .exceptions import CreditExhaustedError
                        raise CreditExhaustedError(f"CRÉDITOS AGOTADOS: {chunk_err}")

                    console.print(f"[yellow]    ⚠ Chunk {i} falló: {chunk_err}[/yellow]")
                    all_content.append(f"=== PÁGINAS {page_range} ===\n[ERROR: {chunk_err}]")

            await client.close()

            # Unir todo el contenido
            full_content = "\n\n".join(all_content)

            # Extraer título y evaluar calidad
            title = self._extract_title(full_content)
            quality = self._assess_quality(full_content, total_chunks, total_chunks)
            quality["extraction_method"] = "image_chunks_vision"

            console.print(f"[green]✓ Extraído {len(full_content):,} caracteres en {total_chunks} chunks (Vision)[/green]")

            return title, full_content, quality

        except Exception as e:
            await client.close()
            raise

    async def _extract_pdf_as_images(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str,
        max_pages: Optional[int],
        extract_tables: bool
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto convirtiendo PDF a imágenes (MÉTODO LEGACY).

        Hace 1 llamada API por página (176 llamadas para un PDF de 176 páginas).
        """
        from openai import AsyncOpenAI

        console.print("[cyan]📸 Procesando PDF página por página (método legacy)...[/cyan]")

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
        quality["extraction_method"] = "vision_api_images"

        return title, content, quality

    async def _extract_pdf_with_glm_ocr(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str,
        extract_tables: bool
    ) -> Tuple[str, str, dict]:
        """
        Extrae PDF usando GLM-OCR API de Z.AI.

        GLM-OCR está especializado en tablas financieras complejas.
        """
        from extractors.glm_ocr_extractor import GLMOCRExtractor, html_to_markdown

        console.print("[cyan]📄 Procesando con GLM-OCR...[/cyan]")

        try:
            extractor = GLMOCRExtractor()
            title, content, quality = extractor.extract_pdf(
                pdf_content, url, municipio, extract_tables
            )

            # Agregar metadata adicional
            quality["pdf_engine"] = "glm-ocr"

            return title, content, quality

        except Exception as e:
            console.print(f"[red]Error en GLM-OCR: {e}[/red]")
            # Retornar vacío en caso de error
            return "", "", {"confidence": 0, "quality": "failed", "error": str(e)}

    def _get_tables_prompt(self) -> str:
        """Retorna el prompt optimizado para extracción de tablas financieras."""
        return (
            "Eres un extractor de datos financieros experto. Extrae TODO el contenido de este documento PDF:\n\n"
            "**PRIMERO: CABECERA DEL DOCUMENTO** (IMPORTANTE)\n"
            "- Extrae TODA la información de la cabecera ANTES de las tablas\n"
            "- Incluye: institución, municipio, ejercicio, periodo (Desde el... hasta el...), fecha de generación\n"
            "- Incluye el tipo de documento (BALANCE DE SUMAS Y SALDOS, BALANCE DE TESORERIA, etc.)\n"
            "- NO omitas la cabecera\n\n"
            "**SEGUNDO: TABLAS** (prioridad máxima)\n"
            "- Si hay tablas con datos contables/financieros, extráelas en formato Markdown\n"
            "- Usa el carácter | para separar columnas\n"
            "- Incluye fila de encabezado separadora con |---|---|---|\n"
            "- **IMPORTANTE: Usa el formato numérico Español/Europeo:** "
            "1.234.567,89 (punto para miles, coma para decimales)\n"
            "- Ejemplo: | Cuenta | Debe | Haber |\\n|---|---|---|\\n| Caja | 1.000,00 | 500,00 |\n\n"
            "**FORMATO DE COLUMNAS**:\n"
            "- Si el documento tiene 2 columnas de texto, lee IZQUIERDA completa primero, luego DERECHA\n\n"
            "**REGLAS**:\n"
            "- Mantén números, fechas y símbolos exactos (., $ %)\n"
            "- NO resumas ni interpretes\n"
            "- Devuelve TODO el contenido, PRIMERO la cabecera, LUEGO las tablas"
        )

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
                images.append(base64.b64encode(
                    buffer.getvalue()).decode('utf-8'))

            os.unlink(tmp_path)

        except Exception as e:
            console.print(f"[red]Error convirtiendo PDF: {e}[/red]")
            return []

        return images

    async def _extract_page(self, image_base64: str, client, extract_tables: bool = False) -> str:
        """Extrae texto de una página usando Vision API (método legacy por imagen).

        Args:
            image_base64: Imagen codificada en base64
            client: Cliente OpenAI
            extract_tables: Si True, usa prompt optimizado para tablas financieras
        """
        # Usar prompt centralizado
        prompt = self._get_tables_prompt() if extract_tables else (
            "Extrae TODO el texto de esta imagen de un documento legal. "
            "IMPORTANTE: Este documento puede tener DOS COLUMNAS. "
            "Debes leer la COLUMNA IZQUIERDA completa primero, luego la COLUMNA DERECHA completa. "
            "NO mezcles el texto entre columnas. "
            "Mantén el formato original con números, fechas y artículos. "
            "NO resumas, NO interpretes, SOLO extrae el texto literalmente."
        )

        try:
            # Configuración base de la llamada
            call_kwargs = {
                "model": self.model_id,
                "messages": [
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
                "max_tokens": 8192,
                "temperature": 0.0,
            }

            # Para Mistral Small 3.1, forzar proveedor "chutes"
            if "mistral-small-3.1-24b-instruct" in self.model_id:
                call_kwargs["extra_body"] = {
                    "provider": {
                        "only": ["chutes"],
                        "quantizations": ["bf16"]
                    }
                }

            response = await client.chat.completions.create(**call_kwargs)

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
                console.print(
                    "\n[bold red]⚠️⚠️⚠️ ERROR DE CRÉDITO/RATE LIMIT DETECTADO ⚠️⚠️⚠️[/bold red]\n")
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
        legal_count = sum(
            1 for word in legal_words if word.lower() in content.lower())

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
    extract_tables: bool = False,
    pdf_engine: str = "file"
) -> Optional[Tuple[str, str, dict]]:
    """
    Extrae un boletín usando Vision API con prompt especial para columnas.

    Wrapper para uso rápido. Procesa TODAS las páginas del PDF.

    Args:
        content: Contenido binario del PDF
        url: URL de origen
        municipio: Nombre del municipio
        extract_tables: Si True, usa prompt optimizado para tablas financieras
        pdf_engine: Motor "file" (File API, 1 llamada) o "images" (imágenes, 176 llamadas)

    Returns:
        (title, content, quality) o None si falla
    """
    extractor = VisionExtractor(pdf_engine=pdf_engine)

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
                console.print(
                    f"\n[bold green]✅ EXTRACCIÓN COMPLETADA[/bold green]")
                console.print(f"Título: {title[:80]}...")
                console.print(f"Longitud: {len(content):,} caracteres")
                console.print(
                    f"Calidad: {quality['confidence']:.1%} ({quality['quality']})")
            else:
                console.print("[red]❌ Falló la extracción[/red]")

    asyncio.run(test())
