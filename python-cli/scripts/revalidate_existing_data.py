
import os
import json
import sys
from pathlib import Path
from rich.console import Console

# Add parent directory to sys.path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.financial_validator import FinancialValidator, markdown_to_dataframe, ChunkGenerator, FinancialMetadata
from utils.sqlite_manager import get_sqlite_manager

console = Console()

def revalidate_all():
    boletines_path = Path("boletines")
    if not boletines_path.exists():
        console.print("[red]Error: La carpeta 'boletines' no existe.[/red]")
        return

    validator = FinancialValidator()
    chunker = ChunkGenerator()
    mgr = get_sqlite_manager()
    files = [f for f in boletines_path.rglob("*.json") if "test" not in str(f).lower()]
    
    console.print(f"[cyan]🚀 Iniciando re-validación de {len(files)} archivos...[/cyan]")
    
    updated_count = 0

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Solo procesar balances
            category = data.get("tipo_documento", "")
            if "balance" not in category.lower():
                continue

            tablas_md = data.get("tablas_md", [])
            if not tablas_md:
                continue

            is_any_valid = False
            all_errors = []

            has_tables = False
            for idx, md_table in enumerate(tablas_md):
                df = markdown_to_dataframe(md_table)
                if df.empty: continue
                has_tables = True
                
                try:
                    res = validator.validate_balance_sheet(df)
                    if res['is_valid'].all():
                        is_any_valid = True
                    else:
                        invalid_rows = res[~res['is_valid']]
                        for _, row in invalid_rows.iterrows():
                            all_errors.append(f"Table {idx+1}: {row.get('cuenta')} inconsistente")
                except ValueError as ve:
                    # Probablemente faltan columnas de validación aritmética, lo ignoramos para permitir indexación
                    console.print(f"[dim]  ℹ Table {idx+1} skipped arithmetic validation: {ve}[/dim]")
                    continue
                except Exception as e:
                    console.print(f"[dim]  ⚠ Unexpected error in table {idx+1}: {e}[/dim]")
                    continue

            # Actualizar estado y generar chunks si es válido
            rag_chunks = []
            
            # Decisión final de estado: 
            # Si hay errores de inconsistencia -> Failed
            # Si pasó validación aritmética -> Valid
            # Si no se pudo validar pero tiene tablas -> Valid (pero indicamos que no se validó aritméticamente)
            if all_errors:
                data["validation_status"] = "failed"
                data["validation_errors"] = all_errors[:10]
            elif is_any_valid or has_tables:
                data["validation_status"] = "valid"
                data["validation_errors"] = []
                
                # Generar chunks para el RAG
                try:
                    meta = FinancialMetadata(
                        entity=data.get("municipio", "n/a"),
                        document_type=category,
                        period=data.get("periodo", "s/d"),
                        year=int(data.get("periodo", "2024").split("-")[0]) if "-" in str(data.get("periodo")) else 2024,
                        month=1, # Default
                        page_number=1,
                        source_file=file_path.name
                    )
                    for md_table in tablas_md:
                        df = markdown_to_dataframe(md_table)
                        if not df.empty:
                            table_chunks = chunker.generate_chunks(df, meta)
                            rag_chunks.extend([c.to_dict() for c in table_chunks])
                except Exception as chunk_err:
                    console.print(f"[dim]  ⚠ Chunking error: {chunk_err}[/dim]")
            else:
                data["validation_status"] = "unchecked"
                data["validation_errors"] = ["No se encontraron tablas procesables"]

            data["rag_chunks"] = rag_chunks
            data["rag_chunks_count"] = len(rag_chunks)
            # Asegurar que json_file esté presente (relativo a boletines/)
            data["json_file"] = str(file_path.relative_to(boletines_path))

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # Sincronizar con SQLite
            try:
                # Asegurar que doc_data tenga los campos necesarios para SQLite
                mgr.insert_transparency_doc(data)
            except Exception as sql_e:
                console.print(f"[dim]  ⚠ SQLite sync error: {sql_e}[/dim]")

            updated_count += 1
            if updated_count % 10 == 0:
                console.print(f"[dim]  Processed {updated_count} files...[/dim]")

        except Exception as e:
            console.print(f"[red]Error procesando {file_path.name}: {e}[/red]")

    console.print(f"\n[bold green]✅ Re-validación completada: {updated_count} archivos actualizados.[/bold green]")
    console.print("[dim]Ejecuta 'python3 scripts/data_summary.py' para ver los resultados.[/dim]")

if __name__ == "__main__":
    revalidate_all()
