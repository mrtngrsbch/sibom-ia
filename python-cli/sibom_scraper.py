#!/usr/bin/env python3
"""
SIBOM Scraper - CLI Tool
Extrae boletines oficiales de SIBOM usando OpenRouter con modelos LLM configurables
Default: google/gemini-3-flash-preview
Soporta: z-ai/glm-4.5-air:free, google/gemini-2.5-flash-lite, x-ai/grok-4.1-fast, etc.
"""

import os
import sys
import json
import time
import re
import argparse
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from bs4 import BeautifulSoup

# Cargar variables de entorno
load_dotenv()

console = Console()

class SIBOMScraper:
    def __init__(self, api_key: str, model: str = "z-ai/glm-4.5-air:free"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self.rate_limit_delay = 3  # segundos entre llamadas
        self.last_call_time = 0

    def _wait_for_rate_limit(self):
        """Espera según rate limiting"""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_call_time = time.time()

    def _extract_json(self, text: str) -> str:
        """Limpia markdown code blocks de la respuesta"""
        cleaned = text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _sanitize_filename(self, description: str, number: str = None) -> str:
        """
        Convierte descripción en nombre de archivo válido.
        Ejemplo: "105º de Carlos Tejedor" -> "Carlos_Tejedor_105"
        Ejemplo: "Boletín Oficial Municipal de Carlos Tejedor...", number="98º" -> "Carlos_Tejedor_98"
        """
        # Si se proporciona number explícitamente, úsalo; sino, extráelo de la descripción
        if number:
            # Extraer solo dígitos del número (ej: "98º" -> "98")
            number_match = re.search(r'(\d+)', number)
            num = number_match.group(1) if number_match else "0"
        else:
            # Extraer número del boletín de la descripción (buscar patrón como "105º")
            number_match = re.search(r'(\d+)º?', description)
            num = number_match.group(1) if number_match else "0"

        # Para descripciones largas (modo individual), extraer solo el nombre de la ciudad
        # Buscar patrón "de [Ciudad]" o "Municipal de [Ciudad]" o "Municipalidad de [Ciudad]"
        if len(description) > 50:
            city_match = re.search(r'(?:de\s+la\s+Municipalidad\s+de\s+|Municipal\s+de\s+|de\s+)([A-Z][a-zA-Z\s]+?)(?:\s+que|\s*$|,)', description)
            if city_match:
                cleaned = city_match.group(1).strip()
                cleaned = re.sub(r'[^\w\s-]', '', cleaned)
                cleaned = re.sub(r'\s+', '_', cleaned.strip())
                return f"{cleaned}_{num}"

        # Para descripciones cortas (modo listado), remover el número y "de" del principio
        cleaned = re.sub(r'^\d+º?\s*(de\s*)?', '', description, flags=re.IGNORECASE)

        # Limpiar caracteres no válidos para nombres de archivo
        cleaned = re.sub(r'[^\w\s-]', '', cleaned)

        # Reemplazar espacios por guiones bajos
        cleaned = re.sub(r'\s+', '_', cleaned.strip())

        # Formato final: NombreCiudad_Numero
        return f"{cleaned}_{num}" if cleaned else f"boletin_{num}"

    def _update_index_md(self, bulletin: Dict, output_dir: Path, base_url: str):
        """
        Actualiza el archivo boletines.md con la información del boletín procesado
        """
        index_file = output_dir / "boletines.md"

        # Crear archivo si no existe
        if not index_file.exists():
            with index_file.open('w', encoding='utf-8') as f:
                f.write("# Boletines Procesados\n\n")
                f.write("JSON2Markdown Converter = https://memochou1993.github.io/json2markdown-converter/\n\n\n")
                f.write("| Number | Date | Description | Link | Status |\n")
                f.write("|--------|------|-------------|------|--------|\n")

        # Preparar datos
        number = bulletin.get('number', 'N/A')
        date = bulletin.get('date', 'N/A')
        description = bulletin.get('description', 'N/A')
        link = bulletin.get('link', '')
        status = bulletin.get('status', 'unknown')

        # Construir URL completa
        if link:
            full_url = link if link.startswith('http') else f"{base_url}{link}"
        else:
            full_url = 'N/A'

        # Formato de status con emoji
        status_display = {
            'completed': '✅ Completado',
            'skipped': '🤖 Creado',
            'error': '❌ Error',
            'no_content': '⚠️ Sin contenido',
            'unknown': '❓ Desconocido'
        }.get(status, status)

        # Leer archivo existente para verificar si ya existe esta entrada
        with index_file.open('r', encoding='utf-8') as f:
            content = f.read()

        # Crear nueva línea
        new_line = f"| {number} | {date} | {description} | [{full_url}]({full_url}) | {status_display} |\n"

        # Verificar si ya existe una entrada para este boletín
        if f"| {number} |" in content:
            # Reemplazar la línea existente
            lines = content.split('\n')
            updated_lines = []
            for line in lines:
                if line.startswith(f"| {number} |"):
                    updated_lines.append(new_line.rstrip())
                else:
                    updated_lines.append(line)
            content = '\n'.join(updated_lines)

            with index_file.open('w', encoding='utf-8') as f:
                f.write(content)
        else:
            # Agregar nueva línea al final
            with index_file.open('a', encoding='utf-8') as f:
                f.write(new_line)

    def _make_llm_call(self, prompt: str, use_json_mode: bool = True) -> str:
        """Realiza una llamada al LLM con rate limiting"""
        self._wait_for_rate_limit()

        params = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }

        if use_json_mode:
            params["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[red]Error en llamada LLM: {e}[/red]")
            raise

    def fetch_html(self, url: str, max_retries: int = 3) -> str:
        """Obtiene HTML de una URL con reintentos"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    console.print(f"[red]Error al obtener {url}: {e}[/red]")
                    raise
                time.sleep(2 ** attempt)
        return ""

    def parse_listing_page(self, html: str, url: str) -> List[Dict]:
        """Nivel 1: Extrae listado de boletines usando BeautifulSoup (con fallback a LLM)"""
        console.print("[cyan]📋 Nivel 1: Extrayendo listado de boletines...[/cyan]")

        try:
            # Intentar con BeautifulSoup primero (95% de casos)
            soup = BeautifulSoup(html, 'lxml')
            bulletins = []

            # Buscar todos los divs con clase "row bulletin"
            bulletin_divs = soup.find_all('div', class_='row bulletin')

            for bulletin_div in bulletin_divs:
                # Extraer título (número + descripción)
                title_elem = bulletin_div.find('p', class_='bulletin-title')
                title = title_elem.get_text(strip=True) if title_elem else "N/A"

                # Extraer fecha
                date_elem = bulletin_div.find('p', class_='bulletin-date')
                date_text = date_elem.get_text(strip=True) if date_elem else "N/A"
                # Limpiar "Publicado el " del texto
                date = date_text.replace('Publicado el ', '')

                # Extraer enlace
                form_elem = bulletin_div.find('form', class_='button_to')
                link = form_elem.get('action', '') if form_elem else ''

                # Extraer número del título (ej: "105º de Carlos Tejedor" -> "105º")
                number_match = re.search(r'(\d+º)', title)
                number = number_match.group(1) if number_match else title.split()[0]

                bulletins.append({
                    'number': number,
                    'date': date,
                    'description': title,
                    'link': link
                })

            if bulletins:
                console.print(f"[green]✓ Encontrados {len(bulletins)} boletines (BeautifulSoup)[/green]")
                return bulletins
            else:
                raise ValueError("No se encontraron boletines con BeautifulSoup")

        except Exception as e:
            # Fallback a LLM si BeautifulSoup falla
            console.print(f"[yellow]⚠ BeautifulSoup falló ({str(e)[:50]}), usando LLM como fallback[/yellow]")

            prompt = f"""Analiza este HTML de SIBOM. Extrae los boletines dentro de <div class="row bulletin">.
IMPORTANTE: Busca el número, la fecha, una breve descripción y el enlace (href).
Devuelve SOLO un JSON válido (sin texto adicional) con el formato: {{"bulletins": [{{"number": string, "date": string, "description": string, "link": string}}]}}

HTML: {html[:50000]}"""

            response = self._make_llm_call(prompt, use_json_mode=True)
            cleaned = self._extract_json(response)
            data = json.loads(cleaned)

            bulletins = data.get("bulletins", [])
            console.print(f"[green]✓ Encontrados {len(bulletins)} boletines (LLM fallback)[/green]")
            return bulletins

    def detect_total_pages(self, html: str) -> int:
        """
        Detecta el número total de páginas usando BeautifulSoup.
        Extrae el número de la última página del elemento <ul class="pagination">.

        Args:
            html: HTML de la página de listado

        Returns:
            int: Número total de páginas (1 si no hay paginación)
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Buscar el contenedor de paginación
            pagination = soup.find('ul', class_='pagination')

            if not pagination:
                console.print("[dim]No se encontró paginación, asumiendo 1 página[/dim]")
                return 1

            # Buscar el enlace "Última" que contiene el número total de páginas
            # Patrón: <a href="/cities/22?page=14">Última &raquo;</a>
            last_page_link = pagination.find('a', string=lambda text: text and 'Última' in text)

            if last_page_link:
                href = last_page_link.get('href', '')
                # Extraer número de página usando regex
                match = re.search(r'page=(\d+)', href)
                if match:
                    total_pages = int(match.group(1))
                    console.print(f"[green]✓ Detectadas {total_pages} páginas totales[/green]")
                    return total_pages

            # Fallback: buscar todos los enlaces con page= y tomar el máximo
            all_page_links = pagination.find_all('a', href=re.compile(r'page=\d+'))
            if all_page_links:
                page_numbers = []
                for link in all_page_links:
                    href = link.get('href', '')
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_numbers.append(int(match.group(1)))

                if page_numbers:
                    total_pages = max(page_numbers)
                    console.print(f"[yellow]✓ Detectadas {total_pages} páginas (fallback)[/yellow]")
                    return total_pages

            # Si no se encontró nada, asumir 1 página
            console.print("[dim]No se pudo determinar número de páginas, asumiendo 1[/dim]")
            return 1

        except Exception as e:
            console.print(f"[yellow]⚠ Error detectando páginas: {e}, asumiendo 1 página[/yellow]")
            return 1

    def parse_bulletin_content_links(self, html: str) -> List[str]:
        """Nivel 2: Extrae enlaces de contenido específico usando BeautifulSoup (con fallback a LLM)"""
        console.print("[cyan]🔗 Nivel 2: Extrayendo enlaces de contenido...[/cyan]")

        try:
            # Intentar con BeautifulSoup primero (95% de casos)
            soup = BeautifulSoup(html, 'lxml')

            # Buscar todos los enlaces con clase "content-link"
            content_links = soup.find_all('a', class_='content-link')

            # Extraer los atributos href
            links = [link.get('href', '') for link in content_links if link.get('href')]

            if links:
                console.print(f"[green]✓ Encontrados {len(links)} enlaces de contenido (BeautifulSoup)[/green]")
                return links
            else:
                raise ValueError("No se encontraron enlaces con BeautifulSoup")

        except Exception as e:
            # Fallback a LLM si BeautifulSoup falla
            console.print(f"[yellow]⚠ BeautifulSoup falló ({str(e)[:50]}), usando LLM como fallback[/yellow]")

            prompt = f"""Eres un experto en scraping. En este HTML de un boletín oficial, identifica TODOS los enlaces que llevan a contenidos específicos (ordenanzas, decretos, edictos).
Suelen tener la clase "content-link" o estar dentro de una lista de sumario.
Extrae exclusivamente los atributos 'href'.
Devuelve SOLO un JSON válido (sin texto adicional) con el formato: {{"links": ["url1", "url2", ...]}}

HTML: {html[:80000]}"""

            try:
                response = self._make_llm_call(prompt, use_json_mode=True)
                cleaned = self._extract_json(response)

                # Intentar parsear JSON
                data = json.loads(cleaned)
                links = data.get("links", [])
                console.print(f"[green]✓ Encontrados {len(links)} enlaces de contenido (LLM fallback)[/green]")
            except json.JSONDecodeError as e:
                console.print(f"[red]⚠ Error parseando JSON del LLM: {e}[/red]")
                console.print(f"[dim]Respuesta recibida (primeros 500 chars):[/dim]")
                console.print(f"[dim]{response[:500]}...[/dim]")

                # Intentar extraer manualmente el primer objeto JSON válido
                try:
                    # Buscar el primer { hasta el primer }
                    start = response.find('{')
                    if start != -1:
                        count = 0
                        for i, char in enumerate(response[start:], start):
                            if char == '{':
                                count += 1
                            elif char == '}':
                                count -= 1
                                if count == 0:
                                    first_json = response[start:i+1]
                                    data = json.loads(first_json)
                                    links = data.get("links", [])
                                    console.print(f"[yellow]✓ Recuperado {len(links)} enlaces (usando fallback JSON)[/yellow]")
                                    break
                    else:
                        raise ValueError("No se encontró objeto JSON en la respuesta")
                except Exception as fallback_error:
                    console.print(f"[red]✗ Fallback también falló: {fallback_error}[/red]")
                    links = []
            return links

    def parse_final_content(self, html: str) -> str:
        """Nivel 3: Extrae texto completo del documento usando BeautifulSoup (con fallback a LLM)"""
        console.print("[cyan]📄 Nivel 3: Extrayendo contenido textual...[/cyan]")

        try:
            # Intentar con BeautifulSoup primero (95% de casos)
            soup = BeautifulSoup(html, 'lxml')

            # Buscar el contenedor principal con id="frontend-container"
            container = soup.find('div', id='frontend-container')

            if container:
                # Extraer texto limpio, preservando saltos de línea
                text = container.get_text(separator='\n', strip=True)

                # Limpiar múltiples saltos de línea consecutivos
                text = re.sub(r'\n{3,}', '\n\n', text)

                console.print(f"[green]✓ Texto extraído: {len(text)} caracteres (BeautifulSoup)[/green]")
                return text
            else:
                raise ValueError("No se encontró el contenedor principal")

        except Exception as e:
            # Fallback a LLM si BeautifulSoup falla
            console.print(f"[yellow]⚠ BeautifulSoup falló ({str(e)[:50]}), usando LLM como fallback[/yellow]")

            prompt = f"""Extrae el contenido textual íntegro de este documento legal.
Céntrate en lo que está dentro de id="frontend-container" o la sección principal de texto.
Mantén el formato de los artículos y el rigor legal. Omite cabeceras de navegación y pies de página.

HTML: {html[:100000]}"""

            response = self._make_llm_call(prompt, use_json_mode=False)

            console.print(f"[green]✓ Texto extraído: {len(response)} caracteres (LLM fallback)[/green]")
            return response

    def process_bulletin(self, bulletin: Dict, base_url: str, output_dir: Path, skip_existing: bool = False) -> Dict:
        """Procesa un boletín completo (niveles 2 y 3) y guarda archivo individual"""
        try:
            # Verificar si el archivo ya existe
            filename = self._sanitize_filename(
                bulletin.get('description', bulletin['number']),
                number=bulletin.get('number')
            )
            filepath = output_dir / f"{filename}.json"

            if filepath.exists():
                if skip_existing:
                    console.print(f"[yellow]⏭ Saltando boletín {bulletin['number']} (ya existe)[/yellow]")
                    # Leer el archivo existente
                    with filepath.open('r', encoding='utf-8') as f:
                        existing_data = json.load(f)

                    # Actualizar índice con status "skipped" solo si no está en el índice
                    # o si el status actual no es completed
                    if existing_data.get('status') != 'error':
                        update_data = {**existing_data, 'status': 'skipped'}
                        self._update_index_md(update_data, output_dir, base_url)

                    return existing_data
                else:
                    console.print(f"\n[yellow]⚠ El archivo {filepath.name} ya existe[/yellow]")
                    console.print(f"\n¿Qué deseas hacer con el boletín [bold]{bulletin['number']}[/bold]?")
                    console.print("  [cyan]1.[/cyan] Saltar y continuar con el siguiente")
                    console.print("  [cyan]2.[/cyan] Sobreescribir este boletín")
                    console.print("  [cyan]3.[/cyan] Cancelar todo el proceso")

                    try:
                        choice = input("\nElige una opción (1-3) [1]: ").strip() or "1"

                        if choice == "3":
                            console.print(f"[red]✗ Proceso cancelado por el usuario[/red]")
                            sys.exit(0)
                        elif choice == "1":
                            console.print(f"[yellow]⏭ Saltando boletín {bulletin['number']}[/yellow]\n")

                            # Leer archivo existente
                            with filepath.open('r', encoding='utf-8') as f:
                                existing_data = json.load(f)

                            # Actualizar índice con status "skipped"
                            if existing_data.get('status') != 'error':
                                update_data = {**existing_data, 'status': 'skipped'}
                                self._update_index_md(update_data, output_dir, base_url)

                            return existing_data
                        elif choice == "2":
                            console.print(f"[cyan]♻️ Sobreescribiendo {filepath.name}...[/cyan]\n")
                        else:
                            console.print(f"[yellow]⚠ Opción inválida, saltando...[/yellow]\n")

                            # Leer archivo existente
                            with filepath.open('r', encoding='utf-8') as f:
                                existing_data = json.load(f)

                            # Actualizar índice con status "skipped"
                            if existing_data.get('status') != 'error':
                                update_data = {**existing_data, 'status': 'skipped'}
                                self._update_index_md(update_data, output_dir, base_url)

                            return existing_data
                    except KeyboardInterrupt:
                        console.print(f"\n[red]✗ Proceso cancelado por el usuario[/red]")
                        sys.exit(0)

            console.print(f"\n[bold cyan]📰 Procesando boletín: {bulletin['number']}[/bold cyan]")

            # Nivel 2: Obtener enlaces
            bulletin_url = bulletin['link'] if bulletin['link'].startswith('http') else f"{base_url}{bulletin['link']}"
            bulletin_html = self.fetch_html(bulletin_url)
            content_links = self.parse_bulletin_content_links(bulletin_html)

            if not content_links:
                console.print(f"[yellow]⚠ Sin enlaces de contenido en {bulletin['number']}[/yellow]")
                no_content_result = {**bulletin, "status": "no_content", "fullText": ""}

                # Actualizar índice markdown
                self._update_index_md(no_content_result, output_dir, base_url)

                return no_content_result

            # Nivel 3: Extraer texto de cada documento
            full_text = ""
            for i, link in enumerate(content_links, 1):
                console.print(f"[dim]  → Documento {i}/{len(content_links)}[/dim]")
                doc_url = link if link.startswith('http') else f"{base_url}{link}"
                doc_html = self.fetch_html(doc_url)
                doc_text = self.parse_final_content(doc_html)
                full_text += f"\n[DOC {i}]\n{doc_text}\n"

            result = {**bulletin, "status": "completed", "fullText": full_text}

            # Guardar archivo individual
            filename = self._sanitize_filename(bulletin.get('description', bulletin['number']))
            filepath = output_dir / f"{filename}.json"

            with filepath.open('w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # Actualizar índice markdown
            self._update_index_md(result, output_dir, base_url)

            console.print(f"[bold green]✓ Boletín {bulletin['number']} completado → {filepath.name}[/bold green]")
            return result

        except Exception as e:
            console.print(f"[bold red]✗ Error en boletín {bulletin['number']}: {e}[/bold red]")
            error_result = {**bulletin, "status": "error", "fullText": "", "error": str(e)}

            # Actualizar índice markdown incluso en caso de error
            self._update_index_md(error_result, output_dir, base_url)

            return error_result

    def scrape(self, target_url: str, limit: Optional[int] = None, parallel: int = 1, skip_existing: bool = False) -> List[Dict]:
        """
        Scraping principal

        Args:
            target_url: URL de la página de listado O de un boletín individual
            limit: Número máximo de boletines a procesar (None = todos)
            parallel: Número de boletines a procesar en paralelo
        """
        # Detectar si es URL de boletín individual o listado de ciudad
        is_bulletin_url = '/bulletins/' in target_url

        console.print(Panel.fit(
            f"[bold cyan]SIBOM Scraper[/bold cyan]\n"
            f"Modo: {'🎯 Boletín Individual' if is_bulletin_url else '📋 Listado'}\n"
            f"URL: {target_url}\n"
            f"Modelo: {self.model}\n"
            f"Límite: {limit or 'sin límite'}\n"
            f"Paralelismo: {parallel}",
            title="🚀 Iniciando"
        ))

        if is_bulletin_url:
            # Modo boletín individual
            console.print("\n[bold cyan]🎯 Modo: Boletín Individual[/bold cyan]")

            # Extraer número del boletín de la URL
            bulletin_id = target_url.split('/bulletins/')[-1].split('?')[0].split('#')[0]
            console.print(f"[dim]Obteniendo metadatos del boletín {bulletin_id}...[/dim]")

            # Obtener metadatos reales del boletín
            try:
                bulletin_html = self.fetch_html(target_url)

                # Extraer metadatos del HTML usando LLM
                metadata_prompt = f"""Extrae los metadatos de este boletín oficial.
Busca el número del boletín (ej: "105º", "Boletín 98º"), la fecha de publicación, y una descripción breve.
Devuelve SOLO un JSON válido con el formato: {{"number": string, "date": string, "description": string}}

HTML: {bulletin_html[:50000]}"""

                response = self._make_llm_call(metadata_prompt, use_json_mode=True)
                cleaned = self._extract_json(response)
                metadata = json.loads(cleaned)

                # Crear objeto bulletin con metadatos reales
                bulletins = [{
                    "number": metadata.get("number", f"#{bulletin_id}"),
                    "date": metadata.get("date", "N/A"),
                    "description": metadata.get("description", f"Boletín {bulletin_id}"),
                    "link": f"/bulletins/{bulletin_id}"
                }]

                console.print(f"[green]✓ Boletín: {bulletins[0]['number']} - {bulletins[0]['description']}[/green]")

            except Exception as e:
                console.print(f"[yellow]⚠ No se pudieron obtener metadatos: {e}[/yellow]")
                console.print(f"[yellow]  Usando valores por defecto...[/yellow]")

                # Fallback a valores genéricos
                bulletins = [{
                    "number": f"#{bulletin_id}",
                    "date": "N/A",
                    "description": f"Boletín {bulletin_id}",
                    "link": f"/bulletins/{bulletin_id}"
                }]
        else:
            # Modo listado con detección automática de paginación
            console.print("\n[bold]═══ NIVEL 1: LISTADO ═══[/bold]")

            # Detectar si la URL ya tiene parámetro ?page=
            has_page_param = 'page=' in target_url

            if has_page_param:
                # Modo página única: procesar solo la página especificada
                console.print("[cyan]🎯 Modo: Página única (parámetro ?page= detectado)[/cyan]")
                list_html = self.fetch_html(target_url)
                bulletins = self.parse_listing_page(list_html, target_url)
            else:
                # Modo automático: detectar y procesar todas las páginas
                console.print("[cyan]🔄 Modo: Detección automática de paginación[/cyan]")

                # Obtener primera página para detectar total de páginas
                list_html = self.fetch_html(target_url)
                total_pages = self.detect_total_pages(list_html)

                # Extraer boletines de la primera página
                bulletins = self.parse_listing_page(list_html, target_url)
                console.print(f"[dim]  Página 1/{total_pages}: {len(bulletins)} boletines[/dim]")

                # Procesar páginas restantes
                if total_pages > 1:
                    # Construir URL base (remover cualquier parámetro existente)
                    base_url_parsed = target_url.split('?')[0]

                    for page_num in range(2, total_pages + 1):
                        try:
                            page_url = f"{base_url_parsed}?page={page_num}"
                            console.print(f"[cyan]📄 Página {page_num}/{total_pages}...[/cyan]")

                            page_html = self.fetch_html(page_url)
                            page_bulletins = self.parse_listing_page(page_html, page_url)

                            bulletins.extend(page_bulletins)
                            console.print(f"[dim]  Página {page_num}/{total_pages}: {len(page_bulletins)} boletines (total acumulado: {len(bulletins)})[/dim]")
                        except Exception as e:
                            console.print(f"[red]✗ Error en página {page_num}: {e}[/red]")
                            console.print(f"[yellow]⚠ Continuando con las páginas restantes...[/yellow]")
                            continue

                    console.print(f"\n[bold green]✓ Total: {len(bulletins)} boletines de {total_pages} páginas[/bold green]")

        # Aplicar límite DESPUÉS de recolectar todos los boletines
        if limit:
            original_count = len(bulletins)
            bulletins = bulletins[:limit]
            console.print(f"[yellow]⚙ Limitando de {original_count} a {limit} boletines[/yellow]")

        # Crear carpeta de salida
        output_dir = Path("boletines")
        output_dir.mkdir(exist_ok=True)
        console.print(f"[cyan]📁 Carpeta de salida: {output_dir.absolute()}[/cyan]")

        # Procesar boletines
        console.print(f"\n[bold]═══ NIVELES 2 y 3: PROCESANDO {len(bulletins)} BOLETINES ═══[/bold]")

        base_url = "https://sibom.slyt.gba.gob.ar"
        results = []

        if parallel > 1:
            # Procesamiento paralelo
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = {executor.submit(self.process_bulletin, b, base_url, output_dir, skip_existing): b for b in bulletins}

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(f"[cyan]Procesando...", total=len(bulletins))

                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        progress.update(task, advance=1)
        else:
            # Procesamiento secuencial
            for i, bulletin in enumerate(bulletins, 1):
                console.print(f"\n[dim]→ Procesando {i}/{len(bulletins)}: {bulletin['number']}[/dim]")
                result = self.process_bulletin(bulletin, base_url, output_dir, skip_existing)
                results.append(result)
                console.print(f"[dim]→ Resultado agregado. Total acumulado: {len(results)}[/dim]")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="SIBOM Scraper - Extrae boletines oficiales",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s --url https://sibom.slyt.gba.gob.ar/cities/22 --limit 5
  %(prog)s --url https://sibom.slyt.gba.gob.ar/cities/22 --parallel 3
  %(prog)s --url https://sibom.slyt.gba.gob.ar/cities/22 --output resultados.json
        """
    )

    parser.add_argument(
        '--url',
        default='https://sibom.slyt.gba.gob.ar/cities/22',
        help='URL de la página de listado de SIBOM (default: Merlo)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Número máximo de boletines a procesar (default: todos)'
    )

    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Número de boletines a procesar en paralelo (default: 1)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='sibom_results.json',
        help='Archivo de salida JSON (default: sibom_results.json)'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='OpenRouter API key (si no se provee, usa OPENROUTER_API_KEY del .env)'
    )

    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Saltar automáticamente boletines que ya fueron procesados (no preguntar)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='google/gemini-3-flash-preview',
        help='Modelo de OpenRouter a usar (default: google/gemini-3-flash-preview)'
    )

    args = parser.parse_args()

    # Obtener API key
    api_key = args.api_key or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        console.print("[bold red]Error: No se encontró OPENROUTER_API_KEY[/bold red]")
        console.print("Usa --api-key o configura la variable en .env")
        sys.exit(1)

    # Crear scraper y ejecutar
    scraper = SIBOMScraper(api_key, model=args.model)

    try:
        start_time = time.time()
        results = scraper.scrape(args.url, limit=args.limit, parallel=args.parallel, skip_existing=args.skip_existing)
        elapsed = time.time() - start_time

        # Guardar resumen consolidado (opcional)
        output_path = Path(args.output)
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Mostrar resumen
        completed = sum(1 for r in results if r.get('status') == 'completed')
        errors = sum(1 for r in results if r.get('status') == 'error')
        no_content = sum(1 for r in results if r.get('status') == 'no_content')

        table = Table(title="📊 Resumen de Ejecución")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="green")

        table.add_row("Total procesados", str(len(results)))
        table.add_row("Completados", str(completed))
        table.add_row("Errores", str(errors))
        table.add_row("Sin contenido", str(no_content))
        table.add_row("Tiempo total", f"{elapsed:.1f}s")
        table.add_row("Tiempo por boletín", f"{elapsed/len(results):.1f}s" if len(results) > 0 else "N/A")
        table.add_row("Carpeta boletines", "boletines/")
        table.add_row("Resumen consolidado", str(output_path))

        console.print("\n")
        console.print(table)
        console.print(f"\n[bold green]✓ Boletines individuales guardados en: boletines/[/bold green]")
        console.print(f"[bold green]✓ Resumen consolidado guardado en: {output_path}[/bold green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Proceso interrumpido por el usuario[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error fatal: {e}[/bold red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
