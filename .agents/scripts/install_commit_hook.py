#!/usr/bin/env python3
"""
Instala el commit-msg hook para validación de Conventional Commits

Uso:
    python3 install_commit_hook.py
"""

import shutil
import sys
from pathlib import Path


def install_commit_hook():
    """Instala el commit-msg hook en .git/hooks/"""
    
    repo_root = Path.cwd()
    hook_source = repo_root / '.git' / 'hooks' / 'commit-msg.template'
    hook_target = repo_root / '.git' / 'hooks' / 'commit-msg'
    
    # Crear el template si no existe
    if not hook_source.exists():
        hook_content = '''#!/bin/sh
set -e

# Commit-msg hook for SIBOM Scraper Assistant
# Validates commit message format (Conventional Commits)

COMMIT_MSG_FILE=$1

echo "✨ Validating commit message format..."

# Validar con script Python
if command -v python3 &> /dev/null; then
    if python3 .agents/scripts/validate_commit_message.py "$COMMIT_MSG_FILE"; then
        echo "✅ Commit message format validated!"
    else
        echo ""
        echo "❌ Commit message validation failed!"
        echo ""
        echo "   You can bypass this hook with:"
        echo "   git commit --no-verify"
        echo ""
        echo "   But it's highly recommended to use the correct format"
        exit 1
    fi
else
    echo "⚠️  WARNING: python3 not found, skipping commit message validation"
    echo "   Consider installing Python 3.13 for validation"
fi
'''
        hook_source.write_text(hook_content)
        print(f"✅ Created hook template: {hook_source}")
    
    # Copiar el template al hook
    try:
        shutil.copy2(hook_source, hook_target)
        hook_target.chmod(0o755)  # Hacer ejecutable
        print(f"✅ Installed commit-msg hook: {hook_target}")
        return True
    except Exception as e:
        print(f"❌ Error installing hook: {e}")
        return False


def main():
    print("🔧 Installing commit-msg hook...")
    print("=" * 40)
    
    if install_commit_hook():
        print()
        print("✅ Installation complete!")
        print()
        print("The commit-msg hook will now validate all commit messages.")
        print("Invalid formats will be rejected with helpful error messages.")
        print()
        print("You can test it with:")
        print("  git commit -m 'feat(chatbot): add vector search'")
        print()
        print("To bypass validation:")
        print("  git commit --m 'invalid message' --no-verify")
        sys.exit(0)
    else:
        print()
        print("❌ Installation failed!")
        print("Please check the error above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
