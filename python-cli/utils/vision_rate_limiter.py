#!/usr/bin/env python3
"""
vision_rate_limiter.py

Control de límites diarios para Vision API (OpenRouter).
Previene exceder el límite de 1000 requests/día.

@version 1.0.0
@created 2026-01-29
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class VisionRateLimiter:
    """
    Controla el uso de Vision API para no exceder límites diarios.

    Guarda un archivo JSON con el registro de uso por día.
    """

    def __init__(
        self,
        cache_dir: Path = None,
        daily_limit: int = 1000,
        safety_margin: float = 0.9  # Usar solo 90% del límite
    ):
        """
        Args:
            cache_dir: Directorio para guardar el registro
            daily_limit: Límite diario de requests (default: 1000)
            safety_margin: Margen de seguridad (0.9 = usar solo 900)
        """
        from config import CACHE_DIR

        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        self.cache_file = self.cache_dir / "vision_api_usage.json"
        self.daily_limit = daily_limit
        self.safety_margin = safety_margin
        self.effective_limit = int(daily_limit * safety_margin)

        # Cargar registro existente
        self.usage = self._load_usage()

    def _load_usage(self) -> dict:
        """Carga el registro de uso desde el archivo"""
        if self.cache_file.exists():
            try:
                with self.cache_file.open('r') as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "total_requests": 0,
            "days": {}
        }

    def _save_usage(self):
        """Guarda el registro de uso"""
        with self.cache_file.open('w') as f:
            json.dump(self.usage, f, indent=2)

    def _get_today_key(self) -> str:
        """Retorna la clave de hoy"""
        return date.today().isoformat()

    def _get_today_count(self) -> int:
        """Retorna el número de requests hoy"""
        today = self._get_today_key()
        return self.usage["days"].get(today, 0)

    def _reset_if_new_day(self):
        """Resetea el contador si es un día nuevo"""
        today = self._get_today_key()

        # Eliminar días antiguos (más de 7 días)
        old_days = list(self.usage["days"].keys())
        for day in old_days:
            if day != today:
                del self.usage["days"][day]

    def can_request(self) -> bool:
        """
        Verifica si se puede hacer una request.

        Returns:
            True si hay capacidad, False si se alcanzó el límite
        """
        self._reset_if_new_day()
        today_count = self._get_today_count()

        return today_count < self.effective_limit

    def get_remaining(self) -> int:
        """Retorna el número de requests restantes hoy"""
        self._reset_if_new_day()
        today_count = self._get_today_count()
        return max(0, self.effective_limit - today_count)

    def get_today_count(self) -> int:
        """Retorna el número de requests hechos hoy"""
        self._reset_if_new_day()
        return self._get_today_count()

    def record_request(self):
        """Registra que se hizo una request"""
        self._reset_if_new_day()

        today = self._get_today_key()
        self.usage["days"][today] = self.usage["days"].get(today, 0) + 1
        self.usage["total_requests"] += 1

        self._save_usage()

    def get_stats(self) -> dict:
        """Retorna estadísticas de uso"""
        self._reset_if_new_day()
        today = self._get_today_key()

        return {
            "today": self.usage["days"].get(today, 0),
            "remaining": self.get_remaining(),
            "limit": self.effective_limit,
            "total_all_time": self.usage["total_requests"],
            "date": today
        }

    def check_and_request(self) -> bool:
        """
        Verifica si hay capacidad y registra la request.

        Returns:
            True si se puede proceder, False si se alcanzó el límite

        Imprime un warning si se está cerca del límite (>80%)
        """
        if not self.can_request():
            stats = self.get_stats()
            console.print(
                f"[red]❌ Límite diario alcanzado: {stats['today']}/{stats['limit']}[/red]"
            )
            return False

        # Warning si estamos cerca del límite (>80%)
        remaining = self.get_remaining()
        if remaining < (self.effective_limit * 0.2):
            console.print(
                f"[yellow]⚠️ Vision API: {remaining} requests restantes hoy[/yellow]"
            )

        self.record_request()
        return True


# =============================================================================
# SINGLETON GLOBAL
# =============================================================================

_rate_limiter: Optional[VisionRateLimiter] = None


def get_rate_limiter() -> VisionRateLimiter:
    """Retorna el singleton del rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = VisionRateLimiter()
    return _rate_limiter


def check_vision_limit() -> bool:
    """
    Verifica si se puede usar Vision API.
    Convenience function para uso rápido.
    """
    return get_rate_limiter().check_and_request()


def get_vision_stats() -> dict:
    """Retorna estadísticas de uso de Vision API"""
    return get_rate_limiter().get_stats()


if __name__ == "__main__":
    # Test
    limiter = VisionRateLimiter(daily_limit=1000)

    stats = limiter.get_stats()
    console.print(f"[cyan]Estadísticas Vision API:[/cyan]")
    console.print(f"  Hoy: {stats['today']}")
    console.print(f"  Restantes: {stats['remaining']}")
    console.print(f"  Límite: {stats['limit']}")
    console.print(f"  Total histórico: {stats['total_all_time']}")
