#!/usr/bin/env python3
"""
utils/state_tracker.py

Tracker unificado de estado de scraping.

Reemplaza los múltiples sistemas de tracking (.progress.json, _procesamiento.json,
_pdfs_grandes_pending.txt) con un único archivo de estado.

@version 2.0.0
@created 2026-02-02
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class StateTracker:
    """
    Tracker unificado de estado de scraping.

    Mantiene un único archivo .categoria_state.json con:
    - URLs procesadas
    - Estado de cada PDF (pending, processed, error, skipped)
    - Rutas a archivos PDF y JSON
    - Estadísticas

    Formato del archivo:
    {
      "municipio": "Carlos Tejedor",
      "categoria": "balances",
      "updated_at": "2026-02-02T19:30:00",
      "stats": {...},
      "files": {
        "hash_url": {
          "url": "...",
          "status": "processed",
          "pdf_path": "pdfs/...",
          "json_path": "...",
          "processed_at": "..."
        }
      }
    }
    """

    def __init__(self, municipio: str, categoria: str, output_dir: Path = None):
        """
        Inicializa el tracker para un municipio y categoría.

        Args:
            municipio: Nombre del municipio
            categoria: Categoría (balances, presupuestos, etc.)
            output_dir: Directorio de salida (por defecto: boletines/{municipio}/)
        """
        from config import BOLETINES_DIR

        self.municipio = municipio
        self.categoria = categoria

        if output_dir is None:
            # Convertir a slug
            municipio_slug = municipio.lower().replace(" ", "_")
            output_dir = BOLETINES_DIR / municipio_slug

        self.output_dir = Path(output_dir)
        self.state_file = self.output_dir / f".{categoria}_state.json"

        # Crear directorio si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Cargar estado existente
        self.data = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Carga estado desde JSON o retorna estructura vacía."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # Estructura vacía
        return {
            "municipio": self.municipio,
            "categoria": self.categoria,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stats": {
                "total": 0,
                "processed": 0,
                "pending": 0,
                "errors": 0,
                "skipped": 0
            },
            "files": {}
        }

    def _save_state(self):
        """Guarda estado a JSON."""
        self.data["updated_at"] = datetime.now().isoformat()

        # Recalcular estadísticas
        files = list(self.data["files"].values())
        self.data["stats"]["total"] = len(files)
        self.data["stats"]["processed"] = sum(1 for f in files if f.get("status") == "processed")
        self.data["stats"]["pending"] = sum(1 for f in files if f.get("status") == "pending")
        self.data["stats"]["errors"] = sum(1 for f in files if f.get("status") == "error")
        self.data["stats"]["skipped"] = sum(1 for f in files if f.get("status") == "skipped")

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _get_url_hash(self, url: str) -> str:
        """Genera hash único para una URL."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def is_processed(self, url: str) -> bool:
        """
        Verifica si una URL ya fue procesada.

        Args:
            url: URL del PDF

        Returns:
            True si ya fue procesada exitosamente
        """
        url_hash = self._get_url_hash(url)
        file_data = self.data["files"].get(url_hash, {})
        return file_data.get("status") == "processed"

    def get_status(self, url: str) -> str:
        """
        Retorna el estado de una URL.

        Args:
            url: URL del PDF

        Returns:
            Estado (pending, processed, error, skipped) o "unknown"
        """
        url_hash = self._get_url_hash(url)
        return self.data["files"].get(url_hash, {}).get("status", "unknown")

    def add_url(
        self,
        url: str,
        status: str = "pending",
        pdf_path: str = "",
        json_path: str = "",
        error: str = ""
    ) -> None:
        """
        Agrega o actualiza una URL en el tracker.

        Args:
            url: URL del PDF
            status: Estado (pending, processed, error, skipped)
            pdf_path: Ruta al PDF guardado
            json_path: Ruta al JSON generado
            error: Mensaje de error (si aplica)
        """
        url_hash = self._get_url_hash(url)

        # Obtener datos existentes o crear nuevos
        if url_hash in self.data["files"]:
            file_data = self.data["files"][url_hash]
        else:
            file_data = {
                "url": url,
                "status": "pending",
                "added_at": datetime.now().isoformat()
            }

        # Actualizar campos
        if status:
            file_data["status"] = status
        if status == "processed":
            file_data["processed_at"] = datetime.now().isoformat()
        if pdf_path:
            file_data["pdf_path"] = pdf_path
        if json_path:
            file_data["json_path"] = json_path
        if error:
            file_data["error"] = error
        elif status == "processed":
            file_data.pop("error", None)

        self.data["files"][url_hash] = file_data
        self._save_state()

    def mark_processed(
        self,
        url: str,
        pdf_path: str = "",
        json_path: str = ""
    ) -> None:
        """
        Marca una URL como procesada.

        Args:
            url: URL del PDF
            pdf_path: Ruta al PDF guardado
            json_path: Ruta al JSON generado
        """
        self.add_url(url, status="processed", pdf_path=pdf_path, json_path=json_path)

    def mark_pending(self, url: str, reason: str = "") -> None:
        """
        Marca una URL como pendiente.

        Args:
            url: URL del PDF
            reason: Razón para estar pendiente
        """
        self.add_url(url, status="pending")

        if reason:
            url_hash = self._get_url_hash(url)
            self.data["files"][url_hash]["reason"] = reason
            self._save_state()

    def mark_error(self, url: str, error: str) -> None:
        """
        Marca una URL con error.

        Args:
            url: URL del PDF
            error: Mensaje de error
        """
        self.add_url(url, status="error", error=error)

    def mark_skipped(self, url: str, reason: str = "") -> None:
        """
        Marca una URL como saltada.

        Args:
            url: URL del PDF
            reason: Razón del salto
        """
        self.add_url(url, status="skipped")

        if reason:
            url_hash = self._get_url_hash(url)
            self.data["files"][url_hash]["skip_reason"] = reason
            self._save_state()

    def get_stats(self) -> Dict[str, Any]:
        """Retorna las estadísticas actuales."""
        return self.data["stats"]

    def get_pending_urls(self) -> List[str]:
        """Retorna la lista de URLs pendientes."""
        return [
            f["url"]
            for f in self.data["files"].values()
            if f.get("status") == "pending"
        ]

    def get_processed_urls(self) -> List[str]:
        """Retorna la lista de URLs procesadas."""
        return [
            f["url"]
            for f in self.data["files"].values()
            if f.get("status") == "processed"
        ]

    def get_skipped_urls(self) -> List[Dict[str, Any]]:
        """Retorna la lista de URLs saltadas con info."""
        return [
            {**f, "url_hash": k}
            for k, f in self.data["files"].items()
            if f.get("status") == "skipped"
        ]

    def get_error_urls(self) -> List[Dict[str, Any]]:
        """Retorna la lista de URLs con errores."""
        return [
            {**f, "url_hash": k}
            for k, f in self.data["files"].items()
            if f.get("status") == "error"
        ]

    def get_files_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Retorna archivos filtrados por estado."""
        return [
            {**f, "url_hash": k}
            for k, f in self.data["files"].items()
            if f.get("status") == status
        ]

    def print_summary(self):
        """Imprime un resumen en consola."""
        stats = self.get_stats()
        print(f"\n📊 Estado de Scraping - {self.municipio} ({self.categoria})")
        print(f"   Total: {stats['total']}")
        print(f"   ✅ Procesados: {stats['processed']}")
        print(f"   ⏳ Pendientes: {stats['pending']}")
        print(f"   ❌ Errores: {stats['errors']}")
        print(f"   ⊘ Saltados: {stats['skipped']}")
        print(f"   📁 Estado: {self.state_file}")

    def generate_markdown_report(self) -> str:
        """Genera reporte Markdown del estado."""
        lines = [
            f"# Tabla de Procesamiento - {self.municipio}",
            f"**Categoría:** {self.categoria}",
            "",
            f"**Última actualización:** {self.data['updated_at']}",
            "",
            "## Resumen",
            "",
            f"| Total | Procesados | Pendientes | Errores | Saltados |",
            f"|-------|-------------|------------|--------|----------|",
        ]

        stats = self.get_stats()
        lines.append(f"| {stats['total']} | {stats['processed']} | {stats['pending']} | {stats['errors']} | {stats['skipped']} |")
        lines.extend([
            "",
            "## Detalle de Archivos",
            "",
            "| Archivo | Estado | Fecha | PDF | JSON | Errores |",
            "|---------|--------|-------|-----|------|---------|"
        ])

        # Ordenar archivos: primero pendientes, luego por fecha
        files = list(self.data["files"].values())
        files.sort(key=lambda f: (
            f.get("status") != "pending",
            f.get("processed_at", ""),
        ))

        for f in files:
            # Icono de estado
            status = f.get("status", "unknown")
            if status == "processed":
                status_icon = "✅"
            elif status == "pending":
                status_icon = "⏳"
            elif status == "error":
                status_icon = "❌"
            elif status == "skipped":
                status_icon = "⊘"
            else:
                status_icon = "❓"

            # Nombre de archivo (desde URL)
            url = f.get("url", "")
            filename = url.split('/')[-1][:40] if url else "Unknown"

            # Fecha
            processed_at = f.get("processed_at", "-")
            if processed_at and processed_at != "-":
                try:
                    dt = datetime.fromisoformat(processed_at)
                    processed_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            # PDF
            pdf_path = f.get("pdf_path", "")
            pdf_status = "✅" if pdf_path else "❌"

            # JSON
            json_path = f.get("json_path", "")
            json_status = "✅" if json_path else "❌"

            # Errores
            error = f.get("error", "") or f.get("skip_reason", "") or "-"

            lines.append(
                f"| {filename} | {status_icon} {status} | {processed_at} | {pdf_status} | {json_status} | {error} |"
            )

        return "\n".join(lines)

    def save_markdown_report(self, output_path: Path = None) -> Path:
        """
        Guarda el reporte Markdown.

        Args:
            output_path: Ruta de salida (por defecto: _procesamiento.md)

        Returns:
            Ruta al archivo MD generado
        """
        if output_path is None:
            output_path = self.output_dir / "_procesamiento.md"

        md_content = self.generate_markdown_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        return output_path


def get_state_tracker(municipio: str, categoria: str) -> StateTracker:
    """
    Obtiene el tracker para un municipio y categoría.

    Args:
        municipio: Nombre del municipio
        categoria: Categoría (balances, presupuestos, etc.)

    Returns:
        StateTracker instance
    """
    return StateTracker(municipio, categoria)
