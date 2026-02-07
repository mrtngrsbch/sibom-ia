#!/usr/bin/env python3
"""
scripts/download_pdfs_from_json.py

Descarga los PDFs originales desde los archivos JSON extraídos.

Uso:
    python scripts/download_pdfs_from_json.py <directorio>
    python scripts/download_pdfs_from_json.py boletines/Carlos_Tejedor

El script:
1. Lee todos los JSON del directorio
2. Extrae las URLs de los PDFs (url_origen)
3. Descarga los PDFs
4. Los guarda con nombres legibles en carpeta pdfs/
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import quote

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

console = Console()


def sanitize_filename(name: str) -> str:
    """Limpia un nombre para usarlo como filename."""
    # Reemplazar caracteres inválidos
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, '-')
    # Limpiar espacios múltiples
    name = ' '.join(name.split())
    return name


def extract_pdf_info(json_path: Path) -> Dict:
    """Extrae información del PDF desde un JSON."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        url = data.get('url_origen', '')
        if not url:
            return None

        # Extraer info para el nombre
        periodo = data.get('periodo', '')
        tipo_detalle = data.get('tipo_detalle', '')
        fecha_doc = data.get('fecha_documento', '')

        # Crear nombre legible
        nombre_base = sanitize_filename(tipo_detalle)
        if periodo:
            nombre_base += f"_{periodo}"
        if fecha_doc and fecha_doc != "s/d":
            nombre_base += f"_{fecha_doc.replace('/', '-')}"

        # Hash único por URL (para evitar duplicados)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

        return {
            'url': url,
            'nombre_base': nombre_base,
            'hash': url_hash,
            'json_path': json_path
        }
    except Exception as e:
        console.print(f"[yellow]Error leyendo {json_path.name}: {e}[/yellow]")
        return None


def collect_pdfs(directory: Path) -> List[Dict]:
    """Colecta información de todos los PDFs de los JSON."""
    json_files = list(directory.glob("*.json"))
    console.print(f"[cyan]Encontrados {len(json_files)} archivos JSON[/cyan]")

    pdfs = []
    urls_vistas = set()

    for json_file in json_files:
        info = extract_pdf_info(json_file)
        if info and info['url'] not in urls_vistas:
            pdfs.append(info)
            urls_vistas.add(info['url'])

    console.print(f"[cyan]{len(pdfs)} PDFs únicos para descargar[/cyan]")
    return pdfs


def download_pdf(url: str, dest_path: Path) -> bool:
    """Descarga un PDF desde una URL."""
    try:
        # Codificar URL correctamente para caracteres especiales
        # Separar la URL en esquema+host y path, luego codificar el path
        if '://' in url:
            scheme, rest = url.split('://', 1)
            if '/' in rest:
                host, path = rest.split('/', 1)
                # Codificar solo el path (preservando /)
                encoded_path = '/'.join(quote(part, safe='') for part in path.split('/'))
                url = f"{scheme}://{host}/{encoded_path}"

        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(req, timeout=30)

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dest_path, 'wb') as f:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f.write(chunk)

        return True
    except Exception as e:
        console.print(f"[red]Error descargando {url[:60]}...: {e}[/red]")
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/download_pdfs_from_json.py <directorio>")
        print("Ejemplo: python scripts/download_pdfs_from_json.py boletines/Carlos_Tejedor")
        sys.exit(1)

    source_dir = Path(sys.argv[1])

    if not source_dir.exists():
        console.print(f"[red]Error: El directorio '{source_dir}' no existe[/red]")
        sys.exit(1)

    # Crear carpeta de salida
    output_dir = source_dir / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Colectar info de PDFs
    console.print(f"\n[cyan]Escaneando {source_dir}...[/cyan]\n")
    pdfs = collect_pdfs(source_dir)

    if not pdfs:
        console.print("[yellow]No se encontraron PDFs para descargar[/yellow]")
        return

    # Descargar
    console.print(f"\n[cyan]Descargando {len(pdfs)} PDFs a {output_dir}/[/cyan]\n")

    success_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        console=console
    ) as progress:

        task = progress.add_task("[cyan]Descargando PDFs...", total=len(pdfs))

        for pdf_info in pdfs:
            # Nombre del archivo
            filename = f"{pdf_info['nombre_base']}_{pdf_info['hash']}.pdf"
            dest_path = output_dir / filename

            # Ya existe?
            if dest_path.exists():
                progress.update(task, advance=1)
                continue

            # Descargar
            progress.update(task, description=f"[cyan]{filename[:50]}...[/cyan]")

            if download_pdf(pdf_info['url'], dest_path):
                success_count += 1
            else:
                error_count += 1

            progress.update(task, advance=1, description=f"[cyan]Descargando PDFs...[/cyan]")

    # Resumen
    console.print(f"\n[green]✓ Descarga completada[/green]")
    console.print(f"  Exitosos: {success_count}")
    console.print(f"  Errores: {error_count}")
    console.print(f"  Ubicación: {output_dir}/")


if __name__ == "__main__":
    main()
