#!/usr/bin/env python3
"""
extractors/glm_ocr_extractor.py

Extractor de PDFs usando GLM-OCR API de Z.AI.

GLM-OCR es especializado en documentos financieros con tablas complejas.
Devuelve contenido en formato Markdown con tablas correctamente estructuradas.

@version 1.1.0
@created 2026-02-03
@updated 2026-02-03 - Soporte para chunking de PDFs grandes (147+ páginas)
"""

import base64
import io
import os
import re
from typing import Optional, Tuple, List
from pathlib import Path
from rich.console import Console

console = Console()

# ============================================================================
# CONFIGURACIÓN DE CHUNKING
# ============================================================================

# Máximo de páginas que GLM-OCR puede procesar en una sola llamada
GLM_OCR_MAX_PAGES = 15

# Tamaño del chunk para PDFs grandes
CHUNK_SIZE = int(os.getenv("GLM_OCR_CHUNK_SIZE", str(GLM_OCR_MAX_PAGES)))


# ============================================================================
# UTILIDADES PARA REPARAR HTML
# ============================================================================

def fix_html_tables(html_content: str) -> str:
    """
    Repara HTML mal formado de GLM-OCR.

    GLM-OCR devuelve HTML sin etiquetas de cierre (</th>, </tr>, </table>).
    Esta función agrega los cierres donde faltan y elimina duplicados de OCR.

    El HTML mal formado se ve así:
    <th>2095\nDecisión que has atenido...
    (falta el </th> después del último año)
    """
    result = html_content

    # Buscar <th>AÑO seguido de salto de línea y texto (sin </th>)
    # Esto es el último <th> de la fila de encabezados
    def close_last_th(m):
        """Agrega </th></tr></thead></table> antes del texto externo."""
        year_content = m.group(1)  # 2095
        after_text = m.group(2)     # Decisión que has atenido...
        return f"<th>{year_content}</th></tr></thead></table>\n\n{after_text}"

    # Patrón: <th>1234\nTexto (sin </th>)
    result = re.sub(
        r'<th>(\d{4})\r?\n([A-Z][^\n<].*)',
        close_last_th,
        result,
        flags=re.DOTALL
    )

    # Eliminar <th> duplicados causados por errores de OCR
    # A veces GLM-OCR detecta años después de 2095 que son duplicados
    result = re.sub(
        r'(<th>2095</th>)(<th>2096</th><th>2097</th><th>2098</th><th>2099</th><th>2000</th>.*?<th>2095</th>)',
        r'\1',
        result,
        flags=re.DOTALL
    )

    return result


def fix_markdown_tables(markdown: str) -> str:
    """Limpia espacios y pipes extra en tablas Markdown."""
    lines = markdown.split('\n')
    result = []

    for line in lines:
        # Si la línea de separación de tabla está incompleta, completarla
        if line.strip().startswith('|---') and not line.strip().endswith('|'):
            line = line.rstrip() + ' |'
        result.append(line)

    return '\n'.join(result)


def html_to_markdown(html_content: str) -> str:
    """
    Convierte HTML a Markdown usando bibliotecas disponibles.

    Prioridad:
    1. html-to-markdown (mejor para tablas)
    2. html2text (fallback)
    """
    # Primero reparar el HTML mal formado
    fixed_html = fix_html_tables(html_content)

    # Intentar con html-to-markdown
    try:
        from html_to_markdown import convert
        md = convert(fixed_html)
        return fix_markdown_tables(md)
    except ImportError:
        pass

    # Fallback a html2text
    try:
        from html2text import HTML2Text
        h = HTML2Text()
        h.body_width = 0
        h.unicode_snob = True
        md = h.handle(fixed_html)
        return fix_markdown_tables(md)
    except ImportError:
        pass

    # Último recurso: retornar HTML tal cual
    return fixed_html


# ============================================================================
# FUNCIONES DE CHUNKING
# ============================================================================

def get_pdf_page_count(pdf_content: bytes) -> int:
    """
    Retorna el número de páginas de un PDF sin procesarlo.

    Args:
        pdf_content: Contenido binario del PDF

    Returns:
        Número de páginas (0 si falla)
    """
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        console.print("[red]❌ Instala: pip install PyPDF2[/red]")
        return 0

    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        return len(pdf_reader.pages)
    except Exception:
        return 0


def split_pdf_into_chunks(pdf_content: bytes, chunk_size: int = CHUNK_SIZE) -> List[Tuple[bytes, str]]:
    """
    Divide un PDF en chunks de N páginas cada uno.

    Args:
        pdf_content: Contenido binario del PDF
        chunk_size: Páginas por chunk (default: CHUNK_SIZE = 15)

    Returns:
        Lista de (chunk_bytes, page_range) donde page_range = "1-15", "16-30", etc.
    """
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


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# API Token de Z.AI para GLM-OCR
GLM_API_KEY = os.getenv("ZAI_API_KEY", "407612aefd694ce29ddda150fa34fe2b.zn0SA8iAduvarrDm")


# ============================================================================
# GLM OCR EXTRACTOR
# ============================================================================

class GLMOCRExtractor:
    """
    Extractor de PDFs usando GLM-OCR API de Z.AI.

    GLM-OCR está optimizado para:
    - Tablas financieras complejas (balances, presupuestos)
    - Documentos con múltiples columnas
    - Layouts irregulares

    Ventajas sobre Vision API tradicional:
    - Devuelve Markdown directamente (no necesita prompt)
    - Mejor precisión en tablas con muchos años
    - Más económico para documentos grandes
    """

    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: API Key de Z.AI (si None, usa GLM_API_KEY o variable de entorno)
        """
        self.api_key = api_key or GLM_API_KEY

        if not self.api_key:
            raise ValueError("ZAI_API_KEY no configurada. Setea la variable de entorno o pasa api_key.")

    def extract_pdf(
        self,
        pdf_content: bytes,
        url: str = "",
        municipio: str = "Desconocido",
        max_pages: Optional[int] = None,
        extract_tables: bool = False,
        chunk_size: int = CHUNK_SIZE,
        force_chunks: bool = False,
        **kwargs
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto de un PDF usando GLM-OCR API.

        Soporta chunking automático para PDFs grandes (> CHUNK_SIZE páginas).

        Args:
            pdf_content: Contenido binario del PDF
            url: URL de origen (para logging)
            municipio: Nombre del municipio
            max_pages: Límite de páginas (si None, procesa todas)
            extract_tables: Si True, intenta extraer tablas (siempre True en GLM-OCR)
            chunk_size: Páginas por chunk para PDFs grandes
            force_chunks: Si True, fuerza el modo chunking sin importar el tamaño
            **kwargs: Parámetros adicionales ignorados

        Returns:
            (title, content, quality) - Título extraído, contenido completo, metadata de calidad
        """
        from zai import ZaiClient

        # Verificar tamaño del PDF
        page_count = get_pdf_page_count(pdf_content)

        console.print(f"[cyan]📄 Procesando PDF con GLM-OCR ({page_count} páginas)...[/cyan]")

        # Si el PDF es grande o se fuerza chunking, usar modo chunks
        if page_count > chunk_size or force_chunks:
            console.print(f"[yellow]→ PDF grande ({page_count} pág), usando modo chunking ({chunk_size} pág/chunk)[/yellow]")
            return self._extract_pdf_by_chunks(
                pdf_content, url, municipio, chunk_size, max_pages
            )

        # PDF pequeño: procesar en una sola llamada
        return self._extract_pdf_single(pdf_content, url, municipio)

    def _extract_pdf_single(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto de un PDF pequeño en una sola llamada GLM-OCR.
        """
        from zai import ZaiClient

        client = ZaiClient(api_key=self.api_key)

        # Codificar PDF en base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        data_url = f"data:application/pdf;base64,{pdf_base64}"

        try:
            # Llamar a GLM-OCR API
            response = client.layout_parsing.create(
                model="glm-ocr",
                file=data_url
            )

            # Extraer markdown
            markdown_content = None
            if hasattr(response, 'md_results'):
                markdown_content = response.md_results
            elif isinstance(response, dict):
                markdown_content = response.get('md_results', response.get('data', ''))

            if not markdown_content:
                return "", "", {"confidence": 0, "quality": "failed", "error": "No se pudo extraer contenido"}

            # Convertir HTML a Markdown si es necesario
            if '<table' in markdown_content or '<th>' in markdown_content:
                content = html_to_markdown(markdown_content)
            else:
                content = markdown_content

            # Extraer título
            title = self._extract_title(content, url)

            # Evaluar calidad
            quality = self._assess_quality(content)
            quality["extraction_method"] = "glm_ocr_single"

            console.print(f"[green]✓ Extraído {len(content):,} caracteres con GLM-OCR (1 llamada)[/green]")

            return title, content, quality

        except Exception as e:
            console.print(f"[red]Error en GLM-OCR: {e}[/red]")
            return "", "", {
                "confidence": 0,
                "quality": "failed",
                "error": str(e),
                "extraction_method": "glm_ocr_single"
            }

    def _extract_pdf_by_chunks(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str,
        chunk_size: int,
        max_pages: Optional[int]
    ) -> Tuple[str, str, dict]:
        """
        Extrae texto de un PDF grande dividiéndolo en chunks.

        Args:
            pdf_content: Contenido binario del PDF
            url: URL de origen
            municipio: Nombre del municipio
            chunk_size: Páginas por chunk
            max_pages: Máximo de páginas a procesar

        Returns:
            (title, content, quality) - Contenido combinado de todos los chunks
        """
        from zai import ZaiClient

        client = ZaiClient(api_key=self.api_key)

        # Dividir PDF en chunks
        chunks = split_pdf_into_chunks(pdf_content, chunk_size)
        total_chunks = len(chunks)

        if not chunks:
            return "", "", {"confidence": 0, "quality": "failed", "error": "No se pudo dividir el PDF"}

        console.print(f"[cyan]  PDF dividido en {total_chunks} chunks[/cyan]")

        # Aplicar max_pages si se especificó
        if max_pages and max_pages < total_chunks * chunk_size:
            chunks_to_process = (max_pages + chunk_size - 1) // chunk_size
            chunks = chunks[:chunks_to_process]
            console.print(f"[yellow]  Limitado a {max_pages} páginas ({chunks_to_process} chunks)[/yellow]")

        # Procesar cada chunk
        all_content = []
        failed_chunks = []

        for i, (chunk_bytes, page_range) in enumerate(chunks, 1):
            console.print(f"[cyan]  [{i}/{len(chunks)}] Procesando páginas {page_range}...[/cyan]")

            # Codificar chunk en base64
            chunk_base64 = base64.b64encode(chunk_bytes).decode('utf-8')
            data_url = f"data:application/pdf;base64,{chunk_base64}"

            try:
                # Llamar a GLM-OCR API para este chunk
                response = client.layout_parsing.create(
                    model="glm-ocr",
                    file=data_url
                )

                # Extraer markdown
                markdown_content = None
                if hasattr(response, 'md_results'):
                    markdown_content = response.md_results
                elif isinstance(response, dict):
                    markdown_content = response.get('md_results', response.get('data', ''))

                if not markdown_content:
                    console.print(f"[yellow]    ⚠ Chunk {i} no retornó contenido[/yellow]")
                    failed_chunks.append((i, page_range))
                    all_content.append(f"=== PÁGINAS {page_range} ===\n[ERROR: No se pudo extraer contenido]")
                    continue

                # Convertir HTML a Markdown si es necesario
                if '<table' in markdown_content or '<th>' in markdown_content:
                    chunk_md = html_to_markdown(markdown_content)
                else:
                    chunk_md = markdown_content

                # Agregar separador de páginas y contenido
                all_content.append(f"=== PÁGINAS {page_range} ===\n{chunk_md}")

                console.print(f"[green]    ✓ Chunk {i} completado ({len(chunk_md):,} caracteres)[/green]")

            except Exception as chunk_err:
                console.print(f"[yellow]    ⚠ Chunk {i} falló: {chunk_err}[/yellow]")
                failed_chunks.append((i, page_range))
                all_content.append(f"=== PÁGINAS {page_range} ===\n[ERROR: {chunk_err}]")

        # Unir todo el contenido
        full_content = "\n\n".join(all_content)

        # Extraer título
        title = self._extract_title(full_content, url)

        # Evaluar calidad
        quality = self._assess_quality(full_content)
        quality["extraction_method"] = "glm_ocr_chunks"
        quality["total_chunks"] = len(chunks)
        quality["processed_chunks"] = len(chunks) - len(failed_chunks)
        quality["failed_chunks"] = len(failed_chunks)

        if failed_chunks:
            quality["warnings"].append(f"chunks_fallidos:{len(failed_chunks)}/{len(chunks)}")

        console.print(f"[green]✓ Extraído {len(full_content):,} caracteres en {len(chunks)} chunks[/green]")

        if failed_chunks:
            console.print(f"[yellow]⚠ {len(failed_chunks)} chunks fallaron: {[f'{i}({r})' for i, r in failed_chunks]}[/yellow]")

        return title, full_content, quality

    def _extract_title(self, content: str, url: str) -> str:
        """Extrae un título del contenido o de la URL."""
        # Primero intentar extraer del contenido
        lines = content.split('\n')
        for line in lines[:10]:
            line = line.strip()
            # Buscar línea que parezca título (no tabla, no vacía)
            if len(line) > 15 and len(line) < 200:
                # Evitar líneas de tablas
                if not line.startswith('|') and '---' not in line:
                    # Limpiar caracteres corruptos
                    line = re.sub(r'[´\x00-\x1f\x7f-\x9f]', '', line)
                    if len(line) > 10:
                        return line[:100]

        # Fallback a nombre de archivo de URL
        if url:
            filename = url.split('/')[-1]
            # Limpiar extensión
            name = re.sub(r'\.(pdf|png|jpe?g)$', '', filename, flags=re.IGNORECASE)
            name = name.replace('_', ' ').replace('-', ' ')
            return name[:100]

        return "Extraído con GLM-OCR"

    def _assess_quality(self, content: str) -> dict:
        """Evalúa la calidad de la extracción."""
        if not content:
            return {"confidence": 0, "quality": "failed"}

        score = 1.0
        warnings = []

        # Longitud mínima
        if len(content) < 100:
            score -= 0.5
            warnings.append("texto_corto")

        # Verificar si hay tablas (buen indicador para GLM-OCR)
        has_tables = '|' in content and '---' in content
        if not has_tables and len(content) > 500:
            score -= 0.1
            warnings.append("sin_tablas")

        # Caracteres corruptos
        corrupt_count = content.count('´')
        if corrupt_count > 10:
            score -= min(0.2, corrupt_count * 0.01)
            warnings.append(f"acentos_rotos:{corrupt_count}")

        # Palabras clave financieras
        financial_words = [
            'balance', 'tesoreria', 'presupuesto', 'ejercicio',
            'debe', 'haber', 'activo', 'pasivo', 'patrimonio'
        ]
        financial_count = sum(
            1 for word in financial_words if word.lower() in content.lower()
        )

        if financial_count > 0:
            score = min(1.0, score + 0.1)  # Bonus para contenido financiero

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
            "confidence": max(0, min(1.0, score)),
            "quality": quality,
            "warnings": warnings[:5]
        }


# ============================================================================
# FUNCIÓN DE CONVENIENCIA (SÍNCRONA)
# ============================================================================

def extract_pdf_with_glm_ocr(
    pdf_content: bytes,
    url: str = "",
    municipio: str = "Desconocido",
    api_key: str = None,
    chunk_size: int = CHUNK_SIZE,
    force_chunks: bool = False
) -> Optional[Tuple[str, str, dict]]:
    """
    Extrae un PDF usando GLM-OCR (versión síncrona).

    Args:
        pdf_content: Contenido binario del PDF
        url: URL de origen
        municipio: Nombre del municipio
        api_key: API Key de Z.AI
        chunk_size: Páginas por chunk (para PDFs grandes)
        force_chunks: Si True, fuerza el modo chunking

    Returns:
        (title, content, quality) o None si falla
    """
    extractor = GLMOCRExtractor(api_key=api_key)

    try:
        return extractor.extract_pdf(
            pdf_content, url, municipio,
            chunk_size=chunk_size,
            force_chunks=force_chunks
        )
    except Exception as e:
        console.print(f"[red]Error en extracción GLM-OCR: {e}[/red]")
        return None


# ============================================================================
# FUNCIÓN ASÍNCRONA (para compatibilidad con VisionExtractor)
# ============================================================================

async def extract_pdf_with_glm_ocr_async(
    pdf_content: bytes,
    url: str = "",
    municipio: str = "Desconocido",
    api_key: str = None,
    chunk_size: int = CHUNK_SIZE,
    force_chunks: bool = False
) -> Optional[Tuple[str, str, dict]]:
    """
    Extrae un PDF usando GLM-OCR (versión asíncrona para compatibilidad).

    Args:
        pdf_content: Contenido binario del PDF
        url: URL de origen
        municipio: Nombre del municipio
        api_key: API Key de Z.AI
        chunk_size: Páginas por chunk (para PDFs grandes)
        force_chunks: Si True, fuerza el modo chunking

    Returns:
        (title, content, quality) o None si falla
    """
    # GLM-OCR es síncrono, pero envolvemos para compatibilidad
    return extract_pdf_with_glm_ocr(
        pdf_content, url, municipio, api_key,
        chunk_size=chunk_size,
        force_chunks=force_chunks
    )


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    import httpx

    def test():
        # URL de prueba - PDF de Carlos Tejedor
        url = "https://boletin.carlostejedor.gob.ar/pdfs/balances_f572eef0b91f.pdf"

        console.print("[cyan]📥 Descargando PDF de prueba...[/cyan]")

        with httpx.Client(timeout=60.0) as client:
            response = client.get(url)
            if response.status_code != 200:
                console.print(f"[red]❌ Error: {response.status_code}[/red]")
                return

            result = extract_pdf_with_glm_ocr(
                response.content,
                url,
                municipio="Carlos Tejedor"
            )

            if result:
                title, content, quality = result
                console.print("\n[bold green]✅ EXTRACCIÓN COMPLETADA[/bold green]")
                console.print(f"Título: {title}")
                console.print(f"Longitud: {len(content):,} caracteres")
                console.print(f"Calidad: {quality['confidence']:.1%} ({quality['quality']})")

                # Mostrar primeras líneas
                lines = content.split('\n')
                console.print("\n[dim]Primeras líneas:[/dim]")
                for line in lines[:10]:
                    if line.strip():
                        console.print(f"  {line[:80]}")
            else:
                console.print("[red]❌ Falló la extracción[/red]")

    test()
