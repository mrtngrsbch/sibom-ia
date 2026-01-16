#!/usr/bin/env python3
"""
build_database.py

Construye una base de datos SQLite optimizada desde los archivos JSON de boletines.
Esta DB se usa en el chatbot para queries rápidas sin necesidad de LLM.

Uso:
    python3 build_database.py

Output:
    boletines/normativas.db - Base de datos SQLite
"""

import json
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress

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
    # Limpiar formato "Carlos Tejedor, 31/12/2024"
    if ',' in date_str:
        date_str = date_str.split(',')[1].strip()
    
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d'), dt.year
    except:
        console.print(f"[yellow]⚠️  Fecha inválida: {date_str}[/yellow]")
        return '1900-01-01', 1900

def extract_normativas_from_bulletin(bulletin_data: dict, filename: str) -> list[dict]:
    """
    Extrae todas las normativas de un boletín
    """
    normativas = []
    municipality = bulletin_data.get('municipio', 'Unknown')
    bulletin_url = bulletin_data.get('boletin_url', '')
    
    # Procesar cada norma en el boletín
    for doc in bulletin_data.get('normas', []):
        doc_type = doc.get('tipo', '').lower()
        
        # Normalizar tipos
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
        
        normalized_type = type_map.get(doc_type, doc_type)
        
        # Extraer número y año
        number = doc.get('numero', 'S/N')
        date_str = doc.get('fecha', '')
        date_iso, year = parse_date(date_str)
        
        # Título (truncado a 200 chars)
        title = doc.get('titulo', '')[:200]
        
        # ID único
        doc_id = f"{municipality}_{normalized_type}_{number}_{year}".replace('/', '_').replace(' ', '_')
        
        normativas.append({
            'id': doc_id,
            'municipality': municipality,
            'type': normalized_type,
            'number': number,
            'year': year,
            'date': date_iso,
            'title': title,
            'source_bulletin': filename,
            'url': bulletin_url,
            'status': 'vigente'  # Por defecto vigente
        })
    
    return normativas

def build_database():
    """
    Construye la base de datos desde los archivos JSON
    """
    boletines_dir = Path(__file__).parent / 'boletines'
    db_path = boletines_dir / 'normativas.db'
    
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
    
    # Procesar archivos JSON
    json_files = list(boletines_dir.glob('*.json'))
    # Filtrar archivos de progreso y test
    json_files = [f for f in json_files if not f.name.startswith('.progress') and not f.name.startswith('Test_')]
    
    console.print(f"[blue]📂 Encontrados {len(json_files)} archivos JSON[/blue]")
    
    total_normativas = 0
    
    with Progress() as progress:
        task = progress.add_task("Procesando boletines...", total=len(json_files))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    bulletin_data = json.load(f)
                
                normativas = extract_normativas_from_bulletin(bulletin_data, json_file.name)
                
                # Insertar en DB
                for norm in normativas:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO normativas 
                            (id, municipality, type, number, year, date, title, source_bulletin, url, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            norm['id'],
                            norm['municipality'],
                            norm['type'],
                            norm['number'],
                            norm['year'],
                            norm['date'],
                            norm['title'],
                            norm['source_bulletin'],
                            norm['url'],
                            norm['status']
                        ))
                    except sqlite3.IntegrityError:
                        # Duplicado, ignorar
                        pass
                
                total_normativas += len(normativas)
                conn.commit()
                
            except Exception as e:
                console.print(f"[red]❌ Error procesando {json_file.name}: {e}[/red]")
            
            progress.update(task, advance=1)
    
    # Estadísticas
    cursor.execute("SELECT COUNT(*) FROM normativas")
    total_db = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT municipality) FROM normativas")
    total_municipalities = cursor.fetchone()[0]
    
    console.print(f"\n[green]✅ Base de datos creada exitosamente[/green]")
    console.print(f"[blue]📊 Estadísticas:[/blue]")
    console.print(f"   • Total normativas: {total_db}")
    console.print(f"   • Municipios: {total_municipalities}")
    console.print(f"   • Tamaño DB: {db_path.stat().st_size / 1024:.1f} KB")
    
    # Mostrar stats por municipio
    cursor.execute("SELECT * FROM stats_by_municipality")
    stats = cursor.fetchall()
    
    console.print(f"\n[blue]📈 Por municipio:[/blue]")
    for row in stats:
        municipality, total, decretos, ordenanzas, resoluciones, year_min, year_max = row
        console.print(f"   • {municipality}: {total} normativas ({decretos} decretos, {ordenanzas} ordenanzas)")
        console.print(f"     Años: {year_min}-{year_max}")
    
    conn.close()
    console.print(f"\n[green]💾 Base de datos guardada en: {db_path}[/green]")

if __name__ == '__main__':
    console.print("[bold blue]🔨 Construyendo base de datos SQLite...[/bold blue]\n")
    build_database()
