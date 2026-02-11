import os
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Add parent directory to sys.path (if needed for future imports)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

console = Console()

def generate_summary():
    boletines_path = Path("boletines")
    if not boletines_path.exists():
        console.print("[red]Error: La carpeta 'boletines' no existe.[/red]")
        return

    table = Table(title="Resumen de Calidad de Datos (Transparencia)")
    table.add_column("Municipio", style="cyan")
    table.add_column("Archivo JSON", style="white")
    table.add_column("Estado", justify="center")
    table.add_column("Tablas", justify="right")
    table.add_column("Error Principal", style="dim red")

    files = list(boletines_path.rglob("*.json"))
    
    # Contadores
    stats = {"valid": 0, "failed": 0, "unchecked": 0, "error": 0}

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Solo procesar documentos de transparencia (tienen validation_status)
            if "validation_status" not in data:
                continue

            municipio = data.get("municipio", "n/a")
            status = data.get("validation_status", "unchecked")
            tablas_count = len(data.get("tablas_md", []))
            
            # Iconos de estado
            status_display = ""
            if status == "valid":
                status_display = "[green]✅ Valid[/green]"
                stats["valid"] += 1
            elif status == "failed":
                status_display = "[bold red]❌ Failed[/bold red]"
                stats["failed"] += 1
            elif status == "error":
                status_display = "[yellow]⚠ Error[/yellow]"
                stats["error"] += 1
            else:
                status_display = "[dim]? Unchecked[/dim]"
                stats["unchecked"] += 1

            # Extraer primer error si existe
            errors = data.get("validation_errors", [])
            main_error = errors[0] if errors else ""

            table.add_row(municipio, file_path.name, status_display, str(tablas_count), main_error[:50])
            
        except Exception as e:
            console.print(f"[red]Error leyendo {file_path.name}: {e}[/red]")

    console.print(table)
    
    # Resumen final
    console.print(f"\n[bold]Totales:[/bold] [green]Válidos: {stats['valid']}[/green] | [red]Fallidos: {stats['failed']}[/red] | [yellow]Errores: {stats['error']}[/yellow]")
    console.print("\n[dim]Tip: Para corregir un 'Failed', abre el archivo en 'boletines/' y edita 'validation_status'.[/dim]")

if __name__ == "__main__":
    generate_summary()
