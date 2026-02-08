#!/usr/bin/env python3
"""
build_database_from_index.py

Construye una base de datos SQLite desde el índice comprimido de normativas.
El índice es una lista con 216K+ normativas con campos abreviados.

Uso:
    python3 scripts/build_database_from_index.py

Output:
    normativas.db - Base de datos SQLite
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
    """Parsea fecha en formato DD/MM/YYYY"""
    if not date_str:
        return '1900-01-01', 1900

    # Limpiar formato que tenga texto adicional
    for char in ['(', ')', '[', ']']:
        date_str = date_str.split(char)[0].strip()

    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d'), dt.year
    except:
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d'), dt.year
        except:
            return '1900-01-01', 1900

def normalize_type(tipo: str) -> str:
    """Normaliza tipos de normativa"""
    if not tipo:
        return 'desconocido'

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

def build_database():
    """Construye la base de datos desde el índice comprimido"""
    # Buscar el índice comprimido
    index_path = Path('data/indices/normativas_index_minimal.json.gz')

    if not index_path.exists():
        # Alternativa: buscar en dist/
        index_path = Path('dist/normativas_index_minimal.json.gz')

    if not index_path.exists():
        console.print("[red]❌ No se encontró el índice[/red]")
        console.print("[yellow]   Buscando en:[/yellow]")
        console.print("     • data/indices/normativas_index_minimal.json.gz")
        console.print("     • dist/normativas_index_minimal.json.gz")
        return

    db_path = Path('normativas.db')

    # Eliminar DB existente y temporales
    if db_path.exists():
        db_path.unlink()
        console.print("[yellow]🗑️  Base de datos existente eliminada[/yellow]")

    # Eliminar archivos temporales
    for ext in ['-shm', '-wal']:
        temp_file = Path(f'normativas.db{ext}')
        if temp_file.exists():
            temp_file.unlink()

    # Crear nueva DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear schema
    cursor.executescript(SCHEMA)
    conn.commit()
    console.print("[green]✅ Schema creado[/green]")

    # Cargar índice comprimido
    console.print(f"[blue]📂 Cargando índice desde: {index_path}[/blue]")

    with gzip.open(index_path, 'rt', encoding='utf-8') as f:
        index_data = json.load(f)

    if not isinstance(index_data, list):
        console.print(f"[red]❌ El índice no es una lista[/red]")
        return

    total_normas = len(index_data)
    console.print(f"[blue]📊 Total normativas en índice: {total_normas:,}[/blue]")

    # Procesar normas
    inserted = 0
    skipped = 0

    with Progress() as progress:
        task = progress.add_task("Procesando normativas...", total=total_normas)

        batch_size = 1000
        batch = []

        for item in index_data:
            # Campos del índice (formato minimal)
            # m=municipio, t=tipo, n=numero, y=año, d=fecha, ti=titulo, sb=source bulletin, url=url
            norm_id = item.get('id', '')
            municipio = item.get('m', 'Unknown')
            tipo = item.get('t', 'desconocido')
            numero = item.get('n', 'S/N')
            year_str = item.get('y', '1900')
            fecha = item.get('d', '')
            titulo = item.get('ti', '')[:500]  # Limitar a 500 chars
            fuente = item.get('sb', norm_id.split('_')[0] if '_' in norm_id else municipio)
            url = item.get('url', '')

            # Convertir año a entero
            try:
                year = int(year_str)
            except:
                year = 1900

            # Normalizar tipo
            tipo_norm = normalize_type(tipo)

            # Parsear fecha
            date_iso, _ = parse_date(fecha)

            # Normalizar ID
            doc_id = norm_id.replace('/', '_').replace(' ', '_')

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
