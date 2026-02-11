#!/usr/bin/env python3
"""
scripts/cleanup_pdfs.py

Limpia y verifica la consistencia entre PDFs y JSONs.

Acciones:
1. Elimina PDFs que NO tienen JSON correspondiente (huérfanos)
2. Lista JSONs que NO tienen PDF (faltantes)
3. Muestra resumen de estado

Uso:
    python scripts/cleanup_pdfs.py <directorio>
    python scripts/cleanup_pdfs.py boletines/Carlos_Tejedor
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

console = Console()


def cleanup_directory(directory: Path, dry_run: bool = False) -> dict:
    """
    Limpia PDFs huérfanos y verifica consistencia.

    Args:
        directory: Directorio a limpiar
        dry_run: Si True, solo muestra qué se haría sin ejecutar

    Returns:
        Dict con estadísticas
    """
    result = {
        'pdfs_total': 0,
        'pdfs_deleted': 0,
        'pdfs_kept': 0,
        'jsons_total': 0,
        'jsons_missing_pdf': [],
        'pdfs_orphan': []
    }

    # Buscar PDFs y JSONs
    pdfs = list((directory / 'pdfs').glob('*.pdf')) if (directory / 'pdfs').exists() else []
    jsons = list(directory.glob('*_balances_*.json')) + list(directory.glob('*_presupuestos_*.json'))

    result['pdfs_total'] = len(pdfs)
    result['jsons_total'] = len(jsons)

    # Extraer hashes/base de JSONs para comparar
    # Formato: Nombre_Tipo_YYYYMMDD_HHMMSS_<hash>.json
    json_hashes = set()
    for json_file in jsons:
        # El hash está antes del .json (12 caracteres hex)
        stem = json_file.stem
        if '_' in stem:
            parts = stem.split('_')
            if parts:
                json_hashes.add(parts[-1])  # Última parte es el hash

    # Verificar PDFs
    for pdf in pdfs:
        # El PDF podría tener el hash en el nombre o necesitamos buscar en JSONs
        pdf_kept = False

        # Buscar si algún JSON referencia este PDF (por nombre de archivo)
        pdf_name = pdf.name

        for json_file in jsons:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    # Verificar por nombre de archivo en cualquier campo PDF
                    for field in ['pdf_file', 'pdf_path']:
                        pdf_path = data.get(field, '') or data.get('calidad', {}).get('pdf_path', '')
                        if pdf_name in pdf_path:
                            pdf_kept = True
                            break
                    if pdf_kept:
                        break
            except:
                pass

        if pdf_kept:
            result['pdfs_kept'] += 1
        else:
            result['pdfs_orphan'].append(pdf.name)
            if not dry_run:
                pdf.unlink()
                result['pdfs_deleted'] += 1
            else:
                result['pdfs_deleted'] += 1  # Solo contador

    # Verificar JSONs sin PDF
    for json_file in jsons:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                pdf_path = data.get('pdf_file', '') or data.get('calidad', {}).get('pdf_path', '')
                if pdf_path:
                    pdf_file = Path(pdf_path)
                    if not pdf_file.exists():
                        result['jsons_missing_pdf'].append(json_file.name)
                else:
                    result['jsons_missing_pdf'].append(json_file.name)
        except:
            pass

    return result


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/cleanup_pdfs.py <directorio>")
        print("       python scripts/cleanup_pdfs.py <directorio> --dry-run")
        sys.exit(1)

    directory = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv

    if not directory.is_dir():
        print(f"Error: '{directory}' no es un directorio válido")
        sys.exit(1)

    console.print(f"[cyan]Limpiando: {directory}[/cyan]")
    if dry_run:
        console.print("[yellow]MODO DRY-RUN - No se eliminarán archivos[/yellow]")

    result = cleanup_directory(directory, dry_run=dry_run)

    # Mostrar resultados
    console.print("\n[bold]Resumen[/bold]")
    console.print(f"  PDFs totales:     {result['pdfs_total']}")
    console.print(f"  PDFs eliminados:  [red]{result['pdfs_deleted']}[/red]")
    console.print(f"  PDFs conservados: [green]{result['pdfs_kept']}[/green]")
    console.print(f"  JSONs totales:    {result['jsons_total']}")

    if result['pdfs_orphan']:
        console.print(f"\n[yellow]PDFs huérfanos eliminados:[/yellow]")
        for name in result['pdfs_orphan']:
            console.print(f"  - {name}")

    if result['jsons_missing_pdf']:
        console.print(f"\n[red]JSONs sin PDF:[/red]")
        for name in result['jsons_missing_pdf']:
            console.print(f"  - {name}")

    console.print(f"\n[green]✅ Limpieza completada[/green]")


if __name__ == '__main__':
    main()
