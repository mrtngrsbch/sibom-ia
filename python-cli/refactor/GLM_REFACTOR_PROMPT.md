# PROMPT REFACTORING PYTHON-CLI V3.0 - PARA GLM-4.7
# =============================================================================
# Copiar TODO este contenido y pegarlo en GLM-4.7
# =============================================================================

Eres un **refactoring specialist** senior. Tu tarea es refactorizar el proyecto 'python-cli' con las siguientes especificaciones:

## 📋 CONTEXTO DEL PROYECTO

- **Nombre**: python-cli (scraper de boletines oficiales)
- **Líneas totales**: 3,949
- **Archivos críticos**: core/sibom_scraper.py (2,152 líneas), core/web_scraper.py (1,630 líneas)
- **Problema principal**: God class y 0% de tests

## 🔥 ISSUES CRÍTICOS A CORREGIR (en orden de prioridad)

### 1. Path Traversal Vulnerable (LÍNEA 331, core/sibom_scraper.py)
**Código actual (INSEGURO):**
```python
def _sanitize_filename(self, description: str, number: str = None) -> str:
    cleaned = re.sub(r'[^\w\s-]', '', cleaned)
    return f"{cleaned}_{num}"
```

**Código refactoreado (SEGURO):**
```python
from pathlib import PurePath

def _sanitize_filename(self, description: str, number: str = None) -> str:
    if not description or not isinstance(description, str):
        raise ValueError("Descripción inválida")
    
    cleaned = re.sub(r'[^\w\s-]', '', description)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    filename = f"{cleaned}_{num or '0'}"
    
    # Prevención de path traversal
    if any(char in filename for char in '/\\'):
        raise SecurityError(f"Caracteres de ruta detectados: {filename}")
    
    return PurePath(filename).name
```

### 2. Función Duplicada (LÍNEAS 301, 314, core/sibom_scraper.py)
**Eliminar la segunda definición de `_get_city_name_from_url` (línea 314-329).**

### 3. God Class - Dividir `process_bulletin()` (LÍNEA 931)
**Código actual (315 líneas):**
```python
def process_bulletin(self, bulletin, base_url, output_dir, skip_existing=True, resume=True, use_llm=True):
    # ... 315 líneas monolíticas ...
```

**Refactoreado (6 funciones de <50 líneas):**
```python
def process_bulletin(self, bulletin: dict, base_url: str, output_dir: Path, 
                     skip_existing: bool = True, resume: bool = True) -> dict:
    """Orquestador principal."""
    self._validate_bulletin(bulletin)
    metadata = self._extract_bulletin_metadata(bulletin, base_url)
    progress = self._load_existing_progress(bulletin, resume)
    content = self._extract_full_content(metadata, progress, use_llm)
    result = self._build_complete_result(metadata, content)
    self._save_all_outputs(result, output_dir)
    self._update_indices_and_logs(result)
    return result

def _validate_bulletin(self, bulletin: dict) -> None:
    """Valida estructura del boletín."""
    required = ["id", "number", "description"]
    if not all(k in bulletin for k in required):
        raise ValueError(f"Boletín inválido: falta {required}")

def _extract_bulletin_metadata(self, bulletin: dict, base_url: str) -> dict:
    """Extrae metadata inicial."""
    return {
        "id": bulletin["id"],
        "number": bulletin.get("number", "N/A"),
        "title": bulletin.get("description", "No title"),
        "url": f"{base_url}/bulletins/{bulletin['id']}",
    }

def _load_existing_progress(self, bulletin: dict, resume: bool) -> set:
    """Carga progreso previo si existe."""
    if not resume:
        return set()
    progress_file = Path(f".progress_{bulletin['id']}.json")
    return json.loads(progress_file.read_text()) if progress_file.exists() else set()

def _extract_full_content(self, metadata: dict, progress: set, use_llm: bool) -> dict:
    """Extrae contenido completo (scraper + extractores)."""
    # ... implementación específica ...
    pass

def _build_complete_result(self, metadata: dict, content: dict) -> dict:
    """Construye resultado final combinado."""
    return {**metadata, "content": content, "status": "completed"}

def _save_all_outputs(self, result: dict, output_dir: Path) -> None:
    """Guarda JSON y metadata."""
    output_file = output_dir / f"{result['id']}.json"
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

def _update_indices_and_logs(self, result: dict) -> None:
    """Actualiza índice global y logs."""
    logger.info(f"✓ Procesado boletín {result['id']}")
```

### 4. Type Hints Completos
**Agregar anotaciones a TODAS las funciones:**
```python
from typing import Optional, Dict, List, Any

def scrape_city(self, city_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    ...
```

### 5. Tests Unitarios
**Crear test para cada función refactoreada:**
```python
def test__sanitize_filename_prevents_traversal():
    scraper = SIBOMScraper(api_key="test")
    with pytest.raises(SecurityError):
        scraper._sanitize_filename("../../../etc/passwd")
```

## 📏 ESTÁNDARES DE CÓDIGO

- **Máximo 50 líneas por función**
- **Type coverage >95%**
- **Test coverage >85%**
- **Nombre variables**: inglés técnico, español dominio de negocio
- **Excepciones**: custom con contexto, nunca bare except
- **Async**: usar para operaciones I/O

## ✅ CHECKLIST DE VERIFICACIÓN

Antes de entregar, verifica:
- [ ] Path traversal está prevenido
- [ ] Función duplicada eliminada
- [ ] process_bulletin() dividida en 6 funciones
- [ ] Todos los parámetros tienen type hints
- [ ] Tests unitarios creados
- [ ] Mypy --strict pasa sin errores
- [ ] pylint score > 9.0
- [ ] Tiene docstrings Google style

## 🎯 ENTREGA ESPERADA

Refactoriza SECUENCIALMENTE:
1. `_sanitize_filename()` → con seguridad
2. `_get_city_name_from_url()` → eliminar duplicación
3. `process_bulletin()` → dividir en 6 funciones
4. Agregar type hints a todas las funciones nuevas
5. Crear tests unitarios

**IMPORTANTE**: Devuelve SOLO el código refactoreado, no explicaciones largas.
