"""Sistema de caché para imágenes satelitales.

Implementa FEAT-001: Caché de imágenes descargadas para evitar
descargas repetidas de las mismas imágenes Sentinel-2.
"""
from __future__ import annotations

import hashlib
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class ImageCache:
    """Caché para imágenes satelitales descargadas.

    Almacena bandas Sentinel-2 en disco para evitar descargarlas
    repetidamente. Cada entrada de caché incluye:
    - Los datos de las bandas (arrays numpy)
    - Metadatos (CRS, transform, fecha)
    - Timestamp de creación

    El caché usa una clave basada en:
    - ID del item STAC
    - BBOX de descarga
    - Hash de los parámetros
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        max_size_mb: float = 5000.0,
        ttl_days: int = 30,
    ):
        """Inicializa el caché.

        Args:
            cache_dir: Directorio donde almacenar el caché (default: logs/cache/)
            max_size_mb: Tamaño máximo del caché en MB
            ttl_days: Tiempo de vida en días para las entradas
        """
        if cache_dir is None:
            # Default: logs/cache/ dentro del proyecto sat-analysis
            cache_dir = Path(__file__).parent.parent.parent.parent / "logs" / "cache"

        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.ttl_days = ttl_days

        # Crear directorio si no existe
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Archivo de índice
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> dict[str, Any]:
        """Carga el índice del caché desde disco."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando índice de caché: {e}")
        return {}

    def _save_index(self):
        """Guarda el índice del caché a disco."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando índice de caché: {e}")

    def _generate_key(
        self,
        item_id: str,
        bbox: list[float] | None,
        geometry: dict | None,
    ) -> str:
        """Genera una clave única para la entrada de caché.

        Args:
            item_id: ID del item STAC
            bbox: BBOX de descarga
            geometry: Geometría de la parcela (opcional)

        Returns:
            Clave hash hexadecimal
        """
        # Crear string base para el hash
        key_parts = [item_id]

        if bbox is not None:
            key_parts.append(f"bbox:{bbox}")

        if geometry is not None:
            # Hash simple de la geometría
            geom_str = json.dumps(geometry, sort_keys=True)
            geom_hash = hashlib.md5(geom_str.encode()).hexdigest()[:8]
            key_parts.append(f"geom:{geom_hash}")

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Retorna la ruta del archivo para una clave dada."""
        return self.cache_dir / f"{key}.npz"

    def _is_expired(self, entry: dict[str, Any]) -> bool:
        """Verifica si una entrada de caché ha expirado."""
        if "created_at" not in entry:
            return True

        created_at = datetime.fromisoformat(entry["created_at"])
        age_days = (datetime.now() - created_at).days

        return age_days > self.ttl_days

    def get(
        self,
        item_id: str,
        bbox: list[float] | None = None,
        geometry: dict | None = None,
    ) -> dict[str, Any] | None:
        """Obtiene bandas desde el caché si existen.

        Args:
            item_id: ID del item STAC
            bbox: BBOX de descarga
            geometry: Geometría de la parcela (opcional)

        Returns:
            Diccionario con las bandas y metadatos, o None si no está en caché
        """
        key = self._generate_key(item_id, bbox, geometry)

        if key not in self.index:
            return None

        entry = self.index[key]

        # Verificar expiración
        if self._is_expired(entry):
            logger.info(f"Caché expirado para key={key[:8]}...")
            self.delete(key)
            return None

        # Cargar datos desde disco
        cache_path = self._get_cache_path(key)
        if not cache_path.exists():
            logger.warning(f"Archivo de caché no encontrado: {cache_path}")
            del self.index[key]
            self._save_index()
            return None

        try:
            data = np.load(cache_path, allow_pickle=True)

            # Retornar diccionario con bandas y metadatos
            result = {
                "b02": data["b02"],
                "b03": data["b03"],
                "b04": data["b04"],
                "b08": data["b08"],
                "b11": data["b11"],
                "b12": data["b12"],
                "crs": str(data["crs"]),
                "transform": tuple(data["transform"]),
                "shape": tuple(data["shape"]),
                "from_cache": True,
                "cache_key": key,
            }

            logger.info(f"✅ Caché HIT: {item_id} ({cache_path.stat().st_size / 1024 / 1024:.1f} MB)")
            return result

        except Exception as e:
            logger.error(f"Error cargando caché: {e}")
            return None

    def put(
        self,
        item_id: str,
        bands: dict[str, np.ndarray],
        crs: str,
        transform: tuple,
        bbox: list[float] | None = None,
        geometry: dict | None = None,
    ) -> bool:
        """Guarda bandas en el caché.

        Args:
            item_id: ID del item STAC
            bands: Diccionario con las bandas (b02, b03, b04, b08, b11, b12)
            crs: CRS de las bandas
            transform: Transform affine
            bbox: BBOX de descarga
            geometry: Geometría de la parcela (opcional)

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        key = self._generate_key(item_id, bbox, geometry)
        cache_path = self._get_cache_path(key)

        try:
            # Guardar arrays numpy comprimidos
            np.savez_compressed(
                cache_path,
                b02=bands["b02"],
                b03=bands["b03"],
                b04=bands["b04"],
                b08=bands["b08"],
                b11=bands["b11"],
                b12=bands["b12"],
                crs=crs,
                transform=transform,
                shape=bands["b02"].shape,
            )

            # Actualizar índice
            file_size_mb = cache_path.stat().st_size / 1024 / 1024

            self.index[key] = {
                "item_id": item_id,
                "created_at": datetime.now().isoformat(),
                "file_size_mb": file_size_mb,
                "bbox": bbox,
            }

            self._save_index()

            # Limpiar caché si excede el tamaño máximo
            self._cleanup_if_needed()

            logger.info(f"✅ Caché PUT: {item_id} ({file_size_mb:.1f} MB)")
            return True

        except Exception as e:
            logger.error(f"Error guardando en caché: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Elimina una entrada del caché.

        Args:
            key: Clave de la entrada a eliminar

        Returns:
            True si se eliminó correctamente
        """
        cache_path = self._get_cache_path(key)

        try:
            if cache_path.exists():
                cache_path.unlink()

            if key in self.index:
                del self.index[key]
                self._save_index()

            return True

        except Exception as e:
            logger.error(f"Error eliminando del caché: {e}")
            return False

    def _cleanup_if_needed(self):
        """Limpia entradas antiguas si el caché excede el tamaño máximo."""
        total_size = sum(e.get("file_size_mb", 0) for e in self.index.values())

        if total_size <= self.max_size_mb:
            return

        logger.info(f"Caché excede tamaño máximo ({total_size:.1f} MB > {self.max_size_mb} MB), limpiando...")

        # Ordenar por fecha de creación (más antiguas primero)
        entries = sorted(
            self.index.items(),
            key=lambda x: x[1].get("created_at", ""),
        )

        # Eliminar entradas hasta estar por debajo del límite
        for key, entry in entries:
            if total_size <= self.max_size_mb * 0.8:  # Dejar margen del 20%
                break

            size_mb = entry.get("file_size_mb", 0)
            if self.delete(key):
                total_size -= size_mb
                logger.info(f"  Eliminada entrada antigua: {key[:8]}... ({size_mb:.1f} MB)")

    def clear(self):
        """Limpia todo el caché."""
        for key in list(self.index.keys()):
            self.delete(key)

        logger.info("🗑️ Caché limpiado completamente")

    def stats(self) -> dict[str, Any]:
        """Retorna estadísticas del caché.

        Returns:
            Diccionario con estadísticas
        """
        total_size = sum(e.get("file_size_mb", 0) for e in self.index.values())
        entry_count = len(self.index)

        return {
            "entry_count": entry_count,
            "total_size_mb": total_size,
            "max_size_mb": self.max_size_mb,
            "usage_percentage": (total_size / self.max_size_mb * 100) if self.max_size_mb > 0 else 0,
            "cache_dir": str(self.cache_dir),
        }
