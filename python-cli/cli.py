#!/usr/bin/env python3
"""
cli.py - CLI unificada para python-cli v3.0

Este módulo proporciona un punto de entrada único para todos los scrapers:
- SIBOM: Boletines oficiales del sistema SIBOM
- Web: Scraping de sitios web municipales
- Transparency: Datos de transparencia (balances, presupuestos, etc.)
- DB: Operaciones de base de datos

@version 3.0.0
@created 2026-01-29
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


# ============================================================================
# COMANDOS SIBOM
# ============================================================================

def cmd_sibom(args):
    """
    Ejecuta scraping de SIBOM.

    Uso:
        python cli.py sibom --municipality "Carlos Tejedor" --limit 1
        python cli.py sibom --all --limit 5
    """
    from core.sibom_scraper import SIBOMScraper

    console.print(Panel.fit("[bold cyan]SIBOM Scraper[/bold cyan]"))
    console.print()

    scraper = SIBOMScraper()

    if args.all:
        console.print("[yellow]Modo: todos los municipios[/yellow]")
        # Ejecutar para todos los municipios configurados
        scraper.run_all(limit=args.limit)
    elif args.municipality:
        console.print(f"[yellow]Modo: municipio {args.municipality}[/yellow]")
        scraper.run(municipality=args.municipality, limit=args.limit)
    else:
        console.print("[red]Error: especifica --municipality o --all[/red]")
        sys.exit(1)


# ============================================================================
# COMANDOS WEB
# ============================================================================

def cmd_web(args):
    """
    Ejecuta scraping de sitios web municipales.

    Uso:
        python cli.py web --sources config/sources.yaml
        python cli.py web --filter "Carlos Tejedor" "Daireaux"
    """
    console.print(Panel.fit("[bold cyan]Web Scraper[/bold cyan]"))
    console.print()

    async def run_web():
        from core.web_scraper import scrape_all_sources

        sources_file = Path(args.sources) if args.sources else None

        filter_list = args.filter if args.filter else None

        await scrape_all_sources(
            sources_file=sources_file,
            filter_names=filter_list
        )

    asyncio.run(run_web())


# ============================================================================
# COMANDOS TRANSPARENCY
# ============================================================================

def cmd_transparency(args):
    """
    Ejecuta scraping de datos de transparencia.

    MODO AUTOMÁTICO (producción): Lee URLs desde sources_user.yaml
        python cli.py transparency --municipality "Carlos Tejedor" --category balances

    MODO MANUAL (test): URL específica
        python cli.py transparency --municipality "Carlos Tejedor" --category balances --url <URL>
    """
    console.print(Panel.fit("[bold cyan]Transparency Scraper[/bold cyan]"))
    console.print()

    if not args.municipality:
        console.print("[red]Error: --municipality es obligatorio[/red]")
        sys.exit(1)

    async def run_transparency():
        from extractors.vision_extractor import extract_bulletin_with_vision
        import httpx
        from datetime import datetime
        import json
        from config import BOLETINES_DIR, USER_SOURCES_FILE, SOURCES_FILE
        import yaml

        municipio = args.municipality
        category = args.category or "balances"

        console.print(f"[yellow]Municipio: {municipio}[/yellow]")
        console.print(f"[yellow]Categoría: {category}[/yellow]")
        console.print()

        # Directorio de salida: boletines/{Municipio}/
        municipio_slug = municipio.replace(' ', '_')
        output_dir = BOLETINES_DIR / municipio_slug
        output_dir.mkdir(parents=True, exist_ok=True)

        # Obtener URLs: desde --url (modo manual/test) o desde sources_user.yaml (producción)
        if args.url:
            # Modo MANUAL: URL específica proporcionada
            urls = [args.url]
            console.print("[cyan]Modo: Manual (URL específica)[/cyan]")
        else:
            # Modo AUTOMÁTICO: Leer desde sources_user.yaml
            console.print("[cyan]Modo: Automático (desde sources_user.yaml)[/cyan]")

            # Cargar configuración de fuentes
            sources_file = USER_SOURCES_FILE if USER_SOURCES_FILE.exists() else SOURCES_FILE

            with sources_file.open('r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # Buscar fuentes que coincidan con el municipio y categoría
            urls = []
            for source in config_data.get('sources', []):
                source_name = source.get('name', '')
                source_categories = source.get('categories', [])

                # Verificar si coincide con el municipio Y la categoría
                municipio_matches = municipio.lower() in source_name.lower()

                # Verificar si la categoría coincide o si no hay categorías definidas
                category_matches = (not source_categories) or (category in source_categories)

                if municipio_matches and category_matches:
                    url_patterns = source.get('url_patterns', [])
                    # Si la categoría coincide, agregar TODAS las URLs
                    urls.extend(url_patterns)

            if not urls:
                console.print(f"[yellow]No se encontraron URLs para {municipio} / {category}[/yellow]")
                console.print(f"[yellow]Revisa {sources_file.name} o usa --url <URL>[/yellow]")
                return

            console.print(f"[cyan]URLs encontradas: {len(urls)}[/cyan]")

        # Aplicar límite si se especificó
        limit = args.limit if args.limit > 0 else len(urls)
        urls_to_process = urls[:limit]
        if limit < len(urls):
            console.print(f"[yellow]Limitando a {limit} de {len(urls)} URLs[/yellow]")

        # Archivo de progreso para poder retomar
        import hashlib
        progress_file = output_dir / f".{category}_progress.json"
        processed_urls = set()

        # Cargar progreso anterior si existe
        if progress_file.exists():
            try:
                content = progress_file.read_text().strip()
                if content:
                    processed_urls = set(json.loads(content))
                    console.print(f"[dim]Retomando desde {len(processed_urls)} PDFs ya procesados[/dim]")
                else:
                    # Archivo vacío, empezar de cero
                    processed_urls = set()
            except (json.JSONDecodeError, Exception) as e:
                console.print(f"[yellow]Advertencia: archivo de progreso corrupto, empezando de cero[/yellow]")
                processed_urls = set()

        # Función para guardar progreso
        def save_progress():
            with progress_file.open('w') as f:
                json.dump(list(processed_urls), f)

        # Función para guardar un documento individualmente
        def save_individual_doc(doc_data, url):
            # Generar nombre único del archivo basado en la URL
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{municipio_slug}_{category.capitalize()}_{timestamp}_{url_hash}.json"
            output_file = output_dir / filename

            with output_file.open('w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)

            return output_file

        # Estadísticas
        success_count = 0
        error_count = 0
        skip_count = 0

        try:
            for i, url in enumerate(urls_to_process, 1):
                # Saltar si ya fue procesado
                if url in processed_urls:
                    skip_count += 1
                    continue

                console.print(f"[cyan][{i}/{len(urls_to_process)}] {url}[/cyan]")

                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.get(url)
                        if response.status_code != 200:
                            console.print(f"[red]Error HTTP {response.status_code}[/red]")
                            error_count += 1
                            continue

                        # Guardar PDF original si se solicita
                        pdf_file = None
                        if args.keep_pdf:
                            pdf_dir = output_dir / "pdfs"
                            pdf_dir.mkdir(exist_ok=True)
                            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                            pdf_filename = f"{category}_{url_hash}.pdf"
                            pdf_file = pdf_dir / pdf_filename
                            pdf_file.write_bytes(response.content)
                            console.print(f"[dim]  PDF guardado: {pdf_filename}[/dim]")

                        # Usar Vision API para extraer contenido
                        # Para documentos de transparencia (balances, presupuestos), usar prompt de tablas
                        is_transparency_doc = category in ["balances", "presupuestos", "concursos", "licitaciones"]

                        result = await extract_bulletin_with_vision(
                            response.content,
                            url,
                            municipio,
                            extract_tables=is_transparency_doc
                        )

                        if result:
                            title, content, quality = result

                            # Guardar en formato TransparencyDocument
                            from extractors.vision_extractor import extract_tables_as_markdown
                            tablas_md = extract_tables_as_markdown(content)

                            # =====================================================================
                            # EXTRAER CABECERA DEL DOCUMENTO (datos importantes de la primera página)
                            # =====================================================================
                            from extractors.balance_header import extract_header_with_periodo_code

                            cabecera = {}
                            periodo_extraido = "s/d"  # sin dato
                            fecha_doc_extraida = "s/d"
                            tipo_detalle = ""

                            # Intentar extraer desde la cabecera del contenido
                            try:
                                cabecera, periodo_from_header = extract_header_with_periodo_code(content, municipio)

                                if cabecera.get("fecha_generacion"):
                                    # Formato: "20/07/2020 08:09" -> tomar solo la fecha
                                    fecha_doc_extraida = cabecera["fecha_generacion"].split()[0]

                                if cabecera.get("tipo_documento"):
                                    tipo_detalle = cabecera["tipo_documento"]

                                # Usar periodo de cabecera si está disponible
                                if periodo_from_header:
                                    periodo_extraido = periodo_from_header
                            except Exception as header_err:
                                # Si falla la extracción de cabecera, continuar con fallback
                                pass

                            # =====================================================================
                            # FALLBACK: Extraer periodo del nombre del archivo si no se pudo de cabecera
                            # =====================================================================
                            if periodo_extraido == "s/d":
                                import re
                                filename = url.split('/')[-1]
                                year_match = re.search(r'20\d{2}', filename)
                                trimestre_match = re.search(r'(\d+)[°o]?\s*-?\s*Trimestre', filename, re.IGNORECASE)
                                semestre_match = re.search(r'(\d+)[°o]?\s*-?\s*Semestre', filename, re.IGNORECASE)

                                if year_match:
                                    year = year_match.group(0)
                                    if trimestre_match:
                                        trimestre_num = trimestre_match.group(1)
                                        periodo_extraido = f"{year}-T{trimestre_num}"
                                    elif semestre_match:
                                        semestre_num = semestre_match.group(1)
                                        periodo_extraido = f"{year}-S{semestre_num}"
                                    else:
                                        periodo_extraido = year

                            # Usar el periodo especificado por args si existe, sino el extraído
                            periodo_final = args.period if args.period else periodo_extraido

                            doc_data = {
                                "municipio": municipio,
                                "tipo_documento": category,
                                "tipo_detalle": tipo_detalle,  # NUEVO: tipo específico del documento
                                "periodo": periodo_final,
                                "fecha_documento": fecha_doc_extraida,
                                "cabecera": cabecera,  # NUEVO: datos completos de cabecera
                                "contenido": content,  # CRÍTICO: texto completo extraído del PDF
                                "url_origen": url,
                                "titulo_extraido": title,
                                "status": "completed",
                                "tablas_md": tablas_md,
                                "calidad": quality,
                                "pdf_file": str(pdf_file) if pdf_file else None,
                                "metadata": {
                                    "fecha_scraping": datetime.now().isoformat(),
                                    "version_scraper": "3.2",  # Actualizado: ahora incluye cabecera y contenido
                                    "source_type": "transparency_vision"
                                }
                            }

                            # Guardar individualmente INMEDIATAMENTE
                            output_file = save_individual_doc(doc_data, url)

                            # Agregar el nombre del archivo JSON para que el chatbot lo pueda encontrar
                            doc_data["json_file"] = output_file.name

                            # Guardar en SQLite
                            try:
                                from utils.sqlite_manager import get_sqlite_manager
                                mgr = get_sqlite_manager()
                                mgr.insert_transparency_doc(doc_data)
                                console.print(f"[dim]  → SQLite actualizado[/dim]")
                            except Exception as sqlite_err:
                                console.print(f"[yellow]  ⚠ SQLite: {sqlite_err}[/yellow]")

                            processed_urls.add(url)
                            save_progress()  # Guardar progreso después de cada PDF

                            success_count += 1
                            console.print(f"[green]✓ Extraído: {title[:50]}...[/green]")
                            console.print(f"  Tablas: {len(tablas_md)}, Calidad: {quality['confidence']:.1%}")
                            console.print(f"  [dim]JSON guardado: {output_file.name}[/dim]")
                        else:
                            error_count += 1
                            console.print(f"[yellow]⚠ No se pudo extraer contenido[/yellow]")

                except KeyboardInterrupt:
                    # Usuario canceló con Ctrl+C
                    console.print("\n[yellow]⚠️ Cancelado por usuario (Ctrl+C)[/yellow]")
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    error_count += 1

        finally:
            # Siempre mostrar resumen final
            console.print()
            console.print(f"[bold]Resumen:[/bold]")
            console.print(f"  ✓ Exitosos: {success_count}")
            console.print(f"  ✗ Errores: {error_count}")
            console.print(f"  ⊘ Saltados (ya procesados): {skip_count}")
            console.print(f"  → Total procesados: {len(processed_urls)}")

            if processed_urls and success_count > 0:
                console.print(f"\n[green]✓ Progreso guardado en {progress_file.name}[/green]")
                console.print("[dim]Usa --skip-existing para retomar donde dejaste[/dim]")

    asyncio.run(run_transparency())


# ============================================================================
# COMANDOS DB
# ============================================================================

def cmd_db(args):
    """
    Operaciones de base de datos.

    Uso:
        python cli.py db --stats
        python cli.py db --export output.json
        python cli.py db --search --municipality "Carlos Tejedor"
    """
    from utils.sqlite_manager import get_sqlite_manager
    from config import DEFAULT_DB_PATH

    console.print(Panel.fit("[bold cyan]SQLite Manager[/bold cyan]"))
    console.print()

    mgr = get_sqlite_manager(DEFAULT_DB_PATH)

    if args.stats:
        console.print("[yellow]Estadísticas de la base de datos:[/yellow]\n")
        mgr.print_stats()

    elif args.export:
        output_path = Path(args.export)
        console.print(f"[yellow]Exportando a {output_path}...[/yellow]")
        mgr.export_json(output_path, include_content=args.content)

    elif args.search:
        console.print("[yellow]Buscando normativas:[/yellow]\n")

        results = mgr.search(
            municipality=args.municipality,
            tipo=args.type,
            year=args.year,
            limit=args.limit
        )

        if results:
            table = Table(title=f"Resultados ({len(results)})")
            table.add_column("ID", style="dim")
            table.add_column("Municipio")
            table.add_column("Tipo")
            table.add_column("Nº")
            table.add_column("Año")
            table.add_column("Fecha")
            table.add_column("Título")

            for r in results[:args.limit]:
                table.add_row(
                    r['id'][:8] + "...",
                    r['municipality'][:20],
                    r['type'][:15],
                    r['number'],
                    r['year'],
                    r['date'] or "-",
                    r['title'][:40] + "..." if r['title'] and len(r['title']) > 40 else (r['title'] or "-")
                )

            console.print(table)
        else:
            console.print("[dim]No se encontraron resultados[/dim]")

    else:
        console.print("[yellow]Opciones disponibles:[/yellow]")
        console.print("  --stats     Mostrar estadísticas")
        console.print("  --export    Exportar a JSON")
        console.print("  --search    Buscar normativas")


# ============================================================================
# COMANDOS VISION
# ============================================================================

def cmd_vision(args):
    """
    Prueba la extracción con Vision API.

    Uso:
        python cli.py vision --url https://example.com/documento.pdf
        python cli.py vision --test
    """
    console.print(Panel.fit("[bold cyan]Vision API Test[/bold cyan]"))
    console.print()

    async def run_vision():
        from extractors.vision_extractor import extract_bulletin_with_vision
        import httpx

        if args.test:
            # URL de prueba
            url = "https://boletin.casares.gob.ar/archivos_boletin_oficial/boletin_oficial_31.pdf"
            console.print(f"[yellow]URL de prueba: {url}[/yellow]\n")
        elif args.url:
            url = args.url
            console.print(f"[yellow]URL: {url}[/yellow]\n")
        else:
            console.print("[red]Error: especifica --url o --test[/red]")
            sys.exit(1)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    console.print(f"[red]Error HTTP {response.status_code}[/red]")
                    return

            console.print("[cyan]Extrayendo con Vision API...[/cyan]\n")

            result = await extract_bulletin_with_vision(
                response.content,
                url,
                municipio=args.municipality or "Prueba"
            )

            if result:
                title, content, quality = result

                console.print(Panel.fit(f"[bold green]Extracción exitosa[/bold green]"))
                console.print()
                console.print(f"Título: {title}")
                console.print(f"Longitud: {len(content):,} caracteres")
                console.print(f"Calidad: {quality['confidence']:.1%} ({quality['quality']})")
                console.print()

                if args.output:
                    output_path = Path(args.output)
                    with output_path.open('w', encoding='utf-8') as f:
                        f.write(content)
                    console.print(f"[green]✓ Contenido guardado en {output_path}[/green]")
            else:
                console.print("[red]La extracción falló[/red]")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    asyncio.run(run_vision())


# ============================================================================
# COMANDO INDEX
# ============================================================================

def cmd_index(args):
    """
    Gestiona índices de normativas.

    Uso:
        python cli.py index --rebuild
    """
    from config import BOLETINES_DIR, INDEXES_DIR
    from extractors.normativas_extractor import save_index, save_minimal_index
    import json

    console.print(Panel.fit("[bold cyan]Index Manager[/bold cyan]"))
    console.print()

    if args.rebuild:
        console.print("[yellow]Reconstruyendo índices desde boletines/ y SQLite...[/yellow]\n")

        all_normas = []

        # 1. Leer todos los JSON de boletines
        console.print("[cyan]1. Leyendo JSONs de boletines...[/cyan]")
        for json_file in BOLETINES_DIR.glob("*.json"):
            console.print(f"[dim]  Leyendo {json_file.name}...[/dim]")

            try:
                with json_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'normas' in data:
                    all_normas.extend(data['normas'])
                elif isinstance(data, list):
                    all_normas.extend(data)
            except Exception as e:
                console.print(f"[yellow]  Error leyendo {json_file.name}: {e}[/yellow]")

        console.print(f"\n[cyan]  Normativas desde JSON: {len(all_normas):,}[/cyan]\n")

        # 2. Leer documentos de transparencia desde SQLite
        console.print("[cyan]2. Leyendo documentos de transparencia desde SQLite...[/cyan]")
        try:
            from utils.sqlite_manager import get_sqlite_manager
            mgr = get_sqlite_manager()

            # Obtener documentos de transparencia
            trans_docs = mgr.get_all_transparency_for_index()
            console.print(f"[cyan]  Documentos de transparencia: {len(trans_docs):,}[/cyan]\n")

            # Agregar a las normativas (el índice del chatbot usa el mismo formato)
            all_normas.extend(trans_docs)

        except Exception as e:
            console.print(f"[yellow]  ⚠ No se pudieron leer documentos de transparencia: {e}[/yellow]\n")

        console.print(f"[bold green]Total de documentos a indexar: {len(all_normas):,}[/bold green]\n")

        # Guardar índices
        index_file = INDEXES_DIR / "normativas_index.json"
        compact_file = INDEXES_DIR / "normativas_index_compact.json"
        minimal_file = INDEXES_DIR / "normativas_index_minimal.json"

        # Intentar convertir a objetos Normativa, pero mantener dicts minimalistas
        from core.data_models import Normativa

        final_list = []
        for n in all_normas:
            if isinstance(n, dict):
                # Los documentos de transparencia ya vienen en formato minimalista (m, t, n, etc.)
                # Los dejamos tal cual para que save_minimal_index los use directamente
                if 'm' in n and 'municipality' not in n:
                    # Formato minimalista (desde SQLite transparency)
                    final_list.append(n)
                elif 'municipality' in n:
                    # Formato completo, intentar convertir a Normativa
                    try:
                        final_list.append(Normativa(**n))
                    except Exception:
                        final_list.append(n)
                else:
                    final_list.append(n)
            else:
                final_list.append(n)

        save_index(final_list, index_file, compact=False)
        save_index(final_list, compact_file, compact=True)
        save_minimal_index(final_list, minimal_file)

        console.print(f"[green]✓ Índices reconstruidos:[/green]")
        console.print(f"  - {index_file.name}")
        console.print(f"  - {compact_file.name}")
        console.print(f"  - {minimal_file.name}")


# ============================================================================
# COMANDO STATUS
# ============================================================================

def cmd_status(args):
    """
    Muestra el estado completo del scraping.

    Dashboard con información de:
    - Archivos procesados por categoría
    - PDFs exitosos vs fallidos
    - Rate limit de Vision API
    - Progreso global con barras visuales

    Uso:
        python cli.py status
        python cli.py status --municipality "Carlos Tejedor"
    """
    from config import BOLETINES_DIR, USER_SOURCES_FILE, SOURCES_FILE
    import json
    import yaml
    from datetime import datetime

    console.print()
    console.print(Panel.fit(
        "[bold cyan]📊 Estado del Scraping[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    # 1. Obtener municipios disponibles
    municipios = {}
    for municipio_dir in BOLETINES_DIR.iterdir():
        if municipio_dir.is_dir() and not municipio_dir.name.startswith('.'):
            municipio_slug = municipio_dir.name
            municipio_name = municipio_slug.replace('_', ' ')

            # Contar archivos JSON
            json_files = list(municipio_dir.glob("*.json"))
            json_count = len(json_files)

            # Buscar archivos de progreso
            progress_files = list(municipio_dir.glob(".*_progress.json"))

            # PDFs guardados
            pdf_dir = municipio_dir / "pdfs"
            pdf_count = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0

            municipios[municipio_name] = {
                'slug': municipio_slug,
                'json_count': json_count,
                'progress_files': progress_files,
                'pdf_count': pdf_count
            }

    # 2. Categorías por municipio (desde sources)
    sources_file = USER_SOURCES_FILE if USER_SOURCES_FILE.exists() else SOURCES_FILE
    categories_info = {}

    if sources_file.exists():
        with sources_file.open('r', encoding='utf-8') as f:
            sources = yaml.safe_load(f).get('sources', [])

        for source in sources:
            name = source.get('name', '')
            cats = source.get('categories', ['general'])
            url_count = len(source.get('url_patterns', []))
            enabled = source.get('enabled', False)

            for cat in cats:
                if cat not in categories_info:
                    categories_info[cat] = {'total_urls': 0, 'enabled': False, 'sources': []}
                categories_info[cat]['total_urls'] += url_count
                categories_info[cat]['sources'].append(name)
                if enabled:
                    categories_info[cat]['enabled'] = True

    # 3. Tabla de municipios
    console.print("[bold]📁 Municipios:[/bold]")
    municipio_table = Table(show_header=True, header_style="bold cyan")
    municipio_table.add_column("Municipio", style="cyan")
    municipio_table.add_column("JSONs", justify="right", style="green")
    municipio_table.add_column("PDFs", justify="right", style="yellow")
    municipio_table.add_column("Progreso", justify="right")

    for name, info in sorted(municipios.items()):
        # Calcular progreso
        processed_urls = 0
        for progress_file in info['progress_files']:
            try:
                with progress_file.open('r') as f:
                    urls = json.load(f)
                    processed_urls += len(urls) if isinstance(urls, list) else 0
            except:
                pass

        # Total URLs para este municipio
        total_urls = sum(v['total_urls'] for k, v in categories_info.items() if name.lower() in ' '.join(v['sources']).lower())

        if total_urls > 0:
            percent = (processed_urls / total_urls) * 100
            bar_length = int(percent / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            progress_str = f"{percent:.0f}% [{bar}]"
        else:
            progress_str = "-"

        municipio_table.add_row(
            name,
            str(info['json_count']),
            str(info['pdf_count']),
            progress_str
        )

    console.print(municipio_table)
    console.print()

    # 4. Tabla de categorías
    if categories_info:
        console.print("[bold]📂 Categorías:[/bold]")
        cat_table = Table(show_header=True, header_style="bold cyan")
        cat_table.add_column("Categoría", style="cyan")
        cat_table.add_column("URLs", justify="right", style="green")
        cat_table.add_column("Estado", justify="center")
        cat_table.add_column("Fuentes")

        for cat, info in sorted(categories_info.items()):
            status = "[green]✓ Habilitado[/green]" if info['enabled'] else "[dim]— Deshabilitado[/dim]"
            sources_str = ', '.join(info['sources'])[:40] + '...' if len(', '.join(info['sources'])) > 40 else ', '.join(info['sources'])

            cat_table.add_row(
                cat.capitalize(),
                str(info['total_urls']),
                status,
                sources_str
            )

        console.print(cat_table)
        console.print()

    # 5. Archivos JSON recientes
    all_jsons = []
    for municipio_dir in BOLETINES_DIR.iterdir():
        if municipio_dir.is_dir() and not municipio_dir.name.startswith('.'):
            for json_file in municipio_dir.glob("*.json"):
                try:
                    stat = json_file.stat()
                    all_jsons.append({
                        'file': json_file,
                        'municipio': municipio_dir.name.replace('_', ' '),
                        'size': stat.st_size,
                        'mtime': stat.st_mtime
                    })
                except:
                    pass

    # Ordenar por fecha de modificación
    all_jsons.sort(key=lambda x: x['mtime'], reverse=True)

    if all_jsons:
        console.print("[bold]📄 Archivos JSON Recientes:[/bold]")
        recent_table = Table(show_header=True, header_style="bold cyan")
        recent_table.add_column("Municipio", style="cyan")
        recent_table.add_column("Archivo")
        recent_table.add_column("Tamaño", justify="right")
        recent_table.add_column("Fecha")

        for f in all_jsons[:10]:
            fecha = datetime.fromtimestamp(f['mtime']).strftime("%Y-%m-%d %H:%M")
            size_str = f"{f['size'] / 1024:.1f} KB" if f['size'] > 1024 else f"{f['size']} B"
            recent_table.add_row(
                f['municipio'][:20],
                f['file'].name[:35],
                size_str,
                fecha
            )

        console.print(recent_table)
        console.print()

    # 6. Rate limit Vision API con detalles de consumo
    try:
        from utils.vision_rate_limiter import get_rate_limiter
        from config import CACHE_DIR

        limiter = get_rate_limiter()
        stats = limiter.get_stats()

        if stats:
            console.print("[bold]🔌 Vision API - Consumo:[/bold]")

            today = stats.get('today', 0)
            limit = stats.get('limit', 1000)
            total_all_time = stats.get('total_all_time', 0)
            remaining = limit - today
            percent = (today / limit * 100) if limit > 0 else 0

            bar_length = int(percent / 5)
            if percent < 70:
                bar_color = "green"
            elif percent < 90:
                bar_color = "yellow"
            else:
                bar_color = "red"

            bar = "█" * bar_length + "░" * (20 - bar_length)

            # Calcular tokens y costos estimados
            # Asumiendo: ~500 tokens/input + ~1000 tokens/output por página
            # Promedio: 5 páginas por PDF
            avg_tokens_per_request = 7500  # estimado conservador
            total_tokens_estimated = total_all_time * avg_tokens_per_request

            # Costo estimado (Qwen VL: $0.50/1M tokens input, $1.50/1M tokens output)
            # Promedio ponderado: ~$1/1M tokens
            cost_per_million_tokens = 1.0  # USD
            estimated_cost_usd = (total_tokens_estimated / 1_000_000) * cost_per_million_tokens

            # Obtener historial de días si existe
            usage_file = CACHE_DIR / "vision_api_usage.json"
            days_history = []
            if usage_file.exists():
                try:
                    with usage_file.open('r') as f:
                        usage_data = json.load(f)
                        days_history = [
                            (day, count) for day, count in usage_data.get('days', {}).items()
                        ]
                        days_history.sort(reverse=True)
                except:
                    pass

            # Tabla de consumo
            api_table = Table(show_header=False, box=None)
            api_table.add_column("Metrica", style="cyan")
            api_table.add_column("Valor", justify="right")

            api_table.add_row("Calls hoy", f"[bold]{today}[/bold] / {limit}")
            api_table.add_row("Restantes", f"[{bar_color}]{remaining}[/{bar_color}]")
            api_table.add_row("Progreso", f"[{bar_color}][{bar}][/{bar_color}] {percent:.1f}%")
            api_table.add_row("")
            api_table.add_row("Calls hist.", f"[dim]{total_all_time:,}[/dim]")
            api_table.add_row("Tokens est.", f"[dim]~{total_tokens_estimated:,}[/dim]")
            api_table.add_row("Costo total", f"[dim]~${estimated_cost_usd:.2f} USD[/dim]")

            console.print(api_table)

            # Historial de últimos días
            if days_history and len(days_history) > 1:
                console.print(f"\n[dim]Últimos {len(days_history)} días:[/dim]", end=" ")
                for day, count in days_history[:7]:
                    console.print(f"[dim]{day[5:]}:[/dim] {count}", end="  ")
                console.print()

            if today >= limit:
                console.print("\n  [red]⚠️ Límite diario alcanzado[/red]")

            console.print()
    except Exception as e:
        console.print(f"[dim]Error obteniendo stats de Vision API: {e}[/dim]")
        console.print()

    # 7. Modelos LLM - Consumo detallado
    try:
        from utils.llm_tracker import get_llm_tracker

        tracker = get_llm_tracker()
        stats = tracker.get_stats(days=7)  # Últimos 7 días

        if stats and stats.get('models'):
            console.print("[bold]🤖 Modelos LLM - Consumo (7 días):[/bold]")

            models_table = Table(show_header=True, header_style="bold cyan")
            models_table.add_column("Modelo", style="cyan", width=25)
            models_table.add_column("Tarea", justify="left")
            models_table.add_column("Calls", justify="right")
            models_table.add_column("Tokens", justify="right")
            models_table.add_column("Costo", justify="right")

            for model_name, data in stats['models'].items():
                # Nombre corto del modelo
                short_name = data.get('display_name', model_name.split('/')[-1][:20])

                # Emoji según tarea
                task_emoji = {
                    'vision': '👁️',
                    'vision_tables': '📊',
                    'sibom_parsing': '📄',
                    'transparency': '💰',
                    'llm': '🤖'
                }.get(data.get('task', ''), '📌')

                # Formatear costo
                costo = data['cost']
                if costo == 0:
                    costo_str = "[green]GRATIS[/green]"
                else:
                    costo_str = f"[yellow]${costo:.4f}[/yellow]"

                # Formatear tokens
                tokens = data['total_tokens']
                if tokens >= 1_000_000:
                    tokens_str = f"{tokens/1_000_000:.1f}M"
                elif tokens >= 1_000:
                    tokens_str = f"{tokens/1_000:.1f}K"
                else:
                    tokens_str = str(tokens)

                models_table.add_row(
                    short_name,
                    f"{task_emoji} {data.get('task', 'N/A')}",
                    str(data['calls']),
                    tokens_str,
                    costo_str
                )

            console.print(models_table)

            # Total
            total = stats['total']
            console.print(f"  [dim]Total: {total['calls']} calls, {total['total_tokens']:,} tokens, ${total['cost']:.4f} USD[/dim]")
            console.print(f"  [dim]Período: {stats['period']}[/dim]")
            console.print()
    except Exception as e:
        console.print(f"[dim]Error obteniendo stats de LLM: {e}[/dim]")
        console.print()

    # 8. Estadísticas de SQLite (incluyendo transparency)
    try:
        from utils.sqlite_manager import get_sqlite_manager

        mgr = get_sqlite_manager()
        stats = mgr.get_stats()

        if stats.get('total_normativas', 0) > 0 or stats.get('total_transparency', 0) > 0:
            console.print("[bold]🗄️ SQLite - Base de Datos:[/bold]")

            db_table = Table(show_header=False, box=None)
            db_table.add_column("Métrica", style="cyan")
            db_table.add_column("Valor", justify="right")

            # Normativas
            total_norm = stats.get('total_normativas', 0)
            with_content = stats.get('with_content', 0)
            db_table.add_row("Normativas", f"[bold]{total_norm:,}[/bold]")
            db_table.add_row("  Con contenido", f"[dim]{with_content:,}[/dim]")

            # Transparency
            total_trans = stats.get('total_transparency', 0)
            trans_with_tables = stats.get('transparency_with_tables', 0)
            db_table.add_row("Transparencia", f"[bold green]{total_trans:,}[/bold green]")
            db_table.add_row("  Con tablas", f"[dim]{trans_with_tables:,}[/dim]")

            # Total
            db_table.add_row("")
            db_table.add_row("Total documentos", f"[bold]{total_norm + total_trans:,}[/bold]")

            console.print(db_table)
            console.print()
    except Exception as e:
        console.print(f"[dim]Error obteniendo stats de SQLite: {e}[/dim]")
        console.print()

    # 9. Resumen general
    total_jsons = sum(m['json_count'] for m in municipios.values())
    total_pdfs = sum(m['pdf_count'] for m in municipios.values())
    total_urls = sum(c['total_urls'] for c in categories_info.values())

    summary_text = (
        f"[bold]Resumen:[/bold]\n"
        f"  Municipios: {len(municipios)}\n"
        f"  JSONs generados: {total_jsons}\n"
        f"  PDFs guardados: {total_pdfs}\n"
        f"  URLs descubiertas: {total_urls}"
    )

    console.print(Panel.fit(
        summary_text,
        title="[bold green]Estado General[/bold green]",
        border_style="green"
    ))
    console.print()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Punto de entrada principal de la CLI."""

    parser = argparse.ArgumentParser(
        description="SIBOM Scraper v3.0 - CLI unificada",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # SIBOM
  python cli.py sibom --municipality "Carlos Tejedor" --limit 1
  python cli.py sibom --all --limit 5

  # Web (lee desde sources_user.yaml)
  python cli.py web --filter "Carlos Tejedor"

  # Transparency (automático desde sources_user.yaml)
  python cli.py transparency --municipality "Carlos Tejedor" --category balances

  # Transparency (manual - para tests)
  python cli.py transparency --municipality "Carlos Tejedor" --category balances --url <URL>

  # Base de datos
  python cli.py db --stats
  python cli.py db --search --municipality "Carlos Tejedor"

  # Status - Estado del scraping
  python cli.py status

Para más ayuda sobre un comando específico:
  python cli.py <comando> --help
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')

    # ---------------------------------------------------------------------
    # SIBOM
    # ---------------------------------------------------------------------
    sibom_parser = subparsers.add_parser(
        'sibom',
        help='Scrapear boletines de SIBOM'
    )
    sibom_parser.add_argument(
        '--municipality', '--municipio',
        dest='municipality',
        help='Nombre del municipio (ej: "Carlos Tejedor")'
    )
    sibom_parser.add_argument(
        '--all',
        action='store_true',
        help='Ejecutar para todos los municipios'
    )
    sibom_parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Límite de boletines a procesar (0 = todos)'
    )

    # ---------------------------------------------------------------------
    # WEB
    # ---------------------------------------------------------------------
    web_parser = subparsers.add_parser(
        'web',
        help='Scrapear sitios web municipales'
    )
    web_parser.add_argument(
        '--sources',
        default='config/sources.yaml',
        help='Archivo YAML con configuración de fuentes'
    )
    web_parser.add_argument(
        '--filter',
        nargs='+',
        help='Filtrar por nombre de fuente'
    )
    web_parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Saltar archivos ya procesados'
    )

    # ---------------------------------------------------------------------
    # TRANSPARENCY
    # ---------------------------------------------------------------------
    trans_parser = subparsers.add_parser(
        'transparency',
        help='Scrapear datos de transparencia'
    )
    trans_parser.add_argument(
        '--municipality', '--municipio',
        dest='municipality',
        required=True,
        help='Nombre del municipio'
    )
    trans_parser.add_argument(
        '--category',
        choices=['balances', 'presupuestos', 'licitaciones', 'concursos'],
        default='balances',
        help='Categoría de documento'
    )
    trans_parser.add_argument(
        '--url',
        help='URL específica del documento'
    )
    trans_parser.add_argument(
        '--period',
        help='Período (ej: 2025-Q2, 2025)'
    )
    trans_parser.add_argument(
        '--sqlite',
        action='store_true',
        help='Guardar también en SQLite'
    )
    trans_parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Saltar archivos ya procesados'
    )
    trans_parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='Límite de documentos a procesar (0 = todos)'
    )
    trans_parser.add_argument(
        '--keep-pdf',
        action='store_true',
        help='Guardar PDF original en carpeta pdfs/'
    )

    # ---------------------------------------------------------------------
    # DB
    # ---------------------------------------------------------------------
    db_parser = subparsers.add_parser(
        'db',
        help='Operaciones de base de datos'
    )
    db_parser.add_argument(
        '--stats',
        action='store_true',
        help='Mostrar estadísticas'
    )
    db_parser.add_argument(
        '--export',
        help='Exportar a JSON (ruta del archivo)'
    )
    db_parser.add_argument(
        '--content',
        action='store_true',
        help='Incluir contenido en exportación'
    )
    db_parser.add_argument(
        '--search',
        action='store_true',
        help='Buscar normativas'
    )
    db_parser.add_argument(
        '--municipality', '--municipio',
        dest='municipality',
        help='Filtrar por municipio'
    )
    db_parser.add_argument(
        '--type',
        help='Filtrar por tipo'
    )
    db_parser.add_argument(
        '--year',
        help='Filtrar por año'
    )
    db_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Límite de resultados'
    )

    # ---------------------------------------------------------------------
    # VISION
    # ---------------------------------------------------------------------
    vision_parser = subparsers.add_parser(
        'vision',
        help='Probar Vision API'
    )
    vision_parser.add_argument(
        '--url',
        help='URL del PDF a procesar'
    )
    vision_parser.add_argument(
        '--test',
        action='store_true',
        help='Usar URL de prueba'
    )
    vision_parser.add_argument(
        '--municipality', '--municipio',
        dest='municipality',
        default='Prueba',
        help='Nombre del municipio (default: Prueba)'
    )
    vision_parser.add_argument(
        '--output',
        help='Guardar contenido extraído en archivo'
    )

    # ---------------------------------------------------------------------
    # INDEX
    # ---------------------------------------------------------------------
    index_parser = subparsers.add_parser(
        'index',
        help='Gestionar índices'
    )
    index_parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Reconstruir índices desde boletines/'
    )

    # ---------------------------------------------------------------------
    # STATUS
    # ---------------------------------------------------------------------
    status_parser = subparsers.add_parser(
        'status',
        help='Mostrar estado del scraping'
    )
    status_parser.add_argument(
        '--municipality', '--municipio',
        dest='municipality',
        help='Filtrar por municipio'
    )

    # Parsear argumentos
    args = parser.parse_args()

    # Ejecutar comando
    if args.command == 'sibom':
        cmd_sibom(args)
    elif args.command == 'web':
        cmd_web(args)
    elif args.command == 'transparency':
        cmd_transparency(args)
    elif args.command == 'db':
        cmd_db(args)
    elif args.command == 'vision':
        cmd_vision(args)
    elif args.command == 'index':
        cmd_index(args)
    elif args.command == 'status':
        cmd_status(args)
    else:
        # Sin comando: mostrar ayuda
        parser.print_help()


if __name__ == '__main__':
    main()
