#!/usr/bin/env python3
"""
core/data_models.py

Dataclasses compartidas entre todos los scrapers.
Define los modelos de datos estándar para SIBOM, Web y Transparency.

@version 3.0.0
@created 2026-01-29
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


# Re-exportar Normativa desde normativas_extractor para compatibilidad
# Esto permite que otros módulos usen from core.data_models import Normativa
# mientras mantiene el código en normativas_extractor.py
try:
    from extractors.normativas_extractor import Normativa as _NormativaBase
    # Crear un wrapper que agregue tablas_md
    @dataclass
    class Normativa(_NormativaBase):
        tablas_md: List[str] = field(default_factory=list)
        montos_extraidos: List[Dict] = field(default_factory=list)
except ImportError:
    # Si no existe aún (circular import), definir aquí
    @dataclass
    class Normativa:
        """
        Normativa individual estándar para SIBOM y Web.

        Atributos:
            id: ID único de la normativa
            municipality: Nombre del municipio
            type: Tipo (ordenanza, decreto, resolucion, etc.)
            number: Número de la normativa
            year: Año
            date: Fecha completa
            title: Título descriptivo
            content: Contenido completo
            source_bulletin: Boletín de origen
            source_bulletin_url: URL del boletín
            norma_url: URL individual de la norma
            doc_index: Índice en el boletín
            status: Estado (vigente, derogado, etc.)
            extracted_at: Timestamp de extracción
            tablas_md: Tablas en formato Markdown (para LLMs)
            montos_extraidos: Montos detectados
        """
        id: str
        municipality: str
        type: str  # ordenanza, decreto, resolucion, disposicion, convenio, licitacion, etc.
        number: str
        year: str
        date: str
        title: str
        content: str
        source_bulletin: str
        source_bulletin_url: str = ""
        norma_url: str = ""
        doc_index: int = 0
        status: str = "vigente"
        extracted_at: str = ""
        tablas_md: List[str] = field(default_factory=list)
        montos_extraidos: List[Dict] = field(default_factory=list)

        def to_dict(self) -> Dict[str, Any]:
            """Convierte el dataclass a diccionario."""
            return asdict(self)

        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> 'Normativa':
            """Crea una instancia desde un diccionario."""
            return cls(**data)


@dataclass
class TransparencyDocument:
    """
    Documento de transparencia municipal.

    Para Balances, Presupuestos, Licitaciones, Concursos, etc.
    que NO son normativas legales sino documentos administrativos.
    """
    municipio: str
    tipo_documento: str  # balance_sumas_saldos, presupuesto, licitacion, etc.
    tipo_detalle: str = ""  # NUEVO: tipo específico (ej: "BALANCE DE SUMAS Y SALDOS")
    periodo: str  # 2025-Q2, 2025, etc.
    fecha_documento: str
    contenido: str = ""  # CRÍTICO: texto completo extraído del PDF
    cabecera: Dict[str, Any] = field(default_factory=dict)  # NUEVO: datos de cabecera completa
    url_origen: str
    tablas_md: List[str]  # Tablas en Markdown
    calidad: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el dataclass a diccionario."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransparencyDocument':
        """Crea una instancia desde un diccionario."""
        return cls(**data)


@dataclass
class BoletinMetadata:
    """
    Metadata de un boletín procesado.
    """
    municipio: str
    numero_boletin: str
    fecha_boletin: str
    boletin_url: str
    status: str = "completed"
    total_normas: int = 0
    total_caracteres: int = 0
    total_tablas: int = 0
    total_montos: int = 0
    fecha_scraping: str = ""
    version_scraper: str = "3.0"
    source_type: str = "sibom"  # sibom, web, transparency

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el dataclass a diccionario."""
        return asdict(self)


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def detect_normativa_type(text: str) -> tuple[str, str, str]:
    """
    Detecta el tipo, número y año de una normativa desde el texto.

    Returns:
        (tipo, numero, year) - Tipo detectado, número, año raw
    """
    import re

    # Patrones en orden de prioridad
    patterns = [
        (r'ORDENANZA\s+N?[º°]?\s*(\d+)(?:/(\d{2,4}))?', 'ordenanza'),
        (r'DECRETO\s+N?[º°]?\s*(\d+)(?:/(\d{2,4}))?', 'decreto'),
        (r'RESOLUCI[ÓO]N\s+N?[º°]?\s*(\d+)(?:/(\d{2,4}))?', 'resolucion'),
        (r'DISPOSICI[ÓO]N\s+N?[º°]?\s*(\d+)(?:/(\d{2,4}))?', 'disposicion'),
        (r'CONVENIO\s+(?:N?[º°]?\s*)?(\d+)?(?:/(\d{2,4}))?', 'convenio'),
        (r'LICITACI[ÓO]N\s+(?:P[ÚU]BLICA\s*)?N?[º°]?\s*(\d+)(?:/(\d{2,4}))?', 'licitacion'),
    ]

    for pattern, tipo in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            numero = match.group(1) if match.group(1) else "0"
            year_raw = match.group(2) if match.lastindex and match.lastindex >= 2 and match.group(2) else ""
            return tipo, numero, year_raw

    return "normativa", "0", ""


def normalize_year(year_raw: str, date_str: str = "") -> str:
    """
    Normaliza un año a formato completo (YYYY).

    Args:
        year_raw: Año extraído (puede ser 25, 2025, etc.)
        date_str: Fecha completa para fallback

    Returns:
        Año en formato YYYY (ej: 2025)
    """
    import re

    if not year_raw and not date_str:
        return "2024"

    # Si year_raw es 2 dígitos
    if year_raw and len(year_raw) == 2:
        return f"20{year_raw}"

    # Si year_raw es 4 dígitos
    if year_raw and len(year_raw) == 4:
        return year_raw

    # Extraer desde date_str
    if date_str:
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            return year_match.group(1)

    return "2024"


def extract_title(content: str, tipo: str, numero: str) -> str:
    """
    Extrae un título desde el contenido.
    """
    import re

    # Buscar primera línea significativa
    lines = content.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if len(line) > 10 and len(line) < 200:
            # Limpiar ruido
            if not line.startswith('Sistema') and not line.startswith('INICIO'):
                return line[:200]

    # Fallback
    return f"{tipo.upper()} {numero}"


def generate_normativa_id(municipio: str, tipo: str, numero: str, year: str) -> str:
    """
    Genera un ID único para una normativa.

    Formato: {municipio}_{tipo}_{numero}_{year}_{uuid_short}
    """
    import uuid
    slug = municipio.replace(' ', '_').replace('-', '_')
    unique = uuid.uuid4().hex[:8]
    return f"{slug}_{tipo}_{numero}_{year}_{unique}"
