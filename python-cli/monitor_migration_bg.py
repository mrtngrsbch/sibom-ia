#!/usr/bin/env python3
"""
Monitor continuo de migración que ejecuta validación automáticamente.
Se ejecuta en background y notifica cuando termina.
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

CHECKPOINT_FILE = Path("data/migration_checkpoint.json")
TOTAL_BALANCE_FILES = 169
POLL_INTERVAL = 60  # segundos


def count_files_in_checkpoint():
    """Cuenta archivos únicos en el checkpoint."""
    if not CHECKPOINT_FILE.exists():
        return 0
    try:
        with open(CHECKPOINT_FILE) as f:
            cp = json.load(f)
            return len(cp.get("processed_file_paths", []))
    except:
        return 0


def get_checkpoint_data():
    """Lee datos completos del checkpoint."""
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

    subprocess.run(
        ["python", "scripts/post_migration_validation.py"],
        cwd=str(CHECKPOINT_FILE.parent)
    )


print("\n" + "="*70)
print("⏳ MONITOR DE MIGRACIÓN (Background)")
print("="*70)
print(f"Esperando completación de 169 balance files...")
print(f"Poll interval: {POLL_INTERVAL} segundos\n")

seen_file_counts = set()

while True:
    file_count = count_files_in_checkpoint()

    # Mostrar solo cambios
    if file_count not in seen_file_counts:
        cp = get_checkpoint_data()
        chunk_count = cp.get("processed_chunks", 0) if cp else "?"
        progress = (file_count / TOTAL_BALANCE_FILES) * 100
        remaining = TOTAL_BALANCE_FILES - file_count

        print(f"[{datetime.now().strftime('%H:%M:%S')}] {file_count:3d}/{TOTAL_BALANCE_FILES} ({progress:5.1f}%) | "
              f"Chunks: {chunk_count:4s} | Pendientes: {remaining:3d}")

        seen_file_counts.add(file_count)

        # Si completó
        if file_count >= TOTAL_BALANCE_FILES:
            print("\n" + "="*70)
            print("✅ MIGRACIÓN COMPLETADA")
            print("="*70)
            run_validation()
            break

    time.sleep(POLL_INTERVAL)
