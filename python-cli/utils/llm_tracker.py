#!/usr/bin/env python3
"""
utils/llm_tracker.py

Sistema unificado de tracking de LLM usage.
Registra todas las llamadas a APIs de LLM (OpenRouter).

La configuración de modelos se lee desde config/models.yaml.

@version 2.0.0
@created 2026-01-30
@updated 2026-02-01 - Migración a models.yaml
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()


# ============================================================================
# CARGA DE CONFIGURACIÓN DESDE models.yaml
# ============================================================================

def _load_models_config() -> Dict[str, Any]:
    """
    Carga la configuración de modelos desde config/models.yaml.

    Returns:
        Dict con defaults, models, llm_models, script_models
    """
    config_path = Path(__file__).parent.parent / "config" / "models.yaml"

    if not config_path.exists():
        console.print("[yellow]⚠️  config/models.yaml no encontrado, usando defaults[/yellow]")
        return {
            "defaults": {"vision": "", "llm": ""},
            "models": [],
            "llm_models": [],
            "script_models": []
        }

    try:
        import yaml
        with config_path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        console.print("[yellow]⚠️  PyYAML no instalado, usando defaults[/yellow]")
        return {"defaults": {}, "models": [], "llm_models": [], "script_models": []}
    except Exception as e:
        console.print(f"[yellow]⚠️  Error cargando models.yaml: {e}[/yellow]")
        return {"defaults": {}, "models": [], "llm_models": [], "script_models": []}


# Cargar configuración al inicio
_MODELS_CONFIG = _load_models_config()


def _build_model_pricing_dict() -> Dict[str, Dict[str, Any]]:
    """
    Construye el diccionario MODEL_PRICING desde models.yaml.
    Compatible con ambos formatos: models (vision) y llm_models.
    """
    pricing = {}

    # Procesar modelos Vision (models)
    for model in _MODELS_CONFIG.get("models", []):
        model_id = model.get("id")
        if not model_id:
            continue

        pricing[model_id] = {
            "type": model.get("type", "vision"),
            "provider": model.get("provider", "openrouter"),
            "cost_per_million_input": model.get("input_price_usd", 0.0),
            "cost_per_million_output": model.get("output_price_usd", 0.0),
            "free": model.get("free", False),
            "display_name": model.get("name", model_id.split("/")[-1][:20]),
            "usage": model.get("notes", ""),
            "active": model.get("active", False),
            "tags": model.get("tags", []),
        }

    # Procesar modelos LLM (llm_models)
    for model in _MODELS_CONFIG.get("llm_models", []):
        model_id = model.get("id")
        if not model_id:
            continue

        pricing[model_id] = {
            "type": model.get("type", "llm"),
            "provider": model.get("provider", "openrouter"),
            "cost_per_million_input": model.get("input_price_usd", 0.0),
            "cost_per_million_output": model.get("output_price_usd", 0.0),
            "free": model.get("free", False),
            "display_name": model.get("name", model_id.split("/")[-1][:20]),
            "usage": model.get("notes", ""),
            "active": model.get("active", False),
            "tags": model.get("tags", []),
        }

    return pricing


# ============================================================================
# DICCIONARIO DE PRECIOS (construido desde models.yaml)
# ============================================================================
MODEL_PRICING = _build_model_pricing_dict()


# ============================================================================
# FUNCIONES DE CONSULTA DE CONFIGURACIÓN
# ============================================================================

def get_default_model(model_type: str = "vision") -> str:
    """
    Retorna el modelo por defecto para un tipo.

    Args:
        model_type: "vision" o "llm"

    Returns:
        ID del modelo por defecto (ej: "google/gemini-2.5-flash-lite-preview-09-2025")
    """
    defaults = _MODELS_CONFIG.get("defaults", {})
    return defaults.get(model_type, "")


def get_model_for_script(script: str, function: str = None) -> Optional[str]:
    """
    Busca qué modelo usa un script específico.

    Args:
        script: Nombre del script (ej: "vision_extractor.py")
        function: Nombre de la función (opcional)

    Returns:
        ID del modelo o None si no se encuentra
    """
    for mapping in _MODELS_CONFIG.get("script_models", []):
        if mapping.get("script") == script:
            if function is None or mapping.get("function") == function:
                return mapping.get("model_id")
    return None


def get_all_models() -> Dict[str, Dict[str, Any]]:
    """Retorna todos los modelos configurados."""
    return MODEL_PRICING.copy()


def reload_models_config() -> None:
    """
    Recarga la configuración desde models.yaml.
    Útil después de editar el archivo manualmente.
    """
    global _MODELS_CONFIG, MODEL_PRICING
    _MODELS_CONFIG = _load_models_config()
    MODEL_PRICING = _build_model_pricing_dict()
    console.print("[green]✓ Configuración de modelos recargada[/green]")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ModelCall:
    """Registro de una llamada a modelo LLM"""
    model: str
    task: str  # "vision", "sibom_parsing", "transparency", etc.
    input_tokens: int
    output_tokens: int
    timestamp: str
    success: bool = True
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class ModelStats:
    """Estadísticas agregadas por modelo"""
    model: str
    task: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0

    @property
    def display_name(self) -> str:
        config = MODEL_PRICING.get(self.model, {})
        return config.get("display_name", self.model.split("/")[-1][:20])

    @property
    def is_free(self) -> bool:
        config = MODEL_PRICING.get(self.model, {})
        return config.get("free", False)


# ============================================================================
# TRACKER PRINCIPAL
# ============================================================================

class LLMTracker:
    """
    Trackea todas las llamadas a APIs de LLM.

    Guarda registros en data/cache/llm_usage.json
    """

    def __init__(self, cache_dir: Path = None):
        """
        Args:
            cache_dir: Directorio para guardar el registro
        """
        from config import CACHE_DIR

        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        self.usage_file = self.cache_dir / "llm_usage.json"

        # Cargar registro existente
        self.data = self._load_usage()

    def _load_usage(self) -> dict:
        """Carga el registro de uso desde el archivo"""
        if self.usage_file.exists():
            try:
                with self.usage_file.open('r') as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "version": "1.0.0",
            "total_calls": 0,
            "total_cost": 0.0,
            "calls": [],  # Lista de ModelCall serializados
            "daily": {}   # {date: {model: {calls, tokens, cost}}}
        }

    def _save_usage(self):
        """Guarda el registro de uso"""
        with self.usage_file.open('w') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _get_today_key(self) -> str:
        """Retorna la clave de hoy"""
        return date.today().isoformat()

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calcula el costo de una llamada.

        Si el modelo no está en MODEL_PRICING, advierte y retorna 0.
        Esto previene que modelos aparezcan como "GRATIS" incorrectamente.
        """
        config = MODEL_PRICING.get(model)

        if config is None:
            # Modelo no configurado - advertir UNA vez
            if not hasattr(self, '_warned_models'):
                self._warned_models = set()
            if model not in self._warned_models:
                console.print(
                    f"[yellow]⚠️  Modelo '{model}' no está en config/models.yaml[/yellow]"
                )
                console.print("[dim]    Agrega el modelo para tracking correcto de costos[/dim]")
                self._warned_models.add(model)
            return 0.0

        if config.get("free", False):
            return 0.0

        cost_input = (input_tokens / 1_000_000) * config.get("cost_per_million_input", 0)
        cost_output = (output_tokens / 1_000_000) * config.get("cost_per_million_output", 0)

        return cost_input + cost_output

    def _update_daily_stats(self, call: ModelCall, cost: float):
        """Actualiza estadísticas diarias"""
        today = self._get_today_key()

        if today not in self.data["daily"]:
            self.data["daily"][today] = {}

        if call.model not in self.data["daily"][today]:
            self.data["daily"][today][call.model] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost": 0.0
            }

        stats = self.data["daily"][today][call.model]
        stats["calls"] += 1
        stats["input_tokens"] += call.input_tokens
        stats["output_tokens"] += call.output_tokens
        stats["total_tokens"] += call.total_tokens
        stats["cost"] += cost

    def _cleanup_old_daily(self, days_to_keep: int = 30):
        """Elimina registros diarios antiguos"""
        today = date.today()
        old_days = list(self.data["daily"].keys())

        for day in old_days:
            try:
                day_date = date.fromisoformat(day)
                delta = today - day_date
                if delta.days > days_to_keep:
                    del self.data["daily"][day]
            except Exception:
                # Formato inválido, eliminar
                del self.data["daily"][day]

    def record_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task: str,
        success: bool = True,
        error: str = "",
        metadata: Dict[str, Any] = None
    ) -> float:
        """
        Registra una llamada a API.

        Args:
            model: ID del modelo (ej: "qwen/qwen3-vl-235b-a22b-instruct")
            input_tokens: Tokens de entrada
            output_tokens: Tokens de salida
            task: Tipo de tarea (vision, sibom_parsing, transparency, etc.)
            success: Si la llamada fue exitosa
            error: Mensaje de error si falló
            metadata: Información adicional

        Returns:
            Costo estimado de la llamada en USD
        """
        call = ModelCall(
            model=model,
            task=task,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            timestamp=datetime.now().isoformat(),
            success=success,
            error=error,
            metadata=metadata or {}
        )

        cost = self._calculate_cost(model, input_tokens, output_tokens)

        # Serializar y agregar
        self.data["calls"].append(asdict(call))
        self.data["total_calls"] += 1
        self.data["total_cost"] += cost

        # Actualizar stats diarias
        self._update_daily_stats(call, cost)

        # Limpiar registros antiguos
        self._cleanup_old_daily()

        # Guardar
        self._save_usage()

        return cost

    def get_stats(self, days: int = 1) -> Dict[str, Any]:
        """
        Retorna estadísticas agregadas.

        Args:
            days: Número de días a incluir (default: 1 = hoy)

        Returns:
            Dict con estructura:
            {
                "models": {
                    "model_id": {
                        "calls": 10,
                        "input_tokens": 5000,
                        "output_tokens": 2000,
                        "total_tokens": 7000,
                        "cost": 0.01,
                        "task": "vision",
                        "display_name": "Qwen3-VL",
                        "is_free": false
                    }
                },
                "total": {
                    "calls": 100,
                    "total_tokens": 50000,
                    "cost": 0.50
                },
                "period": "2026-01-30 to 2026-01-30"
            }
        """
        today = date.today()
        models: Dict[str, Dict[str, Any]] = {}
        total_calls = 0
        total_tokens = 0
        total_cost = 0.0

        # Recopilar datos del período
        for i in range(days):
            day = (today - __import__('datetime').timedelta(days=i)).isoformat()

            if day not in self.data.get("daily", {}):
                continue

            for model_id, stats in self.data["daily"][day].items():
                if model_id not in models:
                    model_config = MODEL_PRICING.get(model_id, {})
                    models[model_id] = {
                        "calls": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "cost": 0.0,
                        "recalculated_cost": 0.0,  # Costo con precios actuales
                        "task": model_config.get("type", "unknown"),
                        "display_name": model_config.get("display_name", model_id.split("/")[-1][:20]),
                        "is_free": model_config.get("free", False)
                    }

                m = models[model_id]
                m["calls"] += stats["calls"]
                m["input_tokens"] += stats["input_tokens"]
                m["output_tokens"] += stats["output_tokens"]
                m["total_tokens"] += stats["total_tokens"]
                m["cost"] += stats["cost"]

                # Recalcular costo con precios actuales
                if not m["is_free"]:
                    model_config = MODEL_PRICING.get(model_id, {})
                    cost_input = (stats["input_tokens"] / 1_000_000) * model_config.get("cost_per_million_input", 0)
                    cost_output = (stats["output_tokens"] / 1_000_000) * model_config.get("cost_per_million_output", 0)
                    m["recalculated_cost"] += cost_input + cost_output

                total_calls += stats["calls"]
                total_tokens += stats["total_tokens"]
                # Usar costo recalculado si está disponible
                total_cost += m.get("recalculated_cost", stats["cost"])

        # Ordenar por costo (descendente)
        sorted_models = dict(sorted(
            models.items(),
            key=lambda x: x[1]["cost"],
            reverse=True
        ))

        from_date = (today - __import__('datetime').timedelta(days=days-1)).isoformat()
        to_date = today.isoformat()

        return {
            "models": sorted_models,
            "total": {
                "calls": total_calls,
                "total_tokens": total_tokens,
                "cost": total_cost
            },
            "period": f"{from_date} to {to_date}"
        }

    def get_model_list(self) -> List[str]:
        """Retorna la lista de modelos trackeados"""
        return list(MODEL_PRICING.keys())

    def add_model_pricing(self, model: str, config: Dict[str, Any]):
        """
        Agrega o actualiza la configuración de precios de un modelo.

        Args:
            model: ID del modelo
            config: Configuración con keys:
                - type: "vision" o "llm"
                - provider: "openrouter", "openai", etc.
                - cost_per_million_input: float
                - cost_per_million_output: float
                - free: bool
                - display_name: str
        """
        MODEL_PRICING[model] = config


# ============================================================================
# SINGLETON GLOBAL
# ============================================================================

_tracker: Optional[LLMTracker] = None


def get_llm_tracker() -> LLMTracker:
    """Retorna el singleton del tracker"""
    global _tracker
    if _tracker is None:
        _tracker = LLMTracker()
    return _tracker


def record_llm_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    task: str,
    success: bool = True,
    error: str = "",
    metadata: Dict[str, Any] = None
) -> float:
    """
    Registra una llamada a LLM. Convenience function.

    Returns:
        Costo estimado de la llamada
    """
    return get_llm_tracker().record_call(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        task=task,
        success=success,
        error=error,
        metadata=metadata
    )


def get_llm_stats(days: int = 1) -> Dict[str, Any]:
    """Retorna estadísticas de uso de LLM. Convenience function."""
    return get_llm_tracker().get_stats(days=days)


# ============================================================================
# FUNCIÓN PARA EXTRACCIÓN DE TOKENS DESDE RESPONSE
# ============================================================================

def extract_token_usage(response: Any) -> tuple[int, int]:
    """
    Extrae input_tokens y output_tokens desde una respuesta de API.

    Compatible con:
    - OpenRouter SDK (response.usage)
    - OpenAI SDK (response.usage)
    - Dict con clave 'usage'

    Returns:
        (input_tokens, output_tokens) - (0, 0) si no se puede determinar
    """
    try:
        # Caso 1: Objeto con atributo .usage
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'prompt_tokens'):
                return (
                    getattr(usage, 'prompt_tokens', 0),
                    getattr(usage, 'completion_tokens', 0)
                )
            # Si usage es un dict
            if isinstance(usage, dict):
                return (
                    usage.get('prompt_tokens', usage.get('input_tokens', 0)),
                    usage.get('completion_tokens', usage.get('output_tokens', 0))
                )

        # Caso 2: Dict directo
        if isinstance(response, dict):
            usage = response.get('usage', {})
            if isinstance(usage, dict):
                return (
                    usage.get('prompt_tokens', usage.get('input_tokens', 0)),
                    usage.get('completion_tokens', usage.get('output_tokens', 0))
                )

        # Caso 3: Anthropic-style (input_tokens, output_tokens)
        if hasattr(response, 'input_tokens') and hasattr(response, 'output_tokens'):
            return response.input_tokens, response.output_tokens

    except Exception:
        pass

    return 0, 0


# ============================================================================
# TEST / DEBUG
# ============================================================================

if __name__ == "__main__":
    # Test básico
    tracker = LLMTracker()

    # Simular algunas llamadas
    tracker.record_call(
        model="qwen/qwen3-vl-235b-a22b-instruct",
        input_tokens=15000,
        output_tokens=3000,
        task="vision"
    )

    tracker.record_call(
        model="z-ai/glm-4.5-air:free",
        input_tokens=5000,
        output_tokens=1000,
        task="sibom_parsing"
    )

    stats = tracker.get_stats()

    console.print("[cyan]📊 Estadísticas de LLM:[/cyan]")
    console.print(f"  Periodo: {stats['period']}")
    console.print(f"  Total calls: {stats['total']['calls']}")
    console.print(f"  Total tokens: {stats['total']['total_tokens']:,}")
    console.print(f"  Total costo: ${stats['total']['cost']:.4f}")
    console.print()

    for model_id, data in stats['models'].items():
        free_str = "[green]GRATIS[/green]" if data['is_free'] else f"${data['cost']:.4f}"
        console.print(f"  {data['display_name']}: {data['calls']} calls, {data['total_tokens']:,} tokens, {free_str}")
