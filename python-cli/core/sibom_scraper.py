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
import random
import platform
import subprocess
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
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

# Importar módulos de extracción (ahora en extractors/)
from extractors.table_extractor import TableExtractor
from extractors.monto_extractor import MontoExtractor
from extractors.normativas_extractor import extract_normativas_from_bulletin, save_index, save_minimal_index, Normativa

# Cargar variables de entorno
load_dotenv()

console = Console()


class SIBOMScraper:
    # Mapeo de IDs de ciudades a nombres (fallback)
    CITY_MAP_FALLBACK = {
        '22': 'Merlo',
        '23': 'Carlos Tejedor',
        '24': 'La Plata',
        '25': 'San Isidro',
        '26': 'Vicente López',
        '27': 'Tigre',
        '28': 'San Fernando',
        '29': 'Morón',
        '30': 'Tres de Febrero',
        # Agregar más ciudades según sea necesario
    }

    CITY_MAP_FILE = Path("boletines/CITY_MAP.json")

    def _load_city_map(self) -> Dict[str, str]:
        """
        Carga el mapa de ciudades desde CITY_MAP.json.

        Returns:
            Dict con el mapeo de IDs a nombres
        """
        if self.CITY_MAP_FILE.exists():
            try:
                with self.CITY_MAP_FILE.open('r', encoding='utf-8') as f:
                    city_map = json.load(f)
                console.print(
                    f"[dim]  ✓ CITY_MAP cargado: {len(city_map)} ciudades[/dim]")
                return city_map
            except Exception as e:
                console.print(
                    f"[yellow]  ⚠ Error cargando CITY_MAP: {e}[/yellow]")

        # Fallback al mapa interno
        console.print(
            f"[dim]  ✓ Usando CITY_MAP_FALLBACK: {len(self.CITY_MAP_FALLBACK)} ciudades[/dim]")
        return self.CITY_MAP_FALLBACK.copy()

    def get_city_name(self, city_id: str, city_url: str = None) -> str:
        """
        Obtiene el nombre de una ciudad usando CITY_MAP.json.

        Args:
            city_id: ID de la ciudad
            city_url: URL de la ciudad (no usado, se mantiene por compatibilidad)

        Returns:
            Nombre de la ciudad o "Ciudad ID {id}" si no se puede obtener
        """
        # Cargar CITY_MAP desde archivo
        city_map = self._load_city_map()

        # Buscar en CITY_MAP
        name = city_map.get(city_id)
        if name:
            return name

        # Fallback
        return f"Ciudad ID {city_id}"

    def __init__(self, api_key: str, model: str = "z-ai/glm-4.5-air:free"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = model
        self.rate_limit_delay = 3  # segundos entre llamadas (base)
        self.jitter_range = 1.0  # +/- 1 segundo de variación aleatoria
        self.last_call_time = 0

        # User-Agent para simular navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Inicializar extractor de tablas
        self.table_extractor = TableExtractor()
        # Inicializar extractor de montos
        self.monto_extractor = MontoExtractor()
        # Almacén de montos extraídos durante el scraping
        self.montos_acumulados = []
        # Almacén de normativas extraídas durante el scraping
        self.normativas_acumuladas: List[Normativa] = []

    def _play_sound(self, sound_type: str = 'success'):
        """
        Reproduce un sonido del sistema según el tipo.

        Args:
            sound_type: 'success' para boletín completado, 'complete' para tarea finalizada
        """
        try:
            system = platform.system()

            if system == 'Darwin':  # macOS
                if sound_type == 'success':
                    # Sonido Hero para cada boletín completado
                    subprocess.run(['afplay', '/System/Library/Sounds/Hero.aiff'],
                                   check=False, capture_output=True)
                elif sound_type == 'complete':
                    # Sonido Funk para tarea completa
                    subprocess.run(['afplay', '/System/Library/Sounds/Funk.aiff'],
                                   check=False, capture_output=True)
            elif system == 'Linux':
                # Usar beep en Linux (requiere beep instalado)
                if sound_type == 'success':
                    subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/message.oga'],
                                   check=False, capture_output=True)
                elif sound_type == 'complete':
                    subprocess.run(['paplay', '/usr/share/sounds/freedesktop/stereo/complete.oga'],
                                   check=False, capture_output=True)
            elif system == 'Windows':
                # Usar winsound en Windows
                import winsound
                if sound_type == 'success':
                    winsound.MessageBeep(winsound.MB_OK)
                elif sound_type == 'complete':
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            # Silenciosamente ignorar errores de sonido
            pass

    def _get_progress_file(self, bulletin_id: str, output_dir: Path) -> Path:
        """Retorna path del archivo de progreso para un boletín"""
        return output_dir / f".progress_{bulletin_id}.json"

    def _save_progress(self, bulletin_id: str, output_dir: Path,
                       normas_procesadas: List[str], normas_pendientes: List[str]):
        """Guarda progreso incremental del scraping de un boletín"""
        progress_file = self._get_progress_file(bulletin_id, output_dir)

        progress_data = {
            "bulletin_id": bulletin_id,
            "timestamp": time.time(),
            "normas_procesadas": normas_procesadas,
            "normas_pendientes": normas_pendientes,
            "total": len(normas_procesadas) + len(normas_pendientes),
            "completed": len(normas_procesadas)
        }

        try:
            with progress_file.open('w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(
                f"[yellow]⚠ No se pudo guardar progreso: {e}[/yellow]")

    def _load_progress(self, bulletin_id: str, output_dir: Path) -> Optional[Dict]:
        """Carga progreso existente de un boletín"""
        progress_file = self._get_progress_file(bulletin_id, output_dir)

        if not progress_file.exists():
            return None

        try:
            with progress_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(
                f"[yellow]⚠ No se pudo cargar progreso: {e}[/yellow]")
            return None

    def _clean_progress(self, bulletin_id: str, output_dir: Path):
        """Elimina archivo de progreso una vez completado el boletín"""
        progress_file = self._get_progress_file(bulletin_id, output_dir)

        if progress_file.exists():
            try:
                progress_file.unlink()
            except Exception as e:
                console.print(
                    f"[dim]No se pudo eliminar archivo de progreso: {e}[/dim]")

    def _detect_document_types(self, text: str) -> List[str]:
        """
        Detecta tipos de documentos presentes en el texto de un boletín.
        Busca patrones como "ORDENANZA Nº", "DECRETO Nº", etc.
        """
        if not text:
            return []

        types_found = []
        patterns = {
            'ordenanza': r'\bORDENANZA\s+N[º°]\s*\d+',
            'decreto': r'\bDECRETO\s+N[º°]\s*\d+',
            'resolucion': r'\bRESOLUCI[ÓO]N\s+N[º°]\s*\d+',
            'disposicion': r'\bDISPOSICI[ÓO]N\s+N[º°]\s*\d+',
            'convenio': r'\bCONVENIO\s+(?:INTERINSTITUCIONAL|DE\s+(?:ADHESI[ÓO]N|COLABORACI[ÓO]N))',
            'licitacion': r'\bLICITACI[ÓO]N\s+(?:P[ÚU]BLICA|PRIVADA)',
            'edicto': r'\bEDITO\s+N[º°]\s*\d+',
        }

        text_upper = text.upper()
        for doc_type, pattern in patterns.items():
            if re.search(pattern, text_upper):
                if doc_type not in types_found:
                    types_found.append(doc_type)

        return types_found

    def _wait_for_rate_limit(self):
        """Espera según rate limiting con jitter aleatorio para evitar patrón detecta"""
        elapsed = time.time() - self.last_call_time

        # Agregar jitter aleatorio: delay base +/- variación aleatoria
        jitter = random.uniform(-self.jitter_range, self.jitter_range)
        actual_delay = max(1.0, self.rate_limit_delay +
                           jitter)  # Mínimo 1 segundo

        if elapsed < actual_delay:
            time.sleep(actual_delay - elapsed)

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

    def _extract_municipality_name(self, description: str) -> str:
        """
        Extrae el nombre del municipio de la descripción del boletín.
        Ejemplo: "105º de Carlos Tejedor" -> "Carlos Tejedor"
        Ejemplo: "Boletín Oficial Municipal de Carlos Tejedor..." -> "Carlos Tejedor"
        """
        # Buscar patrón "de [Ciudad]" o "Municipal de [Ciudad]" o "Municipalidad de [Ciudad]"
        patterns = [
            r'(?:de\s+la\s+Municipalidad\s+de\s+)([A-ZÁÉÍÓÚa-záéíóúñÑ][a-zA-ZÁÉÍÓÚáéíóúñÑ\s]+?)(?:\s+que|\s*$|,)',
            r'(?:Municipal\s+de\s+)([A-ZÁÉÍÓÚa-záéíóúñÑ][a-zA-ZÁÉÍÓÚáéíóúñÑ\s]+?)(?:\s+que|\s*$|,)',
            r'(?:de\s+)([A-ZÁÉÍÓÚa-záéíóúñÑ][a-zA-ZÁÉÍÓÚáéíóúñÑ\s]+?)(?:\s*$)',
            r'\d+º?\s+de\s+([A-ZÁÉÍÓÚa-záéíóúñÑ][a-zA-ZÁÉÍÓÚáéíóúñÑ\s]+?)(?:\s*$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: usar la descripción limpia
        cleaned = re.sub(r'^\d+º?\s*', '', description)
        cleaned = re.sub(r'^de\s+', '', cleaned, flags=re.IGNORECASE)
        return cleaned.strip() or 'Desconocido'

    def _get_city_name_from_url(self, url: str) -> Optional[str]:
        """
        Extrae el nombre de la ciudad desde la URL usando el mapeo CITY_MAP.
        Ejemplo: "https://sibom.slyt.gba.gob.ar/cities/22" -> "Merlo"
        """
        # Buscar patrón /cities/[ID]
        match = re.search(r'/cities/(\d+)', url)
        if match:
            city_id = match.group(1)
            return self.CITY_MAP.get(city_id)
        return None

    def _get_city_name_from_url(self, url: str) -> Optional[str]:
        """
        Extrae el nombre de la ciudad desde la URL usando el mapeo CITY_MAP.json.

        Args:
            url: URL de la ciudad

        Returns:
            Nombre de la ciudad o None si no se puede obtener
        """
        # Buscar patrón en la URL
        match = re.search(r'/cities/(\d+)', url)
        if match:
            city_id = match.group(1)
            city_map = self._load_city_map()
            return city_map.get(city_id)
        return None

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
            city_match = re.search(
                r'(?:de\s+la\s+Municipalidad\s+de\s+|Municipal\s+de\s+|de\s+)([A-Z][a-zA-Z\s]+?)(?:\s+que|\s*$|,)', description)
            if city_match:
                cleaned = city_match.group(1).strip()
                cleaned = re.sub(r'[^\w\s-]', '', cleaned)
                cleaned = re.sub(r'\s+', '_', cleaned.strip())
                return f"{cleaned}_{num}"

        # Para descripciones cortas (modo listado), remover el número y "de" del principio
        cleaned = re.sub(r'^\d+º?\s*(de\s*)?', '',
                         description, flags=re.IGNORECASE)

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
                f.write(
                    "JSON2Markdown Converter = https://memochou1993.github.io/json2markdown-converter/\n\n\n")
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
        """Realiza una llamada al LLM con rate limiting y tracking"""
        self._wait_for_rate_limit()

        params = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }

        if use_json_mode:
            params["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content

            # Registrar en LLM tracker
            try:
                from utils.llm_tracker import extract_token_usage, record_llm_call
                input_tokens, output_tokens = extract_token_usage(response)

                if input_tokens > 0 or output_tokens > 0:
                    record_llm_call(
                        model=self.model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        task="sibom_parsing"
                    )
            except Exception:
                # No fallar si el tracker falla
                pass

            return content
        except Exception as e:
            console.print(f"[red]Error en llamada LLM: {e}[/red]")
            raise

    def fetch_html(self, url: str, max_retries: int = 3) -> str:
        """Obtiene HTML de una URL con reintentos y User-Agent real"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
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
        console.print(
            "[cyan]📋 Nivel 1: Extrayendo listado de boletines...[/cyan]")

        try:
            # Intentar con BeautifulSoup primero (95% de casos)
            soup = BeautifulSoup(html, 'lxml')
            bulletins = []

            # Buscar todos los divs con clase "row bulletin"
            bulletin_divs = soup.find_all('div', class_='row bulletin')

            for bulletin_div in bulletin_divs:
                # Extraer título (número + descripción)
                title_elem = bulletin_div.find('p', class_='bulletin-title')
                title = title_elem.get_text(
                    strip=True) if title_elem else "N/A"

                # Extraer fecha
                date_elem = bulletin_div.find('p', class_='bulletin-date')
                date_text = date_elem.get_text(
                    strip=True) if date_elem else "N/A"
                # Limpiar "Publicado el " del texto
                date = date_text.replace('Publicado el ', '')

                # Extraer enlace
                form_elem = bulletin_div.find('form', class_='button_to')
                link = form_elem.get('action', '') if form_elem else ''

                # Extraer número del título (ej: "105º de Carlos Tejedor" -> "105º")
                number_match = re.search(r'(\d+º)', title)
                number = number_match.group(
                    1) if number_match else title.split()[0]

                bulletins.append({
                    'number': number,
                    'date': date,
                    'description': title,
                    'link': link
                })

            if bulletins:
                console.print(
                    f"[green]✓ Encontrados {len(bulletins)} boletines (BeautifulSoup)[/green]")
                return bulletins
            else:
                raise ValueError(
                    "No se encontraron boletines con BeautifulSoup")

        except Exception as e:
            # Fallback a LLM si BeautifulSoup falla
            console.print(
                f"[yellow]⚠ BeautifulSoup falló ({str(e)[:50]}), usando LLM como fallback[/yellow]")

            prompt = f"""Analiza este HTML de SIBOM. Extrae los boletines dentro de <div class="row bulletin">.
IMPORTANTE: Busca el número, la fecha, una breve descripción y el enlace (href).
Devuelve SOLO un JSON válido (sin texto adicional) con el formato: {{"bulletins": [{{"number": string, "date": string, "description": string, "link": string}}]}}

HTML: {html[:200000]}"""

            response = self._make_llm_call(prompt, use_json_mode=True)
            cleaned = self._extract_json(response)
            data = json.loads(cleaned)

            bulletins = data.get("bulletins", [])
            console.print(
                f"[green]✓ Encontrados {len(bulletins)} boletines (LLM fallback)[/green]")
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
                console.print(
                    "[dim]No se encontró paginación, asumiendo 1 página[/dim]")
                return 1

            # Buscar el enlace "Última" que contiene el número total de páginas
            # Patrón: <a href="/cities/22?page=14">Última &raquo;</a>
            last_page_link = pagination.find(
                'a', string=lambda text: text and 'Última' in text)

            if last_page_link:
                href = last_page_link.get('href', '')
                # Extraer número de página usando regex
                match = re.search(r'page=(\d+)', href)
                if match:
                    total_pages = int(match.group(1))
                    console.print(
                        f"[green]✓ Detectadas {total_pages} páginas totales[/green]")
                    return total_pages

            # Fallback: buscar todos los enlaces con page= y tomar el máximo
            all_page_links = pagination.find_all(
                'a', href=re.compile(r'page=\d+'))
            if all_page_links:
                page_numbers = []
                for link in all_page_links:
                    href = link.get('href', '')
                    match = re.search(r'page=(\d+)', href)
                    if match:
                        page_numbers.append(int(match.group(1)))

                if page_numbers:
                    total_pages = max(page_numbers)
                    console.print(
                        f"[yellow]✓ Detectadas {total_pages} páginas (fallback)[/yellow]")
                    return total_pages

            # Si no se encontró nada, asumir 1 página
            console.print(
                "[dim]No se pudo determinar número de páginas, asumiendo 1[/dim]")
            return 1

        except Exception as e:
            console.print(
                f"[yellow]⚠ Error detectando páginas: {e}, asumiendo 1 página[/yellow]")
            return 1

    def parse_bulletin_content_links(self, html: str) -> List[Dict[str, Any]]:
        """
        Nivel 2: Extrae enlaces de contenido con metadatos completos.

        Retorna lista de dicts con:
        - url: URL de la norma individual
        - tipo: ordenanza/decreto/resolución (de clase CSS)
        - titulo: Título extraído del HTML
        - fecha: Fecha de la norma
        - preview: Preview del contenido (si disponible)
        - id: ID numérico de la norma (extraído de URL)
        """
        console.print(
            "[cyan]🔗 Nivel 2: Extrayendo metadatos de normas...[/cyan]")

        try:
            # Intentar con BeautifulSoup primero (95% de casos)
            soup = BeautifulSoup(html, 'lxml')

            # Buscar todos los enlaces con clase "content-link"
            content_links = soup.find_all('a', class_='content-link')

            normas = []
            for link_elem in content_links:
                url = link_elem.get('href', '')
                if not url:
                    continue

                # Extraer ID de la URL (/bulletins/1636/contents/1270278 -> 1270278)
                norm_id = url.split('/')[-1] if '/' in url else 'unknown'

                # Buscar el div interno con la clase que indica el tipo
                div = link_elem.find('div', class_='white-box')
                if not div:
                    continue

                # Extraer tipo de norma de las clases CSS
                clases = div.get('class', [])
                tipo_raw = [c for c in clases if c != 'white-box']
                tipo = tipo_raw[0] if tipo_raw else 'norma'

                # Mapeo de clases CSS a tipos legibles
                tipo_map = {
                    'ordinance': 'ordenanza',
                    'decree': 'decreto',
                    'resolution': 'resolución',
                    'disposition': 'disposición',
                    'edict': 'edicto'
                }
                tipo = tipo_map.get(tipo, tipo)

                # Extraer título (primer párrafo)
                title_elem = div.find('p')
                titulo = title_elem.get_text(
                    strip=True) if title_elem else f"{tipo.capitalize()} {norm_id}"

                # Extraer fecha (párrafo con clase city-and-date)
                date_elem = div.find('p', class_='city-and-date')
                fecha = date_elem.get_text(strip=True) if date_elem else ''

                # Extraer preview (siguiente párrafo después de título)
                all_p = div.find_all('p', limit=5)
                preview_parts = [p.get_text(strip=True)
                                 for p in all_p[2:4] if p.get_text(strip=True)]
                preview = ' '.join(preview_parts)[
                    :200] if preview_parts else ''

                normas.append({
                    'id': norm_id,
                    'url': url,
                    'tipo': tipo,
                    'titulo': titulo,
                    'fecha': fecha,
                    'preview': preview
                })

            if normas:
                console.print(
                    f"[green]✓ Encontradas {len(normas)} normas con metadatos (BeautifulSoup)[/green]")
                return normas
            else:
                raise ValueError("No se encontraron normas con BeautifulSoup")

        except Exception as e:
            # Fallback a LLM si BeautifulSoup falla
            console.print(
                f"[yellow]⚠ BeautifulSoup falló ({str(e)[:50]}), usando LLM como fallback[/yellow]")

            # Por ahora, retornar lista vacía en vez de usar LLM (muy costoso y lento para fallback)
            console.print(
                f"[red]✗ No se pudieron extraer normas del boletín[/red]")
            return []

    def parse_final_content(self, html: str) -> str:
        """Nivel 3: Extrae texto completo del documento usando BeautifulSoup mejorado (sin LLM)"""
        console.print(
            "[cyan]📄 Nivel 3: Extrayendo contenido textual...[/cyan]")

        # Validación inicial del HTML
        if not html or len(html) < 100:
            raise ValueError(
                f"HTML inválido o demasiado corto ({len(html) if html else 0} caracteres)")

        html_size = len(html)
        console.print(
            f"[dim]  → HTML recibido: {html_size:,} caracteres[/dim]")

        soup = BeautifulSoup(html, 'lxml')

        # Estrategia 1: Buscar contenedor principal por ID
        container = soup.find('div', id='frontend-container')
        strategy_used = "ID #frontend-container"

        if not container:
            # Estrategia 2: Buscar contenedor por clase que contenga 'content'
            container = soup.find(
                'div', class_=lambda x: x and 'content' in str(x).lower())
            strategy_used = "clase con 'content'"

        if not container:
            # Estrategia 3: Buscar elementos semánticos main o article
            container = soup.find('main') or soup.find('article')
            strategy_used = "elemento <main> o <article>"

        if not container:
            # Estrategia 4: Usar body pero excluir elementos no deseados
            body = soup.find('body')
            if body:
                # Remover elementos no deseados
                for unwanted in body.find_all(['script', 'style', 'nav', 'footer', 'header', 'noscript']):
                    unwanted.decompose()
                container = body
                strategy_used = "<body> limpio"

        if not container:
            raise ValueError(
                "No se pudo encontrar contenido válido en el HTML con ninguna estrategia")

        console.print(f"[dim]  → Estrategia utilizada: {strategy_used}[/dim]")

        # Extracción mejorada de texto: recorrer todos los nodos de texto
        text_parts = []
        for element in container.descendants:
            if isinstance(element, str) and element.strip():
                text_parts.append(element.strip())

        text = '\n'.join(text_parts)

        # Limpiar múltiples saltos de línea consecutivos
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Validaciones de calidad
        if len(text) < 100:
            raise ValueError(
                f"Texto extraído demasiado corto ({len(text)} caracteres)")

        # Calcular y mostrar métricas
        text_size = len(text)
        ratio = text_size / html_size if html_size > 0 else 0

        console.print(
            f"[green]✓ Texto extraído: {text_size:,} caracteres ({ratio:.1%} del HTML)[/green]")

        # Alerta si el ratio es sospechosamente bajo
        if ratio < 0.05:
            console.print(
                f"[yellow]⚠ Alerta: Ratio texto/HTML muy bajo ({ratio:.1%}), posible contenido HTML denso[/yellow]")

        return text

    def parse_final_content_structured(self, html: str) -> Dict[str, Any]:
        """
        Nivel 3 mejorado: Extrae contenido preservando estructura tabular.

        Usa TableExtractor para extraer tablas como datos estructurados,
        reemplazándolas con placeholders [TABLA_N] en el texto.

        Args:
            html: Contenido HTML del documento

        Returns:
            Dict con:
                - text_content: Texto con placeholders [TABLA_N]
                - tables: Lista de tablas estructuradas
                - metadata: Información sobre tablas extraídas
        """
        console.print(
            "[cyan]📄 Nivel 3: Extrayendo contenido estructurado...[/cyan]")

        # Validación inicial del HTML
        if not html or len(html) < 100:
            raise ValueError(
                f"HTML inválido o demasiado corto ({len(html) if html else 0} caracteres)")

        html_size = len(html)
        console.print(
            f"[dim]  → HTML recibido: {html_size:,} caracteres[/dim]")

        # Extraer tablas estructuradas
        text_content, tables = self.table_extractor.extract_tables(html)

        # Validaciones de calidad
        if len(text_content) < 50:
            # Fallback al método original si la extracción estructurada falla
            console.print(
                f"[yellow]⚠ Extracción estructurada produjo poco texto, usando método tradicional[/yellow]")
            text_content = self.parse_final_content(html)
            tables = []

        # Calcular métricas
        text_size = len(text_content)
        ratio = text_size / html_size if html_size > 0 else 0
        table_count = len(tables)

        console.print(
            f"[green]✓ Texto extraído: {text_size:,} caracteres ({ratio:.1%} del HTML)[/green]")

        if table_count > 0:
            console.print(
                f"[green]✓ Tablas estructuradas: {table_count}[/green]")
            for t in tables:
                console.print(
                    f"[dim]    → {t.id}: {t.title[:50]}... ({t.stats.row_count} filas)[/dim]")

        # Construir resultado
        return {
            "text_content": text_content,
            "tables": [t.to_dict() for t in tables],
            "metadata": {
                "has_tables": table_count > 0,
                "table_count": table_count,
                "extraction_method": "structured"
            }
        }

    def _scrape_individual_norm(self, norma_metadata: Dict[str, Any], base_url: str,
                                municipio: str) -> Dict[str, Any]:
        """
        Scrapea una norma individual obteniendo contenido completo, tablas y montos.

        Args:
            norma_metadata: Dict con id, url, tipo, titulo, fecha, preview
            base_url: URL base del sitio
            municipio: Nombre del municipio

        Returns:
            Dict con norma completa incluyendo contenido, tablas y montos
        """
        norm_url = norma_metadata['url'] if norma_metadata['url'].startswith(
            'http') else f"{base_url}{norma_metadata['url']}"

        try:
            # Aplicar rate limiting con jitter
            self._wait_for_rate_limit()

            # Fetch HTML de la norma individual
            norm_html = self.fetch_html(norm_url)

            # Extraer contenido estructurado (con tablas)
            try:
                structured = self.parse_final_content_structured(norm_html)
                contenido = structured["text_content"]
                tablas = structured["tables"]
            except Exception as e:
                console.print(
                    f"[yellow]⚠ Error en extracción estructurada: {e}, usando método tradicional[/yellow]")
                contenido = self.parse_final_content(norm_html)
                tablas = []

            # Extraer montos del contenido
            temp_boletin_data = {
                'text_content': contenido,
                'description': municipio,
                'date': norma_metadata.get('fecha', ''),
                'link': norm_url
            }
            montos = self.monto_extractor.extract_from_boletin(
                temp_boletin_data)
            montos_list = [m.to_dict() for m in montos] if montos else []

            # Extraer número de norma del título (ej: "Ordenanza Nº 2319" -> "2319")
            numero_match = re.search(
                r'N[º°]\s*(\d+[/-]?\d*)', norma_metadata['titulo'])
            numero = numero_match.group(
                1) if numero_match else norma_metadata['id']

            # Construir norma completa
            norma_completa = {
                "id": norma_metadata['id'],
                "tipo": norma_metadata['tipo'],
                "numero": numero,
                "titulo": norma_metadata['titulo'],
                "fecha": norma_metadata['fecha'],
                "municipio": municipio,
                "url": norm_url,
                "contenido": contenido,
                "tablas": tablas,
                "montos_extraidos": montos_list,
                "metadata": {
                    "longitud_caracteres": len(contenido),
                    "tiene_tablas": len(tablas) > 0,
                    "total_tablas": len(tablas),
                    "total_montos": len(montos_list)
                }
            }

            return norma_completa

        except Exception as e:
            console.print(
                f"[red]✗ Error scrapeando norma {norma_metadata['id']}: {e}[/red]")
            # Retornar versión mínima con solo metadatos
            return {
                "id": norma_metadata['id'],
                "tipo": norma_metadata['tipo'],
                "numero": norma_metadata.get('id', 'unknown'),
                "titulo": norma_metadata['titulo'],
                "fecha": norma_metadata['fecha'],
                "municipio": municipio,
                "url": norm_url,
                "contenido": norma_metadata.get('preview', ''),
                "tablas": [],
                "montos_extraidos": [],
                "metadata": {
                    "error": str(e),
                    "scraping_failed": True
                }
            }

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
                    # Mostrar información del archivo existente
                    stat = filepath.stat()
                    size_mb = stat.st_size / (1024 * 1024)

                    # Leer el archivo existente para obtener el municipio
                    with filepath.open('r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    municipio = existing_data.get('municipio', 'Desconocido')

                    console.print(
                        f"[green]✓ Saltando boletín {bulletin['number']} (ya existe)[/green]")
                    console.print(f"[dim]    Archivo: {filepath.name}[/dim]")
                    console.print(f"[dim]    Municipio: {municipio}[/dim]")
                    console.print(f"[dim]    Tamaño: {size_mb:.2f} MB[/dim]")
                    console.print(
                        f"[dim]    Modificado: {time.ctime(stat.st_mtime)}[/dim]")

                    # Crear una copia con status="skipped" para el resultado
                    skipped_data = {**existing_data, 'status': 'skipped'}

                    # Actualizar índice con status "skipped"
                    if existing_data.get('status') != 'error':
                        self._update_index_md(
                            skipped_data, output_dir, base_url)

                    return skipped_data
                else:
                    console.print(
                        f"\n[yellow]⚠ El archivo {filepath.name} ya existe[/yellow]")
                    console.print(
                        f"\n¿Qué deseas hacer con el boletín [bold]{bulletin['number']}[/bold]?")
                    console.print(
                        "  [cyan]1.[/cyan] Saltar y continuar con el siguiente")
                    console.print(
                        "  [cyan]2.[/cyan] Sobreescribir este boletín")
                    console.print("  [cyan]3.[/cyan] Cancelar todo el proceso")

                    try:
                        choice = input(
                            "\nElige una opción (1-3) [1]: ").strip() or "1"

                        if choice == "3":
                            console.print(
                                f"[red]✗ Proceso cancelado por el usuario[/red]")
                            sys.exit(0)
                        elif choice == "1":
                            console.print(
                                f"[yellow]⏭ Saltando boletín {bulletin['number']}[/yellow]\n")

                            # Leer archivo existente
                            with filepath.open('r', encoding='utf-8') as f:
                                existing_data = json.load(f)

                            # Actualizar índice con status "skipped"
                            if existing_data.get('status') != 'error':
                                update_data = {
                                    **existing_data, 'status': 'skipped'}
                                self._update_index_md(
                                    update_data, output_dir, base_url)

                            return existing_data
                        elif choice == "2":
                            console.print(
                                f"[cyan]♻️ Sobreescribiendo {filepath.name}...[/cyan]\n")
                        else:
                            console.print(
                                f"[yellow]⚠ Opción inválida, saltando...[/yellow]\n")

                            # Leer archivo existente
                            with filepath.open('r', encoding='utf-8') as f:
                                existing_data = json.load(f)

                            # Actualizar índice con status "skipped"
                            if existing_data.get('status') != 'error':
                                update_data = {
                                    **existing_data, 'status': 'skipped'}
                                self._update_index_md(
                                    update_data, output_dir, base_url)

                            return existing_data
                    except KeyboardInterrupt:
                        console.print(
                            f"\n[red]✗ Proceso cancelado por el usuario[/red]")
                        sys.exit(0)

            console.print(
                f"\n[bold cyan]📰 Procesando boletín: {bulletin['number']}[/bold cyan]")

            # Nivel 2: Obtener metadatos de normas desde el HTML del boletín
            bulletin_url = bulletin['link'] if bulletin['link'].startswith(
                'http') else f"{base_url}{bulletin['link']}"
            bulletin_html = self.fetch_html(bulletin_url)
            normas_metadata = self.parse_bulletin_content_links(bulletin_html)

            if not normas_metadata:
                municipio = self._extract_municipality_name(
                    bulletin.get('description', ''))
                console.print(
                    f"[yellow]⚠ Sin normas en {bulletin['number']} - {municipio}[/yellow]")
                console.print(f"[dim]🔗 Verificar: {bulletin_url}[/dim]")
                no_content_result = {
                    "municipio": self._extract_municipality_name(bulletin.get('description', '')),
                    "numero_boletin": bulletin.get('number', 'N/A'),
                    "fecha_boletin": bulletin.get('date', 'N/A'),
                    "boletin_url": bulletin_url,
                    "status": "no_content",
                    "total_normas": 0,
                    "normas": []
                }

                # Actualizar índice markdown
                self._update_index_md(
                    {**bulletin, "status": "no_content"}, output_dir, base_url)

                return no_content_result

            # Extraer nombre del municipio
            municipio = self._extract_municipality_name(
                bulletin.get('description', ''))

            console.print(
                f"[green]✓ Encontradas {len(normas_metadata)} normas para procesar[/green]")

            # Verificar si hay progreso previo (modo resume)
            bulletin_id = bulletin_url.split(
                '/bulletins/')[-1].split('?')[0] if '/bulletins/' in bulletin_url else filename
            progress_data = self._load_progress(bulletin_id, output_dir)

            # Cargar índice global de normativas para persistencia entre boletines
            from normativas_extractor import load_normativas_index
            global_normas_index = load_normativas_index()

            if progress_data:
                normas_procesadas_ids = set(
                    progress_data.get('normas_procesadas', []))
                console.print(
                    f"[cyan]🔄 Resumiendo scraping: {len(normas_procesadas_ids)} normas ya procesadas[/cyan]")
            else:
                normas_procesadas_ids = set(global_normas_index.keys())
                console.print(
                    f"[cyan]🔄 Resumiendo scraping: {len(normas_procesadas_ids)} normas ya procesadas (índice global)[/cyan]")

            # Nivel 3: Scrapear cada norma individual
            normas_completas = []
            normas_pendientes = [
                n['id'] for n in normas_metadata if n['id'] not in normas_procesadas_ids]

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Procesando {len(normas_pendientes)} normas...",
                    total=len(normas_pendientes)
                )

                for i, norma_meta in enumerate(normas_metadata, 1):
                    # Si ya fue procesada, saltarla
                    if norma_meta['id'] in normas_procesadas_ids:
                        console.print(
                            f"[dim]  ⏭ Norma {norma_meta['id']} ya procesada[/dim]")
                        continue

                    console.print(
                        f"[dim]  → Norma {i}/{len(normas_metadata)}: {norma_meta['titulo'][:50]}...[/dim]")

                    # Scrapear norma individual
                    norma_completa = self._scrape_individual_norm(
                        norma_meta, base_url, municipio)
                    normas_completas.append(norma_completa)

                    # Actualizar progreso
                    normas_procesadas_ids.add(norma_meta['id'])
                    normas_pendientes.remove(norma_meta['id'])
                    self._save_progress(
                        bulletin_id,
                        output_dir,
                        list(normas_procesadas_ids),
                        normas_pendientes
                    )

                    progress.update(task, advance=1)

            # Construir resultado con nuevo formato de normas individuales
            result = {
                "municipio": municipio,
                "numero_boletin": bulletin.get('number', 'N/A'),
                "fecha_boletin": bulletin.get('date', 'N/A'),
                "boletin_url": bulletin_url,
                "status": "completed",
                "total_normas": len(normas_completas),
                "normas": normas_completas,
                "metadata_boletin": {
                    "total_caracteres": sum(n['metadata'].get('longitud_caracteres', 0) for n in normas_completas),
                    "total_tablas": sum(n['metadata'].get('total_tablas', 0) for n in normas_completas),
                    "total_montos": sum(n['metadata'].get('total_montos', 0) for n in normas_completas),
                    "fecha_scraping": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    "version_scraper": "2.0"
                }
            }

            # Guardar archivo individual
            filename = self._sanitize_filename(
                bulletin.get('description', bulletin['number']))
            filepath = output_dir / f"{filename}.json"

            with filepath.open('w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            # Limpiar archivo de progreso (boletín completado)
            self._clean_progress(bulletin_id, output_dir)

            # Agregar montos al índice global (ya fueron extraídos por norma individual)
            total_montos_agregados = 0
            for norma in normas_completas:
                montos_norma = norma.get('montos_extraidos', [])
                if montos_norma:
                    self.montos_acumulados.extend(montos_norma)
                    total_montos_agregados += len(montos_norma)

            if total_montos_agregados > 0:
                console.print(
                    f"[dim]    → {total_montos_agregados} montos agregados al índice global[/dim]")

            # Agregar normativas al índice global
            for norma in normas_completas:
                # Extraer año del número o de la fecha
                year = ''
                if '/' in norma['numero']:
                    year = norma['numero'].split('/')[-1]
                elif norma.get('fecha'):
                    parts = norma['fecha'].split('/')
                    if len(parts) == 3:
                        year = parts[2]

                normativa_obj = Normativa(
                    id=norma['id'],
                    municipality=municipio,
                    type=norma['tipo'],
                    number=norma['numero'],
                    year=year,
                    date=norma.get('fecha', ''),
                    title=norma['titulo'],
                    content=norma.get('contenido', ''),
                    source_bulletin=filename,
                    source_bulletin_url=bulletin_url,
                    norma_url=norma['url'],
                    doc_index=0,  # En V2 no usamos doc_index
                    status='vigente',
                    extracted_at=datetime.now().isoformat()
                )
                self.normativas_acumuladas.append(normativa_obj)

            console.print(
                f"[dim]    → {len(normas_completas)} normativas agregadas al índice global[/dim]")

            # Actualizar índice markdown (adaptar para nuevo formato)
            index_data = {
                "number": bulletin.get('number', 'N/A'),
                "date": bulletin.get('date', 'N/A'),
                "description": bulletin.get('description', ''),
                "link": bulletin_url,
                "status": "completed"
            }
            self._update_index_md(index_data, output_dir, base_url)

            # Contar tipos de normas
            tipos_count = {}
            for norma in normas_completas:
                tipo = norma.get('tipo', 'desconocido')
                tipos_count[tipo] = tipos_count.get(tipo, 0) + 1

            # Construir string de tipos de normas
            tipos_str = "\n".join(
                [f"  • {tipo.capitalize()}: {count}" for tipo, count in sorted(tipos_count.items())])

            # Panel de resumen del boletín procesado
            console.print("\n")
            console.print(Panel.fit(
                f"[bold green]✓ Boletín Completado[/bold green]\n"
                f"Número: {bulletin['number']}\n"
                f"Municipio: {municipio}\n"
                f"Archivo: {filepath.name}\n"
                f"URL: {bulletin_url}\n"
                f"\n"
                f"[cyan]📊 Estadísticas:[/cyan]\n"
                f"  • Total normas: {len(normas_completas)}\n"
                f"{tipos_str}\n"
                f"  • Tablas: {result['metadata_boletin']['total_tablas']}\n"
                f"  • Montos: {result['metadata_boletin']['total_montos']}\n"
                f"  • Caracteres: {result['metadata_boletin']['total_caracteres']:,}",
                title="📰 Resumen del Boletín",
                border_style="green"
            ))

            # Reproducir sonido de éxito
            self._play_sound('success')

            return result

        except Exception as e:
            console.print(
                f"[bold red]✗ Error en boletín {bulletin['number']}: {e}[/bold red]")
            error_result = {**bulletin, "status": "error",
                            "fullText": "", "error": str(e)}

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
            console.print(
                "\n[bold cyan]🎯 Modo: Boletín Individual[/bold cyan]")

            # Extraer número del boletín de la URL
            bulletin_id = target_url.split(
                '/bulletins/')[-1].split('?')[0].split('#')[0]
            console.print(
                f"[dim]Obteniendo metadatos del boletín {bulletin_id}...[/dim]")

            # Obtener metadatos reales del boletín
            try:
                bulletin_html = self.fetch_html(target_url)

                # Extraer metadatos del HTML usando LLM
                metadata_prompt = f"""Extrae los metadatos de este boletín oficial.
Busca el número del boletín (ej: "105º", "Boletín 98º"), la fecha de publicación, y una descripción breve.
Devuelve SOLO un JSON válido con el formato: {{"number": string, "date": string, "description": string}}

HTML: {bulletin_html[:50000]}"""

                response = self._make_llm_call(
                    metadata_prompt, use_json_mode=True)
                cleaned = self._extract_json(response)
                metadata = json.loads(cleaned)

                # Crear objeto bulletin con metadatos reales
                bulletins = [{
                    "number": metadata.get("number", f"#{bulletin_id}"),
                    "date": metadata.get("date", "N/A"),
                    "description": metadata.get("description", f"Boletín {bulletin_id}"),
                    "link": f"/bulletins/{bulletin_id}"
                }]

                console.print(
                    f"[green]✓ Boletín: {bulletins[0]['number']} - {bulletins[0]['description']}[/green]")

            except Exception as e:
                console.print(
                    f"[yellow]⚠ No se pudieron obtener metadatos: {e}[/yellow]")
                console.print(
                    f"[yellow]  Usando valores por defecto...[/yellow]")

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
                console.print(
                    "[cyan]🎯 Modo: Página única (parámetro ?page= detectado)[/cyan]")
                list_html = self.fetch_html(target_url)
                bulletins = self.parse_listing_page(list_html, target_url)
            else:
                # Modo automático: detectar y procesar todas las páginas
                console.print(
                    "[cyan]🔄 Modo: Detección automática de paginación[/cyan]")

                # Obtener primera página para detectar total de páginas
                list_html = self.fetch_html(target_url)
                total_pages = self.detect_total_pages(list_html)

                # Extraer boletines de la primera página
                bulletins = self.parse_listing_page(list_html, target_url)
                console.print(
                    f"[dim]  Página 1/{total_pages}: {len(bulletins)} boletines[/dim]")

                # Procesar páginas restantes
                if total_pages > 1:
                    # Construir URL base (remover cualquier parámetro existente)
                    base_url_parsed = target_url.split('?')[0]

                    for page_num in range(2, total_pages + 1):
                        try:
                            page_url = f"{base_url_parsed}?page={page_num}"
                            console.print(
                                f"[cyan]📄 Página {page_num}/{total_pages}...[/cyan]")

                            page_html = self.fetch_html(page_url)
                            page_bulletins = self.parse_listing_page(
                                page_html, page_url)

                            bulletins.extend(page_bulletins)
                            console.print(
                                f"[dim]  Página {page_num}/{total_pages}: {len(page_bulletins)} boletines (total acumulado: {len(bulletins)})[/dim]")
                        except Exception as e:
                            console.print(
                                f"[red]✗ Error en página {page_num}: {e}[/red]")
                            console.print(
                                f"[yellow]⚠ Continuando con las páginas restantes...[/yellow]")
                            continue

                    console.print(
                        f"\n[bold green]✓ Total: {len(bulletins)} boletines de {total_pages} páginas[/bold green]")

        # Aplicar límite DESPUÉS de recolectar todos los boletines
        if limit:
            original_count = len(bulletins)
            bulletins = bulletins[:limit]
            console.print(
                f"[yellow]⚙ Limitando de {original_count} a {limit} boletines[/yellow]")

        # Crear carpeta de salida
        output_dir = Path("boletines")
        output_dir.mkdir(exist_ok=True)
        console.print(
            f"[cyan]📁 Carpeta de salida: {output_dir.absolute()}[/cyan]")

        # Procesar boletines
        console.print(
            f"\n[bold]═══ NIVELES 2 y 3: PROCESANDO {len(bulletins)} BOLETINES ═══[/bold]")

        base_url = "https://sibom.slyt.gba.gob.ar"
        results = []

        if parallel > 1:
            # Procesamiento paralelo
            with ThreadPoolExecutor(max_workers=parallel) as executor:
                futures = {executor.submit(
                    self.process_bulletin, b, base_url, output_dir, skip_existing): b for b in bulletins}

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(
                        f"[cyan]Procesando...", total=len(bulletins))

                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        progress.update(task, advance=1)
        else:
            # Procesamiento secuencial
            for i, bulletin in enumerate(bulletins, 1):
                console.print(
                    f"\n[dim]→ Procesando {i}/{len(bulletins)}: {bulletin['number']}[/dim]")
                result = self.process_bulletin(
                    bulletin, base_url, output_dir, skip_existing)
                results.append(result)
                console.print(
                    f"[dim]→ Resultado agregado. Total acumulado: {len(results)}[/dim]")

        return results

    # ========================================================================
    # MÉTODOS PARA PROCESAMIENTO MÚLTIPLE DE CIUDADES
    # ========================================================================

    def auto_generate_city_map(self, start_id: int, end_id: int) -> Dict[str, str]:
        """
        Genera CITY_MAP.json consultando SIBOM para cada ciudad en el rango.

        Args:
            start_id: ID inicial de ciudad
            end_id: ID final de ciudad

        Returns:
            Dict con el mapeo de IDs a nombres
        """
        city_map = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Generando CITY_MAP para ciudades {start_id}-{end_id}...",
                total=end_id - start_id + 1
            )

            base_url = "https://sibom.slyt.gba.gob.ar"

            for city_id in range(start_id, end_id + 1):
                try:
                    # Consultar la página de la ciudad
                    url = f"{base_url}/cities/{city_id}"
                    response = requests.get(
                        url, headers=self.headers, timeout=10)

                    if response.status_code == 200:
                        html = response.text

                        # Buscar nombre en el primer boletín
                        # Formato: <p class="bulletin-title">XXº de [Ciudad]</p>
                        match = re.search(
                            r'<p[^>]*class="[^"]*bulletin-title[^"]*"[^>]*>([^<]+)</p>',
                            html,
                            re.IGNORECASE
                        )
                        if match:
                            title = match.group(1).strip()
                            # Formato típico: "105º de Carlos Tejedor"
                            name_match = re.search(
                                r'º?\s+de\s+([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñÑ\s]+)',
                                title
                            )
                            if name_match:
                                name = name_match.group(1).strip()
                                city_map[str(city_id)] = name
                                console.print(
                                    f"[dim]  {city_id}: {name}[/dim]")

                except Exception:
                    # Silenciosamente continuar si una ciudad falla
                    pass

                progress.update(task, advance=1)

        # Guardar el mapa
        if city_map:
            self.CITY_MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self.CITY_MAP_FILE.open('w', encoding='utf-8') as f:
                json.dump(city_map, f, indent=2, ensure_ascii=False)
            console.print(
                f"[green]✓ CITY_MAP guardado: {len(city_map)} ciudades[/green]")
        else:
            console.print("[yellow]⚠ No se pudo generar CITY_MAP[/yellow]")

        return city_map

    def scrape_multiple_cities(
        self,
        city_ids: List[int],
        skip_existing: bool = False,
        parallel: int = 1
    ) -> Dict[int, Dict[str, Any]]:
        """
        Scraping masivo de múltiples ciudades con TODAS las páginas.

        Args:
            city_ids: Lista de IDs de ciudades a procesar
            skip_existing: Saltar boletines ya procesados
            parallel: Procesamiento paralelo de boletines dentro de cada ciudad

        Returns:
            Dict con city_id -> {total_boletines, completados, errores, tiempo, nombre}
        """
        base_url = "https://sibom.slyt.gba.gob.ar"
        output_dir = Path("boletines")
        output_dir.mkdir(exist_ok=True)

        # Estadísticas por ciudad
        city_stats: Dict[int, Dict[str, Any]] = {}
        cities_with_errors: List[tuple[int, str, str]] = []

        # Mostrar panel de inicio
        console.print(Panel.fit(
            f"[bold cyan]SIBOM Scraper - Modo Múltiples Ciudades[/bold cyan]\n"
            f"Total ciudades: {len(city_ids)}\n"
            f"Rango: {min(city_ids)} - {max(city_ids)}\n"
            f"Skip existing: {skip_existing}\n"
            f"Paralelismo: {parallel}",
            title="🚀 Iniciando"
        ))

        # Obtener nombres de ciudades
        city_map = self._load_city_map()

        total_start_time = time.time()

        for idx, city_id in enumerate(city_ids, 1):
            city_name = city_map.get(str(city_id), f"Ciudad {city_id}")
            city_start_time = time.time()

            console.print(
                f"\n[bold cyan]═══ CIUDAD {idx}/{len(city_ids)}: {city_name} (ID: {city_id}) ═══[/bold cyan]")

            try:
                # Construir URL de la ciudad
                city_url = f"{base_url}/cities/{city_id}"

                # Obtener primera página para detectar total de páginas
                list_html = self.fetch_html(city_url)
                total_pages = self.detect_total_pages(list_html)

                # Recolectar boletines de todas las páginas
                all_bulletins = []

                if total_pages == 1:
                    # Solo una página
                    bulletins = self.parse_listing_page(list_html, city_url)
                    all_bulletins.extend(bulletins)
                else:
                    # Múltiples páginas
                    for page_num in range(1, total_pages + 1):
                        if page_num == 1:
                            bulletins = self.parse_listing_page(
                                list_html, city_url)
                        else:
                            page_url = f"{city_url}?page={page_num}"
                            page_html = self.fetch_html(page_url)
                            bulletins = self.parse_listing_page(
                                page_html, page_url)
                        all_bulletins.extend(bulletins)
                        console.print(
                            f"[dim]    Página {page_num}/{total_pages}: {len(bulletins)} boletines[/dim]")

                if not all_bulletins:
                    console.print(
                        f"[yellow]⚠ No se encontraron boletines para {city_name} (ID: {city_id})[/yellow]")
                    console.print(f"[dim]🔗 Verificar: {city_url}[/dim]")
                    city_stats[city_id] = {
                        "nombre": city_name,
                        "total_boletines": 0,
                        "completados": 0,
                        "errores": 0,
                        "tiempo": 0
                    }
                    continue

                console.print(
                    f"[green]✓ Total boletines a procesar: {len(all_bulletins)}[/green]")

                # Procesar boletines de esta ciudad
                city_results = []
                city_errors = 0

                if parallel > 1:
                    # Procesamiento paralelo
                    with ThreadPoolExecutor(max_workers=parallel) as executor:
                        futures = {
                            executor.submit(
                                self.process_bulletin,
                                b,
                                base_url,
                                output_dir,
                                skip_existing
                            ): b for b in all_bulletins
                        }

                        with Progress(
                            SpinnerColumn(),
                            TextColumn(
                                "[progress.description]{task.description}"),
                            BarColumn(),
                            TaskProgressColumn(),
                            console=console
                        ) as progress:
                            task = progress.add_task(
                                f"[cyan]Procesando {city_name}...",
                                total=len(all_bulletins)
                            )

                            for future in as_completed(futures):
                                result = future.result()
                                city_results.append(result)
                                if result.get('status') == 'error':
                                    city_errors += 1
                                progress.update(task, advance=1)
                else:
                    # Procesamiento secuencial
                    for bulletin in all_bulletins:
                        result = self.process_bulletin(
                            bulletin, base_url, output_dir, skip_existing
                        )
                        city_results.append(result)
                        if result.get('status') == 'error':
                            city_errors += 1

                # Contar completados y errores
                city_completed = sum(
                    1 for r in city_results if r.get('status') == 'completed'
                )
                city_error_count = sum(
                    1 for r in city_results if r.get('status') == 'error'
                )
                city_no_content = sum(
                    1 for r in city_results if r.get('status') == 'no_content'
                )
                city_skipped = sum(
                    1 for r in city_results if r.get('status') == 'skipped'
                )

                city_elapsed = time.time() - city_start_time

                # Guardar estadísticas
                city_stats[city_id] = {
                    "nombre": city_name,
                    "total_boletines": len(all_bulletins),
                    "completados": city_completed,
                    "omitidos": city_skipped,
                    "sin_contenido": city_no_content,
                    "errores": city_error_count,
                    "tiempo": city_elapsed
                }

                # Resumen de ciudad
                console.print(Panel.fit(
                    f"[bold green]✓ {city_name} completada[/bold green]\n"
                    f"Boletines: {len(all_bulletins)}\n"
                    f"  Completados: {city_completed}\n"
                    f"  Omítidos: {city_skipped}\n"
                    f"  Sin contenido: {city_no_content}\n"
                    f"  Errores: {city_error_count}\n"
                    f"Tiempo: {city_elapsed:.1f}s",
                    title=f"🏙️ {city_name}"
                ))

            except Exception as e:
                city_elapsed = time.time() - city_start_time
                error_msg = str(e)
                console.print(
                    f"[red]✗ Error procesando {city_name}: {error_msg}[/red]")
                cities_with_errors.append((city_id, city_name, error_msg))
                city_stats[city_id] = {
                    "nombre": city_name,
                    "total_boletines": 0,
                    "completados": 0,
                    "omitidos": 0,
                    "sin_contenido": 0,
                    "errores": 1,
                    "tiempo": city_elapsed
                }

        total_elapsed = time.time() - total_start_time

        # Mostrar resumen final
        self.print_multi_city_summary(
            city_stats, cities_with_errors, total_elapsed)

        return city_stats

    def print_multi_city_summary(
        self,
        city_stats: Dict[int, Dict[str, Any]],
        cities_with_errors: List[tuple[int, str, str]],
        total_time: float
    ):
        """
        Imprime resumen completo del procesamiento de múltiples ciudades.

        Args:
            city_stats: Dict con estadísticas por ciudad
            cities_with_errors: Lista de (city_id, nombre, error)
            total_time: Tiempo total de ejecución
        """
        console.print("\n")
        console.print(Panel.fit(
            f"[bold cyan]RESUMEN DE EJECUCIÓN[/bold cyan]",
            title="📊"
        ))

        # Tabla de estadísticas por ciudad
        table = Table(
            title=f"Estadísticas por Ciudad ({len(city_stats)} ciudades)")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Ciudad", style="green", width=25)
        table.add_column("Total", justify="right", style="white")
        table.add_column("✓", justify="right", style="green")
        table.add_column("⊘", justify="right", style="yellow")
        table.add_column("∅", justify="right", style="dim")
        table.add_column("✗", justify="right", style="red")
        table.add_column("Tiempo", justify="right", style="white")

        for city_id in sorted(city_stats.keys()):
            stats = city_stats[city_id]
            table.add_row(
                str(city_id),
                stats['nombre'][:24],
                str(stats['total_boletines']),
                str(stats['completados']),
                str(stats.get('omitidos', 0)),
                str(stats.get('sin_contenido', 0)),
                str(stats['errores']),
                f"{stats['tiempo']:.1f}s"
            )

        console.print("\n")
        console.print(table)

        # Totales generales
        total_boletines = sum(s['total_boletines']
                              for s in city_stats.values())
        total_completados = sum(s['completados'] for s in city_stats.values())
        total_omitidos = sum(s.get('omitidos', 0) for s in city_stats.values())
        total_no_content = sum(s.get('sin_contenido', 0)
                               for s in city_stats.values())
        total_errores = sum(s['errores'] for s in city_stats.values())

        console.print("\n")
        summary_table = Table(title="Totales Generales")
        summary_table.add_column("Métrica", style="cyan")
        summary_table.add_column("Valor", justify="right", style="green")

        summary_table.add_row("Ciudades procesadas", str(len(city_stats)))
        summary_table.add_row("Total boletines", str(total_boletines))
        summary_table.add_row("Completados", str(total_completados))
        summary_table.add_row("Omitidos (existentes)", str(total_omitidos))
        summary_table.add_row("Sin contenido", str(total_no_content))
        summary_table.add_row("Errores", str(total_errores))
        summary_table.add_row(
            "Tiempo total", f"{total_time:.1f}s ({total_time/60:.1f}m)")

        if total_completados > 0:
            avg_time = total_time / total_completados
            summary_table.add_row("Promedio por boletín", f"{avg_time:.1f}s")

        console.print("\n")
        console.print(summary_table)

        # Ciudades con errores
        if cities_with_errors:
            console.print("\n")
            console.print(Panel.fit(
                f"[bold red]Ciudades con errores ({len(cities_with_errors)})[/bold red]",
                title="⚠️"
            ))
            for city_id, city_name, error in cities_with_errors:
                console.print(
                    f"[red]  ID {city_id} ({city_name}): {error[:60]}...[/red]")


def parse_city_ranges(ranges_str: str) -> List[int]:
    """
    Parsea rangos de ciudades como "1-136", "1-21,23-136", "5".
    Retorna lista ordenada de IDs de ciudades únicos.

    Args:
        ranges_str: String con rangos separados por coma (ej: "1-5,10,15-20")

    Returns:
        Lista de IDs de ciudades como enteros

    Examples:
        >>> parse_city_ranges("1-5")
        [1, 2, 3, 4, 5]
        >>> parse_city_ranges("1-3,5,7-9")
        [1, 2, 3, 5, 7, 8, 9]
        >>> parse_city_ranges("22")
        [22]
    """
    city_ids = set()
    for part in ranges_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            city_ids.update(range(int(start), int(end) + 1))
        else:
            city_ids.add(int(part))
    return sorted(city_ids)


def update_sqlite_database(normativas: List[Normativa], db_path: str = "normativas.db") -> bool:
    """
    Actualiza la base de datos SQLite con las normativas extraídas.

    Esta función se llama automáticamente después del scraping para
    mantener SQLite sincronizado con los archivos JSON.

    Args:
        normativas: Lista de normativas a agregar/actualizar
        db_path: Ruta a la base de datos SQLite

    Returns:
        True si la actualización fue exitosa, False otherwise
    """
    if not normativas:
        return False

    try:
        # Importar el schema desde normativas_to_sqlite
        from normativas_to_sqlite import SCHEMA, create_database

        console.print(
            f"\n[cyan]🗄️ Actualizando SQLite con {len(normativas):,} normativas nuevas...[/cyan]")

        # Crear/conectar a la BD
        conn = create_database(db_path)
        cursor = conn.cursor()

        inserted = 0
        updated = 0
        skipped = 0

        for normativa in normativas:
            try:
                # Verificar si ya existe
                cursor.execute(
                    "SELECT id FROM normativas WHERE id = ?", (normativa.id,))
                exists = cursor.fetchone()

                if exists:
                    # UPDATE: Solo actualizar campos que pueden cambiar
                    cursor.execute("""
                        UPDATE normativas SET
                            title = ?,
                            content = ?,
                            status = ?
                        WHERE id = ?
                    """, (
                        normativa.title[:500],  # Limitar título
                        normativa.content,
                        normativa.status,
                        normativa.id
                    ))
                    updated += cursor.rowcount
                else:
                    # INSERT: Nueva normativa
                    cursor.execute("""
                        INSERT OR REPLACE INTO normativas (
                            id, municipality, type, number, year, date, title,
                            content, source_bulletin, source_bulletin_url,
                            norma_url, doc_index, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        normativa.id,
                        normativa.municipality,
                        normativa.type,
                        normativa.number,
                        normativa.year,
                        normativa.date,
                        normativa.title[:500],
                        normativa.content,
                        normativa.source_bulletin,
                        normativa.source_bulletin_url,
                        normativa.norma_url,
                        normativa.doc_index,
                        normativa.status
                    ))
                    inserted += 1

            except sqlite3.IntegrityError:
                skipped += 1

        conn.commit()

        # Estadísticas finales
        cursor.execute("SELECT COUNT(*) FROM normativas")
        total_db = cursor.fetchone()[0]

        conn.close()

        console.print(
            f"[green]✅ SQLite actualizada:[/green]"
        )
        console.print(
            f"   • Insertadas: {inserted:,}"
        )
        console.print(
            f"   • Actualizadas: {updated:,}"
        )
        console.print(
            f"   • Skip (duplicadas): {skipped:,}"
        )
        console.print(
            f"   • Total en BD: {total_db:,}"
        )
        console.print(
            f"   • Tamaño BD: {Path(db_path).stat().st_size / (1024*1024):.2f} MB"
        )

        return True

    except Exception as e:
        console.print(f"[red]❌ Error actualizando SQLite: {e}[/red]")
        return False


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
        '--cities',
        type=str,
        default=None,
        help='Rangos de ciudades a escrapear (ej: "1-21,23-136")'
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
        '--start-from',
        type=int,
        default=None,
        help='ID de ciudad desde donde comenzar (para reanudar proceso interrumpido)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='google/gemini-3-flash-preview',
        help='Modelo de OpenRouter a usar (default: google/gemini-3-flash-preview)'
    )

    parser.add_argument(
        '--no-sqlite',
        action='store_true',
        help='No actualizar SQLite automáticamente después del scraping'
    )

    args = parser.parse_args()

    # Obtener API key
    api_key = args.api_key or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        console.print(
            "[bold red]Error: No se encontró OPENROUTER_API_KEY[/bold red]")
        console.print("Usa --api-key o configura la variable en .env")
        sys.exit(1)

    # Crear scraper y ejecutar
    scraper = SIBOMScraper(api_key, model=args.model)

    try:
        start_time = time.time()

        # Modo múltiples ciudades vs modo single URL
        if args.cities:
            # Parsear rangos de ciudades
            city_ids = parse_city_ranges(args.cities)

            # Generar CITY_MAP si no existe
            if not scraper.CITY_MAP_FILE.exists():
                console.print(
                    "[yellow]⚠ CITY_MAP.json no encontrado, generando...[/yellow]")
                scraper.auto_generate_city_map(min(city_ids), max(city_ids))

            # Aplicar start-from si se especificó
            if args.start_from:
                filtered_count = len(
                    [c for c in city_ids if c >= args.start_from])
                console.print(
                    f"[cyan]📍 Filtrando ciudades: comenzando desde ID {args.start_from}[/cyan]")
                console.print(
                    f"[dim]    Ciudades antes del filtro: {len(city_ids)}[/dim]")
                console.print(
                    f"[dim]    Ciudades después del filtro: {filtered_count}[/dim]")
                city_ids = [c for c in city_ids if c >= args.start_from]

            # Usar scrape_multiple_cities
            city_stats = scraper.scrape_multiple_cities(
                city_ids=city_ids,
                skip_existing=args.skip_existing,
                parallel=args.parallel
            )
            # No es necesario guardar resumen consolidado en modo múltiple
            # Los archivos individuales ya se guardaron en process_bulletin
        else:
            # Modo existente con --url (backward compatible)
            results = scraper.scrape(
                args.url, limit=args.limit, parallel=args.parallel, skip_existing=args.skip_existing)
            elapsed = time.time() - start_time

            # Guardar resumen consolidado (opcional)
            output_path = Path(args.output)
            with output_path.open('w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            # Mostrar resumen
            completed = sum(1 for r in results if r.get(
                'status') == 'completed')
            errors = sum(1 for r in results if r.get('status') == 'error')
            no_content = sum(1 for r in results if r.get(
                'status') == 'no_content')

            table = Table(title="📊 Resumen de Ejecución")
            table.add_column("Métrica", style="cyan")
            table.add_column("Valor", style="green")

            table.add_row("Total procesados", str(len(results)))
            table.add_row("Completados", str(completed))
            table.add_row("Errores", str(errors))
            table.add_row("Sin contenido", str(no_content))
            table.add_row("Tiempo total", f"{elapsed:.1f}s")
            table.add_row("Tiempo por boletín",
                          f"{elapsed/len(results):.1f}s" if len(results) > 0 else "N/A")
            table.add_row("Carpeta boletines", "boletines/")
            table.add_row("Resumen consolidado", str(output_path))

            console.print("\n")
            console.print(table)
            console.print(
                f"\n[bold green]✓ Boletines individuales guardados en: boletines/[/bold green]")
            console.print(
                f"[bold green]✓ Resumen consolidado guardado en: {output_path}[/bold green]")

            # Reproducir sonido de tarea completa
            scraper._play_sound('complete')

        # Guardar índice de montos extraídos (común a ambos modos)
        if scraper.montos_acumulados:
            montos_path = Path("montos_index.json")
            scraper.monto_extractor._save_index(
                scraper.montos_acumulados, montos_path)
            console.print(
                f"[bold green]✓ Índice de montos guardado: {len(scraper.montos_acumulados):,} registros[/bold green]")

        # Guardar índice de normativas extraídas (común a ambos modos)
        if scraper.normativas_acumuladas:
            normativas_path = Path("normativas_index.json")
            normativas_compact_path = Path("normativas_index_compact.json")
            normativas_minimal_path = Path("normativas_index_minimal.json")

            # Guardar índice completo
            save_index(scraper.normativas_acumuladas,
                       normativas_path, compact=False)
            console.print(
                f"[bold green]✓ Índice de normativas (completo): {len(scraper.normativas_acumuladas):,} registros[/bold green]")

            # Guardar índice compacto (sin contenido)
            save_index(scraper.normativas_acumuladas,
                       normativas_compact_path, compact=True)
            console.print(
                f"[bold green]✓ Índice de normativas (compacto): {normativas_compact_path}[/bold green]")

            # Guardar índice minimalista (para frontend)
            save_minimal_index(scraper.normativas_acumuladas,
                               normativas_minimal_path)
            console.print(
                f"[bold green]✓ Índice de normativas (minimal): {normativas_minimal_path}[/bold green]")

            # Actualizar SQLite automáticamente (a menos que se use --no-sqlite)
            if not args.no_sqlite:
                update_sqlite_database(scraper.normativas_acumuladas)
            else:
                console.print(
                    "[dim]⏭ Saltando actualización de SQLite (--no-sqlite activado)[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Proceso interrumpido por el usuario[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error fatal: {e}[/bold red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
