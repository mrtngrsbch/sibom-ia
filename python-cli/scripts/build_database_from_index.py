#!/usr/bin/env python3
"""
build_database_from_index.py

Construye una base de datos SQLite desde el índice comprimido de normativas.
Este script usa el archivo normativas_index_minimal.json.gz que contiene 216K+ normativas.

Uso:
    python3 scripts/build_database_from_index.py

Output:
    python-cli/normativas.db - Base de datos SQLite
"""

import json
import sqlite3
import gzip
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from datetime import datetime

console = Console()

# Schema de la base de datos
SCHEMA = """
CREATE TABLE IF NOT EXISTS normativas (
    id TEXT PRIMARY KEY,
    municipality TEXT NOT NULL,
    type TEXT NOT NULL,
    number TEXT NOT NULL,
    year INTEGER NOT NULL,
    date TEXT NOT NULL,
    title TEXT NOT NULL,
    source_bulletin TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT DEFAULT 'vigente'
);

CREATE INDEX IF NOT EXISTS idx_municipality ON normativas(municipality);
CREATE INDEX IF NOT EXISTS idx_type ON normativas(type);
CREATE INDEX IF NOT EXISTS idx_year ON normativas(year);
CREATE INDEX IF NOT EXISTS idx_date ON normativas(date);
CREATE INDEX IF NOT EXISTS idx_municipality_type_year ON normativas(municipality, type, year);

-- Vista para agregaciones rápidas
CREATE VIEW IF NOT EXISTS stats_by_municipality AS
SELECT
    municipality,
    COUNT(*) as total,
    SUM(CASE WHEN type = 'decreto' THEN 1 ELSE 0 END) as decretos,
    SUM(CASE WHEN type = 'ordenanza' THEN 1 ELSE 0 END) as ordenanzas,
    SUM(CASE WHEN type = 'resolucion' THEN 1 ELSE 0 END) as resoluciones,
    MIN(year) as year_min,
    MAX(year) as year_max
FROM normativas
GROUP BY municipality;
"""

def parse_date(date_str: str) -> tuple[str, int]:
    """
    Parsea fecha en formato DD/MM/YYYY o "Municipio, DD/MM/YYYY"
    Retorna (fecha_iso, año)
    """
    if not date_str:
        return '1900-01-01', 1900

    # Limpiar formato "Carlos Tejedor, 31/12/2024"
    if ',' in date_str:
        date_str = date_str.split(',')[1].strip()

    # Limpiar formato que tenga texto adicional
    for char in ['(', ')', '[', ']']:
        date_str = date_str.split(char)[0].strip()

    try:
        # Intentar varios formatos
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d'), dt.year
            except:
                continue
        return '1900-01-01', 1900
    except:
        return '1900-01-01', 1900

def normalize_type(tipo: str) -> str:
    """Normaliza tipos de normativa"""
    tipo_lower = tipo.lower().strip()
    type_map = {
        'ordenanza': 'ordenanza',
        'decreto': 'decreto',
        'resolución': 'resolucion',
        'resolucion': 'resolucion',
        'disposición': 'disposicion',
        'disposicion': 'disposicion',
        'convenio': 'convenio',
        'licitación': 'licitacion',
        'licitacion': 'licitacion'
    }
    return type_map.get(tipo_lower, tipo_lower)

def extract_municipality_id(norm_id: str) -> str:
    """
    Extrae el municipio desde el ID de la normativa
    Formato esperado: "municipio_tipo_numero_año"
    """
    parts = norm_id.split('_')
    if parts:
        return parts[0]
    return 'Unknown'

def build_database():
    """
    Construye la base de datos desde el índice comprimido
    """
    # Buscar el índice comprimido
    project_root = Path(__file__).parent.parent
    index_path = project_root / 'data' / 'indices' / 'normativas_index_minimal.json.gz'

    if not index_path.exists():
        console.print(f"[red]❌ No se encontró el índice en: {index_path}[/red]")
        return

    db_path = project_root / 'python-cli' / 'normativas.db'

    # Eliminar DB existente
    if db_path.exists():
        db_path.unlink()
        console.print(f"[yellow]🗑️  Base de datos existente eliminada[/yellow]")

    # Crear nueva DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear schema
    cursor.executescript(SCHEMA)
    conn.commit()
    console.print(f"[green]✅ Schema creado[/green]")

    # Cargar índice comprimido
    console.print(f"[blue]📂 Cargando índice desde: {index_path}[/blue]")

    with gzip.open(index_path, 'rt', encoding='utf-8') as f:
        index_data = json.load(f)

    total_normas = len(index_data)
    console.print(f"[blue]📊 Total normativas en índice: {total_normas:,}[/blue]")

    # Procesar normas
    inserted = 0
    skipped = 0

    with Progress() as progress:
        task = progress.add_task("Procesando normativas...", total=total_normas)

        batch_size = 1000
        batch = []

        for norm_id, norm_data in index_data.items():
            # Extraer campos
            tipo = norm_data.get('tipo', 'desconocido')
            tipo_norm = normalize_type(tipo)
            numero = norm_data.get('numero', 'S/N')
            fecha = norm_data.get('fecha', '')
            date_iso, year = parse_date(fecha)
            titulo = norm_data.get('titulo', '')[:500]  # Limitar a 500 chars

            # ID único
            doc_id = norm_id.replace('/', '_').replace(' ', '_')

            # Determinar municipio
            municipio = norm_data.get('municipio', extract_municipality_id(norm_id))

            # URL y fuente
            url = norm_data.get('url', '')
            fuente = norm_data.get('fuente', norm_id.split('_')[0] if '_' in norm_id else 'Unknown')

            batch.append((
                doc_id, municipio, tipo_norm, numero, year, date_iso,
                titulo, fuente, url, 'vigente'
            ))

            # Insertar en lote
            if len(batch) >= batch_size:
                try:
                    cursor.executemany("""
                        INSERT OR REPLACE INTO normativas
                        (id, municipality, type, number, year, date, title, source_bulletin, url, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    conn.commit()
                    inserted += len(batch)
                    batch = []
                except Exception as e:
                    console.print(f"[red]❌ Error en lote: {e}[/red]")
                    skipped += len(batch)
                    batch = []

            progress.update(task, advance=1)

        # Insertar remaining
        if batch:
            try:
                cursor.executemany("""
                    INSERT OR REPLACE INTO normativas
                    (id, municipality, type, number, year, date, title, source_bulletin, url, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                conn.commit()
                inserted += len(batch)
            except Exception as e:
                console.print(f"[red]❌ Error en lote final: {e}[/red]")
                skipped += len(batch)

    # Estadísticas
    cursor.execute("SELECT COUNT(*) FROM normativas")
    total_db = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT municipality) FROM normativas")
    total_municipalities = cursor.fetchone()[0]

    console.print(f"\n[green]✅ Base de datos creada exitosamente[/green]")
    console.print(f"[blue]📊 Estadísticas:[/blue]")
    console.print(f"   • Total normativas: {total_db:,}")
    console.print(f"   • Municipios: {total_municipalities}")
    console.print(f"   • Procesadas: {inserted:,}")
    console.print(f"   • Omitidas: {skipped:,}")
    console.print(f"   • Tamaño DB: {db_path.stat().st_size / (1024*1024):.1f} MB")

    # Mostrar stats por municipio (top 10)
    cursor.execute("SELECT * FROM stats_by_municipality ORDER BY total DESC LIMIT 10")
    stats = cursor.fetchall()

    console.print(f"\n[blue]📈 Top 10 municipios:[/blue]")
    for row in stats:
        municipality, total, decretos, ordenanzas, resoluciones, year_min, year_max = row
        console.print(f"   • {municipality}: {total:,} normativas ({decretos:,} decretos, {ordenanzas:,} ordenanzas)")

    conn.close()
    console.print(f"\n[green]💾 Base de datos guardada en: {db_path}[/green]")

if __name__ == '__main__':
    console.print("[bold blue]🔨 Construyendo base de datos SQLite desde índice...[/bold blue]\n")
    build_database()
