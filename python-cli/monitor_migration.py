#!/usr/bin/env python3
"""Monitorea migración en tiempo real leyendo checkpoint y logs."""

import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path


def read_checkpoint():
    """Lee el checkpoint actual."""
    cp_file = Path("data/migration_checkpoint.json")
    if not cp_file.exists():
        return None
    try:
        with open(cp_file) as f:
            return json.load(f)
    except:
        return None


def get_log_tail(n=10):
    """Lee últimas líneas del log."""
    log_file = Path("/tmp/migration_full.log")
    if not log_file.exists():
        return []
    try:
        with open(log_file) as f:
            lines = f.readlines()
            return [l.strip() for l in lines[-n:] if l.strip()]
    except:
        return []


def count_total_files():
    """Cuenta archivos Balance de Tesorería."""
    boletines_dir = Path("boletines")
    count = 0
    for f in boletines_dir.rglob("*Balances*.json"):
        if "Balance de Tesorería" in f.read_text() or "BALANCE DE TESORERIA" in f.read_text():
            count += 1
    return count


print("\n" + "="*70)
print("🔄 MONITOR DE MIGRACIÓN DE BALANCES")
print("="*70 + "\n")

total_files = 25  # Sabemos que son 25
last_checkpoint = None

while True:
    # Leer checkpoint
    cp = read_checkpoint()

    if cp and cp != last_checkpoint:
        last_checkpoint = cp
        files_done = len(cp.get("processed_files", []))
        chunks_done = cp.get("total_chunks_processed", 0)
        last_update = cp.get("last_updated", "?")

        print(f"⏱️  {datetime.now().strftime('%H:%M:%S')}")
        print(
            f"   📊 Progreso: {files_done}/{total_files} archivos ({100*files_done//total_files}%)")
        print(f"   📦 Chunks: {chunks_done} generados")
        print(f"   ⏰ Última actualización: {last_update}")
        print()

    # Mostrar últimas líneas del log (solo si hay cambio)
    tail = get_log_tail(3)
    if tail:
        for line in tail:
            if any(x in line for x in ["uploaded", "Checkpoint", "Processing", "Embedding"]):
                print(f"   {line[:60]}...")

    # Check si terminó
    if cp and len(cp.get("processed_files", [])) >= total_files:
        print("\n" + "="*70)
        print("✅ MIGRACIÓN COMPLETADA")
        print("="*70)
        break

    time.sleep(10)  # Actualizar cada 10 segundos
