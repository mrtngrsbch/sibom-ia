#!/usr/bin/env python3
"""
Valida formato de mensaje de commit Conventional Commits

Uso:
    python3 validate_commit_message.py <commit_message_file>
"""

import sys
import re
from pathlib import Path

# Tipos de commits permitidos
COMMIT_TYPES = ['feat', 'fix', 'docs', 'refactor', 'test', 'chore', 'build', 'ci', 'perf', 'style', 'revert']

# Scopes permitidos (opcional, puede ser None)
COMMIT_SCOPES = ['chatbot', 'scraper', 'agents', 'docs', 'ci']

# Regex para Conventional Commits
CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r'^(?P<type>[a-z]+)(\((?P<scope>[a-z0-9-]+)\))?:(?P<breaking>!)? (?P<subject>.+)$',
    re.MULTILINE
)

def validate_commit_message(message: str) -> tuple[bool, str]:
    """
    Valida formato de mensaje de commit
    
    Returns:
        (is_valid, error_message)
    """
    
    # Remover líneas vacías y comentarios
    lines = [line.strip() for line in message.split('\n') if line.strip() and not line.startswith('#')]
    
    if not lines:
        return False, "El mensaje de commit está vacío"
    
    first_line = lines[0]
    
    # Validar formato básico
    match = CONVENTIONAL_COMMIT_PATTERN.match(first_line)
    if not match:
        return False, f"Formato inválido: '{first_line}'"
    
    commit_type = match.group('type')
    scope = match.group('scope')
    subject = match.group('subject')
    
    # Validar tipo
    if commit_type not in COMMIT_TYPES:
        return False, f"Tipo inválido: '{commit_type}'. Debe ser uno de: {', '.join(COMMIT_TYPES)}"
    
    # Validar scope (si existe)
    if scope and scope not in COMMIT_SCOPES:
        return False, f"Scope inválido: '{scope}'. Debe ser uno de: {', '.join(COMMIT_SCOPES)}"
    
    # Validar longitud del subject
    if len(subject) < 10:
        return False, f"Subject muy corto: '{subject}' (mínimo 10 caracteres)"
    
    if len(subject) > 72:
        return False, f"Subject muy largo: '{subject}' (máximo 72 caracteres, tiene {len(subject)})"
    
    # Validar que no termine con punto
    if subject.endswith('.'):
        return False, f"Subject no debe terminar con punto: '{subject}'"
    
    # Validar que sea minúsculas
    if subject[0].isupper():
        return False, f"Subject debe comenzar con minúscula: '{subject}'"
    
    return True, ""


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 validate_commit_message.py <commit_message_file>")
        sys.exit(1)
    
    commit_message_file = sys.argv[1]
    
    try:
        with open(commit_message_file, 'r', encoding='utf-8') as f:
            message = f.read()
    except FileNotFoundError:
        print(f"❌ ERROR: Archivo no encontrado: {commit_message_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: No se pudo leer el archivo: {e}")
        sys.exit(1)
    
    is_valid, error_message = validate_commit_message(message)
    
    if not is_valid:
        print(f"❌ ERROR: {error_message}")
        print()
        print("Formato requerido: type(scope): subject")
        print()
        print("Tipos permitidos:")
        print("  feat, fix, docs, refactor, test, chore, build, ci, perf, style, revert")
        print()
        print("Scopes permitidos:")
        print("  chatbot, scraper, agents, docs, ci")
        print()
        print("Ejemplos:")
        print("  feat(chatbot): add vector search")
        print("  fix(scraper): handle rate limit")
        print("  docs(agents): add commit-agent")
        print("  refactor(rag): improve performance")
        print("  test(api): add integration tests")
        print("  chore(deps): upgrade dependencies")
        print()
        print("Longitud del subject: 10-72 caracteres")
        print("No debe terminar con punto")
        print("Debe comenzar con minúscula")
        sys.exit(1)
    
    print("✅ Commit message válido")
    sys.exit(0)


if __name__ == '__main__':
    main()
