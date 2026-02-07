# PROMPT SIMPLIFICADO PARA GLM-4.7
# =============================================================================
# COPIA TODO ESTE CONTENIDO Y PÉGALO EN:
# https://openrouter.ai/chat?model=z-ai/glm-4.7-64b-1m-fix
# o en tu cliente de OpenRouter
# =============================================================================

Eres un **senior Python refactoring specialist**. Refactoriza el siguiente código:

```python
# Código vulnerable a path traversal
def _sanitize_filename(self, description: str, number: str = None) -> str:
    cleaned = re.sub(r'[^\w\s-]', '', cleaned)
    return f"{cleaned}_{num}"
```

**Requisitos de refactoring:**
1. ✅ Prevenir path traversal (../, .\\, etc.)
2. ✅ Validar que description sea string no vacío
3. ✅ Normalizar con PurePath
4. ✅ Agregar type hints completos
5. ✅ Crear SecurityError custom exception
6. ✅ Máximo 15 líneas
7. ✅ Documentación Google style

**Entrega:** Solo el código refactoreado en un bloque markdown.

# =============================================================================
# FIN DEL PROMPT - COPIA TODO LO DE ARRIBA
# =============================================================================
