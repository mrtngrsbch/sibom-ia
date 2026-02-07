#!/usr/bin/env python3
"""
core/command_runner.py

Sistema unificado de salida para comandos CLI.

Proporciona:
- ExecutionSummary: Context Manager para tracking y resúmenes (sync + async)
- StartupPanel: Panel de inicio estandarizado
- Manejo centralizado de errores comunes

@version 1.0.0
@created 2026-02-02
"""

import sys
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CommandMetrics:
    """Métricas coleccionadas durante la ejecución."""
    successes: int = 0
    errors: int = 0
    skipped: int = 0
    files: Dict[str, int] = field(default_factory=dict)
    custom: Dict[str, Any] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        return self.successes + self.errors + self.skipped


# ============================================================================
# STARTUP PANEL
# ============================================================================

class StartupPanel:
    """Panel de inicio con información del comando."""

    def __init__(
        self,
        title: str,
        description: str = "",
        details: Dict[str, Any] = None
    ):
        self.title = title
        self.description = description
        self.details = details or {}

    def show(self):
        """Muestra el panel de inicio."""
        lines = [f"[bold cyan]{self.title}[/bold cyan]"]

        if self.description:
            lines.append(self.description)

        if self.details:
            lines.append("")
            for key, value in self.details.items():
                lines.append(f"[dim]{key}:[/dim] {value}")

        console.print()
        console.print(Panel.fit(
            "\n".join(lines),
            border_style="cyan"
        ))
        console.print()


# ============================================================================
# EXECUTION SUMMARY
# ============================================================================

class ExecutionSummary:
    """
    Context Manager para trackear métricas y mostrar resumen.

    Compatible con sync Y async:
        with ExecutionSummary("cmd", "target") as s:   # sync
        async with ExecutionSummary("cmd", "target") as s:  # async

    Uso:
        with ExecutionSummary("SIBOM", "Carlos Tejedor") as s:
            s.add_success(5)
            s.add_file("JSON", 5)
            s.add_error(1)
        # Resumen automático al salir
    """

    def __init__(
        self,
        command: str,
        target: str = "",
        show_startup: bool = True,
        startup_details: Dict[str, Any] = None
    ):
        self.command = command
        self.target = target
        self.show_startup = show_startup
        self.startup_details = startup_details or {}

        # Timing
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        # Métricas
        self._metrics = CommandMetrics()

    # --- Context Manager Protocol (Sync) ---

    def __enter__(self):
        if self.show_startup:
            self._show_startup()
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if exc_val is not None:
            self._handle_error(exc_val)
        self.display()
        return False  # No suprimir excepciones

    # --- Async Context Manager Protocol ---

    async def __aenter__(self):
        if self.show_startup:
            self._show_startup()
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if exc_val is not None:
            self._handle_error(exc_val)
        self.display()
        return False

    # --- Métodos de Métricas ---

    def add_file(self, file_type: str, count: int = 1):
        """Registra archivos generados."""
        self._metrics.files[file_type] = self._metrics.files.get(file_type, 0) + count

    def add_success(self, count: int = 1):
        """Registra éxitos."""
        self._metrics.successes += count

    def add_error(self, count: int = 1, message: str = ""):
        """Registra errores."""
        self._metrics.errors += count
        if message:
            self._metrics.error_messages.append(message)

    def add_skipped(self, count: int = 1):
        """Registra items saltados."""
        self._metrics.skipped += count

    def set_metric(self, key: str, value: Any):
        """Define una métrica personalizada."""
        self._metrics.custom[key] = value

    # --- Display ---

    def _show_startup(self):
        """Muestra el panel de inicio."""
        details = {}
        if self.target:
            details["Objetivo"] = self.target
        details.update(self.startup_details)

        panel = StartupPanel(
            title=self.command,
            details=details if details else None
        )
        panel.show()

    def _handle_error(self, error: Exception):
        """Maneja errores específicos."""
        error_type = type(error).__name__

        # CreditExhaustedError - ya manejado por el caller, solo registrar
        if error_type == "CreditExhaustedError":
            self.add_error(1, str(error))
        else:
            self.add_error(1, str(error))

    def _get_llm_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de LLM."""
        try:
            from utils.llm_tracker import get_llm_tracker
            tracker = get_llm_tracker()
            return tracker.get_stats(days=1)
        except Exception:
            return {}

    def display(self):
        """Muestra el resumen de ejecución."""
        duration = self.duration
        llm = self._get_llm_stats()

        console.print()
        console.print(Panel(
            self._build_summary_table(duration, llm),
            title="[bold green]📊 Resumen de Ejecución[/bold green]",
            border_style="green",
            padding=(1, 1)
        ))

    def _build_summary_table(self, duration: float, llm: Dict) -> Table:
        """Construye la tabla de resumen."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right")

        # Comando y objetivo
        table.add_row("[dim]Comando[/dim]", f"[bold]{self.command}[/bold]")
        if self.target:
            table.add_row("[dim]Objetivo[/dim]", self.target)

        # Tiempo
        table.add_row("", "")

        # Hora de inicio
        if self.start_time:
            start_dt = dt.fromtimestamp(self.start_time)
            table.add_row("🕐 Inicio", start_dt.strftime("%H:%M:%S"))

        # Hora de fin
        if self.end_time:
            end_dt = dt.fromtimestamp(self.end_time)
            table.add_row("🕐 Fin", end_dt.strftime("%H:%M:%S"))

        # Duración
        if duration < 60:
            table.add_row("⏱️  Duración", f"{duration:.1f}s")
        else:
            mins = int(duration // 60)
            secs = int(duration % 60)
            table.add_row("⏱️  Duración", f"{mins}m {secs}s")

        # Resultados
        if self._metrics.total_items > 0:
            table.add_row("", "")
            table.add_row("📋 Resultados", "")
            if self._metrics.successes > 0:
                table.add_row("  ✓ Exitosos", f"[green]{self._metrics.successes}[/green]")
            if self._metrics.skipped > 0:
                table.add_row("  ⊘ Saltados", f"[dim]{self._metrics.skipped}[/dim]")
            if self._metrics.errors > 0:
                table.add_row("  ✗ Errores", f"[red]{self._metrics.errors}[/red]")
            table.add_row("  → Total", str(self._metrics.total_items))

        # Archivos
        if self._metrics.files:
            table.add_row("", "")
            table.add_row("📁 Archivos", "")
            for file_type, count in sorted(self._metrics.files.items()):
                table.add_row(f"  - {file_type}", str(count))

        # LLM Stats
        total_calls = llm.get('total', {}).get('calls', 0)
        if total_calls > 0:
            table.add_row("", "")
            table.add_row("🤖 LLM Stats", "")
            table.add_row("  Calls", str(total_calls))
            table.add_row("  Tokens", f"{llm['total'].get('total_tokens', 0):,}")
            total_cost = llm['total'].get('cost', 0)
            if total_cost > 0:
                table.add_row("  Costo", f"[yellow]${total_cost:.4f}[/yellow]")

            # Top modelos
            models = llm.get('models', {})
            if models:
                sorted_models = sorted(
                    models.items(),
                    key=lambda x: x[1].get('recalculated_cost', x[1]['cost']),
                    reverse=True
                )
                for model_id, data in sorted_models[:3]:
                    cost = data.get('recalculated_cost', data['cost'])
                    if cost > 0:
                        name = data.get('display_name', model_id.split('/')[-1])[:20]
                        table.add_row(f"  • {name}", f"${cost:.4f}")

        # Métricas personalizadas
        if self._metrics.custom:
            table.add_row("", "")
            table.add_row("📈 Métricas", "")
            for key, value in self._metrics.custom.items():
                table.add_row(f"  - {key}", str(value))

        return table

    @property
    def duration(self) -> float:
        """Retorna la duración de la ejecución."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0


# ============================================================================
# ERROR HANDLERS
# ============================================================================

class CreditExhaustedHandler:
    """Manejador centralizado para errores de crédito agotado."""

    @staticmethod
    def handle(error: Exception, show_solution: bool = True):
        """Muestra mensaje de error y solución."""
        console.print("\n[bold red]⛔ DETENIENDO SCRAPER POR FALTA DE CRÉDITOS ⛔[/bold red]")
        console.print(f"[red]{error}[/red]")

        if show_solution:
            console.print("\n[yellow]💡 Solución:[/yellow]")
            console.print("  1. Agrega créditos a tu cuenta de OpenRouter")
            console.print("  2. El progreso se guardó automáticamente")
            console.print("  3. Vuelve a ejecutar el mismo comando para continuar")
