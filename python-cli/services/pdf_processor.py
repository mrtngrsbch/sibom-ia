#!/usr/bin/env python3
"""
services/pdf_processor.py

Servicio de procesamiento de PDFs.

Encapsula la lógica de extracción de texto desde PDFs usando Vision API.

@version 2.0.0
@created 2026-02-02
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from rich.console import Console

console = Console()


class PDFProcessor:
    """
    Procesador de PDFs con Vision API.

    Responsabilidades:
    - Extraer texto de PDFs usando Vision API
    - Detectar información de cabecera (periodo, fecha, etc.)
    - Retornar datos estructurados para guardado en JSON

    Estrategia de extracción:
    1. File API (rápido, barato, puede alterar columnas en layouts complejos)
    2. Si falla → Vision chunks (lento, caro, columnas correctas)
    """

    def __init__(self, vision_extractor=None):
        """
        Inicializa el procesador.

        Args:
            vision_extractor: Instancia de VisionExtractor (se crea una si no se proporciona)
        """
        if vision_extractor is None:
            from extractors.vision_extractor import VisionExtractor
            vision_extractor = VisionExtractor()

        self.extractor = vision_extractor

    async def process_pdf(
        self,
        pdf_content: bytes,
        url: str,
        municipio: str,
        extract_tables: bool = True
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Procesa un PDF y extrae su contenido.

        Args:
            pdf_content: Contenido binario del PDF
            url: URL de origen
            municipio: Nombre del municipio
            extract_tables: Si True, usa prompt optimizado para tablas

        Returns:
            Tupla (titulo, contenido, metadata)

            - titulo: Título extraído del documento
            - contenido: Contenido extraído en formato Markdown
            - metadata: Metadatos incluyendo calidad, método usado, etc.
        """
        console.print(f"[cyan]📄 Procesando: {url.split('/')[-1][:50]}...[/cyan]")

        # Usar VisionExtractor
        titulo, contenido, calidad = await self.extractor.extract_pdf(
            pdf_content=pdf_content,
            url=url,
            municipio=municipio,
            extract_tables=extract_tables
        )

        # Metadata adicional
        metadata = {
            **calidad,
            "url_origen": url,
            "procesado_at": datetime.now().isoformat(),
            "tamaño_bytes": len(pdf_content),
            "tamaño_mb": len(pdf_content) / (1024 * 1024)
        }

        return titulo, contenido, metadata

    def generate_filename(
        self,
        url: str,
        municipio: str,
        tipo_documento: str = ""
    ) -> str:
        """
        Genera un nombre de archivo único para el JSON.

        Args:
            url: URL del PDF
            municipio: Nombre del municipio
            tipo_documento: Tipo de documento (opcional)

        Returns:
            Nombre de archivo único
        """
        # Hash de URL para unicidad
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

        # Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Municipio slug
        municipio_slug = municipio.replace(" ", "_")

        # Tipo doc slug
        tipo_slug = tipo_documento.lower().replace(" ", "_")[:20] if tipo_documento else "documento"

        return f"{municipio_slug}_{tipo_slug}_{timestamp}_{url_hash}"

    def save_pdf(self, pdf_content: bytes, output_dir: Path, filename: str) -> Path:
        """
        Guarda el PDF original en disco.

        Args:
            pdf_content: Contenido binario del PDF
            output_dir: Directorio de salida
            filename: Nombre del archivo

        Returns:
            Ruta al PDF guardado
        """
        # Crear subdirectorio pdfs/
        pdf_dir = output_dir / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = pdf_dir / filename

        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)

        return pdf_path

    def save_json(
        self,
        titulo: str,
        contenido: str,
        metadata: Dict[str, Any],
        municipio: str,
        tipo_documento: str,
        output_dir: Path,
        filename: str = None
    ) -> Path:
        """
        Guarda los datos extraídos en formato JSON.

        Args:
            titulo: Título del documento
            contenido: Contenido extraído
            metadata: Metadatos
            municipio: Nombre del municipio
            tipo_documento: Tipo de documento
            output_dir: Directorio de salida
            filename: Nombre del archivo (se genera si no se proporciona)

        Returns:
            Ruta al JSON guardado
        """
        import json

        if filename is None:
            # Usar URL de metadata para generar nombre
            url = metadata.get("url_origen", "")
            filename = self.generate_filename(url, municipio, tipo_documento)

        json_path = output_dir / f"{filename}.json"

        # Estructura del JSON
        data = {
            "municipio": municipio,
            "tipo_documento": tipo_documento,
            "titulo": titulo,
            "contenido": contenido,
            "url_origen": metadata.get("url_origen", ""),
            "status": "completed",
            "calidad": metadata,
            "pdf_file": metadata.get("pdf_path", ""),
            "metadata": {
                "fecha_scraping": metadata.get("procesado_at", datetime.now().isoformat()),
                "version_scraper": "2.0",
                "source_type": "transparency_vision"
            }
        }

        # Guardar JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return json_path


def get_pdf_processor() -> PDFProcessor:
    """
    Obtiene una instancia de PDFProcessor.

    Returns:
        PDFProcessor instance
    """
    return PDFProcessor()
