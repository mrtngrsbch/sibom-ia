#!/usr/bin/env python3
"""
discovery.py

Descubre PDFs de normativas usando múltiples estrategias.

Estrategias en cascada:
1. Sitemap XML (si existe)
2. Google Search vía SerpAPI
3. Crawling de páginas (links directos)

Uso:
    from discovery import PDFDiscovery
    discovery = PDFDiscovery()
    pdfs = await discovery.discover_pdfs("https://boletin.casares.gob.ar")

@version 1.0.0
@created 2026-01-29
"""

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

console = Console()


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class DiscoveredPDF:
    """Representa un PDF descubierto"""
    url: str
    domain: str
    found_date: str
    source: str  # "sitemap", "google_search", "crawling"
    status: str = "pending"  # "pending", "scraped", "error", "skipped"
    content_hash: Optional[str] = None
    title: Optional[str] = None
    size_bytes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# PDF DISCOVERY
# =============================================================================

class PDFDiscovery:
    """
    Descubre PDFs de normativas usando múltiples estrategias.

    Usa cache para evitar reprocesar los mismos PDFs y mantiene
    un registro de qué ya fue scrapeado.
    """

    def __init__(
        self,
        cache_dir: Path = None,
        serpapi_key: str = None,
        max_results: int = 100
    ):
        """
        Args:
            cache_dir: Directorio para el cache de PDFs
            serpapi_key: API key de SerpAPI (opcional)
            max_results: Máximo de PDFs a descubrir por fuente
        """
        from config import CACHE_DIR

        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)

        self.cache_file = self.cache_dir / "scraped_pdfs.json"
        self.serpapi_key = serpapi_key
        self.max_results = max_results

        # Cargar cache existente
        self.cache = self._load_cache()

        # Cliente HTTP
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Carga el cache de PDFs ya procesados"""
        if self.cache_file.exists():
            try:
                with self.cache_file.open('r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]⚠️ Error cargando cache: {e}[/yellow]")
        return {}

    def _save_cache(self):
        """Guarda el cache de PDFs"""
        try:
            with self.cache_file.open('w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[yellow]⚠️ Error guardando cache: {e}[/yellow]")

    def _get_domain_cache(self, domain: str) -> Dict[str, Any]:
        """Obtiene el cache de un dominio específico"""
        if domain not in self.cache:
            self.cache[domain] = {
                "last_scan": None,
                "pdfs": [],
                "total_count": 0
            }
        return self.cache[domain]

    def _is_already_processed(self, domain: str, url: str) -> bool:
        """Verifica si un PDF ya fue procesado"""
        domain_cache = self._get_domain_cache(domain)
        return any(p["url"] == url for p in domain_cache["pdfs"])

    def _add_to_cache(self, pdf: DiscoveredPDF):
        """Agrega un PDF al cache"""
        domain = pdf.domain
        domain_cache = self._get_domain_cache(domain)

        # Verificar si ya existe
        if not any(p["url"] == pdf.url for p in domain_cache["pdfs"]):
            domain_cache["pdfs"].append(pdf.to_dict())
            domain_cache["total_count"] = len(domain_cache["pdfs"])
            domain_cache["last_scan"] = datetime.now().isoformat()

    async def discover_pdfs(
        self,
        base_url: str,
        domain: str = None,
        strategies: List[str] = None
    ) -> List[DiscoveredPDF]:
        """
        Descubre PDFs usando estrategia en cascada.

        Args:
            base_url: URL base del sitio
            domain: Dominio (se extrae de base_url si no se provee)
            strategies: Lista de estrategias a usar (default: todas)

        Returns:
            Lista de PDFs únicos descubiertos (sin duplicados con cache)
        """
        if domain is None:
            domain = urlparse(base_url).netloc

        if strategies is None:
            strategies = ["sitemap", "google_search", "crawling"]

        console.print(f"\n[cyan]🔍 Descubriendo PDFs en {domain}...[/cyan]")

        all_pdfs: List[DiscoveredPDF] = []
        seen_urls: Set[str] = set()

        # Leer URLs ya procesadas del cache
        domain_cache = self._get_domain_cache(domain)
        cached_urls = {p["url"] for p in domain_cache["pdfs"]}
        console.print(f"[dim]  Cache: {len(cached_urls)} PDFs ya procesados[/dim]")

        # 1. Sitemap
        if "sitemap" in strategies:
            console.print("[dim]  → Estrategia 1: Sitemap XML[/dim]")
            sitemap_pdfs = await self._from_sitemap(base_url, domain)
            new_sitemap = [p for p in sitemap_pdfs if p.url not in cached_urls]
            console.print(f"[green]    ✓ Sitemap: {len(sitemap_pdfs)} PDFs ({len(new_sitemap)} nuevos)[/green]")
            all_pdfs.extend(new_sitemap)
            seen_urls.update(p.url for p in sitemap_pdfs)

        # 2. Google Search (SerpAPI)
        if "google_search" in strategies and self.serpapi_key:
            remaining = self.max_results - len(all_pdfs)
            if remaining > 0:
                console.print("[dim]  → Estrategia 2: Google Search (SerpAPI)[/dim]")
                google_pdfs = await self._from_google_search(domain, max_results=remaining)
                new_google = [p for p in google_pdfs if p.url not in cached_urls and p.url not in seen_urls]
                console.print(f"[green]    ✓ Google: {len(google_pdfs)} PDFs ({len(new_google)} nuevos)[/green]")
                all_pdfs.extend(new_google)
                seen_urls.update(p.url for p in google_pdfs)

        # 3. Crawling (solo si necesario)
        if "crawling" in strategies:
            remaining = self.max_results - len(all_pdfs)
            if remaining > 0:
                console.print("[dim]  → Estrategia 3: Crawling de páginas[/dim]")
                crawl_pdfs = await self._from_crawling(base_url, domain, max_results=remaining)
                new_crawl = [p for p in crawl_pdfs if p.url not in cached_urls and p.url not in seen_urls]
                console.print(f"[green]    ✓ Crawling: {len(crawl_pdfs)} PDFs ({len(new_crawl)} nuevos)[/green]")
                all_pdfs.extend(new_crawl)
                seen_urls.update(p.url for p in crawl_pdfs)

        # Guardar nuevos PDFs en cache
        for pdf in all_pdfs:
            self._add_to_cache(pdf)

        self._save_cache()

        # Resumen
        console.print(f"\n[bold cyan]📊 Resumen del descubrimiento:[/bold cyan]")
        console.print(f"  Total PDFs descubiertos: {len(all_pdfs)}")
        console.print(f"  PDFs ya procesados (cache): {len(cached_urls)}")
        console.print(f"  Total en dominio: {len(cached_urls) + len(all_pdfs)}")

        return all_pdfs

    async def _from_sitemap(self, base_url: str, domain: str) -> List[DiscoveredPDF]:
        """Descubre PDFs desde sitemap.xml"""
        pdfs = []

        try:
            # Intentar sitemap estándar
            sitemap_urls = [
                f"{base_url.rstrip('/')}/sitemap.xml",
                f"{base_url.rstrip('/')}/sitemap_index.xml",
                f"{base_url.rstrip('/')}/wp-sitemap.xml",
            ]

            for sitemap_url in sitemap_urls:
                try:
                    response = await self.client.get(sitemap_url)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, 'xml')
                    urls = soup.find_all('loc')

                    for url_tag in urls:
                        url = url_tag.text
                        if url.endswith('.pdf'):
                            pdfs.append(self._create_pdf_entry(url, domain, "sitemap"))

                    if pdfs:
                        break  # Encontrar PDFs, no seguir buscando

                except Exception:
                    continue

        except Exception as e:
            console.print(f"[dim]    No se pudo acceder al sitemap: {e}[/dim]")

        return pdfs[:self.max_results]

    async def _from_google_search(
        self,
        domain: str,
        max_results: int = 50
    ) -> List[DiscoveredPDF]:
        """
        Descubre PDFs usando Google Search vía SerpAPI.

        Usa el plan free de SerpAPI (250 búsquedas/mes).
        Cada búsqueda retorna hasta 100 resultados.

        Args:
            domain: Dominio a buscar
            max_results: Máximo de PDFs a retornar

        Returns:
            Lista de PDFs descubiertos
        """
        if not self.serpapi_key:
            console.print("[yellow]    ⚠️ SerpAPI key no configurada[/yellow]")
            return []

        pdfs = []
        search_queries = [
            f"site:{domain} filetype:pdf ordenanza",
            f"site:{domain} filetype:pdf decreto",
            f"site:{domain} filetype:pdf resolucion",
            f"site:{domain} filetype:pdf boletin oficial",
            f"site:{domain} filetype:pdf normativa",
        ]

        results_per_page = 20  # SerpAPI free plan
        max_searches = min(5, max_results // results_per_page + 1)

        for i, query in enumerate(search_queries[:max_searches]):
            if len(pdfs) >= max_results:
                break

            try:
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": results_per_page,
                }

                response = await self.client.get(
                    "https://serpapi.com/search",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                # Extraer resultados (PDF links)
                if "organic_results" in data:
                    for result in data["organic_results"]:
                        if len(pdfs) >= max_results:
                            break

                        link = result.get("link", "")
                        if link.endswith(".pdf"):
                            # Extraer título del resultado
                            title = result.get("title", "")
                            pdf = DiscoveredPDF(
                                url=link,
                                domain=domain,
                                found_date=datetime.now().isoformat(),
                                source="google_search",
                                title=title
                            )
                            pdfs.append(pdf)

                console.print(f"[dim]    Query {i+1}: '{query[:40]}...' → {len([r for r in data.get('organic_results', []) if r.get('link', '').endswith('.pdf')])} PDFs[/dim]")

            except Exception as e:
                console.print(f"[yellow]    Error en búsqueda {i+1}: {e}[/yellow]")
                continue

        return pdfs[:max_results]

    async def _from_crawling(
        self,
        base_url: str,
        domain: str,
        max_results: int = 50,
        max_depth: int = 2
    ) -> List[DiscoveredPDF]:
        """
        Descubre PDFs haciendo crawling de páginas.

        Busca enlaces a PDFs en las páginas del sitio.

        Args:
            base_url: URL base
            domain: Dominio para verificar mismos sitio
            max_results: Máximo de PDFs a encontrar
            max_depth: Profundidad máxima de crawling

        Returns:
            Lista de PDFs descubiertos
        """
        pdfs = []
        visited: Set[str] = set()
        to_visit: List[str] = [base_url]

        while to_visit and len(pdfs) < max_results:
            url = to_visit.pop(0)
            if url in visited:
                continue

            visited.add(url)

            try:
                response = await self.client.get(url)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')

                # Buscar enlaces a PDFs
                for link in soup.find_all('a', href=True):
                    href = link['href']

                    if href.endswith('.pdf'):
                        full_url = urljoin(base_url, href)

                        # Verificar mismo dominio
                        if urlparse(full_url).netloc == domain:
                            if not any(p.url == full_url for p in pdfs):
                                pdfs.append(self._create_pdf_entry(full_url, domain, "crawling"))

                # Agregar enlaces internos para seguir crawling
                if len(visited) < 50:  # Limitar páginas visitadas
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(base_url, href)

                        if urlparse(full_url).netloc == domain:
                            if full_url not in visited and full_url not in to_visit:
                                # Filtrar URLs relevantes
                                if any(keyword in full_url.lower() for keyword in
                                       ['normativa', 'ordenanza', 'decreto', 'boletin', 'resolucion']):
                                    to_visit.append(full_url)

            except Exception as e:
                console.print(f"[dim]    Error crawling {url[:50]}...: {e}[/dim]")
                continue

        return pdfs[:max_results]

    def _create_pdf_entry(
        self,
        url: str,
        domain: str,
        source: str
    ) -> DiscoveredPDF:
        """Crea una entrada de PDF descubierto"""
        # Extraer título del filename
        filename = url.split('/')[-1]
        title = filename.replace('.pdf', '').replace('-', ' ').replace('_', ' ')

        return DiscoveredPDF(
            url=url,
            domain=domain,
            found_date=datetime.now().isoformat(),
            source=source,
            title=title
        )

    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del cache"""
        stats = {
            "total_domains": len(self.cache),
            "total_pdfs": sum(d["total_count"] for d in self.cache.values()),
            "domains": {}
        }

        for domain, data in self.cache.items():
            stats["domains"][domain] = {
                "total_pdfs": data["total_count"],
                "last_scan": data["last_scan"]
            }

        return stats


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def discover_and_save(
    base_url: str,
    serpapi_key: str = None,
    max_results: int = 100
) -> List[DiscoveredPDF]:
    """
    Función de conveniencia para descubrir y guardar PDFs.

    Args:
        base_url: URL base del sitio
        serpapi_key: API key de SerpAPI (opcional)
        max_results: Máximo de PDFs a descubrir

    Returns:
        Lista de PDFs descubiertos
    """
    discovery = PDFDiscovery(serpapi_key=serpapi_key, max_results=max_results)
    try:
        domain = urlparse(base_url).netloc
        pdfs = await discovery.discover_pdfs(base_url, domain)
        return pdfs
    finally:
        await discovery.close()


if __name__ == "__main__":
    import asyncio

    async def main():
        # Ejemplo de uso
        serpapi_key = os.getenv("SERPAPI_KEY")

        discovery = PDFDiscovery(serpapi_key=serpapi_key, max_results=50)
        try:
            pdfs = await discovery.discover_pdfs(
                "https://boletin.casares.gob.ar",
                strategies=["google_search"]  # Solo Google para empezar
            )

            console.print(f"\n[green]✓ {len(pdfs)} PDFs descubiertos[/green]")

            # Mostrar tabla
            table = Table(title="PDFs Descubiertos")
            table.add_column("URL", style="cyan")
            table.add_column("Fuente")
            table.add_column("Título")

            for pdf in pdfs[:10]:  # Primeros 10
                table.add_row(pdf.url[:60], pdf.source, pdf.title or "N/A")

            console.print(table)

        finally:
            await discovery.close()

    asyncio.run(main())
