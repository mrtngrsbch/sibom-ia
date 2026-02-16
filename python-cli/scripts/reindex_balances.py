#!/usr/bin/env python3
"""
reindex_balances.py

Reindexar todos los balances con títulos mejorados.

Este script:
1. Lee los JSONs de balances existentes de Carlos Tejedor
2. Extrae títulos mejorados desde la cabecera y período
3. Actualiza SQLite con los títulos nuevos
4. Reconstruye los índices (normativas_index_minimal.json)

Uso:
    python scripts/reindex_balances.py
    python scripts/reindex_balances.py --rebuild-all  # Reconstruir índices completamente
"""

from rich.progress import Progress
from rich.console import Console
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


console = Console()


def extract_titulo_from_balance_json(json_file: Path) -> str:
    """
    Extrae un título descriptivo desde un JSON de balance.

    Prioridad:
    1. Construir desde cabecera.tipo_documento + periodo
    2. Fallback a titulo_extraido existente
    3. Fallback a nombre del archivo
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        console.print(f"[red]Error leyendo {json_file.name}: {e}[/red]")
        return None

    # Opción 1: Construir desde metadatos
    tipo_detalle = data.get("tipo_detalle") or data.get(
        "cabecera", {}).get("tipo_documento", "Balance")
    periodo = data.get("periodo", "s/d")

    if periodo and periodo != "s/d":
        # Si tiene período como "2025-T3", convertir a "Trimestre 3, 2025"
        if 'T' in str(periodo):
            parts = str(periodo).split('-')
            if len(parts) == 2:
                year = parts[0]
                trim_num = parts[1].replace('T', '').replace('S', '')
                if 'S' in parts[1]:
                    trim_label = f"Semestre {trim_num}"
                else:
                    trim_label = f"Trimestre {trim_num}"
                return f"{tipo_detalle} - {trim_label}, {year}"
        # Solo año
        return f"{tipo_detalle} - {periodo}"

    # Fallback a titulo_extraido
    if data.get("titulo_extraido") and data.get("titulo_extraido") != "**CABECERA DEL DOCUMENTO**":
        return data.get("titulo_extraido", "Balance sin título")

    # Último fallback: nombre del archivo
    return f"{tipo_detalle} ({json_file.stem})"


def reindex_balances_in_sqlite():
    """
    Lee todos los JSONs de balances, actualiza títulos y reconstruye índices.
    """
    boletines_dir = Path("boletines/Carlos_Tejedor")

    if not boletines_dir.exists():
        console.print(f"[red]No existe directorio: {boletines_dir}[/red]")
        return False

    # Encontrar todos los JSONs de balances
    balance_files = list(boletines_dir.glob("*Balances*.json"))

    if not balance_files:
        console.print(
            "[yellow]No hay archivos de balances encontrados[/yellow]")
        return False

    console.print(
        f"[cyan]Encontrados {len(balance_files)} archivos de balances[/cyan]\n")

    try:
        from utils.sqlite_manager import get_sqlite_manager
    except ImportError:
        console.print("[red]Error: No se puede importar sqlite_manager[/red]")
        return False

    mgr = get_sqlite_manager()
    updated_count = 0
    json_updated = 0

    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Procesando...", total=len(balance_files))

        for json_file in balance_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Generar título mejorado
                titulo_nuevo = extract_titulo_from_balance_json(json_file)

                if not titulo_nuevo:
                    progress.update(task, advance=1)
                    continue

                # 1. Actualizar archivo JSON con título mejorado
                if data.get("titulo_extraido") != titulo_nuevo:
                    data["titulo_extraido"] = titulo_nuevo
                    # Guardar JSON actualizado
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    json_updated += 1

                # 2. Extraer información para SQLite
                municipio = data.get("municipio", "Carlos Tejedor")
                tipo_doc = data.get("tipo_documento", "balances")
                periodo = data.get("periodo", "s/d")
                fecha_doc = data.get("fecha_documento", "s/d")
                url_origen = data.get("url_origen", "")
                json_file_name = json_file.name

                # Generar ID único
                doc_id = f"TRANS_{municipio.replace(' ', '_')}_{tipo_doc}_{json_file.stem}"

                # Insertar o actualizar en SQLite
                doc_entry = {
                    "id": doc_id,
                    "municipio": municipio,
                    "tipo_documento": tipo_doc,
                    "periodo": periodo,
                    "fecha_documento": fecha_doc,
                    "url_origen": url_origen,
                    "titulo_extraido": titulo_nuevo,  # ✅ Título mejorado
                    "json_file": json_file_name,
                    "status": "completed",
                    "tablas_md": data.get("tablas_md", []),
                    "calidad": data.get("calidad", {}),
                    "validation_status": "checked",
                }

                mgr.insert_transparency_doc(doc_entry)
                updated_count += 1

            except Exception as e:
                console.print(
                    f"[yellow]Error procesando {json_file.name}: {e}[/yellow]")

            progress.update(task, advance=1)

    console.print(f"\n[green]✅ {json_updated} JSONs actualizados[/green]")
    console.print(
        f"[green]✅ {updated_count} balances actualizados en SQLite[/green]")
    return True


def rebuild_indexes():
    """
    Reconstruye los índices después de actualizar SQLite.
    """
    console.print("\n[cyan]Reconstruyendo índices...[/cyan]")

    try:
        # Importar y ejecutar reconstrucción
        from cli import rebuild_indexes_cmd
        # O manualmente:
        from extractors.normativas_extractor import save_minimal_index
        from utils.sqlite_manager import get_sqlite_manager

        mgr = get_sqlite_manager()

        # Obtener todos los documentos para indexar
        all_trans = mgr.get_all_transparency_for_index()

        if all_trans:
            console.print(
                f"[cyan]Indexando {len(all_trans)} documentos de transparencia...[/cyan]")

            # Guardar índice minimal
            output_path = Path("data/indexes/normativas_index_minimal.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_trans, f, ensure_ascii=False,
                          separators=(',', ':'))

            size_mb = output_path.stat().st_size / (1024 * 1024)
            console.print(
                f"[green]✅ Índice reconstruido: {output_path}[/green]")
            console.print(f"   Documentos: {len(all_trans)}")
            console.print(f"   Tamaño: {size_mb:.2f} MB")

            return True

    except Exception as e:
        console.print(f"[red]Error reconstruyendo índices: {e}[/red]")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Reindexar balances con títulos mejorados"
    )
    parser.add_argument(
        "--rebuild-all",
        action="store_true",
        help="Reconstruir índices completamente"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué se haría sin hacer cambios"
    )

    args = parser.parse_args()

    console.print("[bold cyan]=== Reindexar Balances ===[/bold cyan]\n")

    if args.dry_run:
        console.print(
            "[yellow]Modo dry-run: Mostrando títulos generados[/yellow]\n")
        boletines_dir = Path("boletines/Carlos_Tejedor")
        for json_file in sorted(boletines_dir.glob("*Balances*.json"))[:5]:
            titulo = extract_titulo_from_balance_json(json_file)
            console.print(f"[dim]{json_file.name}[/dim]")
            console.print(f"  → {titulo}\n")
        return

    # Actualizar SQLite con títulos mejorados
    if reindex_balances_in_sqlite():
        if args.rebuild_all:
            rebuild_indexes()

        console.print("\n[bold green]✅ Reindexación completada[/bold green]")
        console.print(
            "[cyan]Próximo paso: Ejecutar 'python cli.py rebuild-index' para reconstruir índices[/cyan]")
    else:
        console.print("[red]Reindexación fallida[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
