#!/usr/bin/env python3
"""
utils/processing_tracker.py

Sistema de tracking de procesamiento de PDFs.

Mantiene una tabla Markdown con el estado de todos los PDFs:
- Procesados (Sí/No)
- Fecha y hora de procesamiento
- Modelo usado
- Páginas del PDF
- Tamaño del archivo
- Guardado en SQLite (Sí/No)
- Errores

@version 1.0.0
@created 2026-02-02
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


class ProcessingTracker:
    """
    Tracker del estado de procesamiento de PDFs.

    Mantiene dos archivos:
    1. _procesamiento.md - Tabla Markdown legible
    2. _procesamiento.json - Datos estructurados para consultas
    """

    def __init__(self, output_dir: Path):
        """
        Inicializa el tracker para un municipio.

        Args:
            output_dir: Directorio de salida (boletines/{municipio}/)
        """
        self.output_dir = Path(output_dir)
        self.md_file = self.output_dir / "_procesamiento.md"
        self.json_file = self.output_dir / "_procesamiento.json"

        # Crear directorio si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Cargar datos existentes
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        """Carga datos desde JSON o retorna estructura vacía."""
        if self.json_file.exists():
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass

        # Estructura vacía
        return {
            "municipio": self.output_dir.name,
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

    def _save_data(self):
        """Guarda datos a JSON."""
        self.data["updated_at"] = datetime.now().isoformat()

        # Recalcular estadísticas
        files = list(self.data["files"].values())
        self.data["stats"]["total"] = len(files)
        self.data["stats"]["processed"] = sum(1 for f in files if f.get("status") == "processed")
        self.data["stats"]["pending"] = sum(1 for f in files if f.get("status") == "pending")
        self.data["stats"]["errors"] = sum(1 for f in files if f.get("status") == "error")
        self.data["stats"]["skipped"] = sum(1 for f in files if f.get("status") == "skipped")

        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _generate_markdown(self) -> str:
        """Genera la tabla Markdown desde los datos."""
        lines = [
            f"# Tabla de Procesamiento - {self.data['municipio']}",
            "",
            f"**Última actualización:** {self.data['updated_at']}",
            "",
            "## Resumen",
            "",
            f"| Total | Procesados | Pendientes | Errores | Saltados |",
            f"|-------|-------------|------------|--------|----------|",
            f"| {self.data['stats']['total']} | {self.data['stats']['processed']} | {self.data['stats']['pending']} | {self.data['stats']['errors']} | {self.data['stats']['skipped']} |",
            "",
            "## Detalle de Archivos",
            "",
            "| Archivo | Estado | Fecha | Modelo | Páginas | Tamaño | SQLite | Errores |",
            "|---------|--------|-------|--------|---------|--------|--------|---------|"
        ]

        # Ordenar archivos: primero pendientes, luego por fecha
        files = list(self.data["files"].values())
        files.sort(key=lambda f: (
            f.get("status") != "pending",  # Pendientes primero
            f.get("processed_at", ""),      # Luego por fecha
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
            filename = f.get("filename", f.get("url", "Unknown")[-50:])
            if len(filename) > 40:
                filename = "..." + filename[-37:]

            # Fecha
            processed_at = f.get("processed_at", "-")
            if processed_at and processed_at != "-":
                try:
                    dt = datetime.fromisoformat(processed_at)
                    processed_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            # Modelo (acortar)
            model = f.get("model", "-")
            if "gemini" in model.lower():
                model = model.split("/")[-1][:15]

            # Páginas
            pages = f.get("page_count", "-")

            # Tamaño
            size_mb = f.get("size_mb", 0)
            if size_mb:
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "-"

            # SQLite
            sqlite = "✅" if f.get("saved_to_sqlite") else "❌"

            # Errores
            errors = f.get("error", "") or "-"

            lines.append(
                f"| {filename} | {status_icon} {status} | {processed_at} | {model} | {pages} | {size_str} | {sqlite} | {errors} |"
            )

        # PDFs grandes pendientes
        large_pdfs_file = self.output_dir / "_pdfs_grandes_pending.txt"
        if large_pdfs_file.exists():
            lines.extend([
                "",
                "## PDFs Grandes Pendientes",
                "",
                "Los siguientes PDFs fueron omitidos por superar el umbral de páginas:",
                ""
            ])

            with open(large_pdfs_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split(" | ")
                        if len(parts) >= 4:
                            lines.append(f"- [`{parts[3]}`]({parts[0]}) - {parts[1]} - {parts[2]}")

        lines.append("")  # Empty line at end

        return "\n".join(lines)

    def save(self):
        """Guarda tanto JSON como Markdown."""
        self._save_data()

        # Guardar Markdown
        md_content = self._generate_markdown()
        with open(self.md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

    def add_file(
        self,
        url: str,
        filename: str = "",
        status: str = "pending",
        page_count: int = 0,
        size_mb: float = 0,
        model: str = "",
        saved_to_sqlite: bool = False,
        error: str = ""
    ) -> None:
        """
        Agrega o actualiza un archivo en el tracker.

        Args:
            url: URL del PDF
            filename: Nombre del archivo (opcional)
            status: Estado (pending, processed, error, skipped)
            page_count: Número de páginas
            size_mb: Tamaño en MB
            model: Modelo usado
            saved_to_sqlite: Si se guardó en SQLite
            error: Mensaje de error (si aplica)
        """
        # Crear key única desde la URL
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

        # Obtener datos existentes o crear nuevos
        if url_hash in self.data["files"]:
            file_data = self.data["files"][url_hash]
        else:
            file_data = {
                "url": url,
                "filename": filename,
                "status": "pending",
                "added_at": datetime.now().isoformat()
            }

        # Actualizar campos
        if filename:
            file_data["filename"] = filename
        if status:
            file_data["status"] = status
        if status == "processed":
            file_data["processed_at"] = datetime.now().isoformat()
        if page_count:
            file_data["page_count"] = page_count
        if size_mb:
            file_data["size_mb"] = size_mb
        if model:
            file_data["model"] = model
        if saved_to_sqlite is not None:
            file_data["saved_to_sqlite"] = saved_to_sqlite
        if error:
            file_data["error"] = error
        elif status == "processed":
            file_data.pop("error", None)

        self.data["files"][url_hash] = file_data
        self.save()

    def mark_processed(
        self,
        url: str,
        model: str,
        page_count: int = 0,
        size_mb: float = 0,
        saved_to_sqlite: bool = False
    ) -> None:
        """Marca un archivo como procesado."""
        self.add_file(
            url=url,
            status="processed",
            page_count=page_count,
            size_mb=size_mb,
            model=model,
            saved_to_sqlite=saved_to_sqlite
        )

    def mark_error(self, url: str, error: str) -> None:
        """Marca un archivo con error."""
        self.add_file(url=url, status="error", error=error)

    def mark_skipped(self, url: str, reason: str = "") -> None:
        """Marca un archivo como saltado."""
        self.add_file(url=url, status="skipped", error=reason)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna las estadísticas actuales."""
        return self.data["stats"]

    def get_pending_files(self) -> List[Dict[str, Any]]:
        """Retorna la lista de archivos pendientes."""
        return [
            {**f, "url_hash": k}
            for k, f in self.data["files"].items()
            if f.get("status") == "pending"
        ]

    def print_summary(self):
        """Imprime un resumen en consola."""
        stats = self.get_stats()
        print(f"\n📊 Estado de Procesamiento - {self.data['municipio']}")
        print(f"   Total: {stats['total']}")
        print(f"   ✅ Procesados: {stats['processed']}")
        print(f"   ⏳ Pendientes: {stats['pending']}")
        print(f"   ❌ Errores: {stats['errors']}")
        print(f"   ⊘ Saltados: {stats['skipped']}")
        print(f"   📁 Ver detalles: {self.md_file}")


def get_tracker(municipio: str) -> ProcessingTracker:
    """
    Obtiene el tracker para un municipio.

    Args:
        municipio: Nombre del municipio (slug)

    Returns:
        ProcessingTracker instance
    """
    from config import BOLETINES_DIR

    # Convertir a slug
    municipio_slug = municipio.lower().replace(" ", "_")
    output_dir = BOLETINES_DIR / municipio_slug

    return ProcessingTracker(output_dir)
