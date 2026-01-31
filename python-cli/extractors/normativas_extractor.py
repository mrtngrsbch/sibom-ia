#!/usr/bin/env python3
"""
normativas_extractor.py

Extrae normativas individuales de los boletines y genera un índice optimizado.
Soporta: decretos, ordenanzas, resoluciones, disposiciones, convenios, licitaciones, etc.

Ejecutar si es que se escrapean mas archivos !

Uso:
    python normativas_extractor.py                    # Procesa todos los boletines
    python normativas_extractor.py --municipality "Carlos Tejedor"  # Solo un municipio
    python normativas_extractor.py --file boletines/Carlos_Tejedor_98.json  # Solo un archivo

@version 1.0.0
@created 2026-01-09
"""

import json
import re
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from collections import Counter


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Tipos de normativas soportados con sus patrones de detección
# NOTA: El orden importa - se buscan en secuencia y se devuelve el PRIMERO que aparece
# en el encabezado del documento (por posición, no por orden del diccionario)
NORMATIVA_PATTERNS = {
    'ordenanza': re.compile(r'Ordenanza\s*N[º°]?\s*(\d+)(?:/(\d{2,4}))?', re.IGNORECASE),
    'decreto': re.compile(r'Decreto\s*N[º°]?\s*(\d+)(?:/(\d{2,4}))?', re.IGNORECASE),
    'resolucion': re.compile(r'Resolución\s*N[º°]?\s*(\d+)(?:/(\d{2,4}))?', re.IGNORECASE),
    'disposicion': re.compile(r'Disposición\s*N[º°]?\s*(\d+)(?:/(\d{2,4}))?', re.IGNORECASE),
    'convenio': re.compile(r'Convenio\s*(?:N[º°]?\s*)?(\d+)?(?:/(\d{2,4}))?', re.IGNORECASE),
    'licitacion': re.compile(r'Licitaci[oó]n\s*(?:P[uú]blica\s*)?N[º°]?\s*(\d+)(?:/(\d{2,4}))?', re.IGNORECASE),
    'comunicacion': re.compile(r'Comunicación\s*N[º°]?\s*(\d+)(?:/(\d{2,4}))?', re.IGNORECASE),
    'acta': re.compile(r'Acta\s*N[º°]?\s*(\d+)', re.IGNORECASE),
}

# Patrón para extraer fecha del documento
DATE_PATTERN = re.compile(r'([A-Za-zÁÉÍÓÚáéíóú\s]+),\s*(\d{2}/\d{2}/\d{4})')

# Texto de ruido a eliminar (headers del sitio SIBOM)
NOISE_PATTERNS = [
    re.compile(r'Sistema de Boletín Oficial Municipal \| Buenos Aires Provincia'),
    re.compile(r'INICIO\s+ACERCA DEL SIBOM\s+BOLETINES\s+MUNICIPIOS\s+ADMINISTRACION'),
    re.compile(r'Sistema de Boletines Oficiales Municipales \(SIBOM\)'),
    re.compile(r'Boletines/[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+'),
]


# ============================================================================
# TIPOS DE DATOS
# ============================================================================

@dataclass
class Normativa:
    """Representa una normativa individual extraída de un boletín."""
    id: str
    municipality: str
    type: str
    number: str
    year: str
    date: str
    title: str
    content: str
    source_bulletin: str
    source_bulletin_url: str
    norma_url: str  # URL individual de la norma (nuevo formato V2)
    doc_index: int
    status: str
    extracted_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# FUNCIONES DE EXTRACCIÓN
# ============================================================================

def clean_content(text: str) -> str:
    """Elimina ruido del contenido (headers del sitio SIBOM)."""
    cleaned = text
    for pattern in NOISE_PATTERNS:
        cleaned = pattern.sub('', cleaned)
    # Eliminar líneas vacías múltiples
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


def normalize_year(year_str: Optional[str], date_str: Optional[str] = None) -> str:
    """
    Normaliza el año a formato de 4 dígitos.
    - "25" → "2025"
    - "2025" → "2025"
    - "233" (error de tipeo) → usa fecha como fallback
    - None → extrae de la fecha si está disponible
    """
    date_year = None
    if date_str:
        date_year = extract_year_from_date(date_str)

    if year_str:
        # Año de 4 dígitos válido
        if len(year_str) == 4 and year_str.isdigit():
            return year_str

        # Año de 2 dígitos (ej: "25" → "2025")
        if len(year_str) == 2 and year_str.isdigit():
            prefix = "20" if int(year_str) <= 50 else "19"
            return prefix + year_str

        # Año de 3 dígitos es un error de tipeo (ej: "233" debería ser "2023")
        # Usar la fecha como fuente confiable
        if len(year_str) == 3 and date_year:
            return date_year

        # Otros casos inválidos: usar fecha
        if date_year:
            return date_year

        return year_str  # Último recurso

    # Sin año en el número, usar fecha
    if date_year:
        return date_year

    return ''


def detect_normativa_type(content: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Detecta el tipo de normativa PRINCIPAL y extrae número/año.

    IMPORTANTE: Solo busca en los primeros 1000 caracteres para evitar
    detectar menciones a otras normativas dentro del contenido.
    Por ejemplo, una ordenanza puede mencionar "Promulgada por decreto N°293"
    pero la normativa principal sigue siendo la ordenanza.

    La detección se hace por POSICIÓN: devuelve la normativa que aparece
    primero en el texto, no la primera del diccionario de patrones.

    Returns:
        Tuple (tipo, número, año) o (None, None, None) si no se detecta
    """
    # Solo buscar en el encabezado del documento (primeros 1000 chars)
    header = content[:1000]

    # Encontrar TODAS las coincidencias y quedarse con la de menor posición
    best_match = None
    best_position = len(header) + 1
    best_tipo = None

    for tipo, pattern in NORMATIVA_PATTERNS.items():
        match = pattern.search(header)
        if match and match.start() < best_position:
            best_position = match.start()
            best_match = match
            best_tipo = tipo

    if best_match and best_tipo:
        numero = best_match.group(1) if best_match.group(1) else ''
        year_raw = best_match.group(2) if len(best_match.groups()) > 1 and best_match.group(2) else None
        return best_tipo, numero, year_raw

    return None, None, None


def extract_date(content: str) -> Optional[str]:
    """Extrae la fecha del documento en formato DD/MM/YYYY."""
    match = DATE_PATTERN.search(content)
    if match:
        return match.group(2)
    return None


def extract_year_from_date(date_str: str) -> str:
    """Extrae el año de una fecha DD/MM/YYYY."""
    if date_str and '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 3:
            return parts[2]
    return ''


def extract_title(content: str, tipo: str, numero: str) -> str:
    """
    Extrae un título descriptivo de la normativa.
    Busca el VISTO o los primeros párrafos significativos.
    """
    # Intentar extraer del VISTO
    visto_match = re.search(
        r'(?:VISTO|Visto)\s*:?\s*(.{20,300}?)(?:CONSIDERANDO|Considerando|;|\n\n)',
        content,
        re.DOTALL
    )
    if visto_match:
        titulo = visto_match.group(1).strip()
        # Limpiar y truncar
        titulo = re.sub(r'\s+', ' ', titulo)[:150]
        return titulo

    # Fallback: usar tipo y número
    return f"{tipo.capitalize()} N° {numero}"


def parse_documents(full_text: str) -> List[Tuple[int, str]]:
    """
    Separa el fullText en documentos individuales usando marcadores [DOC N].

    Returns:
        Lista de tuplas (índice, contenido)
    """
    # Separar por [DOC N]
    parts = re.split(r'\[DOC (\d+)\]', full_text)

    documents = []
    # El split genera: [texto_antes, num1, texto1, num2, texto2, ...]
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            doc_index = int(parts[i])
            doc_content = parts[i + 1].strip()
            if doc_content:  # Solo si hay contenido
                documents.append((doc_index, doc_content))

    return documents


def extract_normativas_from_bulletin(
    bulletin_data: Dict[str, Any],
    municipality: str,
    bulletin_id: str,
    bulletin_url: str
) -> List[Normativa]:
    """
    Extrae todas las normativas de un boletín.

    Soporta dos formatos:
    - V1: fullText con marcadores [DOC N]
    - V2: array 'normas' con normativas pre-extraídas

    Args:
        bulletin_data: Datos del boletín (JSON parseado)
        municipality: Nombre del municipio
        bulletin_id: ID del boletín (ej: "Carlos_Tejedor_98")
        bulletin_url: URL del boletín en SIBOM

    Returns:
        Lista de normativas extraídas
    """
    normativas = []

    # FORMATO V2: Array 'normas' con normativas pre-extraídas (Carlos Tejedor, etc)
    if 'normas' in bulletin_data and isinstance(bulletin_data['normas'], list):
        normas_array = bulletin_data['normas']
        extracted_at = datetime.now().isoformat()

        for idx, norma in enumerate(normas_array):
            # Extraer campos del formato V2
            tipo_raw = norma.get('tipo', '')
            numero_raw = norma.get('numero', '')
            fecha_raw = norma.get('fecha', '')
            titulo = norma.get('titulo', '')
            contenido = norma.get('contenido', '')
            norma_url = norma.get('url', '')

            # Mapear tipo de normativa (normalizar)
            tipo_mapping = {
                'ordenanza': 'ordenanza',
                'decreto': 'decreto',
                'resolucion': 'resolucion',
                'disposicion': 'disposicion',
                'convenio': 'convenio',
                'licitacion': 'licitacion',
            }
            tipo = tipo_mapping.get(tipo_raw.lower(), tipo_raw.lower())

            # Extraer número de formatos como "2526/18" o "2947/2024"
            numero = numero_raw.split('/')[-1] if '/' in numero_raw else numero_raw

            # Extraer año del número o de la fecha
            year = ''
            if '/' in numero_raw:
                parts = numero_raw.split('/')
                if len(parts) >= 2:
                    year_candidate = parts[1]
                    if len(year_candidate) == 2:
                        year = f"20{year_candidate}"
                    elif len(year_candidate) == 4:
                        year = year_candidate

            # Extraer fecha (formato: "Carlos Tejedor, 07/08/2018")
            date = ''
            if fecha_raw:
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', fecha_raw)
                if date_match:
                    date = date_match.group(1)
                    # Si no tenemos año, usar el de la fecha
                    if not year:
                        year = date.split('/')[-1]

            # Limpiar título
            if not titulo or titulo == 'Sin título':
                titulo = f"{tipo.capitalize()} N° {numero}"

            # Limpiar contenido
            cleaned_content = clean_content(contenido)

            # Generar ID único
            normativa_id = f"{municipality.replace(' ', '_')}_{tipo}_{numero}_{year}_{bulletin_id}_norma{idx}"

            # Crear normativa
            normativa = Normativa(
                id=normativa_id,
                municipality=municipality,
                type=tipo,
                number=numero,
                year=year,
                date=date,
                title=titulo[:200],  # Limitar título
                content=cleaned_content,
                source_bulletin=bulletin_id,
                source_bulletin_url=bulletin_url,
                norma_url=norma_url or bulletin_url,
                doc_index=idx + 1,
                status='vigente',
                extracted_at=extracted_at
            )

            normativas.append(normativa)

        if normativas:
            return normativas

    # FORMATO V1: fullText con marcadores [DOC N]
    full_text = bulletin_data.get('fullText', '')

    if not full_text:
        return normativas

    # Parsear documentos individuales
    documents = parse_documents(full_text)

    if not documents:
        # Fallback: si no hay marcadores [DOC N], tratar todo como un documento
        documents = [(1, full_text)]

    extracted_at = datetime.now().isoformat()

    for doc_index, content in documents:
        # Limpiar contenido
        cleaned_content = clean_content(content)

        # Detectar tipo de normativa
        tipo, numero, year_raw = detect_normativa_type(cleaned_content)

        if not tipo:
            # No es una normativa reconocida, saltar
            continue

        # Extraer fecha
        date = extract_date(cleaned_content)

        # Normalizar año (25 → 2025)
        year = normalize_year(year_raw, date)

        # Extraer título
        title = extract_title(cleaned_content, tipo, numero)

        # Generar ID único usando bulletin + doc_index para evitar duplicados
        # Formato: Municipio_tipo_numero_año_bulletin_docN
        normativa_id = f"{municipality.replace(' ', '_')}_{tipo}_{numero}"
        if year:
            normativa_id += f"_{year}"
        normativa_id += f"_{bulletin_id}_doc{doc_index}"

        # Crear normativa
        normativa = Normativa(
            id=normativa_id,
            municipality=municipality,
            type=tipo,
            number=numero,
            year=year,
            date=date or '',
            title=title,
            content=cleaned_content,
            source_bulletin=bulletin_id,
            source_bulletin_url=bulletin_url,
            norma_url=bulletin_url,  # Para V1, usar URL del boletín (no hay URLs individuales)
            doc_index=doc_index,
            status='vigente',  # Por defecto
            extracted_at=extracted_at
        )

        normativas.append(normativa)

    return normativas


# ============================================================================
# FUNCIONES DE PROCESAMIENTO
# ============================================================================

def process_bulletin_file(file_path: Path) -> List[Normativa]:
    """Procesa un archivo de boletín y extrae sus normativas."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extraer información del archivo
        filename = file_path.stem  # "Carlos_Tejedor_98"
        parts = filename.rsplit('_', 1)
        if len(parts) == 2:
            municipality = parts[0].replace('_', ' ')
        else:
            municipality = filename.replace('_', ' ')

        # Para formato V2, la URL viene en 'boletin_url', para V1 en 'link'
        bulletin_url = data.get('boletin_url', '') or data.get('link', '')

        return extract_normativas_from_bulletin(
            bulletin_data=data,
            municipality=municipality,
            bulletin_id=filename,
            bulletin_url=bulletin_url
        )
    except Exception as e:
        print(f"Error procesando {file_path}: {e}", file=sys.stderr)
        return []


def process_all_bulletins(
    boletines_dir: Path,
    municipality_filter: Optional[str] = None,
    progress_callback=None
) -> List[Normativa]:
    """
    Procesa todos los boletines y extrae normativas.

    Args:
        boletines_dir: Directorio con los archivos JSON de boletines
        municipality_filter: Filtrar por municipio (opcional)
        progress_callback: Función de callback para progreso

    Returns:
        Lista de todas las normativas extraídas
    """
    all_normativas = []

    # Listar archivos JSON
    json_files = list(boletines_dir.glob('*.json'))

    # Filtrar por municipio si se especifica
    if municipality_filter:
        filter_pattern = municipality_filter.replace(' ', '_')
        json_files = [f for f in json_files if filter_pattern in f.name]

    total = len(json_files)

    for i, file_path in enumerate(json_files):
        if progress_callback:
            progress_callback(i + 1, total, file_path.name)

        normativas = process_bulletin_file(file_path)
        all_normativas.extend(normativas)

    return all_normativas


def save_index(normativas: List[Normativa], output_path: Path, compact: bool = False):
    """
    Guarda el índice de normativas en formato JSON.

    Args:
        normativas: Lista de normativas (objetos Normativa o dicts)
        output_path: Ruta del archivo de salida
        compact: Si True, omite el campo 'content' para generar un índice más pequeño
    """
    data = []
    for n in normativas:
        # Si es un dataclass Normativa
        if hasattr(n, 'to_dict'):
            entry = n.to_dict()
            if compact:
                # Omitir contenido y tablas_md en modo compacto
                entry.pop('content', None)
                entry.pop('tablas_md', None)
                entry.pop('montos_extraidos', None)
            data.append(entry)
        # Si es un dict (documento de transparencia)
        elif isinstance(n, dict):
            # Expandir campos abreviados para el índice completo
            if not compact:
                # Convertir formato minimalista a completo
                expanded = {
                    'id': n.get('id', ''),
                    'municipality': n.get('m', n.get('municipality', '')),
                    'type': n.get('t', n.get('type', '')),
                    'number': n.get('n', n.get('number', '0')),
                    'year': n.get('y', n.get('year', '')),
                    'date': n.get('d', n.get('date', '')),
                    'title': n.get('ti', n.get('title', '')),
                    'source_bulletin': n.get('sb', n.get('source_bulletin', '')),
                    'norma_url': n.get('url', ''),
                    'status': 'vigente',
                    # Campos vacíos para compatibilidad
                    'content': '',
                    'tablas_md': [],
                    'montos_extraidos': []
                }
                data.append(expanded)
            else:
                # Modo compacto: mantener formato minimalista
                data.append(n)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2 if not compact else None)

    # Calcular tamaño
    size_mb = output_path.stat().st_size / (1024 * 1024)

    print(f"\n✅ Índice guardado: {output_path}")
    print(f"   Total documentos: {len(data)}")
    print(f"   Tamaño: {size_mb:.2f} MB")
    if compact:
        print(f"   Modo: COMPACTO (sin contenido)")


def save_minimal_index(normativas: List[Normativa], output_path: Path):
    """
    Guarda un índice MINIMALISTA para búsqueda rápida en frontend.
    Solo incluye campos esenciales para búsqueda y enlaces.

    Campos: id, m (municipality), t (type), n (number), y (year), d (date), ti (title), sb (source_bulletin), url

    Soporta dos formatos de entrada:
    1. Objetos Normativa (normativas de boletines)
    2. Dicts con formato minimalista (documentos de transparencia desde SQLite)
    """
    data = []
    for n in normativas:
        # Si es un dataclass Normativa
        if hasattr(n, 'municipality'):
            data.append({
                'id': n.id,
                'm': n.municipality,  # Abreviado para reducir tamaño
                't': n.type,
                'n': n.number,
                'y': n.year,
                'd': n.date,
                'ti': n.title[:100] if len(n.title) > 100 else n.title,  # Truncar título
                'sb': n.source_bulletin,
                'url': n.norma_url if hasattr(n, 'norma_url') and n.norma_url else n.source_bulletin_url,
            })
        # Si es un dict con formato minimalista (desde SQLite transparency)
        elif isinstance(n, dict):
            # Ya tiene el formato correcto, solo validar campos
            data.append({
                'id': n.get('id', ''),
                'm': n.get('m', n.get('municipality', '')),
                't': n.get('t', n.get('type', '')),
                'n': n.get('n', n.get('number', '0')),
                'y': n.get('y', n.get('year', '')),
                'd': n.get('d', n.get('date', '')),
                'ti': n.get('ti', n.get('title', ''))[:100],
                'sb': n.get('sb', n.get('source_bulletin', '')),
                'url': n.get('url', ''),
            })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))  # Sin espacios

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Índice MINIMAL guardado: {output_path}")
    print(f"   Total documentos: {len(data)}")
    print(f"   Tamaño: {size_mb:.2f} MB")


def print_statistics(normativas: List[Normativa]):
    """Imprime estadísticas de las normativas extraídas."""
    print("\n" + "=" * 60)
    print("ESTADÍSTICAS DE EXTRACCIÓN")
    print("=" * 60)

    # Por tipo
    type_counts = Counter(n.type for n in normativas)
    print("\nPor tipo de normativa:")
    for tipo, count in type_counts.most_common():
        print(f"  {tipo.upper()}: {count:,}")

    # Por municipio
    muni_counts = Counter(n.municipality for n in normativas)
    print(f"\nMunicipios procesados: {len(muni_counts)}")
    if len(muni_counts) <= 10:
        for muni, count in muni_counts.most_common():
            print(f"  {muni}: {count:,}")

    # Tamaño de contenido
    content_sizes = [len(n.content) for n in normativas]
    if content_sizes:
        avg_size = sum(content_sizes) // len(content_sizes)
        print(f"\nTamaño promedio de contenido: {avg_size:,} chars ({avg_size//1000} KB)")
        print(f"Tamaño total estimado: {sum(content_sizes)//1024//1024} MB")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Extrae normativas individuales de boletines municipales'
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=Path('boletines'),
        help='Directorio de entrada con los JSON de boletines'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('normativas_index.json'),
        help='Archivo de salida para el índice de normativas'
    )
    parser.add_argument(
        '--municipality', '-m',
        type=str,
        help='Filtrar por municipio (ej: "Carlos Tejedor")'
    )
    parser.add_argument(
        '--file', '-f',
        type=Path,
        help='Procesar solo un archivo específico'
    )
    parser.add_argument(
        '--compact', '-c',
        action='store_true',
        help='Generar índice compacto (sin contenido, más pequeño)'
    )
    parser.add_argument(
        '--both', '-b',
        action='store_true',
        help='Generar ambos índices: completo y compacto'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Modo silencioso (sin progreso)'
    )

    args = parser.parse_args()

    # Validar entrada
    if args.file:
        if not args.file.exists():
            print(f"Error: Archivo no encontrado: {args.file}", file=sys.stderr)
            sys.exit(1)

        print(f"Procesando archivo: {args.file}")
        normativas = process_bulletin_file(args.file)
    else:
        if not args.input.exists():
            print(f"Error: Directorio no encontrado: {args.input}", file=sys.stderr)
            sys.exit(1)

        print(f"Procesando boletines en: {args.input}")
        if args.municipality:
            print(f"Filtro de municipio: {args.municipality}")

        def progress(current, total, filename):
            if not args.quiet:
                print(f"\r[{current}/{total}] {filename[:40]}...", end='', flush=True)

        normativas = process_all_bulletins(
            args.input,
            municipality_filter=args.municipality,
            progress_callback=progress if not args.quiet else None
        )

    if not normativas:
        print("\n⚠️ No se encontraron normativas")
        sys.exit(0)

    # Guardar índice(s)
    if args.both:
        # Generar ambos índices
        save_index(normativas, args.output, compact=False)
        compact_path = args.output.with_name(
            args.output.stem + '_compact' + args.output.suffix
        )
        save_index(normativas, compact_path, compact=True)
    else:
        save_index(normativas, args.output, compact=args.compact)

    # Mostrar estadísticas
    print_statistics(normativas)


if __name__ == '__main__':
    main()
