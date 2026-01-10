#!/usr/bin/env python3
"""
Sincronización completa: .kiro/ ↔ .agents/

Ejecuta ambos scripts de sincronización en secuencia:
1. sync_from_kiro.py  - Actualiza .agents/ desde .kiro/
2. propagate_to_kiro.py - Propaga reglas de .agents/ hacia .kiro/

Uso:
    python .agents/hooks/sync_all.py
"""

from pathlib import Path
from datetime import datetime
import subprocess
import sys
import os

def run_script(script_path, script_name):
    """Ejecuta un script Python y maneja errores"""
    print(f"\n{'=' * 60}")
    print(f"Ejecutando: {script_name}")
    print('=' * 60)

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERROR en {script_name}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR inesperado en {script_name}: {e}")
        return False

def create_sync_report():
    """Crea reporte de sincronización"""
    report = f"""# Reporte de Sincronización

## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Scripts Ejecutados

1. ✅ sync_from_kiro.py - .kiro/ → .agents/
2. ✅ propagate_to_kiro.py - .agents/ → .kiro/

### Estado

- `.agents/specs/`: Referencias a .kiro/ generadas
- `.agents/steering/`: Base de .kiro/ + reglas específicas
- `.kiro/steering/`: Actualizado con "Agent AI Requirements"

### Próximos Pasos

1. Revisar cambios: `git diff`
2. Commit: `git add .agents/ .kiro/`
3. Push: `git push`

---

**Para más información:** Ver [GUIA_COMPLETA.md](../GUIA_COMPLETA.md)
"""

    report_file = Path('.agents/SYNC_REPORT.md')
    report_file.write_text(report, encoding='utf-8')
    print(f"\n📝 Reporte creado: {report_file}")

def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("🔄 Sincronización Completa: .kiro/ ↔ .agents/")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Obtener el directorio raíz del proyecto (donde está .git)
    current = Path(__file__).resolve()
    root = current.parent.parent.parent  # .agents/hooks/sync_all.py -> raíz
    
    # Cambiar al directorio raíz
    import os
    os.chdir(root)
    print(f"📂 Directorio de trabajo: {root}")

    agents_hooks = root / '.agents' / 'hooks'

    # Scripts a ejecutar
    scripts = [
        (agents_hooks / 'sync_from_kiro.py', 'sync_from_kiro.py'),
        (agents_hooks / 'propagate_to_kiro.py', 'propagate_to_kiro.py'),
    ]

    # Verificar que scripts existan
    missing = [s for s, _ in scripts if not s.exists()]
    if missing:
        print("\n❌ ERROR: Scripts no encontrados:")
        for s in missing:
            print(f"   - {s}")
        print("\n   Ejecuta primero: python .agents/hooks/sync_from_kiro.py")
        return False

    # Ejecutar scripts en secuencia
    results = []
    for script_path, script_name in scripts:
        success = run_script(script_path, script_name)
        results.append(success)

        if not success:
            print(f"\n⚠️  Deteniendo sincronización debido a errores")
            return False

    # Crear reporte
    create_sync_report()

    # Resumen final
    print("\n" + "=" * 60)
    print("✅ Sincronización completada")
    print("=" * 60)
    print(f"\n📊 Resumen:")
    print(f"   - Scripts ejecutados: {len(results)}")
    print(f"   - Todos exitosos: {all(results)}")
    print(f"\n💡 Próximos pasos:")
    print(f"   1. Revisar: git diff .agents/ .kiro/")
    print(f"   2. Commit: git add .agents/ .kiro/")
    print(f"   3. Mensaje: git commit -m 'docs: sincronizar .agents/ con .kiro/'")

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
