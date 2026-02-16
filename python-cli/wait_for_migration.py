#!/usr/bin/env python3
"""Monitor que espera a que la migración termine y luego ejecuta validación."""

import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

CHECKPOINT_FILE = Path("data/migration_checkpoint.json")
TOTAL_BALANCES = 169
POLL_INTERVAL = 30  # segundos


def read_checkpoint():
    """Lee checkpoint actual."""
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    except:
        return None


def run_validation():
    """Ejecuta validación post-migración."""
    print("\n" + "="*70)
    print("🚀 INICIANDO VALIDACIÓN POST-MIGRACIÓN")
    print("="*70 + "\n")

    result = subprocess.run(
        ["python", "scripts/post_migration_validation.py"],
        cwd=str(Path(__file__).parent)
    )
    return result.returncode == 0


print("\n" + "="*70)
print("⏳ MONITOR DE MIGRACIÓN - Esperando completación")
print("="*70)

last_file_count = 0
last_chunk_count = 0

while True:
    cp = read_checkpoint()

    if not cp:
        print("⏳ Esperando primer checkpoint...")
        time.sleep(POLL_INTERVAL)
        continue

    file_count = len(cp.get("processed_file_paths", []))
    chunk_count = cp.get("processed_chunks", 0)

    # Mostrar solo si cambió
    if file_count != last_file_count or chunk_count != last_chunk_count:
        progress = (file_count / TOTAL_BALANCES) * 100
        eta_remaining = TOTAL_BALANCES - file_count
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {file_count}/{TOTAL_BALANCES} ({progress:.1f}%) | Chunks: {chunk_count} | Pendientes: {eta_remaining}")
        last_file_count = file_count
        last_chunk_count = chunk_count

    # Si completó
    if file_count >= TOTAL_BALANCES:
        print("\n" + "="*70)
        print("✅ MIGRACIÓN COMPLETADA")
        print("="*70)

        if run_validation():
            print("\n✅ Validación completada exitosamente")
        else:
            print("\n⚠️  Validación tuvo advertencias")

        sys.exit(0)

    time.sleep(POLL_INTERVAL)
