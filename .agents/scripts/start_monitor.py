#!/usr/bin/env python3
"""
Inicia el monitor del commit-agent en background

Uso:
    python3 .agents/scripts/start_monitor.py
"""

import subprocess
import sys
from pathlib import Path
import os

def start_monitor():
    """Inicia el monitor en background"""
    
    repo_root = Path.cwd()
    script_path = repo_root / '.agents' / 'scripts' / 'commit_agent.py'
    
    if not script_path.exists():
        print(f"❌ ERROR: Script no encontrado: {script_path}")
        sys.exit(1)
    
    print("🔧 Iniciando monitor del Commit Agent...")
    print("=" * 50)
    print()
    print("📊 Qué hace el monitor:")
    print("  - Verifica cambios cada 30 minutos")
    print("  - Alerta si hay >3 archivos modificados")
    print("  - Alerta si hay >200 líneas cambiadas")
    print("  - Alerta si hace >2 horas desde el último commit")
    print()
    print("📁 Dónde guarda alertas:")
    print("  - .agents/logs/commit-alerts.log")
    print()
    print("🔔 Cómo recibir alertas:")
    print("  - macOS: Notificaciones nativas")
    print("  - Chat: Pregunta en el chat")
    print()
    print("=" * 50)
    print()
    print("⏱️  Iniciando en segundo plano...")
    
    try:
        # Iniciar el proceso en background
        process = subprocess.Popen(
            ['python3', str(script_path), 'monitor', '--interval', '30'],
            cwd=repo_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Guardar el PID
        pid = process.pid
        pid_file = repo_root / '.agents' / 'logs' / 'monitor.pid'
        pid_file.write_text(str(pid))
        
        print(f"✅ Monitor iniciado (PID: {pid})")
        print()
        print("💡 Para ver alertas:")
        print("   cat .agents/logs/commit-alerts.log")
        print()
        print("💡 Para detener el monitor:")
        print("   python3 .agents/scripts/commit_agent.py monitor --stop")
        print("   O: kill {pid}")
        print()
        
    except Exception as e:
        print(f"❌ ERROR al iniciar monitor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_monitor()
