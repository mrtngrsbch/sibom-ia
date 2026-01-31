#!/usr/bin/env python3
"""
web_scraper.py

Scraping flexible de normativas municipales desde múltiples fuentes.
Soporta diferentes estrategias según el tipo de fuente.

@version 1.0.0
@created 2026-01-28
"""

import asyncio
import base64
import json
import os
import re
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
import yaml
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

try:
    from openai import AsyncOpenAI
    VISION_SUPPORT = True
except ImportError:
    VISION_SUPPORT = False

try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Imports de módulos reorganizados
from extractors.normativas_extractor import (
    Normativa, detect_normativa_type, extract_date,
    normalize_year, extract_title
)
from config import SOURCES_FILE, USER_SOURCES_FILE, BOLETINES_DIR, INDEXES_DIR

console = Console()


# =============================================================================
# PDF TEXT CLEANING
# =============================================================================

def clean_pdf_text(text: str) -> str:
    """
    Limpia texto extraído de PDFs con problemas comunes de codificación.
    Corrige:
    - Apóstrofes entre dígitos -> punto decimal
    - Espacios entre dígitos dentro de números (solo en contextos monetarios)
    - Comillas tipográficas
    """
    if not text:
        return text

    # 1. Apóstrofes entre dígitos -> punto decimal
    # Ejemplo: 24'5 -> 24.5, 273'203'00 -> 273.203.00
    text = re.sub(r"(\d)'(\d)", r'\1.\2', text)

    # 2. Eliminar espacios entre dígitos en contextos numéricos/monetarios
    # Patrón: $ X Y Z donde X, Y, Z son grupos numéricos separados por espacios
    # Solo afecta números cerca del símbolo $
    while re.search(r'\$[\d\.,]+\s+\d', text):
        text = re.sub(r'(\$[\d\.,]+\d)\s+(\d{3})', r'\1\2', text)

    # Para casos generales: dígito-punto-espacio-dígito (X. Y -> X.Y)
    text = re.sub(r'(\d\.\d)\s+(\d)', r'\1\2', text)

    # 3. Comillas tipográficas a ASCII
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")

    # 4. Espacios excesivos (pero solo fuera de números)
    text = re.sub(r'\s+', ' ', text)

    # 5. Caracteres de control
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

    return text.strip()


def validate_pdf_quality(content: str, min_expected_chars: int = 500) -> dict:
    """
    Valida la calidad del texto extraído de un PDF.
    Retorna metadatos sobre la calidad y problemas detectados.

    Args:
        content: Texto extraído del PDF
        min_expected_chars: Caracteres mínimos esperados (para detectar PDFs escaneados)

    Returns:
        Dict con:
        - confidence: 0.0-1.0 (puntaje de calidad)
        - needs_review: bool (requiere revisión manual)
        - warnings: list[str] (problemas detectados)
        - extraction_quality: "excelent|good|fair|poor|failed"
    """
    if not content:
        return {
            "confidence": 0.0,
            "needs_review": True,
            "warnings": ["texto_vacio"],
            "extraction_quality": "failed"
        }

    warnings = []
    score = 1.0
    clean_content = re.sub(r'\s+', ' ', content).strip()

    # 1. Longitud del texto (PDF escaneado sin OCR)
    if len(clean_content) < 100:
        score -= 0.8
        warnings.append(f"texto_muy_corto:{len(clean_content)}")
    elif len(clean_content) < min_expected_chars:
        score -= 0.3
        warnings.append(f"texto_por_debajo_esperado:{len(clean_content)}")

    # 2. Caracteres corruptos comunes (secuencias extrañas de puntuación + mayúsculas)
    corrupt_patterns = [
        r'[,\.;][A-ZÓÚÑ][a-zóúñ]?',  # ,Óo, o., etc
        r"[a-z]['`]",  # palabras terminando en apóstrofe
    ]
    for pattern in corrupt_patterns:
        matches = re.findall(pattern, content)
        if len(matches) > 5:
            score -= min(0.1, len(matches) * 0.01)
            warnings.append(f"caracteres_corruptos:{len(matches)}")
            break

    # 3. Proporción de caracteres no ASCII
    non_ascii = sum(1 for c in content if ord(c) > 127)
    if len(content) > 0:
        ascii_ratio = 1 - (non_ascii / len(content))
        if ascii_ratio < 0.7:  # Menos del 70% ASCII
            score -= 0.2
            warnings.append(f"muchos_no_ascii:{ascii_ratio:.1%}")

    # 4. Palabras rotas (letras sueltas rodeadas de espacios)
    broken_words = re.findall(r'\s[A-Z]\s', content)
    if len(broken_words) > 20:
        score -= 0.1
        warnings.append(f"letras_solas:{len(broken_words)}")

    # 5. Números monetarios con espacios irregulares (después de limpieza)
    # Si todavía hay "$ X Y" con espacios, la limpieza no funcionó bien
    money_with_spaces = re.findall(r'\$\s*\d[\s,]+\d[\s,]+\d', clean_content)
    if money_with_spaces:
        for m in money_with_spaces:
            if re.search(r'\d\s+\d', m):  # dígitos con espacios entre ellos
                score -= 0.05
                warnings.append(f"numero_con_espacios:{m[:30]}")
                break

    # 6. Densidad de texto (caracteres por palabra, debe ser ~5-6 en español)
    words = clean_content.split()
    if words:
        avg_word_len = sum(len(w.strip('.,;:')) for w in words) / len(words)
        if avg_word_len < 3:  # Palabras muy cortas = probable corrupción
            score -= 0.1
            warnings.append(f"palabras_cortas:{avg_word_len:.1f}")

    # Determinar nivel de calidad
    if score >= 0.9:
        quality = "excellent"
        needs_review = False
    elif score >= 0.7:
        quality = "good"
        needs_review = False
    elif score >= 0.5:
        quality = "fair"
        needs_review = True
    elif score >= 0.3:
        quality = "poor"
        needs_review = True
    else:
        quality = "failed"
        needs_review = True

    return {
        "confidence": round(max(0, score), 2),
        "needs_review": needs_review,
        "warnings": warnings[:5],  # Máximo 5 warnings
        "extraction_quality": quality,
        "char_count": len(clean_content),
        "word_count": len(words) if words else 0
    }


async def extract_pdf_text(content: bytes, url: str, use_vision_fallback: bool = True) -> tuple[str, str, dict]:
    """
    Extrae texto de un PDF y lo limpia.
    Si la calidad es baja, usa modelo de visión como fallback.

    Args:
        content: Contenido del PDF en bytes
        url: URL del PDF (para metadatos)
        use_vision_fallback: Si es True, usa Vision API cuando pdfplumber falla

    Returns:
        (title, content, quality) - Título, contenido limpio y metadatos de calidad
    """
    if not PDF_SUPPORT:
        return Path(url).name, "[PDF - instalar pdfplumber para extraer contenido]", {
            "confidence": 0.0, "needs_review": True, "warnings": ["sin_pdfplumber"],
            "extraction_quality": "failed"
        }

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=True) as tmp:
        tmp.write(content)
        tmp.flush()

        try:
            with pdfplumber.open(tmp.name) as pdf:
                # Primera página para título
                first_page = pdf.pages[0].extract_text() or ""

                # Unir todas las páginas
                full_text = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(page_text)

                # Limpiar texto
                cleaned_full = clean_pdf_text('\n'.join(full_text))
                cleaned_first = clean_pdf_text(first_page)

                # Extraer título (primera línea o nombre del archivo)
                title_line = cleaned_first.split(
                    '\n')[0] if cleaned_first else Path(url).name
                title = title_line[:100]

                # Validar calidad
                quality = validate_pdf_quality(cleaned_full)

                # Decidir si usar Vision API como fallback
                # Se activa si:
                # 1. La confianza está por debajo del umbral, O
                # 2. Hay muchos warnings (caracteres corruptos, letras sueltas, etc.)
                warning_count = len(quality.get("warnings", []))
                has_severe_corruption = any(
                    "caracteres_corruptos" in w or "letras_solas" in w for w in quality.get("warnings", []))

                should_use_vision = (
                    use_vision_fallback
                    and VISION_SUPPORT
                    and (
                        quality["confidence"] < VISION_FALLBACK_THRESHOLD
                        or (has_severe_corruption and warning_count >= 2)
                    )
                )

                if should_use_vision:
                    reason = "corrupción detectada" if has_severe_corruption else f"confianza {quality['confidence']:.1%}"
                    console.print(
                        f"[yellow]⚠️ Usando Vision API ({reason})...[/yellow]")

                    try:
                        vision_text = await extract_pdf_with_vision(content, url)
                        if vision_text:
                            # Actualizar con texto de Vision
                            cleaned_full = vision_text
                            title = cleaned_full.split('\n')[0][:100]

                            # Re-validar con el nuevo texto
                            quality = validate_pdf_quality(cleaned_full)
                            quality["extraction_method"] = "vision_api"
                            quality["original_confidence"] = quality.get(
                                "confidence", 0)
                            quality["confidence"] = min(
                                # Boost por usar Vision
                                quality["confidence"] + 0.3, 1.0)

                            console.print(
                                f"[green]✅ Vision API mejoró calidad a: {quality['confidence']:.1%}[/green]")
                    except Exception as e:
                        console.print(
                            f"[yellow]⚠️ Fallback Vision falló: {e}, usando pdfplumber[/yellow]")
                        quality["vision_error"] = str(e)

                return title, cleaned_full, quality

        except Exception as e:
            return Path(url).name, f"[Error extrayendo PDF: {e}]", {
                "confidence": 0.0, "needs_review": True, "warnings": [f"extraction_error:{e}"],
                "extraction_quality": "failed"
            }


async def extract_pdf_with_vision(content: bytes, url: str) -> Optional[str]:
    """
    Extrae texto de un PDF usando modelo de visión.

    Convierte cada página a imagen y usa un modelo multimodal para extraer texto.
    Ideal para PDFs escaneados o con problemas de codificación.

    Args:
        content: Contenido del PDF en bytes
        url: URL del PDF (para logging)

    Returns:
        Texto extraído del PDF o None si falla
    """
    if not VISION_SUPPORT:
        console.print(
            "[dim]ℹ️ Vision API no disponible (instala openai)[/dim]")
        return None

    # Verificar API key
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[dim]ℹ️ No se encontró API key para Vision[/dim]")
        return None

    # Convertir PDF a imágenes
    images = await _pdf_to_images(content)
    if not images:
        console.print(
            "[yellow]⚠️ No se pudieron convertir las páginas a imágenes[/yellow]")
        return None

    # Limitar páginas para controlar costos
    pages_to_process = min(len(images), VISION_MAX_PAGES)
    if len(images) > VISION_MAX_PAGES:
        console.print(
            f"[dim]ℹ️ Procesando {pages_to_process} de {len(images)} páginas (limitado por VISION_MAX_PAGES)[/dim]")

    # Crear cliente OpenAI con endpoint de OpenRouter
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    full_text = []

    for i, image_base64 in enumerate(images[:pages_to_process]):
        try:
            response = await client.chat.completions.create(
                model=VISION_MODEL_ID,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Extrae TODO el texto de esta imagen de un documento legal (ordenanza, decreto, resolución). "
                                    "Mantén el formato original, incluyendo números, fechas y artículos. "
                                    "NO resumas, NO interpretes, SOLO extrae el texto literalmente. "
                                    "Si hay tablas, inclúyelas en formato de texto legible."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.0,  # Determinista para mejor OCR
            )

            page_text = response.choices[0].message.content or ""
            full_text.append(f"--- PÁGINA {i + 1} ---\n{page_text}")

        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error procesando página {i + 1} con Vision: {e}[/yellow]")
            continue

    await client.close()

    if not full_text:
        return None

    return clean_pdf_text('\n\n'.join(full_text))


async def extract_bulletin_with_vision(
    content: bytes,
    url: str,
    municipio: str = "Desconocido"
) -> Optional[tuple[str, str, dict]]:
    """
    Extrae texto de un boletín usando Vision API con prompt especial para columnas.

    Esta es la función RECOMENDADA para boletines municipales que típicamente
    tienen layout de 2 columnas. Usa un prompt específico que instruye al modelo
    a leer columnas por separado.

    Args:
        content: Contenido del PDF en bytes
        url: URL del PDF (para metadatos)
        municipio: Nombre del municipio

    Returns:
        (title, content, quality) o None si falla o se alcanza el límite diario
    """
    if not VISION_SUPPORT:
        console.print("[dim]ℹ️ Vision API no disponible (instala openai)[/dim]")
        return None

    # Verificar rate limit
    from utils.vision_rate_limiter import get_rate_limiter
    limiter = get_rate_limiter()

    if not limiter.can_request():
        stats = limiter.get_stats()
        console.print(
            f"[red]❌ Límite diario de Vision API alcanzado ({stats['today']}/{stats['limit']})[/red]"
        )
        console.print("[yellow]💡 Intenta de nuevo mañana o usa una API key con más límite[/yellow]")
        return None

    # Verificar API key
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[dim]ℹ️ No se encontró API key para Vision[/dim]")
        return None

    console.print(f"[cyan]🔍 Vision API para boletín: {Path(url).name}[/cyan]")

    # Convertir PDF a imágenes
    images = await _pdf_to_images(content)
    if not images:
        console.print("[yellow]⚠️ No se pudieron convertir las páginas a imágenes[/yellow]")
        return None

    # Procesar TODAS las páginas (sin límite para boletines)
    pages_to_process = len(images)
    console.print(f"[dim]  → Procesando {pages_to_process} páginas...[/dim]")

    # Registrar la request
    if not limiter.check_and_request():
        return None

    # Crear cliente
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # Prompt específico para boletines con columnas
    prompt = (
        "Extrae TODO el texto de esta imagen de un boletín municipal legal. "
        "IMPORTANTE: Este documento puede tener DOS COLUMNAS. "
        "Debes leer la COLUMNA IZQUIERDA completa primero, luego la COLUMNA DERECHA completa. "
        "NO mezcles el texto entre columnas. "
        "Mantén el formato original, incluyendo números, fechas y artículos. "
        "NO resumas, NO interpretes, SOLO extrae el texto literalmente. "
        "Si hay tablas, inclúyelas en formato de texto legible."
    )

    full_text = []
    total_tokens = 0

    for i, image_base64 in enumerate(images):
        try:
            response = await client.chat.completions.create(
                model=VISION_MODEL_ID,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                            }
                        ]
                    }
                ],
                max_tokens=8192,  # Más tokens para boletines completos
                temperature=0.0,
            )

            page_text = response.choices[0].message.content or ""
            total_tokens += response.usage.total_tokens if hasattr(response, 'usage') else 0

            # Solo marcar página si hay contenido significativo
            if len(page_text) > 50:
                full_text.append(page_text)
            else:
                console.print(f"[dim]    Página {i + 1}: poco contenido ({len(page_text)} chars)[/dim]")

        except Exception as e:
            console.print(f"[yellow]  ⚠️ Error en página {i + 1}: {e}[/yellow]")
            continue

    await client.close()

    if not full_text:
        return None

    # Unir todo el texto
    complete_text = '\n\n'.join(full_text)

    # Extraer título (primera línea o nombre del archivo)
    first_line = complete_text.split('\n')[0] if complete_text else ""
    title = first_line[:100] if first_line else Path(url).name

    # Validar calidad
    quality = validate_pdf_quality(complete_text)
    quality["extraction_method"] = "vision_api_bulletin"
    quality["pages_processed"] = len(full_text)
    quality["total_pages"] = pages_to_process
    quality["municipio"] = municipio

    # Mostrar resultado
    stats = limiter.get_stats()
    console.print(
        f"[green]✓ Extraídos {len(complete_text):,} caracteres ({quality['confidence']:.1%} calidad)[/green]"
    )
    console.print(f"[dim]  Vision API hoy: {stats['today']}/{stats['limit']} requests[/dim]")

    return title, complete_text, quality


async def _pdf_to_images(content: bytes) -> List[str]:
    """
    Convierte un PDF a una lista de imágenes en base64.

    Args:
        content: Contenido del PDF en bytes

    Returns:
        Lista de imágenes en formato base64 PNG
    """
    if not PDF_SUPPORT:
        return []

    images = []

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=True) as tmp:
        tmp.write(content)
        tmp.flush()

        try:
            import pdf2image  # Necesario: pip install pdf2image
            from io import BytesIO

            # Convertir PDF a imágenes
            pillow_images = pdf2image.convert_from_path(
                tmp.name,
                dpi=200,  # Buen balance calidad/tamaño
                fmt='png'
            )

            for img in pillow_images:
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                images.append(base64.b64encode(
                    buffer.getvalue()).decode('utf-8'))

        except ImportError:
            console.print(
                "[yellow]⚠️ Instala pdf2image para usar Vision API: pip install pdf2image[/yellow]")
        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error convirtiendo PDF a imágenes: {e}[/yellow]")

    return images


# =============================================================================
# VISION MODELS CONFIGURATION (OpenRouter)
# =============================================================================
# Modelos de visión analizados por precio y capacidad OCR para fallback de PDFs.
# Cambia VISION_MODEL_ID para usar otro modelo.
#
# ┌────────────────────────────────────────────────────────────────────────────┐
# │ MEJORES MODELOS DE VISIÓN PARA OCR (OpenRouter)                           │
# ├────────────────────────────────────────────────────────────────────────────┤
# │                                                                            │
# │ 🏆 GRATIS Y EXCELENTE:                                                     │
# │   nvidia/nemotron-nano-12b-v2-vl:free                                     │
# │   - Precio: GRATIS                                                         │
# │   - OCR: Excelente (60%)                                                   │
# │   - Contexto: 128,000 tokens                                               │
# │                                                                            │
# │ ⭐ MEJOR OCR (PAGA):                                                       │
# │   qwen/qwen3-vl-235b-a22b-instruct                                        │
# │   - Precio: ~$1.2000 / 1M tokens                                          │
# │   - OCR: Excelente (90%)                                                   │
# │   - Contexto: 262,144 tokens                                               │
# │                                                                            │
# │ 🆓 OTRAS OPCIONES GRATIS:                                                  │
# │   - google/gemini-2.0-flash-exp:free       (Alta: 50%, 1M ctx)           │
# │   - qwen/qwen-2.5-vl-7b-instruct:free     (Alta: 50%, 32K ctx)           │
# │   - mistralai/mistral-small-3.1-24b-instruct:free  (Media: 35%)           │
# │                                                                            │
# │ 💰 MEJOR RELACIÓN CALIDAD-PRECIO:                                         │
# │   mistralai/pixtral-12b                    ($0.0000, Media: 35%)          │
# │   mistralai/pixtral-large-2411             ($6.0000, Excelente: 65%)      │
# │                                                                            │
# │ 🔗 Para ver lista completa:                                                │
# │   https://openrouter.ai/models?fmt=cards&input_modalities=image            │
# │                                                                            │
# └────────────────────────────────────────────────────────────────────────────┘

# Modelo activo para fallback de PDFs (cambiar según necesidad)
VISION_MODEL_ID = "qwen/qwen3-vl-235b-a22b-instruct"  # Mejor OCR - TOP !

# Umbral de calidad para activar fallback (0.0-1.0)
# Si pdfplumber obtiene confidence < este valor, se usa Vision API
VISION_FALLBACK_THRESHOLD = 0.5

# Máximo de páginas a procesar con Vision API (para controlar costos)
VISION_MAX_PAGES = 5


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class SourceConfig:
    """Configuración de una fuente de datos"""
    name: str
    type: str  # sibom, wordpress, generic, manual
    enabled: bool
    base_url: str
    url_patterns: List[str] = None
    document_types: List[str] = None
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> 'SourceConfig':
        return cls(
            name=data['name'],
            type=data['type'],
            enabled=data.get('enabled', True),
            base_url=data['base_url'],
            url_patterns=data.get('url_patterns', []),
            document_types=data.get('document_types', []),
            description=data.get('description', '')
        )


@dataclass
class ScrapedDocument:
    """Documento extraído de una fuente web"""
    url: str
    title: str
    content: str
    source_type: str  # pdf, html
    metadata: dict[str, Any]
    municipality: str


# =============================================================================
# BASE SCRAPER
# =============================================================================

class BaseScraper(ABC):
    """Base para todos los scrapers"""

    def __init__(self, config: SourceConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.documents: List[ScrapedDocument] = []

    @abstractmethod
    async def scrape(self) -> List[ScrapedDocument]:
        """Ejecuta el scraping y retorna documentos encontrados"""
        pass

    async def close(self):
        """Cierra conexiones"""
        await self.client.aclose()


# =============================================================================
# WORDPRESS SCRAPER
# =============================================================================

class WordPressScraper(BaseScraper):
    """
    Scraper para sitios WordPress de municipios.
    Muchos municipios usan WordPress para su sitio web.
    """

    async def scrape(self) -> List[ScrapedDocument]:
        console.print(f"[cyan]🔍 Scraping WordPress: {self.config.name}[/cyan]")

        documents = []

        try:
            # 1. Buscar página de normativas
            normativa_urls = await self._find_normativa_pages()

            console.print(f"  📄 Páginas encontradas: {len(normativa_urls)}")

            # 2. Extraer documentos de cada página
            for url in normativa_urls:
                docs = await self._scrape_page(url)
                documents.extend(docs)

            # 3. Buscar PDFs directamente
            pdf_urls = await self._find_pdfs()
            console.print(f"  📑 PDFs encontrados: {len(pdf_urls)}")

            for pdf_url in pdf_urls:
                doc = await self._scrape_pdf(pdf_url)
                if doc:
                    documents.append(doc)

        except Exception as e:
            console.print(
                f"[red]❌ Error scraping {self.config.name}: {e}[/red]")

        self.documents = documents
        return documents

    async def _find_normativa_pages(self) -> List[str]:
        """Busca páginas de normativas"""
        urls = []

        # Patrones comunes en WordPress
        paths = [
            "/normativa/",
            "/ordenanzas/",
            "/decretos/",
            "/resoluciones/",
            "/normativa/ordenanzas/",
            "/normativa/decretos/",
        ]

        for path in paths:
            url = urljoin(self.config.base_url, path)
            try:
                response = await self.client.get(url)
                if response.status_code == 200:
                    urls.append(url)
                    # Buscar enlaces a más páginas
                    soup = BeautifulSoup(response.text, 'html.parser')
                    urls.extend(self._extract_page_links(soup, url))
            except Exception:
                continue

        return list(set(urls))

    def _extract_page_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extrae enlaces a páginas de normativas"""
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True).lower()

            # Filtrar enlaces relevantes
            if any(term in text or href for term in ['ordenanza', 'decreto', 'resolución', 'normativa']):
                full_url = urljoin(base_url, href)
                if self._is_same_domain(full_url):
                    links.append(full_url)

        return links

    def _is_same_domain(self, url: str) -> bool:
        """Verifica si la URL es del mismo dominio"""
        base_domain = urlparse(self.config.base_url).netloc
        url_domain = urlparse(url).netloc
        return url_domain == base_domain

    async def _find_pdfs(self) -> List[str]:
        """Busca PDFs en el sitio"""
        pdf_urls = []

        # Patrones comunes para PDFs de normativas
        patterns = [
            "/wp-content/uploads/**/*.pdf",
            "/ordenanzas/**/*.pdf",
            "/decretos/**/*.pdf",
            "/normativas/**/*.pdf",
        ]

        # Nota: Para búsqueda completa de PDFs necesitaríamos
        # hacer crawling más exhaustivo o usar sitemap

        return pdf_urls

    async def _scrape_page(self, url: str) -> List[ScrapedDocument]:
        """Extrae contenido de una página HTML"""
        documents = []

        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return documents

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extraer título
            title = soup.find('h1', class_='entry-title')
            if not title:
                title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ""

            # Extraer contenido
            content_div = soup.find(
                'div', class_='entry-content') or soup.find('article')
            if content_div:
                content = content_div.get_text(separator='\n', strip=True)

                # Detectar tipo de normativa
                doc_type = self._detect_document_type(
                    title_text + " " + content)

                documents.append(ScrapedDocument(
                    url=url,
                    title=title_text,
                    content=content[:10000],  # Limitar contenido
                    source_type="html",
                    metadata={
                        "municipality": self.config.name,
                        "type": doc_type
                    },
                    municipality=self.config.name
                ))

        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error scrapeando página {url}: {e}[/yellow]")

        return documents

    async def _scrape_pdf(self, url: str) -> Optional[ScrapedDocument]:
        """Extrae contenido de un PDF con limpieza de codificación y validación de calidad"""
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return None

            title, content, quality = await extract_pdf_text(response.content, url)

            # Detectar tipo de normativa
            doc_type = self._detect_document_type(title + " " + content)

            # Mostrar warnings si hay problemas de calidad
            if quality["warnings"]:
                warning_str = ", ".join(quality["warnings"])
                if quality["needs_review"]:
                    console.print(
                        f"[yellow]⚠️ PDF necesita revisión: {url}[/yellow]")
                    console.print(
                        f"[yellow]   Warnings: {warning_str}[/yellow]")
                else:
                    console.print(
                        f"[dim]ℹ️ PDF calidad {quality['extraction_quality']}: {url}[/dim]")

            # Guardar calidad en metadata
            metadata = {
                "municipality": self.config.name,
                "type": doc_type,
                "quality": quality["extraction_quality"],
                "confidence": quality["confidence"],
                "needs_review": quality["needs_review"]
            }

            return ScrapedDocument(
                url=url,
                title=title,
                content=content[:50000],
                source_type="pdf",
                metadata=metadata,
                municipality=self.config.name
            )

        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error scrapeando PDF {url}: {e}[/yellow]")
            return None

    def _detect_document_type(self, text: str) -> str:
        """Detecta el tipo de normativa basado en el texto"""
        text_lower = text.lower()

        if 'ordenanza' in text_lower:
            return 'ordenanza'
        elif 'decreto' in text_lower:
            return 'decreto'
        elif 'resoluci' in text_lower:
            return 'resolucion'
        elif 'disposici' in text_lower:
            return 'disposicion'
        else:
            return 'normativa'


# =============================================================================
# GENERIC SCRAPER
# =============================================================================

class GenericScraper(BaseScraper):
    """Scraper genérico para sitios no identificados"""

    async def scrape(self) -> List[ScrapedDocument]:
        console.print(f"[cyan]🔍 Scraping genérico: {self.config.name}[/cyan]")

        documents = []

        # Estrategia: buscar enlaces a PDFs
        try:
            response = await self.client.get(self.config.base_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                pdf_links = self._find_pdf_links(soup)

                console.print(f"  📑 PDFs encontrados: {len(pdf_links)}")

                for pdf_url in pdf_links:
                    doc = await self._scrape_pdf(pdf_url)
                    if doc:
                        documents.append(doc)

        except Exception as e:
            console.print(
                f"[red]❌ Error scraping genérico {self.config.name}: {e}[/red]")

        return documents

    async def _scrape_pdf(self, url: str) -> Optional[ScrapedDocument]:
        """Extrae contenido de un PDF con limpieza de codificación y validación de calidad"""
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return None

            title, content, quality = await extract_pdf_text(response.content, url)

            # Mostrar warnings si hay problemas de calidad
            if quality["warnings"]:
                warning_str = ", ".join(quality["warnings"])
                if quality["needs_review"]:
                    console.print(
                        f"[yellow]⚠️ PDF necesita revisión: {url}[/yellow]")
                    console.print(
                        f"[yellow]   Warnings: {warning_str}[/yellow]")
                else:
                    console.print(
                        f"[dim]ℹ️ PDF calidad {quality['extraction_quality']}: {url}[/dim]")

            return ScrapedDocument(
                url=url,
                title=title,
                content=content[:50000],
                source_type="pdf",
                metadata={
                    "municipality": self.config.name,
                    "quality": quality["extraction_quality"],
                    "confidence": quality["confidence"],
                    "needs_review": quality["needs_review"]
                },
                municipality=self.config.name
            )

        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error scrapeando PDF {url}: {e}[/yellow]")
            return None

    def _find_pdf_links(self, soup: BeautifulSoup) -> List[str]:
        """Busca enlaces a PDFs"""
        pdf_urls = []

        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if href.endswith('.pdf'):
                full_url = urljoin(self.config.base_url, link['href'])
                pdf_urls.append(full_url)

        return pdf_urls

    def _extract_title_from_filename(self, filename: str) -> str:
        """Intenta extraer un título del nombre del archivo"""
        # Ejemplo: "Ordenanza_123_2025.pdf" -> "Ordenanza 123/2025"

        # Remover extensión
        name = filename.replace('.pdf', '')

        # Reemplazar guiones bajos y otros separadores
        name = re.sub(r'[_\-]+', ' ', name)

        # Intentar detectar número y año
        match = re.search(r'(\d{2,5})[_\s\-]*(\d{4})', name)
        if match:
            number, year = match.groups()
            name = re.sub(r'\d+[_\s\-]*\d+', f'{number}/{year}', name)

        return name


# =============================================================================
# MANUAL SCRAPER (para URLs específicas)
# =============================================================================

class ManualScraper(BaseScraper):
    """Scraper para URLs específicas proveídas manualmente"""

    def __init__(self, config: SourceConfig, urls: List[str] = None):
        super().__init__(config)
        self.urls = urls or config.url_patterns or []

    async def scrape(self) -> List[ScrapedDocument]:
        console.print(
            f"[cyan]🔍 Scraping manual: {self.config.name} ({len(self.urls)} URLs)[/cyan]")

        documents = []

        for url in self.urls:
            try:
                if url.endswith('.pdf'):
                    doc = await self._scrape_pdf(url)
                    if doc:
                        documents.append(doc)
                else:
                    docs = await self._scrape_html(url)
                    documents.extend(docs)

            except Exception as e:
                console.print(f"[yellow]⚠️ Error con {url}: {e}[/yellow]")

        return documents

    async def _scrape_pdf(self, url: str) -> Optional[ScrapedDocument]:
        """Extrae contenido de un PDF con limpieza de codificación y validación de calidad"""
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return None

            title, content, quality = await extract_pdf_text(response.content, url)

            # Mostrar warnings si hay problemas de calidad
            if quality["warnings"]:
                warning_str = ", ".join(quality["warnings"])
                if quality["needs_review"]:
                    console.print(
                        f"[yellow]⚠️ PDF necesita revisión: {url}[/yellow]")
                    console.print(
                        f"[yellow]   Warnings: {warning_str}[/yellow]")
                else:
                    console.print(
                        f"[dim]ℹ️ PDF calidad {quality['extraction_quality']}: {url}[/dim]")

            return ScrapedDocument(
                url=url,
                title=title,
                content=content[:50000],
                source_type="pdf",
                metadata={
                    "municipality": self.config.name,
                    "quality": quality["extraction_quality"],
                    "confidence": quality["confidence"],
                    "needs_review": quality["needs_review"]
                },
                municipality=self.config.name
            )

        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error scrapeando PDF {url}: {e}[/yellow]")
            return None

    async def _scrape_html(self, url: str) -> List[ScrapedDocument]:
        documents = []

        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return documents

            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else ""

            # Extraer contenido principal
            content = soup.get_text(separator='\n', strip=True)

            documents.append(ScrapedDocument(
                url=url,
                title=title_text,
                content=content[:10000],
                source_type="html",
                metadata={"municipality": self.config.name},
                municipality=self.config.name
            ))

        except Exception as e:
            console.print(f"[yellow]⚠️ Error scrapeando {url}: {e}[/yellow]")

        return documents


# =============================================================================
# SCRAPER FACTORY
# =============================================================================

SCRAPER_CLASSES = {
    'wordpress': WordPressScraper,
    'generic': GenericScraper,
    'manual': ManualScraper,
    'discovery': None,  # Se maneja especialmente
    # 'sibom': SIBOMScraper,  # Ya implementado en sibom_scraper.py
}


def create_scraper(config: SourceConfig) -> BaseScraper:
    """Crea un scraper según el tipo de fuente"""
    if config.type == 'discovery':
        # Discovery se maneja especialmente en scrape_all_sources
        return None

    scraper_class = SCRAPER_CLASSES.get(config.type, GenericScraper)

    if config.type == 'manual':
        return ManualScraper(config)
    else:
        return scraper_class(config)


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

async def scrape_all_sources(
    sources_file: Path = None,
    filter_names: List[str] = None
) -> dict[str, List[ScrapedDocument]]:
    """
    Ejecuta scraping de todas las fuentes configuradas

    Args:
        sources_file: Archivo YAML con configuración (por defecto: sources.yaml)
        filter_names: Filtra por nombre de fuente (solo estos)

    Returns:
        Diccionario {nombre_fuente: [documentos]}
    """
    # Cargar configuración
    config_file = sources_file or SOURCES_FILE

    # También cargar archivo de usuario si existe
    if USER_SOURCES_FILE.exists():
        console.print(
            f"[green]📋 Cargando configuración de usuario: {USER_SOURCES_FILE}[/green]")
        sources_file = USER_SOURCES_FILE

    with open(config_file) as f:
        config_data = yaml.safe_load(f)

    sources = [SourceConfig.from_dict(s)
               for s in config_data.get('sources', [])]

    # Filtrar si se especificó
    if filter_names:
        sources = [s for s in sources if s.name in filter_names]

    # Filtrar solo habilitadas
    sources = [s for s in sources if s.enabled]

    console.print(
        f"\n[cyan]🚀 Iniciando scraping de {len(sources)} fuentes...[/cyan]\n")

    # Ejecutar scraping en paralelo
    results = {}
    all_normativas: List[Normativa] = []

    for source in sources:
        try:
            # Caso especial: tipo discovery
            if source.type == 'discovery':
                from utils.discovery import PDFDiscovery
                import os

                serpapi_key = os.getenv("SERPAPI_KEY")
                max_pdfs = source.url_patterns[0] if source.url_patterns else 100
                if isinstance(max_pdfs, str) and max_pdfs.isdigit():
                    max_pdfs = int(max_pdfs)

                discovery = PDFDiscovery(
                    serpapi_key=serpapi_key,
                    max_results=max_pdfs
                )

                try:
                    domain = urlparse(source.base_url).netloc
                    discovered_pdfs = await discovery.discover_pdfs(
                        source.base_url,
                        domain
                    )

                    # Ahora scrapear los PDFs descubiertos
                    documents = []
                    for pdf_info in discovered_pdfs[:max_pdfs]:
                        doc = await _scrape_discovered_pdf(pdf_info, source.name)
                        if doc:
                            documents.append(doc)

                    results[source.name] = documents
                    console.print(
                        f"[green]✅ {source.name}: {len(documents)} documentos (discovery)[/green]")

                finally:
                    await discovery.close()
            else:
                scraper = create_scraper(source)
                documents = await scraper.scrape()

                results[source.name] = documents
                console.print(
                    f"[green]✅ {source.name}: {len(documents)} documentos[/green]")

            # Convertir a Normativa y guardar archivos
            if documents:
                normativas = convert_to_normativas(
                    documents,
                    bulletin_name=f"web_{source.name.replace(' ', '_')}"
                )
                all_normativas.extend(normativas)

                # Guardar JSON individual y actualizar índices
                await save_normativas_to_files(
                    normativas,
                    municipality=source.name
                )

            await scraper.close()

        except Exception as e:
            console.print(f"[red]❌ {source.name}: Error - {e}[/red]")
            results[source.name] = []

    # Resumen
    console.print(f"\n[cyan]📊 RESUMEN:[/cyan]")
    table = Table(title="Documentos por fuente")
    table.add_column("Fuente", style="cyan")
    table.add_column("Documentos", justify="right")
    table.add_column("Normativas", justify="right")
    table.add_column("Estado")

    total = 0
    for name, docs in results.items():
        status = "[green]✓[/green]" if docs else "[red]✗[/red]"
        table.add_row(name, str(len(docs)), str(len(docs)), status)
        total += len(docs)

    table.add_row("TOTAL", str(total), str(len(all_normativas)), "")
    console.print(table)

    # Opcionalmente actualizar SQLite
    if all_normativas:
        try:
            from sibom_scraper import update_sqlite_database
            from config import DEFAULT_DB_PATH
            console.print(
                f"\n[cyan]🗄️ Actualizando SQLite con {len(all_normativas)} normativas...[/cyan]")
            update_sqlite_database(
                all_normativas, db_path=str(DEFAULT_DB_PATH))
        except Exception as e:
            console.print(
                f"[yellow]⚠️ No se pudo actualizar SQLite: {e}[/yellow]")

    return results


async def _scrape_discovered_pdf(
    pdf_info: Any,
    municipality: str
) -> Optional[ScrapedDocument]:
    """
    Scrapea un PDF descubierto por el módulo discovery.

    Args:
        pdf_info: Objeto DiscoveredPDF del módulo discovery
        municipality: Nombre del municipio

    Returns:
        ScrapedDocument o None si falla
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(pdf_info.url)
            if response.status_code != 200:
                console.print(
                    f"[dim]    Error {response.status_code}: {pdf_info.url[:50]}...[/dim]")
                return None

            # Extraer contenido del PDF
            title, content, quality = await extract_pdf_text(
                response.content,
                pdf_info.url,
                use_vision_fallback=True
            )

            # Usar título descubierto o extraído
            doc_title = pdf_info.title or title

            return ScrapedDocument(
                url=pdf_info.url,
                title=doc_title,
                content=content[:50000],  # Limitar contenido
                source_type="pdf",
                metadata={
                    "municipality": municipality,
                    "quality": quality.get("extraction_quality", "unknown"),
                    "confidence": quality.get("confidence", 0),
                    "needs_review": quality.get("needs_review", False),
                    "discovery_source": pdf_info.source
                },
                municipality=municipality
            )

    except Exception as e:
        console.print(f"[yellow]    Error scrapeando PDF: {e}[/yellow]")
        return None


async def scrape_urls(
    urls: List[str],
    municipality: str = "Desconocido",
    save_results: bool = True
) -> List[ScrapedDocument]:
    """
    Scrapea una lista específica de URLs

    Args:
        urls: Lista de URLs a scrapear
        municipality: Nombre del municipio
        save_results: Si es True, guarda JSON y actualiza índices

    Returns:
        Lista de documentos extraídos
    """
    console.print(
        f"[cyan]🔍 Scrapeando {len(urls)} URLs para {municipality}...[/cyan]")

    config = SourceConfig(
        name=municipality,
        type="manual",
        enabled=True,
        base_url=urls[0] if urls else "",
        url_patterns=urls
    )

    scraper = ManualScraper(config, urls)
    documents = await scraper.scrape()
    await scraper.close()

    console.print(f"[green]✅ Extraídos {len(documents)} documentos[/green]")

    # Convertir a Normativa y guardar si se solicitó
    if save_results and documents:
        normativas = convert_to_normativas(
            documents,
            bulletin_name=f"web_{municipality.replace(' ', '_')}"
        )

        await save_normativas_to_files(
            normativas,
            municipality=municipality
        )

        # Actualizar SQLite
        try:
            from utils.sqlite_manager import get_sqlite_manager
            from config import DEFAULT_DB_PATH
            mgr = get_sqlite_manager(DEFAULT_DB_PATH)
            mgr.insert_normativas(normativas)
        except Exception as e:
            console.print(
                f"[yellow]⚠️ No se pudo actualizar SQLite: {e}[/yellow]")

    return documents


def convert_to_normativas(
    documents: List[ScrapedDocument],
    bulletin_name: str = None
) -> List[Normativa]:
    """
    Convierte documentos scrapeados al formato Normativa.

    Usa las funciones de detección de normativas_extractor.py para
    mantener compatibilidad con sibom_scraper.py.

    Args:
        documents: Lista de documentos scrapeados
        bulletin_name: Nombre del boletín de origen (para source_bulletin)

    Returns:
        Lista de objetos Normativa compatibles con SQLite
    """
    import uuid
    from datetime import datetime
    from extractors.normativas_extractor import (
        detect_normativa_type,
        extract_date,
        normalize_year,
        extract_title
    )

    normativas = []
    timestamp = datetime.now().isoformat()

    for i, doc in enumerate(documents):
        # 1. Detectar tipo y número usando patrones de normativas_extractor
        tipo, numero, year_raw = detect_normativa_type(
            doc.title + "\n" + doc.content[:1000]
        )

        # Si no se detectó tipo, usar el del metadata si existe
        if not tipo:
            tipo = doc.metadata.get('type', 'normativa')

        # 2. Extraer número si no se detectó
        if not numero:
            number_match = re.search(r'(\d{2,5})[/\-]\s*(\d{2,4})', doc.title)
            if number_match:
                numero = number_match.group(1)
                year_raw = year_raw or number_match.group(2)
            else:
                numero_match = re.search(r'\b(\d{2,5})\b', doc.title)
                numero = numero_match.group(1) if numero_match else "0"

        # 3. Normalizar año
        date_str = extract_date(doc.content) or doc.metadata.get('date', '')
        year = normalize_year(year_raw, date_str) or "2024"

        # 4. Extraer/limpiar título
        if doc.title and len(doc.title) > 10:
            title = doc.title[:200]
        else:
            title = extract_title(doc.content, tipo, numero)

        # 5. Generar ID único
        # Formato: {municipio}_{tipo}_{numero}_{year}_{uuid}
        municipio_slug = doc.municipality.replace(' ', '_').replace('-', '_')
        unique_suffix = uuid.uuid4().hex[:8]
        normativa_id = f"{municipio_slug}_{tipo}_{numero}_{year}_{unique_suffix}"

        # 6. Determinar source_bulletin
        if bulletin_name:
            source_bulletin = bulletin_name
        else:
            source_bulletin = doc.metadata.get(
                'source_bulletin',
                f"web_{doc.municipality.replace(' ', '_')}"
            )

        # 7. Crear objeto Normativa con el formato correcto
        normativa = Normativa(
            id=normativa_id,
            municipality=doc.municipality,
            type=tipo,
            number=numero,
            year=year,
            date=date_str,
            title=title,
            content=doc.content,
            source_bulletin=source_bulletin,
            source_bulletin_url=doc.metadata.get('source_bulletin_url', ''),
            norma_url=doc.url,
            doc_index=i,
            status='vigente',
            extracted_at=timestamp
        )

        normativas.append(normativa)

    return normativas


async def save_normativas_to_files(
    normativas: List[Normativa],
    municipality: str,
    output_dir: Path = None
) -> Dict[str, Any]:
    """
    Guarda normativas en el mismo formato que sibom_scraper.py.

    Crea un JSON individual del "boletín" web y actualiza los índices
    globales para compatibilidad con el sistema SIBOM.

    Args:
        normativas: Lista de normativas a guardar
        municipality: Nombre del municipio
        output_dir: Directorio de salida (default: boletines/)

    Returns:
        Dict con rutas de archivos guardados y estadísticas
    """
    from datetime import datetime
    from extractors.normativas_extractor import save_index, save_minimal_index
    from config import BOLETINES_DIR, INDEXES_DIR

    if output_dir is None:
        output_dir = BOLETINES_DIR

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    if not normativas:
        console.print("[yellow]⚠️ No hay normativas para guardar[/yellow]")
        return {"total_normas": 0}

    # 1. Guardar JSON individual del "boletín" web
    # Formato similar al de SIBOM pero para fuentes web
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{municipality.replace(' ', '_')}_{timestamp_str}"
    bulletin_file = output_dir / f"{filename}.json"

    bulletin_data = {
        "municipio": municipality,
        "numero_boletin": "WEB",
        "fecha_boletin": datetime.now().strftime("%Y-%m-%d"),
        "boletin_url": "",
        "status": "completed",
        "total_normas": len(normativas),
        "normas": [norm.to_dict() for norm in normativas],
        "metadata_boletin": {
            "total_caracteres": sum(len(n.content) for n in normativas),
            "total_tablas": 0,  # No extraemos tablas en web_scraper aún
            "total_montos": 0,
            "fecha_scraping": datetime.now().isoformat(),
            "version_scraper": "web_2.0",
            "source_type": "web_scraper"
        }
    }

    with bulletin_file.open('w', encoding='utf-8') as f:
        json.dump(bulletin_data, f, indent=2, ensure_ascii=False)

    console.print(f"[green]✓ Boletín guardado: {bulletin_file.name}[/green]")

    # 2. Actualizar índices globales
    index_file = INDEXES_DIR / "normativas_index.json"
    compact_file = INDEXES_DIR / "normativas_index_compact.json"
    minimal_file = INDEXES_DIR / "normativas_index_minimal.json"

    # Leer índice existente si existe
    existing_normas = []
    if index_file.exists():
        try:
            with index_file.open('r', encoding='utf-8') as f:
                existing_data = json.load(f)
                # El índice puede ser un dict con clave 'normativas' o una lista directa
                if isinstance(existing_data, dict):
                    existing_normas = existing_data.get('normativas', [])
                elif isinstance(existing_data, list):
                    existing_normas = existing_data
        except Exception as e:
            console.print(
                f"[yellow]⚠️ Error leyendo índice existente: {e}[/yellow]")

    # Combinar normativas existentes con nuevas
    all_normas = existing_normas + [n.to_dict() for n in normativas]

    # Guardar índices actualizados
    try:
        save_index(normativas, index_file, compact=False)
        save_index(normativas, compact_file, compact=True)
        save_minimal_index(normativas, minimal_file)
        console.print(
            f"[green]✓ Índices actualizados: {len(normativas)} nuevas normativas[/green]"
        )
    except Exception as e:
        console.print(f"[yellow]⚠️ Error actualizando índices: {e}[/yellow]")

    return {
        "bulletin_file": str(bulletin_file),
        "index_file": str(index_file),
        "total_normas": len(normativas),
        "total_acumulado": len(all_normas)
    }


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scraping flexible de normativas municipales")
    parser.add_argument(
        "--sources", help="Archivo YAML con configuración de fuentes")
    parser.add_argument("--filter", nargs="+",
                        help="Filtrar por nombre de fuente")
    parser.add_argument("--urls", nargs="+",
                        help="URLs específicas para scrapear")
    parser.add_argument(
        "--municipality", help="Nombre del municipio (para URLs específicas)")

    args = parser.parse_args()

    if args.urls:
        # Modo: URLs específicas
        async def main_urls():
            docs = await scrape_urls(args.urls, args.municipality or "Desconocido")
            normativas = convert_to_normativas(docs)
            console.print(
                f"\n[green]💾 Guardando {len(normativas)} normativas...[/green]")

        asyncio.run(main_urls())

    else:
        # Modo: Fuentes configuradas
        async def main_sources():
            await scrape_all_sources(
                sources_file=Path(args.sources) if args.sources else None,
                filter_names=args.filter
            )

        asyncio.run(main_sources())
