#!/usr/bin/env python3
"""
services/

Servicios de alto nivel para el scraper.

PDFProcessor: Procesamiento de PDFs con Vision API
ScraperService: Orquestación del scraping completo
"""

from .pdf_processor import PDFProcessor
from .scraper_service import ScraperService

__all__ = ["PDFProcessor", "ScraperService"]
