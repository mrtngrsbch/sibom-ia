#!/usr/bin/env python3
"""Analiza estado de migración."""

import json
from pathlib import Path

# Leer checkpoint
with open("data/migration_checkpoint.json") as f:
    cp = json.load(f)

processed_files = len(cp["processed_file_paths"])
total_chunks = cp["processed_chunks"]
total_files = len(list(Path("boletines").rglob("*Balances*.json")))

print("\n" + "="*70)
print("📊 ESTADO ACTUAL DE MIGRACIÓN DE BALANCES")
print("="*70)
print(f"\n✅ PROGRESO:")
print(
    f"   • Archivos procesados: {processed_files}/{total_files} ({100*processed_files//total_files}%)")
print(f"   • Chunks generados: {total_chunks}")
print(f"   • Última actualización: {cp['last_updated']}")

print(f"\n📈 ESTIMACIONES:")
remaining = total_files - processed_files
avg_chunks = total_chunks // processed_files if processed_files > 0 else 13
remaining_chunks = remaining * avg_chunks
estimated_cost = (remaining_chunks * 700 * 0.02) / 1_000_000

print(f"   • Archivos pendientes: {remaining}")
print(f"   • Chunks estimados: ~{remaining_chunks}")
print(f"   • Costo estimado: ${estimated_cost:.4f} USD")
print(f"   • Tiempo estimado: ~{remaining * 1.5:.0f} minutos")

print(f"\n☁️  QDRANT CLOUD:")
print(f"   • Inicio: 8,760 points")
print(f"   • Chunks agregados: {total_chunks}")
print(f"   • Total estimado: {8760 + total_chunks:,} puntos")

print("\n" + "="*70 + "\n")
